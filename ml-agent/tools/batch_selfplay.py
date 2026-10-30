"""Speed prototype for RL: many self-play games in lockstep, the board network batched on the GPU.

Each process plays --games games at once (both seats are our agent). Every turn it asks the template and encoder
for every board, runs one batched network pass for all of them, then decides worker by worker exactly as
NetPlayer.act does, one batched `decide` per worker index.

python tools/batch_selfplay.py --games 64 --procs 1 --device cuda
python tools/batch_selfplay.py --check        # 2 games: batched (cpu) against the plain NetPlayer, same banks?
"""
import argparse
import copy
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from kagml.net_player import NetPlayer
from kagml.paths import runs
from kagml.preview import pin_weeds

SPEC = 'board-p5:market:overflow:endmask:endwork:end29'
SUPPORTED = {'market', 'overflow', 'endmask', 'endwork', 'end29'}


class BatchNet(NetPlayer):
    """NetPlayer.__call__ split around the network call, for the options in SUPPORTED only."""

    def __init__(self, spec=SPEC):
        super().__init__(spec)
        assert set(spec.split(':')[1:]) <= SUPPORTED, spec

    def prepare(self, obs, conf):
        """Template action and encoded board, or (final action, None) outside the network's days."""
        self.net = self._model_for_day(int(obs['day']))
        action = dict(self.module.agent(obs, conf))
        self.history.observe(obs, obs['player'], self.prev_action)
        if not self.days[0] <= obs['day'] <= self.days[1]:
            if self.endmask:
                action = self._end_mask(obs, action)
            if self.end29 and obs['day'] == self.LAST_DAY:
                action = self._end29_sell(obs, action)
            self.prev_action = action
            return action, None
        return action, self.bf.encode(obs, obs['player'], self.history)

    def legal_fn(self, obs):
        """Same masks as NetPlayer._legal, but incremental: one copy of the farm per turn, each chosen command
        applied once, instead of a fresh copy and replay of all earlier commands for every worker."""
        bf, seat, day = self.bf, obs['player'], int(obs['day'])
        st = {'k': 0, 'farm': None, 'private': None}

        def f(k, chosen, amts):
            if st['farm'] is None:
                st['farm'], st['private'] = copy.deepcopy((obs['farms'][seat], obs['private']))
            while st['k'] < k:
                j = st['k']
                bf.apply(st['farm'], st['private'], j, self._engine(chosen[j], amts[j]), day)
                st['k'] += 1
            farm = st['farm']
            mask = bf.mask_for_state(farm, st['private'], k, day)
            if not self.endwork:
                return mask
            for c, fy in self.FIRST_YIELD.items():
                if day + fy > self.LAST_DAY:
                    mask[bf.COMMAND_ID[('PLANT', c)]] = False
            if day > self.LAST_ANIMAL_DAY:
                mask[bf.COMMAND_ID[('BUILD_COOP',)]] = mask[bf.COMMAND_ID[('BUILD_PASTURE',)]] = False
            care = bf.COMMAND_ID[('CARE',)]
            if mask[care] and day >= 20:
                x, y = bf.K._farmer_position(farm, k)
                tile = farm['tiles'][y][x]
                fy, every = self.ANIMAL_YIELD[tile['animal']]
                mask[care] = any((n + 1 - tile['placed_day'] - fy) >= 0 and (n + 1 - tile['placed_day'] - fy) % every == 0
                                 for n in range(day + 1, self.LAST_DAY))
            return mask
        return f

    def finish(self, obs, action, cmds, amounts, market_logits):
        commands = [self._engine(c, amounts[k]) for k, c in enumerate(cmds)]
        n = len(obs['farms'][obs['player']]['hands']) + 1
        commands += [['PASS']] * (n - len(commands))
        if self.use_market and self.net.cfg.market:
            net, self.net = self.net, SimpleNamespace(cfg=self.net.cfg, market_logits=lambda: market_logits[None])
            action['market'] = self._market_orders(n)
            self.net = net
        if self.overflow:
            action = self._overflow_sell(obs, action, n)
        if self.endmask:
            action = self._end_mask(obs, action)
        action['farmer'], action['hands'] = commands[0], commands[1:n]
        self.prev_action = action
        return action


@torch.no_grad()
def batched_act(net, xs, legal_fns, dev):
    """NetPlayer's worker-by-worker decoding for many boards at once (argmax, no logit bias)."""
    T = lambda k, dt=torch.float32: torch.as_tensor(np.stack([x[k] for x in xs])).to(dev, dt)
    mask = T('unit_mask', torch.bool)
    xy = torch.as_tensor(np.stack([x['units'][..., :2] for x in xs])).long().to(dev)
    tile_h, unit_h = net.encode(T('tiles'), T('units'), xy, mask, T('glob'))
    market = net.market_logits().float().cpu() if net.cfg.market else None
    b, u = mask.shape
    # earlier workers' decisions are written on the CPU and sent once per worker index (single-element writes to a
    # GPU tensor each wait for the GPU)
    prev_cmd = np.full((b, u), net.cfg.n_commands, dtype=np.int64)
    prev_tgt = np.full((b, u), 100, dtype=np.int64)
    n = mask.sum(1).tolist()
    cmds, amts = [[] for _ in xs], [[] for _ in xs]
    for k in range(max(n)):
        cmd, tgt, amt = net.decide(tile_h, unit_h, mask, torch.from_numpy(prev_cmd).to(dev),
                                   torch.from_numpy(prev_tgt).to(dev))
        ck, tk, ak = cmd[:, k].float().cpu().numpy(), tgt[:, k].argmax(-1).tolist(), (amt[:, k].argmax(-1) + 1).tolist()
        for i in range(b):
            if k >= n[i]:
                continue
            legal = np.asarray(legal_fns[i](k, cmds[i], amts[i]), dtype=bool)
            c = int(np.where(legal, ck[i], -np.inf).argmax())
            cmds[i].append(c), amts[i].append(ak[i])
            prev_cmd[i, k], prev_tgt[i, k] = c, tk[i]
    return cmds, amts, market


def play(job):
    """Play the seeds in lockstep; returns (seed, bank seat 0, bank seat 1, seconds) per game plus a time split."""
    seeds, dev = job
    torch.set_num_threads(1)
    from kaggle_environments import make
    pin_weeds(True)
    envs, players = [], []
    for s in seeds:
        env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': s}, debug=False)
        env.reset(2)
        envs.append(env)
        players.append([BatchNet(), BatchNet()])
    net = players[0][0].net.to(dev)          # one shared copy of the weights does the batched passes
    split = dict(cpu=0.0, net=0.0, engine=0.0)
    start = time.perf_counter()
    while not all(e.done for e in envs):
        t = time.perf_counter()
        live = [g for g, e in enumerate(envs) if not e.done]
        acts = {g: [None, None] for g in live}
        todo = []
        for g in live:
            for i in (0, 1):
                obs = envs[g].state[i].observation
                a, x = players[g][i].prepare(obs, envs[g].configuration)
                if x is None:
                    acts[g][i] = a
                else:
                    todo.append((g, i, obs, a, x))
        split['cpu'] += time.perf_counter() - t
        if todo:
            t = time.perf_counter()
            cmds, amts, market = batched_act(net, [r[4] for r in todo],
                                             [players[g][i].legal_fn(obs) for g, i, obs, _, _ in todo], dev)
            split['net'] += time.perf_counter() - t       # includes the legal masks inside the worker loop
            t = time.perf_counter()
            for j, (g, i, obs, a, _) in enumerate(todo):
                acts[g][i] = players[g][i].finish(obs, a, cmds[j], amts[j], market[j] if market is not None else None)
            split['cpu'] += time.perf_counter() - t
        t = time.perf_counter()
        for g in live:
            envs[g].step(acts[g])
        split['engine'] += time.perf_counter() - t
    wall = time.perf_counter() - start
    games = [(s, e.state[0].observation.farms[0].money, e.state[0].observation.farms[1].money) for s, e in zip(seeds, envs)]
    return games, wall, split


def check():
    """Batched play on the CPU must give the same game as the plain NetPlayer (manual loop, same seeds)."""
    from kaggle_environments import make
    pin_weeds(True)
    seeds = [90001, 90002]                    # not evaluation seeds
    batched, _, _ = play((seeds, 'cpu'))
    for (s, b0, b1) in batched:
        env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': s}, debug=False)
        env.reset(2)
        ps = [NetPlayer(SPEC), NetPlayer(SPEC)]
        while not env.done:
            env.step([p(env.state[i].observation, env.configuration) for i, p in enumerate(ps)])
        f = env.state[0].observation.farms
        print(f'seed {s}: batched {b0:.0f} / {b1:.0f}   plain {f[0].money:.0f} / {f[1].money:.0f}   '
              f'{"SAME" if (b0, b1) == (f[0].money, f[1].money) else "DIFFERENT"}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--games', type=int, default=64, help='games per process')
    ap.add_argument('--procs', type=int, default=1)
    ap.add_argument('--device', default='cuda')
    ap.add_argument('--seed0', type=int, default=90001)   # not an evaluation seed
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--worker', type=int)
    ap.add_argument('--out', default=str(runs() / 'batch-speed'))
    a = ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED') == '0'
    if a.check:
        return check()
    if a.worker is not None:                 # one process: play its seeds, write the result
        seeds = list(range(a.seed0 + a.worker * a.games, a.seed0 + (a.worker + 1) * a.games))
        Path(a.out, f'proc{a.worker}.json').write_text(json.dumps(play((seeds, a.device))))
        return
    # separate processes with their own logs: a crashed process shows up instead of hanging a pool
    Path(a.out).mkdir(parents=True, exist_ok=True)
    start = time.perf_counter()
    procs = []
    for p in range(a.procs):
        log = open(Path(a.out, f'proc{p}.log'), 'w')
        procs.append(subprocess.Popen([sys.executable, __file__, '--worker', str(p), '--games', str(a.games),
                                       '--device', a.device, '--seed0', str(a.seed0), '--out', a.out],
                                      stdout=log, stderr=subprocess.STDOUT))
        time.sleep(2)
    codes = [p.wait() for p in procs]
    wall = time.perf_counter() - start
    out = [json.loads(Path(a.out, f'proc{p}.json').read_text()) for p, c in enumerate(codes) if c == 0]
    if any(codes):
        print('FAILED processes:', [p for p, c in enumerate(codes) if c], '(see their .log files)')
    n = sum(len(g) for g, _, _ in out)
    print(f'{n} games, {a.procs} procs x {a.games}, {a.device}: {wall:.0f} s wall, {n / wall * 3600:.0f} games/hour')
    for g, w, s in out:
        print(f'  proc: {w:.0f} s; cpu {s["cpu"]:.0f}, net+legal {s["net"]:.0f}, engine {s["engine"]:.0f}')
    banks = [b for g, _, _ in out for _, b0, b1 in g for b in (b0, b1)]
    print(f'  mean bank {np.mean(banks):.0f}')


if __name__ == '__main__':
    main()

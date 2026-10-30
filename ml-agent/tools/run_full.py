"""Full paired games. PYTHONHASHSEED=0; WORKERS=1/2; AGENT_MAIN/OPPONENT remain supported.
python tools/run_full.py TAG --players template,model:ranker-own-v1 --opponent METAV4.py
python tools/run_full.py TAG --audit
An omitted --players uses AGENT_MAIN (or the pinned template). Every game gets fresh policy state.
"""
import argparse
from collections import Counter, defaultdict
from multiprocessing import Pool
import gzip
import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from kagml.paths import models, runs
from kagml.preview import TemplatePlayer, pin_weeds
from compare_day import make_player
from check_opponents import Meter, SB


def save(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(json.dumps(value, separators=(',', ':')), encoding='utf8')
    tmp.replace(path)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def gameplay(replay):
    # The framework's wall-clock allowance is not game state.
    return digest([[{k: ({a: b for a, b in v.items() if a != 'remainingOverageTime'} if k == 'observation' else v)
                     for k, v in seat.items()} for seat in frame] for frame in replay['steps']])


def signature(player, opponent):
    paths = list((ROOT / 'src/kagml').glob('*.py')) + [Path(__file__), ROOT / 'tools/compare_day.py',
              ROOT / 'vendor/template_agent/main.py']
    paths += [Path(p) for p in (player.removeprefix('file:'), opponent) if Path(p).is_file()]
    if player.startswith('template:'):
        paths += list((ROOT / 'agents/template_switches').glob('*.py'))
    if player.startswith('model:'):
        paths += list((models() / player.split(':')[1]).glob('*'))
    return digest({str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths if p.is_file()})


class Handover:
    """handover:<day>:<player>: the player until the morning of <day>, then the teacher (fourth), fresh, to the end.
    The teacher's gain over the player's own game from the same seed measures what the player loses from <day> on."""

    def __init__(self, day, ours, seed):
        self.day, self.seed, self.ours, self.teacher = day, seed, actor(ours, seed), None

    def __call__(self, observation, configuration):
        if int(observation['day']) < self.day:
            return self.ours(observation, configuration)
        if self.teacher is None:
            self.teacher = actor('fourth', self.seed)
        return self.teacher(observation, configuration)

    def diagnostics(self):
        parts = [p.diagnostics() for p in (self.ours, self.teacher) if hasattr(p, 'diagnostics')]
        return {k: sum(d.get(k, 0) for d in parts) for k in ('fallbacks', 'search_errors')}


def actor(name, seed):
    if name.startswith('handover:'):
        _, day, ours = name.split(':', 2)
        return Handover(int(day), ours, seed)
    if name.startswith('file:') or Path(name).is_file():
        result = TemplatePlayer(name.removeprefix('file:'))
    else:
        result = make_player(name)
    if not callable(result):
        raise ValueError('Full games require a callable, not recorded actions')
    if hasattr(result, 'reset'):
        result.reset(seed)
    return result


class StrictMeter(Meter):
    def __init__(self, actor):
        super().__init__(actor)
        self.errors = []

    def __call__(self, observation, configuration):
        try:
            return self.checked(observation, configuration)
        except Exception as exc:
            self.errors.append({'step':observation['day']*24+observation['hour'],'error':repr(exc)})
            raise

    def checked(self, observation, configuration):
        result = super().__call__(observation, configuration)
        module = getattr(self.actor, 'module', None)
        errors = getattr(module, 'ERRORS', {})
        if errors.get('count', 0):
            raise RuntimeError(f'Policy fallback: {errors}')
        if hasattr(self.actor, 'diagnostics'):
            diagnostics = self.actor.diagnostics()
            if diagnostics.get('fallbacks') or diagnostics.get('search_errors'):
                raise RuntimeError(f'Policy fallback: {diagnostics}')
        if not isinstance(result, dict) or not isinstance(result.get('farmer'), list):
            raise ValueError('Missing farmer action')
        return result


def stem(player, seed, seat):
    label = ('file-' + Path(player[5:]).stem + '-' + digest(player)[:8]) if player.startswith('file:') else player.replace(':', '_')
    return f'{label}-{seed}-seat{seat}'


def one(job):
    root, name, opponent, seed, seat, expected = job
    root = Path(root)
    assert os.environ.get('PYTHONHASHSEED') == '0'
    assert signature(name, opponent) == expected, 'Sources changed during run'
    from kaggle_environments import make
    pin_weeds(True)
    ours, theirs = StrictMeter(actor(name, seed)), StrictMeter(actor(opponent, seed))
    ours.progress = str(root / f'progress-{os.getpid()}.json')
    env = make('kaggriculture', configuration={'episodeSteps': 720, 'seed': seed, 'actTimeout': 30,
                                               'runTimeout': 7200}, debug=False)
    start = time.perf_counter()
    env.run([ours, theirs] if seat == 0 else [theirs, ours])
    replay = env.toJSON()
    farms = replay['steps'][-1][0]['observation']['farms']
    shops = replay['steps'][144][0]['observation']['town']['unlocked_shops'][:2]
    result = dict(name=name, control='metav4', opponent=opponent, seed=seed, seat=seat, signature=expected,
                  banks=[farms[seat]['money'], farms[1-seat]['money']], steps=len(env.steps),
                  statuses=[s.status for s in env.state], early_shops=shops, buyers=sum(s in SB for s in shops),
                  seconds=time.perf_counter()-start, timing=ours.report(), opponent_timing=theirs.report(),
                  diagnostics={'fallbacks':0, 'search_errors':0}, gameplay_sha256=gameplay(replay),
                  policy_errors=ours.errors, opponent_errors=theirs.errors)
    result.update(margin=result['banks'][0]-result['banks'][1], win=result['banks'][0]>result['banks'][1],
                  tie=result['banks'][0]==result['banks'][1])
    target = root / stem(name, seed, seat)
    with gzip.open(str(target)+'.json.gz', 'wt', encoding='utf8', compresslevel=1) as f:
        json.dump(replay, f, separators=(',', ':'))
    save(Path(str(target)+'.metrics.json'), result)
    assert result['steps'] == 720 and result['statuses'] == ['DONE', 'DONE'], result
    assert result['timing']['turns'] == result['opponent_timing']['turns'] == 719, (name,seed,seat,ours.errors,theirs.errors)
    return {k:result[k] for k in ('name','seed','seat','banks','seconds')}


def verify(root, name, seed, seat, expected):
    path = root / stem(name, seed, seat)
    m = json.loads(Path(str(path)+'.metrics.json').read_text())
    with gzip.open(str(path)+'.json.gz', 'rt', encoding='utf8') as f:
        replay = json.load(f)
    assert (m['name'],m['seed'],m['seat'],m['signature']) == (name,seed,seat,expected), 'Identity/provenance'
    assert replay['info']['seed'] == seed and len(replay['steps']) == m['steps'] == 720
    assert [s['status'] for s in replay['steps'][-1]] == m['statuses'] == ['DONE','DONE']
    assert gameplay(replay) == m['gameplay_sha256'], 'Replay changed'
    for p, field in ((seat, 'timing'), (1-seat, 'opponent_timing')):
        daily = defaultdict(Counter)
        for step, frame in enumerate(replay['steps'][:-1]):
            obs = frame[p]['observation']
            assert obs['player'] == p and obs['day']*24+obs['hour'] == step
            action = replay['steps'][step+1][p]['action']
            assert isinstance(action,dict) and isinstance(action.get('farmer'),list)
            row = daily[obs['day']]; row['turns'] += 1
            for command in [action['farmer']] + list(action.get('hands') or []):
                if command and command[0] != 'PASS':
                    row['non_pass'] += 1; row['op_'+command[0]] += 1
            row['market_orders'] += len(action.get('market') or [])
        assert {str(k):dict(v) for k,v in daily.items()} == m[field]['daily']
        assert len(m[field]['turn_ms']) == m[field]['turns'] == 719
        assert all(t>=0 for t in m[field]['turn_ms'])
        assert sum(d['non_pass'] for d in daily.values())>0
    farms = replay['steps'][-1][0]['observation']['farms']
    assert m['banks'] == [farms[seat]['money'],farms[1-seat]['money']]
    assert m['margin'] == m['banks'][0]-m['banks'][1]
    assert m['win'] == (m['margin']>0) and m['tie'] == (m['margin']==0)
    shops = replay['steps'][144][0]['observation']['town']['unlocked_shops'][:2]
    assert m['early_shops'] == shops and m['buyers'] == sum(s in SB for s in shops)
    assert not any(m['diagnostics'].values())
    assert not m.get('policy_errors') and not m.get('opponent_errors'), 'Policy error'
    return m


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('tag'); ap.add_argument('--players')
    ap.add_argument('--opponent', default=os.environ.get('OPPONENT'))
    ap.add_argument('--seeds', default='20001-20024'); ap.add_argument('--seats', default='0,1')
    ap.add_argument('--workers', type=int, choices=range(1, 9), default=int(os.environ.get('WORKERS','2')))
    ap.add_argument('--audit', action='store_true')
    a = ap.parse_args()
    if os.environ.get('PYTHONHASHSEED') != '0': ap.error('Set PYTHONHASHSEED=0 before starting Python')
    if not 1 <= a.workers <= 8: ap.error('WORKERS must be 1-8')
    root = runs()/a.tag
    if a.audit:
        config = json.loads((root/'config.json').read_text())
        rows = [verify(root,n,s,p,config['signatures'][n]) for n in config['players']
                for s in config['seeds'] for p in config['seats']]
        scenarios=defaultdict(set)
        for r in rows: scenarios[r['seed']].add(tuple(r['early_shops']))
        assert all(len(v)==1 for v in scenarios.values())
        repeats=[]
        for n,s,p in config['repeat_jobs']:
            m=verify(root/'repeats',n,s,p,config['signatures'][n])
            original=next(r for r in rows if (r['name'],r['seed'],r['seat'])==(n,s,p))
            assert m['gameplay_sha256']==original['gameplay_sha256'], 'Repeat differs'
            repeats.append({'name':n,'seed':s,'seat':p,'gameplay_sha256':m['gameplay_sha256']})
        save(root/'checks.json',dict(accepted=len(rows),rejected=0,repeats=repeats,
             calls_per_game=719,hash_seed=0,workers=config['workers']))
        print(json.dumps({'accepted':len(rows),'repeats':len(repeats),'rejected':0})); return
    if not a.opponent: ap.error('--opponent or OPPONENT required')
    names=a.players.split(',') if a.players else ['file:'+str(Path(os.environ.get('AGENT_MAIN',ROOT/'vendor/template_agent/main.py')).resolve())]
    seeds=list(range(int(a.seeds.split('-')[0]),int(a.seeds.split('-')[1])+1)) if '-' in a.seeds else [int(s) for s in a.seeds.split(',')]
    seats=[int(s) for s in a.seats.split(',')]
    assert len(names)==len(set(names)) and len(seeds)==len(set(seeds))
    assert names and seeds and set(seats)<= {0,1} and len(seats)==len(set(seats))
    opponent=str(Path(a.opponent).resolve()) if Path(a.opponent).is_file() else a.opponent
    sigs={n:signature(n,opponent) for n in names}
    config=dict(players=names,seeds=seeds,seats=seats,opponent=opponent,signatures=sigs,workers=a.workers,isolation='fresh-process-per-game',
                repeat_jobs=[(names[0],seeds[0],seats[0]),(names[-1],seeds[-1],seats[-1])])
    root.mkdir(parents=True,exist_ok=True)
    if (root/'config.json').exists():
        assert json.loads((root/'config.json').read_text())==json.loads(json.dumps(config)), 'Tag already has another configuration'
    else: save(root/'config.json',config)
    jobs=[]
    for n in names:
        for s in seeds:
            for p in seats:
                if Path(str(root/stem(n,s,p))+'.metrics.json').exists(): verify(root,n,s,p,sigs[n])
                else: jobs.append((str(root),n,opponent,s,p,sigs[n]))
    start=time.perf_counter()
    with Pool(processes=a.workers, maxtasksperchild=1) as pool:
        for row in pool.imap(one,jobs): print(json.dumps(row),flush=True)
    repeat_root=root/'repeats'; repeat_root.mkdir(exist_ok=True)
    with Pool(processes=a.workers, maxtasksperchild=1) as pool:
        for row in pool.imap(one,[(str(repeat_root),n,opponent,s,p,sigs[n]) for n,s,p in config['repeat_jobs']]):
            print('REPEAT '+json.dumps(row),flush=True)
    save(root/'run.json',{'seconds':time.perf_counter()-start,'new_games':len(jobs),'repeat_games':2})
    print('RUN COMPLETE',flush=True)


if __name__=='__main__': main()

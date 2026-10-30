"""Swap test (Claude, 2026-10-29): is the remaining gap in our market orders or in our worker moves?

For each source game (seat 0) and day, from the recorded morning, opponent on tape, four branches play to dawn:
  B   our player;  T   the teacher;
  MT  our workers + the teacher's market orders;  WT  the teacher's workers + our market orders.
In MT/WT both policies see every real observation and the executed action mixes their answers. The teacher plans
workers and market together, so the split is approximate. A fresh teacher then plays every branch to the end
(regret_map.teacher_to_end). Rows: final margin of T, MT, WT minus B, and their market/work differences against B.

python tools/swap_test.py --source DIR --player net:board-p5:market:overflow:endmask:endwork --out runs/swap-test
"""
import argparse
import copy
import csv
import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from shadow_labels import ROOT, source, player_instance, warm_memories, valid_action
from takeover_labels import generate
from regret_map import ours_day, teacher_to_end, work
from kagml.preview import env_from_snapshot, pin_weeds, snapshot_from_replay


def mixed_day(path, day, name, teacher, side):
    """side 'market': our workers, the teacher's market orders. side 'workers': the teacher's workers, our orders."""
    from shadow_compat import overflow_guard
    recorded, _ = source(path)
    player, _ = player_instance(name)
    player.restore(copy.deepcopy(warm_memories(path, name)[day]))
    teacher.reset(int(recorded['info']['seed']))
    pin_weeds(True)
    start = day * 24
    env = env_from_snapshot(snapshot_from_replay(recorded, start))
    policy, events = teacher.play.POL, []
    original = policy.night_room_value
    policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)
    try:
        for offset in range(24):
            obs = env.state[0].observation
            ours = copy.deepcopy(player(copy.deepcopy(obs), env.configuration))
            theirs = copy.deepcopy(teacher(copy.deepcopy(obs), env.configuration))
            act = ours if side == 'market' else theirs
            act['market'] = (theirs if side == 'market' else ours).get('market') or []
            valid_action(act)
            env.step([act, copy.deepcopy(recorded['steps'][start + offset + 1][1]['action'])])
    finally:
        policy.night_room_value = original
    return env.toJSON()['steps'][start:], len(teacher.diagnostics().get('fallbacks') or [])


def one(job):
    path, day, name = job
    path = Path(path)
    recorded, _ = source(path)
    from kagml.opponents import load
    teacher = load('fourth')
    t0, end = time.perf_counter(), day * 24 + 24
    b = ours_day(path, day, name)
    fb = teacher_to_end(recorded, b[-1], end, teacher)
    t = generate(recorded, path.stem, day, 0, name, teacher)[0]['steps']
    row = dict(game=path.stem, day=day)
    jo, oo = work(b, 0)
    for tag, steps, fallbacks in [('T', t, 0), ('MT', *mixed_day(path, day, name, teacher, 'market')),
                                  ('WT', *mixed_day(path, day, name, teacher, 'workers'))]:
        f = teacher_to_end(recorded, steps[-1], end, teacher)
        row.update({f'{tag}_margin': (f[0] - f[1]) - (fb[0] - fb[1]), f'{tag}_ours': f[0] - fb[0],
                    f'{tag}_opp': f[1] - fb[1], f'{tag}_fallbacks': fallbacks})
        jx, ox = work(steps, 0)
        for k in set(ox) | set(oo):
            row[f'{tag}_m_{k}'] = ox[k] - oo[k]
        for k in set(jx) | set(jo):
            row[f'{tag}_w_{k}'] = jx[k] - jo[k]
    return dict(row=row, seconds=time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--player', required=True)
    ap.add_argument('--out', default='runs/swap-test')
    ap.add_argument('--workers', type=int, choices=range(1, 9), default=8)
    ap.add_argument('--days', default='6,10,14,18,22,26')
    ap.add_argument('--games', type=int, default=0, help='first N games only (smoke)')
    a = ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED') == '0'
    paths = sorted(a.source.glob('*.json'))[:a.games or None]
    days = [int(d) for d in a.days.split(',')]
    jobs = [(str(p), d, a.player) for p in paths for d in days]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows, t = [], time.perf_counter()
    with ProcessPoolExecutor(a.workers) as pool:          # chunks of one game keep warm_memories cached
        for i, r in enumerate(pool.map(one, jobs, chunksize=len(days))):
            rows.append(r['row'])
            if (i + 1) % 12 == 0 or i + 1 == len(jobs):
                print(json.dumps(dict(jobs=i + 1, total=len(jobs), seconds=round(time.perf_counter() - t))), flush=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: ('_m_' in k or '_w_' in k, k))
    with (out / 'rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, restval=0)
        w.writeheader()
        w.writerows(rows)
    (out / 'run.json').write_text(json.dumps(dict(player=a.player, source=str(a.source), games=len(paths), days=days,
                                                  rows=len(rows), seconds=time.perf_counter() - t)))
    print('DONE', len(rows), 'rows', round(time.perf_counter() - t), 's')


if __name__ == '__main__':
    main()

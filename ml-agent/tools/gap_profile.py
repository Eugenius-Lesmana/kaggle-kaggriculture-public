"""Day-by-day profile of full games: money, work done and farm layout, for our seat and the opponent's.

python tools/gap_profile.py OUT.csv RUN[:PLAYER] [RUN[:PLAYER] ...]

RUN as in market_compete.py (run_full folders, or folders below them; games paired by seed and seat). Each game is
re-simulated by the replay extractor. Per game, side (ours / opponent) and day: revenue, spending (market buys and
hires), workers that acted, effective worker jobs by type, idle unit-turns, and the farm at dawn (tiles by kind, crops, animals,
land quadrants, mean distance of crop and animal tiles to the nearest shed-side tile). Prints means per game by day
band for each run.
"""
import csv
import gzip
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

from kagml.paths import runs
from kagml.preview import pin_weeds
from kagml.replay_tables import replay
from kagml.work_features import SHED_TILES, dist

JOBS = ('PLANT', 'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'CARE', 'COLLECT_FERTILIZER', 'BUILD_COOP', 'BUILD_PASTURE',
        'DIG', 'PICKUP', 'PLACE')
BANDS = ((6, 11), (12, 17), (18, 23), (24, 29))


def games(spec):
    run, _, player = spec.partition(':')
    folder = Path(run) if Path(run).exists() else runs() / run
    for path in sorted(folder.rglob('*.metrics.json')):
        if 'repeats' in path.parts:
            continue
        m = json.loads(path.read_text())
        if not player or m['name'] == player:
            yield spec, m, Path(str(path)[:-len('.metrics.json')] + '.json.gz')


def profile(label, m, path):
    with gzip.open(path, 'rt', encoding='utf8') as f:
        rep = json.load(f)
    seat = m['seat']
    banks = [m['banks'][0], m['banks'][1]] if seat == 0 else [m['banks'][1], m['banks'][0]]
    meta = {'episode': m['seed'], 'created': '', **{f'{k}_{p}': -1 for k in ('sub', 'team', 'rating') for p in (0, 1)},
            **{f'reward_{p}': banks[p] for p in (0, 1)}}
    pin_weeds(True)
    rows, info = replay(rep, meta, 'native')
    if rows is None:
        raise RuntimeError(f'{path}: {info}')
    out = defaultdict(Counter)
    side = lambda s: 'ours' if s == seat else 'opponent'
    for r in rows['sales']:
        out[(side(r['seat']), r['step'] // 24)]['revenue'] += r['revenue']
    for r in rows['market_orders']:
        if r['took_effect'] and r['cash_delta'] < 0:
            out[(side(r['seat']), r['step'] // 24)]['spend'] -= r['cash_delta']
    units = defaultdict(set)
    for r in rows['unit_actions']:
        units[(side(r['seat']), r['step'] // 24)].add(r['unit'])
        o = out[(side(r['seat']), r['step'] // 24)]
        op = json.loads(r['effective_command'])[0] if r['effective_command'] else 'PASS'
        if not r['took_effect']:
            o['idle'] += 1
        elif op in JOBS:
            o[f'job_{op.lower()}'] += 1
        else:
            o['moves'] += 1
    for r in rows['farm_daily']:
        o = out[(side(r['seat']), r['day'])]
        if (r['x'], r['y']) == (0, 0):
            o['land'] += len(json.loads(r['land'])) if r['land'] else 0
        o[f"tile_{str(r['kind']).lower()}"] += 1
        d = min(dist((r['x'], r['y']), s) for s in SHED_TILES)
        if r['crop']:
            o[f"crop_{r['crop'].lower()}"] += 1; o['crop_tiles'] += 1; o['crop_dist'] += d
        if r['animal']:
            o[f"animal_{r['animal'].lower()}"] += 1; o['animal_tiles'] += 1; o['animal_dist'] += d
    for key, u in units.items():
        out[key]['workers'] = len(u)
    return [{'run': label, 'seed': m['seed'], 'seat': seat, 'side': s, 'day': day, **o} for (s, day), o in out.items()]


def main():
    target, specs = Path(sys.argv[1]), sys.argv[2:]
    rows = [row for spec in specs for label, m, path in games(spec) for row in profile(label, m, path)]
    keys = sorted({k for r in rows for k in r} - {'run', 'seed', 'seat', 'side', 'day'})
    with target.open('w', newline='') as f:
        w = csv.DictWriter(f, ['run', 'seed', 'seat', 'side', 'day'] + keys, restval=0); w.writeheader(); w.writerows(rows)
    common = set.intersection(*({(r['seed'], r['seat']) for r in rows if r['run'] == s} for s in specs))
    n = len(common)
    agg = defaultdict(Counter)
    for r in rows:
        if (r['seed'], r['seat']) in common:
            b = next((f'{a}-{z}' for a, z in BANDS if a <= r['day'] <= z), None)
            if b:
                agg[(r['run'], r['side'], b)].update({k: v for k, v in r.items() if k in keys})
    print(f'{n} paired games; per game, summed over the band (tiles, animals, workers: per day)')
    for s in ('ours', 'opponent'):
        for k in keys:
            if k.endswith('_dist'):
                continue
            cells = []
            for spec in specs:
                for a, z in BANDS:
                    c = agg[(spec, s, f'{a}-{z}')]
                    v = c[k] / n / (z - a + 1 if k.startswith(('tile_', 'crop_', 'animal_', 'workers', 'land')) else 1)
                    cells.append(f'{v:8.1f}')
                cells.append('|')
            print(f'{s:8s} {k:24s} ' + ' '.join(cells))
        for spec in specs:
            for kind in ('crop', 'animal'):
                dists = [agg[(spec, s, f'{a}-{z}')] for a, z in BANDS]
                print(f'{s:8s} {kind}_dist {spec:40s} ' + ' '.join(f"{c[kind + '_dist'] / c[kind + '_tiles'] if c[kind + '_tiles'] else 0:6.2f}" for c in dists))
    print('columns: days ' + ' '.join(f'{a}-{z}' for a, z in BANDS) + ' per run: ' + ', '.join(specs))


if __name__ == '__main__':
    main()

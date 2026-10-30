"""Who sells what into the shared market, at what price: our player against the opponent, for full-game runs.

python tools/market_compete.py OUT.csv RUN[:PLAYER] [RUN[:PLAYER] ...]

Each RUN is a run_full folder (games paired by seed and seat across runs). Every game is re-simulated by the replay
extractor (exact sales with the price of each unit sold, orders and the shared market's prices), then summed per
game, side (ours / opponent), product and day band: units sold, revenue, average price received, units bought and
money spent. Writes the per-game rows to OUT.csv and prints the mean per game for each run, by product, on games
present in every run.
"""
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

from kagml.paths import runs
from kagml.preview import pin_weeds
from kagml.replay_tables import replay

BANDS = ((0, 5), (6, 11), (12, 17), (18, 23), (24, 29))
band = lambda day: next(f'{a}-{b}' for a, b in BANDS if a <= day <= b)


def games(spec):
    run, _, player = spec.partition(':')
    folder = Path(run) if Path(run).exists() else runs() / run
    for path in sorted(folder.glob('*.metrics.json')):
        m = json.loads(path.read_text())
        if not player or m['name'] == player:
            yield folder.name, m, Path(str(path)[:-len('.metrics.json')] + '.json.gz')


def summarise(label, m, path):
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
    out = defaultdict(lambda: defaultdict(float))
    side = lambda s: 'ours' if s == seat else 'opponent'
    for r in rows['sales']:
        o = out[(side(r['seat']), r['product'], band(r['step'] // 24))]
        o['sold'] += r['units']; o['revenue'] += r['revenue']
    for r in rows['market_orders']:
        op, item, *_ = json.loads(r['command']) + [None, None]
        if op and op.startswith('BUY') and r['took_effect']:  # empty orders [] are recorded too
            o = out[(side(r['seat']), f'{op}:{item}' if item else op, band(r['step'] // 24))]
            o['bought'] += r['units']; o['spent'] -= r['cash_delta']
    return [{'run': label, 'player': m['name'], 'seed': m['seed'], 'seat': seat, 'bank_ours': m['banks'][0],
             'bank_opponent': m['banks'][1], 'side': s, 'item': item, 'days': d, **{k: v for k, v in o.items()}}
            for (s, item, d), o in out.items()]


def main():
    target, specs = Path(sys.argv[1]), sys.argv[2:]
    rows = [row for spec in specs for label, m, path in games(spec) for row in summarise(label, m, path)]
    keys = ['run', 'player', 'seed', 'seat', 'bank_ours', 'bank_opponent', 'side', 'item', 'days',
            'sold', 'revenue', 'bought', 'spent']
    with target.open('w', newline='') as f:
        w = csv.DictWriter(f, keys); w.writeheader(); w.writerows(rows)
    labels = list(dict.fromkeys(r['run'] for r in rows))
    common = set.intersection(*({(r['seed'], r['seat']) for r in rows if r['run'] == l} for l in labels))
    total = defaultdict(float)
    for r in rows:
        if (r['seed'], r['seat']) in common:
            for k in ('sold', 'revenue', 'bought', 'spent'):
                total[(r['run'], r['side'], r['item'], k)] += r.get(k) or 0
    n = len(common)
    print(f'{n} paired games; mean per game. units sold, revenue, avg price | bought, spent')
    for s in ('ours', 'opponent'):
        for item in sorted({k[2] for k in total}):
            cells = []
            for l in labels:
                sold, rev = total[(l, s, item, 'sold')] / n, total[(l, s, item, 'revenue')] / n
                bought, spent = total[(l, s, item, 'bought')] / n, total[(l, s, item, 'spent')] / n
                cells.append(f'{sold:6.0f} {rev:7.0f} {rev / sold if sold else 0:5.0f} | {bought:5.0f} {spent:6.0f}')
            if any(total[(l, s, item, k)] for l in labels for k in ('sold', 'bought')):
                print(f'{s:8s} {item:22s} ' + '   '.join(cells))
    print('runs: ' + ', '.join(labels))


if __name__ == '__main__':
    main()

"""Sell diagnosis (Claude, 2026-10-30): why does our player earn less from what it sells?

python tools/sell_diagnosis.py OUT_DIR RUN_A RUN_B [--workers 5]

Every game of the two run_full folders is re-simulated with the replay extractor (exact price of every unit sold).
For each game, side (ours / opponent) and product it records:
  units, revenue, mean received price; mean quoted price at the start of the sale step (market level);
  own-step impact (quote minus received); units at a near-worthless price (<= 25% of base); units sold on day 29;
  units left in our shed at the end (worth nothing: the final score is money); mean hold hours (FIFO from shed arrival);
  units sold within 1 hour after a shop pull of that product;
  ceiling_4h / _24h / _any: the most our own volume could have earned with the best timing, each unit sold within 4 h /
  24 h of its release (or by its actual sale if later) or any time (exact price curve, release times from shed arrivals, opponent sales, shop pulls and our product buys held fixed; shed capacity ignored; lots of 1/200 of
  the volume).
Also writes OUT_DIR/sales.csv: one row per sale (seat, product, step, units, received price, start-of-step quote, hours
since the last shop pull of that product). --no-ceiling skips the slow ceiling step.
Games are paired by seed and seat. Writes OUT_DIR/rows.csv.
"""
import argparse
import csv
import gzip
import json
import math
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np

PRODUCTS = ["WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER"]


def ceiling(B, release, n, price, window=None, sale=None):
    """Max revenue from selling n units, unit j released at step release[j] (sorted); price(inv) exact.
    B[t]: market inventory before step t without our sales. Units are grouped in lots of g (the last may be smaller)."""
    if n == 0:
        return 0.0
    g = max(1, math.ceil(n / 200))
    edges = np.minimum(np.arange(1, math.ceil(n / g) + 1) * g, n)        # units sold after each lot
    lots = len(edges)
    lot_rel = np.array([release[e - 1] for e in edges])
    # with a window, each lot must be sold within `window` steps of its release, or by its actual sale if later
    need = (np.searchsorted(np.sort(np.maximum(lot_rel + window, [sale[e - 1] for e in edges])), np.arange(len(B)), side='left')
            if window is not None else np.zeros(len(B), dtype=int))
    avail = np.searchsorted(lot_rel, np.arange(len(B)), side='right')
    starts = np.concatenate([[0], edges])
    dp = np.full(lots + 1, -np.inf); dp[0] = 0.0
    for t in range(len(B)):
        a = int(avail[t])
        if a == 0:
            continue
        new = dp.copy()
        for j in range(a):
            if dp[j] == -np.inf:
                continue
            cum = np.cumsum(price(B[t] + np.arange(starts[j], edges[a - 1])))
            cand = dp[j] + cum[edges[j:a] - starts[j] - 1]
            new[j + 1:a + 1] = np.maximum(new[j + 1:a + 1], cand)
        new[:min(int(need[t]), lots + 1)] = -np.inf
        dp = new
    return float(dp[lots])


def analyse(job):
    import sys
    sys.path.insert(0, 'src')
    from kagml.preview import pin_weeds
    from kagml.replay_tables import replay
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    label, mpath, do_ceiling = job
    m = json.loads(Path(mpath).read_text())
    with gzip.open(mpath[:-len('.metrics.json')] + '.json.gz', 'rt', encoding='utf8') as f:
        rep = json.load(f)
    seat = m['seat']
    banks = [m['banks'][0], m['banks'][1]] if seat == 0 else [m['banks'][1], m['banks'][0]]
    meta = {'episode': m['seed'], 'created': '', **{f'{k}_{p}': -1 for k in ('sub', 'team', 'rating') for p in (0, 1)},
            **{f'reward_{p}': banks[p] for p in (0, 1)}}
    pin_weeds(True)
    rows, info = replay(rep, meta, 'native')
    if rows is None:
        raise RuntimeError(f'{mpath}: {info}')
    ms = {r['step']: r for r in rows['market_steps']}
    T = max(ms) + 1
    inv = {p: np.array([ms[t][f'inventory_{p.lower()}'] for t in range(T)]) for p in PRODUCTS}
    quote = {p: np.array([ms[t][f'price_{p.lower()}'] for t in range(T)]) for p in PRODUCTS}
    sold = {(s, p): np.zeros(T, dtype=int) for s in (0, 1) for p in PRODUCTS}
    soldrev = defaultdict(float); low = defaultdict(int)
    for r in rows['sales']:
        sold[(r['seat'], r['product'])][r['step']] += r['units']
        soldrev[(r['seat'], r['product'])] += r['revenue']
        if r['price'] <= 0.25 * K.MARKET_PARAMS[r['product']]['base']:
            low[(r['seat'], r['product'])] += r['units']
    bought = {p: np.zeros(T, dtype=int) for p in PRODUCTS}
    for r in rows['market_orders']:
        c = json.loads(r['command'])
        if c and c[0] == 'BUY_PRODUCT' and r['took_effect']:
            bought[c[1]][r['step']] += r['units']
    # shop pulls of p: inventory drop between t and t+1 not explained by orders
    pull = {}
    for p in PRODUCTS:
        d = np.zeros(T, dtype=int)
        for t in range(T - 1):
            d[t] = (inv[p][t] + sold[(0, p)][t] + sold[(1, p)][t] - bought[p][t]) - inv[p][t + 1]
        pull[p] = d                                         # >0: consumed by town between t and t+1
    out = []; sale_rows = []
    since = {}
    for p in PRODUCTS:                                       # hours since the last pull ended (1 = right after a pull)
        h = np.full(T, 10 ** 6, dtype=int)
        for t in range(1, T):
            h[t] = 1 if pull[p][t - 1] > 0 else h[t - 1] + 1
        since[p] = h
    for r in rows['sales']:
        p, t = r['product'], r['step']
        sale_rows.append(dict(run=label, seed=m['seed'], seat=seat, side='ours' if r['seat'] == seat else 'opponent', product=p,
                              step=t, units=r['units'], price=r['price'], quote=int(quote[p][t]), since_pull=int(since[p][t])))
    for s in (0, 1):
        side = 'ours' if s == seat else 'opponent'
        shed = {p: np.array([rep['steps'][t][s]['observation']['private']['shed'].get(p, 0) for t in range(T)]) for p in PRODUCTS}
        for p in PRODUCTS:
            u = sold[(s, p)]
            n = int(u.sum())
            par = K.MARKET_PARAMS[p]
            row = dict(run=label, seed=m['seed'], seat=seat, side=side, product=p, units=n, revenue=soldrev[(s, p)],
                       low_units=low[(s, p)], day29_units=int(u[29 * 24:].sum()), left_end=int(shed[p][-1]),
                       left_value=float(shed[p][-1] * quote[p][-1]))
            # quoted (start-of-step) price weighted by units, and units right after a pull
            row['quote_rev'] = float((u * quote[p]).sum())
            after = np.zeros(T, dtype=bool)
            for t in range(T - 1):
                if pull[p][t] > 0:
                    after[t + 1] = True
            row['after_pull_units'] = int(u[after].sum())
            # FIFO hold hours from shed arrival
            arrivals = []
            for t in range(T - 1):
                a = shed[p][t + 1] - shed[p][t] + u[t]
                arrivals += [t + 1] * max(0, int(a))
            arrivals = [0] * int(shed[p][0]) + arrivals
            sale_steps = [t for t in range(T) for _ in range(u[t])]
            rel = sorted(min(a, b) for a, b in zip(arrivals + [10 ** 9] * n, sale_steps)) if n else []
            row['hold_hours'] = float(np.mean([b - a for a, b in zip(rel, sale_steps)])) if n else 0.0
            if side == 'ours' and do_ceiling:
                B = inv[p] - (np.cumsum(u) - u)                  # inventory before step t without our sales
                lo = int(B.min()); P = np.array([K.market_price(p, v) for v in range(lo, int(B.max()) + n + 1)], dtype=float)
                price = lambda x, P=P, lo=lo: P[np.asarray(x, dtype=int) - lo]
                for w, key in ((4, 'ceiling_4h'), (24, 'ceiling_24h'), (None, 'ceiling_any')):
                    row[key] = ceiling(B, rel, n, price, w, sale_steps) if n else 0.0
            out.append(row)
    return out, sale_rows


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('out', type=Path)
    ap.add_argument('runs', nargs=2)
    ap.add_argument('--workers', type=int, default=5, choices=range(1, 9))
    ap.add_argument('--no-ceiling', action='store_true')
    a = ap.parse_args()
    root = Path('kaggriculture-ml-data/runs')
    jobs = [(r, str(f), not a.no_ceiling) for r in a.runs for f in sorted((root / r).glob('*.metrics.json'))]
    with ProcessPoolExecutor(a.workers) as pool:
        res = list(pool.map(analyse, jobs))
    a.out.mkdir(parents=True, exist_ok=True)
    for name, rows in (('rows.csv', [x for r, _ in res for x in r]), ('sales.csv', [x for _, s in res for x in s])):
        keys = list(dict.fromkeys(k for r in rows for k in r))
        with (a.out / name).open('w', newline='') as f:
            w = csv.DictWriter(f, keys, restval=''); w.writeheader(); w.writerows(rows)
    print('rows', len(rows), 'games', len(jobs))


if __name__ == '__main__':
    main()

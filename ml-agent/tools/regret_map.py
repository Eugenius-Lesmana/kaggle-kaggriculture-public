"""Regret map (Claude, 2026-10-28): where in a day do our decisions lose money, and on what?

For each source game (seat 0) and day d in 6-28, from the recorded morning, with the opponent replaying its recorded
actions (tape):
  B    = our player plays the whole day;
  A(h) = our player plays h hours, then the teacher (fresh) plays to dawn, h in HOURS.
Both are valued the next morning. regret(h) = value(A(h)) - value(B): what our play from hour h to dawn costs,
given that the teacher plays instead. With --to-end, a fresh teacher then plays both branches from that dawn to the
end of the game (opponent on tape) and `final` = difference in final banks: money, no valuation needed. Rows also hold the situation at hour h and the teacher's and our work counts.

python tools/regret_map.py --source DIR --player net:board-p4:market:overflow:endmask:endwork --out runs/regret-map
"""
import argparse
import copy
import csv
import json
import os
import time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from shadow_labels import ROOT, source, player_instance, warm_memories, valid_action
from takeover_labels import generate
from kagml.preview import TemplatePlayer, env_from_snapshot, pin_weeds, snapshot_from_replay

HOURS = (0, 4, 8, 12, 16, 20)
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}          # engine ANIMALS / CROPS / LAND_PRICES
SEED = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
LAND_PRICES = (1000, 2000, 4000)
WORK = ("WATER", "HARVEST", "FEED", "CARE", "FERTILIZE", "COLLECT_FERTILIZER", "PLANT", "DIG", "PICKUP", "PLACE",
        "DROP", "BUILD_COOP", "BUILD_PASTURE", "PASS")


def ours_day(path, day, name):
    """Our player from the recorded morning of `day` to the next dawn, opponent on tape (as takeover_labels)."""
    recorded, _ = source(path)
    player, _ = player_instance(name)
    assert isinstance(player, TemplatePlayer)
    player.restore(copy.deepcopy(warm_memories(path, name)[day]))
    pin_weeds(True)
    start = day * 24
    env = env_from_snapshot(snapshot_from_replay(recorded, start))
    for offset in range(24):
        action = copy.deepcopy(player(copy.deepcopy(env.state[0].observation), env.configuration))
        valid_action(action)
        env.step([action, copy.deepcopy(recorded['steps'][start + offset + 1][1]['action'])])
    return env.toJSON()['steps'][start:]


def liquidation(units, market):
    """What `units` {product: n} fetch sold one by one into the market (price falls per unit sold, engine rule)."""
    from kaggle_environments.envs.kaggriculture.kaggriculture import market_price
    total = 0
    for p, n in units.items():
        inv = market['inventory'][p]
        for _ in range(int(n)):
            price = market_price(p, inv, market.get('params'))
            total += price
            inv += price > 1
    return total


def value(frame):
    """Next-morning value of seat 0. total: cash + all goods (shed, ripe crop and animal yield) at what they fetch
    sold unit by unit into that morning's market + unripe plants at seed cost + animals and land at purchase cost.
    total_mark: the same with goods at the quoted price (overvalues holding stock)."""
    obs = frame[0]['observation']
    prices, farm, shed = obs['market']['prices'], obs['farms'][0], obs['private']['shed']
    stock = sum(shed.get(p, 0) * prices[p] for p in PRODUCTS)
    crops = animals = 0
    tiles = Counter()
    for row in farm['tiles']:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get('kind') == 'PLANT':
                crops += t.get('yield_units', 0) * prices[t['crop']] or SEED[t['crop']]
                tiles[t['crop']] += 1
            elif t.get('animal'):
                animals += t.get('yield_units', 0) * prices[ANIMAL_PRODUCT[t['animal']]] + ANIMAL_COST[t['animal']]
                tiles[t['animal']] += 1
    goods = Counter({p: shed.get(p, 0) for p in PRODUCTS})
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict) and t.get('yield_units', 0) > 0 and (t.get('kind') == 'PLANT' or t.get('animal')):
                goods[t['crop'] if t.get('kind') == 'PLANT' else ANIMAL_PRODUCT[t['animal']]] += t['yield_units']
    marked = stock + sum(t.get('yield_units', 0) * prices[t['crop'] if t.get('kind') == 'PLANT' else ANIMAL_PRODUCT[t['animal']]]
                         for row in farm['tiles'] for t in row if isinstance(t, dict) and (t.get('kind') == 'PLANT' or t.get('animal')))
    goods_value = liquidation(goods, obs['market'])
    cash = farm['money']
    locked = sum(t == 'LOCKED' for row in farm['tiles'] for t in row) // 25
    land = sum(LAND_PRICES[:3 - locked])
    holdings = crops + animals + stock - marked          # unripe plants at seed cost, animals at cost
    return dict(cash=cash, stock=stock, crops=crops, animals=animals, land=land, goods=goods_value,
                total_mark=cash + stock + crops + animals + land,
                total=cash + goods_value + holdings + land,
                opp_cash=obs['farms'][1]['money']), tiles


def situation(frame):
    obs = frame[0]['observation']
    farm, private = obs['farms'][0], obs['private']
    count = Counter()
    for row in farm['tiles']:
        for t in row:
            if isinstance(t, dict):
                count[t.get('animal') or (t['crop'] if t.get('kind') == 'PLANT' else t.get('kind'))] += 1
            elif t is None:
                count['EMPTY'] += 1
    return dict(cash=farm['money'], shed=sum(private['shed'].values()),
                bags=sum(sum(b.values()) for b in private['inventories']), units=len(farm['hands']) + 1,
                cows=count['COW'], sheep=count['SHEEP'], geese=count['GOOSE'], empty=count['EMPTY'],
                **{c.lower(): count[c] for c in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")})


def work(steps, frm):
    """Effective-or-not work counts and market orders by seat 0 from frame index `frm` on."""
    jobs, orders = Counter(), Counter()
    for f in steps[frm + 1:]:
        a = f[0]['action'] or {}
        for c in [a.get('farmer') or ['PASS'], *(a.get('hands') or [])]:
            if c and c[0] in WORK:
                jobs[c[0] if c[0] != 'PLANT' else 'PLANT_' + c[1]] += 1
        for o in a.get('market') or []:
            if o and o[0] in ('BUY_ANIMAL', 'BUY_SEED', 'BUY_LAND', 'HIRE'):
                orders[o[0] + ('_' + o[1] if len(o) > 1 else '')] += int(o[2]) if len(o) > 2 else 1
            elif o and o[0] == 'SELL':
                orders['SELL_' + o[1]] += int(o[2])
            elif o and o[0] == 'BUY_PRODUCT':
                orders['BUYP_' + o[1]] += int(o[2])
    return jobs, orders


def first_moves(steps, h):
    a = steps[h + 1][0]['action'] or {}
    return [c[0] if c else 'PASS' for c in [a.get('farmer') or ['PASS'], *(a.get('hands') or [])]]


def teacher_to_end(recorded, frame, step, teacher):
    """From the dawn `frame` (at `step`), a fresh teacher plays to the end of the game, opponent on tape.
    Returns the final banks [ours, opponent]."""
    from shadow_compat import overflow_guard
    teacher.reset(int(recorded['info']['seed']))
    pin_weeds(True)
    env = env_from_snapshot(dict(seed=int(recorded['info']['seed']), step=step,
                                 obs=[copy.deepcopy(s['observation']) for s in frame]))
    policy, events = teacher.play.POL, []
    original = policy.night_room_value
    policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)
    try:
        for t in range(step, len(recorded['steps']) - 1):
            action = copy.deepcopy(teacher(copy.deepcopy(env.state[0].observation), env.configuration))
            valid_action(action)
            env.step([action, copy.deepcopy(recorded['steps'][t + 1][1]['action'])])
    finally:
        policy.night_room_value = original
    d = teacher.diagnostics()
    assert not d['fallbacks'] and not d['search_errors'], d
    return [f['money'] for f in env.state[0].observation['farms']]


def one(job):
    path, day, name, hours, to_end = job
    path = Path(path)
    recorded, _ = source(path)
    from kagml.opponents import load
    teacher = load('fourth')
    t0 = time.perf_counter()
    b = ours_day(path, day, name)
    vb, tb = value(b[-1])
    if to_end:
        fb = teacher_to_end(recorded, b[-1], day * 24 + 24, teacher)
    rows = []
    for h in hours:
        rep, _ = generate(recorded, path.stem, day, h, name, teacher, (b, []) if h else None)
        a = rep['steps']
        assert len(a) == len(b) and a[h] == b[h] if h else True
        va, ta = value(a[-1])
        jo, oo = work(b, h)
        jt, ot = work(a, h)
        ours_first, teacher_first = first_moves(b, h), first_moves(a, h)
        row = dict(game=path.stem, day=day, H=h, regret=va['total'] - vb['total'], regret_mark=va['total_mark'] - vb['total_mark'],
                   regret_margin=(va['total'] - va['opp_cash']) - (vb['total'] - vb['opp_cash']),
                   **{f'd_{k}': va[k] - vb[k] for k in ('cash', 'goods', 'stock', 'crops', 'animals', 'land', 'opp_cash')},
                   first_diff=sum(x != y for x, y in zip(ours_first, teacher_first)),
                   **{f's_{k}': v for k, v in situation(b[h]).items()})
        for k in sorted(set(jo) | set(jt)):
            row[f'w_{k}'] = jt[k] - jo[k]
        for k in sorted(set(oo) | set(ot)):
            row[f'm_{k}'] = ot[k] - oo[k]
        for k in sorted(set(ta) | set(tb)):
            row[f't_{k}'] = ta[k] - tb[k]
        if to_end:
            fa = teacher_to_end(recorded, a[-1], day * 24 + 24, teacher)
            row.update(final=fa[0] - fb[0], final_opp=fa[1] - fb[1], final_margin=(fa[0] - fa[1]) - (fb[0] - fb[1]))
        rows.append(row)
    return dict(rows=rows, seconds=time.perf_counter() - t0)


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--player', required=True)
    ap.add_argument('--out', default='runs/regret-map')
    ap.add_argument('--workers', type=int, choices=range(1, 9), default=8)
    ap.add_argument('--days', default='6-28')
    ap.add_argument('--day-step', type=int, default=1)
    ap.add_argument('--games', type=int, default=0, help='first N games only (smoke)')
    ap.add_argument('--hours', default=','.join(map(str, HOURS)))
    ap.add_argument('--to-end', action='store_true', help='then the teacher plays both branches to the end; final banks')
    a = ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED') == '0'
    lo, hi = map(int, a.days.split('-'))
    paths = sorted(a.source.glob('*.json'))[:a.games or None]
    hours = tuple(int(h) for h in a.hours.split(','))
    jobs = [(str(p), d, a.player, hours, a.to_end) for p in paths for d in range(lo, hi + 1, a.day_step)]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    rows, t = [], time.perf_counter()
    with ProcessPoolExecutor(a.workers) as pool:          # chunks of one game keep warm_memories cached
        for i, r in enumerate(pool.map(one, jobs, chunksize=len(range(lo, hi + 1, a.day_step)))):
            rows += r['rows']
            if (i + 1) % 12 == 0:
                print(json.dumps(dict(jobs=i + 1, total=len(jobs), seconds=round(time.perf_counter() - t))), flush=True)
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k[:2] in ('w_', 'm_', 't_'), k))
    with (out / 'rows.csv').open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=keys, restval=0)
        w.writeheader()
        w.writerows(rows)
    (out / 'run.json').write_text(json.dumps(dict(player=a.player, source=str(a.source), games=len(paths),
                                                  days=a.days, day_step=a.day_step, hours=hours, to_end=a.to_end, rows=len(rows),
                                                  seconds=time.perf_counter() - t)))
    print('DONE', len(rows), 'rows', round(time.perf_counter() - t), 's')


if __name__ == '__main__':
    main()

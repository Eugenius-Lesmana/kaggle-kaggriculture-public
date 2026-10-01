"""Extract top-agent worker routes and test route medoids and local action rules.

Run from the repository root: python evaluation/backbones/analyze.py
Outputs are compact CSV tables; no replay JSON is copied.
"""
import csv
import gzip
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path('research/intake/replays')
OUT = Path('evaluation/backbones')
WORK = {'WATER', 'HARVEST', 'PLANT', 'FEED', 'CARE', 'COLLECT_FERTILIZER',
        'FERTILIZE', 'DIG', 'BUILD_COOP', 'BUILD_PASTURE', 'PLACE'}
MOVE = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
SHOPS = {
    'wool': {'YARN_STORE'},
    'carrot': {'PET_CAFE', 'FARMERS_MARKET'},
    'tomato_milk': {'PIZZA_SHOP'},
    'strawberry_milk': {'ICE_CREAM_SHOP', 'SMOOTHIE_SHOP'},
    'egg': {'BAKERY', 'BRUNCH_SPOT'},
}


def inputs():
    old = ROOT / '24 Sept'
    for folder in sorted(old.iterdir()):
        if folder.is_dir():
            team = folder.name.split(' - Top')[0]
            for path in sorted(folder.glob('*.json.gz')):
                yield '24', team, path, None
    new = ROOT / '29 Sept top'
    for folder in sorted(new.iterdir()):
        if not folder.is_dir() or not (folder / 'episodes.json').exists():
            continue
        submission = int(folder.name)
        manifest = json.loads((folder / 'episodes.json').read_text(encoding='utf-8'))
        seats = {str(e['id']): next((j for j, a in enumerate(e['agents'])
                                    if a.get('submissionId') == submission), None)
                 for e in manifest['episodes']}
        for path in sorted(folder.glob('*.json.gz')):
            if seats.get(path.name.split('.')[0]) is not None:
                yield '29', folder.name, path, seats[path.name.split('.')[0]]


def groups(shops):
    active = set(shops)
    return '+'.join(k for k, v in SHOPS.items() if active & v) or 'none'


def predict(tile, inv, day, seeds):
    """One deliberately simple cell-local service priority, with GO for no job."""
    if isinstance(tile, dict):
        kind = tile.get('kind')
        if kind == 'PLANT':
            if not tile.get('watered_today'):
                return ('WATER',)
            if inv.get('FERTILIZER', 0) and tile.get('fertilized_until_day', -1) < day:
                return ('FERTILIZE',)
            if tile.get('yield_units', 0) > 0:
                return ('HARVEST',)
        elif kind in ('COOP', 'PASTURE') and tile.get('animal'):
            if tile.get('fertilizer_available', 0) > 0:
                return ('COLLECT_FERTILIZER',)
            if not tile.get('fed_today') and inv.get('WHEAT', 0):
                return ('FEED',)
            if tile.get('yield_units', 0) > 0:
                return ('HARVEST',)
            if tile.get('fed_today') and not tile.get('cared_today'):
                return ('CARE',)
    elif tile is None:
        for crop in ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON'):
            if seeds.get(crop, 0):
                return ('PLANT', crop)
    return ('GO',)


def fuzzy(a, b):
    if not a and not b:
        return 1.0
    prev = list(range(len(b) + 1))
    for i, u in enumerate(a, 1):
        cur = [i]
        for j, v in enumerate(b, 1):
            d = abs(u[0] - v[0]) + abs(u[1] - v[1])
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (0 if d == 0 else .5 if d == 1 else 1)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b))


def blocks(cells):
    result = []
    for x, y in cells:
        block = x // 2, y // 2
        if not result or result[-1] != block:
            result.append(block)
    return result


def edit(a, b):
    if not a and not b:
        return 1.0
    prev = list(range(len(b) + 1))
    for i, u in enumerate(a, 1):
        cur = [i]
        for j, v in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[-1] + 1, prev[j - 1] + (u != v)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b))


def gap(a, b):
    if not a or not b:
        return float('nan')
    prev = [(float('inf'), 0)] * (len(b) + 1)
    prev[0] = (0, 0)
    for u in a:
        cur = [(float('inf'), 0)]
        for j, v in enumerate(b, 1):
            best = min(prev[j], cur[-1], prev[j - 1])
            cur.append((best[0] + abs(u[0] - v[0]) + abs(u[1] - v[1]), best[1] + 1))
        prev = cur
    return prev[-1][0] / prev[-1][1]


def medoid(rows):
    """Best fuzzy-order medoid among frequent and sampled observed routes."""
    counts = Counter(tuple(r['jobs']) for r in rows)
    routes = list(counts)
    if len(routes) == 1:
        return routes[0]
    # Full pairwise search is expensive for 500+ games. Select candidates from
    # frequent routes, then score every candidate against every member.
    # honey: candidate cap can miss the exact medoid; revisit if groups exceed 1000 games.
    candidates = [r for r, _ in counts.most_common(12)]
    if len(routes) > 12:
        candidates += random.Random(0).sample(routes[12:], min(12, len(routes) - 12))
    return max(candidates, key=lambda c: sum(n * fuzzy(c, r) for r, n in counts.items()))


def write_csv(name, rows, fields):
    with (OUT / name).open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fields)
        writer.writeheader()
        writer.writerows(rows)


def main():
    routes = []
    actions = Counter()
    disputes = Counter()
    games = Counter()
    with gzip.open(OUT / 'routes.csv.gz', 'wt', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['cohort', 'team', 'episode', 'seat', 'hand', 'day', 'shop_groups', 'visits_json'])
        for cohort, team, path, seat in inputs():
            try:
                replay = json.load(gzip.open(path, 'rt', encoding='utf-8'))
            except (OSError, json.JSONDecodeError):
                continue
            if seat is None:
                names = replay.get('info', {}).get('TeamNames', [])
                norm = lambda value: ''.join(c for c in value.casefold() if c.isalnum())
                seat = next((j for j, name in enumerate(names) if norm(name) == norm(team)), None)
            if seat is None:
                continue
            games[cohort, team] += 1
            days = defaultdict(lambda: {'visits': [], 'jobs': [], 'path': [], 'shop': 'none'})
            steps = replay['steps']
            for i in range(1, len(steps)):
                before = steps[i - 1][seat]['observation']
                action = steps[i][seat].get('action') or {}
                if not isinstance(action, dict):
                    continue
                farm = before['farms'][seat]
                positions = [farm['farmer']] + list(farm.get('hands') or [])
                commands = [action.get('farmer')] + list(action.get('hands') or [])
                day = before['day']
                shop = groups(before['town']['unlocked_shops'])
                for hand, position in enumerate(positions):
                    x, y = position
                    cmd = commands[hand] if hand < len(commands) else None
                    op = cmd[0] if isinstance(cmd, list) and cmd else 'PASS'
                    record = days[hand, day]
                    record['shop'] = shop
                    record['path'].append((x, y))
                    record['visits'].append([x, y, cmd if isinstance(cmd, list) and cmd else ['PASS']])
                    if op in WORK:
                        record['jobs'].append((x, y))
                    if 6 <= day <= 19:
                        tile = farm['tiles'][y][x]
                        inv = before['private']['inventories']
                        carried = inv[hand] if hand < len(inv) else {}
                        predicted = predict(tile, carried, day, before['private']['seeds'])
                        actual = ('GO',) if op in MOVE or op == 'PASS' else tuple(cmd)
                        key = cohort, team, op
                        actions[key, 'all'] += 1
                        actions[key, 'match'] += predicted == actual
                        if predicted != actual:
                            kind = tile.get('kind', 'empty') if isinstance(tile, dict) else str(tile)
                            disputes[cohort, team, op, predicted[0], kind] += 1
            for (hand, day), record in days.items():
                writer.writerow([cohort, team, path.stem.split('.')[0], seat, hand, day,
                                 record['shop'], json.dumps(record['visits'], separators=(',', ':'))])
                if 6 <= day <= 19 and record['jobs']:
                    routes.append(dict(cohort=cohort, team=team, episode=path.stem.split('.')[0],
                                       seat=seat, hand=hand, day=day, shop=record['shop'],
                                       jobs=record['jobs'], path=record['path']))
            del replay

    collections = defaultdict(list)
    for route in routes:
        for mode in ('ungrouped', 'shop'):
            key = (route['cohort'], route['team'], route['hand'], route['day'],
                   'all' if mode == 'ungrouped' else route['shop'])
            collections[key].append(route)
    summary = []
    backbone = []
    for (cohort, team, hand, day, shop), members in sorted(collections.items()):
        if len(members) < 2:
            continue
        center = medoid(members)
        center_row = next(r for r in members if tuple(r['jobs']) == center)
        order = [fuzzy(center, r['jobs']) for r in members]
        block = [edit(blocks(center), blocks(r['jobs'])) for r in members]
        gaps = [gap(center_row['path'], r['path']) for r in members]
        summary.append(dict(cohort=cohort, team=team, hand=hand, day=day, shop_groups=shop,
                            n=len(members), order=round(sum(order)/len(order), 4),
                            blocks=round(sum(block)/len(block), 4), gap=round(sum(gaps)/len(gaps), 4)))
        backbone.append(dict(cohort=cohort, team=team, hand=hand, day=day, shop_groups=shop,
                             n=len(members), episode=center_row['episode'],
                             cells=json.dumps(center, separators=(',', ':')),
                             walk=json.dumps(center_row['path'], separators=(',', ':'))))
    write_csv('stability.csv', summary, ['cohort', 'team', 'hand', 'day', 'shop_groups', 'n', 'order', 'blocks', 'gap'])
    write_csv('medoids.csv', backbone, ['cohort', 'team', 'hand', 'day', 'shop_groups', 'n', 'episode', 'cells', 'walk'])
    write_csv('action_accuracy.csv', [dict(cohort=c, team=t, action=a, n=actions[(c,t,a),'all'],
                                            matches=actions[(c,t,a),'match'])
                                      for c,t,a in sorted({k[0] for k in actions})],
              ['cohort', 'team', 'action', 'n', 'matches'])
    write_csv('disagreements.csv', [dict(cohort=c, team=t, actual=a, predicted=p, tile=k, n=n)
                                    for (c,t,a,p,k), n in disputes.most_common()],
              ['cohort', 'team', 'actual', 'predicted', 'tile', 'n'])
    print('games', dict(games), 'routes', len(routes), 'groups', len(summary))


if __name__ == '__main__':
    main()

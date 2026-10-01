"""Equal-game-count comparison for teams present on both replay dates."""
import csv
import gzip
import json
import random
from collections import defaultdict

from analyze import WORK, blocks, edit, fuzzy, gap, medoid

TARGET = {'56654377': 'Team B', '56664798': 'Team A'}


def main():
    routes = defaultdict(list)
    with gzip.open('evaluation/backbones/routes.csv.gz', 'rt', encoding='utf-8', newline='') as file:
        for row in csv.DictReader(file):
            if row['team'] not in TARGET and row['team'] not in TARGET.values():
                continue
            day = int(row['day'])
            if not 6 <= day <= 19:
                continue
            visits = json.loads(row['visits_json'])
            jobs = [(x, y) for x, y, cmd in visits if cmd[0] in WORK]
            if jobs:
                team = TARGET.get(row['team'], row['team'])
                routes[row['cohort'], team].append(dict(episode=row['episode'], hand=int(row['hand']),
                                                       day=day, jobs=jobs,
                                                       path=[(x,y) for x,y,_ in visits]))
    for team in ('Team B', 'Team A'):
        for cohort in ('24', '29'):
            pool = routes[cohort, team]
            episodes = sorted({r['episode'] for r in pool})
            samples = [episodes] if cohort == '24' else [random.Random(seed).sample(episodes, 10) for seed in range(5)]
            for label, low, high in [('6-11', 6, 11), ('12-19', 12, 19)]:
                results = []
                for sample in samples:
                    groups = defaultdict(list)
                    for row in pool:
                        if row['episode'] in sample and low <= row['day'] <= high:
                            groups[row['hand'], row['day']].append(row)
                    values = []
                    for members in groups.values():
                        if len(members) < 2:
                            continue
                        center = medoid(members)
                        chosen = next(r for r in members if tuple(r['jobs']) == center)
                        values += [(fuzzy(center, r['jobs']), edit(blocks(center), blocks(r['jobs'])),
                                    gap(chosen['path'], r['path'])) for r in members]
                    results.append(tuple(sum(v[i] for v in values)/len(values) for i in range(3)))
                print(cohort, team, label, 'games', len(samples[0]),
                      'order/blocks/gap', *(round(sum(v[i] for v in results)/len(results), 3) for i in range(3)))


if __name__ == '__main__':
    main()

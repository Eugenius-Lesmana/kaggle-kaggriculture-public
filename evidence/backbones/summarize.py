"""Print the report figures from analyze.py outputs."""
import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path('evaluation/backbones')


def read(name):
    with (ROOT / name).open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file))


def weighted(rows, metric):
    n = sum(int(r['n']) for r in rows)
    return round(sum(int(r['n']) * float(r[metric]) for r in rows) / n, 3) if n else None


def main():
    stability = read('stability.csv')
    base = {(r['cohort'], r['team'], r['hand'], r['day']): r
            for r in stability if r['shop_groups'] == 'all'}
    period_rows = []
    for cohort in ('24', '29'):
        for period, days in [('6-11', range(6, 12)), ('12-19', range(12, 20))]:
            for team in sorted({r['team'] for r in stability if r['cohort'] == cohort}):
                rows = [r for r in stability if r['cohort'] == cohort and r['team'] == team
                        and int(r['day']) in days and r['shop_groups'] == 'all']
                sub = [r for r in stability if r['cohort'] == cohort and r['team'] == team
                       and int(r['day']) in days and r['shop_groups'] != 'all']
                matched = [dict(base[(r['cohort'], r['team'], r['hand'], r['day'])], n=r['n'])
                           for r in sub]
                period_rows.append(dict(cohort=cohort, team=team, days=period,
                                        ungrouped_n=sum(int(r['n']) for r in rows),
                                        shop_n=sum(int(r['n']) for r in sub),
                                        **{f'ungrouped_{x}': weighted(rows, x) for x in ('order', 'blocks', 'gap')},
                                        **{f'shop_{x}': weighted(sub, x) for x in ('order', 'blocks', 'gap')},
                                        **{f'matched_base_{x}': weighted(matched, x) for x in ('order', 'blocks', 'gap')}))
                print('ROUTE', cohort, team, period, 'n', sum(int(r['n']) for r in rows),
                      'base', *(weighted(rows, x) for x in ('order', 'blocks', 'gap')),
                      'shop', *(weighted(sub, x) for x in ('order', 'blocks', 'gap')),
                      'matched_base', *(weighted(matched, x) for x in ('order', 'blocks', 'gap')),
                      'matched_n', sum(int(r['n']) for r in sub))
    with (ROOT / 'period_summary.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, period_rows[0])
        writer.writeheader()
        writer.writerows(period_rows)
    actions = read('action_accuracy.csv')
    core = {'WATER', 'HARVEST', 'FERTILIZE', 'FEED', 'COLLECT_FERTILIZER', 'CARE', 'PLANT'}
    for cohort in ('24', '29'):
        for team in sorted({r['team'] for r in actions if r['cohort'] == cohort}):
            rows = [r for r in actions if r['cohort'] == cohort and r['team'] == team]
            for label, subset in [('all', rows), ('nonmovement', [r for r in rows if r['action'] not in
                                                 {'NORTH', 'SOUTH', 'EAST', 'WEST', 'PASS'}]),
                                  ('core', [r for r in rows if r['action'] in core])]:
                n = sum(int(r['n']) for r in subset)
                m = sum(int(r['matches']) for r in subset)
                print('ACTION', cohort, team, label, n, m, round(m/n, 3) if n else None)
    grouped = defaultdict(lambda: [0, 0])
    for r in actions:
        k = r['cohort'], r['action']
        grouped[k][0] += int(r['n'])
        grouped[k][1] += int(r['matches'])
    for k, (n, m) in sorted(grouped.items()):
        print('TYPE', *k, n, m, round(m/n, 3))
    disagreements = read('disagreements.csv')
    total = defaultdict(int)
    for r in disagreements:
        total[r['actual'], r['predicted'], r['tile']] += int(r['n'])
    for (actual, predicted, tile), n in sorted(total.items(), key=lambda x: -x[1])[:25]:
        print('DISAGREE', actual, predicted, tile, n)


if __name__ == '__main__':
    main()

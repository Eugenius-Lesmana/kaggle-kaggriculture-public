"""Validate D4/D6 traces and report paired morning-level and game-level standard errors.
python tools/report_diag_d4_d6.py --smoke --workers 2
python tools/report_diag_d4_d6.py --workers 2
"""
import argparse
from collections import defaultdict
from concurrent.futures import ProcessPoolExecutor
import csv
import gzip
import json
import math
from pathlib import Path
import statistics
import time

from diag_d4_d6 import (ROOT, REPO, LOG, SOURCE, GAMES, ARMS, SMOKE, case_id, sha, source, compact,
    save_json, digest, dependencies, expected_teacher_steps, measure)


def check_one(job):
    game, day, diagnostic, arm, signature = job
    key = case_id(game, day, diagnostic, arm)
    receipt = json.loads((LOG/'runs'/f'{key}.receipt.json').read_bytes())
    assert receipt['reason'] == 'kept' and receipt['signature'] == signature
    path = LOG/'runs'/f'{key}.json.gz'
    assert sha(path) == receipt['replay_sha256']
    rep = json.loads(gzip.decompress(path.read_bytes()))
    mark = rep['diagnostic']
    assert (mark['game'], mark['day'], mark['diagnostic'], mark['arm']) == (game, day, diagnostic, arm)
    recorded, source_sha = source(SOURCE/f'{game}.json')
    assert source_sha == receipt['source_sha256'] == mark['source_sha256']
    assert receipt['teacher_steps'] == expected_teacher_steps(day*24, diagnostic, arm)
    assert len(receipt['teacher_ms']) == len(receipt['teacher_steps'])
    assert not receipt['diagnostics']['fallbacks'] and not receipt['diagnostics']['search_errors']
    assert receipt['template_actual_warm_steps'] == (list(range(day*24, day*24+24)) if diagnostic == 'D4' and arm == 'B' else [])
    assert digest(rep['steps']) == receipt['steps_sha256']
    result = measure(rep, recorded)
    assert result == receipt['measurement'] and digest(result) == receipt['measurement_sha256']
    assert receipt['compatibility_events'] == mark['compatibility_events']
    for event in receipt['compatibility_events']:
        assert event['step'] in receipt['teacher_steps']
        assert event['helper'] == 'night_room_value' and not event['changed_unit_commands']
        assert event['teacher_pre_helper_action'] == event['returned_action']
        executed = rep['steps'][event['step']-day*24+1][0]['action']
        for key in (('farmer', 'hands') if diagnostic == 'D6' and arm == '4' else event['returned_action'].keys()):
            assert executed.get(key) == event['returned_action'].get(key)
    return dict(game=game, day=day, diagnostic=diagnostic, arm=arm,
        rows=result['rows'], first_day_steps_sha256=digest(rep['steps'][:25]),
        teacher_turns=len(receipt['teacher_steps']), compatibility_events=receipt['compatibility_events'])


def benchmark_rows():
    # Do not expose or analyse non-analysis rows, including any test rows in these mixed files.
    rows = []
    for filename in ('mixA.csv', 'mixB.csv'):
        with (ROOT/'runs/compare'/filename).open() as fh:
            for row in csv.DictReader(fh):
                if row['game'] not in {str(g) for g in GAMES}:
                    continue
                if row['player'] in ('template', 'fourth'):
                    rows.append(dict(row, benchmark_file=filename))
    return rows


def summary(values, games):
    assert len(values) == len(games) and len(values) > 1
    n = len(values)
    groups = defaultdict(list)
    for game, value in zip(games, values):
        groups[game].append(value)
    game_means = [statistics.mean(v) for v in groups.values()]
    assert len({len(v) for v in groups.values()}) == 1, 'game-level SE requires balanced games'
    return dict(n=n, games=len(groups), mean=statistics.mean(values),
        se_morning=statistics.stdev(values)/math.sqrt(n),
        se_game=statistics.stdev(game_means)/math.sqrt(len(game_means)))


def write_csv(path, rows):
    with path.open('w', newline='', encoding='utf-8') as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def analyse(rows):
    output = {'D4': [], 'D6': []}
    index = {(r['diagnostic'], r['game'], r['morning'], r['arm'], r['relative_day']): r for r in rows}
    numeric = [k for k in rows[0] if k not in ('game', 'morning', 'diagnostic', 'arm', 'relative_day', 'day')]
    for diagnostic, arms in ARMS.items():
        for arm in arms:
            for relative in range(1, 4 if diagnostic == 'D4' else 2):
                chosen = [r for r in rows if r['diagnostic'] == diagnostic and r['arm'] == arm and r['relative_day'] == relative]
                metrics = numeric+([k for k in chosen[0] if k.startswith('buy_') or k == 'hires'] if diagnostic == 'D6' else [])
                for metric in metrics:
                    output[diagnostic].append(dict(kind='arm', arm_or_difference=arm, period=str(relative), metric=metric,
                        **summary([r[metric] for r in chosen], [r['game'] for r in chosen])))
    for diagnostic, differences in [('D4', [('B', 'A')]), ('D6', [('3', '2'), ('4', '2'), ('2', '1')])]:
        mornings = [(g, d) for g in GAMES for d in range(6, 27 if diagnostic == 'D4' else 29)]
        periods = [(1,), (2,), (3,), (2, 3)] if diagnostic == 'D4' else [(1,)]
        for a, b in differences:
            for periods_in_pair in periods:
                for metric in ('value_plus_assets', 'cash_change', 'assets_change', 'dawn_value_change',
                               'cumulative_value_plus_assets', 'cumulative_dawn_value_change', 'dawn_value_end'):
                    # Cumulative/end-point metrics use only the final dawn, never sum successive endpoints.
                    periods_used = periods_in_pair[-1:] if metric.startswith('cumulative_') or metric == 'dawn_value_end' else periods_in_pair
                    deltas = [sum(index[diagnostic, g, d, a, p][metric]-index[diagnostic, g, d, b, p][metric]
                                  for p in periods_used) for g, d in mornings]
                    output[diagnostic].append(dict(kind='paired', arm_or_difference=f'{a}-{b}',
                        period='+'.join(map(str, periods_in_pair)), metric=metric,
                        **summary(deltas, [g for g, d in mornings])))
    # Explicit actual purchase differences in the first three turns, with zeros included.
    d6 = [r for r in rows if r['diagnostic'] == 'D6' and r['arm'] == '1']
    for metric in [k for k in d6[0] if k.startswith('buy_') or k == 'hires']:
        deltas = [r[metric]-index['D6', r['game'], r['morning'], '2', 1][metric] for r in d6]
        output['D6'].append(dict(kind='opening_purchase_difference', arm_or_difference='1-2', period='hours0-3',
            metric=metric, **summary(deltas, [r['game'] for r in d6])))
    return output


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = ap.parse_args()
    signature, hashes, versions = dependencies()
    run = json.loads((LOG/('smoke.json' if args.smoke else 'full.json')).read_bytes())
    assert signature == run['signature'] and hashes == run['dependency_hashes'] and versions == run['versions']
    assert set(run['source_hashes']) == {str(SOURCE/f'{g}.json') for g in GAMES}
    assert all(sha(Path(p)) == h for p, h in run['source_hashes'].items())
    cases = ([(g, d, diagnostic, arm) for g, d in SMOKE for diagnostic, arms in ARMS.items() for arm in arms]
             if args.smoke else [(g, d, diagnostic, arm) for diagnostic, arms in ARMS.items() for g in GAMES
                                for d in range(6, 27 if diagnostic == 'D4' else 29) for arm in arms])
    assert run['outcomes'] == {'kept': len(cases)}
    begun = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check_one, [(*case, signature) for case in cases], chunksize=1))
    rows = [row for r in results for row in r['rows']]
    index = {(r['diagnostic'], r['game'], r['morning'], r['arm'], r['relative_day']): r for r in rows}
    comparisons = []
    metrics = ('cash_change', 'goods', 'on_farm', 'value_change', 'assets_change', 'value_plus_assets', 'opp_cash_change')
    benchmarks = benchmark_rows()
    for b in benchmarks:
        key = ('D6', int(b['game']), int(b['day']), '1' if b['player'] == 'template' else '2', 1)
        if key not in index:
            continue
        for metric in metrics:
            assert index[key][metric] == float(b[metric]), (key, metric, index[key][metric], b[metric])
        comparisons.append(dict(game=int(b['game']), morning=int(b['day']), player=b['player'], benchmark_file=b['benchmark_file']))
    first_hash = {(r['diagnostic'], r['game'], r['day'], r['arm']): r['first_day_steps_sha256'] for r in results}
    controls = 0
    for g, d in sorted({(r['game'], r['morning']) for r in rows if r['diagnostic'] == 'D4'}):
        for a, b in [('A', '1'), ('B', '2'), ('C', '2')]:
            assert first_hash['D4', g, d, a] == first_hash['D6', g, d, b]
            for metric in metrics:
                assert index['D4', g, d, a, 1][metric] == index['D6', g, d, b, 1][metric]
            controls += 1
    smoke = json.loads((LOG/'smoke.json').read_bytes())
    assert smoke['signature'] == signature and smoke['determinism_cases'] == 21
    for g, d in SMOKE:
        for diagnostic, arms in ARMS.items():
            for arm in arms:
                key = case_id(g, d, diagnostic, arm)
                a = json.loads((LOG/'runs'/f'{key}.receipt.json').read_bytes())
                b = json.loads((LOG/'repeat'/f'{key}.receipt.json').read_bytes())
                assert b['signature'] == signature and b['reason'] == 'kept'
                assert a['steps_sha256'] == b['steps_sha256'] and a['measurement'] == b['measurement']
                assert sha(LOG/'repeat'/f'{key}.json.gz') == b['replay_sha256']
    if not args.smoke:
        output = analyse(rows)
        for diagnostic, values in output.items():
            write_csv(REPO/'reports'/f'DIAG_{diagnostic}.csv', values)
        write_csv(LOG/'daily_rows.csv', rows if all(set(r) == set(rows[0]) for r in rows) else
                  [{k: r.get(k) for k in dict.fromkeys(k for row in rows for k in row)} for r in rows])
    report = dict(cases=len(results), daily_rows=len(rows), games=list(GAMES), workers=args.workers,
        seconds=time.perf_counter()-begun, signature=signature, build_seconds=run['seconds'],
        determinism_cases=21, exact_benchmark_rows=len(comparisons), benchmark_numeric_checks=len(comparisons)*len(metrics),
        benchmark_analysis_rows_sha256=digest(benchmarks), exact_first_day_controls=controls,
        teacher_turns=sum(r['teacher_turns'] for r in results),
        compatibility_events=[dict(game=r['game'], morning=r['day'], diagnostic=r['diagnostic'], arm=r['arm'], **e)
                              for r in results for e in r['compatibility_events']], failures=0,
        source_hashes=run['source_hashes'], dependency_hashes=hashes, versions=versions)
    save_json(LOG/('smoke-check.json' if args.smoke else 'full-check.json'), report)
    if not args.smoke:
        save_json(REPO/'reports/DIAG_D4_D6_CHECKS.json', report)
    print(compact({k: v for k, v in report.items() if k not in ('dependency_hashes', 'source_hashes')}), flush=True)


if __name__ == '__main__':
    main()

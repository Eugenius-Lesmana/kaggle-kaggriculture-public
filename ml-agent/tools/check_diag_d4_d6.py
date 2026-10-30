"""Independent SQL checks of all paired statistics, plus corruption and split guards.
python tools/check_diag_d4_d6.py
"""
import copy
from contextlib import contextmanager
import csv
import gzip
import json
import math
from pathlib import Path
import re
import time

import duckdb
import diag_d4_d6 as implementation
from diag_d4_d6 import GAMES, LOG, REPO, SOURCE, case_id, measure, source, sha, save_json


def main():
    begun = time.perf_counter()
    checked = json.loads((LOG/'full-check.json').read_bytes())
    assert checked['cases'] == 775 and checked['failures'] == 0
    con = duckdb.connect()
    con.execute('CREATE TABLE daily AS SELECT * FROM read_csv_auto(?)', [str(LOG/'daily_rows.csv')])
    assert con.sql('SELECT DISTINCT game FROM daily ORDER BY game').fetchall() == [(g,) for g in GAMES]
    results = []
    for diagnostic in ('D4', 'D6'):
        with (REPO/'reports'/f'DIAG_{diagnostic}.csv').open() as fh:
            rows = [r for r in csv.DictReader(fh) if r['kind'] in ('paired', 'opening_purchase_difference')]
        for row in rows:
            metric = row['metric']
            assert re.fullmatch('[a-z_]+', metric)
            a, b = row['arm_or_difference'].split('-')
            periods = ((1,) if row['period'] == 'hours0-3' else tuple(map(int, row['period'].split('+'))))
            if metric.startswith('cumulative_') or metric == 'dawn_value_end':
                periods = periods[-1:]
            assert set(periods) <= {1, 2, 3}
            delta_sql = f'''SELECT a.game,a.morning,sum(a.{metric}-b.{metric}) delta
                FROM daily a JOIN daily b ON a.game=b.game AND a.morning=b.morning
                AND a.diagnostic=b.diagnostic AND a.relative_day=b.relative_day
                WHERE a.diagnostic=? AND a.arm=? AND b.arm=?
                AND a.relative_day IN ({','.join(map(str,periods))}) GROUP BY a.game,a.morning'''
            sql = f'''WITH deltas AS ({delta_sql}), gm AS (SELECT game,avg(delta) m FROM deltas GROUP BY game)
                SELECT count(*),avg(delta),stddev_samp(delta)/sqrt(count(*)),
                (SELECT stddev_samp(m)/sqrt(count(*)) FROM gm) FROM deltas'''
            n, mean, sem, game_sem = con.execute(sql, [diagnostic, a, b]).fetchone()
            assert n == int(row['n'])
            for key, actual in (('mean', mean), ('se_morning', sem), ('se_game', game_sem)):
                assert math.isclose(actual, float(row[key]), rel_tol=1e-12, abs_tol=1e-9), (row, key, actual)
            results.append(dict(diagnostic=diagnostic, comparison=row['arm_or_difference'], period=row['period'],
                                metric=metric,n=n,mean=mean,se_morning=sem,se_game=game_sem))
    recorded, _ = source(SOURCE/'10315.json')
    rep = json.loads(gzip.decompress((LOG/'runs/D6-10315-d8-1.json.gz').read_bytes()))
    for mutation in ('market', 'opponent'):
        broken = copy.deepcopy(rep)
        if mutation == 'market':
            broken['steps'][1][0]['observation']['market']['prices']['WHEAT'] += 1
        else:
            broken['steps'][1][1]['action'] = {'farmer': ['INVALID_CORRUPTION']}
        try:
            measure(broken, recorded)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'{mutation} corruption accepted')
    # A valid replay with all counters suppressed must fail conservation checks.
    @contextmanager
    def empty_observer(env):
        yield [], {'step': 0}
    original = implementation.actual_events
    implementation.actual_events = empty_observer
    try:
        try:
            measure(rep, recorded)
        except AssertionError:
            pass
        else:
            raise AssertionError('zero-count observer admitted')
    finally:
        implementation.actual_events = original
    for game in (10314, 10320, 10324):
        try:
            case_id(game, 8, 'D6', '1')
        except AssertionError:
            pass
        else:
            raise AssertionError('non-analysis identifier admitted')
    result = dict(paired_statistic_rows=len(results), sql_results=results, corrupted_replays_rejected=2, zero_count_observer_rejected=1,
        non_analysis_identifiers_rejected=3, daily_rows_sha256=sha(LOG/'daily_rows.csv'),
        checker_sha256=sha(Path(__file__)), seconds=time.perf_counter()-begun)
    save_json(LOG/'extra-checks.json', result)
    print(json.dumps({k:v for k,v in result.items() if k!='sql_results'}),flush=True)


if __name__ == '__main__':
    main()

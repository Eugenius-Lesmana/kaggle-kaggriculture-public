"""Validate own-farm shards and full-game extractor compatibility.
python tools/check_ownfarm.py [--smoke]
"""
import argparse
from collections import Counter
import copy
import csv
import gzip
import json
import statistics
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from kagml.replay_tables import TABLES, connect, replay
from ownfarm_labels import OUT, RAW, ROOT, LOG, REPO, sha, source, save_json
import pyarrow.parquet as pq


def metadata(row):
    return {'episode': row['episode'], 'created': '',
            **{f'{k}_{p}': -1 for k in ('sub', 'team', 'rating') for p in (0, 1)},
            **{f'reward_{p}': row[f'end_cash_{p}'] for p in (0, 1)}}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--smoke', action='store_true')
    args = parser.parse_args()
    run = json.loads((LOG / ('smoke.json' if args.smoke else 'full.json')).read_bytes())
    assert all(sha(Path(p)) == digest for p, digest in run['dependency_hashes'].items()), 'build dependencies changed'
    if args.smoke:
        manifest = [json.loads((OUT / 'audit' / f'10301{d:02}.json').read_bytes())['manifest'] for d in (6, 16, 28)]
    else:
        manifest = list(csv.DictReader((REPO / 'manifests/ownfarm.csv').open(encoding='utf-8')))
        assert len(manifest) == 552
        assert {(int(r['game']), int(r['day'])) for r in manifest} == {(g, d) for g in range(10301, 10325) for d in range(6, 29)}
    totals, effects = Counter(), Counter()
    all_times, receipts = [], []
    benchmark = {(r['game'], int(r['day'])): r for r in csv.DictReader((ROOT / 'runs/compare/rev24.csv').open()) if r['player'] == 'fourth'}
    comparisons = []
    for row in manifest:
        eid, game, day = int(row['episode']), str(row['game']), int(row['day'])
        assert eid == int(game) * 100 + day and int(row['seat']) == 0
        path = ROOT / row['file']
        assert sha(path) == row['sha256']
        audit = json.loads((OUT / 'audit' / f'{eid}.json').read_bytes())
        assert audit['signature'] == run['signature']
        assert audit['reason'] == 'kept' and audit['teacher_calls'] == 24
        assert not audit['diagnostics']['fallbacks'] and not audit['diagnostics']['search_errors']
        receipts.append(audit)
        effects.update(audit['effective_own_commands'])
        all_times.extend(audit['teacher_ms'])
        rep = json.loads(gzip.decompress(path.read_bytes()))
        original, original_sha = source(REPO.parent / 'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3' / f'{game}.json')
        assert audit['source_sha256'] == original_sha == rep['ownfarm']['source_sha256']
        assert rep['info']['seed'] == int(row['seed']) == original['info']['seed']
        assert len(rep['steps']) == 25 and int(row['start_step']) == day * 24 and int(row['end_step']) == (day + 1) * 24
        for p in (0, 1):
            assert rep['steps'][0][p]['observation'] == {**original['steps'][day*24][p]['observation'], 'step': day*24}
        for i, frame in enumerate(rep['steps']):
            assert frame[0]['observation']['step'] == day * 24 + i
            assert (frame[0]['observation']['day'], frame[0]['observation']['hour']) == divmod(day*24+i, 24)
            assert all(s['status'] == 'ACTIVE' for s in frame)
            if i:
                assert frame[1]['action'] == original['steps'][day*24+i][1]['action']
        banks = [f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
        assert banks == [float(row[f'end_cash_{p}']) for p in (0, 1)]
        for table in TABLES:
            count = pq.read_metadata(OUT / table / f'{eid}.parquet').num_rows
            assert count == audit['rows'][table]
            totals[table] += count
        if (game, day) in benchmark:
            b = benchmark[game, day]
            start = original['steps'][day*24][0]['observation']['farms']
            comparisons.append({'game': game, 'day': day,
                'own_cash_change': banks[0]-start[0]['money'], 'bench_own_cash_change': float(b['cash_change']),
                'own_delta': banks[0]-start[0]['money']-float(b['cash_change']),
                'opponent_delta': banks[1]-start[1]['money']-float(b['opp_cash_change'])})
    # All smoke shards share this directory; it becomes the full corpus on completion.
    db = connect(OUT)
    checks = {}

    def check(name, sql):
        count = db.sql(sql).fetchone()[0]
        assert count == 0, (name, count)
        checks[name] = count

    keys = {'games': 'episode', 'market_steps': 'episode,step', 'farm_daily': 'episode,seat,day,x,y',
            'unit_actions': 'episode,seat,step,unit', 'sales': 'episode,seat,step,order_index,product,price',
            'market_orders': 'episode,seat,step,order_index'}
    for table, key in keys.items():
        assert db.sql(f'SELECT count(*) FROM {table}').fetchone()[0] == totals[table]
        check(table+'_unique', f'SELECT count(*) FROM (SELECT {key} FROM {table} GROUP BY ALL HAVING count(*)>1)')
        assert {p.stem for p in (OUT / table).glob('*.parquet')} == {str(r['episode']) for r in manifest}
    check('frame_coverage', '''SELECT count(*) FROM (SELECT episode,count(*) n,min(step) lo,max(step) hi FROM market_steps GROUP BY episode)
        WHERE n<>25 OR hi-lo<>24 OR lo%24<>0 OR lo<>(episode%100)*24''')
    check('daily_tile_coverage', 'SELECT count(*) FROM (SELECT episode,seat,day,count(*) n FROM farm_daily GROUP BY ALL HAVING n<>100)')
    check('daily_at_dawn', 'SELECT count(*) FROM farm_daily f JOIN market_steps m USING(episode,step) WHERE m.hour<>0 OR m.day<>f.day')
    check('sales_valid', 'SELECT count(*) FROM sales WHERE units<=0 OR price<1 OR revenue<>units*price')
    check('actions_prestate', '''SELECT count(*) FROM unit_actions a LEFT JOIN market_steps m USING(episode,step)
        WHERE m.episode IS NULL OR a.step>=(a.episode%100+1)*24''')
    check('unit_existence', 'SELECT count(*) FROM unit_actions WHERE NOT "exists" AND (took_effect OR x IS NOT NULL OR y IS NOT NULL)')
    check('orders_effect', 'SELECT count(*) FROM market_orders WHERE took_effect<>(units>0) OR (NOT attempted AND (units<>0 OR cash_delta<>0))')
    check('sale_order_revenue', '''SELECT count(*) FROM
        (SELECT episode,seat,step,order_index,sum(units) units,sum(revenue) revenue FROM sales GROUP BY ALL) s
        FULL JOIN (SELECT episode,seat,step,order_index,units,cash_delta revenue FROM market_orders
            WHERE json_extract_string(command,'$[0]')='SELL' AND took_effect) o USING(episode,seat,step,order_index)
        WHERE s.units IS DISTINCT FROM o.units OR s.revenue IS DISTINCT FROM o.revenue''')
    check('cash_bridges', '''WITH deltas AS (SELECT episode,seat,step,sum(cash_delta) delta FROM (
        SELECT episode,seat,step,cash_delta FROM market_orders UNION ALL SELECT episode,seat,step,cash_delta FROM unit_actions) GROUP BY ALL),
        banks AS (SELECT episode,step,0 seat,cash_0 cash FROM market_steps UNION ALL SELECT episode,step,1 seat,cash_1 cash FROM market_steps),
        shifts AS (SELECT *,lead(cash) OVER(PARTITION BY episode,seat ORDER BY step) next_cash FROM banks)
        SELECT count(*) FROM shifts b LEFT JOIN deltas d USING(episode,seat,step)
        WHERE next_cash IS NOT NULL AND cash+coalesce(delta,0)<>next_cash''')
    check('end_cash', '''SELECT count(*) FROM market_steps m JOIN games g USING(episode)
        WHERE m.step=(m.episode%100+1)*24 AND (m.cash_0<>g.bank_0 OR m.cash_1<>g.bank_1 OR g.frames<>25)''')
    check('teacher_acts', '''SELECT count(*) FROM (SELECT episode,count(*) FILTER(WHERE seat=0 AND took_effect) n
        FROM unit_actions GROUP BY episode) WHERE n=0''')
    sample = manifest[0]
    rep = json.loads(gzip.decompress((ROOT / sample['file']).read_bytes()))
    rows, reason = replay(rep, metadata(sample), 'split-weeds')
    assert rows is None and reason['reason'] == 'state_mismatch', reason
    rep['steps'][1][0]['observation']['market']['prices']['WHEAT'] += 1
    rows, reason = replay(rep, metadata(sample), 'split-weeds', segment=True)
    assert rows is None and reason['reason'] == 'state_mismatch' and reason['field'] == 'market', reason
    checks['segment_requires_opt_in'] = checks['corrupted_segment_rejected'] = 0
    # The default path must still reproduce a complete Kaggle replay byte-for-byte as tables.
    native_meta = next(csv.DictReader((REPO / 'manifests/replays.csv').open(encoding='utf-8')))
    native_path = ROOT / 'raw/replays' / native_meta['folder'] / (native_meta['episode']+'.json.gz')
    native = json.loads(gzip.decompress(native_path.read_bytes()))
    rows, reason = replay(native, native_meta)
    assert rows is not None, reason
    for table in TABLES:
        assert rows[table] == pq.read_table(ROOT / 'datasets/d1' / table / (native_meta['episode']+'.parquet')).to_pylist(), table
    checks['full_game_tables_identical'] = 0
    local, _ = source(REPO.parent / 'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10301.json')
    local_meta = metadata({'episode': 10301, **{f'end_cash_{p}': local['steps'][-1][0]['observation']['farms'][p]['money'] for p in (0, 1)}})
    local_rows, local_reason = replay(local, local_meta, 'split-weeds')
    assert local_rows is not None and len(local_rows['market_steps']) == 720, local_reason
    checks['full_local_split_weeds_reconciles'] = 0
    incomplete = copy.deepcopy(native)
    incomplete['steps'] = incomplete['steps'][:25]
    rows, reason = replay(incomplete, native_meta)
    assert rows is None and reason['reason'] == 'incomplete_game', reason
    checks['full_game_requires_terminal'] = 0
    save_json(LOG / ('smoke-benchmark.json' if args.smoke else 'benchmark.json'), comparisons)
    result = {'segments': len(manifest), 'rows': dict(totals), 'checks': checks, 'teacher_calls': len(all_times),
              'teacher_median_ms': statistics.median(all_times), 'teacher_max_ms': max(all_times),
              'effective_own_commands': dict(effects), 'benchmark_pairs': len(comparisons),
              'benchmark_exact_own': sum(r['own_delta']==0 for r in comparisons),
              'benchmark_exact_both': sum(r['own_delta']==0 and r['opponent_delta']==0 for r in comparisons),
              'benchmark_mean_own_delta': statistics.mean(r['own_delta'] for r in comparisons) if comparisons else None}
    save_json(LOG / ('smoke-validation.json' if args.smoke else 'validation.json'), result)
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()

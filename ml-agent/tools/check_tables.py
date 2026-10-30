"""Independent D1 table checks. Run after build_tables finishes; threads capped at two."""
import argparse
import csv
import json
import gzip
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
import pyarrow.parquet as pq
from kagml.paths import datasets, data_root
from kagml.replay_tables import TABLES, connect, replay


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--root', type=Path, default=datasets()/'d1')
    args = parser.parse_args()
    root = args.root
    manifest = list(csv.DictReader((root/'manifest.csv').open(encoding='utf-8')))
    episodes = {r['episode'] for r in manifest}
    receipts = {p.stem: json.loads(p.read_text()) for p in (root/'audit').glob('*.json') if p.stem in episodes}
    assert set(receipts) == episodes, f'incomplete build: {len(receipts)}/{len(episodes)} receipts'
    totals = Counter()
    for episode, audit in receipts.items():
        for table in TABLES:
            path = root/table/f'{episode}.parquet'
            assert path.exists() == (audit['reason']=='kept'), (episode, table, 'publication mismatch')
            if path.exists():
                count = pq.read_metadata(path).num_rows
                assert count == audit['rows'][table], (episode, table, count)
                totals[table] += count
    for table in TABLES:
        assert {p.stem for p in (root/table).glob('*.parquet')} <= episodes, ('stale shard', table)
    db = connect(root)
    db.execute("SET memory_limit='1GB'")
    temp = str(root/'duckdb-temp').replace("'", "''")
    db.execute(f"SET temp_directory='{temp}'")
    checks = {}

    def check(name, sql):
        count = db.sql(sql).fetchone()[0]
        assert count == 0, (name, count)
        checks[name] = count

    keys = {'games':'episode', 'market_steps':'episode,step', 'farm_daily':'episode,seat,day,x,y',
            'unit_actions':'episode,seat,step,unit', 'sales':'episode,seat,step,order_index,product,price',
            'market_orders':'episode,seat,step,order_index'}
    for table, key in keys.items():
        check(table+'_unique',f'SELECT count(*) FROM (SELECT {key} FROM {table} GROUP BY ALL HAVING count(*)>1)')
        assert db.sql(f'SELECT count(*) FROM {table}').fetchone()[0] == totals[table]
    check('market_coverage', 'SELECT count(*) FROM (SELECT episode,count(*) n,min(step) lo,max(step) hi FROM market_steps GROUP BY episode) m JOIN games g USING(episode) WHERE n<>frames OR lo<>0 OR hi<>frames-1')
    check('daily_tile_coverage', 'SELECT count(*) FROM (SELECT episode,seat,day,count(*) n FROM farm_daily GROUP BY ALL HAVING n<>100)')
    check('sales_positive', 'SELECT count(*) FROM sales WHERE units<=0 OR price<1 OR revenue<>units*price')
    check('sales_prestate_join', 'SELECT count(*) FROM sales s LEFT JOIN market_steps m USING(episode,step) WHERE m.episode IS NULL')
    check('daily_at_dawn', 'SELECT count(*) FROM farm_daily f JOIN market_steps m USING(episode,step) WHERE m.hour<>0 OR m.day<>f.day')
    check('orders_effect', 'SELECT count(*) FROM market_orders WHERE took_effect<>(units>0) OR (NOT attempted AND (units<>0 OR cash_delta<>0))')
    check('sale_order_revenue', '''SELECT count(*) FROM
      (SELECT episode,seat,step,order_index,sum(units) units,sum(revenue) revenue FROM sales GROUP BY ALL) s
      FULL JOIN (SELECT episode,seat,step,order_index,units,cash_delta revenue FROM market_orders
        WHERE json_extract_string(command,'$[0]')='SELL' AND took_effect) o
      USING(episode,seat,step,order_index)
      WHERE s.units IS DISTINCT FROM o.units OR s.revenue IS DISTINCT FROM o.revenue''')
    check('cash_bridges', '''WITH deltas AS (
      SELECT episode,seat,step,sum(cash_delta) delta FROM (
        SELECT episode,seat,step,cash_delta FROM market_orders UNION ALL
        SELECT episode,seat,step,cash_delta FROM unit_actions) GROUP BY ALL),
      banks AS (SELECT episode,step,0 seat,cash_0 cash FROM market_steps UNION ALL
        SELECT episode,step,1 seat,cash_1 cash FROM market_steps),
      shifts AS (SELECT *,lead(cash) OVER(PARTITION BY episode,seat ORDER BY step) next_cash FROM banks)
      SELECT count(*) FROM shifts b LEFT JOIN deltas d USING(episode,seat,step)
      WHERE next_cash IS NOT NULL AND cash+coalesce(delta,0)<>next_cash''')
    check('final_banks', '''SELECT count(*) FROM market_steps m JOIN games g USING(episode)
      WHERE m.step=g.frames-1 AND (m.cash_0<>g.bank_0 OR m.cash_1<>g.bank_1)''')
    check('unit_existence', 'SELECT count(*) FROM unit_actions WHERE NOT "exists" AND (took_effect OR x IS NOT NULL OR y IS NOT NULL)')
    # Prove the replay gate rejects a changed recorded state, without changing a source file.
    sample = manifest[0]
    source = data_root()/'raw'/'replays'/sample['folder']/(sample['episode']+'.json.gz')
    rep = json.loads(gzip.decompress(source.read_bytes()))
    rep['steps'][1][0]['observation']['market']['prices']['WHEAT'] += 1
    rejected, reason = replay(rep, sample)
    assert rejected is None and reason.get('reason') == 'state_mismatch' and reason.get('field') == 'market', reason
    checks['corrupted_state_rejected'] = 0
    result = {'games': len(episodes), 'outcomes': dict(Counter(a['reason'] for a in receipts.values())),
              'rows': dict(totals), 'checks': checks}
    (root/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)


if __name__ == '__main__':
    main()

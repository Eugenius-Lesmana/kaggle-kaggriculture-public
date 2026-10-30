"""Independent artifact validation; no player/teacher inference.
python tools/check_takeover.py --smoke --workers 2
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
import gzip
import json
import time
from pathlib import Path

import os
from takeover_labels import (ROOT, REPO, SOURCE, HOURS, TABLES, folders, sha, source,
    save_json, compact, metadata, extract, dependencies, verify_segment, slug, manifest_path)
import pyarrow.parquet as pq

KEYS = {'games': ('episode',), 'market_steps': ('episode', 'step'),
        'farm_daily': ('episode', 'seat', 'day', 'x', 'y'),
        'unit_actions': ('episode', 'seat', 'step', 'unit'),
        'sales': ('episode', 'seat', 'step', 'order_index', 'product', 'price'),
        'market_orders': ('episode', 'seat', 'step', 'order_index')}


def check_one(job):
    name, episode, signature, source_dir, smoke = job
    raw, out, _ = folders(name)
    audit = json.loads((out/'audit'/f'{episode}.json').read_bytes())
    assert audit['reason'] == 'kept' and audit['signature'] == signature
    row = audit['manifest']
    game, day, hour = str(row['game']), int(row['day']), int(row['H'])
    assert episode == int(game)*10000+day*100+hour
    assert set(audit['output_hashes']) == {row['file'], *(str((out/t/f'{episode}.parquet').relative_to(ROOT).as_posix()) for t in TABLES)}
    assert all(sha(ROOT/p) == h for p, h in audit['output_hashes'].items())
    rep = json.loads(gzip.decompress((ROOT/row['file']).read_bytes()))
    recorded, source_sha = source(source_dir/f'{game}.json')
    assert source_sha == audit['source_sha256'] == rep['takeover']['source_sha256']
    assert sha(ROOT/row['file']) == row['sha256']
    verify_segment(rep, recorded)
    mark = rep['takeover']
    for key in ('game', 'day', 'H', 'takeover_step', 'start_step', 'end_step', 'seat', 'player',
                'takeover_cash', 'takeover_cash_1', 'takeover_state_sha256'):
        assert mark[key] == row[key], key
    assert row['seed'] == rep['info']['seed'] == recorded['info']['seed']
    assert audit['teacher_calls'] == 24-hour
    assert audit['teacher_steps'] == list(range(day*24+hour, (day+1)*24))
    assert len(audit['player_ms']) == hour and len(audit['teacher_ms']) == 24-hour
    assert audit['compatibility_events'] == mark['compatibility_events']
    assert not audit['diagnostics']['fallbacks'] and not audit['diagnostics']['search_errors']
    for event in audit['compatibility_events']:
        action = rep['steps'][event['step']-day*24+1][0]['action']
        assert action == event['returned_action']
    banks = [f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    assert banks == [row['end_cash_0'], row['end_cash_1']]
    rows, reason = extract(rep, metadata(episode, banks), 'split-weeds', segment=True)
    assert rows is not None, reason
    for table, values in rows.items():
        assert values == pq.read_table(out/table/f'{episode}.parquet').to_pylist(), table
        assert len(values) == audit['rows'][table]
        keys = [tuple(r[k] for k in KEYS[table]) for r in values]
        assert len(set(keys)) == len(keys), f'duplicate key: {table}'
    assert len(rows['market_steps']) == 25
    assert sum(r['seat'] == 0 and r['step'] >= day*24+hour and r['took_effect'] for r in rows['unit_actions']) == audit['effective_teacher_commands'] > 0
    plumbing = name == 'fourth' and hour == 0 and audit['l1_sha256'] is not None
    if smoke and hour == 8 and day in (6, 16):
        assert audit.get('continuous_branch_matches'), 'missing smoke branching proof'
    if plumbing:
        l1 = ROOT/'raw/ownfarm/fourth'/f'{game}-d{day}.json.gz'
        assert sha(l1) == audit['l1_sha256']
        assert rep['steps'] == json.loads(gzip.decompress(l1.read_bytes()))['steps']
    return dict(game=game, day=day, H=hour, player=name, rows=audit['rows'],
                teacher_calls=audit['teacher_calls'], compatibility_events=len(audit['compatibility_events']), plumbing=plumbing)


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--player', default='model:ranker-own-v1')
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--workers', type=int, choices=range(1, 9), default=2)
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--tag', default='takeover')
    args = ap.parse_args()
    os.environ['KAGML_TAKEOVER_TAG'] = args.tag
    log = folders(args.player)[2]
    run = json.loads((log/('smoke.json' if args.smoke else 'full.json')).read_bytes())
    assert run.get('tag', 'takeover') == args.tag
    planned = run.get('plan') or [(str(g), d, h) for g in range(10301, 10325) for d in range(6, 29) for h in HOURS]
    assert run['outcomes'] == {'kept': 4 if args.smoke else len(planned)}
    for name, expected in run['signatures'].items():
        signature, hashes, versions = dependencies(name)
        assert signature == expected and hashes == run['dependency_hashes'][name] and versions == run['versions']
    assert all(sha(Path(p)) == h for p, h in run['source_hashes'].items())
    jobs = [(r['player'], r['episode'], run['signatures'][r['player']], args.source, args.smoke) for r in run['receipts']]
    begun = time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results = list(pool.map(check_one, jobs, chunksize=4))
    if not args.smoke:
        expected = {(str(g), d, h) for g, d, h in planned}
        assert {(r['game'], r['day'], r['H']) for r in results} == expected
    names = {r['player'] for r in results}
    for name in names:
        manifests = list(csv.DictReader(manifest_path(name).open(encoding='utf-8')))
        accepted = [json.loads((folders(name)[1]/'audit'/f"{r['episode']}.json").read_bytes())['manifest']
                    for r in run['receipts'] if r['player'] == name]
        assert manifests == [{k: str(v) for k, v in r.items()} for r in accepted]
        ids = {str(r['episode']) for r in accepted}
        if not args.smoke:
            for table in TABLES:
                assert {p.stem for p in (folders(name)[1]/table).glob('*.parquet')} == ids
    # Corrupt a market quote: native frame reconciliation must reject it.
    sample_name, eid, _, _, _ = jobs[0]
    receipt = json.loads((folders(sample_name)[1]/'audit'/f'{eid}.json').read_bytes())
    rep = json.loads(gzip.decompress((ROOT/receipt['manifest']['file']).read_bytes()))
    banks = [f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    broken = copy.deepcopy(rep)
    broken['steps'][1][0]['observation']['market']['prices']['WHEAT'] += 1
    rows, reason = extract(broken, metadata(eid, banks), 'split-weeds', segment=True)
    assert rows is None and reason['reason'] == 'state_mismatch'
    # Corrupt the opponent command or takeover hash: reject before table extraction.
    for mutation in ('opponent', 'takeover_hash'):
        broken = copy.deepcopy(rep)
        if mutation == 'opponent':
            broken['steps'][1][1]['action'] = {'farmer': ['INVALID_CORRUPTION']}
        else:
            broken['takeover']['takeover_state_sha256'] = 'corrupted'
        recorded, _ = source(args.source/f"{receipt['game']}.json")
        try:
            verify_segment(broken, recorded)
        except AssertionError:
            pass
        else:
            raise AssertionError(f'{mutation} corruption accepted')
    summary = dict(segments=len(results), workers=args.workers, seconds=time.perf_counter()-begun,
        signatures=run['signatures'], plumbing_segments=sum(r['plumbing'] for r in results),
        teacher_calls=sum(r['teacher_calls'] for r in results),
        compatibility_events=sum(r['compatibility_events'] for r in results),
        rows=dict(sum((Counter(r['rows']) for r in results), Counter())),
        checks=['dependency/source/output hashes', 'all opponent commands', 'both private states at takeover',
                'all six D1 tables re-extracted identically', 'all primary keys', 'teacher coverage and effects',
                'L1 exact plumbing', 'corrupted market/opponent/takeover hash rejected'])
    save_json(log/('smoke-check.json' if args.smoke else 'full-check.json'), summary)
    print(compact(summary), flush=True)


if __name__ == '__main__':
    main()

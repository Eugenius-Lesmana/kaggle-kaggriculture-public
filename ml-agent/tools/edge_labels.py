"""Package E: existing L1/L3 collectors on mornings 0-5 and 29.
Set PYTHONHASHSEED=0 and KAGML_DATA before running.
python tools/edge_labels.py --kind l1 --smoke
python tools/check_edge.py --kind l1 --smoke
python tools/edge_labels.py --kind l3 --smoke
python tools/check_edge.py --kind l3 --smoke
Then repeat without --smoke, retaining --workers 2 (the default).
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
import hashlib
import json
import os
from pathlib import Path
import time

import ownfarm_labels as L1
import takeover_labels as L3
from shadow_labels import compact, slug

DAYS = (0, 1, 2, 3, 4, 5, 29)
PLAYER = 'model:ranker-v3-fw'
LOG = L1.ROOT/'runs/edge-days'


def locations(kind, plumbing=False):
    if kind == 'l1':
        return L1.folders('plumbing' if plumbing else True)
    return L3.folders(PLAYER, True)


def manifest_path(kind):
    name = 'ownfarm-edge' if kind == 'l1' else 'takeover-edge-'+slug(PLAYER)
    return L1.REPO/'manifests'/f'{name}.csv'


def dependencies(kind):
    _, hashes, versions = L3.dependencies(PLAYER if kind == 'l3' else 'fourth')
    for name in ('edge_labels.py', 'check_edge.py', 'ownfarm_labels.py'):
        p = L1.REPO/'tools'/name
        hashes[str(p)] = L1.sha(p)
    signature = hashlib.sha256(compact(dict(kind=kind, days=DAYS, files=hashes, versions=versions)).encode()).hexdigest()
    return signature, hashes, versions


def prepare(kind, plumbing=False):
    raw, out, log = locations(kind, plumbing)
    for folder in (raw, log, *(out/t for t in (*L1.TABLES, 'audit'))):
        folder.mkdir(parents=True, exist_ok=True)


def run_one(job):
    kind, path, day, hour, signature, smoke, plumbing = job
    if kind == 'l1':
        result = L1.one((path, day, signature, 'plumbing' if plumbing else True))
    else:
        result = L3.one((path, day, hour, PLAYER, signature, smoke, True))
    result['kind'] = kind
    result['plumbing_case'] = plumbing
    return result


def plumbing_test(path, signature):
    prepare('l1', True)
    result = run_one(('l1', path, 6, 0, signature, True, True))
    assert result['reason'] == 'kept', result
    import gzip
    rep = json.loads(gzip.decompress((L1.ROOT/result['manifest']['file']).read_bytes()))
    old = L1.RAW/f'{path.stem}-d6.json.gz'
    original = json.loads(gzip.decompress(old.read_bytes()))
    assert rep['steps'] == original['steps'], 'L1 day-6 frame/action mismatch'
    import pyarrow.parquet as pq
    for table in L1.TABLES:
        assert pq.read_table(locations('l1', True)[1]/table/f"{result['episode']}.parquet").to_pylist() == pq.read_table(L1.OUT/table/f"{result['episode']}.parquet").to_pylist(), table
    return dict(day6_frames_identical=True, day6_six_tables_identical=True,
                existing_l1_sha256=L1.sha(old), generated_sha256=result['manifest']['sha256'])


def recorded_terminal(path):
    from kagml.preview import snapshot_from_replay, pin_weeds, play
    recorded, digest = L1.source(path)
    pin_weeds(True)
    env = play(snapshot_from_replay(recorded, 696), ['recorded', 'recorded'], 24, recorded)
    frames = env.toJSON()['steps'][696:]
    assert len(frames) == 24 and [s['status'] for s in frames[-1]] == ['DONE', 'DONE']
    for actual, expected in zip(frames, recorded['steps'][696:]):
        for p in (0, 1):
            for field in ('farms', 'market', 'town', 'private', 'day', 'hour', 'player'):
                assert actual[p]['observation'][field] == expected[p]['observation'][field], (path.stem, field)
            assert (actual[p]['status'], actual[p]['reward']) == (expected[p]['status'], expected[p]['reward'])
    banks = [f['money'] for f in frames[-1][0]['observation']['farms']]
    assert banks == [f['money'] for f in recorded['steps'][-1][0]['observation']['farms']]
    return dict(game=path.stem, source_sha256=digest, frames=24, statuses=['DONE', 'DONE'], banks=banks)


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--kind', choices=('l1', 'l3'), required=True)
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED') == '0', 'start Python with PYTHONHASHSEED=0'
    paths = sorted(L3.SOURCE.glob('[0-9]*.json'))
    assert {p.stem for p in paths} == {str(g) for g in range(10301, 10325)}
    prepare(args.kind)
    LOG.mkdir(parents=True, exist_ok=True)
    signature, hashes, versions = dependencies(args.kind)
    source_hashes = {str(p): L1.sha(p) for p in paths}
    log = locations(args.kind)[2]
    if not args.smoke:
        smoke = json.loads((log/'smoke.json').read_bytes())
        check = json.loads((log/'smoke-check.json').read_bytes())
        assert smoke['signature'] == check['signature'] == signature
        assert smoke['source_hashes'] == source_hashes and smoke['outcomes'] == {'kept': smoke['segments']}
        assert check['segments'] == smoke['segments']
    cases = ([(paths[0], d, 0) for d in (0, 1, 5, 29)] if args.kind == 'l1' else
             [(paths[0], d, h) for d in (0, 1, 5, 29) for h in L3.HOURS]) if args.smoke else [
                 (p, d, h) for p in paths for d in DAYS for h in ((0,) if args.kind == 'l1' else L3.HOURS)]
    begun = time.perf_counter()
    plumbing = {}
    if args.smoke and args.kind == 'l1':
        plumbing.update(plumbing_test(paths[0], signature))
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            plumbing['recorded_terminal'] = list(pool.map(recorded_terminal, paths))
        L1.save_json(LOG/'plumbing.json', plumbing)
    results = []
    jobs = [(args.kind, p, d, h, signature, args.smoke, False) for p, d, h in cases]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(run_one, jobs, chunksize=4 if args.kind == 'l3' else 1):
            results.append(result)
            if result['reason'] != 'kept' or len(results)%24 == 0 or len(results) == len(jobs):
                print(compact(dict(completed=len(results), total=len(jobs), seconds=round(time.perf_counter()-begun, 2),
                    outcomes=dict(Counter(r['reason'] for r in results)),
                    errors=[r['error'] for r in results if 'error' in r][-3:])), flush=True)
    summary = dict(kind=args.kind, player='fourth' if args.kind=='l1' else PLAYER, days=DAYS,
        signature=signature, dependency_hashes=hashes, versions=versions, source_hashes=source_hashes,
        segments=len(results), workers=args.workers, worker_hash_seed=0, seconds=time.perf_counter()-begun,
        outcomes=dict(Counter(r['reason'] for r in results)), resumed=sum(r.get('resumed', False) for r in results),
        rows=dict(sum((Counter(r.get('rows', {})) for r in results), Counter())),
        teacher_calls=sum(r.get('teacher_calls', 0) for r in results),
        compatibility_events=[dict(game=r['game'], day=r['day'], H=r.get('H', 0), **e) for r in results for e in r.get('compatibility_events', [])],
        failures=[r for r in results if r['reason'] != 'kept'],
        receipts=[r['episode'] for r in results], plumbing=plumbing)
    L1.save_json(log/('smoke.json' if args.smoke else 'full.json'), summary)
    if not args.smoke:
        target = manifest_path(args.kind)
        with target.with_suffix('.tmp').open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=L1.FIELDS if args.kind=='l1' else L3.FIELDS)
            writer.writeheader()
            writer.writerows(r['manifest'] for r in results if r['reason']=='kept')
        target.with_suffix('.tmp').replace(target)
    print(compact({k:v for k,v in summary.items() if k not in ('dependency_hashes','source_hashes','receipts','plumbing','failures')}), flush=True)
    if summary['failures']:
        raise SystemExit('Rejected edge segments; inspect audit receipts')


if __name__ == '__main__':
    main()

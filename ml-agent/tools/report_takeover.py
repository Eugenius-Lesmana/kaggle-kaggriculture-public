"""Summarize the validated takeover corpus and check all shared model prefixes.
Run only after tools/check_takeover.py has accepted the full corpus.
"""
from collections import Counter, defaultdict
import gzip
import json
from pathlib import Path
import statistics
import time

from takeover_labels import ROOT, REPO, folders, compact, sha, save_json, dependencies, one


def main():
    name = 'model:ranker-own-v1'
    raw, out, log = folders(name)
    run = json.loads((log/'full.json').read_bytes())
    check = json.loads((log/'full-check.json').read_bytes())
    assert check['segments'] == 2208 and check['signatures'] == run['signatures']
    signature, _, _ = dependencies(name)
    assert signature == run['signatures'][name]
    begun = time.perf_counter()
    groups = defaultdict(list)
    receipts = []
    hashes = {}
    for item in run['receipts']:
        receipt = json.loads((out/'audit'/f"{item['episode']}.json").read_bytes())
        assert receipt['signature'] == signature and receipt['reason'] == 'kept'
        receipts.append(receipt)
        row = receipt['manifest']
        groups[row['game'], row['day']].append(row)
        hashes.update(receipt['output_hashes'])
    prefix_pairs = 0
    for rows in groups.values():
        rows.sort(key=lambda r:r['H'])
        assert [r['H'] for r in rows] == [4, 8, 12, 16]
        longest = json.loads(gzip.decompress((ROOT/rows[-1]['file']).read_bytes()))
        for row in rows[:-1]:
            rep = json.loads(gzip.decompress((ROOT/row['file']).read_bytes()))
            assert rep['steps'][:row['H']+1] == longest['steps'][:row['H']+1], (row['game'],row['day'],row['H'])
            prefix_pairs += 1
    # Verify the resume path has no inference or artifact writes for a sealed segment.
    sample = receipts[0]
    row = sample['manifest']
    source_dir = Path(next(iter(run['source_hashes']))).parent
    resumed = one((source_dir/f"{row['game']}.json", row['day'], row['H'], name, signature, False))
    assert resumed['resumed'] and resumed['output_hashes'] == sample['output_hashes']
    assert all(sha(ROOT/p) == h for p,h in sample['output_hashes'].items())
    timings = [t for r in receipts for t in r['teacher_ms']]
    events = run['compatibility_events']
    smoke = json.loads((log/'smoke.json').read_bytes())
    smoke_check = json.loads((log/'smoke-check.json').read_bytes())
    result = dict(player=name, segments=len(receipts), failures=len(run['failures']),
        original_games=len({r['game'] for r in receipts}), mornings=len(groups), hours=[4,8,12,16],
        teacher_calls=run['teacher_calls'], model_turns_in_segments=sum(r['H'] for r in receipts),
        actual_cached_model_calls=len(groups)*16, workers=run['workers'], worker_hash_seed=run['worker_hash_seed'],
        full_build_seconds=run['seconds'], full_validation_seconds=check['seconds'],
        smoke_build_seconds=smoke['seconds'], smoke_validation_seconds=smoke_check['seconds'],
        smoke_plumbing_segments=smoke_check['plumbing_segments'], smoke_teacher_calls=smoke['teacher_calls'],
        compatibility_events=events, compatibility_segments=sum(bool(r['compatibility_events']) for r in receipts),
        resumed_segments=run['resumed'], rows=run['rows'], prefix_pairs_checked=prefix_pairs,
        prefix_mornings_checked=len(groups), hash_verified_resume=True,
        teacher_call_ms=dict(median=statistics.median(timings),maximum=max(timings),
                             mean=statistics.mean(timings)),
        raw_bytes=sum((ROOT/p).stat().st_size for p in hashes if p.endswith('.json.gz')),
        parquet_bytes=sum((ROOT/p).stat().st_size for p in hashes if p.endswith('.parquet')),
        artifact_files=len(hashes), manifest_sha256=sha(REPO/'manifests/takeover-model-ranker-own-v1.csv'),
        signature=signature, report_check_seconds=time.perf_counter()-begun,
        checks=check['checks']+['all four branches share exact model prefixes on all 552 mornings',
                               'sealed segment resumes with every output hash unchanged'])
    save_json(REPO/'reports/TAKEOVER_RESULTS.json',result)
    print(compact(result),flush=True)


if __name__ == '__main__':
    main()

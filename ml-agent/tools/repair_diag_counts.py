"""One-off provenance-preserving repair of the original D4/D6 quantity observer.
Replays and teacher actions are never regenerated or edited; only measurements are revised.
python tools/repair_diag_counts.py --workers 2
"""
import argparse
import ast
from concurrent.futures import ProcessPoolExecutor
import copy
import gzip
import json
from pathlib import Path
import shutil
import time

from diag_d4_d6 import (LOG, REPO, SOURCE, GAMES, ARMS, SMOKE, case_id, sha, source,
                       save_json, digest, dependencies, measure)

BACKUP = LOG/'observer-fix'


def one(job):
    game, day, diagnostic, arm, repeat, signature, old_signature = job
    key = case_id(game, day, diagnostic, arm)
    folder = 'repeat' if repeat else 'runs'
    archived = BACKUP/'receipts'/folder/f'{key}.receipt.json'
    old = json.loads(archived.read_bytes())
    assert old['signature'] == old_signature and old['reason'] == 'kept'
    target = LOG/folder/f'{key}.json.gz'
    before = sha(target)
    assert before == old['replay_sha256']
    rep = json.loads(gzip.decompress(target.read_bytes()))
    assert digest(rep['steps']) == old['steps_sha256']
    recorded, source_sha = source(SOURCE/f'{game}.json')
    assert source_sha == old['source_sha256']
    measurement = measure(rep, recorded)
    for a, b in zip(old['measurement']['rows'], measurement['rows']):
        assert set(a) == set(b)
        for k, v in a.items():
            if not k.startswith(('planted_', 'harvested_', 'buy_')) and k not in ('crops_planted', 'fertilizer_applied', 'hires'):
                assert v == b[k], ('non-quantity measurement changed', key, k, v, b[k])
    assert sha(target) == before
    revision = dict(original_signature=old_signature, original_measurement_sha256=old['measurement_sha256'],
        current_measurement_sha256=digest(measurement), replay_sha256_unchanged=before,
        reason='Observer now binds the interpreter current-state farm; all value metrics unchanged')
    updated = {**old, 'signature':signature, 'generated_signature':old_signature,
               'measurement':measurement, 'measurement_sha256':digest(measurement), 'measurement_revision':revision}
    save_json(LOG/folder/f'{key}.receipt.json',updated)
    return dict(case=key, repeat=repeat, raw_sha256=before,
                quantities_changed=old['measurement'] != measurement)


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    args=ap.parse_args()
    old_source=BACKUP/'diag_d4_d6-before.py'
    current=REPO/'tools/diag_d4_d6.py'
    # Only observation/measurement functions may differ; agent generation code must be identical.
    def policy_tree(path):
        tree=ast.parse(path.read_text(encoding='utf-8-sig'))
        tree.body=[n for n in tree.body if not isinstance(n,ast.FunctionDef) or n.name not in ('actual_events','measure')]
        return ast.dump(tree,include_attributes=False)
    assert policy_tree(old_source)==policy_tree(current),'policy/generation code changed'
    for kind in ('full','smoke','full-check','smoke-check'):
        dest=BACKUP/f'{kind}-before.json'
        if not dest.exists():shutil.copyfile(LOG/f'{kind}.json',dest)
    old=json.loads((BACKUP/'full-before.json').read_bytes())
    assert old['dependency_hashes'][str(current)] == sha(old_source)
    signature,hashes,versions=dependencies()
    assert versions==old['versions']
    assert all(sha(Path(p))==h for p,h in old['dependency_hashes'].items() if Path(p)!=current)
    assert all(sha(Path(p))==h for p,h in old['source_hashes'].items())
    cases=[(g,d,diag,arm,False) for diag,arms in ARMS.items() for g in GAMES
           for d in range(6,27 if diag=='D4' else 29) for arm in arms]
    cases += [(g,d,diag,arm,True) for g,d in SMOKE for diag,arms in ARMS.items() for arm in arms]
    for g,d,diag,arm,repeat in cases:
        folder='repeat' if repeat else 'runs'
        dest=BACKUP/'receipts'/folder/f'{case_id(g,d,diag,arm)}.receipt.json'
        dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():shutil.copyfile(LOG/folder/dest.name,dest)
    begun=time.perf_counter()
    results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(one,[(*case,signature,old['signature']) for case in cases],chunksize=1):
            results.append(result)
            if len(results)%100==0 or len(results)==len(cases):
                print(json.dumps({'remeasured':len(results),'total':len(cases),'seconds':time.perf_counter()-begun}),flush=True)
    revision=dict(cases=len(results), unchanged_replays=len(results), new_teacher_calls=0,
        quantities_changed_cases=sum(r['quantities_changed'] for r in results),
        seconds=time.perf_counter()-begun, workers=args.workers,
        original_signature=old['signature'], current_signature=signature,
        original_observer_sha256=sha(old_source), corrected_observer_sha256=sha(current),
        repair_tool_sha256=sha(Path(__file__)), policy_AST_unchanged=True,
        original_receipts=str(BACKUP/'receipts'),
        checks=['all raw replay hashes unchanged','all non-quantity measurements unchanged',
                'seed conservation','opening hires and land match farm changes','opening animals match held totals',
                'harvest inventory gains equal yield removed'])
    for kind in ('full','smoke'):
        updated=json.loads((BACKUP/f'{kind}-before.json').read_bytes())
        updated.update(signature=signature,dependency_hashes=hashes,measurement_revision=revision)
        save_json(LOG/f'{kind}.json',updated)
    save_json(BACKUP/'repair.json',revision)
    print(json.dumps(revision),flush=True)


if __name__=='__main__':main()

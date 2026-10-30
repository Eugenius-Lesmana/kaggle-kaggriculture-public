"""Own-farm fourth-place labels. Smoke first: python tools/ownfarm_labels.py --smoke.
Then python tools/ownfarm_labels.py --workers 2. All generated evidence stays on D:.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))
for key in ('OMP_NUM_THREADS', 'MKL_NUM_THREADS', 'OPENBLAS_NUM_THREADS'):
    os.environ[key] = '1'
from kagml.replay_tables import TABLES, SCHEMAS, compact, replay as extract
from kagml.paths import data_root
import pyarrow as pa
import pyarrow.parquet as pq

ROOT = data_root()
RAW = ROOT / 'raw/ownfarm/fourth'
OUT = ROOT / 'datasets/ownfarm'
LOG = ROOT / 'runs/ownfarm-fourth'
FIELDS = ('game', 'day', 'seat', 'file', 'sha256', 'end_cash_0', 'end_cash_1', 'episode', 'seed', 'start_step', 'end_step')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save_json(path, value):
    tmp = path.with_suffix('.tmp')
    tmp.write_text(compact(value), encoding='utf-8')
    tmp.replace(path)


@lru_cache(maxsize=1)
def source(path):
    return json.loads(path.read_bytes()), sha(path)


def folders(edge=False):
    if edge == 'plumbing':
        base = ROOT/'runs/edge-days/plumbing/l1'
        return base/'raw', base/'datasets', base
    if edge:
        return ROOT/'raw/ownfarm-edge/fourth', ROOT/'datasets/ownfarm-edge', ROOT/'runs/ownfarm-edge'
    return RAW, OUT, LOG


def one(job):
    path, day, signature, *options = job
    edge = options[0] if options else False
    RAW, OUT, _ = folders(edge)
    game = path.stem
    episode = int(game) * 100 + day
    receipt = OUT / 'audit' / f'{episode}.json'
    target = RAW / f'{game}-d{day}.json.gz'
    start = time.perf_counter()
    result = {'game': game, 'day': day, 'episode': episode, 'signature': signature}
    try:
        recorded, source_hash = source(path)
        if receipt.exists():
            old = json.loads(receipt.read_bytes())
            if (old.get('reason') == 'kept' and old.get('signature') == signature
                    and old.get('source_sha256') == source_hash and target.exists()
                    and old['manifest']['sha256'] == sha(target)
                    and all(sha(ROOT/p) == h for p, h in old.get('output_hashes', {}).items())
                    and all((OUT / t / f'{episode}.parquet').exists() for t in TABLES)):
                return {**old, 'resumed': True}
        from kagml.preview import pin_weeds, play, snapshot_from_replay
        from kagml.opponents import load
        from shadow_compat import overflow_guard
        pin_weeds(True)
        actor = load('fourth')
        seed = int(recorded['info']['seed'])
        actor.reset(seed)
        calls, milliseconds = [], []

        def teacher(obs, configuration):
            begun = time.perf_counter()
            action = actor(obs, configuration)
            milliseconds.append((time.perf_counter() - begun) * 1000)
            if not isinstance(action, dict) or not isinstance(action.get('farmer'), list):
                raise ValueError('teacher returned an invalid action')
            assert actor.play._FLOW[0]['act'] == action, 'teacher did not retain its executed answer'
            calls.append(int(obs['day']) * 24 + int(obs['hour']))
            return action

        end = min((day+1)*24, len(recorded['steps'])-1)
        turns = end-day*24
        snap = snapshot_from_replay(recorded, step=day * 24)
        generation = time.perf_counter()
        events = []
        policy = actor.play.POL
        original = policy.night_room_value
        policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)
        try:
            env = play(snap, [teacher, 'recorded'], steps=turns, replay=recorded)
        finally:
            policy.night_room_value = original
        generation = time.perf_counter() - generation
        segment = env.toJSON()
        segment['steps'] = segment['steps'][snap['step']:]
        segment['ownfarm'] = {'game': game, 'day': day, 'seat': 0, 'start_step': snap['step'],
                              'turns': turns, 'teacher': 'fourth', 'reset_seed': seed, 'source_sha256': source_hash}
        assert segment['info']['seed'] == seed
        if edge:
            segment['ownfarm'].update(end_step=end, terminal=end==719, compatibility_events=events)
        assert len(segment['steps']) == turns+1 and calls == list(range(day*24, end))
        for p in (0, 1):
            assert segment['steps'][0][p]['observation'] == {**snap['obs'][p], 'step': day * 24}
        for offset, frame in enumerate(segment['steps'][1:], 1):
            assert frame[1]['action'] == recorded['steps'][day * 24 + offset][1]['action']
        assert [s['status'] for s in segment['steps'][-1]] == (['DONE', 'DONE'] if end==719 else ['ACTIVE', 'ACTIVE'])
        banks = [f['money'] for f in segment['steps'][-1][0]['observation']['farms']]
        meta = {'episode': episode, 'created': '', **{f'{k}_{p}': -1 for k in ('sub', 'team', 'rating') for p in (0, 1)},
                **{f'reward_{p}': banks[p] for p in (0, 1)}}
        # Round-trip the exact bytes that will be published, then reconcile independently.
        packed = gzip.compress(compact(segment).encode(), compresslevel=6, mtime=0)
        extraction = time.perf_counter()
        rows, audit = extract(json.loads(gzip.decompress(packed)), meta, 'split-weeds', segment=True)
        if rows is None:
            raise ValueError(f'segment reconciliation failed: {audit}')
        effects = Counter(json.loads(r['effective_command'])[0] for r in rows['unit_actions']
                          if r['seat'] == 0 and r['took_effect'])
        assert sum(effects.values()) > 0, 'teacher had no effective unit actions'
        diagnostics = actor.diagnostics()
        assert not diagnostics['fallbacks'] and not diagnostics['search_errors'], diagnostics
        manifest = dict(zip(FIELDS, (game, day, 0, target.relative_to(ROOT).as_posix(),
                         hashlib.sha256(packed).hexdigest(), *banks, episode, seed, day * 24, end)))
        result.update(audit, source_sha256=source_hash, manifest=manifest, rows={t: len(v) for t, v in rows.items()},
                      effective_own_commands=dict(effects), teacher_calls=len(calls), diagnostics=diagnostics,
                      teacher_steps=calls, compatibility_events=events, teacher_ms=milliseconds, generation_seconds=generation, load_seconds=actor.load_seconds,
                      extraction_seconds=time.perf_counter() - extraction)
        hashes = {}
        for table, values in rows.items():
            dest = OUT / table / f'{episode}.parquet'
            tmp = dest.with_suffix('.tmp')
            pq.write_table(pa.Table.from_pylist(values, schema=pa.schema(SCHEMAS[table])), tmp, compression='zstd')
            tmp.replace(dest)
            hashes[dest.relative_to(ROOT).as_posix()] = sha(dest)
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(packed)
        tmp.replace(target)
        hashes[target.relative_to(ROOT).as_posix()] = sha(target)
        result['output_hashes'] = hashes
    except Exception as error:
        import traceback
        result.update(reason='error', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
        for table in TABLES:
            (OUT / table / f'{episode}.parquet').unlink(missing_ok=True)
    result['seconds'] = time.perf_counter() - start
    save_json(receipt, result)
    return result


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--source', type=Path, default=REPO.parent / 'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3')
    args = parser.parse_args()
    paths = sorted(args.source.glob('[0-9]*.json'))
    assert len(paths) == 24, f'expected 24 standard games, found {len(paths)}'
    dependencies = [Path(__file__), *(REPO / 'src/kagml' / f'{s}.py' for s in ('preview', 'opponents', 'replay_tables'))]
    upstream = ROOT / 'opponents/fourth-place/fourth-place-model'
    dependencies += sorted(upstream.rglob('*.py')) + [upstream / 'weights.pt']
    hashes = {str(p): sha(p) for p in dependencies}
    signature = hashlib.sha256(compact(hashes).encode()).hexdigest()
    for folder in (RAW, LOG, *(OUT / t for t in (*TABLES, 'audit'))):
        folder.mkdir(parents=True, exist_ok=True)
    jobs = [(p, day, signature) for p in paths for day in range(6, 29)]
    if args.smoke:
        jobs = [(paths[0], d, signature) for d in (6, 16, 28)]
    else:
        smoke = json.loads((LOG / 'smoke.json').read_bytes())
        assert smoke['signature'] == signature and smoke['outcomes'] == {'kept': 3}, 'run a passing smoke with this code first'
    start = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(one, jobs, chunksize=1):
            results.append(result)
            if result['reason'] != 'kept' or len(results) % 12 == 0 or len(results) == len(jobs):
                print(compact({'completed': len(results), 'total': len(jobs), 'seconds': round(time.perf_counter()-start, 2),
                               'outcomes': dict(Counter(r['reason'] for r in results)),
                               **({'error': result['error']} if 'error' in result else {})}), flush=True)
    summary = {'segments': len(results), 'workers': args.workers, 'seconds': time.perf_counter()-start,
               'outcomes': dict(Counter(r['reason'] for r in results)), 'resumed': sum(r.get('resumed', False) for r in results),
               'signature': signature, 'dependency_hashes': hashes,
               'rows': dict(sum((Counter(r.get('rows', {})) for r in results), Counter())),
               'segment_seconds': [dict(game=r['game'], day=r['day'], seconds=r['seconds'],
                                        generation_seconds=r.get('generation_seconds')) for r in results]}
    save_json(LOG / ('smoke.json' if args.smoke else 'full.json'), summary)
    if not args.smoke:
        manifest = REPO / 'manifests/ownfarm.csv'
        tmp = manifest.with_suffix('.tmp')
        with tmp.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(r['manifest'] for r in results if r['reason'] == 'kept')
        tmp.replace(manifest)
    print(compact({k: v for k, v in summary.items() if k not in ('dependency_hashes', 'segment_seconds')}), flush=True)
    if summary['outcomes'] != {'kept': len(jobs)}:
        raise SystemExit('Some segments failed; see datasets/ownfarm/audit on the data drive')


if __name__ == '__main__':
    main()

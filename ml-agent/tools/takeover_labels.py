"""L3: our player runs H hours, then fourth actually plays through dawn.
python tools/takeover_labels.py --smoke --workers 2
python tools/takeover_labels.py --player model:ranker-own-v1 --workers 2
python tools/check_takeover.py --player model:ranker-own-v1 --workers 2
Other sources (Claude, 2026-10-27): --source DIR of <seed>.json seat-0 games, --tag takeover-n1 (keeps output apart),
--late adds hours on days 22-28; --mid adds them on days 12-21 instead (round N3, Claude 2026-10-28);
--focus uses hours 8-18 on days 6-24 (regret map, 2026-10-29).
All large artifacts, receipts and logs stay on the configured data drive.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
import gzip
import hashlib
import json
import os
from functools import lru_cache
from pathlib import Path
import time

from shadow_labels import (ROOT, REPO, sha, source, save_json, compact, metadata,
                           dependencies as shadow_dependencies, player_instance,
                           warm_memories, valid_action, slug)
from shadow_compat import overflow_guard
from kagml.preview import TemplatePlayer, env_from_snapshot, pin_weeds, snapshot_from_replay
from kagml.replay_tables import TABLES, SCHEMAS, replay as extract
import pyarrow as pa
import pyarrow.parquet as pq

HOURS = (4, 8, 12, 16)
LATE_HOURS = (2, 4, 6, 8, 10, 12, 14, 16, 18)  # --late: days 22-28, where board-p2 loses most
FOCUS_HOURS = (8, 10, 12, 14, 16, 18)  # --focus: days 6-24, where the regret map loses most (hours 12-20)
FIELDS = ('game', 'day', 'H', 'takeover_step', 'seat', 'player', 'file', 'sha256',
          'start_step', 'end_step', 'takeover_cash', 'takeover_cash_1', 'takeover_state_sha256',
          'end_cash_0', 'end_cash_1', 'episode', 'seed')
SOURCE = REPO.parent / 'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3'


def folders(name, edge=False):
    key = slug(name)
    tag = 'takeover-edge' if edge else os.environ.get('KAGML_TAKEOVER_TAG', 'takeover')
    return ROOT/'raw'/tag/key, ROOT/'datasets'/tag/key, ROOT/'runs'/tag/key


def state_hash(frame, step, seed):
    # Seat 1's shared step can be stale; day/hour and both private states are authoritative.
    state = {'seed': seed, 'step': step,
             'obs': [{**copy.deepcopy(frame[p]['observation']), 'step': step} for p in (0, 1)]}
    return hashlib.sha256(json.dumps(state, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def dependencies(name):
    _, _, hashes, versions = shadow_dependencies(name)
    for p in (Path(__file__), REPO/'tools/check_takeover.py', REPO/'tools/shadow_compat.py'):
        hashes[str(p)] = sha(p)
    signature = hashlib.sha256(compact({'player': name, 'files': hashes, 'versions': versions}).encode()).hexdigest()
    return signature, hashes, versions


@lru_cache(maxsize=1)
def model_prefix(path, day, name):
    """The four branches share exactly the same deterministic model trajectory."""
    recorded, _ = source(path)
    player, initial = player_instance(name)
    if isinstance(player, TemplatePlayer):
        if 6 <= day <= 28:
            player.restore(copy.deepcopy(warm_memories(path, name)[day]))
        else:
            player.restore(copy.deepcopy(initial))
            for step in range(day*24):
                obs = copy.deepcopy(recorded['steps'][step][0]['observation'])
                obs['step'] = step
                getattr(player, 'warm_step', player)(obs, copy.deepcopy(recorded['configuration']))
    elif hasattr(player, 'reset'):
        player.reset(int(recorded['info']['seed']))
    pin_weeds(True)
    start = day*24
    env = env_from_snapshot(snapshot_from_replay(recorded, start))
    milliseconds = []
    for offset in range(max(LATE_HOURS)):
        begun = time.perf_counter()
        action = copy.deepcopy(player(copy.deepcopy(env.state[0].observation), env.configuration))
        milliseconds.append((time.perf_counter()-begun)*1000)
        valid_action(action)
        env.step([action, copy.deepcopy(recorded['steps'][start+offset+1][1]['action'])])
    if hasattr(player, 'diagnostics'):
        assert not any(player.diagnostics().get(k) for k in ('fallbacks', 'search_errors'))
    return env.toJSON()['steps'][start:], milliseconds


def generate(recorded, game, day, hour, name, teacher, prefix=None):
    pin_weeds(True)
    start = day*24
    seed = int(recorded['info']['seed'])
    end = min(start+24, len(recorded['steps'])-1)
    teacher.reset(seed)
    if hour:
        frames, player_ms = prefix
        frame = frames[hour]
        snap = dict(seed=seed, step=start+hour, obs=[copy.deepcopy(s['observation']) for s in frame])
        env = env_from_snapshot(snap)
        env.state[1].observation.step = frames[0][1]['observation'].get('step', start)
    else:
        env = env_from_snapshot(snapshot_from_replay(recorded, start))
        frame = env.toJSON()['steps'][-1]
        player_ms = []
    takeover_cash, takeover_cash_1 = [f['money'] for f in frame[0]['observation']['farms']]
    takeover_hash = state_hash(frame, start+hour, seed)
    events, calls, teacher_ms = [], [], []
    policy = teacher.play.POL
    original = policy.night_room_value
    policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)
    try:
        for offset in range(hour, end-start):
            step = start+offset
            begun = time.perf_counter()
            action = copy.deepcopy(teacher(copy.deepcopy(env.state[0].observation), env.configuration))
            teacher_ms.append((time.perf_counter()-begun)*1000)
            valid_action(action)
            calls.append(step)
            assert teacher.play._FLOW[0]['act'] == action, 'teacher did not retain its executed answer'
            env.step([action, copy.deepcopy(recorded['steps'][step+1][1]['action'])])
    finally:
        policy.night_room_value = original
    rep = env.toJSON()
    tail = rep['steps'][start+hour:]
    rep['steps'] = copy.deepcopy(frames[:hour+1])+tail[1:] if hour else tail
    rep['takeover'] = dict(game=game, day=day, H=hour, takeover_step=start+hour,
        start_step=start, end_step=end, seat=0, player=name, teacher='fourth',
        teacher_reset_seed=seed, takeover_cash=takeover_cash, takeover_cash_1=takeover_cash_1,
        takeover_state_sha256=takeover_hash, compatibility_events=events)
    assert calls == list(range(start+hour, end))
    diagnostics = teacher.diagnostics()
    assert not diagnostics['fallbacks'] and not diagnostics['search_errors'], diagnostics
    verify_segment(rep, recorded)
    return rep, dict(teacher_calls=len(calls), teacher_steps=calls, teacher_ms=teacher_ms,
                     player_ms=player_ms[:hour], diagnostics=diagnostics, compatibility_events=events)


def check_continuation(rep, recorded, teacher):
    """Smoke: compare snapshot branching against continuous play of the same prefix."""
    mark = rep['takeover']
    start, hour = mark['start_step'], mark['H']
    teacher.reset(int(recorded['info']['seed']))
    pin_weeds(True)
    env = env_from_snapshot(snapshot_from_replay(recorded, start))
    policy = teacher.play.POL
    original, events = policy.night_room_value, []
    policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)
    try:
        for offset in range(len(rep['steps'])-1):
            action = (rep['steps'][offset+1][0]['action'] if offset < hour else
                      teacher(copy.deepcopy(env.state[0].observation), env.configuration))
            env.step([copy.deepcopy(action), copy.deepcopy(recorded['steps'][start+offset+1][1]['action'])])
    finally:
        policy.night_room_value = original
    assert env.toJSON()['steps'][start:] == rep['steps'], 'snapshot branch differs from continuous play'
    assert events == mark['compatibility_events']


def verify_segment(rep, recorded):
    mark = rep['takeover']
    start, hour = mark['start_step'], mark['H']
    end = min(start+24, len(recorded['steps'])-1)
    assert len(rep['steps']) == end-start+1 and rep['info']['seed'] == recorded['info']['seed']
    for p in (0, 1):
        assert rep['steps'][0][p]['observation'] == {**recorded['steps'][start][p]['observation'], 'step': start}
    for i, frame in enumerate(rep['steps']):
        assert frame[0]['observation']['step'] == start+i
        assert (frame[0]['observation']['day'], frame[0]['observation']['hour']) == divmod(start+i, 24)
        assert all(s['status'] == ('DONE' if start+i==719 else 'ACTIVE') for s in frame)
        if i:
            assert frame[1]['action'] == recorded['steps'][start+i][1]['action'], 'opponent command mismatch'
            valid_action(frame[0]['action'])
    frame = rep['steps'][hour]
    assert mark['takeover_state_sha256'] == state_hash(frame, start+hour, rep['info']['seed'])
    assert [mark['takeover_cash'], mark['takeover_cash_1']] == [f['money'] for f in frame[0]['observation']['farms']]
    assert mark['takeover_step'] == start+hour and mark['end_step'] == end
    for event in mark['compatibility_events']:
        assert start+hour <= event['step'] < end
        assert event['helper'] == 'night_room_value' and not event['changed_unit_commands']
        assert event['teacher_pre_helper_action'] == event['returned_action']


def one(job):
    path, day, hour, name, signature, smoke, *options = job
    edge = options[0] if options else False
    raw, out, _ = folders(name, edge)
    episode = int(path.stem)*10000+day*100+hour
    target = raw/f'{path.stem}-d{day}-h{hour}.json.gz'
    receipt = out/'audit'/f'{episode}.json'
    begun = time.perf_counter()
    result = dict(game=path.stem, day=day, H=hour, episode=episode, signature=signature)
    try:
        recorded, source_hash = source(path)
        l1 = ROOT/'raw/ownfarm/fourth'/f'{path.stem}-d{day}.json.gz'
        l1_hash = sha(l1) if hour == 0 and name == 'fourth' and l1.exists() else None
        if receipt.exists():
            old = json.loads(receipt.read_bytes())
            if (old.get('reason') == 'kept' and old.get('signature') == signature
                    and old.get('source_sha256') == source_hash and old.get('l1_sha256') == l1_hash
                    and all((ROOT/p).is_file() and sha(ROOT/p) == h for p, h in old['output_hashes'].items())):
                return {**old, 'resumed': True}
        from kagml.opponents import load
        teacher = load('fourth')
        generation = time.perf_counter()
        prefix = model_prefix(path, day, name) if hour else None
        rep, measurements = generate(recorded, path.stem, day, hour, name, teacher, prefix)
        result['generation_seconds'] = time.perf_counter()-generation
        rep['takeover']['source_sha256'] = source_hash
        if smoke and hour:
            checking = time.perf_counter()
            check_continuation(rep, recorded, teacher)
            result['continuous_branch_matches'] = True
            result['continuous_check_seconds'] = time.perf_counter()-checking
        if l1_hash:
            original = json.loads(gzip.decompress(l1.read_bytes()))
            assert rep['steps'] == original['steps'], 'H=0 differs from L1 frames/actions'
            result['plumbing'] = 'all 25 frames, all actions and both closing banks exactly match L1'
        packed = gzip.compress(compact(rep).encode(), compresslevel=6, mtime=0)
        banks = [f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
        extraction = time.perf_counter()
        rows, audit = extract(json.loads(gzip.decompress(packed)), metadata(episode, banks), 'split-weeds', segment=True)
        if rows is None:
            raise ValueError(f'frame reconciliation failed: {audit}')
        effects = sum(r['seat'] == 0 and r['step'] >= day*24+hour and r['took_effect'] for r in rows['unit_actions'])
        assert effects > 0, 'teacher had no effective unit commands'
        result.update(audit, **measurements, source_sha256=source_hash, l1_sha256=l1_hash,
            extraction_seconds=time.perf_counter()-extraction, rows={t: len(v) for t, v in rows.items()},
            effective_teacher_commands=effects)
        hashes = {}
        for table, values in rows.items():
            dest = out/table/f'{episode}.parquet'
            tmp = dest.with_suffix('.tmp')
            pq.write_table(pa.Table.from_pylist(values, schema=pa.schema(SCHEMAS[table])), tmp, compression='zstd')
            tmp.replace(dest)
            hashes[dest.relative_to(ROOT).as_posix()] = sha(dest)
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(packed)
        tmp.replace(target)
        hashes[target.relative_to(ROOT).as_posix()] = sha(target)
        result['output_hashes'] = hashes
        mark = rep['takeover']
        result['manifest'] = dict(game=path.stem, day=day, H=hour, takeover_step=mark['takeover_step'],
            seat=0, player=name, file=target.relative_to(ROOT).as_posix(), sha256=sha(target),
            start_step=day*24, end_step=mark['end_step'], takeover_cash=mark['takeover_cash'],
            takeover_cash_1=mark['takeover_cash_1'], takeover_state_sha256=mark['takeover_state_sha256'],
            end_cash_0=banks[0], end_cash_1=banks[1], episode=episode, seed=recorded['info']['seed'])
    except Exception as error:
        import traceback
        result.update(reason='error', error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc())
        for p in (target, *(out/t/f'{episode}.parquet' for t in TABLES)):
            p.unlink(missing_ok=True)
    result['seconds'] = time.perf_counter()-begun
    save_json(receipt, result)
    return result


def dense(d, late, mid):
    return (late and d >= 22) or (mid and 12 <= d <= 21)


def hours(d, late, mid, focus):
    return FOCUS_HOURS if focus and d <= 24 else LATE_HOURS if dense(d, late, mid) else HOURS


def plan(paths, late, mid=False, focus=False):
    return [(p.stem, d, h) for p in paths for d in range(6, 29) for h in hours(d, late, mid, focus)]


def manifest_path(name):
    return REPO/'manifests'/f"{os.environ.get('KAGML_TAKEOVER_TAG', 'takeover')}-{slug(name)}.csv"


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--player', default='model:ranker-own-v1')
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--workers', type=int, choices=range(1, 9), default=2)
    ap.add_argument('--source', type=Path, default=SOURCE)
    ap.add_argument('--tag', default='takeover')
    ap.add_argument('--late', action='store_true')
    ap.add_argument('--mid', action='store_true')
    ap.add_argument('--focus', action='store_true')
    args = ap.parse_args()
    os.environ['KAGML_TAKEOVER_TAG'] = args.tag  # spawned workers inherit it
    # ModelPlayer resolves tied scores in set iteration order; pin spawned interpreters.
    os.environ['PYTHONHASHSEED'] = '0'
    slug(args.player)
    paths = sorted(args.source.glob('[0-9]*.json'))
    if args.source == SOURCE:
        assert {p.stem for p in paths} == {str(g) for g in range(10301, 10325)}
    assert paths and not {p.stem for p in paths} & {str(g) for g in range(10320, 10325)}, 'test games'
    by_stem = {p.stem: p for p in paths}
    names = ['fourth', args.player] if args.smoke else [args.player]
    signatures = {n: dependencies(n) for n in names}
    sources = {str(p): sha(p) for p in paths}
    for name in names:
        raw, out, log = folders(name)
        for folder in (raw, log, *(out/t for t in (*TABLES, 'audit'))):
            folder.mkdir(parents=True, exist_ok=True)
    if not args.smoke:
        smoke = json.loads((folders(args.player)[2]/'smoke.json').read_bytes())
        assert smoke['outcomes'] == {'kept': 4} and smoke['source_hashes'] == sources
        assert smoke['signatures'][args.player] == signatures[args.player][0], 'run a current passing smoke first'
        validation = json.loads((folders(args.player)[2]/'smoke-check.json').read_bytes())
        assert validation['segments'] == 4 and validation['signatures'] == smoke['signatures']
    jobs = ([(paths[0], d, h, n, signatures[n][0], True) for n, h in [('fourth', 0), (args.player, 8)] for d in (6, 16)]
            if args.smoke else [(by_stem[g], d, h, args.player, signatures[args.player][0], False)
                              for g, d, h in plan(paths, args.late, args.mid, args.focus)])
    begun = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(one, jobs, chunksize=1 if args.smoke else 4):
            results.append(result)
            if result['reason'] != 'kept' or len(results)%24 == 0 or len(results) == len(jobs):
                print(compact(dict(completed=len(results), total=len(jobs), seconds=round(time.perf_counter()-begun, 2),
                    outcomes=dict(Counter(r['reason'] for r in results)),
                    errors=[r['error'] for r in results if 'error' in r][-3:])), flush=True)
    summary = dict(worker_hash_seed=0, player=args.player, segments=len(results), workers=args.workers,
        seconds=time.perf_counter()-begun, outcomes=dict(Counter(r['reason'] for r in results)),
        signatures={n: v[0] for n, v in signatures.items()}, dependency_hashes={n: v[1] for n, v in signatures.items()},
        versions=signatures[args.player][2], source_hashes=sources, tag=args.tag, late=args.late, mid=args.mid, focus=args.focus,
        plan=None if args.smoke else plan(paths, args.late, args.mid, args.focus),
        rows=dict(sum((Counter(r.get('rows', {})) for r in results), Counter())),
        teacher_calls=sum(r.get('teacher_calls', 0) for r in results),
        compatibility_events=[dict(game=r['game'], day=r['day'], H=r['H'], **e) for r in results for e in r.get('compatibility_events', [])],
        resumed=sum(r.get('resumed', False) for r in results),
        failures=[r for r in results if r['reason'] != 'kept'],
        receipts=[dict(player=r.get('manifest', {}).get('player', args.player), episode=r['episode']) for r in results])
    save_json(folders(args.player)[2]/('smoke.json' if args.smoke else 'full.json'), summary)
    for name in names:
        manifest = manifest_path(name)
        tmp = manifest.with_suffix('.tmp')
        with tmp.open('w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDS)
            writer.writeheader()
            writer.writerows(r['manifest'] for r in results if r['reason'] == 'kept' and r['manifest']['player'] == name)
        tmp.replace(manifest)
    print(compact({k: v for k, v in summary.items() if k not in ('dependency_hashes', 'source_hashes', 'receipts')}), flush=True)
    if summary['failures']:
        raise SystemExit('Rejected segments; see takeover audit receipts on D:')


if __name__ == '__main__':
    main()

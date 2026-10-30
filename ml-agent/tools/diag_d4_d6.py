"""D4/D6, analysis games 10315-10319 ONLY. Run smoke before full.
KAGML_DATA=<data> python tools/diag_d4_d6.py --smoke --workers 2
python tools/diag_d4_d6.py --workers 2
python tools/report_diag_d4_d6.py --workers 2
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from contextlib import contextmanager
import copy
from functools import cache, lru_cache
import gzip
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import sys
import time

from ownfarm_labels import ROOT, REPO, sha, source, save_json
from compare_day import (Mix, assets_at_cost, goods_value, make_player, on_farm_value)
from shadow_compat import overflow_guard
from shadow_labels import valid_action
from kagml.preview import env_from_snapshot, pin_weeds, snapshot_from_replay, PRODUCTS
from kagml.replay_tables import compact
import kaggle_environments.envs.kaggriculture.kaggriculture as K

GAMES = tuple(range(10315, 10320))
SOURCE = REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3'
LOG = ROOT/'runs/diag/d4-d6'
ARMS = {'D4': ('A', 'B', 'C'), 'D6': ('1', '2', '3', '4')}
SMOKE = ((10315, 8), (10317, 16), (10319, 24))
CROPS = tuple(K.CROPS)
ANIMALS = tuple(K.ANIMALS)


def digest(value):
    return hashlib.sha256(compact(value).encode()).hexdigest()


def case_id(game, day, diagnostic, arm):
    assert game in GAMES, 'Only analysis games 10315-10319 are allowed'
    assert arm in ARMS[diagnostic] and 6 <= day <= (26 if diagnostic == 'D4' else 28)
    return f'{diagnostic}-{game}-d{day}-{arm}'


def dependencies():
    files = [Path(__file__), REPO/'tools/report_diag_d4_d6.py', REPO/'tools/ownfarm_labels.py',
        REPO/'tools/compare_day.py', REPO/'tools/shadow_compat.py', REPO/'tools/shadow_labels.py',
        REPO/'vendor/template_agent/main.py',
        *(REPO/'src/kagml'/f'{n}.py' for n in ('preview', 'opponents', 'replay_tables', 'paths'))]
    upstream = ROOT/'opponents/fourth-place/fourth-place-model'
    files += sorted(upstream.rglob('*.py'))+[upstream/'weights.pt']
    hashes = {str(p): sha(p) for p in files}
    versions = {n: importlib.metadata.version(n) for n in ('kaggle-environments', 'numpy', 'torch')}
    return digest(dict(files=hashes, versions=versions, games=GAMES, worker_hash_seed=0)), hashes, versions


@cache
def warm_actor():
    return make_player('template')


@lru_cache(maxsize=1)
def memories(game):
    assert game in GAMES
    recorded, _ = source(SOURCE/f'{game}.json')
    actor = warm_actor()
    actor.restore({})
    result = {}
    for step in range(28*24):
        if step%24 == 0 and step//24 >= 6:
            result[step//24] = actor.memory()
        obs = copy.deepcopy(recorded['steps'][step][0]['observation'])
        obs['step'] = step
        actor(obs, copy.deepcopy(recorded['configuration']))
    result[28] = actor.memory()
    return result


def wealth(obs):
    farm, private = obs['farms'][0], obs['private']
    tiles = [t for row in farm['tiles'] for t in row if isinstance(t, dict)]
    prices = obs['market']['prices']
    return round(farm['money']+goods_value(private, prices)+on_farm_value(tiles, prices)+assets_at_cost(farm, private))


def value_change(before, after):
    """Exactly compare_day.run_day's closing-price convention and rounding."""
    prices = after['market']['prices']
    farms = [o['farms'][0] for o in (before, after)]
    privates = [o['private'] for o in (before, after)]
    goods = [goods_value(p, prices) for p in privates]
    grown = [on_farm_value([t for row in f['tiles'] for t in row if isinstance(t, dict)], prices) for f in farms]
    cash = farms[1]['money']-farms[0]['money']
    assets = [assets_at_cost(f, p) for f, p in zip(farms, privates)]
    value = round(cash+goods[1]-goods[0]+grown[1]-grown[0])
    return dict(cash_change=cash, goods=round(goods[1]), on_farm=round(grown[1]),
        value_change=value, assets_change=assets[1]-assets[0], value_plus_assets=value+assets[1]-assets[0],
        cash_start=farms[0]['money'], cash_end=farms[1]['money'],
        assets_start=assets[0], assets_end=assets[1],
        dawn_value_start=wealth(before), dawn_value_end=wealth(after), dawn_value_change=wealth(after)-wealth(before),
        opp_cash_change=after['farms'][1]['money']-before['farms'][1]['money'])


@contextmanager
def actual_events(env):
    """Observe successful native operations, including harvested quantities before midnight drops."""
    names = ('_apply_unit_action', '_commit_unit', '_do_hire', '_do_buy_land')
    original = {n: getattr(K, n) for n in names}
    events = []
    clock = {'step': 0, 'own_farm': None}
    original_interpreter = env.interpreter

    def interpreter(state, environment):
        # Environment.step deep-copies the state before invoking its interpreter.
        clock['own_farm'] = state[0].observation.farms[0]
        return original_interpreter(state, environment)

    env.interpreter = interpreter

    def ours(farm):
        return farm is clock['own_farm']

    def emit(op, item, units):
        if units:
            events.append(dict(step=clock['step'], op=op, item=item, units=units))

    def apply(farm, private, unit, action, *args, **kwargs):
        own = ours(farm)
        op = action[0] if action else 'PASS'
        bags = private['inventories']
        before = dict(bags[unit]) if own and unit < len(bags) else {}
        seeds = dict(private['seeds']) if own and op == 'PLANT' else {}
        position = K._farmer_position(farm, unit) if own and op == 'HARVEST' else None
        prior_tile = farm['tiles'][position[1]][position[0]] if position else None
        prior_yield = prior_tile.get('yield_units', 0) if isinstance(prior_tile, dict) else 0
        result = original['_apply_unit_action'](farm, private, unit, action, *args, **kwargs)
        after = bags[unit] if own and unit < len(bags) else {}
        if own and op == 'HARVEST':
            tile = farm['tiles'][position[1]][position[0]] if position else None
            remaining = tile.get('yield_units', 0) if isinstance(tile, dict) else 0
            assert sum(max(0, after.get(k, 0)-before.get(k, 0)) for k in PRODUCTS) == prior_yield-remaining
            for item in PRODUCTS:
                emit(op, item, max(0, after.get(item, 0)-before.get(item, 0)))
        elif own and op == 'PLANT' and len(action) > 1:
            emit(op, action[1], max(0, seeds.get(action[1], 0)-private['seeds'].get(action[1], 0)))
        elif own and op == 'FERTILIZE':
            emit(op, 'FERTILIZER', max(0, before.get('FERTILIZER', 0)-after.get('FERTILIZER', 0)))
        return result

    def commit(op, item, price, farm, private, market, *args, **kwargs):
        result = original['_commit_unit'](op, item, price, farm, private, market, *args, **kwargs)
        if result and ours(farm) and op.startswith('BUY_'):
            emit(op, item, 1)
        return result

    def special(name, farm, *args, **kwargs):
        key = 'hands' if name == '_do_hire' else 'unlocked_quadrants'
        before = len(farm[key])
        result = original[name](farm, *args, **kwargs)
        if ours(farm):
            emit('HIRE' if key == 'hands' else 'BUY_LAND', 'WORKER' if key == 'hands' else 'QUADRANT', len(farm[key])-before)
        return result

    K._apply_unit_action, K._commit_unit = apply, commit
    K._do_hire = lambda farm, *a, **kw: special('_do_hire', farm, *a, **kw)
    K._do_buy_land = lambda farm, *a, **kw: special('_do_buy_land', farm, *a, **kw)
    try:
        yield events, clock
    finally:
        env.interpreter = original_interpreter
        for name, function in original.items():
            setattr(K, name, function)


def measure(rep, recorded):
    """No agents: replay every action natively, verify all frames, measure successful quantities."""
    mark = rep['diagnostic']
    game, day, diagnostic, arm = mark['game'], mark['day'], mark['diagnostic'], mark['arm']
    case_id(game, day, diagnostic, arm)
    start = day*24
    turns = 72 if diagnostic == 'D4' else 24
    assert rep['info']['seed'] == recorded['info']['seed'] and len(rep['steps']) == turns+1
    pin_weeds(True)
    env = env_from_snapshot(snapshot_from_replay(recorded, start))
    for p in (0, 1):
        assert rep['steps'][0][p]['observation'] == {**recorded['steps'][start][p]['observation'], 'step': start}
    with actual_events(env) as (events, clock):
        for i in range(1, turns+1):
            frame = rep['steps'][i]
            assert frame[0]['observation']['step'] == start+i
            assert frame[1]['action'] == recorded['steps'][start+i][1]['action']
            assert all(s['status'] == 'ACTIVE' for s in frame)
            clock['step'] = start+i-1
            env.step([copy.deepcopy(s['action']) for s in frame])
            assert env.state == frame, f'native frame mismatch at {start+i}'
    rows = []
    first = rep['steps'][0][0]['observation']
    for relative in range(turns//24):
        before, after = [rep['steps'][k][0]['observation'] for k in (relative*24, (relative+1)*24)]
        chosen = [e for e in events if start+relative*24 <= e['step'] < start+(relative+1)*24]
        counts = Counter()
        for e in chosen:
            counts[e['op'], e['item']] += e['units']
        row = dict(game=game, morning=day, diagnostic=diagnostic, arm=arm, relative_day=relative+1,
            day=day+relative, **value_change(before, after),
            cumulative_value_plus_assets=value_change(first, after)['value_plus_assets'],
            cumulative_dawn_value_change=wealth(after)-wealth(first),
            crops_planted=sum(counts['PLANT', c] for c in CROPS), fertilizer_applied=counts['FERTILIZE', 'FERTILIZER'])
        row.update({f'planted_{c.lower()}': counts['PLANT', c] for c in CROPS})
        row.update({f'harvested_{p.lower()}': counts['HARVEST', p] for p in PRODUCTS})
        rows.append(row)
    opening = Counter()
    for e in events:
        if start <= e['step'] < start+3:
            opening[e['op'], e['item']] += e['units']
    # Seed conservation is independent of the callback's farm-object identity.
    last = rep['steps'][-1][0]['observation']
    for crop in CROPS:
        bought = sum(e['units'] for e in events if e['op'] == 'BUY_SEED' and e['item'] == crop)
        planted = sum(e['units'] for e in events if e['op'] == 'PLANT' and e['item'] == crop)
        assert first['private']['seeds'].get(crop, 0)+bought-planted == last['private']['seeds'].get(crop, 0)
    third = rep['steps'][3][0]['observation']
    assert opening['HIRE', 'WORKER'] == third['farms'][0]['hires_today']-first['farms'][0]['hires_today']
    assert opening['BUY_LAND', 'QUADRANT'] == len(third['farms'][0]['unlocked_quadrants'])-len(first['farms'][0]['unlocked_quadrants'])
    for crop in CROPS:
        assert (first['private']['seeds'].get(crop, 0)+opening['BUY_SEED', crop]-opening['PLANT', crop]
                == third['private']['seeds'].get(crop, 0))
    def animals_held(obs, animal):
        return (obs['private']['shed'].get(animal, 0)+sum(b.get(animal, 0) for b in obs['private']['inventories'])
                +sum(t.get('animal') == animal for row in obs['farms'][0]['tiles'] for t in row if isinstance(t, dict)))
    for animal in ANIMALS:
        assert opening['BUY_ANIMAL', animal] == animals_held(third, animal)-animals_held(first, animal)
    purchases = {**{f'buy_seed_{c.lower()}': opening['BUY_SEED', c] for c in CROPS},
        **{f'buy_animal_{a.lower()}': opening['BUY_ANIMAL', a] for a in ANIMALS},
        'buy_land': opening['BUY_LAND', 'QUADRANT'], 'hires': opening['HIRE', 'WORKER']}
    if diagnostic == 'D6':
        rows[0].update(purchases)
    return dict(rows=rows, opening_purchases=purchases, successful_events=events)


def expected_teacher_steps(start, diagnostic, arm):
    if diagnostic == 'D4':
        return list(range(start, start+(72 if arm == 'C' else 24))) if arm in ('B', 'C') else []
    return list(range(start+(3 if arm == '3' else 0), start+24)) if arm != '1' else []


def generate(game, day, diagnostic, arm):
    assert game in GAMES
    recorded, source_sha = source(SOURCE/f'{game}.json')
    pin_weeds(True)
    actor = make_player('mix:fourth:units' if diagnostic == 'D6' and arm == '4' else 'template')
    actor.restore(copy.deepcopy(memories(game)[day]))
    use_teacher = bool(expected_teacher_steps(day*24, diagnostic, arm))
    teacher = None
    if use_teacher:
        from kagml.opponents import load
        teacher = load('fourth')
        teacher.reset(int(recorded['info']['seed']))
    env = env_from_snapshot(snapshot_from_replay(recorded, day*24))
    events, steps, milliseconds, warm_steps = [], [], [], []
    policy = teacher.play.POL if teacher else None
    original = policy.night_room_value if teacher else None
    if teacher:
        policy.night_room_value = overflow_guard(original, policy.ANIMALS, events)

    def checked_teacher(obs, configuration):
        begun = time.perf_counter()
        action = copy.deepcopy(teacher(copy.deepcopy(obs), configuration))
        milliseconds.append((time.perf_counter()-begun)*1000)
        valid_action(action)
        steps.append(int(obs['day'])*24+int(obs['hour']))
        assert teacher.play._FLOW[0]['act'] == action
        return action

    if isinstance(actor, Mix):
        actor.other = checked_teacher
    try:
        for offset in range(72 if diagnostic == 'D4' else 24):
            obs = copy.deepcopy(env.state[0].observation)
            if diagnostic == 'D4':
                teaching = arm == 'C' or (arm == 'B' and offset < 24)
                if arm == 'B' and offset < 24:
                    # Feed actual pre-decision observations, in order; discard template answers.
                    actor(copy.deepcopy(obs), env.configuration)
                    warm_steps.append(day*24+offset)
            else:
                teaching = arm == '2' or (arm == '3' and offset >= 3)
                if arm == '3' and offset == 3:
                    teacher.reset(int(recorded['info']['seed']))
            action = checked_teacher(obs, env.configuration) if teaching else actor(obs, env.configuration)
            valid_action(action)
            env.step([copy.deepcopy(action), copy.deepcopy(recorded['steps'][day*24+offset+1][1]['action'])])
    finally:
        if teacher:
            policy.night_room_value = original
    assert steps == expected_teacher_steps(day*24, diagnostic, arm)
    assert warm_steps == (list(range(day*24, day*24+24)) if diagnostic == 'D4' and arm == 'B' else [])
    diagnostics = teacher.diagnostics() if teacher else {'fallbacks': 0, 'search_errors': 0}
    assert not diagnostics['fallbacks'] and not diagnostics['search_errors']
    rep = env.toJSON()
    rep['steps'] = rep['steps'][day*24:]
    rep['diagnostic'] = dict(game=game, day=day, diagnostic=diagnostic, arm=arm,
        source_sha256=source_sha, teacher_seed=recorded['info']['seed'], compatibility_events=events)
    measurement = measure(rep, recorded)
    return rep, dict(measurement=measurement, teacher_steps=steps, teacher_ms=milliseconds,
        template_actual_warm_steps=warm_steps, diagnostics=diagnostics, compatibility_events=events,
        source_sha256=source_sha, steps_sha256=digest(rep['steps']), measurement_sha256=digest(measurement))


def one(job):
    game, day, diagnostic, arm, signature, repeat = job
    key = case_id(game, day, diagnostic, arm)
    folder = LOG/('repeat' if repeat else 'runs')
    target, receipt = folder/f'{key}.json.gz', folder/f'{key}.receipt.json'
    begun = time.perf_counter()
    try:
        source_sha = sha(SOURCE/f'{game}.json')
        if receipt.exists() and not repeat:
            old = json.loads(receipt.read_bytes())
            if (old.get('reason') == 'kept' and old['signature'] == signature and old['source_sha256'] == source_sha
                    and target.is_file() and sha(target) == old['replay_sha256']):
                return {**old, 'resumed': True}
        rep, result = generate(game, day, diagnostic, arm)
        packed = gzip.compress(compact(rep).encode(), compresslevel=6, mtime=0)
        tmp = target.with_suffix('.tmp')
        tmp.write_bytes(packed)
        tmp.replace(target)
        result.update(reason='kept', game=game, morning=day, diagnostic=diagnostic, arm=arm,
            file=str(target), replay_sha256=sha(target), signature=signature)
    except Exception as error:
        import traceback
        result = dict(reason='error', game=game, morning=day, diagnostic=diagnostic, arm=arm,
            error=f'{type(error).__name__}: {error}', traceback=traceback.format_exc(), signature=signature)
    result['seconds'] = time.perf_counter()-begun
    save_json(receipt, result)
    return result


def main():
    ap = argparse.ArgumentParser(__doc__)
    ap.add_argument('--smoke', action='store_true')
    ap.add_argument('--workers', type=int, choices=(1, 2), default=2)
    args = ap.parse_args()
    os.environ['PYTHONHASHSEED'] = '0'
    for folder in (LOG, LOG/'runs', LOG/'repeat'):
        folder.mkdir(parents=True, exist_ok=True)
    signature, hashes, versions = dependencies()
    sources = {str(SOURCE/f'{g}.json'): sha(SOURCE/f'{g}.json') for g in GAMES}
    if not args.smoke:
        smoke = json.loads((LOG/'smoke.json').read_bytes())
        assert smoke['signature'] == signature and smoke['source_hashes'] == sources
        assert smoke['outcomes'] == {'kept': 21} and smoke['determinism_cases'] == 21
        checked = json.loads((LOG/'smoke-check.json').read_bytes())
        assert checked['signature'] == signature and checked['exact_benchmark_rows'] == 6
    cases = [(g, d, diag, arm) for diag, arms in ARMS.items() for g in GAMES
             for d in range(6, 27 if diag == 'D4' else 29) for arm in arms]
    if args.smoke:
        cases = [(g, d, diag, arm) for g, d in SMOKE for diag, arms in ARMS.items() for arm in arms]
    jobs = [(*case, signature, False) for case in cases]
    begun = time.perf_counter()
    results = []
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for result in pool.map(one, jobs, chunksize=1):
            results.append(result)
            if len(results)%21 == 0 or result['reason'] != 'kept' or len(results) == len(jobs):
                print(compact(dict(completed=len(results), total=len(jobs), seconds=time.perf_counter()-begun,
                    outcomes=dict(Counter(r['reason'] for r in results)),
                    errors=[r['error'] for r in results if 'error' in r][-2:])), flush=True)
    repeated = []
    if args.smoke and all(r['reason'] == 'kept' for r in results):
        # A new worker pool proves state/seed resets across fresh processes.
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            repeated = list(pool.map(one, [(*case, signature, True) for case in cases], chunksize=1))
        for a, b in zip(results, repeated):
            assert b['reason'] == 'kept', b
            assert a['steps_sha256'] == b['steps_sha256'] and a['measurement'] == b['measurement'], 'determinism failure'
    summary = dict(seconds=time.perf_counter()-begun, cases=len(results), workers=args.workers,
        signature=signature, dependency_hashes=hashes, versions=versions, source_hashes=sources,
        outcomes=dict(Counter(r['reason'] for r in results)), determinism_cases=len(repeated),
        teacher_turns=sum(len(r.get('teacher_steps', [])) for r in results),
        compatibility_events=[dict(game=r['game'], morning=r['morning'], diagnostic=r['diagnostic'], arm=r['arm'], **e)
                              for r in results for e in r.get('compatibility_events', [])],
        resumed=sum(r.get('resumed', False) for r in results), failures=[r for r in results if r['reason'] != 'kept'])
    save_json(LOG/('smoke.json' if args.smoke else 'full.json'), summary)
    print(compact({k: v for k, v in summary.items() if k not in ('dependency_hashes', 'source_hashes')}), flush=True)
    if summary['failures']:
        raise SystemExit('Diagnostics runs failed; see receipts on D:')


if __name__ == '__main__':
    main()

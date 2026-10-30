"""Exact recorded-action replay and D1 Parquet extraction. No agent code is invoked."""
import contextlib
import copy
import csv
import gzip
import hashlib
import io
import json
import random
import time
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import kaggle_environments
    import kaggle_environments.envs.kaggriculture.kaggriculture as K

from kagml.paths import data_root, datasets

VERSION = 1
TABLES = ('games', 'market_steps', 'farm_daily', 'unit_actions', 'sales', 'market_orders')
ORIGINAL = {n: getattr(K, n) for n in ('_apply_unit_action', '_commit_unit', '_do_hire', '_do_buy_land', '_parse_order', '_spawn_weeds')}


def compact(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True)


def snapshot(farm, private, unit):
    pos = K._farmer_position(farm, unit)
    if pos is None:
        return None
    tile = farm['tiles'][pos[1]][pos[0]]
    return (tuple(pos), tile.copy() if isinstance(tile, dict) else tile,
            private['inventories'][unit].copy(), private['shed'].copy(), private['seeds'].copy())


def replay(rep, meta, mode='native', *, segment=False):
    if kaggle_environments.__version__ != '1.32.7':
        raise ValueError('requires kaggle-environments==1.32.7')
    rows = {t: [] for t in TABLES}
    states = [SimpleNamespace(observation=SimpleNamespace(step=0, player=p), action={}, status='ACTIVE', reward=0) for p in (0, 1)]
    config = SimpleNamespace(**rep['configuration'])
    env = SimpleNamespace(configuration=config, info={'seed': rep['info']['seed']}, done=False)
    if segment:
        first = rep['steps'][0]
        start_step = int(first[0]['observation']['step'])
        if start_step < 0 or len(rep['steps']) < 2:
            raise ValueError('segment requires a nonnegative snapshot step and following actions')
        for p in (0, 1):
            obs = copy.deepcopy(first[p]['observation'])
            if obs['day'] * config.turnsPerDay + obs['hour'] != start_step:
                raise ValueError('snapshot day/hour disagrees with step')
            states[p].observation = SimpleNamespace(**obs)
            states[p].status, states[p].reward = first[p]['status'], first[p]['reward']
        for field in ('farms', 'market', 'town'):
            setattr(states[1].observation, field, getattr(states[0].observation, field))
    else:
        start_step = 0
        K._initialize(states, env)
    episode = int(meta['episode'])
    current = {'step': 0, 'seat': 0, 'orders': {}, 'counter': [0, 0]}

    def base(seat=None):
        return {'episode': episode, 'step': current['step'], 'seat': current['seat'] if seat is None else seat}

    def apply(farm, private, unit, action, *args, **kwargs):
        seat = next(p for p in (0, 1) if states[p].observation.private is private)
        before = snapshot(farm, private, unit)
        money = farm['money']
        result = ORIGINAL['_apply_unit_action'](farm, private, unit, action, *args, **kwargs)
        issued = states[seat].action or {}
        commands = issued.get('hands', [])
        issued = issued.get('farmer', ['PASS']) if unit == 0 else commands[unit - 1]
        pos = before[0] if before else (None, None)
        rows['unit_actions'].append({**base(seat), 'unit': unit, 'x': pos[0], 'y': pos[1],
            'command': compact(issued), 'effective_command': compact(action),
            'took_effect': before != snapshot(farm, private, unit), 'exists': before is not None, 'cash_delta': farm['money'] - money})
        return result

    def parse(order):
        seat, row = current['lookup'][id(order)]
        current['orders'][seat] = row
        row['attempted'] = True
        return ORIGINAL['_parse_order'](order)

    def commit(op, item, price, farm, private, market, *args):
        seat = next(p for p in (0, 1) if states[p].observation.private is private)
        ok = ORIGINAL['_commit_unit'](op, item, price, farm, private, market, *args)
        if ok:
            order = current['orders'][seat]
            order['units'] += 1
            order['cash_delta'] += price if op == 'SELL' else -price
            order['took_effect'] = True
            if op == 'SELL':
                key = (seat, order['order_index'], item, price)
                sales[key] += 1
        return ok

    def special(name, farm, *args):
        seat = next(p for p in (0, 1) if states[0].observation.farms[p] is farm)
        money = farm['money']
        result = ORIGINAL[name](farm, *args)
        order = current['orders'][seat]
        order['cash_delta'] += farm['money'] - money
        order['took_effect'] = farm['money'] != money
        order['units'] = int(order['took_effect'])
        return result

    K._apply_unit_action = apply
    K._parse_order = parse
    K._commit_unit = commit
    K._do_hire = lambda farm, *args: special('_do_hire', farm, *args)
    K._do_buy_land = lambda farm, *args: special('_do_buy_land', farm, *args)
    if mode == 'split-weeds':
        K._spawn_weeds = lambda farm, n, chance, rng: ORIGINAL['_spawn_weeds'](farm, n, chance, random.Random(rng.random()))
    try:
        for offset, recorded in enumerate(rep['steps']):
            index = start_step + offset
            if offset:
                current.update(step=index - 1, parsed=0, orders={})
                sales = Counter()
                current['lookup'] = {}
                prior_positions = [[list(f['farmer']), *[list(x) for x in f['hands']]] for f in states[0].observation.farms]
                prior_cash = [f['money'] for f in states[0].observation.farms]
                action_start = len(rows['unit_actions'])
                order_start = len(rows['market_orders'])
                for p in (0, 1):
                    states[p].action = recorded[p].get('action')
                    states[p].observation.step = index - 1
                    action = states[p].action or {}
                    orders = action.get('market', [])
                    if isinstance(orders, list):
                        for order_index, order in enumerate(orders):
                            row = {**base(p), 'order_index': order_index, 'command': compact(order), 'units': 0, 'cash_delta': 0.0, 'took_effect': False, 'attempted': False}
                            rows['market_orders'].append(row)
                            current['lookup'][id(order)] = (p, row)
                K.interpreter(states, env)
                for p in (0, 1):
                    issued = states[p].action or {}
                    hands = issued.get('hands', [])
                    supplied = len(hands) if isinstance(hands, list) else 0
                    for unit in range(supplied + 1, len(prior_positions[p])):
                        pos = prior_positions[p][unit]
                        rows['unit_actions'].append({**base(p), 'unit': unit, 'x': pos[0], 'y': pos[1], 'command': compact(['PASS']), 'effective_command': compact(['PASS']), 'took_effect': False, 'exists': True, 'cash_delta': 0.0})
                    delta = sum(r['cash_delta'] for t, start in (('unit_actions', action_start), ('market_orders', order_start)) for r in rows[t][start:] if r['seat'] == p)
                    if prior_cash[p] + delta != states[0].observation.farms[p]['money']:
                        raise ValueError(f'cash bridge failed at {index} seat {p}')
                for (seat, order, product, price), units in sales.items():
                    rows['sales'].append({**base(seat), 'order_index': order, 'product': product, 'units': units, 'price': price, 'revenue': units * price})
            for p in (0, 1):
                actual = vars(states[p].observation)
                expected = recorded[p]['observation']
                for field in ('farms', 'market', 'town', 'private', 'day', 'hour', 'player'):
                    if actual[field] != expected[field]:
                        return None, {'reason': 'state_mismatch', 'step': index, 'seat': p, 'field': field, 'mode': mode}
                if states[p].status != recorded[p]['status'] or states[p].reward != recorded[p]['reward']:
                    return None, {'reason': 'status_reward_mismatch', 'step': index, 'seat': p, 'mode': mode}
            obs = states[0].observation
            rows['market_steps'].append({'episode': episode, 'step': index, 'day': obs.day, 'hour': obs.hour,
                **{f'price_{k.lower()}': v for k, v in obs.market['prices'].items()},
                **{f'inventory_{k.lower()}': v for k, v in obs.market['inventory'].items()},
                'cash_0': obs.farms[0]['money'], 'cash_1': obs.farms[1]['money']})
            if obs.hour == 0:
                for seat, farm in enumerate(obs.farms):
                    for y, line in enumerate(farm['tiles']):
                        for x, tile in enumerate(line):
                            t = tile if isinstance(tile, dict) else {}
                            planted = t.get('planted_day', t.get('placed_day'))
                            rows['farm_daily'].append({'episode': episode, 'seat': seat, 'day': obs.day, 'step': index, 'x': x, 'y': y,
                                'kind': t.get('kind', tile if tile else 'EMPTY'), 'crop': t.get('crop'),
                                'age': obs.day - planted if planted is not None else None, 'animal': t.get('animal'),
                                'yield_units': t.get('yield_units'), 'watered': t.get('watered_today'), 'fed': t.get('fed_today'),
                                'cared': t.get('cared_today'), 'fertilized_until_day': t.get('fertilized_until_day'),
                                'fertilizer_available': t.get('fertilizer_available'), 'care_bonus': t.get('pending_care_bonus'),
                                'hands': compact(farm['hands']), 'land': compact(farm['unlocked_quadrants'])})
        if not segment and any(s.status != 'DONE' for s in states):
            return None, {'reason': 'incomplete_game', 'mode': mode}
        banks = [f['money'] for f in states[0].observation.farms]
        if any(float(meta[f'reward_{p}']) != banks[p] for p in (0, 1)):
            return None, {'reason': 'manifest_reward_mismatch', 'mode': mode}
        rows['games'].append({'episode': episode, 'date': meta['created'],
            **{f'{field}_{p}': int(meta[f'{source}_{p}']) if field in ('submission', 'team') else float(meta[f'{source}_{p}'])
               for p in (0, 1) for field, source in (('submission', 'sub'), ('team', 'team'), ('rating', 'rating'))},
            'bank_0': banks[0], 'bank_1': banks[1], 'winner': 0 if banks[0] > banks[1] else 1 if banks[1] > banks[0] else -1,
            'shops': states[0].observation.town['unlocked_shops'], 'rng_mode': mode, 'frames': len(rep['steps'])})
        return rows, {'reason': 'kept', 'mode': mode, 'frames': len(rep['steps'])}
    finally:
        for name, function in ORIGINAL.items():
            setattr(K, name, function)


# Fixed schemas prevent all-null early-game columns acquiring incompatible types.
SCHEMAS = {
    'games': [('episode',pa.int64()),('date',pa.string()),*[(f'{f}_{p}',pa.float64() if f=='rating' else pa.int64()) for p in (0,1) for f in ('submission','team','rating')],('bank_0',pa.float64()),('bank_1',pa.float64()),('winner',pa.int64()),('shops',pa.list_(pa.string())),('rng_mode',pa.string()),('frames',pa.int64())],
    'market_steps': [('episode',pa.int64()),('step',pa.int64()),('day',pa.int64()),('hour',pa.int64()),*[(f'{f}_{k.lower()}',pa.int64()) for f in ('price','inventory') for k in K.PRODUCTS],('cash_0',pa.float64()),('cash_1',pa.float64())],
    'farm_daily': [(k, pa.string() if k in ('kind','crop','animal','hands','land') else pa.bool_() if k in ('watered','fed','cared','fertilizer_available') else pa.int64()) for k in ('episode','seat','day','step','x','y','kind','crop','age','animal','yield_units','watered','fed','cared','fertilized_until_day','fertilizer_available','care_bonus','hands','land')],
    'unit_actions': [(k,pa.string() if k in ('command','effective_command') else pa.float64() if k == 'cash_delta' else pa.bool_() if k in ('took_effect','exists') else pa.int64()) for k in ('episode','step','seat','unit','x','y','command','effective_command','took_effect','exists','cash_delta')],
    'sales': [(k,pa.int64()) for k in ('episode','step','seat','order_index','product','units','price','revenue')],
    'market_orders': [(k,pa.string() if k=='command' else pa.bool_() if k in ('took_effect','attempted') else pa.float64() if k=='cash_delta' else pa.int64()) for k in ('episode','step','seat','order_index','command','units','cash_delta','took_effect','attempted')],
}
SCHEMAS['sales'][4] = ('product', pa.string())


def build_one(task):
    meta, output, signature = task
    root = Path(output)
    eid = meta['episode']
    receipt = root / 'audit' / f'{eid}.json'
    if receipt.exists():
        old = json.loads(receipt.read_text())
        if old.get('signature') == signature and old.get('sha256') == meta['sha256']:
            if old['reason'] != 'kept' or all((root/t/f'{eid}.parquet').exists() for t in TABLES):
                return old
    start = time.perf_counter()
    result = {'episode': int(eid), 'folder': meta['folder'], 'sub_0': meta['sub_0'], 'sub_1': meta['sub_1'], 'sha256': meta['sha256'], 'signature': signature}
    try:
        source = data_root() / 'raw' / 'replays' / meta['folder'] / f'{eid}.json.gz'
        raw = source.read_bytes()
        if hashlib.sha256(raw).hexdigest() != meta['sha256']:
            raise ValueError('manifest SHA256 mismatch')
        rep = json.loads(gzip.decompress(raw))
        rows, audit = replay(rep, meta)
        if rows is None and audit['reason'] == 'state_mismatch' and audit['field'] in ('farms','town'):
            rows, second = replay(rep, meta, 'split-weeds')
            if rows is not None:
                audit = second
        result.update(audit)
        if rows is not None:
            result['rows'] = {}
            for table, values in rows.items():
                path = root / table / f'{eid}.parquet'
                tmp = path.with_suffix('.tmp')
                pq.write_table(pa.Table.from_pylist(values, schema=pa.schema(SCHEMAS[table])), tmp, compression='zstd')
                tmp.replace(path)
                result['rows'][table] = len(values)
    except Exception as error:
        result.update(reason='error', error=f'{type(error).__name__}: {error}')
    if result['reason'] != 'kept':
        for table in TABLES:
            (root/table/f'{eid}.parquet').unlink(missing_ok=True)
    result['seconds'] = round(time.perf_counter()-start, 3)
    tmp = receipt.with_suffix('.tmp')
    tmp.write_text(compact(result), encoding='utf-8')
    tmp.replace(receipt)
    return result


def connect(root=None):
    """DuckDB connection with views over accepted game shards; only visible state for sales features."""
    import duckdb
    root = Path(root) if root else datasets() / 'd1'
    db = duckdb.connect(config={'threads': 2})
    for table in TABLES:
        path = str(root / table / '*.parquet').replace("'", "''")
        db.execute(f"CREATE VIEW {table} AS SELECT * FROM read_parquet('{path}')")
    return db

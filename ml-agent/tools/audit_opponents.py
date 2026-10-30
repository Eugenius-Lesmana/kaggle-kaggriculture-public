"""Verify D2 replay evidence before summarising; optionally rerun only rejected games.
python tools/audit_opponents.py [--rerun --metav4 <main.py>] [--workers 2]
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import json
from pathlib import Path
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'src'))
from kagml.paths import runs
from kagml.opponents import NAMES
from check_opponents import SB, one

CONTROL_FLOW = {'GeneratorExit', 'StopIteration', 'StopAsyncIteration'}


def verify(path, name, control, seed, seat):
    m = json.loads(path.read_text())
    assert (m['name'], m['control'], m['seed'], m['seat']) == (name, control, seed, seat), 'metric identity'
    with gzip.open(str(path).replace('.metrics.json', '.json.gz'), 'rt') as f:
        r = json.load(f)
    assert r['info']['seed'] == seed, 'replay seed'
    assert len(r['steps']) == m['steps'] == 720, 'incomplete replay'
    assert [s['status'] for s in r['steps'][-1]] == m['statuses'] == ['DONE', 'DONE'], 'terminal status'
    daily = defaultdict(Counter)
    for step, frame in enumerate(r['steps'][:-1]):
        obs = frame[seat]['observation']
        assert obs['player'] == seat and obs['day'] * 24 + obs['hour'] == step, 'seat/clock'
        action = r['steps'][step + 1][seat]['action']
        assert isinstance(action, dict), 'missing action'
        row = daily[obs['day']]; row['turns'] += 1
        for command in [action.get('farmer', [])] + list(action.get('hands') or []):
            if command and command[0] != 'PASS':
                row['non_pass'] += 1; row['op_' + command[0]] += 1
        row['market_orders'] += len(action.get('market') or [])
    assert {str(k):dict(v) for k,v in daily.items()} == m['timing']['daily'], 'daily activity differs'
    assert len(m['timing']['turn_ms']) == m['timing']['turns'] == 719, 'timing coverage'
    assert all(t >= 0 for t in m['timing']['turn_ms']), 'negative timing'
    assert sum(v['non_pass'] for v in daily.values()) > 0, 'all unit actions PASS'
    assert sum(v['market_orders'] for v in daily.values()) > 0, 'no market orders'
    assert not m['diagnostics']['fallbacks'] and not m['diagnostics']['search_errors'], 'policy fallback/search error'
    traced = seed == 10301 and seat == 0 and control == 'metav4'
    assert m['exception_tracing'] == traced, 'proof tracing coverage'
    errors = [e for e in m['exceptions'] if e['type'] not in CONTROL_FLOW]
    assert not errors, f'non-control-flow policy exception: {errors}'
    farms = r['steps'][-1][0]['observation']['farms']
    banks = [farms[seat]['money'], farms[1-seat]['money']]
    assert banks == m['banks'] and m['margin'] == banks[0] - banks[1], 'banks/margin'
    assert m['win'] == (banks[0] > banks[1]) and m['tie'] == (banks[0] == banks[1]), 'win/tie'
    shops = r['steps'][144][0]['observation']['town']['unlocked_shops'][:2]
    assert m['early_shops'] == shops and m['buyers'] == sum(s in SB for s in shops), 'shop scenario'
    return {'name':name,'control':control,'seed':seed,'seat':seat,'buyers':m['buyers'],
            'non_pass':sum(v['non_pass'] for v in daily.values()),
            'market_orders':sum(v['market_orders'] for v in daily.values()),
            'zero_non_pass_days':[k for k,v in daily.items() if not v['non_pass']],
            'zero_market_days':[k for k,v in daily.items() if not v['market_orders']]}


def audit(root):
    accepted, rejected = [], []
    for name in NAMES:
        for control in ('metav4','template'):
            for seed in range(10301,10313):
                for seat in (0,1):
                    path=root/f'{name}-{control}-{seed}-seat{seat}.metrics.json'
                    try:
                        accepted.append(verify(path,name,control,seed,seat))
                    except (OSError,ValueError,KeyError,TypeError,AssertionError) as error:
                        rejected.append({'name':name,'control':control,'seed':seed,'seat':seat,'error':str(error)})
    scenarios=defaultdict(set)
    for row in accepted:scenarios[row['seed']].add(row['buyers'])
    assert all(len(v)==1 for v in scenarios.values()), 'paired scenarios differ'
    return {'accepted':len(accepted),'rejected':len(rejected),'games':accepted,'failures':rejected,
            'exception_scope':'One traced full game per policy; other games validated through actions and fallback diagnostics.'}


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--tag',default='d2-opponents-2026-10-17')
    p.add_argument('--rerun',action='store_true');p.add_argument('--metav4',type=Path)
    p.add_argument('--workers',type=int,choices=(1,2),default=2)
    args=p.parse_args();root=runs()/args.tag
    assert root.is_dir(), root
    result=audit(root)
    if args.rerun and result['failures']:
        if not args.metav4 or not args.metav4.is_file():p.error('--rerun requires --metav4')
        jobs=[(r['name'],r['control'],str(args.metav4 if r['control']=='metav4' else REPO/'vendor/template_agent/main.py'),r['seed'],r['seat'],str(root)) for r in result['failures']]
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for row in pool.map(one,jobs):print(json.dumps(row),flush=True)
        result=audit(root)
    (root/'verification.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({k:v for k,v in result.items() if k not in ('games','failures')}))
    if result['rejected']:raise SystemExit('Rejected games: see verification.json; rerun with --rerun')

if __name__=='__main__':main()

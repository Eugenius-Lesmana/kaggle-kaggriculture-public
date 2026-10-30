"""Package V: exact saved-game diagnostics, no policy calls. PYTHONHASHSEED=0.
python tools/v4_diagnostics.py [--smoke] [--workers 2]
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
from pathlib import Path
import sys
import time
REPO=Path(__file__).resolve().parents[1];sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from kagml import replay_tables as RT
from kagml.paths import data_root
from market_pressure import cases as old_cases,gameplay,sha
ROOT=data_root();OUT=ROOT/'runs/v4-diagnostics'
CROPS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON');ANIMALS=('GOOSE','COW','SHEEP');PRODUCTS=tuple(RT.K.PRODUCTS)


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_bytes(gzip.compress(RT.compact(value).encode(),mtime=0));tmp.replace(path)


def load(path):return json.loads(gzip.decompress(Path(path).read_bytes()))


def identity(tile):
    if not isinstance(tile,dict):return None
    if tile.get('animal'):return ['ANIMAL',tile['animal'],tile['placed_day']]
    if tile.get('kind')=='PLANT':return ['PLANT',tile['crop'],tile['planted_day']]
    return None


def inventory():
    found=old_cases()
    for p in sorted((ROOT/'runs/full-netv4g').glob('*.metrics.json')):
        m=json.loads(p.read_bytes());assert m['name']=='net:board-v4:guard' and m['steps']==720 and m['statuses']==['DONE','DONE'];assert not m['policy_errors'] and not m['opponent_errors']
        raw=Path(str(p).replace('.metrics.json','.json.gz'));found.append(dict(group='v4',seed=m['seed'],seat=m['seat'],metrics=str(p),raw=str(raw),metrics_sha256=sha(p),raw_sha256=sha(raw)))
    assert len(found)==192 and len({(x['group'],x['seed'],x['seat']) for x in found})==192
    for g in ('v4','teacher','v3fw','template'):assert {(x['seed'],x['seat']) for x in found if x['group']==g}=={(s,p) for s in range(20001,20025) for p in (0,1)}
    return sorted(found,key=lambda x:(x['group'],x['seed'],x['seat']))


def selection(cases):
    chosen=[];used=set()
    for outcome in ('loss','win'):
        for seat in (0,1):
            eligible=[c for c in cases if c['group']=='v4' and c['seat']==seat and (json.loads(Path(c['metrics']).read_bytes())['margin']<0)==(outcome=='loss')]
            for c in eligible:
                if c['seed'] in used:continue
                chosen.append({**c,'outcome':outcome});used.add(c['seed'])
                if sum(x['outcome']==outcome and x['seat']==seat for x in chosen)==2:break
    assert len(chosen)==8 and len(used)==8;return chosen


def signature():return hashlib.sha256(b''.join(p.read_bytes() for p in (Path(__file__),Path(RT.__file__),Path(RT.K.__file__)))).hexdigest()


def extract(rep):
    original=dict(RT.ORIGINAL);interpreter=RT.K.interpreter;endday=RT.K._end_of_day;clock={};services=[];nights=[]
    def interpret(states,env):
        clock.update(step=int(states[0].observation.step),farms=states[0].observation.farms)
        return interpreter(states,env)
    def apply(farm,private,unit,action,*args,**kwargs):
        before=RT.snapshot(farm,private,unit);tile=copy.deepcopy(before[1]) if before else None
        result=original['_apply_unit_action'](farm,private,unit,action,*args,**kwargs)
        if before and action and action[0] in ('FEED','WATER') and before!=RT.snapshot(farm,private,unit):
            services.append(dict(step=clock['step'],seat=next(p for p in (0,1) if clock['farms'][p] is farm),unit=unit,kind=action[0],x=before[0][0],y=before[0][1],identity=identity(tile)))
        return result
    def night(states,env,day):
        o=states[0].observation;nights.append(dict(day=day,tiles=copy.deepcopy([f['tiles'] for f in o.farms]),prices=dict(o.market['prices'])))
        return endday(states,env,day)
    RT.K.interpreter=interpret;RT.K._end_of_day=night;RT.ORIGINAL['_apply_unit_action']=apply
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']];meta=dict(episode=1,created='',**{f'{k}_{p}':banks[p] if k=='reward' else -1 for p in (0,1) for k in ('reward','sub','team','rating')})
    try:rows,audit=RT.replay(rep,meta,'split-weeds');assert rows is not None,audit
    finally:
        RT.ORIGINAL.clear();RT.ORIGINAL.update(original);RT.K.interpreter=interpreter;RT.K._end_of_day=endday
        for n,f in original.items():setattr(RT.K,n,f)
    native=[(r['step'],r['seat'],r['unit'],json.loads(r['effective_command'])[0],r['x'],r['y']) for r in rows['unit_actions'] if r['took_effect'] and json.loads(r['effective_command'])[0] in ('FEED','WATER')]
    assert native==[(r['step'],r['seat'],r['unit'],r['kind'],r['x'],r['y']) for r in services]
    return rows,audit,services,nights


def one(c):
    t=time.perf_counter();target=OUT/'cases'/f"{c['group']}-{c['seed']}-seat{c['seat']}.json.gz";sig=signature()
    if target.exists():
        old=load(target)
        if old['source']==c and old['signature']==sig:return dict(source=c,seconds=old['seconds'],resumed=True)
    assert sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'];rep=load(c['raw']);m=json.loads(Path(c['metrics']).read_bytes());seat=c['seat']
    assert len(rep['steps'])==720 and rep['info']['seed']==c['seed'] and gameplay(rep)==m['gameplay_sha256']
    rows,audit,services,nights=extract(rep);days=[];cash=Counter();sales=Counter()
    for r in rows['market_orders']:cash[r['seat'],r['step']//24]+=r['cash_delta']
    for r in rows['unit_actions']:cash[r['seat'],r['step']//24]+=r['cash_delta']
    for r in rows['sales']:
        for field in ('units','revenue'):sales[r['seat'],r['step']//24,r['product'],field]+=r[field]
    for day in range(30):
        first=rep['steps'][day*24][0]['observation'];last=rep['steps'][min((day+1)*24,719)][0]['observation']
        for p in (0,1):
            f=first['farms'][p];tiles=[t for line in f['tiles'] for t in line if isinstance(t,dict)];r=dict(day=day,role='ours' if p==seat else 'metav4',cash=f['money'],end_cash=last['farms'][p]['money'],land=len(f['unlocked_quadrants']),hands=len(f['hands']),crops=sum(t.get('kind')=='PLANT' for t in tiles),animals=sum(bool(t.get('animal')) for t in tiles))
            r.update({'crop_'+s.lower():sum(t.get('crop')==s for t in tiles) for s in CROPS});r.update({'animal_'+s.lower():sum(t.get('animal')==s for t in tiles) for s in ANIMALS})
            assert r['cash']+cash[p,day]==r['end_cash'],(c,day,p,'daily cash bridge')
            r['net_cash']=cash[p,day]
            for s in PRODUCTS:
                for field in ('units','revenue'):r[field+'_'+s.lower()]=sales[p,day,s,field]
            r['revenue']=sum(r['revenue_'+s.lower()] for s in PRODUCTS);r['net_spending']=r['revenue']-r['net_cash'];days.append(r)
    banks=[rep['steps'][-1][0]['observation']['farms'][p]['money'] for p in (seat,1-seat)];assert banks==m['banks']
    fingerprint=hashlib.sha256(RT.compact(dict(town=[f[0]['observation']['town'] for f in rep['steps']],initial_market=rep['steps'][0][0]['observation']['market'],config={k:v for k,v in rep['configuration'].items() if k not in ('seed','actTimeout','runTimeout')})).encode()).hexdigest()
    value=dict(source=c,signature=sig,banks=banks,margin=banks[0]-banks[1],early_shops=m['early_shops'],town_fingerprint=fingerprint,days=days,services=services if c['group']=='v4' else [],nights=nights if c['group']=='v4' else [],audit=audit,seconds=time.perf_counter()-t)
    save(target,value);return dict(source=c,seconds=value['seconds'],resumed=False)


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--workers',type=int,choices=(1,2),default=2);p.add_argument('--smoke',action='store_true');a=p.parse_args();assert os.environ.get('PYTHONHASHSEED')=='0'
    cases=inventory();chosen=selection(cases);OUT.mkdir(parents=True,exist_ok=True);(OUT/'sources.json').write_text(RT.compact(cases));(OUT/'guard-selection.json').write_text(RT.compact(chosen))
    jobs=[c for c in cases if c['seed']==20001 and c['seat']==0] if a.smoke else cases;t=time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,r in enumerate(pool.map(one,jobs)):
            if (i+1)%12==0:print(RT.compact(dict(cases=i+1,seconds=time.perf_counter()-t)),flush=True)
    for c in jobs:assert sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256']
    summary=dict(cases=len(jobs),seconds=time.perf_counter()-t,signature=signature());(OUT/f"{'smoke' if a.smoke else 'full'}.json").write_text(RT.compact(summary));print(RT.compact(summary),flush=True)

if __name__=='__main__':main()

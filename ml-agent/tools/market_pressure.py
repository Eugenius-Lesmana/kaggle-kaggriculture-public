"""Package M. Analyze only saved games; never instantiate or call a policy.
PYTHONHASHSEED=0 KAGML_DATA=... python tools/market_pressure.py --workers 2
"""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'src'))
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[key]='1'
from kagml import replay_tables as RT
from kagml.paths import data_root
ROOT=data_root();OUT=ROOT/'runs/market-pressure'
PRODUCTS=tuple(RT.K.PRODUCTS)
SOURCES=(('teacher','full-teacher','fourth',20001,20024),
         ('v3fw','full-v3fw-d628','model:ranker-v3-fw:d6-28',20001,20012),
         ('v3fw','full-v3fw-d628-b','model:ranker-v3-fw:d6-28',20013,20024),
         ('template','overnight-g-fresh','template',20001,20024))


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):return hashlib.sha256(RT.compact(value).encode()).hexdigest()
def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(RT.compact(value),encoding='utf-8');tmp.replace(path)


def signature():
    return digest({str(p):sha(p) for p in (Path(__file__),Path(RT.__file__),Path(RT.K.__file__))})


def cases():
    found=[]
    for group,folder,name,lo,hi in SOURCES:
        pattern='template-*.metrics.json' if group=='template' else '*.metrics.json'
        rows=[]
        for p in sorted((ROOT/'runs'/folder).glob(pattern)):
            m=json.loads(p.read_bytes())
            assert m['name']==name and lo<=m['seed']<=hi and m['seat'] in (0,1),(p,m['name'])
            assert m['control']=='metav4' and m['steps']==720 and m['statuses']==['DONE','DONE']
            assert not m.get('policy_errors') and not m.get('opponent_errors') and not any(m['diagnostics'].values())
            raw=Path(str(p).replace('.metrics.json','.json.gz'));assert raw.is_file(),raw
            rows.append(dict(group=group,seed=m['seed'],seat=m['seat'],metrics=str(p),raw=str(raw),
                metrics_sha256=sha(p),raw_sha256=sha(raw)))
        assert {(r['seed'],r['seat']) for r in rows}=={(s,p) for s in range(lo,hi+1) for p in (0,1)}
        found.extend(rows)
    assert len(found)==144 and len({(r['group'],r['seed'],r['seat']) for r in found})==144
    assert len({json.loads(Path(r['metrics']).read_bytes())['opponent'] for r in found})==1
    return found


def gameplay(rep):
    return digest([[{k:({a:b for a,b in v.items() if a!='remainingOverageTime'} if k=='observation' else v)
                    for k,v in seat.items()} for seat in frame] for frame in rep['steps']])


def native(rep):
    original=dict(RT.ORIGINAL);interpreter=RT.K.interpreter
    clock={};trades=[];harvest=Counter();planted=Counter();failed=Counter()
    def interpret(state,env):
        clock.update(step=int(state[0].observation.step),farms=state[0].observation.farms,
                     lookup={id(o):(p,i) for p in (0,1) for i,o in enumerate((state[p].action or {}).get('market',[]))},
                     current={},rounds=Counter())
        return interpreter(state,env)
    def parse(order):
        p,i=clock['lookup'][id(order)];clock['current'][p]=i
        return original['_parse_order'](order)
    def commit(op,item,price,farm,private,market,*args):
        p=next(p for p in (0,1) if clock['farms'][p] is farm);i=clock['current'][p]
        clock['rounds'][p,i]+=1;iteration=clock['rounds'][p,i]
        before_stock=market['inventory'].get(item)
        ok=original['_commit_unit'](op,item,price,farm,private,market,*args)
        if ok:trades.append((clock['step'],p,i,iteration,op,item,price,before_stock))
        else:failed[p,clock['step']//144,op,item]+=1
        return ok
    def apply(farm,private,unit,action,*args,**kwargs):
        pos=RT.K._farmer_position(farm,unit);p=next(p for p in (0,1) if clock['farms'][p] is farm)
        op=action[0] if action else 'PASS';bag=dict(private['inventories'][unit]) if pos is not None else {}
        tile=copy_tile(farm,pos);result=original['_apply_unit_action'](farm,private,unit,action,*args,**kwargs)
        if pos is not None:
            after=private['inventories'][unit]
            if op in ('HARVEST','COLLECT_FERTILIZER'):
                for item,n in after.items():
                    if n>bag.get(item,0):harvest[p,clock['step']//144,item]+=n-bag.get(item,0)
            if op=='PLANT' and tile!=copy_tile(farm,pos):planted[p,clock['step']//144,action[1]]+=1
        return result
    RT.K.interpreter=interpret
    RT.ORIGINAL.update(_parse_order=parse,_commit_unit=commit,_apply_unit_action=apply)
    try:
        banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
        meta=dict(episode=1,created='',**{f'{k}_{p}':v for p in (0,1) for k,v in [('reward',banks[p]),('sub',0),('team',0),('rating',0)]})
        rows,audit=RT.replay(rep,meta,'split-weeds')
        assert rows is not None,audit
    finally:
        RT.ORIGINAL.clear();RT.ORIGINAL.update(original);RT.K.interpreter=interpreter
        for name,fn in original.items():setattr(RT.K,name,fn)
    return rows,audit,trades,harvest,planted,failed


def copy_tile(farm,pos):
    if pos is None:return None
    t=farm['tiles'][pos[1]][pos[0]]
    return dict(t) if isinstance(t,dict) else t


def one(case):
    begun=time.perf_counter();key=f"{case['group']}-{case['seed']}-seat{case['seat']}"
    target=OUT/'cases'/f'{key}.json.gz';sig=signature()
    if target.exists():
        old=json.loads(gzip.decompress(target.read_bytes()))
        if old['source']==case and old['signature']==sig:return dict(key=key,seconds=old['seconds'],resumed=True)
    assert sha(case['raw'])==case['raw_sha256'] and sha(case['metrics'])==case['metrics_sha256']
    m=json.loads(Path(case['metrics']).read_bytes());rep=json.loads(gzip.decompress(Path(case['raw']).read_bytes()))
    assert len(rep['steps'])==720 and rep['info']['seed']==case['seed'] and gameplay(rep)==m['gameplay_sha256']
    seat=case['seat'];banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    assert m['banks']==[banks[seat],banks[1-seat]] and [s['status'] for s in rep['steps'][-1]]==['DONE','DONE']
    rows,audit,trades,harvest,planted,failed=native(rep)
    # Independently captured successful per-unit commits must reproduce audited D1 totals.
    actual=Counter();quoted={};ties=0
    sales=defaultdict(Counter);timing=defaultdict(Counter);sell_orders=defaultdict(dict)
    for step,p,index,iteration,op,item,price,stock in trades:
        actual[p,step,index,op,item,'units']+=1;actual[p,step,index,op,item,'cash']+=price*(-1 if op!='SELL' else 1)
        if op=='SELL':
            band=step//144;v=sales[p,band,item];v['units']+=1;v['revenue']+=price;v['floor_units']+=int(price==1);v['unit_hours']+=step%24
            sell_orders[step,item].setdefault(p,index)
            qkey=(step,index,iteration,item);other=quoted.get(qkey)
            if other is not None:
                assert other[0]!=p and other[1]==price,'lockstep same-position quotes differ';ties+=1
            quoted[qkey]=(p,price)
    orders=defaultdict(Counter)
    for r in rows['market_orders']:
        cmd=json.loads(r['command']);op=cmd[0] if isinstance(cmd,list) and cmd else 'INVALID';item=cmd[1] if isinstance(cmd,list) and len(cmd)>1 else '_';p=r['seat'];step=r['step'];index=r['order_index']
        if op not in ('HIRE','BUY_LAND'):
            assert r['units']==actual[p,step,index,op,item,'units'] and r['cash_delta']==actual[p,step,index,op,item,'cash']
        v=orders[p,step//144,op,item];v['units']+=r['units'];v['cash']+=r['cash_delta'];v['orders']+=1;v['effect_orders']+=int(r['took_effect'])
    native_sales=Counter()
    for r in rows['sales']:native_sales[r['seat'],r['step']//144,r['product'],'units']+=r['units'];native_sales[r['seat'],r['step']//144,r['product'],'revenue']+=r['revenue']
    for k,v in sales.items():
        assert v['units']==native_sales[*k,'units'] and v['revenue']==native_sales[*k,'revenue']
    for (step,item),indices in sell_orders.items():
        if len(indices)==2:
            v=timing[step//144,item];v['both_sell_turns']+=1
            v['ours_first']+=int(indices[seat]<indices[1-seat]);v['metav4_first']+=int(indices[seat]>indices[1-seat]);v['same_position']+=int(indices[seat]==indices[1-seat])
    unitcash=Counter()
    for r in rows['unit_actions']:unitcash[r['seat'],r['step']//144,json.loads(r['effective_command'])[0]]+=r['cash_delta']
    farm=defaultdict(Counter);path=defaultdict(Counter)
    for step,frame in enumerate(rep['steps'][:-1]):
        obs=frame[0]['observation'];band=step//144;hour=step%24
        assert (obs['day'],obs['hour'])==divmod(step,24)
        for item in PRODUCTS:
            v=path[band,hour,item];v['n']+=1;v['stock']+=obs['market']['inventory'][item];v['price']+=obs['market']['prices'][item]
        for p in (0,1):
            v=farm[p,band];v['n']+=1;v['hands']+=len(obs['farms'][p]['hands']);v['land']+=len(obs['farms'][p]['unlocked_quadrants'])
            for line in obs['farms'][p]['tiles']:
                for tile in line:
                    if isinstance(tile,dict):
                        if tile.get('kind')=='PLANT':v['crop_'+tile['crop']]+=1
                        if tile.get('animal'):v['animal_'+tile['animal']]+=1
    for p in (0,1):
        assert rep['steps'][0][0]['observation']['farms'][p]['money']+sum(v['cash'] for (q,*_),v in orders.items() if q==p)+sum(v for (q,*_),v in unitcash.items() if q==p)==banks[p]
    result=dict(source=case,signature=sig,banks=m['banks'],audit=audit,same_position_unit_quote_pairs=ties,
        sales=[dict(seat=p,band=b,product=item,**v) for (p,b,item),v in sales.items()],
        orders=[dict(seat=p,band=b,op=op,item=item,**v) for (p,b,op,item),v in orders.items()],
        timing=[dict(band=b,product=item,**v) for (b,item),v in timing.items()],
        unitcash=[dict(seat=p,band=b,op=op,cash=v) for (p,b,op),v in unitcash.items() if v],
        farm=[dict(seat=p,band=b,**v) for (p,b),v in farm.items()],
        path=[dict(band=b,hour=h,product=item,price=v['price']/v['n'],stock=v['stock']/v['n'],n=v['n']) for (b,h,item),v in path.items()],
        harvest=[dict(seat=p,band=b,product=item,units=n) for (p,b,item),n in harvest.items()],
        planted=[dict(seat=p,band=b,product=item,units=n) for (p,b,item),n in planted.items()],
        failures=[dict(seat=p,band=b,op=op,item=item,attempts=n) for (p,b,op,item),n in failed.items()],
        native_sales=rows['sales'],native_orders=rows['market_orders'],
        seconds=time.perf_counter()-begun)
    tmp=target.with_suffix('.tmp');tmp.write_bytes(gzip.compress(RT.compact(result).encode(),mtime=0));tmp.replace(target)
    return dict(key=key,seconds=result['seconds'],resumed=False)


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--workers',type=int,choices=(1,2),default=2);ap.add_argument('--smoke',action='store_true');args=ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0'
    OUT.mkdir(parents=True,exist_ok=True);(OUT/'cases').mkdir(exist_ok=True)
    items=cases();selected=items if not args.smoke else [next(c for c in items if c['group']==g and c['seed']==20001 and c['seat']==s) for g in ('teacher','v3fw','template') for s in (0,1)]
    begun=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results=[]
        for r in pool.map(one,selected,chunksize=1):
            results.append(r)
            if len(results)%12==0 or len(results)==len(selected):print(RT.compact(dict(completed=len(results),total=len(selected),seconds=time.perf_counter()-begun)),flush=True)
    assert all(sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'] for c in items),'existing run inputs changed'
    summary=dict(cases=len(selected),workers=args.workers,seconds=time.perf_counter()-begun,resumed=sum(r['resumed'] for r in results),signature=signature(),sources=items)
    save(OUT/('smoke.json' if args.smoke else 'full.json'),summary)
    print(RT.compact({k:v for k,v in summary.items() if k!='sources'}),flush=True)


if __name__=='__main__':main()

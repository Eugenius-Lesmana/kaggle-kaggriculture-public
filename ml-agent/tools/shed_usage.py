"""S: native audit of recorded non-test teacher shed decisions; no policy inference.
python tools/shed_usage.py [--smoke] --workers 2
"""
import argparse
from collections import Counter,defaultdict
import copy
import csv
import gzip
import hashlib
import json
from multiprocessing import Pool
import os
from pathlib import Path
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'src'))
from kagml import replay_tables as RT
from kagml.paths import data_root,runs
import pyarrow.parquet as pq

DATA=data_root();OUT=runs()/'overnight-s-complete';TOOLS=('WHEAT','FERTILIZER');OPS=('PICKUP','DROP','PLACE')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()


def save(path,value):
    tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,separators=(',',':')),encoding='utf8');tmp.replace(path)


def signature():
    return digest({str(p):sha(p) for p in (Path(__file__),REPO/'src/kagml/replay_tables.py',Path(RT.K.__file__),
        REPO/'manifests/ownfarm.csv',REPO/'manifests/takeover-model-ranker-own-v1.csv')})


def validate_case(m):
    g,d,h=m['game'],m['day'],m['H']
    assert g in range(10301,10320) and d in range(6,29) and m['seat']==0,'non-test teacher cases only'
    assert h in ((0,) if m['source']=='L1' else (4,8,12,16))
    assert m['episode']==g*100+d if h==0 else m['episode']==g*10000+d*100+h
    expected=f'raw/ownfarm/fourth/{g}-d{d}.json.gz' if h==0 else f'raw/takeover/model-ranker-own-v1/{g}-d{d}-h{h}.json.gz'
    assert m['file']==expected and m['cutoff']==d*24+h and m['end']==(d+1)*24


def cases(smoke=False):
    result=[]
    for source,name in (('L1','ownfarm.csv'),('L3','takeover-model-ranker-own-v1.csv')):
        with (REPO/'manifests'/name).open() as f:
            reader=csv.reader(f);header=next(reader);game_index=header.index('game')
            for values in reader:
                game=int(values[game_index])
                if game not in range(10301,10320):continue
                r=dict(zip(header,values));day=int(r['day'])
                if smoke and (game,day)!=(10301,8):continue
                h=int(r.get('H',0))
                m=dict(source=source,game=game,day=day,H=h,seat=int(r['seat']),episode=int(r['episode']),file=r['file'],
                    raw_sha256=r['sha256'],cutoff=int(r.get('takeover_step',r['start_step'])),end=int(r['end_step']),
                    end_cash_0=float(r['end_cash_0']),end_cash_1=float(r['end_cash_1']))
                validate_case(m);result.append(m)
    return result


def context(farm,private,unit,day):
    tiles=[t for row in farm['tiles'] for t in row if isinstance(t,dict)]
    plants=[t for t in tiles if t.get('kind')=='PLANT']
    need={'WHEAT':sum(bool(t.get('animal')) and not t.get('fed_today') for t in tiles),
          'FERTILIZER':sum(t.get('fertilized_until_day',-1)<day for t in plants)}
    for a,definition in RT.K.ANIMALS.items():
        need[a]=sum(t.get('kind')==definition['structure'] and 'animal' not in t for t in tiles)
    other_qty=Counter();other_workers=Counter();workers=len(farm['hands'])+1
    for i,bag in enumerate(private['inventories'][:workers]):
        if i!=unit:
            other_qty.update({k:n for k,n in bag.items() if n>0});other_workers.update(k for k,n in bag.items() if n>0)
    return dict(needs=need,fert_legal=len(plants),other_qty=dict(other_qty),other_workers=dict(other_workers),workers=workers)


def observe(rep,cutoff,episode):
    """Bind the actual native-interpreter farm, then observe each real unit operation."""
    native_apply=RT.ORIGINAL['_apply_unit_action'];native_interpreter=RT.K.interpreter
    native_night_drop=RT.K._drop_inventories_to_shed
    trace=[];clock={}
    def interpreter(state,env):
        clock.update(step=int(state[0].observation.step),farm=state[0].observation.farms[0],private=state[0].observation.private)
        return native_interpreter(state,env)
    def apply(farm,private,unit,action,*args,**kwargs):
        if farm is not clock.get('farm') or clock['step']<cutoff:
            return native_apply(farm,private,unit,action,*args,**kwargs)
        size,day=args[:2];step=clock['step'];op=action[0] if action else 'PASS'
        pos=RT.K._farmer_position(farm,unit)
        before={k:n for k,n in private['inventories'][unit].items() if n>0} if pos is not None else {}
        at_shed=bool(pos is not None and RT.K._is_shed_adjacent(tuple(pos),size))
        tile=farm['tiles'][pos[1]][pos[0]] if pos is not None else None
        item=action[1] if len(action)>1 else None
        animal_place=(op=='PLACE' and item in RT.K.ANIMALS and isinstance(tile,dict)
                      and tile.get('kind')==RT.K.ANIMALS[item]['structure'] and 'animal' not in tile)
        shed_place=op=='PLACE' and at_shed and not animal_place
        special=op in ('PICKUP','DROP') or shed_place
        keeper=at_shed and any(before.get(k,0)>0 for k in TOOLS)
        ctx=context(farm,private,unit,day) if special or keeper else {}
        shed_before=dict(private['shed']) if special else {}
        result=native_apply(farm,private,unit,action,*args,**kwargs)
        after={k:n for k,n in private['inventories'][unit].items() if n>0} if pos is not None else {}
        added={k:max(0,after.get(k,0)-before.get(k,0)) for k in after if after.get(k,0)>before.get(k,0)}
        used={}
        if op=='FEED':used={'WHEAT':max(0,before.get('WHEAT',0)-after.get('WHEAT',0))}
        if op=='FERTILIZE':used={'FERTILIZER':max(0,before.get('FERTILIZER',0)-after.get('FERTILIZER',0))}
        if animal_place:used={item:max(0,before.get(item,0)-after.get(item,0))}
        trace.append(dict(step=step,hour=step%24,unit=unit,command=list(action),op=op,pos=list(pos) if pos is not None else None,
            exists=pos is not None,at_shed=at_shed,shed_place=shed_place,special=special,keeper=keeper,
            deposit=at_shed and (op=='DROP' or shed_place),before=before,after=after,added=added,used=used,ctx=ctx,
            shed_before=shed_before,shed_after=dict(private['shed']) if special else {}))
        return result
    def night_drop(private,capacity):
        own=private is clock.get('private') and clock['step']>=cutoff
        bags=[{k:n for k,n in b.items() if n>0} for b in private['inventories']] if own else []
        result=native_night_drop(private,capacity)
        if own:
            assert all(not b for b in private['inventories'])
            for unit,before in enumerate(bags):
                trace.append(dict(step=clock['step']+1,hour=24,unit=unit,op='NIGHT_RETURN',command=['NIGHT_RETURN'],pos=None,
                    exists=True,at_shed=False,shed_place=False,special=False,keeper=False,deposit=True,deposit_kind='overnight',
                    before=before,after={},added={},used={},ctx={},shed_before={},shed_after={}))
        return result
    RT.K.interpreter=interpreter;RT.ORIGINAL['_apply_unit_action']=apply
    RT.K._drop_inventories_to_shed=night_drop
    try:
        farms=rep['steps'][-1][0]['observation']['farms']
        meta=dict(episode=episode,created='2026-10-24',**{f'{k}_{p}':v for p in (0,1)
                  for k,v in (('reward',farms[p]['money']),('sub',0),('team',0),('rating',0.0))})
        rows,check=RT.replay(rep,meta,mode='split-weeds',segment=True)
        assert check['reason']=='kept',check
    finally:
        RT.ORIGINAL['_apply_unit_action']=native_apply;RT.K._apply_unit_action=native_apply;RT.K.interpreter=native_interpreter
        RT.K._drop_inventories_to_shed=native_night_drop
    return rows,check,trace


def followup(records,index,item):
    current=records[index];future=records[index+1:]
    next_drop=next((r for r in future if r['deposit']),None)
    limit=next_drop['step'] if next_drop else float('inf')
    until=[r for r in future if r['step']<limit]
    first_use=None;censor='window'
    if current['after'].get(item,0)<=0:censor='not_acquired'
    else:
        for r in future:
            if r['used'].get(item,0)>0:first_use=r;censor=None;break
            if r['after'].get(item,0)<=0:censor='overnight_return' if r.get('deposit_kind')=='overnight' else 'returned';break
    adds=sum(r['added'].get(item,0) for r in until);used=sum(r['used'].get(item,0) for r in until)
    result=dict(first_use_lag=first_use['step']-current['step'] if first_use else None,
        use_censor=censor,
        next_drop_lag=next_drop['step']-current['step'] if next_drop else None,
        next_drop_kind=next_drop.get('deposit_kind','command') if next_drop else None,
        left_before_next_drop=next_drop['before'].get(item,0) if next_drop else None,
        removed_at_next_drop=max(0,next_drop['before'].get(item,0)-next_drop['after'].get(item,0)) if next_drop else None,
        kept_after_next_drop=next_drop['after'].get(item,0) if next_drop else None,
        additions_before_next_drop=adds,used_before_next_drop=used,
        clean_cohort=current['before'].get(item,0)==0 and adds==0)
    if next_drop and current['op']=='PICKUP' and current['exists']:
        picked=max(0,current['after'].get(item,0)-current['before'].get(item,0))
        assert current['before'].get(item,0)+picked+adds-used==result['left_before_next_drop'],'pickup flow balance'
    return result


def extract(trace,identity):
    byunit=defaultdict(list)
    for t in trace:byunit[t['unit']].append(t)
    events=[];keeps=[]
    for unit,records in byunit.items():
        for index,t in enumerate(records):
            op,cmd=t['op'],t['command'];ctx=t['ctx']
            base=dict(**identity,step=t['step'],hour=t['hour'],unit=unit,event_id=f"{identity['source']}-{identity['episode']}-{t['step']}-{unit}")
            goods=sum(n for k,n in t['before'].items() if k in RT.K.PRODUCTS and k not in TOOLS)
            def features(item):
                needed=ctx['needs'].get(item,0);other=ctx['other_qty'].get(item,0)
                return dict(open_jobs=needed,legal_jobs=ctx['fert_legal'] if item=='FERTILIZER' else needed,
                    other_carried=other,other_workers_carrying=ctx['other_workers'].get(item,0),uncovered_jobs=max(0,needed-other),
                    n_workers=ctx['workers'],goods_before=goods)
            if t['special']:
                items=(cmd[1] if len(cmd)>1 else 'UNKNOWN',) if op!='DROP' else tuple(t['before']) or ('EMPTY',)
                for item in items:
                    amount=max(0,(t['after'].get(item,0)-t['before'].get(item,0)) if op=='PICKUP' else (t['before'].get(item,0)-t['after'].get(item,0)))
                    received=t['shed_after'].get(item,0)-t['shed_before'].get(item,0)
                    if op=='PICKUP':assert amount==-received
                    else:assert 0<=received<=amount
                    row=dict(**base,op=op,item=item,amount=amount,requested=(cmd[2] if len(cmd)>2 else 1) if op!='DROP' else None,
                        carried_before=t['before'].get(item,0),bag_before=t['before'],at_shed=t['at_shed'],exists=t['exists'],
                        shed_available=t['shed_before'].get(item,0),shed_received=received,
                        discarded=0 if op=='PICKUP' else amount-received,**features(item))
                    if op=='PICKUP':row.update(followup(records,index,item))
                    events.append(row)
            if t['keeper']:
                for item in TOOLS:
                    if t['before'].get(item,0)<=0:continue
                    intent_return=t['deposit'] and (op=='DROP' or (len(cmd)>1 and cmd[1]==item))
                    decision=('return' if intent_return else 'pickup_more' if op=='PICKUP' and len(cmd)>1 and cmd[1]==item
                              else 'use' if t['used'].get(item,0)>0 else 'keep')
                    keeps.append(dict(**base,item=item,decision=decision,op=op,held=t['before'][item],held_after=t['after'].get(item,0),
                        removed=max(0,t['before'][item]-t['after'].get(item,0)),**features(item)))
    return events,keeps


def key(m):return f"{m['source']}-{m['game']}-d{m['day']}-h{m['H']}"


def one(m):
    validate_case(m);assert os.environ.get('PYTHONHASHSEED')=='0'
    raw=DATA/m['file'];folder='ownfarm' if m['source']=='L1' else 'takeover/model-ranker-own-v1'
    parquet=DATA/'datasets'/folder/'unit_actions'/f"{m['episode']}.parquet"
    assert sha(raw)==m['raw_sha256'],'source replay changed'
    pq_sha=sha(parquet);sig=signature();target=OUT/'cases'/key(m);path=Path(str(target)+'.metrics.json');packed=Path(str(target)+'.json.gz')
    if path.exists():
        receipt=json.loads(path.read_text());assert receipt['signature']==sig and receipt['parquet_sha256']==pq_sha
        assert sha(packed)==receipt['output_sha256'];return receipt
    expected=pq.read_table(parquet,columns=['step','unit','x','y','effective_command','exists','took_effect'],
        filters=[('seat','=',0),('step','>=',m['cutoff']),('step','<',m['end'])]).to_pylist()
    with gzip.open(raw,'rt',encoding='utf8') as f:rep=json.load(f)
    assert rep['info']['seed']==m['game']
    # Reconstruct insertion order from the morning. A sorted serialized midpoint
    # loses bag order, which changes what an overflowing shed keeps at night.
    assert len(rep['steps'])==25
    assert rep['steps'][0][0]['observation']['step']==m['day']*24
    assert all(rep['steps'][-1][0]['observation']['farms'][p]['money']==m[f'end_cash_{p}'] for p in (0,1))
    tables,check,trace=observe(rep,m['cutoff'],m['episode'])
    actual=[r for r in tables['unit_actions'] if r['seat']==0 and r['step']>=m['cutoff']]
    fields=('step','unit','x','y','effective_command','exists','took_effect')
    normalize=lambda rows:sorted(tuple(tuple(json.loads(r[k])) if k=='effective_command' else r[k] for k in fields) for r in rows)
    assert normalize(expected)==normalize(actual),'teacher unit table differs from native replay'
    expected_ops={(r['step'],r['unit'],r['effective_command']) for r in expected if json.loads(r['effective_command'])[0] in OPS}
    observed_ops={(t['step'],t['unit'],RT.compact(t['command'])) for t in trace if t['op'] in OPS}
    assert expected_ops==observed_ops,'missing shed operation'
    assert {t['step'] for t in trace if t['unit']==0 and t['op']!='NIGHT_RETURN'}==set(range(m['cutoff'],m['end']))
    identity={k:m[k] for k in ('source','game','day','H','episode')}
    events,keeps=extract(trace,identity)
    assert len({r['event_id'] for r in events})==sum(t['special'] for t in trace)
    payload=dict(case=identity,events=events,keeps=keeps)
    with gzip.open(packed,'wt',encoding='utf8',compresslevel=1) as f:json.dump(payload,f,separators=(',',':'))
    receipt=dict(**identity,teacher_start=m['cutoff'],teacher_end=m['end'],teacher_turns=m['end']-m['cutoff'],
        signature=sig,raw_sha256=m['raw_sha256'],parquet_sha256=pq_sha,output_sha256=sha(packed),payload_sha256=digest(payload),native_check=check,
        unit_rows=len(expected),implicit_passes=len(expected)-sum(t['op']!='NIGHT_RETURN' for t in trace),automatic_return_records=sum(t['op']=='NIGHT_RETURN' for t in trace),shed_commands=len({r['event_id'] for r in events}),item_rows=len(events),keep_rows=len(keeps))
    save(path,receipt);return receipt


def game_job(items):
    totals=Counter()
    for m in items:
        r=one(m)
        for k in ('teacher_turns','unit_rows','shed_commands','item_rows','keep_rows'):totals[k]+=r[k]
    return dict(game=items[0]['game'],cases=len(items),**totals)


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--smoke',action='store_true');ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    a=ap.parse_args();assert os.environ.get('PYTHONHASHSEED')=='0';chosen=cases(a.smoke)
    expected=5 if a.smoke else 2185;assert len(chosen)==expected
    (OUT/'cases').mkdir(parents=True,exist_ok=True)
    groups=defaultdict(list)
    for m in chosen:groups[m['game']].append(m)
    start=time.perf_counter()
    with Pool(a.workers,maxtasksperchild=1) as pool:
        for result in pool.imap(game_job,list(groups.values())):print(json.dumps(result),flush=True)
    result=dict(cases=len(chosen),teacher_turns=sum(m['end']-m['cutoff'] for m in chosen),seconds=time.perf_counter()-start,
        workers=a.workers,hash_seed=0,signature=signature())
    save(OUT/('smoke.json' if a.smoke else 'run.json'),result);print(json.dumps(result),flush=True)


if __name__=='__main__':main()

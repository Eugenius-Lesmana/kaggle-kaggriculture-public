"""Package N: native-reconciled teacher turns. No teacher code is loaded.
python tools/build_turn_dataset.py --workers 2 [--smoke] [--verify]
"""
import argparse
import contextlib
import copy
import csv
from functools import lru_cache
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from concurrent.futures import ProcessPoolExecutor

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
from kagml import replay_tables as RT
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kagml import board_features as B
from kagml.paths import data_root
from kagml.work_data import load_replay
from build_ownfarm_dataset import warm_history,EL3
import numpy as np
import pyarrow.parquet as pq

ROOT=data_root()
OUT=ROOT/'datasets/turns'
SOURCES={'l1':'ownfarm','l3-r1':'takeover-model-ranker-own-v1','l3-r2':'takeover-model-ranker-v3-fw','l1-edge':'ownfarm-edge','l3-edge':'takeover-edge-model-ranker-v3-fw',
         'l3-net1':'takeover-net-board-v2-guard','l3-net2':'takeover-net-board-v4','l3-p1':'takeover-net-board-p1-market',
         'l3-n1':'takeover-n1-net-board-p2-market','l3-n2':'takeover-n2-net-board-p3-market','l3-n3':'takeover-n3-net-board-p4-market-overflow-endmask-endwork','l3-n4':'takeover-n4-net-board-p5-market-overflow-endmask-endwork'}  # l3-n1/n2/n3: rounds vs fifth-nflow from our own games (Claude, 2026-10-27); l3-net1: correction round for the whole-board network (Claude)
FIELDS=('source','game','day','H','split','file','turns','worker_decisions','sha256','episode','raw_file','raw_sha256','encoder_sha256')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def signature():
    return hashlib.sha256((REPO/'src/kagml/board_features.py').read_bytes()+(REPO/'tools/build_turn_dataset.py').read_bytes()).hexdigest()

@lru_cache(maxsize=1)
def parent(path):return load_replay(Path(path))

@lru_cache(maxsize=8)
def warm(path,seat,start):return warm_history(parent(path),seat,start)


def table_root(source):
    return ROOT/'datasets'/({'l1':'ownfarm','l1-edge':'ownfarm-edge','l3-r1':'takeover/model-ranker-own-v1','l3-r2':'takeover/model-ranker-v3-fw','l3-edge':'takeover-edge/model-ranker-v3-fw','l1more':'ownfarm-more','l3-net1':'takeover/net-board-v2-guard','l3-net2':'takeover/net-board-v4','l3-p1':'takeover/net-board-p1-market','l3-n1':'takeover-n1/net-board-p2-market','l3-n2':'takeover-n2/net-board-p3-market','l3-n3':'takeover-n3/net-board-p4-market-overflow-endmask-endwork','l3-n4':'takeover-n4/net-board-p5-market-overflow-endmask-endwork'}[source])

PARENTS={'l3-n1':'raw/src-n1','l3-n2':'raw/src-n2','l3-n3':'raw/src-n3','l3-n4':'raw/src-n4'}  # copies of the source games the rounds started from


SKIP={'105552606'}  # l3-n1 game 10555 d26 H6: the teacher reached 17 units, above the encoder's 14 (Claude, 2026-10-27)
CAPACITY=REPO/'manifests/capacity-skip.txt'  # more such episodes, one per line (round N3 on, Claude 2026-10-28)
if CAPACITY.exists():SKIP|={l.strip() for l in CAPACITY.read_text().split() if l.strip()}


def tasks(sources=None):
    jobs=[]
    for source,name in SOURCES.items():
        if sources and source not in sources:continue
        for r in csv.DictReader((REPO/'manifests'/f'{name}.csv').open()):
            if r['episode'] not in SKIP:jobs.append((source,r))
    return sorted(jobs,key=lambda j:(int(j[1]['game']),int(j[1]['day']),j[0],int(j[1].get('H',0))))


def job_value(obs,unit,command):
    farm=obs['farms'][int(obs['player'])];x,y=B.positions(farm)[unit];tile=farm['tiles'][y][x];op=command[0];prices=obs['market']['prices']
    if not isinstance(tile,dict):
        if op=='PLANT':
            c=B.CROPS[command[1]];return c['max_yield']*prices[command[1]]*(3 if c['ongoing'] else 1)-c['seed']
        return 0
    item=tile.get('crop',B.ANIMALS.get(tile.get('animal'),{}).get('product'))
    price=prices.get(item,0)
    if op=='HARVEST':return tile.get('yield_units',0)*price
    if op=='WATER':return price*(B.CROPS[item]['max_yield'] if tile.get('consecutive_unwatered',0)>=1 else 1)
    if op=='FEED':return price*(1+tile.get('pending_care_bonus',0))
    if op in ('CARE','FERTILIZE'):return price
    if op=='COLLECT_FERTILIZER':return prices['FERTILIZER']
    return 0


def arrays_for(source,r,stored=None):
    raw=ROOT/r['file']
    if sha(raw)!=r['sha256']:raise ValueError('raw hash mismatch')
    rep=load_replay(raw);seat=int(r['seat']);start=int(r['start_step']);cut=int(r.get('takeover_step',start));game=int(r['game'])
    parent_path=str(ROOT/'raw/template-games'/f'{game}.json.gz') if source=='l1more' else str(ROOT/PARENTS[source]/f'{game}.json') if source in PARENTS else str(EL3/f'{game}.json')
    history=B.History(warm(parent_path,seat,start));features=[];labels=[];times=[];previous=None
    native_interpreter=RT.K.interpreter
    # Morning bags are empty, so JSON key sorting has not lost live bag order here.
    assert all(not bag for s in rep['steps'][0] for bag in s['observation']['private']['inventories'])
    def interpreter(states,env):
        nonlocal previous
        obs=copy.deepcopy(vars(states[seat].observation));step=int(obs['step']);action=copy.deepcopy(states[seat].action or {})
        history.observe(obs,seat,previous)
        if step>=cut:
            idx=len(features)
            if stored is not None:
                assert int(stored['step'][idx])==step
                action['farmer']=B.decode(stored['command'][idx,0],stored['amount'][idx,0],stored['command_argc'][idx,0])
                action['hands']=[B.decode(stored['command'][idx,u],stored['amount'][idx,u],stored['command_argc'][idx,u]) for u in range(1,len(B.positions(obs['farms'][seat]))) if stored['command_issued'][idx,u]]
                states[seat].action['farmer']=action['farmer']
                states[seat].action['hands']=action['hands']
            t=time.perf_counter();features.append(B.encode(obs,seat,history));times.append((time.perf_counter()-t)*1000)
            farm,private=copy.deepcopy((obs['farms'][seat],obs['private']));commands=[action.get('farmer',['PASS']),*action.get('hands',[])];turn=[]
            for u,pos in enumerate(B.positions(farm)):
                cmd=commands[u] if u<len(commands) else ['PASS'];cid=B.command_id(cmd)
                mask=B.mask_for_state(farm,private,u,obs['day']);app=B.amount_applies(farm,u,cmd);before=copy.deepcopy(private['inventories'][u])
                value=job_value(obs,u,cmd);effect=B.apply(farm,private,u,cmd,obs['day'])
                if effect and not mask[cid]:raise AssertionError(('effective command masked',step,u,cmd))
                if cmd[0]!='PASS' and bool(mask[cid])!=effect:raise AssertionError(('mask/native disagreement',step,u,cmd))
                amount=int(cmd[2]) if len(cmd)>=3 and cmd[0] in ('PICKUP','PLACE') else 1
                transferred=sum(abs(private['inventories'][u].get(k,0)-before.get(k,0)) for k in set(before)|set(private['inventories'][u])) if app else 0
                turn.append(dict(command=cid,command_argc=len(cmd),command_issued=u<len(commands),amount=amount,amount_applicable=app,amount_class=amount-1 if app and 1<=amount<=5 else -1,amount_loss_mask=app and effect and 1<=amount<=5,took_effect=effect,command_loss_mask=effect or cmd[0]=='PASS',legal=mask,position=pos,target_value=value,transferred=transferred))
            labels.append(turn)
        previous=copy.deepcopy(action)
        return native_interpreter(states,env)
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    meta={'episode':r['episode'],'created':'',**{f'{k}_{p}':banks[p] if k=='reward' else -1 for p in (0,1) for k in ('reward','sub','team','rating')}}
    RT.K.interpreter=interpreter
    try:rows,audit=RT.replay(rep,meta,'split-weeds',segment=True)
    finally:RT.K.interpreter=native_interpreter
    if rows is None:raise AssertionError(audit)
    for table in RT.TABLES:
        expected=pq.read_table(table_root(source)/table/f"{r['episode']}.parquet").to_pylist()
        assert rows[table]==expected,(source,r['episode'],table)
    result={key:np.stack([f[key] for f in features]) for key in features[0]}
    n=len(features);result['step']=np.arange(cut,cut+n,dtype=np.int16)
    dtypes={'command':np.int16,'command_argc':np.int8,'command_issued':bool,'amount':np.int32,'amount_applicable':bool,'amount_class':np.int8,'amount_loss_mask':bool,'took_effect':bool,'command_loss_mask':bool,'legal':bool,'position':np.int16,'transferred':np.int32}
    for key,dtype in dtypes.items():
        shape=(n,B.MAX_UNITS,len(B.COMMANDS)) if key=='legal' else ((n,B.MAX_UNITS,2) if key=='position' else (n,B.MAX_UNITS))
        a=np.zeros(shape,dtype=dtype)
        if key in ('command','amount_class'):a.fill(-1)
        for t,turn in enumerate(labels):
            for u,label in enumerate(turn):a[t,u]=label[key]
        result[key]=a
    result['target']=np.full((n,B.MAX_UNITS),100,np.int16);result['target_step']=np.full((n,B.MAX_UNITS),-1,np.int16);result['target_command']=np.full((n,B.MAX_UNITS),-1,np.int16);result['target_value']=np.zeros((n,B.MAX_UNITS),np.float32);result['target_distance']=np.zeros((n,B.MAX_UNITS),np.int16)
    for u in range(B.MAX_UNITS):
        next_job=None
        for t in reversed(range(n)):
            if u>=len(labels[t]):continue
            label=labels[t][u];op=B.COMMANDS[label['command']][0];x,y=label['position']
            if label['took_effect'] and op not in (*B.MOVES,'PASS'):next_job=(x,y,int(result['step'][t]),label['command'],label['target_value'])
            if next_job is not None:
                a,b,s,c,v=next_job;result['target'][t,u]=b*10+a;result['target_step'][t,u]=s;result['target_command'][t,u]=c;result['target_value'][t,u]=v;result['target_distance'][t,u]=abs(x-a)+abs(y-b)
    # Independently extracted native rows agree with every stored worker command/effect.
    indexed={(x['step'],x['unit']):x for x in rows['unit_actions'] if x['seat']==seat and x['exists'] and x['step']>=cut}
    assert len(indexed)==int(result['unit_mask'].sum())
    for t,turn in enumerate(labels):
        for u,label in enumerate(turn):
            native=indexed[(cut+t,u)];assert native['took_effect']==label['took_effect']
            assert json.loads(native['command'])==B.decode(label['command'],label['amount'],label['command_argc'])
    if stored is not None:
        assert set(stored.files)==set(result)
        for key in result:np.testing.assert_array_equal(result[key],stored[key],err_msg=key)
    return result,dict(encode_ms=times,native_tables=6,frames=len(rep['steps']),effective=int(result['took_effect'].sum()),issued_noops=int((result['unit_mask']&~result['command_loss_mask']).sum()))


def one(task):
    source,r,verify,force=task;start=time.perf_counter();game=int(r['game']);day=int(r['day']);H=int(r.get('H',0));path=OUT/source/f'{game}-d{day}-h{H}.npz';receipt=OUT/'audit'/source/f'{game}-d{day}-h{H}.json';sig=signature()
    if not verify and not force and receipt.exists() and path.exists():
        old=json.loads(receipt.read_text())
        if old['signature']==sig and old['manifest']['raw_sha256']==r['sha256'] and old['manifest']['sha256']==sha(path):return old
    path.parent.mkdir(parents=True,exist_ok=True);receipt.parent.mkdir(parents=True,exist_ok=True)
    with np.load(path,allow_pickle=False) if verify else contextlib.nullcontext() as stored:
        arrays,audit=arrays_for(source,r,stored)
    if not verify:
        tmp=path.with_suffix('.tmp')
        with tmp.open('wb') as f:np.savez_compressed(f,**arrays)
        tmp.replace(path)
    row=dict(source=source,game=game,day=day,H=H,split='train' if game<=10314 or game>=10401 else ('analysis' if game<=10319 else 'test'),file=path.relative_to(ROOT).as_posix(),turns=len(arrays['step']),worker_decisions=int(arrays['unit_mask'].sum()),sha256=sha(path),episode=r['episode'],raw_file=r['file'],raw_sha256=r['sha256'],encoder_sha256=sha(REPO/'src/kagml/board_features.py'))
    result=dict(manifest=row,signature=sig,seconds=time.perf_counter()-start,**audit)
    if not verify:receipt.write_text(json.dumps(result,separators=(',',':')),encoding='utf-8')
    return result


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--workers',type=int,choices=range(1, 9),default=2);ap.add_argument('--smoke',action='store_true');ap.add_argument('--verify',action='store_true');ap.add_argument('--force',action='store_true');ap.add_argument('--sources',default='');a=ap.parse_args()
    if os.environ.get('PYTHONHASHSEED')!='0' and not a.verify:raise ValueError('set PYTHONHASHSEED=0 before starting')
    jobs=tasks(a.sources.split(',') if a.sources else None)
    if a.smoke:
        jobs=[j for j in jobs if int(j[1]['game'])==10301 and int(j[1]['day']) in (0,6,16,29) and int(j[1].get('H',4)) in (4,16)]
    t=time.perf_counter();results=[]
    with ProcessPoolExecutor(max_workers=a.workers) as pool:
        for i,result in enumerate(pool.map(one,[(s,r,a.verify,a.force) for s,r in jobs])):
            results.append(result)
            if (i+1)%100==0:print(json.dumps(dict(segments=i+1,seconds=round(time.perf_counter()-t,1))),flush=True)
    if not a.smoke and not a.verify:
        target=REPO/'manifests/turns.csv';new=[x['manifest'] for x in results]
        if target.exists():new=[r for r in csv.DictReader(target.open()) if r['source'] not in {s for s,r in jobs}]+new
        with target.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(sorted(new,key=lambda r:(r['source'],int(r['game']),int(r['day']),int(r['H']))))
    ms=[v for r in results for v in r['encode_ms']]
    summary=dict(segments=len(results),turns=sum(int(x['manifest']['turns']) for x in results),decisions=sum(int(x['manifest']['worker_decisions']) for x in results),seconds=round(time.perf_counter()-t,3),encode_ms=dict(median=float(np.median(ms)),p95=float(np.percentile(ms,95)),maximum=max(ms)),verify=a.verify,hashseed=os.environ.get('PYTHONHASHSEED'))
    print(json.dumps(summary),flush=True)
    log=ROOT/'runs/turns';log.mkdir(parents=True,exist_ok=True);(log/f"{'verify' if a.verify else 'build'}-{'smoke' if a.smoke else 'full'}-{os.environ.get('PYTHONHASHSEED')}.json").write_text(json.dumps(summary),encoding='utf-8')

if __name__=='__main__':main()

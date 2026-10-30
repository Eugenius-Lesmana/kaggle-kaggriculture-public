"""Package P market sidecars and new-source turn encoding. Never writes an existing worker NPZ.
PYTHONHASHSEED=0 KAGML_DATA=<data> python tools/plan_dataset.py markets|encode|check --workers 1
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import contextlib
import copy
import csv
from functools import lru_cache
import gzip
import hashlib
import json
import os
from pathlib import Path
import sys
import time

for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
REPO=Path(__file__).resolve().parents[1];sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
import build_turn_dataset as T
from build_ownfarm_dataset import warm_history
import plan_games as G
from kagml import replay_tables as RT
from kagml.work_data import load_replay
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
ROOT=G.ROOT;RUN=G.RUN;MARKET=ROOT/'datasets/turn-markets'
PRODUCTS=T.B.PRODUCTS;CROPS=T.B.CROP_NAMES;ANIMALS=T.B.ANIMAL_NAMES
VOCAB=tuple([('SELL',p) for p in PRODUCTS]+[('BUY_SEED',c) for c in CROPS]+[('BUY_ANIMAL',a) for a in ANIMALS]+[('BUY_PRODUCT',p) for p in PRODUCTS]+[('BUY_LAND',),('HIRE',)])
VID={k:i for i,k in enumerate(VOCAB)};VERSION=1
OLD_TABLES=T.table_root;OLD_WARM=T.warm


def read_csv(p):
    with Path(p).open() as f:return list(csv.DictReader(f))

def write_csv(p,rows):G.N.manifest(Path(p),list(rows[0]),rows)

def safe(game):
    game=int(game);assert game not in G.TEST,game;return game

def teacher_seat(row):
    if row['source']=='tfull':
        name=Path(row['file']).name;seat=int(name.split('-seat',1)[1].split('-',1)[0]);assert seat in (0,1)
        assert (int(row['episode'])%1000)//100==seat
        if 'seat' in row:assert int(row['seat'])==seat
        return seat
    return int(row.get('seat',0))


def dump_npz(path,a):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp')
    with tmp.open('wb') as f:np.savez_compressed(f,**a)
    tmp.replace(path)


def native(rep,episode):
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    meta={'episode':int(episode),'created':'',**{f'{k}_{s}':banks[s] if k=='reward' else -1 for s in (0,1) for k in ('reward','sub','team','rating')}}
    rows,audit=RT.replay(rep,meta,'split-weeds',segment=True)
    assert rows is not None,audit
    return rows,audit


def market_arrays(rep,seat,steps,orders,sales):
    steps=np.asarray(steps,dtype=np.int16);idx={int(s):i for i,s in enumerate(steps)};start=int(rep['steps'][0][0]['observation']['step'])
    issued=[rep['steps'][int(s)-start+1][seat]['action'].get('market',[]) or [] for s in steps]
    n=len(steps);width=max(1,max(map(len,issued),default=0));shape=(n,width)
    a=dict(step=steps,seat=np.full(n,seat,np.int8),units_issued=np.zeros((n,len(VOCAB)),np.int64),units_executed=np.zeros((n,len(VOCAB)),np.int64),
        order_token=np.full(shape,-1,np.int16),order_quantity=np.zeros(shape,np.int64),order_executed=np.zeros(shape,np.int64),order_mask=np.zeros(shape,bool),
        order_valid=np.zeros(shape,bool),order_attempted=np.zeros(shape,bool),order_took_effect=np.zeros(shape,bool),order_cash_delta=np.zeros(shape,np.float64),
        order_count=np.array(list(map(len,issued)),np.int16))
    raw=[['']*width for _ in steps];lookup={(r['step'],r['order_index']):r for r in orders if r['seat']==seat and r['step'] in idx}
    assert len(lookup)==sum(map(len,issued)),(len(lookup),sum(map(len,issued)))
    for t,oset in enumerate(issued):
        for j,order in enumerate(oset):
            r=lookup[(int(steps[t]),j)];assert json.loads(r['command'])==order
            a['order_mask'][t,j]=True;raw[t][j]=RT.compact(order)
            parsed=RT.K._parse_order(order);key=((order[0],) if order[0] in ('HIRE','BUY_LAND') else tuple(order[:2])) if isinstance(order,list) and order else ()
            token=VID.get(key,-1);quantity=1 if parsed and parsed['type'] in ('HIRE','BUY_LAND') else parsed.get('remaining',0) if parsed else 0
            valid=parsed is not None and token>=0 and not (key[0]=='BUY_PRODUCT' and key[1] not in ('WHEAT','FERTILIZER'))
            a['order_token'][t,j]=token;a['order_quantity'][t,j]=quantity;a['order_valid'][t,j]=valid
            for col,field in [('order_executed','units'),('order_attempted','attempted'),('order_took_effect','took_effect'),('order_cash_delta','cash_delta')]:a[col][t,j]=r[field]
            if token>=0:
                a['units_issued'][t,token]+=quantity;a['units_executed'][t,token]+=r['units']
            else:assert r['units']==0
            assert bool(r['units'])==r['took_effect']
            if not r['attempted']:assert not r['units'] and not r['took_effect'] and r['cash_delta']==0
    a['order_json']=np.asarray(raw,dtype=str)
    chosen=[r for r in sales if r['seat']==seat and r['step'] in idx]
    for name,field,dtype in [('sale_step','step',np.int16),('sale_order_index','order_index',np.int16),('sale_units','units',np.int64),('sale_unit_price','price',np.int64),('sale_revenue','revenue',np.int64)]:a[name]=np.array([r[field] for r in chosen],dtype=dtype)
    a['sale_product']=np.array([PRODUCTS.index(r['product']) for r in chosen],np.int8)
    sold=Counter();revenue=Counter()
    for r in chosen:
        assert r['revenue']==r['units']*r['price'];sold[r['step'],r['order_index']]+=r['units'];revenue[r['step'],r['order_index']]+=r['revenue']
    for key,r in lookup.items():
        order=json.loads(r['command'])
        if isinstance(order,list) and order and order[0]=='SELL':assert sold[key]==r['units'] and revenue[key]==r['cash_delta']
    a['buy_land_requested']=a['units_issued'][:,VID[('BUY_LAND',)]]>0
    a['buy_land_executed']=a['units_executed'][:,VID[('BUY_LAND',)]]>0
    return a


def existing_rows():return [r for r in read_csv(REPO/'manifests/turns.csv') if safe_metadata(r)]

def safe_metadata(r):return int(r['game']) not in G.TEST


def market_one(job):
    r,verify=job;game=safe(r['game']);worker=ROOT/r['file'];before=T.sha(worker);assert before==r['sha256']
    seat=teacher_seat(r);source=r['source'];stem=worker.stem;out=MARKET/source/f'{stem}.npz';receipt=RUN/'markets'/source/f'{stem}.json'
    if receipt.exists() and not verify:
        old=json.loads(receipt.read_text())
        if old['version']==VERSION and old['worker_sha256']==before and old['raw_sha256']==r['raw_sha256'] and out.exists() and T.sha(out)==old['sha256']:return old
    rep=load_replay(ROOT/r['raw_file']);assert T.sha(ROOT/r['raw_file'])==r['raw_sha256']
    if source=='l1bal':base=G.TABLES
    elif source=='tfull':base=ROOT/'datasets/teacher-full-days'
    else:base=OLD_TABLES(source)
    orders=pq.read_table(base/'market_orders'/f"{r['episode']}.parquet").to_pylist();sales=pq.read_table(base/'sales'/f"{r['episode']}.parquet").to_pylist()
    with np.load(worker,allow_pickle=False) as z:steps=z['step'].copy()
    a=market_arrays(rep,seat,steps,orders,sales)
    if verify:
        native_rows,audit=native(rep,r['episode'])
        assert native_rows['market_orders']==orders and native_rows['sales']==sales
        b=market_arrays(rep,seat,steps,native_rows['market_orders'],native_rows['sales'])
        for key in a:np.testing.assert_array_equal(a[key],b[key],err_msg=key)
        with np.load(out,allow_pickle=False) as z:
            assert set(z.files)==set(a)
            for key in a:np.testing.assert_array_equal(a[key],z[key],err_msg=key)
    else:dump_npz(out,a)
    assert T.sha(worker)==before
    row=dict(source=source,game=game,day=int(r['day']),H=int(r['H']),split=r['split'],seat=seat,file=out.relative_to(ROOT).as_posix(),sha256=T.sha(out),worker_file=r['file'],worker_sha256=before,raw_sha256=r['raw_sha256'],turns=len(steps),orders=int(a['order_mask'].sum()),executed_units=int(a['units_executed'].sum()),version=VERSION)
    if not verify:G.save(receipt,row)
    return row


def markets(workers,smoke=False,verify=False):
    rows=existing_rows();assert all(r['split'] in ('train','analysis','analysis2','endval') for r in rows)
    if smoke:
        selected=[]
        for s in sorted({r['source'] for r in rows}):selected.extend([r for r in rows if r['source']==s][:1])
        rows=selected
    start=time.perf_counter();results=[]
    if not smoke and not verify and (REPO/'manifests/turn-markets.csv').exists():  # reuse labels whose worker file is unchanged (also sources built by other tools, e.g. Codex's l1end)
        old={m['worker_file']:m for m in read_csv(REPO/'manifests/turn-markets.csv')}
        ok=lambda r:r['file'] in old and old[r['file']]['worker_sha256']==r['sha256'] and (ROOT/old[r['file']]['file']).exists()
        results=[dict(old[r['file']],split=r['split']) for r in rows if ok(r)];rows=[r for r in rows if not ok(r)]
        print(json.dumps(dict(stage='markets',reused=len(results),to_build=len(rows))),flush=True)
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for i,r in enumerate(pool.map(market_one,[(r,verify) for r in rows])):
            results.append(r)
            if (i+1)%100==0 or i+1==len(rows):print(json.dumps(dict(stage='market-verify' if verify else 'markets',segments=i+1,total=len(rows),seconds=round(time.perf_counter()-start,1))),flush=True)
    if not smoke and not verify:write_csv(REPO/'manifests/turn-markets.csv',results)
    G.save(RUN/f"markets-{'verify' if verify else 'build'}-{'smoke' if smoke else 'full'}.json",dict(segments=len(results),turns=sum(int(r['turns']) for r in results),orders=sum(int(r['orders']) for r in results),sources=dict(Counter(r['source'] for r in results)),seconds=time.perf_counter()-start,worker_npz_unchanged=True))


def configure_encoder(source,parent):
    T.table_root=lambda s:G.TABLES if s=='l1bal' else ROOT/'datasets/teacher-full-days' if s=='tfull' else OLD_TABLES(s)
    @lru_cache(maxsize=32)
    def warm(path,seat,start):return warm_history(parent,seat,start)
    T.warm=warm


def encode_segment(source,r,parent,seat=0,verify=False):
    game=safe(r['game']);day=int(r['day']);configure_encoder(source,parent)
    stem=f'{game}-seat{seat}-d{day}-h0';out=ROOT/'datasets/turns'/source/f'{stem}.npz';receipt=RUN/'encoding'/source/f'{stem}.json'
    if receipt.exists() and not verify:
        old=json.loads(receipt.read_text())
        if old['manifest']['raw_sha256']==r['sha256'] and T.sha(out)==old['manifest']['sha256'] and old['encoder_sha256']==T.sha(REPO/'src/kagml/board_features.py'):return old['manifest']
    if verify:
        with np.load(out,allow_pickle=False) as stored:arrays,audit=T.arrays_for(source,r,stored)
    else:
        arrays,audit=T.arrays_for(source,r);dump_npz(out,arrays)
    row=dict(source=source,game=game,day=day,H=0,split=r['split'],file=out.relative_to(ROOT).as_posix(),turns=len(arrays['step']),worker_decisions=int(arrays['unit_mask'].sum()),sha256=T.sha(out),episode=r['episode'],raw_file=r['file'],raw_sha256=r['sha256'],encoder_sha256=T.sha(REPO/'src/kagml/board_features.py'),seat=seat)
    if not verify:G.save(receipt,dict(manifest=row,encoder_sha256=row['encoder_sha256'],**audit))
    market_one((row,False));return row


def split_full(rep,seed,seat,day,split):
    safe(seed);start=day*24;end=min(start+24,719);episode=seed*1000+seat*100+day
    path=ROOT/'raw/teacher-full-days'/f'{seed}-seat{seat}-d{day}.json.gz';path.parent.mkdir(parents=True,exist_ok=True)
    segment={k:v for k,v in rep.items() if k!='steps'};segment['steps']=copy.deepcopy(rep['steps'][start:end+1]);segment['ownfarm']=dict(game=seed,day=day,seat=seat,start_step=start,turns=end-start,teacher='fourth',parent_full_game=True)
    if not path.exists():path.write_bytes(gzip.compress(RT.compact(segment).encode(),compresslevel=3,mtime=0))
    else:assert load_replay(path)==segment
    rows,audit=native(segment,episode);base=ROOT/'datasets/teacher-full-days'
    for table,values in rows.items():
        dest=base/table/f'{episode}.parquet';dest.parent.mkdir(parents=True,exist_ok=True)
        if not dest.exists():pq.write_table(pa.Table.from_pylist(values,schema=pa.schema(RT.SCHEMAS[table])),dest,compression='zstd')
        else:assert pq.read_table(dest).to_pylist()==values
    return dict(game=seed,day=day,seat=seat,split=split,file=path.relative_to(ROOT).as_posix(),sha256=T.sha(path),start_step=start,end_step=end,episode=episode)


def encode_seed(job):
    seed,split,smoke,verify=job;seed=safe(seed);start=time.perf_counter();days=(0,6,16,29) if smoke else range(30);rows=[]
    parent=load_replay(Path(str(G.GAMES/F_STEM('template',seed,0))+'.json.gz'))
    receipt=json.loads((RUN/'seeds'/f'{seed}.json').read_text())
    labels={int(r['day']):dict(r['manifest'],split=split) for r in receipt['days']}
    for day in days:
        r=labels[day];r['start_step']=day*24;r['end_step']=min((day+1)*24,719);r['seat']=0
        rows.append(encode_segment('l1bal',r,parent,0,verify))
    for seat in (0,1):
        parent=load_replay(Path(str(G.GAMES/F_STEM('fourth',seed,seat))+'.json.gz'))
        for day in days:
            r=split_full(parent,seed,seat,day,split);rows.append(encode_segment('tfull',r,parent,seat,verify))
    G.save(RUN/'encoded-seeds'/f"{seed}-{'verify' if verify else 'smoke' if smoke else 'full'}.json",dict(rows=rows,seconds=time.perf_counter()-start))
    print(json.dumps(dict(seed=seed,stage='encoded',segments=len(rows),seconds=round(time.perf_counter()-start,1))),flush=True)
    return rows


def F_STEM(player,seed,seat):return G.F.stem(player,seed,seat)


def encode(workers,smoke=False,verify=False):
    selected=G.seed_rows();selected=selected[:1] if smoke else selected
    results=[]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        for rows in pool.map(encode_seed,[(int(r['seed']),r['split'],smoke,verify) for r in selected]):results.extend(rows)
    if not smoke and not verify:
        old=read_csv(REPO/'manifests/turns.csv');old=[r for r in old if r['source'] not in ('l1bal','tfull')]
        fields=list(T.FIELDS);G.N.manifest(REPO/'manifests/turns.csv',fields,[{k:r[k] for k in fields} for r in old+results])
        markets(workers)
    G.save(RUN/f"encoding-{'verify' if verify else 'smoke' if smoke else 'full'}.json",dict(segments=len(results),turns=sum(int(r['turns']) for r in results),sources=dict(Counter(r['source'] for r in results))))


def main():
    a=argparse.ArgumentParser(__doc__);a.add_argument('stage',choices=('markets','encode','check'));a.add_argument('--workers',type=int,choices=range(1, 9),default=1);a.add_argument('--smoke',action='store_true');a.add_argument('--verify',action='store_true');p=a.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0'
    if p.stage=='markets':markets(p.workers,p.smoke,p.verify)
    elif p.stage=='encode':encode(p.workers,p.smoke,p.verify)
    else:raise SystemExit('Final independent audit is tools/check_plan_data.py')

if __name__=='__main__':main()

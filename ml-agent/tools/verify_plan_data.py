"""Package P native/parity/determinism checks, after both generation lanes finish."""
import argparse
import contextlib
import csv
import json
from multiprocessing import Pool
import os
import time
import plan_dataset as D
import plan_games as G
import numpy as np


def repeat(job):
    kind,seed,seat,day=job
    if kind=='full':
        original=G.F.verify(G.GAMES,'fourth',seed,seat,G.F.signature('fourth',str(G.METAV4)))
        again=G.full(seed,seat,'fourth',G.RUN/'repeats')
        assert original['gameplay_sha256']==again['gameplay_sha256']
        return dict(kind=kind,seed=seed,seat=seat,gameplay_sha256=again['gameplay_sha256'])
    if kind=='template':
        original=G.F.verify(G.GAMES,'template',seed,0,G.F.signature('template',str(G.METAV4)))
        again=G.full(seed,0,'template',G.RUN/'repeats')
        assert original['gameplay_sha256']==again['gameplay_sha256']
        return dict(kind=kind,seed=seed,seat=0,gameplay_sha256=again['gameplay_sha256'])
    G.configure();root=G.RUN/'repeat-days'/f'{seed}-d{day}'
    folders=(root/'raw',root/'tables',root/'logs')
    G.L.folders=lambda edge=False:folders
    for p in (folders[0],folders[2],*(folders[1]/t for t in (*G.RT.TABLES,'audit'))):p.mkdir(parents=True,exist_ok=True)
    result=G.L.one((G.Path(f'{seed}.json'),day,G.teacher_signature(),True));assert result['reason']=='kept',result
    original=G.load_replay(G.RAW/f'{seed}-d{day}.json.gz');again=G.load_replay(G.ROOT/result['manifest']['file'])
    assert G.F.gameplay(original)==G.F.gameplay(again)
    return dict(kind=kind,seed=seed,day=day,gameplay_sha256=G.F.gameplay(again),teacher_calls=result['teacher_calls'])


def parity(row):
    seed=int(row['seed']);rows=D.encode_seed((seed,row['split'],True,True))
    for r in rows:D.market_one((r,True))
    return dict(seed=seed,split=row['split'],B=int(row['B']),segments=len(rows),market_parity=True,worker_encoder_parity=True)


def native_full(job):
    seed,player,seat=job
    path=G.Path(str(G.GAMES/G.F.stem(player,seed,seat))+'.json.gz');rep=G.load_replay(path)
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    meta={'episode':seed,'created':'',**{f'{k}_{s}':banks[s] if k=='reward' else -1 for s in (0,1) for k in ('reward','sub','team','rating')}}
    rows,audit=G.RT.replay(rep,meta,'split-weeds');assert rows is not None,audit
    return dict(seed=seed,player=player,seat=seat,frames=720,native=True,rows={k:len(v) for k,v in rows.items()})


def old_worker_parity(source):
    r=next(r for r in D.read_csv(G.RUN/'original-turns.csv') if r['source']==source and int(r['game']) not in G.TEST)
    D.safe(r['game']);rep=G.load_replay(G.ROOT/r['raw_file']);mark=rep.get('takeover',rep.get('ownfarm'))
    raw=dict(game=r['game'],day=r['day'],H=r['H'],seat=0,episode=r['episode'],file=r['raw_file'],sha256=r['raw_sha256'],start_step=mark['start_step'],end_step=mark.get('end_step',mark['start_step']+mark.get('turns',24)),takeover_step=mark.get('takeover_step',mark['start_step']))
    with np.load(G.ROOT/r['file'],allow_pickle=False) as stored:arrays,audit=D.T.arrays_for(source,raw,stored)
    D.market_one((r,True))
    return dict(source=source,worker_encoder_parity=True,native_market_parity=True,turns=len(arrays['step']))


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--workers',type=int,choices=(1,2),default=2);a=p.parse_args();assert os.environ.get('PYTHONHASHSEED')=='0'
    rows=G.seed_rows();chosen=[next(r for r in rows if r['B']==str(b) and r['split']==split) for b in range(3) for split in ('train','analysis2')]
    started=time.perf_counter()
    with Pool(processes=a.workers,maxtasksperchild=1) as pool:parities=list(pool.imap(parity,chosen))
    first,last=int(rows[0]['seed']),int(rows[-1]['seed'])
    jobs=[('template',first,0,0),('full',first,0,0),('full',last,1,0)]+[('day',first,0,d) for d in (0,16,29)]
    with Pool(processes=a.workers,maxtasksperchild=1) as pool:repeats=list(pool.imap(repeat,jobs))
    with Pool(processes=a.workers,maxtasksperchild=1) as pool:natives=list(pool.imap(native_full,[(first,'template',0),(first,'fourth',0),(last,'fourth',1)]))
    sources=sorted({r['source'] for r in D.read_csv(G.RUN/'original-turns.csv') if int(r['game']) not in G.TEST})
    with Pool(processes=a.workers,maxtasksperchild=1) as pool:old=list(pool.imap(old_worker_parity,sources))
    G.save(G.RUN/'verification.json',dict(passed=True,new_source_parity=parities,repeats=repeats,native_full=natives,old_source_parity=old,seconds=time.perf_counter()-started))
    print(json.dumps(dict(passed=True,new_shards=sum(r['segments'] for r in parities),repeats=len(repeats),native_full=len(natives),old_sources=len(old),seconds=time.perf_counter()-started)),flush=True)

if __name__=='__main__':main()

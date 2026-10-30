"""Package P generation, resumable per seed. Two worker processes maximum.
PYTHONHASHSEED=0 KAGML_DATA=<data> python tools/plan_games.py seeds|generate|collect --lane 0 --lanes 2 --workers 1
"""
import argparse
from collections import Counter
from functools import lru_cache
import gzip
import hashlib
import json
from multiprocessing import Pool
import os
from pathlib import Path
import sys
import time

for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):os.environ[k]='1'
REPO=Path(__file__).resolve().parents[1];sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
import more_teacher_data as N
import ownfarm_labels as L
import run_full as F
from kagml import replay_tables as RT
from kagml.work_data import load_replay
import pandas as pd
ROOT=N.ROOT;RUN=ROOT/'runs/plan-data-v1';GAMES=RUN/'games';DAYS=RUN/'days'
RAW=ROOT/'raw/ownfarm-balanced/fourth';TABLES=ROOT/'datasets/ownfarm-balanced'
METAV4=N.METAV4
TEST=set(range(10320,10325))


def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def save(p,v):N.save(Path(p),v)

def seeds():
    candidates=pd.read_csv(REPO/'reports/SCENARIO_SEEDS_10501_11500.csv')
    current=pd.read_csv(REPO/'reports/SCENARIO_CENSUS.csv');prior=Counter(current[current.split=='train'].pair)
    selected=[]
    for b in range(3):
        pending=candidates[candidates.B==b].to_dict('records');used=Counter();chosen=[]
        for rank in range(20):
            r=min(pending,key=lambda r:(prior[r['pair']]>0,used[r['pair']],prior[r['pair']],r['pair'],r['game']))
            # After every missing pair has appeared, avoid repeats before filling represented pairs.
            if chosen:
                r=min(pending,key=lambda r:(used[r['pair']]>0,prior[r['pair']]>0,used[r['pair']],prior[r['pair']],r['pair'],r['game']))
            pending.remove(r);used[r['pair']]+=1;r.update(seed=r['game'],selection_rank=rank+1,prior_fit_pair_count=prior[r['pair']],split='train');chosen.append(r)
        held=[];unused=chosen[:];held_pairs=Counter()
        for rank in range(5):
            r=min(unused,key=lambda r:(held_pairs[r['pair']],prior[r['pair']]>0,prior[r['pair']],r['pair'],r['seed']))
            r['split']='analysis2';held_pairs[r['pair']]+=1;unused.remove(r);held.append(r)
        selected.extend(chosen)
    fields=['seed','B','shop1','shop2','pair','split','selection_rank','prior_fit_pair_count','full_schedule']
    rows=[{k:r[k] for k in fields} for r in sorted(selected,key=lambda r:r['seed'])]
    assert len(rows)==60 and len({r['seed'] for r in rows})==60
    assert Counter((r['B'],r['split']) for r in rows)==Counter({(b,s):n for b in range(3) for s,n in [('train',15),('analysis2',5)]})
    N.manifest(REPO/'manifests/plan-seeds.csv',fields,rows)
    save(RUN/'seed-rule.json',dict(rule='Within B, unselected ordered pairs first; then pairs missing from the 62 prior fitting games, selected pair count, prior fitting count, lexicographic ordered pair, smallest seed. Analysis2 greedily selects five different ordered pairs per B, preferring pairs absent from prior fitting games. All decisions fixed before games.',base='eb22c63',rows=rows))
    print(json.dumps(rows),flush=True)


def seed_rows():
    import csv
    with (REPO/'manifests/plan-seeds.csv').open() as f:return list(csv.DictReader(f))


def safe_seed(seed):
    seed=int(seed);assert seed not in TEST and 10501<=seed<=11500
    assert seed in {int(r['seed']) for r in seed_rows()};return seed


def full(seed,seat,player,folder=GAMES):
    seed=safe_seed(seed);folder.mkdir(parents=True,exist_ok=True);sig=F.signature(player,str(METAV4));stem=folder/F.stem(player,seed,seat)
    if Path(str(stem)+'.metrics.json').exists():return F.verify(folder,player,seed,seat,sig)
    F.one((str(folder),player,str(METAV4),seed,seat,sig))
    return F.verify(folder,player,seed,seat,sig)


@lru_cache(maxsize=1)
def parent_source(path):
    seed=safe_seed(path.stem);p=Path(str(GAMES/F.stem('template',seed,0))+'.json.gz')
    return load_replay(p),sha(p)


def configure():
    L.folders=lambda edge=False:(RAW,TABLES,DAYS)
    L.source=parent_source
    for p in (RAW,DAYS,*(TABLES/t for t in (*RT.TABLES,'audit'))):p.mkdir(parents=True,exist_ok=True)


def teacher_signature():
    upstream=ROOT/'opponents/fourth-place/fourth-place-model'
    files=[Path(__file__),Path(L.__file__),REPO/'tools/shadow_compat.py',Path(RT.K.__file__),*(REPO/'src/kagml'/f'{n}.py' for n in ('preview','opponents','replay_tables')),*(upstream.rglob('*.py')),upstream/'weights.pt']
    return hashlib.sha256(RT.compact({str(p):sha(p) for p in files}).encode()).hexdigest()


def one(row):
    seed=safe_seed(row['seed']);configure();sig=teacher_signature();receipt=RUN/'seeds'/f'{seed}.json'
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old['signature']==sig:
            for m in old['full_games']:F.verify(GAMES,m['name'],seed,m['seat'],m['signature'])
            for d in old['days']:assert sha(ROOT/d['manifest']['file'])==d['manifest']['sha256']
            return dict(seed=seed,resumed=True,seconds=old['seconds'])
    start=time.perf_counter();template=full(seed,0,'template');day_rows=[]
    print(json.dumps(dict(seed=seed,stage='template',seconds=template['seconds'])),flush=True)
    for day in range(30):
        r=L.one((Path(f'{seed}.json'),day,sig,True));assert r['reason']=='kept',r
        turns=23 if day==29 else 24
        assert r['teacher_calls']==turns and r['teacher_steps']==list(range(day*24,day*24+turns))
        assert not any(r['diagnostics'].values())
        day_rows.append(r)
        if day%10==9:print(json.dumps(dict(seed=seed,stage='days',days=day+1,seconds=round(time.perf_counter()-start,1))),flush=True)
    games=[full(seed,s,'fourth') for s in (0,1)]
    assert all(m['early_shops']==[row['shop1'],row['shop2']] and m['buyers']==int(row['B']) for m in [template,*games])
    result=dict(seed=seed,B=int(row['B']),split=row['split'],signature=sig,template=template,days=day_rows,full_games=games,seconds=time.perf_counter()-start,hashseed=0)
    save(receipt,result);print(json.dumps(dict(seed=seed,stage='complete',seconds=round(result['seconds'],1))),flush=True)
    return dict(seed=seed,seconds=result['seconds'],resumed=False)


def collect():
    rows=seed_rows();receipts=[json.loads((RUN/'seeds'/f"{r['seed']}.json").read_text()) for r in rows]
    templates=[];days=[];fulls=[]
    for r in receipts:
        seed=r['seed'];m=r['template'];p=Path(str(GAMES/F.stem('template',seed,0))+'.json.gz')
        templates.append(dict(game=seed,seed=seed,seat=0,split=r['split'],file=p.relative_to(ROOT).as_posix(),sha256=sha(p),frames=720,calls=719,B=r['B'],gameplay_sha256=m['gameplay_sha256']))
        for d in r['days']:days.append(dict(d['manifest'],split=r['split'],B=r['B']))
        for m in r['full_games']:
            p=Path(str(GAMES/F.stem('fourth',seed,m['seat']))+'.json.gz')
            fulls.append(dict(game=seed,seed=seed,seat=m['seat'],split=r['split'],file=p.relative_to(ROOT).as_posix(),sha256=sha(p),frames=720,calls=719,B=r['B'],gameplay_sha256=m['gameplay_sha256']))
    for name,rs in [('template-balanced',templates),('ownfarm-balanced',days),('teacher-full',fulls)]:N.manifest(REPO/f'manifests/{name}.csv',list(rs[0]),rs)
    assert len(templates)==60 and len(days)==1800 and len(fulls)==120
    save(RUN/'generation.json',dict(templates=60,days=1800,teacher_full=120,seconds=sum(r['seconds'] for r in receipts),seed_split_counts=dict(Counter(r['split'] for r in receipts))))
    print((RUN/'generation.json').read_text())


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('stage',choices=('seeds','generate','collect'));p.add_argument('--workers',type=int,choices=(1,2),default=1);p.add_argument('--lane',type=int,default=0);p.add_argument('--lanes',type=int,default=1);p.add_argument('--smoke',action='store_true');a=p.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0';assert 0<=a.lane<a.lanes
    RUN.mkdir(parents=True,exist_ok=True)
    if a.stage=='seeds':seeds()
    elif a.stage=='collect':collect()
    else:
        rows=seed_rows();rows=rows[:1] if a.smoke else rows;rows=rows[a.lane::a.lanes]
        with Pool(processes=a.workers,maxtasksperchild=1) as pool:
            for r in pool.imap_unordered(one,rows):print(json.dumps(dict(lane=a.lane,**r)),flush=True)

if __name__=='__main__':main()

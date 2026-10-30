"""N2: 48 fresh template games, L1 days 6-28, unchanged N encoding.
PYTHONHASHSEED=0 python tools/more_teacher_data.py games|labels|encode|check [--smoke] [--workers 2]
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import csv
from functools import lru_cache
import hashlib
import json
from multiprocessing import Pool
import os
from pathlib import Path
import sys
import time

REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
for key in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[key]='1'
import build_turn_dataset as T
import ownfarm_labels as L
import run_full as F
from kagml import replay_tables as RT
ROOT=T.ROOT;RAW=ROOT/'raw/template-games';OUT=ROOT/'datasets/ownfarm-more';LOG=ROOT/'runs/more-teacher-data'
METAV4=REPO.parent/'Kaggle-Kaggriculture/agents/public/2026-09-20/the-metav4-farm-submission-v13/main.py'
METAV4_SHA='9d63494603f88219857a3101d7dc19cc750ded04e5886732ee428580326967d9'
GAME_FIELDS=('game','seed','seat','split','file','sha256','frames','calls','end_cash_0','end_cash_1','gameplay_sha256','template_sha256','opponent_sha256')


def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True);tmp=path.with_suffix('.tmp');tmp.write_text(json.dumps(value,separators=(',',':')),encoding='utf-8');tmp.replace(path)


def manifest(path,fields,rows):
    tmp=path.with_suffix('.tmp')
    with tmp.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    tmp.replace(path)


def game_one(job):
    game,signature=job;receipt=LOG/'games'/f'{game}.json';target=RAW/f'{game}.json.gz';begun=time.perf_counter()
    if receipt.exists() and target.exists():
        old=json.loads(receipt.read_text())
        if old['signature']==signature and old['pipeline_sha256']==T.sha(__file__) and old['manifest']['sha256']==T.sha(target):return {**old,'resumed':True}
    stem=RAW/F.stem('template',game,0)
    if not Path(str(stem)+'.json.gz').exists():F.one((str(RAW),'template',str(METAV4),game,0,signature))
    metrics=F.verify(RAW,'template',game,0,signature);rep=T.load_replay(Path(str(stem)+'.json.gz'))
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    meta={'episode':game,'created':'',**{f'{k}_{p}':banks[p] if k=='reward' else -1 for p in (0,1) for k in ('reward','sub','team','rating')}}
    rows,audit=RT.replay(rep,meta,'split-weeds');assert rows is not None,audit
    assert rep['info']['seed']==game and len(rep['steps'])==720 and metrics['timing']['turns']==719
    raw=Path(str(stem)+'.json.gz');assert raw.resolve().parent==target.resolve().parent==RAW.resolve();raw.replace(target)
    row=dict(game=game,seed=game,seat=0,split='train',file=target.relative_to(ROOT).as_posix(),sha256=T.sha(target),frames=720,calls=719,end_cash_0=banks[0],end_cash_1=banks[1],gameplay_sha256=F.gameplay(rep),template_sha256=T.sha(REPO/'vendor/template_agent/main.py'),opponent_sha256=T.sha(METAV4))
    result=dict(manifest=row,signature=signature,pipeline_sha256=T.sha(__file__),seconds=time.perf_counter()-begun,generation_seconds=metrics['seconds'],native=audit,native_rows={k:len(v) for k,v in rows.items()},policy_errors=metrics['policy_errors'],opponent_errors=metrics['opponent_errors'])
    save(receipt,result);return result


@lru_cache(maxsize=1)
def more_source(path):
    actual=RAW/f'{path.stem}.json.gz';return T.load_replay(actual),T.sha(actual)


def configure_labels(repeat=False):
    base=LOG/'repeat-labels' if repeat else ROOT
    L.RAW=base/'raw/ownfarm-more';L.OUT=base/'datasets/ownfarm-more';L.LOG=LOG/'labels';L.source=more_source
    for folder in (L.RAW,*(L.OUT/t for t in (*RT.TABLES,'audit'))):folder.mkdir(parents=True,exist_ok=True)


def teacher_one(job):
    game,day,signature,*repeat=job;configure_labels(bool(repeat and repeat[0]));result=L.one((RAW/f'{game}.json',day,signature))
    if result['reason']!='kept':raise RuntimeError(result)
    assert result['teacher_calls']==24 and result['teacher_steps']==list(range(day*24,(day+1)*24))
    assert not any(result['diagnostics'].values()),result['diagnostics']
    return result


def teacher_signature():
    upstream=ROOT/'opponents/fourth-place/fourth-place-model'
    paths=[Path(__file__),Path(L.__file__),REPO/'tools/shadow_compat.py',*(REPO/'src/kagml'/f'{n}.py' for n in ('preview','opponents','replay_tables')),Path(RT.K.__file__),*sorted(upstream.rglob('*.py')),upstream/'weights.pt']
    return hashlib.sha256(RT.compact({str(p):T.sha(p) for p in paths}).encode()).hexdigest()


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('stage',choices=('games','labels','encode','check','verify','repeat'));ap.add_argument('--workers',type=int,choices=(1,2),default=2);ap.add_argument('--smoke',action='store_true');a=ap.parse_args()
    if a.stage not in ('verify','repeat') and os.environ.get('PYTHONHASHSEED')!='0':raise ValueError('set PYTHONHASHSEED=0')
    assert T.sha(METAV4)==METAV4_SHA
    RAW.mkdir(parents=True,exist_ok=True);LOG.mkdir(parents=True,exist_ok=True);start=time.perf_counter();results=[]
    if a.stage=='games':
        seeds=[10401,10448] if a.smoke else list(range(10401,10449));sig=F.signature('template',str(METAV4))
        with Pool(processes=a.workers,maxtasksperchild=1) as pool:
            for r in pool.imap(game_one,[(s,sig) for s in seeds]):
                results.append(r);print(json.dumps({'games':len(results),'total':len(seeds),'seed':r['manifest']['game'],'seconds':round(time.perf_counter()-start,1),'resumed':r.get('resumed',False)}),flush=True)
        if not a.smoke:manifest(REPO/'manifests/template-games.csv',GAME_FIELDS,[r['manifest'] for r in results])
    elif a.stage in ('labels','repeat'):
        seeds=list(range(10401,10449));sig=teacher_signature();jobs=[(s,d,sig) for s in seeds for d in range(6,29)]
        if a.smoke or a.stage=='repeat':jobs=[(10401,d,sig,a.stage=='repeat') for d in (6,16,28)]
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            for r in pool.map(teacher_one,jobs):
                results.append(r)
                if len(results)%12==0 or len(results)==len(jobs):print(json.dumps({'segments':len(results),'total':len(jobs),'seconds':round(time.perf_counter()-start,1),'resumed':sum(x.get('resumed',False) for x in results)}),flush=True)
        if a.stage=='labels' and not a.smoke:manifest(REPO/'manifests/ownfarm-more.csv',L.FIELDS,[r['manifest'] for r in results])
        if a.stage=='repeat':
            for r in results:
                original=T.load_replay(ROOT/'raw/ownfarm-more'/f"{r['game']}-d{r['day']}.json.gz");again=T.load_replay(LOG/'repeat-labels/raw/ownfarm-more'/f"{r['game']}-d{r['day']}.json.gz");assert F.gameplay(original)==F.gameplay(again)
    elif a.stage in ('encode','verify'):
        T.SOURCES['l1more']='ownfarm-more';jobs=[(s,r) for s,r in T.tasks(['l1more'])]
        if a.smoke or a.stage=='verify':jobs=[(s,r) for s,r in jobs if int(r['game']) in (10401,10424,10448) and int(r['day']) in (6,16,28)]
        original=list(csv.DictReader((REPO/'manifests/turns.csv').open()))
        with ProcessPoolExecutor(max_workers=a.workers) as pool:
            for r in pool.map(T.one,[(s,r,a.stage=='verify',False) for s,r in jobs]):
                results.append(r)
                if len(results)%100==0:print(json.dumps({'encoded':len(results),'seconds':round(time.perf_counter()-start,1)}),flush=True)
        if a.stage=='encode' and not a.smoke:
            retained=[r for r in original if r['source']!='l1more'];new=retained+[r['manifest'] for r in results]
            manifest(REPO/'manifests/turns.csv',T.FIELDS,sorted(new,key=lambda r:(r['source'],int(r['game']),int(r['day']),int(r['H']))))
            published=list(csv.DictReader((REPO/'manifests/turns.csv').open()));assert [r for r in published if r['source']!='l1more']==retained
            assert all(r['manifest']['split']=='train' for r in results)
    else:
        import check_turn_dataset as C
        T.SOURCES['l1more']='ownfarm-more';C.main()
        games=list(csv.DictReader((REPO/'manifests/template-games.csv').open()));labels=list(csv.DictReader((REPO/'manifests/ownfarm-more.csv').open()))
        assert {int(r['game']) for r in games}==set(range(10401,10449)) and len(games)==48
        assert {(int(r['game']),int(r['day'])) for r in labels}=={(s,d) for s in range(10401,10449) for d in range(6,29)} and len(labels)==1104
        for r in games:assert r['split']=='train' and T.sha(ROOT/r['file'])==r['sha256']
        for r in labels:
            audit=json.loads((OUT/'audit'/f"{r['episode']}.json").read_text());assert audit['reason']=='kept' and audit['teacher_calls']==24 and not any(audit['diagnostics'].values());assert audit['source_sha256']==T.sha(RAW/f"{r['game']}.json.gz")
        original=list(csv.DictReader((REPO.parent/'kaggriculture-ml-turns/manifests/turns.csv').open()));published=list(csv.DictReader((REPO/'manifests/turns.csv').open()));assert [r for r in published if r['source']!='l1more']==original
    summary=dict(stage=a.stage,smoke=a.smoke,hashseed=os.environ.get('PYTHONHASHSEED'),workers=a.workers,items=len(results),seconds=time.perf_counter()-start,resumed=sum(r.get('resumed',False) for r in results))
    if a.stage in ('encode','verify'):summary.update(turns=sum(int(r['manifest']['turns']) for r in results),decisions=sum(int(r['manifest']['worker_decisions']) for r in results))
    if a.stage=='labels':summary.update(teacher_calls=sum(r['teacher_calls'] for r in results),compatibility_events=sum(len(r.get('compatibility_events',[])) for r in results))
    save(LOG/f"{a.stage}-{'smoke' if a.smoke else 'full'}-{os.environ.get('PYTHONHASHSEED')}.json",summary);print(json.dumps(summary),flush=True)

if __name__=='__main__':main()

"""Causal market-history sidecars. Default is <=5 analysis segments; --full is explicit."""
import argparse,csv,gzip,hashlib,json,os,sys
from pathlib import Path
from functools import lru_cache
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml.market_net import MarketHistory,VERSION,PRODUCTS
from kagml.paths import data_root

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
@lru_cache(maxsize=4)
def replay(path):
    p=Path(path)
    if p.suffix=='.gz':
        with gzip.open(p,'rt',encoding='utf8') as f:return json.load(f)
    return json.loads(p.read_text(encoding='utf8'))
def physical(frame,seat):
    obs=frame[seat]['observation'];return int(obs['day'])*24+int(obs['hour'])
def parent_path(row,seat,data):
    source=row['source'];game=int(row['game'])
    if source in ('l3-n1','l3-n2','l3-n3'):
        return data/'raw'/('src-'+source.removeprefix('l3-'))/f'{game}.json'
    if source=='l1more':return data/'raw/template-games'/f'{game}.json.gz'
    if source in ('l1bal','tfull'):
        actor='template' if source=='l1bal' else 'fourth';return data/'runs/plan-data-v1/games'/f'{actor}-{game}-seat{0 if source=="l1bal" else seat}.json.gz'
    if source=='l1end':
        matches=list((data/'runs/overnight-20261027/endgame-e-p2-nflow/games').glob(f'*-{game}-seat{seat}.json.gz'))
        if len(matches)!=1:raise ValueError(f'unambiguous original P2 parent missing: {game} seat{seat}')
        return matches[0]
    if source in ('l1','l1-edge','l3-r1','l3-r2','l3-edge','l3-net1','l3-net2','l3-p1'):
        return ROOT.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3'/f'{game}.json'
    raise ValueError(f'no parent mapping for {source}; do not substitute a different farm')

def history_arrays(rep,parent,seat,steps):
    wanted=set(map(int,steps));first=physical(rep['steps'][0],seat);last=max(wanted);h=MarketHistory();hs=[];extra=[];where={}
    prefix={physical(f,seat):f for f in parent['steps']}
    if first not in prefix:raise ValueError('parent missing fork observation')
    for field in ('farms','private','market','town','day','hour'):
        if prefix[first][seat]['observation'][field]!=rep['steps'][0][seat]['observation'][field]:raise ValueError('parent/fork state mismatch: '+field)
    for t in range(max(0,first-24),first):
        if t not in prefix:raise ValueError('parent does not contain the required causal prefix')
        frame=prefix[t];h.observe(frame[seat]['observation'],seat,frame[seat].get('action') if t else None)
    for index,frame in enumerate(rep['steps']):
        step=physical(frame,seat)
        if step>last:break
        previous=(prefix[first][seat].get('action') if first and first in prefix else None) if index==0 else frame[seat].get('action')
        h.observe(frame[seat]['observation'],seat,previous)
        if step in wanted:
            where[step]=len(hs);hs.append(h.sequence());extra.append(h.extra.copy())
    if set(where)!=wanted:raise ValueError('raw segment does not cover every labeled step')
    order=[where[int(t)] for t in steps];return np.stack(hs)[order],np.stack(extra)[order]

def build_one(row,market,data,out):
    game=int(row['game'])
    if game in set(range(10320,10325))|set(range(20001,20049)):raise ValueError('forbidden test/evaluation game for sidecar construction')
    if row['split'] not in ('train','analysis','analysis2'):raise ValueError('unsupported sidecar split')
    seat=int(market['seat']);raw=data/row['raw_file'];worker=data/row['file'];labels=data/market['file'];assert sha(raw)==row['raw_sha256'] and sha(worker)==row['sha256'] and sha(labels)==market['sha256']
    with np.load(worker,allow_pickle=False) as z:steps=z['step'].copy();glob=z['glob'].copy()
    parent=parent_path(row,seat,data);rep=replay(str(raw));hist,extras=history_arrays(rep,replay(str(parent)),seat,steps)
    frames={physical(f,seat):f[seat]['observation'] for f in rep['steps']}
    for t,g in zip(steps,glob):
        for k,p in enumerate(PRODUCTS):assert g[33+k*8]==frames[int(t)]['market']['prices'][p] and g[34+k*8]==frames[int(t)]['market']['inventory'][p]
    dest=out/row['source']/(worker.stem+'.npz');dest.parent.mkdir(parents=True,exist_ok=True)
    if dest.exists():
        with np.load(dest,allow_pickle=False) as old:np.testing.assert_array_equal(old['step'],steps);np.testing.assert_array_equal(old['history'],hist);np.testing.assert_array_equal(old['extra'],extras)
    else:
        temporary=dest.with_suffix('.tmp')
        with temporary.open('wb') as f:np.savez_compressed(f,step=steps,history=hist,extra=extras)
        temporary.replace(dest)
    assert sha(worker)==row['sha256'] and sha(labels)==market['sha256']
    return dict(family=int(replay(str(parent))['info']['seed']),source=row['source'],game=game,seat=seat,day=row['day'],H=row['H'],split=row['split'],file=dest.relative_to(data).as_posix(),sha256=sha(dest),worker_file=row['file'],worker_sha256=row['sha256'],market_file=market['file'],market_sha256=market['sha256'],raw_file=row['raw_file'],raw_sha256=row['raw_sha256'],parent_file=str(parent),parent_sha256=sha(parent),turns=len(steps),version=VERSION)

def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--splits',default='analysis');p.add_argument('--limit',type=int,default=5);p.add_argument('--full',action='store_true');p.add_argument('--diverse',action='store_true');p.add_argument('--tag',default='prep-smoke');p.add_argument('--manifest',default='.cache/prep/market-history-smoke.csv');a=p.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0'
    if not a.full and not 1<=a.limit<=5:p.error('smoke is limited to 1..5 segments; full builds require --full')
    if a.tag in ('.','..') or Path(a.tag).name!=a.tag or ':' in a.tag:p.error('tag must be a directory name')
    splits=set(a.splits.split(','))
    if not splits<=set(('train','analysis','analysis2')):p.error('test/evaluation splits are forbidden')
    rows=[r for r in csv.DictReader((ROOT/'manifests/turns.csv').open()) if r['split'] in splits]
    if a.diverse and not a.full:
        chosen=[]
        for source in dict.fromkeys(r['source'] for r in rows):
            group=[r for r in rows if r['source']==source];chosen.append(next((r for r in group if int(r['H'])>=12),group[0]))
        rows=chosen[:a.limit]
    elif not a.full:rows=rows[:a.limit]
    if a.full:rows=sorted(rows,key=lambda r:(int(r['game']),int(r.get('seat',0)),int(r['day']),int(r['H']),r['source']))
    sides={r['worker_file']:r for r in csv.DictReader((ROOT/'manifests/turn-markets.csv').open()) if r['split'] in splits};data=data_root();out=data/'datasets/market-history'/a.tag
    target=(ROOT/a.manifest).resolve()
    if not target.is_relative_to(ROOT):raise ValueError('manifest must stay in this worktree')
    results=[]
    for i,r in enumerate(rows):
        results.append(build_one(r,sides[r['file']],data,out))
        if (i+1)%100==0:print(json.dumps(dict(segments=i+1,total=len(rows),source=r['source']),separators=(',',':')),flush=True)
    target.parent.mkdir(parents=True,exist_ok=True)
    if not results:raise ValueError('empty selection')
    with target.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(results[0]));w.writeheader();w.writerows(results)
    print(json.dumps(dict(segments=len(results),turns=sum(r['turns'] for r in results),manifest=str(target),full=a.full),separators=(',',':')))
if __name__=='__main__':main()

"""Family-level l1end fine-tuning hold-out; metadata only, no arrays rewritten."""
from pathlib import Path
from collections import Counter
import csv,hashlib,json
ROOT=Path(__file__).resolve().parents[1]
def read(p):
 with p.open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def write(p,rows):
 q=p.with_suffix('.tmp')
 with q.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 q.replace(p)
def main():
 base=read(ROOT/'manifests/turns.csv');l1=[r for r in base if r['source']=='l1end'];seeds=sorted({int(r['game']) for r in l1});assert len(seeds)==107 and len(l1)==2987
 held=set(sorted(seeds,key=lambda s:hashlib.sha256(f'endval-v1:{s}'.encode()).hexdigest())[:11]);assert not held & (set(range(10320,10325))|set(range(20001,20025)))
 files=['turns.csv','turn-markets.csv','endgame-turns.csv','endgame-markets.csv','ownfarm-endgame.csv','endgame-seeds.csv'];counts={}
 for name in files:
  p=ROOT/'manifests'/name;rows=read(p);changes=0
  for r in rows:
   seed=int(r.get('game',r.get('seed')))
   if seed in held and (name in ('ownfarm-endgame.csv','endgame-seeds.csv') or r.get('source')=='l1end'):
    assert r['split'] in ('train','endval');changes+=r['split']=='train';r['split']='endval'
    if name=='endgame-seeds.csv':r['purpose']='validation'
  write(p,rows);counts[name]=changes
 l1=read(ROOT/'manifests/turns.csv');selected=[r for r in l1 if r['source']=='l1end'];train={int(r['game']) for r in selected if r['split']=='train'};valid={int(r['game']) for r in selected if r['split']=='endval'};assert not train&valid and valid==held and len(train)==96
 for name in ('turns.csv','turn-markets.csv'):
  now=read(ROOT/'manifests'/name);old=base if name=='turns.csv' else None
  if old is not None:assert all(a==b for a,b in zip(old,now) if a['source']!='l1end')
 proof=dict(passed=True,selection='11 smallest SHA256(endval-v1:seed), all seats/days reserved together',held_seeds=sorted(held),train_seeds=96,validation_seeds=11,split_counts=dict(Counter(r['split'] for r in selected)),changed_rows=counts,worker_arrays_written=0,test_contents_read=0,evaluation_training=0,limitation='Fine-tune holdout only: board-p4 pretraining may include these parent seeds via other sources; not a pristine generalization test.')
 (ROOT/'reports/ENDGAME_VALIDATION_SPLIT.json').write_text(json.dumps(proof,separators=(',',':')),encoding='utf8');write(ROOT/'manifests/endgame-validation.csv',[dict(seed=s,split='endval',selection='sha256-endval-v1') for s in sorted(held)])
 print(json.dumps(proof,separators=(',',':')))
if __name__=='__main__':main()
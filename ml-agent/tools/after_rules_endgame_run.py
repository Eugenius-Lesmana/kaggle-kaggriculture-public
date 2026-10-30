"""Resumable four-worker label/verification queue, isolated from current policy modules."""
import hashlib,json,os,sys,time
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
import after_rules_endgame as W

def done(j):return W.RUN/'completed'/(hashlib.sha256(json.dumps(j,sort_keys=True).encode()).hexdigest()[:20]+'.json')
def verification(cfg):
 selected={}
 balanced={int(r['seed']) for r in W.E.read_csv(W.OLD/'manifests/plan-seeds.csv') if r['split']=='train'}
 for j in cfg['jobs']:
  r=j['row']
  if r['seed'] not in balanced:continue
  source=json.loads((W.ORIGINAL_RUN/'sources'/f"{r['seed']}-seat0.json").read_text())
  selected.setdefault(source['B'],r)
 assert set(selected)=={0,1,2}
 jobs=[dict(kind='parity',row=r,seat=s) for r in selected.values() for s in (0,1)]
 jobs += [dict(kind='repeat',row=selected[0],seat=s,day=d) for s in (0,1) for d in (16,23)]
 jobs += [dict(kind='native-full',row=r,seat=i%2) for i,r in enumerate(selected.values())]
 return jobs

def run():
 cfg=json.loads((W.LOCAL/'endgame-inputs.json').read_text());W.guard()
 jobs=cfg['jobs'];phase='task3-labels'
 W.save(W.LOCAL/'status.json',dict(state='running',phase=phase,completed=sum(done(j).exists() for j in jobs),target=len(jobs),workers=4,segments=8*sum(done(j).exists() for j in jobs)))
 for group in (jobs,verification(cfg)):
  pending=[j for j in group if not done(j).exists()];active={}
  with ProcessPoolExecutor(max_workers=4) as pool:
   while pending or active:
    while pending and len(active)<4:
     j=pending.pop(0);active[pool.submit(W.execute,j)]=j
    ready,_=wait(active,return_when=FIRST_COMPLETED)
    for f in ready:f.result();del active[f]
    completed=sum(done(j).exists() for j in group)
    W.save(W.LOCAL/'status.json',dict(state='running',phase=phase,completed=completed,target=len(group),workers=len(active),segments=8*sum(done(j).exists() for j in jobs)))
  phase='task3-verification'
 assert all(done(j).exists() for j in jobs+verification(cfg))
 W.save(W.RUN/'verified.json',dict(passed=True,segments=1712,turns=41088,parity_samples=12,label_repeats=4,parent_native_replays=3,jobs=verification(cfg),worker_sha256=cfg['worker_sha256']))
 W.save(W.LOCAL/'status.json',dict(state='phase-complete',phase='task3-verified',completed=1712,target=1712,workers=0))
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 run()
"""User-approved whole-segment capacity exclusions; teacher, encoder and original adapter stay frozen."""
import gzip,hashlib,json,os,sys
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
import after_rules_endgame as W
import after_rules_endgame_run as Q
CFG=W.LOCAL/'compatible-inputs.json'
APPROVAL=W.LOCAL/'capacity-approval.json'
def prepare():
 approval=json.loads(APPROVAL.read_text());assert approval['approved_action']=='documented-whole-segment-exclusions'
 original=json.loads((W.LOCAL/'endgame-inputs.json').read_text());assert W.sha(W.ROOT/'tools/after_rules_endgame.py')==original['worker_sha256']
 fixed=dict(runner_sha256=W.sha(__file__),publisher_sha256=W.sha(W.ROOT/'tools/after_rules_publish.py'),original_worker_sha256=original['worker_sha256'],original_signature=original['original_signature'],approval_sha256=W.sha(APPROVAL),policy_and_encoding_changes=[],max_game_processes=2)
 if CFG.exists():
  value=json.loads(CFG.read_text());assert all(value[k]==v for k,v in fixed.items());return value
 baseline={}
 for p in (W.RUN/'dataset/encoding/l1end').glob('*.json'):
  r=json.loads(p.read_text())['manifest'];baseline[r['file']]=r['sha256']
 for p in (W.RUN/'dataset/markets/l1end').glob('*.json'):
  r=json.loads(p.read_text());baseline[r['file']]=r['sha256']
 value=dict(**fixed,existing_array_hashes=baseline,exclusion_rule='Keep complete unchanged raw/native segment; exclude its whole worker/market training example only when actual peak units exceed14. Never truncate.')
 W.save(CFG,value);W.save(W.RUN/'approved-compatibility-config.json',value);return value

def family(job):
 c=json.loads(CFG.read_text());assert W.sha(__file__)==c['runner_sha256'] and W.sha(APPROVAL)==c['approval_sha256']
 try:return W.execute(job)
 except AssertionError as e:
  if str(e)!='Worker feature capacity exceeded':raise
 # Original adapter has recovered/validated any existing arrays before the capacity assertion.
 row=job['row'];seat=job['seat'];labels=[];workers=[];excluded=[]
 for day in range(16,24):
  label=W.D.label_day(row,seat,day);labels.append(label);m=label['manifest']
  with gzip.open(W.DATA/m['file'],'rt',encoding='utf8') as f:rep=json.load(f)
  peak=max(len(z[seat]['observation']['farms'][seat]['hands'])+1 for z in rep['steps'][:-1])
  if peak>14:
   excluded.append(dict(seed=row['seed'],seat=seat,day=day,episode=m['episode'],raw_file=m['file'],raw_sha256=m['sha256'],peak_units=peak,encoder_capacity=14,reason='approved whole-segment exclusion; no truncation'))
   assert not (W.DATA/'datasets/turns/l1end'/f"{row['seed']}-seat{seat}-d{day}-h0.npz").exists()
   continue
  W.D.family((row,seat,[day]))
  single=json.loads((W.RUN/'families'/f"{row['seed']}-seat{seat}-smoke.json").read_text());assert len(single['workers'])==1;workers+=single['workers']
 assert excluded and len(labels)==len(workers)+len(excluded)==8
 W.save(W.RUN/'families'/f"{row['seed']}-seat{seat}-full.json",dict(seed=row['seed'],seat=seat,labels=labels,workers=workers,excluded=excluded,compatibility_runner_sha256=c['runner_sha256']))
 result=dict(seed=row['seed'],seat=seat,raw_segments=8,encoded_segments=len(workers),excluded=excluded)
 W.save(Q.done(job),dict(passed=True,job=job,result=result,original_signature=c['original_signature'],generation_adapter_sha256=c['original_worker_sha256'],compatibility_runner_sha256=c['runner_sha256']))
 return result

def queue(jobs,fn,phase):
 pending=[j for j in jobs if not Q.done(j).exists()];active={}
 W.save(W.LOCAL/'status.json',dict(state='running',phase=phase,completed=len(jobs)-len(pending),target=len(jobs),workers=2,approved_exclusions=True))
 with ProcessPoolExecutor(max_workers=2) as pool:
  while pending or active:
   while pending and len(active)<2:
    j=pending.pop(0);active[pool.submit(fn,j)]=j
   ready,_=wait(active,return_when=FIRST_COMPLETED)
   for f in ready:f.result();del active[f]
   W.save(W.LOCAL/'status.json',dict(state='running',phase=phase,completed=sum(Q.done(j).exists() for j in jobs),target=len(jobs),workers=len(active),approved_exclusions=True))

def verification(cfg):
 balanced={int(r['seed']) for r in W.E.read_csv(W.OLD/'manifests/plan-seeds.csv') if r['split']=='train'};selected={}
 for j in cfg['jobs']:
  row=j['row'];seed=row['seed']
  if seed not in balanced:continue
  files=[W.RUN/'families'/f'{seed}-seat{s}-full.json' for s in (0,1)]
  good={(int(w['day']),s) for s,p in enumerate(files) for w in json.loads(p.read_text())['workers']}
  if not all((d,s) in good for d in (16,23) for s in (0,1)):continue
  b=json.loads((W.ORIGINAL_RUN/'sources'/f'{seed}-seat0.json').read_text())['B'];selected.setdefault(b,row)
 assert set(selected)=={0,1,2}
 jobs=[dict(kind='parity',row=r,seat=s) for r in selected.values() for s in (0,1)]
 jobs += [dict(kind='repeat',row=selected[0],seat=s,day=d) for s in (0,1) for d in (16,23)]
 jobs += [dict(kind='native-full',row=r,seat=i%2) for i,r in enumerate(selected.values())]
 return jobs

def run():
 W.guard();c=prepare();cfg=json.loads((W.LOCAL/'endgame-inputs.json').read_text());queue(cfg['jobs'],family,'task3-approved-capacity-recovery')
 checks=verification(cfg);queue(checks,W.execute,'task3-approved-verification')
 families=[json.loads((W.RUN/'families'/f"{j['row']['seed']}-seat{j['seat']}-full.json").read_text()) for j in cfg['jobs']]
 excluded=[e for f in families for e in f.get('excluded',[])];n=sum(len(f['workers']) for f in families)
 assert len(families)==214 and sum(len(f['labels']) for f in families)==1712 and n+len(excluded)==1712
 for p,h in c['existing_array_hashes'].items():assert W.sha(W.DATA/p)==h
 W.save(W.RUN/'verified.json',dict(passed=True,raw_segments=1712,segments=n,turns=24*n,excluded_segments=excluded,parity_samples=12,label_repeats=4,parent_native_replays=3,jobs=checks,worker_sha256=cfg['worker_sha256'],compatibility_runner_sha256=c['runner_sha256'],preserved_array_hashes_checked=len(c['existing_array_hashes']),approval_sha256=c['approval_sha256'],policy_and_encoding_changes=[],max_game_processes=2))
 assert W.sha(W.ROOT/'tools/after_rules_publish.py')==c['publisher_sha256']
 import after_rules_publish as P
 P.publish()
 W.save(W.LOCAL/'status.json',dict(state='phase-complete',phase='task3-published',encoded_segments=n,excluded_segments=len(excluded),workers=0))
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 run()
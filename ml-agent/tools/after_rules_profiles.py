"""Gated native profile census/queue; no policy games are launched here."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import json,sys
from pathlib import Path
from after_rules_extract import ROOT,DATA,RUN,LOCAL,PROFILES,sha,save,key,extract

def prepare():
 assert json.loads((RUN/'games-complete.json').read_text())['passed']
 from after_rules_games import library,BEST
 F=library();jobs=[];teacher=[];frozen=json.loads((LOCAL/'config.json').read_text());baseline={(r['seed'],r['seat']):r for r in frozen['baseline']}
 for h in (12,22,28,0,100):
  for seed in range(20001,20009):
   for seat in (0,1):
    name='fourth' if h==100 else (f'handover:{h}:' if h else '')+BEST
    folder=DATA/'runs/nflow-teacher' if h==100 else DATA/'runs/nflow-p4-ovf-end-ew' if h==0 else RUN/'games'
    p=folder/F.stem(name,seed,seat);m=json.loads(p.with_suffix('.metrics.json').read_text());raw=p.with_suffix('.json.gz')
    assert m['name']==name and m['seed']==seed and m['seat']==seat and m['statuses']==['DONE','DONE'] and m['steps']==720
    assert not m.get('policy_errors') and not m.get('opponent_errors')
    j=dict(handover=h,seed=seed,seat=seat,file=raw.relative_to(DATA).as_posix(),sha256=sha(raw),margin=m['margin'],original_seconds=m['seconds'])
    if h==0:
     old=baseline[seed,seat];assert j['file']==old['file'] and j['sha256']==old['sha256'] and j['margin']==old['margin']
    (teacher if h==100 else jobs).append(j)
 protected=['tools/run_full.py','tools/build_turn_dataset.py','src/kagml/net_player.py','src/kagml/replay_tables.py','src/kagml/board_features.py']
 cfg=dict(analysis_version=2,jobs=jobs,teacher_jobs=teacher,worker_sha256=sha(ROOT/'tools/after_rules_extract.py'),protected_hashes={p:sha(ROOT/p) for p in protected},workers=4,base_commit='b991ec8')
 path=LOCAL/'profiles-inputs.json'
 if path.exists():assert json.loads(path.read_text())==cfg,'Frozen profile inputs changed'
 else:save(path,cfg)
 save(RUN/'profiles-inputs.json',cfg);return cfg

def run(phase):
 cfg=json.loads((LOCAL/'profiles-inputs.json').read_text());jobs=cfg['jobs'] if phase=='task1-profiles' else cfg['teacher_jobs']
 assert phase in ('task1-profiles','task2-profiles')
 if phase=='task2-profiles':assert json.loads((RUN/'task1-reported.json').read_text())['passed']
 todo=[j for j in jobs if not (PROFILES/(key(j)+'.json')).exists()]
 save(LOCAL/'status.json',dict(state='running',phase=phase,completed=len(jobs)-len(todo),target=len(jobs),workers=4))
 with ProcessPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(extract,j) for j in todo]):
   f.result();n=sum((PROFILES/(key(j)+'.json')).exists() for j in jobs)
   save(LOCAL/'status.json',dict(state='running',phase=phase,completed=n,target=len(jobs),workers=4))
 save(RUN/(phase+'-complete.json'),dict(passed=True,cases=len(jobs),worker_sha256=cfg['worker_sha256']))
 save(LOCAL/'status.json',dict(state='phase-complete',phase=phase,completed=len(jobs),target=len(jobs),workers=0))
if __name__=='__main__':
 if sys.argv[1]=='prepare':print(json.dumps({k:len(v) for k,v in prepare().items() if k in ('jobs','teacher_jobs')}))
 else:run(sys.argv[1])
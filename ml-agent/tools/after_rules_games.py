"""Four-worker fresh-process handover runs using unchanged run_full, under explicit user authorization."""
import contextlib,hashlib,io,json,os,sys,time
from pathlib import Path
from multiprocessing import Pool
ROOT=Path(__file__).resolve().parents[1];DATA=Path('kaggriculture-ml-data');RUN=DATA/'runs/after-rules-20261028';LOCAL=ROOT/'.cache/after-rules'
BEST='net:board-p4:market:overflow:endmask:endwork';WORKERS=4
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp')
 for n in range(10):
  try:tmp.write_text(json.dumps(v,separators=(',',':')),encoding='utf8');tmp.replace(p);return
  except PermissionError:
   if n==9:raise
   time.sleep(.1)
def library():
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):import run_full as F
 return F

def prepare():
 F=library();opponent=str(DATA/'opponents/fifth-place/nflow-main-wash8014/main.py');players=[f'handover:{d}:'+BEST for d in (12,22,28)]
 pins=[DATA/'models/board-p4/model.pt',DATA/'opponents/fourth-place/fourth-place-model/weights.pt',DATA/'opponents/fifth-place/nflow-main-wash8014/policy.pt']
 for folder in ('fourth-place/fourth-place-model','fifth-place/nflow-main-wash8014'):pins.extend((DATA/'opponents'/folder).rglob('*.py'))
 baseline=[]
 for seed in range(20001,20009):
  for seat in (0,1):
   p=DATA/'runs/nflow-p4-ovf-end-ew'/F.stem(BEST,seed,seat);m=json.loads(p.with_suffix('.metrics.json').read_text())
   assert m['name']==BEST and m['seed']==seed and m['seat']==seat and m['statuses']==['DONE','DONE']
   assert not m.get('policy_errors') and not m.get('opponent_errors')
   raw=p.with_suffix('.json.gz');baseline.append(dict(seed=seed,seat=seat,file=raw.relative_to(DATA).as_posix(),sha256=sha(raw),margin=m['margin']))
 cfg=dict(base_commit='b991ec8',best=BEST,workers=WORKERS,worker_authorization='Eugene explicitly authorized4-5; use4 maximum',opponent=opponent,
  players=players,signatures={n:F.signature(n,opponent) for n in players},pins={str(p):sha(p) for p in pins},runner_sha256=sha(__file__),baseline=baseline,
  jobs=[dict(name=n,seed=s,seat=p,repeat=False) for s in range(20001,20009) for p in (0,1) for n in players],
  repeats=[dict(name=players[0],seed=20001,seat=0,repeat=True),dict(name=players[-1],seed=20008,seat=1,repeat=True)])
 save(LOCAL/'config.json',cfg);save(RUN/'config.json',cfg);return cfg

def game(j):
 assert os.environ.get('PYTHONHASHSEED')=='0' and j['seed'] in range(20001,20009)
 assert not (LOCAL/'STOP-NEW').exists()
 cfg=json.loads((LOCAL/'config.json').read_text());assert sha(__file__)==cfg['runner_sha256']
 for p,h in cfg['pins'].items():assert sha(p)==h,('Changed frozen input',p)
 F=library();folder=RUN/('repeats' if j['repeat'] else 'games');folder.mkdir(parents=True,exist_ok=True)
 expected=cfg['signatures'][j['name']];assert F.signature(j['name'],cfg['opponent'])==expected
 target=folder/F.stem(j['name'],j['seed'],j['seat'])
 if target.with_suffix('.metrics.json').exists():m=F.verify(folder,j['name'],j['seed'],j['seat'],expected)
 else:
  F.one((folder,j['name'],cfg['opponent'],j['seed'],j['seat'],expected));m=F.verify(folder,j['name'],j['seed'],j['seat'],expected)
 if j['repeat']:
  original=F.verify(RUN/'games',j['name'],j['seed'],j['seat'],expected);assert m['gameplay_sha256']==original['gameplay_sha256'],'Fresh process repeat differs'
 return dict(**j,margin=m['margin'],seconds=m['seconds'],gameplay_sha256=m['gameplay_sha256'])

def run():
 cfg=json.loads((LOCAL/'config.json').read_text());assert cfg['workers']==4
 F=library();cached=[];todo=[]
 for j in cfg['jobs']:
  folder=RUN/'games';p=(folder/F.stem(j['name'],j['seed'],j['seat'])).with_suffix('.metrics.json')
  if p.exists():cached.append(game(j))
  else:todo.append(j)
 save(LOCAL/'status.json',dict(state='running',phase='task1-games',completed=len(cached),target=48,workers=4))
 with Pool(processes=4,maxtasksperchild=1) as pool:
  for r in pool.imap_unordered(game,todo):
   cached.append(r);save(LOCAL/'status.json',dict(state='running',phase='task1-games',completed=len(cached),target=48,workers=4,last={k:r[k] for k in ('name','seed','seat','seconds')}))
 with Pool(processes=4,maxtasksperchild=1) as pool:repeats=list(pool.imap_unordered(game,cfg['repeats']))
 proof=dict(passed=True,main_games=48,repeats=len(repeats),workers=4,repeat_results=repeats,test_contents_read=0)
 save(RUN/'games-complete.json',proof);save(LOCAL/'status.json',dict(state='phase-complete',phase='task1-games',completed=48,target=48,workers=0))
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 if sys.argv[1]=='prepare':print(json.dumps(dict(jobs=len(prepare()['jobs']),workers=4)))
 else:run()
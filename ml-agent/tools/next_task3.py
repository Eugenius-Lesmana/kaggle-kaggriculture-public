"""Next task1: training-only herd caps, immutable default gate and48 paired live games."""
from collections import Counter
from pathlib import Path
from multiprocessing import Pool
import contextlib,csv,gzip,hashlib,io,json,math,os,statistics,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
DATA=Path('kaggriculture-ml-data');LOCAL=ROOT/'.cache/next';RUN=DATA/'runs/next-20261028/task3';DEST=DATA/'runs/nflow-p4-end16'
BASE='net:board-p4:market:overflow:endmask:endwork';PLAYER=BASE+':end16=board-end16';OPP=str(DATA/'opponents/fifth-place/nflow-main-wash8014/main.py')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(v,separators=(',',':')),encoding='utf8');q.replace(p)
def library():
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):import run_full as F
 return F

def prepare():
 F=library();private=json.loads((ROOT/'.cache/after-rules/config.json').read_text())['pins'];pins={p:sha(p) for p in private if 'nflow-main-wash8014' in p or 'board-p4' in p};p=ROOT/'reports/ENDGAME_MODEL_SELECTION.json';pins[str(p)]=sha(p);p=DATA/'models/board-end16/model.pt';pins[str(p)]=sha(p)
 cfg=dict(base_commit='87ebd94',base=BASE,player=PLAYER,opponent=OPP,workers=4,runner_sha256=sha(__file__),pins=pins,signatures={n:F.signature(n,OPP) for n in (BASE,PLAYER)},jobs=[dict(name=PLAYER,seed=s,seat=p) for s in range(20001,20025) for p in (0,1)])
 save(LOCAL/'task3-inputs.json',cfg);save(RUN/'task3-inputs.json',cfg);return cfg

def game(j,folder=None):
 cfg=json.loads((LOCAL/'task3-inputs.json').read_text());assert sha(__file__)==cfg['runner_sha256']
 for p,h in cfg['pins'].items():assert sha(p)==h,('Frozen input changed',p)
 F=library();expected=cfg['signatures'][j['name']];assert F.signature(j['name'],OPP)==expected;folder=Path(folder) if folder else DEST;folder.mkdir(parents=True,exist_ok=True);p=(folder/F.stem(j['name'],j['seed'],j['seat'])).with_suffix('.metrics.json')
 if not p.exists():F.one((folder,j['name'],OPP,j['seed'],j['seat'],expected))
 return F.verify(folder,j['name'],j['seed'],j['seat'],expected)

def run():
 cfg=json.loads((LOCAL/'task3-inputs.json').read_text());F=library();gate=RUN/'default-gate.json'
 if not gate.exists():
  save(LOCAL/'status.json',dict(state='running',phase='task3-default-gate',workers=1));j=dict(name=BASE,seed=20001,seat=0);m=game(j,RUN/'default-gate');original=json.loads((DATA/'runs/nflow-p4-ovf-end-ew'/F.stem(BASE,20001,0)).with_suffix('.metrics.json').read_text());assert m['gameplay_sha256']==original['gameplay_sha256'],'Default gameplay changed; no variant games allowed';save(gate,dict(passed=True,gameplay_sha256=m['gameplay_sha256']))
 todo=[j for j in cfg['jobs'] if not (DEST/F.stem(PLAYER,j['seed'],j['seat'])).with_suffix('.metrics.json').exists()]
 save(LOCAL/'status.json',dict(state='running',phase='task3-end16-live',completed=48-len(todo),target=48,workers=4))
 with Pool(4,maxtasksperchild=1) as pool:
  for m in pool.imap_unordered(game,todo):
   n=len(list(DEST.glob('*.metrics.json')));save(LOCAL/'status.json',dict(state='running',phase='task3-end16-live',completed=n,target=48,workers=4))
 data=[game(j) for j in cfg['jobs']];save(RUN/'task3-games-complete.json',dict(passed=True,games=48,default_gate_passed=True,runner_sha256=cfg['runner_sha256']));save(LOCAL/'status.json',dict(state='phase-complete',phase='task3-end16-live',completed=48,target=48,workers=0))
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 if sys.argv[1]=='prepare':prepare()
 else:run()
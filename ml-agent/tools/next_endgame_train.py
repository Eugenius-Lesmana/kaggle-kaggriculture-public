"""Pinned, CUDA-only endgame fine-tunes and same-row baseline evaluation. No policy games."""
from pathlib import Path
import csv,hashlib,json,os,subprocess,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
DATA=Path('kaggriculture-ml-data');RUN=DATA/'runs/next-20261028/training';LOCAL=ROOT/'.cache/next'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,separators=(',',':')),encoding='utf8');q.replace(p)
def config():
 pins=[ROOT/p for p in ('tools/train_board_net.py','src/kagml/board_net.py','src/kagml/board_features.py','manifests/turns.csv','manifests/turn-markets.csv','reports/ENDGAME_VALIDATION_SPLIT.json','tools/next_endgame_eval.py')]+[DATA/'models/board-p4/model.pt',Path(__file__)]
 c=dict(pins={str(p):sha(p) for p in pins},runs=[dict(name='board-end16',day_min=16),dict(name='board-end24',day_min=24)],init='board-p4',epochs=4,lr=2e-4,validation_split='endval',day_max=29)
 p=LOCAL/'training-inputs.json'
 if p.exists():assert json.loads(p.read_text())==c,'Frozen training inputs changed'
 else:
  for r in c['runs']:assert not (DATA/'models'/r['name']).exists(),'Refusing pre-existing model directory without this run config'
  save(p,c)
 save(RUN/'inputs.json',c);return c

def main():
 assert os.environ.get('PYTHONHASHSEED')=='0';assert json.loads((LOCAL/'agent-state.json').read_text(encoding='utf-8-sig'))['task2_reported'];import torch;assert torch.cuda.is_available(),'CUDA required'
 c=config()
 with (ROOT/'manifests/turns.csv').open(encoding='utf8',newline='') as f:rows=[r for r in csv.DictReader(f) if r['source']=='l1end']
 assert len(rows)==2987 and all(int(r['game']) not in range(10320,10325) and not 20001<=int(r['game'])<=20024 for r in rows)
 seeds={split:{int(r['game']) for r in rows if r['split']==split} for split in ('train','endval')};assert len(seeds['train'])==96 and len(seeds['endval'])==11 and not seeds['train']&seeds['endval']
 # Only selected l1end files are touched; no test metadata path is opened.
 with (ROOT/'manifests/turn-markets.csv').open(encoding='utf8',newline='') as f:markets={r['worker_file']:r for r in csv.DictReader(f) if r['source']=='l1end'}
 for r in rows:
  assert sha(DATA/r['file'])==r['sha256'];m=markets[r['file']];assert m['worker_sha256']==r['sha256'] and sha(DATA/m['file'])==m['sha256'] and m['split']==r['split']
 save(RUN/'data-checked.json',dict(passed=True,rows=2987,train_seeds=96,validation_seeds=11,worker_arrays_written=0,test_contents_read=0))
 for job in c['runs']:
  for p,h in c['pins'].items():assert sha(p)==h
  report=DATA/'models'/job['name']/'report.json'
  args=[job['name'],'--sources','l1end','--day-min',str(job['day_min']),'--day-max','29','--validation-split','endval','--require-cuda','--init','board-p4','--market','--epochs','4','--lr','2e-4']
  if report.exists():
   old=json.loads(report.read_text());assert len(old['log'])==4 and old['config']['day_min']==job['day_min'] and old['config']['validation_split']=='endval';continue
  save(LOCAL/'status.json',dict(state='running',phase='task3-cuda-training',model=job['name'],epochs=4,game_processes=0))
  log=LOCAL/(job['name']+'-training.log')
  with log.open('a',encoding='utf8') as f:subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/train_board_net.py'),*args],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
  assert len(json.loads(report.read_text())['log'])==4
 save(LOCAL/'status.json',dict(state='running',phase='task3-validation',game_processes=0))
 with (LOCAL/'endgame-validation.log').open('a',encoding='utf8') as f:subprocess.run([sys.executable,'-X','utf8',str(ROOT/'tools/next_endgame_eval.py')],cwd=ROOT,stdout=f,stderr=subprocess.STDOUT,check=True)
 save(RUN/'complete.json',dict(passed=True,models={j['name']:dict(weights_sha256=sha(DATA/'models'/j['name']/'model.pt'),report_sha256=sha(DATA/'models'/j['name']/'report.json')) for j in c['runs']},validation_sha256=sha(ROOT/'reports/ENDGAME_MODEL_VALIDATION.json')))
 save(LOCAL/'status.json',dict(state='phase-complete',phase='task3-training-and-validation',workers=0))
if __name__=='__main__':main()
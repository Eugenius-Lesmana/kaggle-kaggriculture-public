"""Same-row CUDA comparison with P4; invokes unchanged evaluation machinery."""
from pathlib import Path
import csv,json,sys,os
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
import torch
import train_board_net as T
from kagml.board_net import load
from kagml.board_features import COMMANDS
from kagml.paths import data_root,models

def evaluate(name,lo,hi):
 assert torch.cuda.is_available(),'CUDA required';torch.set_num_threads(2);root=data_root()
 with (ROOT/'manifests/turns.csv').open(encoding='utf8') as f:rows=[r for r in csv.DictReader(f) if r['source']=='l1end' and r['split']=='endval' and lo<=int(r['day'])<=hi]
 assert rows and all(int(r['game']) not in range(10320,10325) and not 20001<=int(r['game'])<=20024 for r in rows)
 with (ROOT/'manifests/turn-markets.csv').open(encoding='utf8') as f:
  for r in csv.DictReader(f):T.MARKETS[(root/r['worker_file']).as_posix()]=root/r['file']
 model=load(models()/name/'model.pt','cuda',market=True);model.to('cuda');result=T.evaluate(model,T.Chunks([root/r['file'] for r in rows]),'cuda',[':'.join(c) for c in COMMANDS]);assert result['decisions']>0
 return dict(model=name,day_min=lo,day_max=hi,rows=len(rows),result=result)
def main():
 out=ROOT/'reports/ENDGAME_MODEL_VALIDATION.json';results=[]
 for name,lo,hi in [('board-p4',16,29),('board-p4',24,29),('board-end16',16,29),('board-end16',24,29),('board-end24',24,29)]:
  results.append(evaluate(name,lo,hi));out.write_text(json.dumps(dict(passed=True,results=results),separators=(',',':')),encoding='utf8')
 print(json.dumps([dict(model=r['model'],day_min=r['day_min'],command_acc=r['result']['command_acc'],decisions=r['result']['decisions']) for r in results],separators=(',',':')))
if __name__=='__main__':main()
"""One detached, resumable phase. Reports await review before the next task is authorized."""
import json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];RUN=Path('kaggriculture-ml-data/runs/after-rules-20261028')
def main(stage):
 assert os.environ.get('PYTHONHASHSEED')=='0'
 if stage in ('task1-analysis','task2-analysis'):
  import after_rules_profiles as P
  import after_rules_reports as R
  if stage=='task1-analysis':
   assert json.loads((RUN/'games-complete.json').read_text())['passed'];P.prepare();P.run('task1-profiles')
   import after_rules_loss as L
   L.main();R.loss_report()
  else:
   assert json.loads((RUN/'task1-reported.json').read_text())['passed'];P.run('task2-profiles');R.selling_report()
  P.save(RUN/(stage+'-ready.json'),dict(passed=True,awaiting_review=True))
 elif stage=='task3-labels':
  import after_rules_endgame as W
  import after_rules_endgame_run as Q
  W.guard();W.prepare();Q.run()
  import after_rules_publish as P
  P.publish()
 else:raise ValueError(stage)
if __name__=='__main__':main(sys.argv[1])
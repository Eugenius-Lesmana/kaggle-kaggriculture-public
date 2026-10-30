"""Detached four-process analysis queue, followed by report aggregation."""
from concurrent.futures import ProcessPoolExecutor,as_completed
import sale_timing_bound as T
if __name__=='__main__':
 cfg=T.prepare();T.RUN.mkdir(parents=True,exist_ok=True)
 with ProcessPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(T.case,j) for j in cfg['jobs']]):
   f.result();n=sum((T.RUN/f"{j['seed']}-seat{j['seat']}.json").exists() for j in cfg['jobs']);T.save(T.LOCAL/'status.json',dict(state='running',phase='task5-timing-analysis',completed=n,target=16,analysis_processes=4,game_processes=0))
 import sale_timing_report as R
 R.main();T.save(T.LOCAL/'status.json',dict(state='phase-complete',phase='task5-reported',completed=16,target=16,workers=0))
"""Generate unaffected families with the ORIGINAL frozen worker. Hold failures; never publish or omit them."""
import hashlib,json,os,sys
from concurrent.futures import ProcessPoolExecutor,wait,FIRST_COMPLETED
from pathlib import Path
import after_rules_endgame as W
import after_rules_endgame_run as Q
HELD=W.RUN/'held-families.json'
def key(j):return f"{j['row']['seed']}-{j['seat']}"
def stamp(cfg,held,active,state='running'):
 W.save(W.LOCAL/'status.json',dict(state=state,phase='task3-unaffected-families',completed_families=sum(Q.done(j).exists() for j in cfg['jobs']),target_families=214,held_families=len(held),requested_segments=1712,encoded_receipts=len(list((W.RUN/'dataset/encoding/l1end').glob('*.json'))),workers=active,publication_allowed=False))
def run():
 W.guard();cfg=json.loads((W.LOCAL/'endgame-inputs.json').read_text());assert W.sha(W.ROOT/'tools/after_rules_endgame.py')==cfg['worker_sha256']
 held=json.loads(HELD.read_text());pending=[j for j in cfg['jobs'] if not Q.done(j).exists() and key(j) not in held];active={};stamp(cfg,held,0)
 with ProcessPoolExecutor(max_workers=4) as pool:
  while pending or active:
   while pending and len(active)<4:
    j=pending.pop(0);active[pool.submit(W.execute,j)]=j
   ready,_=wait(active,return_when=FIRST_COMPLETED)
   for f in ready:
    j=active.pop(f)
    try:f.result()
    except AssertionError as e:
     if str(e)!='Worker feature capacity exceeded':raise
     held[key(j)]=dict(job=j,reason=str(e),state='incomplete-pending-user-decision');W.save(HELD,held)
   stamp(cfg,held,len(active))
 assert all(Q.done(j).exists() or key(j) in held for j in cfg['jobs'])
 stamp(cfg,held,0,'waiting-approval')
 # No verification marker, no publication, no count changes: the requested full dataset remains incomplete.
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 run()
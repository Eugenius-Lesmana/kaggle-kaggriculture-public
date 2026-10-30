"""Non-test package N counting tables; all quantities are computed from the published arrays."""
import csv
from collections import Counter,defaultdict
import json
from pathlib import Path
import sys
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from build_turn_dataset import B,ROOT,REPO,sha
import numpy as np


def write(name,fields,rows):
    with (REPO/'reports'/name).open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    manifest=list(csv.DictReader((REPO/'manifests/turns.csv').open()));counts=Counter();amounts=defaultdict(Counter);order=defaultdict(Counter);walk=defaultdict(Counter);path=defaultdict(Counter);sizes=defaultdict(Counter)
    # Filter before opening any tensor: held-out labels cannot enter these tables.
    selected=[r for r in manifest if r['split']!='test']
    for i,r in enumerate(selected):
        assert int(r['game']) not in range(10320,10325)
        source=r['source'];day=int(r['day']);band='0-5' if day<6 else ('6-13' if day<14 else ('14-21' if day<22 else ('22-28' if day<29 else '29')))
        assert sha(ROOT/r['file'])==r['sha256']
        with np.load(ROOT/r['file'],allow_pickle=False) as packed:
            a={k:packed[k] for k in packed.files}
            mask=a['unit_mask'];sizes[source].update(segments=1,turns=len(mask),worker_decisions=int(mask.sum()),compressed_bytes=(ROOT/r['file']).stat().st_size,effective=int(a['took_effect'].sum()),issued_noops=int((mask&~a['command_loss_mask']).sum()),amount_above_5=int((mask&a['amount_applicable']&(a['amount']>5)).sum()))
            for t,u in zip(*np.where(mask)):
                cid=int(a['command'][t,u]);cmd=B.COMMANDS[cid];op=cmd[0];effect=bool(a['took_effect'][t,u]);hour=int(a['step'][t])%24;n=int(mask[t].sum());relative='farmer' if u==0 else ('early' if (u-1)/max(1,n-2)<1/3 else ('middle' if (u-1)/max(1,n-2)<2/3 else 'late'))
                for dimension,group in [('overall','all'),('hour',str(hour)),('day_band',band)]:counts[(source,dimension,group,':'.join(cmd),effect)]+=1
                for axis,group in [('absolute',str(u)),('relative',relative)]:
                    v=order[(source,axis,group,op)];v.update(decisions=1,effective=int(effect),future_jobs=int(a['target'][t,u]!=100),target_distance=int(a['target_distance'][t,u]))
                if op in ('PICKUP','PLACE'):
                    v=amounts[(source,op,cmd[1],int(a['amount'][t,u]),bool(a['amount_applicable'][t,u]),effect)];v.update(decisions=1,transferred=int(a['transferred'][t,u]))
                if op in B.MOVES and effect and a['target'][t,u]!=100:
                    x,y=a['position'][t,u];target=int(a['target'][t,u]);dx,dy=B.MOVES[op];before=abs(x-target%10)+abs(y-target//10);after=abs(x+dx-target%10)+abs(y+dy-target//10);kind=B.COMMANDS[int(a['target_command'][t,u])][0];dist='0-2' if before<=2 else ('3-5' if before<=5 else '6+');value=float(a['target_value'][t,u]);vb='negative' if value<0 else ('0' if value==0 else ('1-99' if value<100 else ('100-499' if value<500 else '500+')));v=walk[(source,kind,dist,vb)];v.update(moves=1,away=int(after>before),toward=int(after<before))
                    if t and mask[t-1,u] and B.COMMANDS[int(a['command'][t-1,u])][0] in B.MOVES and a['target'][t-1,u]!=100:
                        v.update(consecutive_walking=1,target_changes=int(a['target'][t-1,u]!=a['target'][t,u]))
            for u in range(B.MAX_UNITS):
                present=np.where(mask[:,u])[0]
                if not len(present):continue
                jobs=[t for t in present if a['took_effect'][t,u] and B.COMMANDS[int(a['command'][t,u])][0] not in (*B.MOVES,'PASS')]
                for j,t in enumerate(jobs[:-1]):
                    anchor=jobs[j-1] if j else int(present[0]);later=jobs[j+1];A=a['position'][anchor,u];P=a['position'][t,u];C=a['position'][later,u];ab=int(np.abs(A-P).sum());bc=int(np.abs(P-C).sum());ac=int(np.abs(A-C).sum());strict=ab>0 and bc>0;onpath=strict and ab+bc==ac
                    actual=sum(bool(a['took_effect'][q,u]) and B.COMMANDS[int(a['command'][q,u])][0] in B.MOVES for q in range(anchor,later))
                    v=path[(source,B.COMMANDS[int(a['command'][t,u])][0],j==0)];v.update(intermediate_jobs=1,distinct_legs=int(strict),geometric_shortest=int(onpath),actual_shortest=int(onpath and actual==ac))
        if (i+1)%500==0:print(json.dumps({'counted_segments':i+1}),flush=True)
    write('turns-command-mix.csv',('source','dimension','group','command','took_effect','decisions'),[dict(zip(('source','dimension','group','command','took_effect','decisions'),(*k,v))) for k,v in sorted(counts.items())])
    for filename,keys,stats,data in [('turns-amounts.csv',('source','command','item','amount','amount_applies','took_effect'),('decisions','transferred'),amounts),('turns-worker-order.csv',('source','axis','group','command'),('decisions','effective','future_jobs','target_distance'),order),('turns-walking.csv',('source','next_job','distance_band','value_band'),('moves','away','toward','consecutive_walking','target_changes'),walk),('turns-on-path.csv',('source','job','left_censored_anchor'),('intermediate_jobs','distinct_legs','geometric_shortest','actual_shortest'),path)]:
        write(filename,(*keys,*stats),[{**dict(zip(keys,k)),**{f:v[f] for f in stats}} for k,v in sorted(data.items())])
    fields=('segments','turns','worker_decisions','compressed_bytes','effective','issued_noops','amount_above_5')
    write('turns-sizes.csv',('source',*fields),[{'source':s,**{f:v[f] for f in fields}} for s,v in sorted(sizes.items())])
    total=sum(sizes.values(),Counter());w=sum(walk.values(),Counter());p=sum(path.values(),Counter())
    summary=dict(total=total,walking=w,on_path=p,command_mix=dict(Counter({op:sum(v for k,v in counts.items() if k[1]=='overall' and k[3].split(':')[0]==op) for op in {k[3].split(':')[0] for k in counts}})))
    (ROOT/'runs/turns/counts.json').write_text(json.dumps(summary),encoding='utf-8')
    text=f"""# Turn-dataset counts (package N)

Non-test teacher turns only: {total['segments']:,} segments, {total['turns']:,} turns,
{total['worker_decisions']:,} worker decisions; {total['effective']:,} change native state.
All test games 10320-10324 were filtered before opening tensors. Counts include train and analysis;
L3 begins at its takeover. See `turns-sizes.csv` for each source.

Issued non-PASS no-ops: {total['issued_noops']:,}. They remain in arrays; command-loss mask excludes them.
PASS is a valid stay choice even though native state does not change. Amounts above five:
{total['amount_above_5']:,}; exact values retained, excluded from the five-class amount loss.

## Movement and targets

{w['moves']:,} effective moves have a future effective job. {w['away']:,} move away from that job's tile;
{w['toward']:,} move toward it. `turns-walking.csv` separates destination job, distance and rough value.
Consecutive walking pairs with targets: {w['consecutive_walking']:,}; target changes: {w['target_changes']:,}.
The target is the next *observed* effective job, so it cannot change across uninterrupted walking by
construction. This is not evidence that the teacher never changes hidden intention. Intention/diversion
frequency is unidentifiable from issued commands alone; away moves are only an observable proxy.

Of {p['intermediate_jobs']:,} intermediate jobs with a later job, {p['distinct_legs']:,} have nonzero legs
from anchor to job and job to later job; {p['geometric_shortest']:,} lie on a Manhattan shortest path
and {p['actual_shortest']:,} also have an observed movement count equal to that shortest distance.
Anchor = previous effective job, or first teacher position if none (left-censored, explicitly flagged).
The current job and next later job must differ; repeated care/feed on the same tile do not count.
These observed on-path jobs do not prove a prior intended target.

## Reading the CSVs

- `turns-command-mix.csv`: exact command including item, issued count, native effect, source, overall/hour/day band.
- `turns-worker-order.csv`: absolute slot and relative farmer/early/middle/late hand groups; job mix and
  sum of distance to next effective job (divide by future_jobs for its mean). Relative groups split hand
  ordinal into thirds separately each turn. These are associations, not causal coordination effects.
- `turns-amounts.csv`: exact requested quantity, context applicability, native effect and units transferred.
  `amount_applies=False` includes animal placement (native always places one) and invalid field placement.
- `turns-walking.csv`: toward/away counts plus consecutive walking target comparisons. Distance uses Manhattan
  geometry (locked land is passable); value is the existing work_features immediate-dollar heuristic, not
  realized profit. Value/distance refer to the future job, never encoder inputs.
- `turns-on-path.csv`: intermediate-job geometry and observed shortest movement, grouped by job and censoring.
- `turns-sizes.csv`: compressed NPZ bytes and non-test source totals. Each worker present before the turn counts
  once, including implicit PASS; newly hired hands appear next turn. No nonexistent workers are counted.

Rerun: `PYTHONHASHSEED=0 python tools/report_turn_dataset.py` (set KAGML_DATA to the external data root).
"""
    (REPO/'reports/TURNS_COUNTS.md').write_text(text,encoding='utf-8');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()

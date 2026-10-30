"""Summarize complete live runs without opening protected test contents."""
from pathlib import Path
from collections import defaultdict
import csv,json,statistics,math
ROOT=Path(__file__).resolve().parents[1];DATA=Path('kaggriculture-ml-data');LOCAL=ROOT/'.cache/next'
def paired(folder,base='nflow-p4-ovf-end-ew'):
 def load(n):
  rows=[json.loads(p.read_text()) for p in (DATA/'runs'/n).glob('*.metrics.json')];d={(r['seed'],r['seat']):r for r in rows};assert len(d)==48 and set(d)=={(s,t) for s in range(20001,20025) for t in (0,1)}
  assert all(r['steps']==720 and r['statuses']==['DONE','DONE'] and not r.get('policy_errors') and not r.get('opponent_errors') for r in d.values());return d
 a,b=load(folder),load(base);out=dict(run=folder,base=base,games=48)
 for label,fn in [('margin',lambda r:r['banks'][0]-r['banks'][1]),('ours',lambda r:r['banks'][0]),('opponent',lambda r:r['banks'][1])]:
  vals=[statistics.mean(fn(a[s,t])-fn(b[s,t]) for t in (0,1)) for s in range(20001,20025)];out[label]=dict(delta=statistics.mean(vals),seed_se=statistics.stdev(vals)/math.sqrt(24))
 out.update(share=sum(r['banks'][0] for r in a.values())/sum(r['banks'][1] for r in a.values()),wins=sum(r['win'] for r in a.values()),kept=out['margin']['delta']>2*out['margin']['seed_se']);return out

def animal():
 result=paired('nflow-p4-herdcap');caps=json.loads((ROOT/'reports/ANIMAL_MIX_TRAIN_CAPS.json').read_text());gate=json.loads((DATA/'runs/next-20261028/default-gate.json').read_text());assert gate['passed']
 with (ROOT/'reports/2026-10-28-animal-mix-daily.csv').open(encoding='utf8',newline='') as f:daily=list(csv.DictReader(f))
 agg=[]
 for day in range(30):
  for role in ('ruled','teacher'):
   rs=[r for r in daily if int(r['day'])==day and r['role']==role];assert len(rs)==16
   z=dict(day=day,role=role)
   for a in ('COW','SHEEP','GOOSE'):z[a]=sum(float(r[a]) for r in rs)/16;z['bought_'+a]=sum(float(r['bought_'+a]) for r in rs)/16
   for p in ('MILK','WOOL','EGG'):
    q=sum(float(r[p+'_units']) for r in rs);rev=sum(float(r[p+'_revenue']) for r in rs);z[p+'_units']=q/16;z[p+'_price']=rev/q if q else None
   agg.append(z)
 with (ROOT/'reports/2026-10-28-animal-mix-summary.csv').open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(agg[0]));w.writeheader();w.writerows(agg)
 m=result['margin'];text=['# Animal mix — 2026-10-28',f"**Reject `herdcap`: paired margin {m['delta']:+,.0f} coins/game (seed SE {m['seed_se']:,.0f}); share {result['share']:.3f}, {result['wins']}/48 wins.** Best remains `net:board-p4:market:overflow:endmask:endwork`.",f"Our bank changes {result['ours']['delta']:+,.0f}/game (SE {result['ours']['seed_se']:,.0f}); fifth-nflow’s bank changes {result['opponent']['delta']:+,.0f} (SE {result['opponent']['seed_se']:,.0f}). Difference of these bank changes equals the margin result. The retention rule was positive paired gain of at least about2SE; this version fails.",
 'All48 games use evaluation seeds20001–20024 bothseats against live fifth-nflow, unchanged opponent and frozen P4 weights. The default ruled agent was first replayed at seed20001seat0 and its exact gameplay hash matched the specified control. Four game workers, PYTHONHASHSEED=0. No test contents or evaluation tuning.',
 '## Fixed rule and training-only cap derivation',
 'The opt-in market-side cap clips cows/sheep purchases above ceil(median teacher end-of-day placed+stored+carried holdings), by day. Already placed animals, inventory animals and earlier same-turn purchase orders count. Geese are unchanged; no substitution or selling existing livestock. All90 cap inputs are teacher full games on45 plan TRAIN seeds, bothseats, against Metav4. No20001–20024 cap inputs. Transferring that teacher size to our farm/opponent can fail; the observed loss does not disprove all animal-mix interventions.',
 'An animal retained after a shrinking daily cap is not removed; only new purchases are clipped. This can leave empty structures/plans and inputs designed for the original mix. We did not retune on these evaluation results.',
 '## Existing-game descriptive daily comparison',
 'The following tables compare16 ruled P4 games and16 teacher games against fifth-nflow, seeds20001–20008 bothseats. They are descriptive and were never used to derive caps. Held counts are placed animals at dawn; training caps instead use total holdings at day end. Purchases are native executed units; sale prices are unit-weighted revenue/units. Full30-day values are supplied in the linked CSVs.',
 '| Day | Agent | Cows | Sheep | Geese | Cows bought | Sheep bought | Geese bought | Milk units / price | Wool units / price | Egg units / price |','| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |']
 for r in agg:
  def f(x):return f'{x:.2f}' if x is not None else 'NA'
  text.append('| '+' | '.join([str(r['day']),r['role'],*[f(r[a]) for a in ('COW','SHEEP','GOOSE','bought_COW','bought_SHEEP','bought_GOOSE')],*[f(r[p+'_units'])+' / '+f(r[p+'_price']) for p in ('MILK','WOOL','EGG')]])+' |')
 text+=['[Daily game-level inputs](2026-10-28-animal-mix-daily.csv), [daily summary](2026-10-28-animal-mix-summary.csv), [training caps and90 source hashes](ANIMAL_MIX_TRAIN_CAPS.json), [paired checks](ANIMAL_MIX_CHECKS.json).','The opt-in implementation remains available for reproducibility; it is not part of the best agent. This test does not identify the benefit of replacing livestock with crops or geese, which was not attempted.']
 (ROOT/'reports/2026-10-28-animal-mix.md').write_text('\n\n'.join(text)+'\n',encoding='utf8');(ROOT/'reports/ANIMAL_MIX_CHECKS.json').write_text(json.dumps(dict(passed=True,paired=result,cap_training_games=90,cap_training_seeds=45,default_gameplay_hash=gate['gameplay_sha256'],test_contents_read=0,evaluation_tuning=0),separators=(',',':')))
 print(json.dumps(result,separators=(',',':')))
if __name__=='__main__':animal()
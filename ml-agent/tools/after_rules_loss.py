"""Exact paired loss bridges and non-additive work/asset diagnostics, from existing native profiles."""
from collections import Counter,defaultdict
import csv,json,math,statistics,sys
from pathlib import Path
import numpy as np
from after_rules_extract import ROOT,DATA,RUN,LOCAL,PROFILES,PRODUCTS,sha,save,key
WINDOWS=((12,22,12,22),(22,28,22,28),(28,30,28,0))

def table(name,rows):
 p=ROOT/'reports'/name;p.parent.mkdir(exist_ok=True)
 fields=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='',encoding='utf8') as f:
  w=csv.DictWriter(f,fields);w.writeheader();w.writerows(rows)
def mn(xs):return statistics.mean(xs)
def ratio(a,b):return a/b if b else None

def uncertainty(rows,column):
 g=defaultdict(list)
 for r in rows:g[r['seed']].append(r[column])
 assert len(g)==8 and all(len(v)==2 for v in g.values())
 a=[mn(v) for v in g.values()]
 return mn(a),statistics.stdev(a)/math.sqrt(len(a))

def at(c,seat,day):return c['daily'][day*2+seat]
def best(c,day,p):return max(at(c,s,day)['products'][p]['best'] for s in (0,1))
def period(c,seat,a,b):return [at(c,seat,d) for d in range(a,b)]

def assets(c,seat,b,prices):
 s=c['snapshots'][str(b)][str(seat)];held=sum(s['held'][p]*prices[p] for p in PRODUCTS)
 seed_costs={'WHEAT':10,'CARROT':20,'TOMATO':50,'STRAWBERRY':100,'MELON':80}
 crop_ready=sum(t['yield_units']*prices[t['crop']] for t in s['crops'])+sum(q*prices[p] for p,q in s['animal_yield'].items())
 immature=[t for t in s['crops'] if t['days_to_ripen']>0]
 return dict(held_products_value=held,seed_stock_cost=sum(q*seed_costs[p] for p,q in s['seeds'].items()),
  stored_animal_cost=sum(q*c['animal_costs'][p] for p,q in s['stored_animals'].items()),
  placed_animal_cost=sum(q*c['animal_costs'][p] for p,q in s['animals'].items()),standing_ready_yield_value=crop_ready,
  growing_crop_seed_cost=sum(t['seed_cost'] for t in s['crops']),
  immature_first_yield_gross=sum(t['first_yield_units']*prices[t['crop']] for t in immature if t['viable']),
  immature_crops=len(immature),nonripening_crops=sum(not t['viable'] for t in immature),crop_tiles=len(s['crops']),animal_tiles=sum(s['animals'].values()))

def main():
 cfg=json.loads((LOCAL/'profiles-inputs.json').read_text(encoding='utf8'));assert cfg['analysis_version']==2
 cs={};source_rows=[]
 for j in cfg['jobs']:
  c=json.loads((PROFILES/(key(j)+'.json')).read_text(encoding='utf8'));assert c['passed'] and c['source']==j and c['worker_sha256']==cfg['worker_sha256']
  assert c['new_games']==c['test_contents_read']==0 and len(c['native_rows'])==6
  terminal=c['snapshots']['30'];assert terminal[str(j['seat'])]['money']-terminal[str(1-j['seat'])]['money']==j['margin']
  cs[j['handover'],j['seed'],j['seat']]=c;source_rows.append(dict(**j,profile_sha256=sha(PROFILES/(key(j)+'.json'))))
 assert len(cs)==64
 pairs=[];products=[];works=[];spends=[];cropchoices=[];asset_rows=[];asset_crops=[];all_residual=[]
 for start,end,ha,hb in WINDOWS:
  window=f'{start}-{end-1}'
  for seed in range(20001,20009):
   for seat in (0,1):
    A=cs[ha,seed,seat];B=cs[hb,seed,seat];assert A['prefixes'][str(start)]==B['prefixes'][str(start)],('prefix mismatch',window,seed,seat)
    ident=dict(window=window,seed=seed,seat=seat)
    a=period(A,seat,start,end);b=period(B,seat,start,end)
    later_a=period(A,seat,end,30);later_b=period(B,seat,end,30)
    delta=lambda getter:sum(getter(r) for r in a)-sum(getter(r) for r in b)
    r=dict(**ident,gain=A['source']['margin']-B['source']['margin'],own_revenue=delta(lambda d:d['revenue']),spend_saving=-delta(lambda d:d['spend']),
     own_later_net=sum(d['revenue']-d['spend'] for d in later_a)-sum(d['revenue']-d['spend'] for d in later_b))
    for label,lo,hi in [('in',start,end),('after',end,30)]:
     aa=period(A,1-seat,lo,hi);bb=period(B,1-seat,lo,hi)
     r['opponent_'+label+'_benefit']=-(sum(d['revenue']-d['spend'] for d in aa)-sum(d['revenue']-d['spend'] for d in bb))
    r['opponent_benefit']=r['opponent_in_benefit']+r['opponent_after_benefit']
    for n in ('produced_value','sale_timing_gap','market_frontier_gap','inventory_release','input_buyback_value','consumed_value','other_loss_value'):r[n]=0.
    for side,s in [('ours',seat),('opponent',1-seat)]:
     for phase,lo,hi in [('in',start,end),('after',end,30)]:
      for p in PRODUCTS:
       sums=[Counter(),Counter()]
       for d in range(lo,hi):
        price=max(best(A,d,p),best(B,d,p))
        for i,c in enumerate((A,B)):
         z=at(c,s,d)['products'][p];v=sums[i];gb=best(c,d,p)
         for k in ('produced','consumed','bought','sold','revenue','opening','closing'):v[k]+=z[k]
         v['volume_notional']+=z['sold']*price;v['own_best_notional']+=z['sold']*gb
         v['timing_gap']+=z['revenue']-z['sold']*gb;v['frontier_gap']+=z['sold']*(gb-price)
         v['produced_value']+=z['produced']*price;v['inventory_release']-=(z['closing']-z['opening'])*price
         v['input_buyback_value']+=z['bought']*price;v['consumed_value']-=z['consumed']*price
         lost=z['opening']+z['produced']+z['bought']-z['sold']-z['consumed']-z['closing']
         v['other_loss_units']+=lost;v['other_loss_value']-=lost*price
       x,y=sums;out=dict(**ident,side=side,phase=phase,product=p)
       for name,v in [('A',x),('B',y)]:
        out.update({name+'_'+('sum_daily_'+k if k in ('opening','closing') else k):v[k] for k in v});out[name+'_avg_price']=ratio(v['revenue'],v['sold']);out[name+'_capture_best']=ratio(v['revenue'],v['own_best_notional'])
       for k in ('produced','sold','revenue','volume_notional','timing_gap','frontier_gap','other_loss_units'):out['delta_'+k]=x[k]-y[k]
       assert abs(out['delta_revenue']-(out['delta_volume_notional']+out['delta_timing_gap']+out['delta_frontier_gap']))<1e-6
       products.append(out)
       if side=='ours' and phase=='in':
        for k in ('produced_value','inventory_release','input_buyback_value','consumed_value','other_loss_value'):r[k]+=x[k]-y[k]
        r['sale_timing_gap']+=x['timing_gap']-y['timing_gap'];r['market_frontier_gap']+=x['frontier_gap']-y['frontier_gap']
    flow=sum(r[k] for k in ('produced_value','sale_timing_gap','market_frontier_gap','inventory_release','input_buyback_value','consumed_value','other_loss_value'))
    r['sales_bridge_residual']=r['own_revenue']-flow
    r['cash_residual']=r['gain']-(r['own_revenue']+r['spend_saving']+r['own_later_net']+r['opponent_benefit'])
    r['full_bridge_residual']=r['gain']-(flow+r['spend_saving']+r['own_later_net']+r['opponent_benefit'])
    assert max(abs(r[k]) for k in ('cash_residual','full_bridge_residual','sales_bridge_residual'))<1e-6,r
    all_residual.append(r['full_bridge_residual'])
    for name,c,ds in [('A',A,a),('B',B,b)]:
     w=Counter();[w.update(d['work']) for d in ds]
     for k in ('slots','jobs','moves','idle','ineffective_nonpass','job_value'):r[name+'_'+k]=w[k]
     r[name+'_value_per_worker_turn']=ratio(w['job_value'],w['slots']);r[name+'_moves_per_job']=ratio(w['moves'],w['jobs'])
    ops=sorted({k.removeprefix('effective_') for d in a+b for k in d['work'] if k.startswith('effective_')})
    for op in ops:
     works.append(dict(**ident,op=op,A_jobs=sum(d['work'].get('effective_'+op,0) for d in a),B_jobs=sum(d['work'].get('effective_'+op,0) for d in b),A_value=sum(d['work'].get('job_value_'+op,0) for d in a),B_value=sum(d['work'].get('job_value_'+op,0) for d in b)))
    for crop in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON'):
     cropchoices.append(dict(**ident,crop=crop,**{name+'_'+k:sum(d['work'].get(k+'_'+crop,0) for d in ds) for name,ds in [('A',a),('B',b)] for k in ('plant','ripenable','seed_bought')}))
    for bucket in sorted({k for d in a+b for k in d['spending']}):
     spends.append(dict(**ident,bucket=bucket,A_spend=sum(d['spending'].get(bucket,0) for d in a),B_spend=sum(d['spending'].get(bucket,0) for d in b)))
    prices={p:max(best(A,end-1,p),best(B,end-1,p)) for p in PRODUCTS}
    for label,c in [('A',A),('B',B)]:
     av=assets(c,seat,end,prices);asset_rows.append(dict(**ident,condition=label,boundary=end,**av))
     for t in c['snapshots'][str(end)][str(seat)]['crops']:asset_crops.append(dict(**ident,condition=label,**t))
    pairs.append(r)
 for seed in range(20001,20009):
  for seat in (0,1):assert sum(r['gain'] for r in pairs if r['seed']==seed and r['seat']==seat)==cs[12,seed,seat]['source']['margin']-cs[0,seed,seat]['source']['margin']
 outputs=[('paired',pairs),('products',products),('work',works),('spending',spends),('planting',cropchoices),('assets',asset_rows),('boundary-crops',asset_crops),('sources',source_rows)]
 for name,rows in outputs:table('2026-10-28-loss-after-rules-'+name+'.csv',rows)
 summary=[]
 for start,end,_,_ in WINDOWS:
  window=f'{start}-{end-1}';rs=[r for r in pairs if r['window']==window]
  mean,se=uncertainty(rs,'gain');s=dict(window=window,gain=mean,se=se)
  for k in rs[0]:
   if k not in ('window','seed','seat','gain'):s[k]=mn([r[k] for r in rs if r[k] is not None]) if any(r[k] is not None for r in rs) else None
  for label in ('A','B'):
   s[label+'_value_per_worker_turn']=sum(r[label+'_job_value'] for r in rs)/sum(r[label+'_slots'] for r in rs)
   s[label+'_moves_per_job']=sum(r[label+'_moves'] for r in rs)/sum(r[label+'_jobs'] for r in rs)
  summary.append(s)
 table('2026-10-28-loss-after-rules-summary.csv',summary)
 proof=dict(passed=True,source_games=64,paired_windows=48,independent_seeds=8,physical_seats=[0,1],identical_prefixes_checked=48,native_tables_per_game=6,
  max_full_bridge_residual=max(abs(v) for v in all_residual),stock_flow_loss_inferred=False,direct_discard_hooks=True,stock_flow_adjustment_by_window={r['window']:r['other_loss_value'] for r in summary},telescoping_passed=True,evaluation_games_generated=48,verification_repeat_games=2,new_games_by_profile_extraction=0,test_contents_read=0,worker_sha256=cfg['worker_sha256'],protected_hashes=cfg['protected_hashes'])
 save(ROOT/'reports/AFTER_RULES_LOSS_CHECKS.json',proof);save(LOCAL/'summary.json',dict(summary=summary,proof=proof))
 print(json.dumps(summary,separators=(',',':')))
if __name__=='__main__':main()
"""Markdown delivery from the current ruled-agent profiles; no games or training calls."""
from collections import Counter,defaultdict
import csv,json,math,statistics
from pathlib import Path
from after_rules_extract import ROOT,DATA,RUN,LOCAL,PROFILES,PRODUCTS,key,sha
from after_rules_loss import table,uncertainty

def read(name):return list(csv.DictReader((ROOT/'reports'/name).open(encoding='utf8')))
def mean(xs):return statistics.mean(xs) if xs else 0
def fmt(x):return '—' if x is None else f'{x:,.2f}'
def signed(x):return f'{x:+,.0f}'
def md(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join('---' for _ in headers)+' |']+['| '+' | '.join(map(str,row))+' |' for row in rows])
def cases(teacher=False):
 cfg=json.loads((LOCAL/'profiles-inputs.json').read_text());jobs=cfg['teacher_jobs'] if teacher else cfg['jobs'];out=[]
 for j in jobs:
  c=json.loads((PROFILES/(key(j)+'.json')).read_text());assert c['passed'] and c['worker_sha256']==cfg['worker_sha256'] and c['source']==j
  out.append(c)
 return out

def loss_report():
 value=json.loads((LOCAL/'summary.json').read_text());s=value['summary'];assert value['proof']['passed']
 cs={(c['source']['handover'],c['source']['seed'],c['source']['seat']):c for c in cases()};curve=[]
 for d in (12,22,28):
  rows=[dict(seed=seed,seat=seat,gain=cs[d,seed,seat]['source']['margin']-cs[0,seed,seat]['source']['margin']) for seed in range(20001,20009) for seat in (0,1)]
  m,se=uncertainty(rows,'gain');curve.append(dict(day=d,gain=m,se=se))
 table('2026-10-28-loss-after-rules-curve.csv',curve)
 labels={'own_revenue':'our window sales','spend_saving':'spending saved','own_later_net':'later own net','opponent_benefit':'opponent net effect'}
 lead=[]
 for r in s:
  tops=sorted(labels,key=lambda k:abs(r[k]),reverse=True)[:3]
  lead.append([r['window'],f"{r['gain']:+,.0f} ({r['se']:,.0f})",'; '.join(labels[k]+' '+signed(r[k]) for k in tops)])
 largest=max(s,key=lambda r:r['gain'])
 text=['# Loss curve after rules — 2026-10-28',
 f"**The largest remaining window is days {largest['window']}: {largest['gain']:+,.0f} coins/game (paired-seed SE {largest['se']:,.0f}) recovered by the teacher.** The exact cash contributions follow.",
 '**Current agent: `net:board-p4:market:overflow:endmask:endwork`.** The table below gives the largest remaining cash contributions per window. These estimates use eight independent evaluation seeds, both seats; positive means the teacher intervention improves our final margin.',
 md(['Window','Margin gain/game (seed SE)','Largest cash contributions'],lead),
 'All 48 requested handover games are complete, plus two exact fresh-process repeat checks. The teacher takes over at day 12, 22 or 28 and plays the remainder including day 29 itself; our rules do not wrap its actions. Controls are the same seed/seat games from `runs/nflow-p4-ovf-end-ew`. This updates the old unruled P4 diagnosis; it does not compare the new and old policies on different farms as if they shared a morning.',
 md(['Teacher from day','Gain vs ruled baseline/game','Paired-seed SE'],[[r['day'],signed(r['gain']),fmt(r['se'])] for r in curve]),
 '## Cash split that adds exactly',
 md(['Window','Our sales Δ','Spend saving','Later own net Δ','Opponent during','Opponent later','Total','Residual'],[[r['window'],*[signed(r[k]) for k in ('own_revenue','spend_saving','own_later_net','opponent_in_benefit','opponent_after_benefit','gain')],fmt(r['cash_residual'])] for r in s]),
 'Every pair is identical through the window-start morning. Windows are handover12 vs handover22 (12–21), handover22 vs handover28 (22–27), and handover28 vs the ruled baseline (28–29). All 48 pair prefixes and terminal margins are checked, and the window gains telescope to handover12 minus baseline for every seed and seat. Later own net is realized subsequent revenue minus spending. Both branches use the teacher later, but its memory, cash, inventory and reacting market/opponent can differ; it is not a pure farm-layout causal effect.',
 '## Production, selling and directly measured discarded stock',
 md(['Window','Harvest/collection Δ value','Own-best timing Δ','Market frontier Δ','Inventory release Δ','Buyback input value Δ','Consumption saving Δ','Discard saving Δ','Own sales Δ'],[[r['window'],*[signed(r[k]) for k in ('produced_value','sale_timing_gap','market_frontier_gap','inventory_release','input_buyback_value','consumed_value','other_loss_value','own_revenue')]] for r in s]),
 'For each product/day, both branches use the same reference C: the maximum observed price across the pair, including executed unit prices from both seats. Revenue is produced×C + bought-input×C − consumed×C − discarded×C − (closing-held−opening-held)×C plus sale-timing and market-frontier gaps. The native hooks directly count both night overflow and DROP discards; their sum must equal the stock-flow depletion remainder for every product/day/seat. Thus this update checks actual discard units rather than leaving the old inferred remainder unclassified. Their marked value is a diagnostic inside the sales bridge, not extra cash added to sales again. Add the cash table’s spend/later/opponent terms to this production-to-sales row to recover final margin exactly.',
 'Daily best is a hindsight opportunity benchmark, not an executable price for an entire batch. Timing is actual revenue minus sold units times that branch’s own day-best; the frontier term records differences between its own day-best and the pair’s C. Prices are endogenous to both players. Opponent effects include its spending; this does not identify a specific sale as causing a particular opponent price change.',
 '## Per-product in-window detail',
 ]
 pr=read('2026-10-28-loss-after-rules-products.csv')
 rows=[]
 for r in s:
  for p in PRODUCTS:
   rs=[v for v in pr if v['window']==r['window'] and v['side']=='ours' and v['phase']=='in' and v['product']==p]
   av=lambda k:mean([float(v.get(k) or 0) for v in rs])
   rows.append([r['window'],p,fmt(av('delta_produced')),fmt(av('delta_sold')),signed(av('delta_revenue')),signed(av('delta_timing_gap')),signed(av('delta_frontier_gap'))])
 text+=[md(['Window','Product','Harvested Δ units','Sold Δ units','Revenue Δ','Timing Δ','Frontier Δ'],rows),
  '## Evidence and limits',
  'The SE averages the two seats within each of eight seeds before estimating dispersion. No test contents 10320–10324 are read. These seeds 20001–20008 are evaluation only. Worker count is four by Eugene’s explicit override of the handoff’s original two-worker limit. An owned wrapper invokes unchanged `run_full.one/verify` in fresh processes; protected player/training/encoding/vendor files are unchanged. Teacher code and weights remain on D:.',
  '- [Curve](2026-10-28-loss-after-rules-curve.csv), [paired monetary bridges](2026-10-28-loss-after-rules-paired.csv), [window summary](2026-10-28-loss-after-rules-summary.csv).\n- [Product and opponent detail](2026-10-28-loss-after-rules-products.csv), [spending](2026-10-28-loss-after-rules-spending.csv), [work](2026-10-28-loss-after-rules-work.csv), [planting](2026-10-28-loss-after-rules-planting.csv).\n- [Boundary assets](2026-10-28-loss-after-rules-assets.csv), [boundary crops](2026-10-28-loss-after-rules-boundary-crops.csv), [source hashes](2026-10-28-loss-after-rules-sources.csv), [checks](AFTER_RULES_LOSS_CHECKS.json).']
 (ROOT/'reports/2026-10-28-loss-curve-after-rules.md').write_text('\n\n'.join(text)+'\n',encoding='utf8')
 return curve

def selling_report():
 assert json.loads((RUN/'task1-reported.json').read_text())['passed']
 base=[c for c in cases() if c['source']['handover']==0];teachers=cases(True);assert len(base)==len(teachers)==16
 cohorts=[('ruled',base,False),('nflow-vs-ruled',base,True),('teacher',teachers,False),('nflow-vs-teacher',teachers,True)]
 sales=[];overflow=[];h23=[];early=[];work=[];farms=[]
 bands=[(6,12),(12,18),(18,24),(24,30)]
 for role,cs,opponent in cohorts:
  for c in cs:
   seat=c['source']['seat']^(1 if opponent else 0);ident=dict(role=role,seed=c['source']['seed'],seat=c['source']['seat'])
   for p in PRODUCTS:
    ds=[d for d in c['daily'] if d['seat']==seat];sold=sum(d['products'][p]['sold'] for d in ds);rev=sum(d['products'][p]['revenue'] for d in ds)
    benchmark=sum(d['products'][p]['sold']*max(x['products'][p]['best'] for x in c['daily'] if x['day']==d['day']) for d in ds)
    sales.append(dict(**ident,product=p,units=sold,revenue=rev,best_notional=benchmark,average_price=rev/sold if sold else None,capture=rev/benchmark if benchmark else None))
    for d in ds:overflow.append(dict(**ident,product=p,day=d['day'],night=d['products'][p]['night_discarded'],manual=d['products'][p]['manual_discarded']))
   for r in c['night_sales']:
    if r['seat']==seat:h23.append(dict(**ident,day=r['step']//24,product=r['product'],units=r['units'],revenue=r['revenue'],posted_notional=r['posted_price']*r['units'],next_notional=r['next_morning_price']*r['units'],best_notional=max(d['products'][r['product']]['best'] for d in c['daily'] if d['day']==r['step']//24)*r['units'],risk_units=r['units'] if r['forecast_excess']>0 else 0,price=r['price']))
   for e in c['evening']:
    if e['seat']==seat:early.append(dict(**ident,**{k:v for k,v in e.items() if k!='seat'}))
   if role not in ('ruled','teacher'):continue
   for lo,hi in bands:
    ds=[d for d in c['daily'] if d['seat']==seat and lo<=d['day']<hi];w=Counter()
    for d in ds:w.update(d['work'])
    for k in ['effective_WATER','effective_HARVEST','effective_FEED','effective_CARE','effective_FERTILIZE','effective_COLLECT_FERTILIZER','idle','ineffective_nonpass',*['plant_'+p for p in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')]]:work.append(dict(**ident,band=f'{lo}-{hi-1}',metric=k,count=w[k]))
    for k in ds[0]['farm']:farms.append(dict(**ident,band=f'{lo}-{hi-1}',kind=k,mean_dawn_tiles=mean([d['farm'][k] for d in ds])))
 for label,rows in [('sales',sales),('discarded',overflow),('hour23',h23),('early-scenario',early),('work',work),('farms',farms)]:table('2026-10-28-selling-'+label+'.csv',rows)
 aggregated=[]
 for p in PRODUCTS:
  for role,_,_ in cohorts:
   rs=[r for r in sales if r['product']==p and r['role']==role];q=sum(r['units'] for r in rs);rev=sum(r['revenue'] for r in rs);bench=sum(r['best_notional'] for r in rs)
   aggregated.append(dict(role=role,product=p,units=q/16,revenue=rev/16,price=rev/q if q else None,capture=rev/bench if bench else None))
 comp=[]
 for p in PRODUCTS:
  a=next(r for r in aggregated if r['product']==p and r['role']=='teacher');b=next(r for r in aggregated if r['product']==p and r['role']=='ruled');pa=a['price'] if a['price'] is not None else b['price'] or 0;pb=b['price'] if b['price'] is not None else pa
  volume=(a['units']-b['units'])*(pa+pb)/2;price=(pa-pb)*(a['units']+b['units'])/2
  assert abs(a['revenue']-b['revenue']-volume-price)<1e-7
  comp.append(dict(product=p,teacher_revenue_delta=a['revenue']-b['revenue'],volume_effect=volume,price_effect=price))
 table('2026-10-28-selling-summary.csv',aggregated);table('2026-10-28-selling-volume-price.csv',comp)
 ours_night=sum(r['night'] for r in overflow if r['role']=='ruled')/16;teacher_night=sum(r['night'] for r in overflow if r['role']=='teacher')/16
 text=['# Selling and work after rules — 2026-10-28',
 f"**The teacher earns {sum(r['teacher_revenue_delta'] for r in comp):+,.0f} more sale revenue/game in this sample: {sum(r['volume_effect'] for r in comp):+,.0f} from volume and {sum(r['price_effect'] for r in comp):+,.0f} from realized prices by the exact decomposition below.** The ruled agent still discards {ours_night:.2f} product units at night per game, versus {teacher_night:.2f} for the teacher.",
 'The tables below separate remaining native-measured overflow, sale volume, realized prices and work mix. Comparisons use seeds 20001–20008, both seats: 16 ruled-agent games and 16 teacher games against live fifth-nflow. They are full-game comparisons on each player’s own farm, not shared-prefix policy interventions. Daily-best capture is a hindsight/depth-limited benchmark.',
 md(['Product','Teacher revenue minus ours','Volume component','Price component'],[[r['product'],signed(r['teacher_revenue_delta']),signed(r['volume_effect']),signed(r['price_effect'])] for r in comp]),
 f"The largest realized-price gaps are milk and wool: the teacher sells fewer units of both, at higher average prices. Its late farm also holds fewer cows/sheep. These are different full-game farm and market paths, so the price component is not a measured gain from sale timing alone. The restricted earlier-delivery scenario below adds only {sum(e['spread_frozen_quote_revenue']-e['shifted_actual_revenue'] for e in early if e['role']=='ruled')/16:,.0f} coins/game before displaced work and market reactions; it supports a targeted test rather than explaining the whole revenue gap.",
 'The revenue decomposition is exact: ΔQ×(Pa+Pb)/2 + ΔP×(Qa+Qb)/2. Prices are unit-weighted over the full season. Price effects include different endogenous market paths and mix across days, not just tactical sale timing. When one side has zero units, the other side’s price is used only as an accounting convention; no missing observed price is invented in the table.',
 '## Units sold, actual prices and capture of daily best',
 md(['Product','Role','Units/game','Revenue/game','Actual average price','Revenue / daily-best notional'],[[r['product'],r['role'],fmt(r['units']),fmt(r['revenue']),fmt(r['price']),fmt(100*r['capture'])+'%' if r['capture'] is not None else '—'] for r in aggregated]),
 'Capture is total actual revenue divided by Σ(day units × that game’s maximum observed day price), including actual unit executions from both seats. It is not an unweighted mean of daily percentages. A large batch depresses the price while it sells, and first-unit quotes cannot be applied to all its units.',
 '## Goods still discarded',
 'Both DROP and night transfer losses are directly instrumented in native replay. For every product/day/seat, opening + harvested + bought − sold − consumed − closing must equal the measured two discard paths. Day 29 has no end-of-day refresh in the terminal game, so its night discard is absent, not an observed night of zero waste.',
 md(['Product','Ours night units/game','Teacher night units/game','Ours manual DROP','Teacher manual DROP'],[[p,*[fmt(sum(r[k] for r in overflow if r['role']==role and r['product']==p)/16) for role,k in [('ruled','night'),('teacher','night'),('ruled','manual'),('teacher','manual')]]] for p in PRODUCTS]),
 md(['Day','Ours night discarded units/game','Teacher night discarded units/game'],[[d,*[fmt(sum(r['night'] for r in overflow if r['role']==role and r['day']==d)/16) for role in ('ruled','teacher')]] for d in range(29)]),
 'The full product-by-day detail is in the discarded CSV; counts include both cohorts’ opponents too.',
 '## Hour-23 sales and next-morning prices',
 'These are actual final post-rule sales, priced per unit by the native matcher. Raw actions cannot identify exactly which units were added by overflow, since the rule also enlarges existing SELL orders. The “risk” column identifies sales on turns where the rule’s observable overflow forecast was positive; it is not a claim that every such sale was caused by the rule.',
 md(['Product','Hour23 units/game','Actual average price','Next-morning quote (unit weighted)','Own day-best (unit weighted)','Risk-turn share of units'],[[p,fmt(q/16),fmt(rev/q) if q else '—',fmt(nxt/q) if q else '—',fmt(bench/q) if q else '—',fmt(100*risk/q)+'%' if q else '—'] for p in PRODUCTS for rs in [[r for r in h23 if r['role']=='ruled' and r['product']==p]] for q,rev,nxt,bench,risk in [(sum(r['units'] for r in rs),sum(r['revenue'] for r in rs),sum(r['next_notional'] for r in rs),sum(r['best_notional'] for r in rs),sum(r['risk_units'] for r in rs))]]),
 '## Would earlier drop-off earn more?',
 'Existing games cannot establish the causal gain of a worker rule. We provide a frozen-trajectory scenario: at hour18 find goods in bags whose workers are within four moves of a shed tile, clip to that night’s sold quantity, and split the candidate units over hours18–22. Each chunk is repriced down the native sale-price curve at that recorded turn’s inventory. This assumes free earlier delivery and shed room, preserves observed market trajectories, ignores the displaced jobs, and does not enforce arrival times within those five turns. It is an optimistic diagnostic scenario, not an executable schedule, rigorous bound or prediction. Wheat/fertilizer may be needed for consumption and need extra caution.',
 md(['Product','Candidate units/game','Scenario revenue/game','Proportional actual night revenue','Scenario difference'],[[p,*[fmt(v/16) for v in (q,gross,actual,gross-actual)]] for p in PRODUCTS for rs in [[r for r in early if r['role']=='ruled' and r['product']==p]] for q,gross,actual in [(sum(r['candidate_units'] for r in rs),sum(r['spread_frozen_quote_revenue'] for r in rs),sum(r['shifted_actual_revenue'] for r in rs))]]),
 'A positive scenario gap supports testing earlier delivery; a negative or small gap weakens a blanket “sell earlier” rule. It does not say whether the lost worker jobs or the reacting opponent would erase the gap. Claude should test a worker-behaviour change separately; no new games were run for this task.',
 '## Effective work and farm mix',
 'Counts are per game in each requested band. Idle means PASS including implicit omitted-hand PASS; ineffective non-PASS is separate. Farm mix is mean tiles at the dawn of each day in the band, not cumulative purchases or all-turn exposure.',
 md(['Work metric','6–11 ours / teacher','12–17 ours / teacher','18–23 ours / teacher','24–29 ours / teacher'],[[metric,*[' / '.join(fmt(mean([r['count'] for r in work if r['metric']==metric and r['band']==band and r['role']==role])) for role in ('ruled','teacher')) for band in ('6-11','12-17','18-23','24-29')]] for metric in sorted({r['metric'] for r in work})]),
 md(['Farm type','6–11 ours / teacher','12–17 ours / teacher','18–23 ours / teacher','24–29 ours / teacher'],[[kind,*[' / '.join(fmt(mean([r['mean_dawn_tiles'] for r in farms if r['kind']==kind and r['band']==band and r['role']==role])) for role in ('ruled','teacher')) for band in ('6-11','12-17','18-23','24-29')]] for kind in sorted({r['kind'] for r in farms})]),
 '## Sources and checks',
 'Source raw hashes and worker/protected-code hashes are pinned in `runs/after-rules-20261028/profiles-inputs.json`. All cases use 720 recorded frames and native replay; cash, stock-flow and price/volume identities are checked. These eight evaluation seeds are never training labels. No test contents10320–10324, policy/encoder changes, pushes or submissions. Worker cap4 follows Eugene’s explicit override. Night-sales attribution and frozen-market scenario limitations above remain material.',
 '- [Sales](2026-10-28-selling-sales.csv), [summary](2026-10-28-selling-summary.csv), [volume/price identity](2026-10-28-selling-volume-price.csv).\n- [Discarded by product/day](2026-10-28-selling-discarded.csv), [hour23 executions](2026-10-28-selling-hour23.csv), [earlier scenario](2026-10-28-selling-early-scenario.csv).\n- [Work](2026-10-28-selling-work.csv), [farm mix](2026-10-28-selling-farms.csv), [checks](AFTER_RULES_SELLING_CHECKS.json).']
 (ROOT/'reports/2026-10-28-selling-and-work.md').write_text('\n\n'.join(text)+'\n',encoding='utf8')
 proof=dict(passed=True,own_rule_games=16,teacher_games=16,native_tables_per_game=6,direct_discard_hooks=True,all_product_daily_stock_flows_exact=True,volume_price_identity_exact=True,new_games_for_task2=0,test_contents_read=0,source_worker_sha256=json.loads((LOCAL/'profiles-inputs.json').read_text())['worker_sha256'])
 from after_rules_extract import save
 save(ROOT/'reports/AFTER_RULES_SELLING_CHECKS.json',proof)
 return proof
if __name__=='__main__':
 import sys
 print(json.dumps(loss_report() if sys.argv[1]=='loss' else selling_report(),separators=(',',':')))
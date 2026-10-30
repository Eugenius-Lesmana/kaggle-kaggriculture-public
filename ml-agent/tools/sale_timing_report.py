"""Aggregate verified timing cells and paired-seed uncertainty; no games or training."""
from collections import defaultdict
from pathlib import Path
import csv,json,math,statistics
import sale_timing_bound as T
ROOT=T.ROOT;RUN=T.RUN

def write(name,rows):
 p=ROOT/'reports'/name
 with p.open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def md(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |',*['| '+' | '.join(str(x) for x in r)+' |' for r in rows]])
def estimate(rows,key):
 sums=defaultdict(float)
 for r in rows:sums[r['seed'],r['seat']]+=float(r[key] or 0)
 values=[(sums[s,0]+sums[s,1])/2 for s in range(20001,20009)]
 return statistics.mean(values),statistics.stdev(values)/math.sqrt(8)
def main():
 cfg=json.loads((T.LOCAL/'timing-inputs.json').read_text());cases=[json.loads((RUN/f"{j['seed']}-seat{j['seat']}.json").read_text()) for j in cfg['jobs']]
 assert len(cases)==16 and all(c['passed'] and c['worker_sha256']==cfg['worker_sha256'] and len(c['native_rows'])==6 for c in cases)
 rows=[r for c in cases for r in c['rows']];assert len(rows)==4320 and all(r['free_oracle']>=r['stock_oracle']>=r['actual_revenue'] for r in rows)
 write('2026-10-28-sale-timing-daily.csv',rows);write('2026-10-28-sale-timing-schedules.csv',[r for c in cases for r in c['schedules']]);summary=[]
 for p in (*T.PRODUCTS,'ALL'):
  for band in ('ALL','0-5','6-11','12-17','18-23','24-29'):
   rs=[r for r in rows if (p=='ALL' or r['product']==p) and (band=='ALL' or r['band']==band)]
   a=estimate(rs,'actual_revenue')[0];v,se=estimate(rs,'stock_gain');f,fse=estimate(rs,'free_gain');m,mse=estimate(rs,'matched_gain');q=sum(r['units'] for r in rs);covered=sum(r['matched_units'] for r in rs)
   summary.append(dict(product=p,band=band,actual_revenue=a,stock_gain=v,stock_seed_se=se,free_gain=f,free_seed_se=fse,matched_gain_on_covered_cells=m,matched_seed_se=mse,matched_unit_coverage=covered/q if q else None,units=q/16,own_capture=sum(r['actual_revenue'] for r in rs)/sum(r['units']*r['day_best'] for r in rs) if q else None))
 write('2026-10-28-sale-timing-summary.csv',summary)
 total=next(r for r in summary if r['product']=='ALL' and r['band']=='ALL');products=[r for r in summary if r['product']!='ALL' and r['band']=='ALL'];bands=[r for r in summary if r['product']=='ALL' and r['band']!='ALL'];signed=lambda x:f'{x:+,.1f}';pct=lambda x:f'{100*x:.1f}%' if x is not None else 'NA'
 text=['# Sale timing on recorded markets — 2026-10-28',f"**The recorded-market timing oracle adds {total['stock_gain']:+,.0f} sale coins/game (paired-seed SE {total['stock_seed_se']:,.0f}) with recorded shed availability. Giving it the whole day’s goods from dawn raises the ceiling to {total['free_gain']:+,.0f}.** These are conditional hindsight revenue benchmarks, not measured full-game margin improvements.",
 'Uses the 16 existing ruled-P4 games in `runs/nflow-p4-ovf-end-ew`, seeds20001–20008, both seats. Each product/day retains exactly its recorded sold quantity. No policy games, training or protected code changes.',
 '## Benchmark definition and scope',
 'Start-of-turn inventory is reset to that turn’s recorded market. Within a turn we use the actual engine price function and per-unit simultaneous quoting: a sale at price1 does NOT increase supply; purchases reduce supply; both seats quote before either commits. Fifth-nflow’s recorded order slots and executed quantities, and our recorded product purchases, are fixed. Counterfactual prices do not change fills, solvency, worker behaviour or the next turn’s recorded inventory. Thus this is a recorded-path/recorded-fill benchmark, not a self-consistent counterfactual season with opponent cash and inventory feedback.',
 'The oracle chooses a turn, order slot and quantity, with at most one positive SELL per product/turn, matching the current market head. We verify that the baseline also has at most one. Products are optimized independently, so summed schedules may conflict with the joint10-order limit. Day29 has23 actionable turns. Costs, purchases, terminal margin and opponent gains are not added to our sale-revenue gain.',
 'The stock-aware variant constrains cumulative sales using recorded post-worker/pre-market shed stock and unchanged purchases/flows. It cannot sell goods before their recorded arrival in the shed. Intermediate worker-order effects, changed discard/capacity outcomes and cross-product conflicts are not simulated, so its schedule is still an optimistic conditional benchmark. The free-stock ceiling additionally grants the entire fixed daily quantity from dawn. Dynamic programming finds the exact optimum in each stated model, including nonlinear per-unit depth and floor effects.',
 '## Per product, coins per game',
 md(['Product','Actual sales','Stock-aware timing gain','Seed SE','Free-stock gain','Match fifth gain on covered cells','Covered units'],[[r['product'],f"{r['actual_revenue']:,.1f}",signed(r['stock_gain']),f"{r['stock_seed_se']:,.1f}",signed(r['free_gain']),signed(r['matched_gain_on_covered_cells']),pct(r['matched_unit_coverage'])] for r in products]),
 '## Day bands, coins per game',
 md(['Days','Actual sales','Stock-aware timing gain','Seed SE','Free-stock gain','Match fifth gain on covered cells','Covered units'],[[r['band'],f"{r['actual_revenue']:,.1f}",signed(r['stock_gain']),f"{r['stock_seed_se']:,.1f}",signed(r['free_gain']),signed(r['matched_gain_on_covered_cells']),pct(r['matched_unit_coverage'])] for r in bands]),
 '## Matching fifth-nflow’s capture',
 f"Matching its same-game/product/day capture changes revenue by {total['matched_gain_on_covered_cells']:+,.0f}/game on cells covering {pct(total['matched_unit_coverage'])} of our sold units. Where it sold nothing, capture is undefined: no gain is imputed for those cells. The reported gain is only the subtotal on covered cells, not an estimate for uncovered goods.",
 'For each product/day, the common hindsight day-best includes both seats’ actual unit executions and recorded displayed quotes. Capture = actual revenue/(units×day-best). Matching fifth’s capture therefore gives our units×its average realized unit price on that same market/day. Negative gains are retained. This arithmetic transfer does not respect the depth cost of our batch size and can exceed an executable timing result; it is not another feasible oracle schedule.',
 '## Interpretation',
 f"A learned selling experiment is worth testing first on wool, milk and strawberry: they account for {100*sum(r['stock_gain'] for r in products if r['product'] in ('WOOL','MILK','STRAWBERRY'))/total['stock_gain']:.1f}% of this model’s stock-aware headroom. Days18–29 account for {100*sum(r['stock_gain'] for r in bands if r['band'] in ('18-23','24-29'))/total['stock_gain']:.1f}%. These priorities come from the benchmark; they are not expected realized gains.",
 f"The learned seller’s timing opportunity on unchanged recorded deliveries is bounded by this model’s {total['stock_gain']:,.0f} coins/game headroom; the larger free-stock number additionally requires earlier availability/delivery assumptions. These quantities size a selling-policy experiment; they do not establish that a learned policy will attain the oracle, or that market reactions and work costs preserve its gain. Realized-price differences in the earlier teacher comparison include product mix and different market paths, so that entire gap cannot be called timing loss.",
 '## Verification and evidence',
 'All16 original action traces are replayed natively (six tables each). Every product/day’s original unit count and revenue is reconstructed exactly with the market primitive, including floor1 supply suppression. Every oracle path is backtracked: unit totals, availability constraints, path revenue and baseline dominance are checked. Small independent exhaustive-search and native-auction tests cover both seats, purchases and floor prices. SEs average both seats within each of eight seeds; they do not treat16 games as16 independent samples.',
 '[Daily product cells](2026-10-28-sale-timing-daily.csv), [product/band summary](2026-10-28-sale-timing-summary.csv), [stock-aware schedules](2026-10-28-sale-timing-schedules.csv), [checks](SALE_TIMING_BOUND_CHECKS.json).']
 (ROOT/'reports/2026-10-28-sale-timing-bound.md').write_text('\n\n'.join(text)+'\n',encoding='utf8')
 proof=dict(passed=True,source_games=16,independent_seeds=8,product_day_cells=4320,source_worker_sha256=cfg['worker_sha256'],native_tables_per_game=6,independent_native_and_bruteforce_checks=78,source_inputs=cfg['jobs'],baseline_revenue_and_units_exact=True,oracle_backtracking_checked=True,recorded_turn_inventory_reset=True,opponent_executed_quantities_fixed=True,floor1_supply_rule_checked=True,new_policy_games=0,test_contents_read=0,summary=total)
 T.save(ROOT/'reports/SALE_TIMING_BOUND_CHECKS.json',proof);print(json.dumps(proof,separators=(',',':')))
if __name__=='__main__':main()
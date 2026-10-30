"""Native replay-only loss profiles. No policy is instantiated and no training arrays are written."""
from collections import Counter,defaultdict
import contextlib,copy,hashlib,io,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
DATA=Path('kaggriculture-ml-data');RUN=DATA/'runs/after-rules-20261028';LOCAL=ROOT/'.cache/after-rules'
PROFILES=RUN/'profiles'
PRODUCTS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER')
MOVES={'NORTH','SOUTH','EAST','WEST'}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);tmp=p.with_suffix('.tmp')
 for attempt in range(10):
  try:tmp.write_text(json.dumps(v,separators=(',',':')),encoding='utf8');tmp.replace(p);return
  except PermissionError:
   if attempt==9:raise
   time.sleep(.1)
def key(j):return f"h{j['handover']}-{j['seed']}-seat{j['seat']}"
def held(o):return {k:o['private']['shed'].get(k,0)+sum(b.get(k,0) for b in o['private']['inventories']) for k in PRODUCTS}
def extract(j):
 assert os.environ.get('PYTHONHASHSEED')=='0' and j['seed'] in range(20001,20009) and j['seed'] not in range(10320,10325)
 cfg=json.loads((LOCAL/'profiles-inputs.json').read_text(encoding='utf8'));assert sha(__file__)==cfg['worker_sha256']
 assert json.loads((RUN/'games-complete.json').read_text())['passed'],'Task1 game queue must finish before native profiles'
 for p,h in cfg['protected_hashes'].items():assert sha(ROOT/p)==h
 target=PROFILES/(key(j)+'.json')
 if target.exists():
  v=json.loads(target.read_text(encoding='utf8'));assert v['source']==j and v['worker_sha256']==cfg['worker_sha256'];return key(j)
 begun=time.time();assert sha(DATA/j['file'])==j['sha256']
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  from kagml import replay_tables as RT,board_features as B
  from kagml.work_data import load_replay
  from build_turn_dataset import job_value
 rep=load_replay(DATA/j['file']);assert len(rep['steps'])==720 and rep['info']['seed']==j['seed']
 assert [s['status'] for s in rep['steps'][-1]]==['DONE','DONE']
 days=[[[Counter() for _ in PRODUCTS] for _ in range(30)] for _ in (0,1)]
 work=defaultdict(Counter);current={};original=RT.ORIGINAL['_apply_unit_action'];interpreter=RT.K.interpreter;original_night=RT.K._drop_inventories_to_shed
 def drop_at_night(private,capacity):
  seat=next(s for s in (0,1) if current['states'][s].observation.private is private);day=current['step']//24
  before=held(dict(private=private));result=original_night(private,capacity);after=held(dict(private=private))
  for i,p in enumerate(PRODUCTS):days[seat][day][i]['night_discarded']+=before[p]-after[p]
  return result
 RT.K._drop_inventories_to_shed=drop_at_night
 def hook(farm,private,unit,action,*args,**kwargs):
  seat=next(s for s in (0,1) if current['states'][s].observation.private is private);step=current['step'];day=step//24
  before=RT.snapshot(farm,private,unit);old=held(dict(private=private));obs=rep['steps'][step][seat]['observation'];op=action[0]
  value=job_value(obs,unit,action) if unit<len(B.positions(obs['farms'][seat])) else 0
  result=original(farm,private,unit,action,*args,**kwargs)
  effect=before!=RT.snapshot(farm,private,unit)
  if before is not None and effect:
   work[seat,day]['job_value']+=value
   work[seat,day]['job_value_'+op]+=value
   now=held(dict(private=private))
   for i,p in enumerate(PRODUCTS):
    if op in ('HARVEST','COLLECT_FERTILIZER'):days[seat][day][i]['produced']+=max(0,now[p]-old[p])
    if op in ('FEED','FERTILIZE'):days[seat][day][i]['consumed']+=max(0,old[p]-now[p])
    if op=='DROP':days[seat][day][i]['manual_discarded']+=max(0,old[p]-now[p])
  return result
 def intercept(states,env):
  current.update(states=states,step=int(states[0].observation.step));return interpreter(states,env)
 RT.ORIGINAL['_apply_unit_action']=hook;RT.K.interpreter=intercept
 banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
 meta=dict(episode=940000000000+j['handover']*1000000+j['seed']*10+j['seat'],created='',**{f'{k}_{s}':banks[s] if k=='reward' else -1 for s in (0,1) for k in ('reward','sub','team','rating')})
 try:tables,audit=RT.replay(rep,meta,'split-weeds');assert tables is not None,audit
 finally:RT.ORIGINAL['_apply_unit_action']=original;RT.K._apply_unit_action=original;RT.K.interpreter=interpreter;RT.K._drop_inventories_to_shed=original_night
 spending=defaultdict(Counter)
 for r in tables['unit_actions']:
  if not r['exists']:continue
  s,d=r['seat'],r['step']//24;w=work[s,d];op=json.loads(r['effective_command'])[0]
  w['slots']+=1;w['idle']+=op=='PASS';w['ineffective_nonpass']+=op!='PASS' and not r['took_effect']
  w['moves']+=op in MOVES and r['took_effect'];w['jobs']+=op not in MOVES and op!='PASS' and r['took_effect']
  if r['took_effect']:w['effective_'+op]+=1
  if r['cash_delta']<0:spending[s,d]['construction']-=r['cash_delta']
 for r in tables['market_orders']:
  s,d=r['seat'],r['step']//24;cmd=json.loads(r['command']);op=cmd[0] if cmd else ''
  if r['cash_delta']<0:
   bucket=cmd[1] if op=='BUY_PRODUCT' else op
   spending[s,d][bucket]-=r['cash_delta']
  if op=='BUY_PRODUCT' and cmd[1] in PRODUCTS:days[s][d][PRODUCTS.index(cmd[1])]['bought']+=r['units']
  if op=='BUY_SEED':work[s,d]['seed_bought_'+cmd[1]]+=r['units']
  if op=='BUY_ANIMAL':work[s,d]['animal_bought_'+cmd[1]]+=r['units']
 for r in tables['sales']:
  z=days[r['seat']][r['step']//24][PRODUCTS.index(r['product'])];z['sold']+=r['units'];z['revenue']+=r['revenue'];z['best_execution']=max(z['best_execution'],r['price'])
 for r in tables['unit_actions']:
  if r['exists'] and r['took_effect']:
   cmd=json.loads(r['effective_command'])
   if cmd[0]=='PLANT':
    s,d=r['seat'],r['step']//24;crop=cmd[1];work[s,d]['plant_'+crop]+=1
    work[s,d]['ripenable_'+crop]+=(d+int(B.CROPS[crop]['first_yield_day']))*24<=718
 night_sales=[]
 for r in tables['sales']:
  if r['step']%24==23:
   row=dict(r);step=r['step'];obs=rep['steps'][step][r['seat']]['observation'];p=r['product'];private=obs['private'];risk=max(0,sum(private['shed'].values())+sum(sum(b.values()) for b in private['inventories'])+len(B.positions(obs['farms'][r['seat']]))-100);night_sales.append(dict(row,forecast_excess=risk,posted_price=obs['market']['prices'][p],next_morning_price=rep['steps'][step+1][0]['observation']['market']['prices'][p]))
 daily=[];snapshots={};prefixes={};digest=hashlib.sha256()
 for step,frame in enumerate(rep['steps']):
  clean=[{k:({a:b for a,b in v.items() if a!='remainingOverageTime'} if k=='observation' else v) for k,v in s.items()} for s in frame]
  digest.update(json.dumps(clean,sort_keys=True,separators=(',',':')).encode())
  if step in (144,288,528,672):prefixes[str(step//24)]=digest.hexdigest()
 for d in range(30):
  close=min((d+1)*24,719)
  best={p:max([rep['steps'][t][0]['observation']['market']['prices'][p] for t in range(d*24,close)]+[r['price'] for r in tables['sales'] if r['product']==p and r['step']//24==d]) for p in PRODUCTS}
  for s in (0,1):
   a=held(rep['steps'][d*24][s]['observation']);b=held(rep['steps'][close][s]['observation']);products={}
   for i,p in enumerate(PRODUCTS):
    z=days[s][d][i];products[p]=dict(produced=z['produced'],consumed=z['consumed'],bought=z['bought'],sold=z['sold'],revenue=z['revenue'],opening=a[p],closing=b[p],best=max(best[p],z['best_execution']),night_discarded=z['night_discarded'],manual_discarded=z['manual_discarded'])
    flow=a[p]+z['produced']+z['bought']-z['sold']-z['consumed']-b[p]
    assert flow==z['night_discarded']+z['manual_discarded'],('Unexplained stock flow',j,s,d,p,flow,z)
   opening_money=rep['steps'][d*24][s]['observation']['farms'][s]['money'];closing_money=rep['steps'][close][s]['observation']['farms'][s]['money']
   revenue=sum(r['revenue'] for r in products.values());spend=sum(spending[s,d].values())
   assert abs((closing_money-opening_money)-(revenue-spend))<1e-8,(j,s,d,'cash')
   farm=rep['steps'][d*24][s]['observation']['farms'][s];ts=[t for line in farm['tiles'] for t in line if isinstance(t,dict)]
   occupancy={'crop_'+p:sum(t.get('crop')==p for t in ts) for p in B.CROP_NAMES};occupancy.update({'animal_'+p:sum(t.get('animal')==p for t in ts) for p in B.ANIMAL_NAMES})
   daily.append(dict(seat=s,day=d,farm=occupancy,products=products,spending=dict(spending[s,d]),work=dict(work[s,d]),opening_money=opening_money,closing_money=closing_money,revenue=revenue,spend=spend))
 for boundary in (6,12,22,28,30):
  step=min(boundary*24,719);snapshots[str(boundary)]={}
  for s in (0,1):
   obs=rep['steps'][step][s]['observation'];farm=obs['farms'][s];crops=[];animals=Counter();yield_units=Counter();structures=Counter()
   for y,line in enumerate(farm['tiles']):
    for x,tile in enumerate(line):
     if not isinstance(tile,dict):continue
     if tile['kind']=='PLANT':
      crop=tile['crop'];delay=max(0,tile['planted_day']+B.CROPS[crop]['first_yield_day']-obs['day'])
      crops.append(dict(x=x,y=y,crop=crop,days_to_ripen=delay,yield_units=tile.get('yield_units',0),viable=boundary<30 and delay<=29-obs['day'],seed_cost=B.CROPS[crop]['seed'],first_yield_units=1 if B.CROPS[crop]['ongoing'] else B.CROPS[crop]['max_yield']))
     if tile['kind'] in ('COOP','PASTURE'):structures[tile['kind']]+=1
     if tile.get('animal'):animals[tile['animal']]+=1;yield_units[B.ANIMALS[tile['animal']]['product']]+=tile.get('yield_units',0)
   snapshots[str(boundary)][str(s)]=dict(money=farm['money'],held=held(obs),seeds=obs['private']['seeds'],stored_animals={a:obs['private']['shed'].get(a,0)+sum(b.get(a,0) for b in obs['private']['inventories']) for a in B.ANIMALS},crops=crops,animals=dict(animals),animal_yield=dict(yield_units),structures=dict(structures),land=farm['unlocked_quadrants'])
 evening=[]
 for day in range(29):
  for seat in (0,1):
   obs=rep['steps'][day*24+18][seat]['observation'];farm=obs['farms'][seat];eligible=Counter();travel=0
   for pos,bag in zip(B.positions(farm),obs['private']['inventories']):
    dist=min(abs(pos[0]-x)+abs(pos[1]-y) for x,y in ((4,4),(5,4),(4,5),(5,5)))
    if dist<=4 and bag:
     travel+=dist+1
     for p in PRODUCTS:eligible[p]+=bag.get(p,0)
   for p in PRODUCTS:
    sold=sum(r['units'] for r in night_sales if r['step']//24==day and r['seat']==seat and r['product']==p)
    revenue=sum(r['revenue'] for r in night_sales if r['step']//24==day and r['seat']==seat and r['product']==p)
    quotes=[rep['steps'][day*24+h][0]['observation']['market']['prices'][p] for h in range(18,23)]
    eligible_n=min(sold,eligible[p]);per_turn=[eligible_n//5+(i<eligible_n%5) for i in range(5)]
    gross=0
    for i,h in enumerate(range(18,23)):
     inv=rep['steps'][day*24+h][0]['observation']['market']['inventory'][p]
     for unit in range(per_turn[i]):gross+=RT.K.market_price(p,inv+unit,rep['steps'][day*24+h][0]['observation']['market'].get('params'))
    evening.append(dict(day=day,seat=seat,product=p,hour23_units=sold,hour23_revenue=revenue,within_reach_bag_units_at18=eligible[p],redirected_worker_turns=travel,candidate_units=eligible_n,earlier_best_quote=max(quotes),spread_frozen_quote_revenue=gross,shifted_actual_revenue=revenue*eligible_n/sold if sold else 0))
 value=dict(source=j,passed=True,night_sales=night_sales,evening=evening,worker_sha256=cfg['worker_sha256'],native_audit=audit,native_rows={k:len(v) for k,v in tables.items()},prefixes=prefixes,daily=daily,snapshots=snapshots,animal_costs={a:v['cost'] for a,v in B.ANIMALS.items()},seconds=time.time()-begun,new_games=0,test_contents_read=0)
 save(target,value);return key(j)
if __name__=='__main__':print(extract(json.loads(Path(sys.argv[1]).read_text(encoding='utf8'))))
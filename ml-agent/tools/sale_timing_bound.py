"""Recorded-flow intraday selling oracles. No policy games, training or protected edits."""
from collections import Counter,defaultdict
from concurrent.futures import ProcessPoolExecutor,as_completed
from functools import lru_cache
from itertools import product
from pathlib import Path
from types import SimpleNamespace as NS
import contextlib,copy,csv,gzip,hashlib,io,json,os,sys,time
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
DATA=Path('kaggriculture-ml-data');RUN=DATA/'runs/after-rules-20261028/sale-timing';LOCAL=ROOT/'.cache/after-rules'
PRODUCTS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER');NEG=-(1<<60)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,separators=(',',':')),encoding='utf8');q.replace(p)
def engine():
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  from kagml import replay_tables as RT
 return RT

def transition(inventory,sell,buy,n,sign,price):
 revenue=0
 for u in range(max(sell,buy,n)):
  quote=price(inventory);delta=int(u<sell and quote>1)-int(u<buy)
  if u<n:delta+=int(quote>1) if sign>0 else -1
  if u<sell:revenue+=quote
  inventory+=delta
 return revenue,inventory

def curve(inventory,Q,n,sign,price):
 values=[0]
 for u in range(Q):
  quote=price(inventory);values.append(values[-1]+quote)
  inventory+=int(quote>1)+(int(quote>1) if sign>0 else -1 if sign<0 else 0)*(u<n)
 return np.array(values,np.int64)

def solve(turns,Q,stock=True):
 if not Q:return 0,[]
 j=np.arange(Q+1);X=j[:,None];Y=j[None,:];diff=np.maximum(Y-X,0);dp=np.full(Q+1,NEG,np.int64);dp[0]=0;backs=[]
 for t in turns:
  if stock:dp[j>t['before_available']]=NEG
  best=np.full(Q+1,NEG,np.int64);back=np.zeros(Q+1,np.int32);chosen=np.zeros(Q+1,np.int32)
  # Equal availability groups share the best curve, preserving its winning order slot per quantity.
  groups=defaultdict(list)
  for c in t['candidates']:groups[min(Q,c['available']) if stock else Q].append(c)
  for cap,cs in groups.items():
   allcurves=np.array([c['curve'] for c in cs]);which=allcurves.argmax(0);payoff=allcurves.max(0)
   values=dp[:,None]+payoff[diff];values=np.where((Y>=X)&(Y<=cap)&(dp[:,None]>NEG//2),values,NEG)
   prev=values.argmax(0);v=values.max(0);improve=v>best
   best[improve]=v[improve];back[improve]=prev[improve]
   chosen[improve]=np.array([cs[int(which[y-prev[y]])]['slot'] for y in j[improve]])
  dp=best;backs.append((back,chosen))
 assert dp[Q]>=Q,('No feasible fixed-total schedule',Q)
 y=Q;schedule=[]
 for t,(back,chosen) in zip(reversed(turns),reversed(backs)):
  x=int(back[y]);q=y-x;slot=int(chosen[y]);c=next(c for c in t['candidates'] if c['slot']==slot)
  if q:schedule.append(dict(step=t['step'],slot=slot,units=q,revenue=int(c['curve'][q])))
  y=x
 assert y==0 and sum(r['units'] for r in schedule)==Q and sum(r['revenue'] for r in schedule)==int(dp[Q])
 return int(dp[Q]),list(reversed(schedule))

def check():
 RT=engine();K=RT.K;tests=0
 for Q in range(1,6):
  turns=[dict(step=0,before_available=2,candidates=[dict(slot=0,available=2,curve=np.arange(Q+1)*3)]),dict(step=1,before_available=Q,candidates=[dict(slot=0,available=Q,curve=np.cumsum([0]+[max(1,6-u) for u in range(Q)])),dict(slot=1,available=Q,curve=np.arange(Q+1)*4)])]
  for stock in (True,False):
   brute=max(turns[0]['candidates'][0]['curve'][q]+max(c['curve'][Q-q] for c in turns[1]['candidates']) for q in range(Q+1) if not stock or q<=2)
   assert solve(turns,Q,stock)[0]==brute;tests+=1
 for seat in (0,1):
  for sign in (-1,0,1):
   p='WHEAT' if sign<0 else 'MILK';hi=400
   while K.market_price(p,hi)>1:hi*=2
   for start in (190,hi):
    for q in (1,3,9):
     n=4 if sign else 0;m=K._new_market();m['inventory'][p]=start;K._refresh_prices(m);farms=[dict(money=10**9) for _ in (0,1)];priv=[dict(shed={}) for _ in (0,1)];priv[seat]['shed'][p]=q
     if sign>0:priv[1-seat]['shed'][p]=n
     states=[NS(observation=NS(market=m,farms=farms,private=priv[z]),action={'market':[]}) for z in (0,1)];states[seat].action['market']=[['SELL',p,q]]
     if sign:states[1-seat].action['market']=[['SELL' if sign>0 else 'BUY_PRODUCT',p,n]]
     K._process_market(states,NS(configuration=NS(boardSize=10,maxMarketOrdersPerTurn=10,shedCapacity=10000)))
     price=lambda i:K.market_price(p,i);expected,end=transition(start,q,0,n,sign,price)
     assert farms[seat]['money']-10**9==expected and m['inventory'][p]==end and curve(start,q,n,sign,price)[q]==expected;tests+=1
 print(json.dumps(dict(passed=True,independent_bruteforce_and_native_checks=tests,new_policy_games=0)))

def case(j):
 cfg=json.loads((LOCAL/'timing-inputs.json').read_text());assert sha(__file__)==cfg['worker_sha256'] and sha(DATA/j['file'])==j['sha256']
 out=RUN/f"{j['seed']}-seat{j['seat']}.json"
 if out.exists():
  x=json.loads(out.read_text());assert x['source']==j and x['worker_sha256']==cfg['worker_sha256'];return str(out)
 RT=engine();K=RT.K;snap={};original=K._process_market
 def capture(states,env):
  t=int(states[0].observation.step);m=states[0].observation.market;snap[t]=dict(before=dict(m['inventory']),shed=[dict(s.observation.private['shed']) for s in states],params=copy.deepcopy(m.get('params')))
  result=original(states,env);snap[t]['after']=dict(m['inventory']);return result
 K._process_market=capture
 with gzip.open(DATA/j['file'],'rt',encoding='utf8') as f:rep=json.load(f)
 banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']];meta=dict(episode=960000000000+j['seed']*10+j['seat'],created='',**{f'{k}_{s}':banks[s] if k=='reward' else -1 for s in (0,1) for k in ('reward','sub','team','rating')})
 try:tables,audit=RT.replay(rep,meta,'split-weeds');assert tables is not None,audit
 finally:K._process_market=original
 assert len(snap)==719
 orders={(r['step'],r['seat'],r['order_index']):(json.loads(r['command']),r['units']) for r in tables['market_orders']};sold=Counter();revenue=Counter();executed_best=defaultdict(int)
 for r in tables['sales']:
  key=(r['step']//24,r['seat'],r['product']);sold[key]+=r['units'];revenue[key]+=r['revenue'];executed_best[r['step']//24,r['product']]=max(executed_best[r['step']//24,r['product']],r['price'])
 rows=[];schedules=[]
 for d in range(30):
  ts=range(d*24,min((d+1)*24,719))
  for p in PRODUCTS:
   Q=sold[d,j['seat'],p];R=revenue[d,j['seat'],p];oppq=sold[d,1-j['seat'],p];oppr=revenue[d,1-j['seat'],p];best=max([executed_best[d,p]]+[rep['steps'][t][0]['observation']['market']['prices'][p] for t in ts]);turns=[];actual_x=0;actual_R=0
   for t in ts:
    before=snap[t]['before'][p];base=before;actual_base=before;candidates=[];buy_before=0;turn_x=actual_x;actual_turn_R=0;sale_orders=0
    price=lru_cache(None)(lambda i:K.market_price(p,i,snap[t]['params']))
    for slot in range(int(rep['configuration'].get('maxMarketOrdersPerTurn',10))):
     a,an=orders.get((t,j['seat'],slot),([],0));b,bn=orders.get((t,1-j['seat'],slot),([],0));ownbuy=an if a[:2]==['BUY_PRODUCT',p] else 0;ownsell=an if a[:2]==['SELL',p] else 0;sign=1 if b[:2]==['SELL',p] else -1 if b[:2]==['BUY_PRODUCT',p] else 0;n=bn if sign else 0
     r,actual_base=transition(actual_base,ownsell,ownbuy,n,sign,price);actual_turn_R+=r;actual_x+=ownsell;sale_orders+=ownsell>0
     if not ownbuy:candidates.append(dict(slot=slot,available=int(snap[t]['shed'][j['seat']].get(p,0))+turn_x+buy_before,curve=curve(base,Q,n,sign,price)))
     _,base=transition(base,0,ownbuy,n,sign,price);buy_before+=ownbuy
    assert sale_orders<=1,'Timing model requires at most one positive SELL per product/turn, as emitted by this market head'
    assert actual_base==snap[t]['after'][p],(j,t,p,actual_base,snap[t]['after'][p])
    actual_R+=actual_turn_R;turns.append(dict(step=t,before_available=int(snap[t]['shed'][j['seat']].get(p,0))+turn_x,candidates=candidates))
   assert actual_x==Q and actual_R==R,(j,d,p,actual_x,Q,actual_R,R)
   optimal,schedule=solve(turns,Q,True);ceiling,_=solve(turns,Q,False)
   assert ceiling>=optimal>=R,(j,d,p,ceiling,optimal,R)
   row=dict(seed=j['seed'],seat=j['seat'],day=d,band=f'{d//6*6}-{d//6*6+5}',product=p,units=Q,actual_revenue=R,stock_oracle=optimal,stock_gain=optimal-R,free_oracle=ceiling,free_gain=ceiling-R,opponent_units=oppq,opponent_revenue=oppr,day_best=best,capture=R/(Q*best) if Q else None,opponent_capture=oppr/(oppq*best) if oppq else None,matched_gain=Q*oppr/oppq-R if oppq and Q else None,matched_units=Q if oppq else 0)
   rows.append(row);schedules += [dict(seed=j['seed'],seat=j['seat'],day=d,product=p,**s) for s in schedule]
 save(out,dict(passed=True,source=j,worker_sha256=cfg['worker_sha256'],rows=rows,schedules=schedules,native_rows={k:len(v) for k,v in tables.items()},baseline_revenue_exact=True,new_policy_games=0,test_contents_read=0));return str(out)

def prepare():
 jobs=[j for j in json.loads((LOCAL/'profiles-inputs.json').read_text())['jobs'] if j['handover']==0];assert len(jobs)==16
 cfg=dict(jobs=jobs,worker_sha256=sha(__file__),max_analysis_processes=4,new_policy_games=0,model='recorded start-of-turn inventory; native floor/lockstep; fixed opponent executed order quantities; daily quantity fixed; one SELL/product/turn')
 p=LOCAL/'timing-inputs.json'
 if p.exists():assert json.loads(p.read_text())==cfg
 else:save(p,cfg)
 return cfg
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 if sys.argv[1]=='check':check()
 elif sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='run':
  cfg=prepare();RUN.mkdir(parents=True,exist_ok=True)
  with ProcessPoolExecutor(max_workers=4) as pool:
   for f in as_completed([pool.submit(case,j) for j in cfg['jobs']]):f.result()
  save(RUN/'computed.json',dict(passed=True,cases=16,worker_sha256=cfg['worker_sha256']))
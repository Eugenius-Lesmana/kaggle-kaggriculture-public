"""TRAIN-only recorded-market tuning; native auction, fixed future market/worker paths."""
from pathlib import Path
from collections import Counter
from types import SimpleNamespace as NS
from concurrent.futures import ProcessPoolExecutor,as_completed
import contextlib,copy,csv,gzip,hashlib,io,json,os,sys,time
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
DATA=Path('kaggriculture-ml-data');RUN=DATA/'runs/next-20261028/selling-train';LOCAL=ROOT/'.cache/next'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):
 p.parent.mkdir(parents=True,exist_ok=True);q=p.with_suffix('.tmp');q.write_text(json.dumps(x,separators=(',',':')),encoding='utf8');q.replace(p)
def lib():
 with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
  from kagml import replay_tables as RT
  from kagml.net_player import NetPlayer
 return RT,NetPlayer

def prepare():
 with (ROOT/'manifests/plan-seeds.csv').open(encoding='utf8',newline='') as f:seeds=[int(r['seed']) for r in csv.DictReader(f) if r['split']=='train']
 parents=json.loads((ROOT/'.cache/after-rules/endgame-inputs.json').read_text())['parents'];jobs=[dict(seed=s,seat=t,**parents[f'{s}-{t}']) for s in seeds for t in (0,1)];assert len(jobs)==90
 value=dict(jobs=jobs,worker_sha256=sha(__file__),net_sha256=sha(ROOT/'src/kagml/net_player.py'),parameters=[dict(fraction=f,room=r) for f in (.8,.9,.95) for r in (70,85)],source='original P2 market full games against fifth-nflow;45planTRAINseeds bothseats',test_contents_read=0,evaluation_tuning=0)
 p=LOCAL/'selling-inputs.json'
 if p.exists():assert json.loads(p.read_text())==value
 else:save(p,value)
 return value

def case(j):
 cfg=json.loads((LOCAL/'selling-inputs.json').read_text());assert sha(__file__)==cfg['worker_sha256'] and sha(ROOT/'src/kagml/net_player.py')==cfg['net_sha256'];out=RUN/f"{j['seed']}-seat{j['seat']}.json"
 if out.exists():return str(out)
 assert j['seed'] not in range(20001,20025) and j['seed'] not in range(10320,10325) and sha(DATA/j['file'])==j['sha256']
 RT,Net=lib();K=RT.K;snap=[];original=K._process_market
 def capture(states,env):
  snap.append(dict(step=int(states[0].observation.step),market=copy.deepcopy(states[0].observation.market),shed=[dict(s.observation.private['shed']) for s in states],actions=copy.deepcopy([s.action for s in states]),farms=copy.deepcopy(states[0].observation.farms),configuration=copy.deepcopy(env.configuration)))
  return original(states,env)
 K._process_market=capture
 with gzip.open(DATA/j['file'],'rt',encoding='utf8') as f:rep=json.load(f)
 banks=[r['money'] for r in rep['steps'][-1][0]['observation']['farms']];meta=dict(episode=970000000000+j['seed']*10+j['seat'],created='',**{f'{k}_{s}':banks[s] if k=='reward' else -1 for s in (0,1) for k in ('reward','sub','team','rating')})
 try:tables,audit=RT.replay(rep,meta,'split-weeds');assert tables is not None,audit
 finally:K._process_market=original
 seat=j['seat'];goods=Net.SHOP_GOODS;actual=Counter();actual_revenue=Counter()
 for r in tables['sales']:
  if r['seat']==seat and r['product'] in goods:actual[r['step'],r['product']]+=r['units'];actual_revenue[r['product']]+=r['revenue']
 options=[]
 for param in cfg['parameters']:
  actor=Net.__new__(Net);actor.sell_state=None;actor.ONLINE_FRACTION=param['fraction'];actor.ONLINE_ROOM=param['room'];shift=Counter();received=Counter();qty=Counter();day=-1;terminal_backlog=0
  for z in snap:
   t=z['step'];d=t//24
   if d!=day:terminal_backlog+=sum(max(0,-v) for v in shift.values());shift=Counter();day=d
   shed=dict(z['shed'][seat])
   for p in goods:shed[p]=max(0,shed.get(p,0)-shift[p])
   obs=dict(day=d,hour=t%24,market=z['market'],private=dict(shed=shed));action=actor._online_sell(obs,copy.deepcopy(z['actions'][seat] or {}))
   # Only target goods are re-auctioned; other market/worker paths remain recorded.
   actions=[]
   for s in (0,1):
    source=action if s==seat else z['actions'][s] or {};orders=[]
    for order in (source.get('market') or [])[:10]:
     orders.append(order if len(order)>=2 and order[0]=='SELL' and order[1] in goods else ['PASS'])
    actions.append(dict(market=orders))
   m=copy.deepcopy(z['market']);farms=[dict(money=10**9) for _ in (0,1)];priv=[dict(shed=dict(z['shed'][s])) for s in (0,1)];priv[seat]['shed']=shed
   states=[NS(observation=NS(market=m,farms=farms,private=priv[s]),action=actions[s]) for s in (0,1)];start=dict(shed)
   K._process_market(states,NS(configuration=z['configuration']))
   # Revenue attribute each good using native per-unit commit, not aggregate bank shared acrossgoods.
   # Re-run each good alone, preserving same order slots and the other products as no-op slots.
   for p in goods:
    mm=copy.deepcopy(z['market']);ff=[dict(money=10**9) for _ in (0,1)];pp=[dict(shed=dict(z['shed'][s])) for s in (0,1)];pp[seat]['shed']=dict(start)
    ss=[NS(observation=NS(market=mm,farms=ff,private=pp[s]),action=dict(market=[o if len(o)>=2 and o[1]==p else ['PASS'] for o in actions[s]['market']])) for s in (0,1)]
    K._process_market(ss,NS(configuration=z['configuration']));n=start.get(p,0)-pp[seat]['shed'].get(p,0);qty[p]+=n;received[p]+=ff[seat]['money']-10**9;shift[p]+=n-actual[t,p]
  terminal_backlog+=sum(max(0,-v) for v in shift.values())
  options.append(dict(**param,gain=sum(received.values())-sum(actual_revenue.values()),actual_revenue=dict(actual_revenue),revenue=dict(received),sold=dict(qty),day_end_unsold_units=terminal_backlog))
 save(out,dict(passed=True,source=j,options=options,worker_sha256=cfg['worker_sha256'],native_tables=6,new_policy_games=0));return str(out)

def aggregate(cfg):
 data=[json.loads((RUN/f"{j['seed']}-seat{j['seat']}.json").read_text()) for j in cfg['jobs']];scores=[]
 for i,p in enumerate(cfg['parameters']):scores.append(dict(**p,gain=sum(d['options'][i]['gain'] for d in data)/90,day_end_unsold=sum(d['options'][i]['day_end_unsold_units'] for d in data)/90))
 best=max(scores,key=lambda r:r['gain']);save(ROOT/'reports/ONLINE_SELL_TRAINING.json',dict(passed=True,training_games=90,source=cfg['source'],scores=scores,selected=best,evaluation_tuning=0,limitations='Recorded preturn inventories reset; fixed worker arrivals and opponent issued sell orders; no future-state/solvency feedback; only3goods; not directly comparable with16evalgame oracle4946; daily sold volume may shift/deadline delivery differ.'))
 print(json.dumps(best,separators=(',',':')))
if __name__=='__main__':
 assert os.environ.get('PYTHONHASHSEED')=='0'
 cfg=prepare()
 with ProcessPoolExecutor(max_workers=4) as pool:
  for f in as_completed([pool.submit(case,j) for j in cfg['jobs']]):f.result();save(LOCAL/'status.json',dict(state='running',phase='task2-training-market-tune',completed=len(list(RUN.glob('*-seat*.json'))),target=90,analysis_workers=4,game_processes=0))
 aggregate(cfg);save(LOCAL/'status.json',dict(state='phase-complete',phase='task2-training-market-tune',completed=90,target=90,workers=0))
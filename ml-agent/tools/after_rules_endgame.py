"""Owned day16-23 adapter around the frozen original E producer. Policy/encoders are never edited."""
import hashlib,json,os,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OLD=ROOT.parent/'kaggriculture-ml-overnight'
DATA=Path('kaggriculture-ml-data');CAMPAIGN=DATA/'runs/after-rules-20261028';RUN=CAMPAIGN/'l1end-d16-23';LOCAL=ROOT/'.cache/after-rules'
sys.path[:0]=[str(OLD/'tools'),str(OLD/'src')]
import endgame_common as E
import endgame_runtime as R
import endgame_dataset as D
ORIGINAL_RUN=E.RUN

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,v):
 p.parent.mkdir(parents=True,exist_ok=True);t=p.with_suffix('.tmp')
 for attempt in range(10):
  try:t.write_text(json.dumps(v,separators=(',',':')),encoding='utf8');t.replace(p);return
  except PermissionError:
   if attempt==9:raise
   time.sleep(.1)
def episode(seed,seat,day):
 E.safe(seed);assert seat in (0,1) and 16<=day<=23
 return int(seed)*1000+seat*100+day

def prepare():
 cfg=R.config();rows=[r for r in cfg['schedule'] if r['purpose']=='labels'];assert len(rows)==107 and all(r['split']=='train' for r in rows)
 parents={f"{r['seed']}-{s}":dict(file=R.full_path(r['seed'],s).relative_to(DATA).as_posix(),sha256=sha(R.full_path(r['seed'],s))) for r in rows for s in (0,1)}
 RUN.mkdir(parents=True,exist_ok=True)
 original=(ORIGINAL_RUN/'config.json').read_bytes();copy=RUN/'config.json'
 if copy.exists():assert copy.read_bytes()==original
 else:
  temporary=copy.with_suffix('.tmp');temporary.write_bytes(original);temporary.replace(copy)
 jobs=[dict(kind='family',row=r,seat=s) for r in rows for s in (0,1)]
 value=dict(original_signature=cfg['signature'],original_config_sha256=sha(ORIGINAL_RUN/'config.json'),worker_sha256=sha(__file__),
  parents=parents,jobs=jobs,days=list(range(16,24)),workers=4,target_segments=1712,target_turns=41088,
  adapter_changes=['extend only episode day guard to16-23 with identical episode arithmetic','route receipts/raw/native tables to new versioned folders','reuse exact original P2 parent paths','replace obsolete scheduling gate with current authorization'],
  policy_and_encoding_changes=[],test_contents_read=0)
 path=LOCAL/'endgame-inputs.json'
 if path.exists():assert json.loads(path.read_text())==value
 else:save(path,value)
 save(RUN/'extension-config.json',value);return value

def guard():
 assert os.environ.get('PYTHONHASHSEED')=='0'
 assert json.loads((CAMPAIGN/'task1-reported.json').read_text())['passed']
 assert json.loads((CAMPAIGN/'task2-reported.json').read_text())['passed']
 assert not (LOCAL/'STOP-NEW').exists()

def install():
 value=json.loads((LOCAL/'endgame-inputs.json').read_text());assert sha(__file__)==value['worker_sha256']
 cfg=R.config();assert cfg['signature']==value['original_signature']
 assert sha(ORIGINAL_RUN/'config.json')==value['original_config_sha256']
 parents={k:DATA/v['file'] for k,v in value['parents'].items()}
 E.RUN=RUN;E.episode=episode
 R.full_path=lambda seed,seat:parents[f'{E.safe(seed)}-{seat}']
 R.require_free=guard
 D.RAW=DATA/'raw/endgame-p2-nflow-d16-23/fourth';D.TABLES=DATA/'datasets/endgame-p2-nflow-l1-d16-23'
 return value

def execute(job):
 guard();value=install();r=job['row'];seat=job['seat'];assert dict(kind='family',row=r,seat=seat) in value['jobs']
 p=value['parents'][f"{r['seed']}-{seat}"];assert sha(DATA/p['file'])==p['sha256']
 kind=job['kind'];begun=time.time()
 F,_,_,RT,_=R.libraries();assert Path(F.__file__).resolve()==(OLD/'tools/run_full.py').resolve()
 assert Path(RT.__file__).resolve()==(OLD/'src/kagml/replay_tables.py').resolve()
 if kind=='family':
  # Existing arrays are verified/adopted only with this extension's own label receipt.
  adapter=None;parent=None
  for day in range(16,24):
   stem=f"{r['seed']}-seat{seat}-d{day}-h0";file=DATA/'datasets/turns/l1end'/(stem+'.npz');receipt=RUN/'dataset/encoding/l1end'/(stem+'.json')
   if not file.exists():continue
   label_path=RUN/'labels'/f"{r['seed']}-seat{seat}-d{day}.json"
   assert label_path.exists(),'Refusing to overwrite or adopt an array without our frozen label receipt'
   label=json.loads(label_path.read_text());assert label['signature']==value['original_signature'] and label['parent_sha256']==p['sha256']
   if receipt.exists():
    w=json.loads(receipt.read_text())['manifest'];assert sha(file)==w['sha256'] and w['raw_sha256']==label['manifest']['sha256']
   else:
    if adapter is None:adapter=D.adapters();_,_,_,_,load=R.libraries();parent=load(R.full_path(r['seed'],seat))
    w=adapter.encode_segment('l1end',label['manifest'],parent,seat,True)
    save(receipt,dict(manifest=w,encoder_sha256=w['encoder_sha256'],recovered_from_verified_existing_array=True))
   market=DATA/'datasets/turn-markets/l1end'/(stem+'.npz');market_receipt=RUN/'dataset/markets/l1end'/(stem+'.json')
   if not market.exists() or not market_receipt.exists():
    if adapter is None:adapter=D.adapters()
    row=adapter.market_one((w,market.exists()));save(market_receipt,row)
  result=D.family((r,seat,list(range(16,24))))
 elif kind=='parity':
  adapter=D.adapters();_,_,_,_,load=R.libraries();parent=load(R.full_path(r['seed'],seat));result=[]
  for day in (16,23):
   label=json.loads((RUN/'labels'/f"{r['seed']}-seat{seat}-d{day}.json").read_text())
   w=adapter.encode_segment('l1end',label['manifest'],parent,seat,True);adapter.market_one((w,True));result.append(dict(day=day,turns=w['turns']))
 elif kind=='repeat':
  old=json.loads((RUN/'labels'/f"{r['seed']}-seat{seat}-d{job['day']}.json").read_text());again=D.label_day(r,seat,job['day'],True)
  assert old['gameplay_sha256']==again['gameplay_sha256'];result=dict(day=job['day'],gameplay_sha256=again['gameplay_sha256'])
 elif kind=='native-full':
  from endgame_pipeline import native_full
  result=native_full((r,seat))
 else:raise ValueError(kind)
 assert R.config()['signature']==value['original_signature']
 k=hashlib.sha256(json.dumps(job,sort_keys=True).encode()).hexdigest()[:20]
 save(RUN/'completed'/(k+'.json'),dict(passed=True,job=job,result=result,seconds=time.time()-begun,original_signature=value['original_signature'],worker_sha256=value['worker_sha256']))
 return result
if __name__=='__main__':
 if sys.argv[1]=='prepare':print(len(prepare()['jobs']))
 else:print(json.dumps(execute(json.loads(Path(sys.argv[1]).read_text())),separators=(',',':')))
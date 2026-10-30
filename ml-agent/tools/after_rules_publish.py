"""Append verified day16-23 labels and retain all original rows/arrays, including full old l1end."""
from collections import Counter
import csv,io,json,subprocess,time,gzip
from pathlib import Path
import after_rules_endgame as W
ROOT=W.ROOT;DATA=W.DATA;RUN=W.RUN

def read(p):
 with Path(p).open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))
def git(*args):return subprocess.check_output(['git',*args],cwd=ROOT,text=True,encoding='utf8')
def merge(base,extra,key):
 index={r[key]:r for r in base};assert len(index)==len(base);out=list(base)
 for r in extra:
  if r[key] in index:assert {k:str(v) for k,v in index[r[key]].items()}=={k:str(v) for k,v in r.items()},('Metadata collision',r[key])
  else:out.append(r);index[r[key]]=r
 return out

def publish():
 cfg=json.loads((W.LOCAL/'endgame-inputs.json').read_text());v=json.loads((RUN/'verified.json').read_text());assert v['passed'] and v['worker_sha256']==cfg['worker_sha256']
 assert W.R.config()['signature']==cfg['original_signature']
 assert Counter(j['kind'] for j in v['jobs'])=={'parity':6,'repeat':4,'native-full':3}
 for j in v['jobs']:
  import hashlib
  key=hashlib.sha256(json.dumps(j,sort_keys=True).encode()).hexdigest()[:20];r=json.loads((RUN/'completed'/(key+'.json')).read_text())
  assert r['passed'] and r['worker_sha256']==cfg['worker_sha256'] and r['original_signature']==cfg['original_signature']
  if j['kind']=='parity':assert len(r['result'])==2 and {x['day'] for x in r['result']}=={16,23}
 oldroot=ROOT.parent/'kaggriculture-ml-endgame-model';old=[r for r in read(oldroot/'manifests/turns.csv') if r['source']=='l1end'];assert len(old)==1284
 parents={k:p['sha256'] for k,p in cfg['parents'].items()}
 for p in cfg['parents'].values():assert W.sha(DATA/p['file'])==p['sha256']
 new=[];labels=[];family_excluded=[]
 for j in cfg['jobs']:
  f=json.loads((RUN/'families'/f"{j['row']['seed']}-seat{j['seat']}-full.json").read_text());assert len(f['labels'])==8 and len(f['workers'])+len(f.get('excluded',[]))==8
  new+=f['workers'];labels+=f['labels'];family_excluded+=f.get('excluded',[])
 excluded=v.get('excluded_segments',[]);assert family_excluded==excluded;expected_new=1712-len(excluded)
 assert len(new)==expected_new and sum(int(r['turns']) for r in new)==24*expected_new
 expected={(j['row']['seed'],j['seat'],d) for j in cfg['jobs'] for d in range(16,24)}
 omitted={(int(r['seed']),int(r['seat']),int(r['day'])) for r in excluded};assert len(omitted)==len(excluded)
 assert {(int(r['game']),W.E.physical_seat(r),int(r['day'])) for r in new}==expected-omitted
 assert {(int(r['manifest']['game']),int(r['manifest']['seat']),int(r['manifest']['day'])) for r in labels}==expected
 if excluded:assert v['approval_sha256']==W.sha(W.LOCAL/'capacity-approval.json')
 for e in excluded:
  assert e['peak_units']>14 and W.sha(DATA/e['raw_file'])==e['raw_sha256']
  with gzip.open(DATA/e['raw_file'],'rt',encoding='utf8') as stream:rep=json.load(stream)
  assert max(len(frame[e['seat']]['observation']['farms'][e['seat']]['hands'])+1 for frame in rep['steps'][:-1])==e['peak_units']
  for folder in ('turns','turn-markets'):assert not (DATA/'datasets'/folder/'l1end'/f"{e['seed']}-seat{e['seat']}-d{e['day']}-h0.npz").exists()
 for label in labels:
  r=label['manifest'];assert label['signature']==cfg['original_signature'] and len(label['native_rows'])==6
  assert label['parent_sha256']==parents[f"{r['game']}-{r['seat']}"] and W.sha(DATA/r['file'])==r['sha256']
  for path,h in label['output_hashes'].items():assert W.sha(DATA/path)==h
 workers=read(ROOT/'manifests/turns.csv');markets=read(ROOT/'manifests/turn-markets.csv');fields=list(workers[0]);market_fields=list(markets[0])
 joined=merge(workers,[{k:r[k] for k in fields} for r in old+new],'file')
 safe={r['file']:r for r in joined if int(r['game']) not in W.E.TEST and r['split']!='test'}
 for r in safe.values():assert W.sha(DATA/r['file'])==r['sha256']
 prior=read(oldroot/'manifests/turn-markets.csv');present={r['worker_file'] for r in markets};extra=[]
 for r in prior:
  if r['worker_file'] not in safe or r['worker_file'] in present:continue
  w=safe[r['worker_file']];assert r['worker_sha256']==w['sha256'] and r['raw_sha256']==w['raw_sha256'] and W.sha(DATA/r['file'])==r['sha256']
  extra.append(r);present.add(r['worker_file'])
 newmarkets=[]
 for w in new:
  r=json.loads((RUN/'dataset/markets/l1end'/(Path(w['file']).stem+'.json')).read_text())
  assert r['worker_file']==w['file'] and r['worker_sha256']==w['sha256'] and r['raw_sha256']==w['raw_sha256'] and W.sha(DATA/r['file'])==r['sha256'];newmarkets.append(r)
 allmarkets=merge(markets,extra+newmarkets,'worker_file')
 assert len(allmarkets)==len(safe) and {r['worker_file'] for r in allmarkets}==set(safe)
 for r in allmarkets:
  w=safe[r['worker_file']];assert r['worker_sha256']==w['sha256'] and r['raw_sha256']==w['raw_sha256'] and W.sha(DATA/r['file'])==r['sha256']
 for name,rows in [('turns.csv',joined),('turn-markets.csv',allmarkets)]:
  original=list(csv.DictReader(io.StringIO(git('show','b991ec8:manifests/'+name))))
  assert rows[:len(original)]==original
 l1end=[r for r in joined if r['source']=='l1end'];assert len(l1end)==1284+expected_new and sum(int(r['turns']) for r in l1end)==30602+24*expected_new
 assert len({int(r['game']) for r in l1end})==107 and Counter(int(r['day']) for r in l1end)=={d:214-sum(int(e['day'])==d for e in excluded) for d in range(16,30)}
 assert all(r['split']=='train' and int(r['game']) not in W.E.TEST and not 20001<=int(r['game'])<=20024 for r in l1end)
 selected=[r for r in safe.values() if not 20001<=int(r['game'])<=20024 and 16<=int(r['day'])<=29];files={r['file'] for r in selected}
 oldraw=read(oldroot/'manifests/ownfarm-endgame.csv');assert len(oldraw)==1284;oldraw=oldraw+[r['manifest'] for r in labels if (int(r['manifest']['game']),int(r['manifest']['seat']),int(r['manifest']['day'])) not in omitted]
 outputs={'turns.csv':joined,'turn-markets.csv':allmarkets,'endgame-seeds.csv':W.R.config()['schedule'],'endgame-turns.csv':selected,'endgame-markets.csv':[r for r in allmarkets if r['worker_file'] in files],'ownfarm-endgame.csv':oldraw}
 if excluded:outputs['ownfarm-endgame-excluded.csv']=excluded
 for name,rows in outputs.items():
  for attempt in range(10):
   try:W.E.write_csv(ROOT/'manifests'/name,rows,fields if name in ('turns.csv','endgame-turns.csv') else market_fields if 'markets' in name else None);break
   except PermissionError:
    if attempt==9:raise
    time.sleep(.1)
 proof=dict(passed=True,requested_new_segments=1712,generated_raw_segments=1712,new_segments=expected_new,new_turns=24*expected_new,excluded_segments=excluded,exclusions_user_approved=bool(excluded),preserved_new_array_hashes_checked=v.get('preserved_array_hashes_checked',0),total_l1end_segments=1284+expected_new,total_l1end_turns=30602+24*expected_new,old_l1end_retained=1284,train_identities=107,physical_seats=[0,1],day_counts=dict(Counter(int(r['day']) for r in l1end)),new_full_games=0,test_contents_read=0,analysis_training_labels=0,evaluation_training_labels=0,existing_rows_preserved=True,all_non_test_worker_hashes_checked=len(safe),existing_worker_arrays_unchanged=True,parity_samples=12,label_repeats=4,parent_native_replays=3,every_new_label_native_tables=6,every_new_market_native_verified=True,original_signature=cfg['original_signature'],adapter_changes=cfg['adapter_changes'],policy_and_encoding_changes=[])
 W.save(ROOT/'reports/AFTER_RULES_ENDGAME_CHECKS.json',proof)
 assert git('branch','--show-current').strip()=='dev/eugene-codex-after-rules'
 paths=['manifests/'+p for p in outputs]+['reports/AFTER_RULES_ENDGAME_CHECKS.json'];assert set(git('diff','--cached','--name-only').splitlines())<=set(paths)
 subprocess.run(['git','add','--',*paths],cwd=ROOT,check=True);subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True);assert not git('ls-files','--cached','-i','--exclude-standard').strip()
 subprocess.run(['git','commit','-m',f'Extend l1end with{expected_new} verified train segments and{len(excluded)} approved capacity exclusions'],cwd=ROOT,check=True)
 commit=git('rev-parse','HEAD').strip();W.save(RUN/'published.json',dict(**proof,commit=commit));print(json.dumps(dict(commit=commit,new_segments=expected_new,total_segments=1284+expected_new,excluded_segments=len(excluded)),separators=(',',':')))
if __name__=='__main__':publish()
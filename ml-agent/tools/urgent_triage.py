"""Package U: recorded-state analysis only. No policy calls or new games.
PYTHONHASHSEED=0 KAGML_DATA=<data> python tools/urgent_triage.py ledger|scenarios|fit|check --workers 2
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import contextlib
import copy
import csv
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import random
import re
import sys
import time

for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS'):
    os.environ[key]='1'
REPO=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(REPO/'src'),str(REPO/'tools')]
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kagml import board_features as B
    from kagml.preview import pin_weeds,env_from_snapshot,snapshot_from_replay
    import kaggle_environments.envs.kaggriculture.kaggriculture as K
import numpy as np
import pandas as pd
ROOT=Path(os.environ.get('KAGML_DATA','<data>'))
OUT=ROOT/'runs/urgent-triage-v1'
MODEL=ROOT/'models/triage-v1'
REPORT=REPO/'reports'
EL3=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3'
ANALYSIS=set(range(10315,10320));TEST=set(range(10320,10325))
SOURCES=('l1','l3-r1','l3-r2','l3-net1','l1-edge','l3-edge','l1more')
ITEMS=tuple(K.CROPS)+tuple(K.ANIMALS)
READS=set()
FEATURES=['hour','days_left','age','held','price','fertilized','survival','production','night_units','night_increment',
          'asset_cost','stake','open_items','open_survival','nearest','nearby2','workers','shed_wheat','money','care_bonus','full',
          'dist_shed','onset_hour']+[f'item_{s.lower()}' for s in ITEMS]


def checked_game(game):
    game=int(game)
    assert game not in TEST, f'Forbidden test game {game}'
    assert game in set(range(10301,10320))|set(range(10401,10449)),game
    return game


def read_game(path,game):
    checked_game(game);path=Path(path);READS.add(str(path))
    data=path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix=='.gz' else data)


def write_csv(path,rows):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    if isinstance(rows,pd.DataFrame):rows.to_csv(path,index=False);return
    assert rows,path
    with (gzip.open(path,'wt',newline='',encoding='utf-8') if path.suffix=='.gz' else path.open('w',newline='',encoding='utf-8')) as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def save(path,value):
    Path(path).parent.mkdir(parents=True,exist_ok=True)
    Path(path).write_text(json.dumps(value,indent=2,default=str),encoding='utf-8')


def ident(tile,x,y):
    if not isinstance(tile,dict):return None
    if tile.get('kind')=='PLANT':return (x,y,tile['crop'],tile['planted_day'])
    if tile.get('animal'):return (x,y,tile['animal'],tile['placed_day'])
    return None


def risk(tile,x,y,obs):
    key=ident(tile,x,y)
    if key is None:return None
    item=key[2];day=obs['day'];animal=item in K.ANIMALS
    tab=K.ANIMALS[item] if animal else K.CROPS[item]
    served=tile.get('fed_today' if animal else 'watered_today',False)
    since=day+1-key[3]-tab['first_yield_day']
    prod=bool(since>=0 and (animal or tab['ongoing']) and since%max(1,tab['interval'])==0
              and (animal or since//tab['interval']+1<=tab['max_yield']))
    survival=tile.get('consecutive_unfed' if animal else 'consecutive_unwatered',0)>=1
    if served or not (survival or prod):return None
    product=tab['product'] if animal else item;price=obs['market']['prices'][product]
    held=tile.get('yield_units',0);fert=not animal and tile.get('fertilized_until_day',-1)>=day
    bonus=tile.get('pending_care_bonus',0) if animal else int(fert)
    cap=tab['max_held'] if animal else tab['max_yield']
    units=min(max(0,cap-held),1+bonus) if prod else 0
    increment=min(max(0,cap-held),1+bonus)-min(max(0,cap-held),1) if prod else 0
    cost=tab['cost'] if animal else tab['seed']
    return dict(x=x,y=y,item=item,animal=int(animal),age=day-key[3],held=held,price=price,fertilized=int(fert),
        survival=int(survival),production=int(prod),night_units=units,night_increment=increment,
        asset_cost=cost,stake=cost+price*(held+units),care_bonus=tile.get('pending_care_bonus',0),full=int(held>=cap),
        actual_skip_loss=cost+price*(held+units) if survival else price*increment,dist_shed=abs(x-4)+abs(y-4))


def segment(r):
    game=checked_game(r['game']);rep=read_game(ROOT/r['raw_file'],game)
    assert hashlib.sha256((ROOT/r['raw_file']).read_bytes()).hexdigest()==r['raw_sha256']
    mark=rep.get('takeover',rep.get('ownfarm'));cut=int(mark.get('takeover_step',mark.get('start_step')))
    events={};hours=[];jobs=[];order=0;previous={};checks=Counter()
    day=int(r['day']);sid=f"{r['source']}:{game}:d{day}:h{r['H']}"
    for i in range(len(rep['steps'])-1):
        obs=rep['steps'][i][0]['observation'];step=obs['day']*24+obs['hour']
        if step<cut:continue
        assert obs['day']==day
        hour=obs['hour'];farm=obs['farms'][0];pos=[farm['farmer'],*farm['hands']]
        active={}
        for y,row in enumerate(farm['tiles']):
            for x,tile in enumerate(row):
                f=risk(tile,x,y,obs)
                if f is not None:active[ident(tile,x,y)]=f
        opens=len(active);surv=sum(f['survival'] for f in active.values())
        action=rep['steps'][i+1][0]['action'] or {};cmds=[action.get('farmer',['PASS']),*action.get('hands',[])]
        kind_counts=Counter((c or ['PASS'])[0] for c in cmds[:len(pos)])
        for key,f in active.items():
            distances=[abs(p[0]-f['x'])+abs(p[1]-f['y']) for p in pos]
            if key not in events:
                events[key]=dict(segment=sid,source=r['source'],split=r['split'],game=game,day=day,H=int(r['H']),
                    onset_hour=hour,served=0,service_hour=-1,service_worker=-1,service_order=-1,service_open=-1,
                    service_dist_at_onset=-1,service_dist_previous=-1,resolution='unserved',terminal_censored=int(day==29),
                    dawn_risk=int(hour==0),takeover_risk=int(step==cut),days_left=29-day,onset_open=opens,onset_nearest=min(distances),**f,initial_positions=json.dumps(pos,separators=(',',':')))
            row=dict(segment=sid,game=game,day=day,source=r['source'],split=r['split'],hour=hour,
                days_left=29-day,open_items=opens,open_survival=surv,nearest=min(distances),nearby2=sum(d<=2 for d in distances),
                workers=len(pos),shed_wheat=obs['private']['shed'].get('WHEAT',0),money=farm['money'],
                onset_hour=events[key]['onset_hour'],**f)
            row['_key']=key;hours.append(row)
        # Execute only unit operations on copies, in engine order. No policy inference.
        ff=copy.deepcopy(farm);pp=copy.deepcopy(obs['private'])
        for u,c in enumerate(cmds[:len(pos)]):
            c=c or ['PASS'];x,y=pos[u];key=ident(ff['tiles'][y][x],x,y)
            before=copy.deepcopy(ff['tiles'][y][x]);ok=B.apply(ff,pp,u,c,day)
            if c[0] in ('WATER','FEED') and ok and key in active:
                e=events[key]
                if not e['served']:
                    order+=1;e.update(served=1,service_hour=hour,service_worker=u,service_order=order,service_open=len(active),resolution=c[0])
                    p=json.loads(e['initial_positions']);e['service_dist_at_onset']=abs(p[u][0]-x)+abs(p[u][1]-y) if u<len(p) else -1
                    prior=previous.get(u);e['service_dist_previous']=abs(prior[0]-x)+abs(prior[1]-y) if prior else -1
                    active.pop(key)
            if ok and c[0] in ('HARVEST','DIG') and key in events and ident(ff['tiles'][y][x],x,y)!=key:
                if not events[key]['served']:events[key]['resolution']=c[0]
                active.pop(key,None)
            checks['unit_commands']+=1
        after_tiles=rep['steps'][i+1][0]['observation']['farms'][0]['tiles']
        for key,e in events.items():
            if e['served'] or e['resolution']!='unserved':continue
            x,y=e['x'],e['y']
            if ident(farm['tiles'][y][x],x,y)==key and ident(after_tiles[y][x],x,y)!=key:
                e['resolution']=('escape' if e['animal'] else 'dry_death') if hour==23 and e['survival'] else 'decay'
        previous={u:p for u,p in enumerate(pos)}
        jobs.append(dict(segment=sid,game=game,day=day,source=r['source'],hour=hour,workers=len(pos),
                         open_items=opens,**{f'job_{k}':kind_counts[k] for k in ('NORTH','SOUTH','EAST','WEST','PASS','WATER','FEED','CARE','HARVEST','FERTILIZE','COLLECT_FERTILIZER','PLANT','DIG','PICKUP','DROP','PLACE','BUILD_COOP','BUILD_PASTURE')}))
        # Recorded next state independently confirms service flags, except at midnight.
        if hour<23:
            after=rep['steps'][i+1][0]['observation']['farms'][0]['tiles']
            for e in events.values():
                if e['service_hour']==hour:
                    t=after[e['y']][e['x']]
                    if ident(t,e['x'],e['y'])==(e['x'],e['y'],e['item'],day-e['age']):
                        assert t.get('fed_today' if e['animal'] else 'watered_today'),(sid,hour,e)
                    checks['service_flags']+=1
    last=rep['steps'][-1][0]['observation']['farms'][0]['tiles']
    for key,e in events.items():
        if not e['served'] and e['resolution']=='unserved':
            t=last[e['y']][e['x']];same=ident(t,e['x'],e['y'])==key
            e['resolution']='remaining' if same else ('escaped_or_removed' if e['animal'] else 'harvested_dug_dead_or_rotted')
        e.pop('initial_positions')
    for h in hours:
        e=events[h.pop('_key')];h['served']=e['served'];h['terminal_censored']=e['terminal_censored']
    return list(events.values()),hours,jobs,checks


def ledger_source(job):
    source,rows=job;READS.clear();events=[];hours=[];jobs=[];counts=Counter();start=time.time()
    receipt=OUT/f'{source}-receipt.json'
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old['segments']==len(rows) and old.get('ledger_version')==2:return {k:v for k,v in old.items() if k!='reads'}
    for i,r in enumerate(rows):
        e,h,j,c=segment(r);events.extend(e);hours.extend(h);jobs.extend(j);counts.update(c)
        if (i+1)%200==0:print(json.dumps(dict(source=source,segments=i+1,total=len(rows))),flush=True)
    for name,data in [('items',events),('hours',hours),('jobs',jobs)]:write_csv(OUT/f'{source}-{name}.csv.gz',data)
    result=dict(ledger_version=2,source=source,segments=len(rows),items=len(events),hours=len(hours),jobs=len(jobs),checks=dict(counts),reads=sorted(READS),seconds=time.time()-start)
    save(OUT/f'{source}-receipt.json',result);return {k:v for k,v in result.items() if k!='reads'}


def manifest_rows():
    with (REPO/'manifests/turns.csv').open() as fh:rows=list(csv.DictReader(fh))
    rows=[r for r in rows if r['source'] in SOURCES and int(r['game']) not in TEST]
    assert {r['split'] for r in rows}=={'train','analysis'}
    assert all((int(r['game']) in ANALYSIS)==(r['split']=='analysis') for r in rows)
    return rows


def ledger(workers,smoke=False):
    OUT.mkdir(parents=True,exist_ok=True);rows=manifest_rows()
    jobs=[(s,[r for r in rows if r['source']==s]) for s in SOURCES]
    if smoke:jobs=[(s,rr[:1]) for s,rr in jobs]
    with ProcessPoolExecutor(max_workers=workers) as pool:
        results=list(pool.map(ledger_source,jobs))
    save(OUT/('smoke.json' if smoke else 'ledger.json'),results)
    print(json.dumps(results),flush=True)


def schedule(seed):
    out=[]
    for day in range(2,24,3):
        rng=random.Random((int(seed)*1_000_003)^day)
        rng.random();rng.random() # pin_weeds: exactly one parent draw per farm
        out.append(rng.choice(sorted(K.SHOPS)))
    return out


def scenario(seed):
    shops=schedule(seed);early=shops[:2]
    row=dict(game=int(seed),shop1=early[0],shop2=early[1],pair=' > '.join(early),B=sum('STRAWBERRY' in K.SHOPS[s] for s in early),
             full_schedule='|'.join(shops))
    for p in ('WHEAT','CARROT','TOMATO','STRAWBERRY','EGG','MILK','WOOL'):
        row[f'early_{p.lower()}']=sum((2 if len(K.SHOPS[s])==1 else 1) for s in early if p in K.SHOPS[s])
    return row


def se_stats(values,games):
    x=np.array(values,dtype=float);g=pd.DataFrame(dict(v=x,g=list(games))).groupby('g').v.mean()
    return dict(n=len(x),games=len(g),mean=float(x.mean()),se_morning=float(x.std(ddof=1)/np.sqrt(len(x))) if len(x)>1 else None,
                se_game=float(g.std(ddof=1)/np.sqrt(len(g))) if len(g)>1 else None)


def scenarios():
    READS.clear();seeds=list(range(10301,10325))+list(range(10401,10449));census=[];checks=Counter()
    for seed in seeds:
        row=scenario(seed);row['corpus']='el3' if seed<10400 else 'N2'
        row['split']='test_metadata_only' if seed in TEST else ('analysis' if seed in ANALYSIS else 'train')
        if seed not in TEST:
            rep=read_game(EL3/f'{seed}.json' if seed<10400 else ROOT/'raw/template-games'/f'{seed}.json.gz',seed)
            for day in range(3,25,3):
                actual=rep['steps'][day*24][0]['observation']['town']['unlocked_shops']
                assert actual==schedule(seed)[:day//3],(seed,day,actual,schedule(seed));checks['shop_dawns']+=1
        census.append(row)
    write_csv(REPORT/'SCENARIO_CENSUS.csv',census)
    write_csv(REPORT/'SCENARIO_SEEDS_10501_11500.csv',[scenario(s) for s in range(10501,11501)])
    table=pd.DataFrame(census);groups=[]
    for scope,d in [('all72_seed_metadata',table),('fit62',table[table.split=='train']),('analysis5',table[table.split=='analysis']),('el3_24_seed_metadata',table[table.corpus=='el3']),('N2_48',table[table.corpus=='N2'])]:
        for b in range(3):groups.append(dict(scope=scope,B=b,games=int((d.B==b).sum()),total=len(d),share=float((d.B==b).mean()),ordered_pairs=d[d.B==b].pair.nunique()))
    write_csv(REPORT/'SCENARIO_BALANCE.csv',groups)
    # All requested comparison files are analysis-only; reject rather than load mixed test data.
    rows=[]
    for filename,player in [('g4A1.csv','board-v4+guard'),('g4B1.csv','board-v4+guard'),('selA1.csv','v3-fw'),('selB1.csv','v3-fw')]:
        with (ROOT/'runs/compare'/filename).open() as f:
            for r in csv.DictReader(f):
                assert int(r['game']) in ANALYSIS,filename
                if r['player'] != ('net:board-v4:guard' if filename.startswith('g4') else 'model:ranker-v3s-fw'):continue
                if 6<=int(r['day'])<=26:rows.append(dict(game=int(r['game']),day=int(r['day']),player=player,**{m:float(r[m]) for m in ('cash_change','value_plus_assets','assets_change','value_change')}))
    with (ROOT/'runs/diag/d4-d6/daily_rows.csv').open() as f:
        for r in csv.DictReader(f):
            assert int(r['game']) in ANALYSIS
            if r['diagnostic']=='D6' and r['arm'] in ('1','2','4') and 6<=int(r['morning'])<=26:
                rows.append(dict(game=int(r['game']),day=int(r['morning']),player={'1':'template','2':'teacher','4':'teacher-workers+our-plan'}[r['arm']],**{m:float(r[m]) for m in ('cash_change','value_plus_assets','assets_change','value_change')}))
    d=pd.DataFrame(rows);assert not d.duplicated(['game','day','player']).any();assert len(d)==525,len(d)
    d['B']=d.game.map(lambda g:scenario(g)['B']);d['pair']=d.game.map(lambda g:scenario(g)['pair'])
    for name in ('early_wheat','early_carrot','early_tomato','early_egg','early_milk','early_wool'):
        d[name]=d.game.map(lambda g:scenario(g)[name])
    write_csv(REPORT/'SCENARIO_MORNINGS.csv',d)
    gap=[];wide=d.pivot(index=['game','day'],columns='player',values=['cash_change','value_plus_assets','assets_change','value_change'])
    for dimension in ('B','pair','early_wheat','early_carrot','early_tomato','early_egg','early_milk','early_wool'):
        for key,cohort in d.groupby(dimension):
            idx=cohort[['game','day']].drop_duplicates();ix=pd.MultiIndex.from_frame(idx)
            for player in sorted(d.player.unique()):
                for metric in ('cash_change','value_plus_assets','assets_change','value_change'):
                    delta=wide.loc[ix,(metric,player)]-wide.loc[ix,(metric,'teacher')]
                    gap.append(dict(dimension=dimension,scenario=key,player=player,metric=metric,comparison='player_minus_teacher',**se_stats(delta,idx.game)))
    write_csv(REPORT/'SCENARIO_GAPS.csv',gap)
    # Recorded one-day actions replayed exactly through native engine; never call a policy.
    pin_weeds(True);plant=[]
    for game in sorted(ANALYSIS):
        rep=read_game(EL3/f'{game}.json',game)
        for day in range(6,27):
            for label,suffix in [('board-v4+guard','net_board-v4_guard'),('teacher','fourth')]:
                path=ROOT/f'runs/diag/d1/{game}-d{day}-{suffix}.json.gz';rec=read_game(path,game)
                snap=snapshot_from_replay(rep,day*24);env=env_from_snapshot(snap);counts=Counter()
                for i,t in enumerate(rec['turns']):
                    obs=env.state[0].observation;farm=obs['farms'][0];pos=[farm['farmer'],*farm['hands']]
                    assert [list(p) for p in pos]==t['pos']
                    ff=copy.deepcopy(farm);pp=copy.deepcopy(obs['private'])
                    turn_plants=Counter()
                    demand=Counter(c[1] for c in t['cmd'] if c and c[0]=='PLANT')
                    blocked={c for c,n in demand.items() if n>pp['seeds'].get(c,0)}
                    for u,c in enumerate(t['cmd'][:len(pos)]):
                        c=c or ['PASS']
                        if c[0]=='PLANT' and c[1] in blocked:continue
                        ok=B.apply(ff,pp,u,c,day)
                        if ok and c[0]=='PLANT':
                            counts[c[1]]+=1;turn_plants[c[1]]+=1;plant.append(dict(game=game,day=day,B=scenario(game)['B'],player=label,hour=i,unit=u,x=pos[u][0],y=pos[u][1],crop=c[1]))
                    from diag_d4_d6 import actual_events
                    with actual_events(env) as (native_events,clock):
                        clock['step']=day*24+i
                        env.step([{'farmer':t['cmd'][0],'hands':t['cmd'][1:],'market':t['market']},rep['steps'][day*24+i+1][1]['action']])
                    native_plants=Counter()
                    for event in native_events:
                        if event['op']=='PLANT':native_plants[event['item']]+=event['units']
                    assert turn_plants==native_plants,(game,day,label,i,turn_plants,native_plants)
                    checks['native_plant_turns']+=1
                    # Check exactly the tile signatures retained by the original diagnostic.
                    from diag_runs import tile_sig
                    actual=[tile_sig(t) for row in env.state[0].observation['farms'][0]['tiles'] for t in row]
                    assert actual==rec['hours'][i+1]['tiles'],(game,day,label,i)
                    checks['diag_turns']+=1
                checks['plantings']+=sum(counts.values())
    p=pd.DataFrame(plant);write_csv(OUT/'plant_events.csv.gz',p)
    mix=[];agreement=[]
    for (game,day),group in p.groupby(['game','day']):
        a=group[group.player=='board-v4+guard'];b=group[group.player=='teacher'];ca=Counter(a.crop);cb=Counter(b.crop)
        same=a.merge(b,on=['game','day','x','y'],suffixes=('_board','_teacher'))
        exact=a.merge(b,on=['game','day','hour','x','y'],suffixes=('_board','_teacher'))
        agreement.append(dict(game=game,day=day,B=scenario(game)['B'],board_plants=len(a),teacher_plants=len(b),
            mix_overlap=sum(min(ca[c],cb[c]) for c in K.CROPS),common_cell_pairs=len(same),same_crop_cell_pairs=int((same.crop_board==same.crop_teacher).sum()),
            common_time_cell_pairs=len(exact),same_crop_time_cell_pairs=int((exact.crop_board==exact.crop_teacher).sum())))
        for label,c in [('board-v4+guard',ca),('teacher',cb)]:
            for crop in K.CROPS:mix.append(dict(game=game,day=day,B=scenario(game)['B'],player=label,crop=crop,count=c[crop],total=sum(c.values())))
    write_csv(REPORT/'SCENARIO_PLANT_MORNINGS.csv',agreement);write_csv(REPORT/'SCENARIO_PLANT_MIX.csv',mix)
    save(OUT/'scenario-checks.json',dict(checks=checks,reads=sorted(READS),no_test_contents=True))
    print(json.dumps(dict(checks=checks,balance=groups)),flush=True)


def summarise_ledger():
    e=pd.concat([pd.read_csv(OUT/f'{s}-items.csv.gz') for s in SOURCES],ignore_index=True)
    e['value_band']=pd.cut(e.stake,[-1,99,299,599,999,1999,float('inf')],labels=['0-99','100-299','300-599','600-999','1000-1999','2000+'])
    e['days_band']=pd.cut(29-e.day,[-1,2,6,13,23,29],labels=['0-2','3-6','7-13','14-23','24-29'])
    e['competition_band']=pd.cut(e.service_open.where(e.served==1,0),[-1,4,9,19,39,100],labels=['0-4','5-9','10-19','20-39','40+'])
    summary=[]
    for dimension in ('item','value_band','days_band','onset_hour','source','split'):
        for value,g in e[e.terminal_censored==0].groupby(dimension,observed=True):
            served=g[g.served==1]
            summary.append(dict(dimension=dimension,group=str(value),items=len(g),games=g.game.nunique(),served_share=g.served.mean(),
                q25_hour=served.service_hour.quantile(.25),median_hour=served.service_hour.median(),q90_hour=served.service_hour.quantile(.9),
                survival_share=g.survival.mean(),actual_loss_mean=g.actual_skip_loss.mean(),removed_unserved=int(((g.served==0)&(g.resolution!='remaining')).sum())))
    write_csv(REPORT/'URGENT_SERVICE.csv',summary)
    write_csv(REPORT/'URGENT_COVERAGE.csv',[dict(source=s,**{k:v for k,v in json.loads((OUT/f'{s}-receipt.json').read_text()).items() if k not in ('source','reads','checks')}) for s in SOURCES])
    # At each hour: fraction of currently open items eventually served, with opening queue size.
    tables=[];miss_jobs=[]
    for s in SOURCES:
        h=pd.read_csv(OUT/f'{s}-hours.csv.gz');h=h[h.terminal_censored==0]
        h['queue_band']=pd.cut(h.open_items,[0,4,9,19,39,100],labels=['1-4','5-9','10-19','20-39','40+'])
        for (item,hour,q),g in h.groupby(['item','hour','queue_band'],observed=True):
            tables.append(dict(source=s,item=item,hour=hour,queue_band=str(q),open_snapshots=len(g),eventually_served=g.served.mean()))
        j=pd.read_csv(OUT/f'{s}-jobs.csv.gz');miss=e[(e.source==s)&(e.served==0)&(e.terminal_censored==0)]
        for window in ('all_open_hours','last_hour'):
            pending=h[h.served==0][['segment','hour']].drop_duplicates()
            if window=='last_hour':pending=pending[pending.hour==23]
            selected=j.merge(pending,on=['segment','hour']);total=selected.workers.sum()
            for c in j.columns:
                if c.startswith('job_'):miss_jobs.append(dict(source=s,window=window,job=c[4:],commands=selected[c].sum(),worker_commands=total,share=selected[c].sum()/total if total else None,unserved_items=len(miss)))
    write_csv(REPORT/'URGENT_OPEN_HOURS.csv',tables);write_csv(REPORT/'URGENT_ALTERNATIVE_JOBS.csv',miss_jobs)
    print(e.groupby('item').agg(items=('served','size'),served=('served','mean'),hour=('service_hour',lambda x:x[x>=0].median())).to_string(),flush=True)


def fit():
    import joblib
    from lightgbm import LGBMClassifier
    from sklearn.tree import DecisionTreeClassifier,export_text
    from sklearn.metrics import accuracy_score,balanced_accuracy_score,roc_auc_score,average_precision_score,precision_score,recall_score,brier_score_loss,confusion_matrix
    MODEL.mkdir(parents=True,exist_ok=True);arrays=[]
    for s in SOURCES:
        h=pd.read_csv(OUT/f'{s}-hours.csv.gz');h=h[h.terminal_censored==0]
        for item in ITEMS:h[f'item_{item.lower()}']=(h.item==item).astype('int8')
        arrays.append(h[FEATURES+['served','split','game','source']])
    d=pd.concat(arrays,ignore_index=True);del arrays
    train=d[d.split=='train'];held=d[d.split=='analysis'];assert not set(train.game)&set(held.game)
    assert set(held.game)==ANALYSIS and not set(d.game)&TEST
    x=train[FEATURES].astype('float32');y=train.served;z=held[FEATURES].astype('float32');target=held.served
    # Fixed before analysis scoring; no tuning on held games.
    models={'gbt':LGBMClassifier(n_estimators=160,num_leaves=15,max_depth=5,learning_rate=.06,min_child_samples=150,reg_lambda=1,random_state=0,n_jobs=2,verbosity=-1),
            'shallow':DecisionTreeClassifier(max_depth=4,min_samples_leaf=500,random_state=0)}
    scores=[]
    for name,m in models.items():
        m.fit(x,y);prob=m.predict_proba(z)[:,1];pred=prob>=.5;joblib.dump(m,MODEL/f'{name}.joblib')
        groups=[('overall',np.ones(len(held),dtype=bool)),('onset_only',held.hour.to_numpy()==held.onset_hour.to_numpy())]+[(f'game:{g}',held.game.to_numpy()==g) for g in sorted(ANALYSIS)]
        for label,mask in groups:
            yy=target[mask];pr=prob[mask];pp=pred[mask]
            scores.append(dict(model=name,cohort=label,n=len(yy),served_share=yy.mean(),accuracy=accuracy_score(yy,pp),balanced_accuracy=balanced_accuracy_score(yy,pp),
                precision=precision_score(yy,pp,zero_division=0),recall=recall_score(yy,pp),roc_auc=roc_auc_score(yy,pr),average_precision=average_precision_score(yy,pr),brier=brier_score_loss(yy,pr),
                majority_accuracy=max(yy.mean(),1-yy.mean())))
        if name=='gbt':
            write_csv(REPORT/'URGENT_FEATURE_IMPORTANCE.csv',pd.DataFrame(dict(feature=FEATURES,importance=m.feature_importances_)).sort_values('importance',ascending=False))
            m.booster_.save_model(str(MODEL/'gbt.txt'))
        else:(MODEL/'shallow_rules.txt').write_text(export_text(m,feature_names=FEATURES,decimals=2),encoding='utf-8')
        predrows=held[['game','source','hour','onset_hour']].copy();predrows['target']=target;predrows['probability']=prob
        write_csv(MODEL/f'{name}-analysis-predictions.csv.gz',predrows)
        assert np.array_equal(joblib.load(MODEL/f'{name}.joblib').predict(z.iloc[:1000]),m.predict(z.iloc[:1000]))
    write_csv(REPORT/'URGENT_MODEL_SCORES.csv',scores)
    save(MODEL/'features.json',dict(features=FEATURES,dtypes='float32',target='successful WATER/FEED before midnight for a currently open item',
        training_games=sorted(train.game.unique().tolist()),analysis_games=sorted(ANALYSIS),train_rows=len(train),analysis_rows=len(held),
        test_excluded=sorted(TEST),terminal_day29_excluded=True,threshold=.5,hashseed=0,random_seed=0,
        note='Observational teacher imitation, not causal benefit. No source/game/worker/future-action features. Hourly rows from correlated branches; accuracy is row-weighted.'))
    print(json.dumps(scores),flush=True);print((MODEL/'shallow_rules.txt').read_text(),flush=True)


def check():
    rows=manifest_rows();receipt=json.loads((OUT/'ledger.json').read_text())
    assert sum(r['segments'] for r in receipt)==len(rows)
    for s in SOURCES:
        r=json.loads((OUT/f'{s}-receipt.json').read_text());assert r['segments']==sum(x['source']==s for x in rows)
        jobs=pd.read_csv(OUT/f'{s}-jobs.csv.gz')
        assert (jobs[[c for c in jobs if c.startswith('job_')]].sum(axis=1)==jobs.workers).all(),('Missing worker jobs',s)
        assert all(not any(re.search(rf'(?<!\d){t}(?!\d)',p) for t in TEST) for p in r['reads'])
    census=pd.read_csv(REPORT/'SCENARIO_CENSUS.csv');assert len(census)==72
    assert len(pd.read_csv(REPORT/'SCENARIO_SEEDS_10501_11500.csv'))==1000
    assert len(pd.read_csv(REPORT/'SCENARIO_MORNINGS.csv'))==525
    rules=MODEL/'features.json';assert rules.exists();meta=json.loads(rules.read_text());assert set(meta['analysis_games'])==ANALYSIS
    assert not set(meta['training_games'])&(ANALYSIS|TEST)
    save(OUT/'checks.json',dict(passed=True,segments=len(rows),sources=list(SOURCES),test_contents_read=0,max_workers=2,hashseed=os.environ.get('PYTHONHASHSEED'),
        scenario_checks=json.loads((OUT/'scenario-checks.json').read_text())['checks']))
    print((OUT/'checks.json').read_text(),flush=True)


def main():
    a=argparse.ArgumentParser(__doc__);a.add_argument('stage',choices=('ledger','scenarios','summary','fit','check'));a.add_argument('--workers',type=int,choices=(1,2),default=2);a.add_argument('--smoke',action='store_true');args=a.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0','Set PYTHONHASHSEED=0'
    OUT.mkdir(parents=True,exist_ok=True)
    if args.stage=='ledger':ledger(args.workers,args.smoke)
    elif args.stage=='scenarios':scenarios()
    elif args.stage=='summary':summarise_ledger()
    elif args.stage=='fit':fit()
    else:check()

if __name__=='__main__':main()

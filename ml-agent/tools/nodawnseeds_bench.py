"""Package H: exact compare_day CLI previews and native seed accounting. At most two workers.
python tools/nodawnseeds_bench.py preview [--smoke] [--repeat] --workers 2
python tools/nodawnseeds_bench.py full-seeds --workers 2
All benchmark processes require PYTHONHASHSEED=0; no test replay is opened.
"""
import argparse
from collections import Counter
import copy
import csv
import gzip
import hashlib
import json
from multiprocessing import Pool
import os
from pathlib import Path
import sys
import time
from unittest.mock import patch

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'src'))
from kagml import replay_tables as RT
from kagml.paths import runs
import compare_day as cd
from kagml.preview import pin_weeds
from run_full import gameplay,save,stem

SOURCE=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3'
OUT=runs()/'overnight-h'
CROPS=tuple(cd.SEED_COST)
PLAYERS=('template','template:nodawnseeds')


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def signature():
    paths=[Path(__file__),REPO/'tools/compare_day.py',REPO/'vendor/template_agent/main.py',
           REPO/'agents/template_switches/main.py',REPO/'src/kagml/preview.py',
           REPO/'src/kagml/replay_tables.py',Path(RT.K.__file__)]
    return hashlib.sha256(json.dumps({str(p):sha(p) for p in paths},sort_keys=True).encode()).hexdigest()


def value_change(before,after):
    prices=after['market']['prices'];seat=before['player']
    a,b=before['farms'][seat],after['farms'][seat]
    tiles=lambda f:[t for row in f['tiles'] for t in row if isinstance(t,dict)]
    return round(b['money']-a['money']+cd.goods_value(after['private'],prices)-cd.goods_value(before['private'],prices)
      +cd.on_farm_value(tiles(b),prices)-cd.on_farm_value(tiles(a),prices)
      +cd.assets_at_cost(b,after['private'])-cd.assets_at_cost(a,before['private']))


def measure(rep,seat):
    """Existing D1 engine audit supplies successful market units and plant effects."""
    start=rep['steps'][0][0]['observation']['day']*24+rep['steps'][0][0]['observation']['hour']
    final=rep['steps'][-1][0]['observation']['farms']
    meta=dict(episode=1,created='2026-10-24',**{f'{key}_{p}':value for p in (0,1)
          for key,value in (('reward',final[p]['money']),('sub',0),('team',0),('rating',0.0))})
    tables,check=RT.replay(rep,meta,mode='split-weeds',segment=start>0)
    assert check['reason']=='kept',check
    buys=Counter();plants=Counter();zero_stock_noops=Counter();attempts=Counter()
    for row in tables['market_orders']:
        cmd=json.loads(row['command'])
        if row['seat']==seat and cmd and cmd[0]=='BUY_SEED':
            buys[row['step']%24,cmd[1]]+=row['units']
    stock={};step=None
    for row in tables['unit_actions']:
        if row['seat']!=seat:continue
        if row['step']!=step:
            step=row['step'];stock=dict(rep['steps'][step-start][seat]['observation']['private']['seeds'])
        cmd=json.loads(row['effective_command'])
        if cmd and cmd[0]=='PLANT' and len(cmd)>1 and row['exists']:
            crop=cmd[1];attempts[crop]+=1
            if row['took_effect']:plants[crop]+=1;stock[crop]=stock.get(crop,0)-1
            elif stock.get(crop,0)<=0:zero_stock_noops[crop]+=1
    first,last=[rep['steps'][i][seat]['observation'] for i in (0,-1)]
    for crop in CROPS:
        assert first['private']['seeds'].get(crop,0)+sum(n for (h,c),n in buys.items() if c==crop)-plants[crop]==last['private']['seeds'].get(crop,0),crop
    dawn=[]
    for frame in rep['steps']:
        o=frame[seat]['observation']
        if o['hour']==0:
            tiles=[t for row in o['farms'][seat]['tiles'] for t in row]
            dawn.append(dict(day=o['day'],relative_day=o['day']-first['day'],
                seeds={c:o['private']['seeds'].get(c,0) for c in CROPS},empty=sum(t is None for t in tiles),
                crops=sum(isinstance(t,dict) and t.get('kind')=='PLANT' for t in tiles)))
    days=[]
    for i in range(0,len(rep['steps'])-24,24):
        a,b=[rep['steps'][j][seat]['observation'] for j in (i,i+24)]
        days.append(value_change(a,b))
    return dict(native_check=check,seed_conservation=True,buys=[dict(hour=h,crop=c,units=n) for (h,c),n in sorted(buys.items())],
        planted=dict(plants),plant_attempts=dict(attempts),zero_stock_plant_noops=dict(zero_stock_noops),
        dawn=dawn,daily_value_plus_assets=days,period_value_plus_assets=value_change(first,last))


def case_stem(game,day,turns,name):return f'{game}-d{day}-t{turns}-{name.replace(":","_")}'


def preview_game(job):
    game,days,directory=job
    assert game in range(10301,10320) and os.environ.get('PYTHONHASHSEED')=='0'
    assert os.environ.get('KAGML_NO_DAWN_SEEDS','1')=='1'
    directory=Path(directory);directory.mkdir(parents=True,exist_ok=True)
    sig=signature();source=SOURCE/f'{game}.json';source_sha=sha(source)
    original_run,original_env=cd.run_day,cd.env_from_snapshot
    holder={};made=0
    def capture(snap):
        pin_weeds(True);holder['env']=original_env(snap);return holder['env']
    def tracked(snap,player,replay,day,turns=24,SEAT=0):
        nonlocal made
        name=PLAYERS[1] if 'template_switches' in Path(player.module.__file__).parts else PLAYERS[0]
        key=case_stem(game,day,turns,name);path=directory/(key+'.metrics.json');raw=directory/(key+'.json.gz')
        if path.exists():
            m=json.loads(path.read_text());assert m['signature']==sig and m['source_sha256']==source_sha
            assert sha(raw)==m['replay_sha256'] and not m['policy_errors']['count'];return m['row']
        row=original_run(snap,player,replay,day,turns,SEAT)
        env=holder['env'];env.steps=env.steps[snap['step']:];rep=env.toJSON()
        with gzip.open(raw,'wt',encoding='utf8',compresslevel=1) as f:json.dump(rep,f,separators=(',',':'))
        measurement=measure(rep,SEAT)
        assert measurement['period_value_plus_assets']==row['value_plus_assets']
        assert len(measurement['daily_value_plus_assets'])==turns//24
        assert name!=PLAYERS[1] or not any(r['units'] for r in measurement['buys'] if r['hour']<3 and r['crop'] in ('WHEAT','CARROT'))
        m=dict(game=game,day=day,turns=turns,player=name,seat=SEAT,signature=sig,source_sha256=source_sha,
            replay_sha256=sha(raw),gameplay_sha256=gameplay(rep),policy_errors=dict(player.module.ERRORS),row=row,**measurement)
        save(path,m);assert not m['policy_errors']['count'],m['policy_errors'];made+=1
        return row
    argv=sys.argv[:]
    try:
        with patch.object(cd,'env_from_snapshot',capture),patch.object(cd,'run_day',tracked):
            for turns in (24,72):
                sys.argv=['compare_day.py',f'overnight-h/{directory.name}-{game}-{turns}',str(source),'--players',','.join(PLAYERS),
                          '--days',','.join(map(str,days)),'--turns',str(turns),'--pinned']
                cd.main()
    finally:sys.argv=argv
    return dict(game=game,new_cases=made,cases=len(days)*4)


def full_case(job):
    name,seed,seat,tag=job;assert os.environ.get('PYTHONHASHSEED')=='0'
    directory=OUT/'full';directory.mkdir(parents=True,exist_ok=True)
    key=stem(name,seed,seat);path=directory/(key+'.metrics.json')
    raw=runs()/tag/(key+'.json.gz');sig=signature()
    if path.exists():
        m=json.loads(path.read_text());assert m['signature']==sig and m['replay_sha256']==sha(raw);return key
    with gzip.open(raw,'rt',encoding='utf8') as f:rep=json.load(f)
    m=dict(player=name,game=seed,seat=seat,turns=719,day=0,signature=sig,file=str(raw),replay_sha256=sha(raw),**measure(rep,seat))
    assert name!=PLAYERS[1] or not any(r['units'] for r in m['buys'] if r['hour']<3 and r['crop'] in ('WHEAT','CARROT'))
    save(path,m);return key


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('mode',choices=('preview','full-seeds'))
    ap.add_argument('--smoke',action='store_true');ap.add_argument('--repeat',action='store_true')
    ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    ap.add_argument('--baseline-tag',default='overnight-g-fresh');ap.add_argument('--variant-tag',default='overnight-h-full')
    a=ap.parse_args();assert os.environ.get('PYTHONHASHSEED')=='0';OUT.mkdir(parents=True,exist_ok=True)
    start=time.perf_counter()
    if a.mode=='preview':
        assert not a.repeat or a.smoke
        games=[10301] if a.smoke else list(range(10301,10320));days=[8] if a.smoke else [8,12,16,20,24]
        directory=OUT/('repeats' if a.repeat else 'preview')
        with Pool(a.workers,maxtasksperchild=1) as pool:
            for r in pool.imap(preview_game,[(g,days,str(directory)) for g in games]):print(json.dumps(r),flush=True)
        if a.repeat:
            for p in directory.glob('*.metrics.json'):
                original=json.loads((OUT/'preview'/p.name).read_text());repeat=json.loads(p.read_text())
                assert original['gameplay_sha256']==repeat['gameplay_sha256'],p.name
    else:
        for tag,count in ((a.baseline_tag,96),(a.variant_tag,48)):
            check=json.loads((runs()/tag/'checks.json').read_text());assert check['accepted']==count and check['rejected']==0
        jobs=[(n,s,p,a.baseline_tag if n=='template' else a.variant_tag) for n in PLAYERS for s in range(20001,20025) for p in (0,1)]
        with Pool(a.workers,maxtasksperchild=1) as pool:
            for r in pool.imap(full_case,jobs):print(r,flush=True)
    result=dict(seconds=time.perf_counter()-start,mode=a.mode,smoke=a.smoke,repeat=a.repeat,workers=a.workers,signature=signature())
    save(OUT/f'{a.mode}-{"smoke" if a.smoke else "full"}{"-repeat" if a.repeat else ""}.json',result)
    print(json.dumps(result),flush=True)


if __name__=='__main__':main()

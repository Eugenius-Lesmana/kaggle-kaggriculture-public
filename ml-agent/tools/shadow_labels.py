"""L2 shadow labels. Smoke fourth, template and model:ranker-v1 before the full template run.
python tools/shadow_labels.py --player fourth --smoke --workers 2
python tools/shadow_labels.py --player template --smoke --workers 2
python tools/shadow_labels.py --player model:ranker-v1 --smoke --workers 2
python tools/shadow_labels.py --player template --workers 2
Large outputs stay on the configured data drive; model:<name> uses folder model-<name>.
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
from functools import cache, lru_cache
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import sys
import time

from ownfarm_labels import ROOT, REPO, FIELDS, sha, source, save_json
from kagml.replay_tables import TABLES, SCHEMAS, compact, replay as extract
from kagml.preview import TemplatePlayer, env_from_snapshot, pin_weeds, snapshot_from_replay
from kagml.work_data import job_of, candidates
from compare_day import make_player
import pyarrow as pa
import pyarrow.parquet as pq

LABEL_SCHEMAS = {
 'teacher_actions': [('episode',pa.int64()),('step',pa.int64()),('seat',pa.int64()),('unit',pa.int64()),
    ('x',pa.int64()),('y',pa.int64()),('exists',pa.bool_()),('command',pa.string()),
    ('job',pa.string()),('job_legal',pa.bool_())],
 'teacher_turns': [('episode',pa.int64()),('step',pa.int64()),('action',pa.string()),('milliseconds',pa.float64())],
 'teacher_market_orders': [('episode',pa.int64()),('step',pa.int64()),('order_index',pa.int64()),('command',pa.string())],
}
ALL_TABLES = (*TABLES, *LABEL_SCHEMAS)


def slug(name):
    if name not in ('template','fourth') and not re.fullmatch(r'(model|net):[A-Za-z0-9][A-Za-z0-9_.:-]*',name):  # net: whole-board player (Claude, 2026-10-25)
        raise ValueError('player must be template, fourth, or model:<model name>')
    return name.replace(':','-')


def folders(name):
    key=slug(name)
    return ROOT/'raw/shadow'/key, ROOT/'datasets/shadow'/key, ROOT/'runs/shadow'/key


def valid_action(action):
    if not isinstance(action,dict) or not isinstance(action.get('farmer'),list) or not action['farmer']:
        raise ValueError('missing/invalid farmer action; no fallback is allowed')
    for key in ('hands','market'):
        if key in action and (not isinstance(action[key],list) or any(not isinstance(c,list) or not c for c in action[key])):
            raise ValueError(f'invalid {key} action')


def label_units(obs,action,episode,step):
    farm=obs['farms'][0];positions=[farm['farmer'],*farm['hands']]
    commands=[action['farmer'],*action.get('hands',[])]
    rows=[]
    for unit in range(max(len(positions),len(commands))):
        exists=unit<len(positions)
        x,y=positions[unit] if exists else (None,None)
        command=commands[unit] if unit<len(commands) else ['PASS']
        job=job_of(command,x,y) if exists else None
        legal=(job in candidates(obs,0,unit)) if job is not None else (None if exists else False)
        rows.append(dict(episode=episode,step=step,seat=0,unit=unit,x=x,y=y,exists=exists,
                         command=compact(command),job=compact(job) if job is not None else None,job_legal=legal))
    return rows


@cache
def player_instance(name):
    if name=='fourth':
        # load('fourth') is cached: a second independent actor is essential for self-shadow.
        from kagml.opponents import Opponent
        return Opponent('fourth'),None
    actor=make_player(name)
    return actor,copy.deepcopy(actor.memory())


@lru_cache(maxsize=1)
def warm_memories(path,name):
    recorded,_=source(path)
    actor,initial=player_instance(name)
    actor.restore(copy.deepcopy(initial))
    memories={}
    for step in range(28*24):
        if step%24==0 and step//24>=6:
            memories[step//24]=copy.deepcopy(actor.memory())
        obs=copy.deepcopy(recorded['steps'][step][0]['observation'])
        obs['step']=step
        getattr(actor,'warm_step',actor)(obs,copy.deepcopy(recorded['configuration']))
    memories[28]=copy.deepcopy(actor.memory())
    return memories


def metadata(episode,banks):
    return {'episode':episode,'created':'',**{f'{k}_{p}':-1 for k in ('sub','team','rating') for p in (0,1)},
            **{f'reward_{p}':banks[p] for p in (0,1)}}


def generate(recorded,game,day,name,player,teacher):
    assert player is not teacher, 'player and teacher must have separate memory and RNG'
    pin_weeds(True)
    seed=int(recorded['info']['seed']);episode=int(game)*100+day;start=day*24
    teacher.reset(seed)
    if hasattr(player,'reset'):
        player.reset(seed)
    snap=snapshot_from_replay(recorded,start);env=env_from_snapshot(snap)
    labels={t:[] for t in LABEL_SCHEMAS};differences=market_differences=0
    player_ms=[]
    for step in range(start,start+24):
        obs=copy.deepcopy(env.state[0].observation);obs['step']=step
        begun=time.perf_counter()
        answer=copy.deepcopy(teacher(copy.deepcopy(obs),copy.deepcopy(env.configuration)))
        milliseconds=(time.perf_counter()-begun)*1000
        valid_action(answer)
        begun=time.perf_counter()
        action=copy.deepcopy(player(copy.deepcopy(obs),copy.deepcopy(env.configuration)))
        player_ms.append((time.perf_counter()-begun)*1000)
        valid_action(action)
        different=answer!=action;differences+=different
        market_differences+=answer.get('market',[])!=action.get('market',[])
        if name=='fourth':
            assert not different, f'self-shadow mismatch at {step}'
        labels['teacher_turns'].append(dict(episode=episode,step=step,action=compact(answer),milliseconds=milliseconds))
        labels['teacher_actions'].extend(label_units(obs,answer,episode,step))
        labels['teacher_market_orders'].extend(dict(episode=episode,step=step,order_index=i,command=compact(order))
            for i,order in enumerate(answer.get('market',[])))
        env.step([action,copy.deepcopy(recorded['steps'][step+1][1]['action'])])
    rep=env.toJSON();rep['steps']=rep['steps'][start:]
    rep['shadow']={'game':str(game),'day':day,'seat':0,'player':name,'teacher':'fourth','start_step':start,'turns':24}
    assert rep['info']['seed']==seed and len(rep['steps'])==25
    for p in (0,1):
        assert rep['steps'][0][p]['observation']=={**snap['obs'][p],'step':start}
    for i,frame in enumerate(rep['steps']):
        assert frame[0]['observation']['step']==start+i
        assert [s['status'] for s in frame]==['ACTIVE','ACTIVE']
        if i:assert frame[1]['action']==recorded['steps'][start+i][1]['action']
    diagnostics=teacher.diagnostics()
    assert not diagnostics['fallbacks'] and not diagnostics['search_errors'],diagnostics
    player_diagnostics=player.diagnostics() if hasattr(player,'diagnostics') else {}
    assert not player_diagnostics.get('fallbacks') and not player_diagnostics.get('search_errors'),player_diagnostics
    state=teacher.play._FLOW.get(0,{}) if getattr(teacher,'play',None) else {}
    memory={'keys':sorted(state),'last_step':state.get('step'),'previous_action_matches_player':state.get('act')==action,
            'gate_accumulator_keys':len(state.get('acc',{})),'land_accumulator_keys':len(state.get('land_acc',{}))}
    return rep,labels,dict(teacher_calls=24,diagnostics=diagnostics,player_diagnostics=player_diagnostics,
        action_differences=differences,market_differences=market_differences,player_ms=player_ms,memory=memory)


def verify_labels(rep,labels,episode,name):
    start=rep['shadow']['start_step']
    turns=labels['teacher_turns']
    assert [r['step'] for r in turns]==list(range(start,start+24)) and len(turns)==24
    expected_units=[];expected_orders=[]
    for i,turn in enumerate(turns):
        assert turn['episode']==episode and turn['milliseconds']>=0
        action=json.loads(turn['action']);valid_action(action)
        obs=rep['steps'][i][0]['observation']
        expected_units.extend(label_units(obs,action,episode,start+i))
        expected_orders.extend(dict(episode=episode,step=start+i,order_index=k,command=compact(order))
            for k,order in enumerate(action.get('market',[])))
        if name=='fourth':assert action==rep['steps'][i+1][0]['action'], 'self-shadow does not match executed action'
    assert labels['teacher_actions']==expected_units
    assert labels['teacher_market_orders']==expected_orders
    assert len({(r['episode'],r['step'],r['unit']) for r in expected_units})==len(expected_units)
    return Counter({'job_rows':sum(r['job'] is not None for r in expected_units),
        'legal_job_rows':sum(r['job_legal'] is True for r in expected_units),
        'movement_or_pass_rows':sum(r['job'] is None and r['exists'] for r in expected_units),
        'nonexistent_unit_rows':sum(not r['exists'] for r in expected_units)})


def one(job):
    path,day,name,signature=job
    raw,out,_=folders(name);episode=int(path.stem)*100+day
    target=raw/f'{path.stem}-d{day}.json.gz';receipt=out/'audit'/f'{episode}.json'
    begun=time.perf_counter();result=dict(game=path.stem,day=day,episode=episode,signature=signature)
    try:
        recorded,source_hash=source(path)
        if receipt.exists():
            old=json.loads(receipt.read_bytes())
            if old.get('reason')=='kept' and old.get('signature')==signature and old.get('source_sha256')==source_hash:
                if all(p.is_file() and sha(p)==digest for rel,digest in old['output_hashes'].items() for p in [ROOT/rel]):
                    return {**old,'resumed':True}
        from kagml.opponents import load
        teacher=load('fourth');player,_=player_instance(name)
        if isinstance(player,TemplatePlayer):
            player.restore(copy.deepcopy(warm_memories(path,name)[day]))
        generation=time.perf_counter()
        rep,labels,measurements=generate(recorded,path.stem,day,name,player,teacher)
        generation=time.perf_counter()-generation
        counts=verify_labels(rep,labels,episode,name)
        rep['shadow']['source_sha256']=source_hash
        packed=gzip.compress(compact(rep).encode(),compresslevel=6,mtime=0)
        banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
        extraction=time.perf_counter()
        rows,audit=extract(json.loads(gzip.decompress(packed)),metadata(episode,banks),'split-weeds',segment=True)
        if rows is None:raise ValueError(f'segment reconciliation failed: {audit}')
        result.update(audit,**measurements,label_counts=dict(counts),source_sha256=source_hash,
            generation_seconds=generation,extraction_seconds=time.perf_counter()-extraction,
            teacher_load_seconds=teacher.load_seconds,rows={t:len(v) for t,v in {**rows,**labels}.items()})
        hashes={}
        for table,values in {**rows,**labels}.items():
            dest=out/table/f'{episode}.parquet';tmp=dest.with_suffix('.tmp')
            schema=LABEL_SCHEMAS.get(table,SCHEMAS.get(table))
            pq.write_table(pa.Table.from_pylist(values,schema=pa.schema(schema)),tmp,compression='zstd');tmp.replace(dest)
            hashes[dest.relative_to(ROOT).as_posix()]=sha(dest)
        tmp=target.with_suffix('.tmp');tmp.write_bytes(packed);tmp.replace(target)
        hashes[target.relative_to(ROOT).as_posix()]=sha(target)
        result['output_hashes']=hashes
        result['manifest']=dict(zip(FIELDS,(path.stem,day,0,target.relative_to(ROOT).as_posix(),sha(target),*banks,
            episode,recorded['info']['seed'],day*24,(day+1)*24)))
    except Exception as error:
        import traceback
        result.update(reason='error',error=f'{type(error).__name__}: {error}',traceback=traceback.format_exc())
        for p in [target,*(out/t/f'{episode}.parquet' for t in ALL_TABLES)]:p.unlink(missing_ok=True)
    result['seconds']=time.perf_counter()-begun
    save_json(receipt,result)
    return result


def dependencies(name):
    files=[Path(__file__),REPO/'tools/ownfarm_labels.py',REPO/'tools/compare_day.py',REPO/'vendor/template_agent/main.py',
           *(REPO/'src/kagml'/f'{n}.py' for n in ('preview','opponents','replay_tables','work_data','model_player','work_features'))]
    upstream=ROOT/'opponents/fourth-place/fourth-place-model'
    files+=sorted(upstream.rglob('*.py'))+[upstream/'weights.pt']
    hashes={str(p):sha(p) for p in files}
    versions={p:importlib.metadata.version(p) for p in ('kaggle-environments','torch','numpy','pyarrow','lightgbm')}
    base=hashlib.sha256(compact({'files':hashes,'versions':versions}).encode()).hexdigest()
    if name.startswith('model:'):
        hashes.update({str(p):sha(p) for p in (ROOT/'models'/name.split(':',1)[1]).glob('*') if p.name in ('model.txt','features.json')})
        assert len([p for p in hashes if str(ROOT/'models') in p])==2, 'missing model/features'
    signature=hashlib.sha256(compact({'player':name,'base':base,'files':hashes}).encode()).hexdigest()
    return signature,base,hashes,versions


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--player',default='template');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    ap.add_argument('--source',type=Path,default=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3')
    args=ap.parse_args();slug(args.player)
    paths=sorted(args.source.glob('[0-9]*.json'))
    assert {p.stem for p in paths}=={str(g) for g in range(10301,10325)}, 'expected el3 games 10301-10324'
    signature,base,hashes,versions=dependencies(args.player)
    raw,out,log=folders(args.player)
    for p in (raw,log,*(out/t for t in (*ALL_TABLES,'audit'))):p.mkdir(parents=True,exist_ok=True)
    source_hashes={str(p):sha(p) for p in paths}
    if not args.smoke:
        for name in ('fourth',args.player):
            smoke=json.loads((folders(name)[2]/'smoke.json').read_bytes())
            assert smoke['base_signature']==base and smoke['outcomes']=={'kept':3}, 'run current passing self/player smoke first'
            assert smoke['source_hashes']==source_hashes, 'source recordings changed since smoke'
            if name==args.player:assert smoke['signature']==signature, 'player/model changed since smoke'
    jobs=[(p,d,args.player,signature) for p in paths for d in range(6,29)]
    if args.smoke:jobs=[(paths[0],d,args.player,signature) for d in (6,16,28)]
    begun=time.perf_counter();results=[]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for row in pool.map(one,jobs,chunksize=1):
            results.append(row)
            if row['reason']!='kept' or len(results)%12==0 or len(results)==len(jobs):
                print(compact({'completed':len(results),'total':len(jobs),'seconds':round(time.perf_counter()-begun,2),
                    'outcomes':dict(Counter(r['reason'] for r in results)),**({'error':row['error']} if 'error' in row else {})}),flush=True)
    summary={'player':args.player,'segments':len(results),'workers':args.workers,'seconds':time.perf_counter()-begun,
        'outcomes':dict(Counter(r['reason'] for r in results)),'signature':signature,'base_signature':base,
        'dependency_hashes':hashes,'versions':versions,'source_hashes':source_hashes,
        'rows':dict(sum((Counter(r.get('rows',{})) for r in results),Counter())),
        'label_counts':dict(sum((Counter(r.get('label_counts',{})) for r in results),Counter())),
        'teacher_calls':sum(r.get('teacher_calls',0) for r in results),'resumed':sum(r.get('resumed',False) for r in results),
        'action_differences':sum(r.get('action_differences',0) for r in results),
        'market_differences':sum(r.get('market_differences',0) for r in results),
        'segment_seconds':[dict(game=r['game'],day=r['day'],seconds=r['seconds']) for r in results]}
    save_json(log/('smoke.json' if args.smoke else 'full.json'),summary)
    if summary['outcomes']!={'kept':len(jobs)}:raise SystemExit('Rejected segments; see shadow audit receipts on D:')
    # Smoke manifests are useful to the checker; the full run replaces them atomically.
    manifest=REPO/'manifests'/f'shadow-{slug(args.player)}.csv';tmp=manifest.with_suffix('.tmp')
    with tmp.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(r['manifest'] for r in results)
    tmp.replace(manifest)
    print(compact({k:v for k,v in summary.items() if k not in ('dependency_hashes','source_hashes','segment_seconds')}),flush=True)

if __name__=='__main__':main()

"""Independently reconcile shadow segments, label joins, hashes, and template benchmark cash.
python tools/check_shadow.py --player template [--smoke] [--workers 2]
"""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
import gzip
import hashlib
import json
from pathlib import Path
import statistics
import time

from shadow_labels import (ROOT,REPO,TABLES,ALL_TABLES,folders,slug,source,sha,save_json,metadata,
                           dependencies,verify_labels,LABEL_SCHEMAS,compact,extract)
import pyarrow.parquet as pq

KEYS={'games':('episode',),'market_steps':('episode','step'),'farm_daily':('episode','seat','day','x','y'),
      'unit_actions':('episode','seat','step','unit'),'sales':('episode','seat','step','order_index','product','price'),
      'market_orders':('episode','seat','step','order_index'),'teacher_actions':('episode','step','unit'),
      'teacher_turns':('episode','step'),'teacher_market_orders':('episode','step','order_index')}


def check_one(job):
    row,name,source_dir,signature=job
    _,out,_=folders(name);eid=int(row['episode']);game=str(row['game']);day=int(row['day'])
    assert int(row['seat'])==0 and eid==int(game)*100+day
    path=ROOT/row['file'];audit=json.loads((out/'audit'/f'{eid}.json').read_bytes())
    assert audit['reason']=='kept' and audit['signature']==signature
    assert all(sha(ROOT/p)==digest for p,digest in audit['output_hashes'].items()), 'output SHA256 mismatch'
    assert sha(path)==row['sha256']
    rep=json.loads(gzip.decompress(path.read_bytes()))
    original,source_hash=source(source_dir/f'{game}.json')
    assert audit['source_sha256']==source_hash==rep['shadow']['source_sha256']
    assert rep['info']['seed']==int(row['seed'])==original['info']['seed']
    assert int(row['start_step'])==day*24 and int(row['end_step'])==(day+1)*24 and len(rep['steps'])==25
    assert rep['shadow']['player']==name and rep['shadow']['teacher']=='fourth'
    for seat in (0,1):
        assert rep['steps'][0][seat]['observation']=={**original['steps'][day*24][seat]['observation'],'step':day*24}
    for i,frame in enumerate(rep['steps']):
        assert frame[0]['observation']['step']==day*24+i
        assert frame[0]['observation']['day']*24+frame[0]['observation']['hour']==day*24+i
        assert [s['status'] for s in frame]==['ACTIVE','ACTIVE']
        if i:assert frame[1]['action']==original['steps'][day*24+i][1]['action']
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    assert banks==[float(row[f'end_cash_{s}']) for s in (0,1)]
    rows,reason=extract(rep,metadata(eid,banks),'split-weeds',segment=True)
    assert rows is not None,reason
    actual={t:pq.read_table(out/t/f'{eid}.parquet').to_pylist() for t in ALL_TABLES}
    for table,values in actual.items():
        assert len(values)==audit['rows'][table]
        assert len({tuple(r[k] for k in KEYS[table]) for r in values})==len(values),f'duplicate {table} keys'
        if table in TABLES:assert rows[table]==values, f'native re-extraction differs: {table}'
    counts=verify_labels(rep,{t:actual[t] for t in LABEL_SCHEMAS},eid,name)
    assert dict(counts)==audit['label_counts']
    assert audit['teacher_calls']==24 and not audit['diagnostics']['fallbacks'] and not audit['diagnostics']['search_errors']
    compatibility=audit.get('compatibility')
    if compatibility:
        assert compatibility['approved_by_user'] and compatibility['effective_signature']==signature
        events=compatibility['events']
        marks=pq.read_table(out/'teacher_compatibility'/f'{eid}.parquet').to_pylist()
        assert len(marks)==len(events)==1 and events[0]['step']==623
        assert rep['shadow']['compatibility']['steps']==[e['step'] for e in events]
        for event,mark in zip(events,marks):
            answer=next(r for r in actual['teacher_turns'] if r['step']==event['step'])
            assert json.loads(answer['action'])==event['returned_action']==event['teacher_pre_helper_action']
            assert not event['changed_unit_commands'] and event['added_market_orders']==[]
            assert mark['episode']==eid and mark['step']==event['step'] and mark['original_error']==event['error']
            assert json.loads(mark['returned_action'])==event['returned_action']
            assert json.loads(mark['teacher_pre_helper_action'])==event['teacher_pre_helper_action']
    else:
        assert 'compatibility' not in rep['shadow']
    assert sum(r['seat']==0 and r['took_effect'] for r in rows['unit_actions'])>0
    legal_by_kind=Counter()
    for r in actual['teacher_actions']:
        if r['job'] is not None:
            kind=json.loads(r['job'])[0]
            legal_by_kind[(kind,'legal' if r['job_legal'] else 'illegal')]+=1
    return {'game':game,'day':day,'rows':audit['rows'],'labels':dict(counts),
        'teacher_ms':[r['milliseconds'] for r in actual['teacher_turns']],
        'compatibility_calls':len(compatibility['events']) if compatibility else 0,
        'action_differences':sum(json.loads(r['action'])!=rep['steps'][i+1][0]['action'] for i,r in enumerate(actual['teacher_turns'])),
        'market_differences':audit['market_differences'],'memory':audit['memory'],
        'by_kind':[{'kind':k,'status':s,'rows':v} for (k,s),v in legal_by_kind.items()],
        'cash_change':banks[0]-original['steps'][day*24][0]['observation']['farms'][0]['money'],
        'opponent_cash_change':banks[1]-original['steps'][day*24][0]['observation']['farms'][1]['money']}


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--player',default='template');ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    ap.add_argument('--accepted-only',action='store_true',help='diagnostic validation of accepted receipts from a failed full build; never releases a complete corpus')
    ap.add_argument('--source',type=Path,default=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3')
    args=ap.parse_args();_,out,log=folders(args.player)
    run=json.loads((log/('smoke.json' if args.smoke else 'full.json')).read_bytes())
    signature,base,hashes,versions=dependencies(args.player)
    assert (signature,base,hashes,versions)==(run['signature'],run['base_signature'],run['dependency_hashes'],run['versions'])
    segment_signatures=run.get('segment_signatures',{})
    assert set(segment_signatures)=={str(r['episode']) for r in run.get('repairs',[])}
    for repair in run.get('repairs',[]):
        assert all(sha(Path(p))==v for p,v in repair['compatibility_hashes'].items()),'adapter changed'
        effective=hashlib.sha256(compact({'parent_signature':signature,'compatibility_hashes':repair['compatibility_hashes']}).encode()).hexdigest()
        assert effective==repair['effective_signature']==segment_signatures[str(repair['episode'])]
    manifest=list(csv.DictReader((REPO/f'manifests/shadow-{slug(args.player)}.csv').open()))
    rejected=[]
    if args.accepted_only:
        assert not args.smoke
        receipts=[json.loads(p.read_bytes()) for p in (out/'audit').glob('*.json')]
        manifest=[r['manifest'] for r in receipts if r['reason']=='kept']
        rejected=[{'game':r['game'],'day':r['day'],'error':r.get('error')} for r in receipts if r['reason']!='kept']
        assert len(manifest)==run['outcomes'].get('kept',0) and len(rejected)==run['outcomes'].get('error',0)
    if args.smoke:manifest=[r for r in manifest if r['game']=='10301' and int(r['day']) in (6,16,28)]
    expected={('10301',d) for d in (6,16,28)} if args.smoke else {(str(g),d) for g in range(10301,10325) for d in range(6,29)}
    if args.accepted_only: expected-={(r['game'],int(r['day'])) for r in rejected}
    else: assert run['outcomes']=={'kept':len(expected)},'full build was not complete'
    assert len(manifest)==len(expected) and {(r['game'],int(r['day'])) for r in manifest}==expected
    if not args.smoke:
        for t in ALL_TABLES:assert {p.stem for p in (out/t).glob('*.parquet')}=={str(r['episode']) for r in manifest}
    begun=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results=list(pool.map(check_one,[(r,args.player,args.source,segment_signatures.get(str(r['episode']),signature)) for r in manifest],chunksize=1))
    times=[t for r in results for t in r['teacher_ms']]
    by_kind=Counter()
    for r in results:
        for k in r['by_kind']:by_kind[(k['kind'],k['status'])]+=k['rows']
    benchmark={(r['game'],int(r['day'])):r for r in csv.DictReader((ROOT/'runs/compare/rev24.csv').open()) if r['player']==args.player}
    comparisons=[dict(game=r['game'],day=r['day'],own_delta=r['cash_change']-float(benchmark[r['game'],r['day']]['cash_change']),
        opponent_delta=r['opponent_cash_change']-float(benchmark[r['game'],r['day']]['opp_cash_change'])) for r in results if (r['game'],r['day']) in benchmark]
    assert all(r['own_delta']==r['opponent_delta']==0 for r in comparisons),'benchmark cash changed'
    # Prove corruption is rejected, beyond trusting hashes or generation receipts.
    sample=manifest[0];eid=int(sample['episode']);rep=json.loads(gzip.decompress((ROOT/sample['file']).read_bytes()))
    labels={t:pq.read_table(out/t/f'{eid}.parquet').to_pylist() for t in LABEL_SCHEMAS}
    labels['teacher_actions'][0]['command']=compact(['PASS','corruption'])
    corrupt_rejected=False
    try:verify_labels(rep,labels,eid,args.player)
    except AssertionError:corrupt_rejected=True
    assert corrupt_rejected,'corrupt teacher label accepted'
    rep['steps'][1][0]['observation']['market']['prices']['WHEAT']+=1
    banks=[float(sample[f'end_cash_{s}']) for s in (0,1)]
    rows,reason=extract(rep,metadata(eid,banks),'split-weeds',segment=True)
    assert rows is None and reason['reason']=='state_mismatch','corrupt replay accepted'
    summary={'player':args.player,'accepted_only':args.accepted_only,'rejected':rejected,'segments':len(results),'workers':args.workers,'seconds':time.perf_counter()-begun,
        'compatibility_calls':sum(r['compatibility_calls'] for r in results),
        'teacher_calls':len(times),'teacher_median_ms':statistics.median(times),'teacher_max_ms':max(times),
        'rows':dict(sum((Counter(r['rows']) for r in results),Counter())),
        'label_counts':dict(sum((Counter(r['labels']) for r in results),Counter())),
        'action_differences':sum(r['action_differences'] for r in results),'market_differences':sum(r['market_differences'] for r in results),
        'legality_by_kind':[dict(kind=k,status=s,rows=n) for (k,s),n in sorted(by_kind.items())],
        'benchmark_pairs':len(comparisons),'benchmark_exact_both':sum(r['own_delta']==r['opponent_delta']==0 for r in comparisons),
        'memory_previous_action_matches_player':sum(r['memory']['previous_action_matches_player'] for r in results),
        'checks':['dependency/source/output hashes','snapshot/seed/step/coverage','recorded opponent actions',
                  'all six native tables re-extracted identically','all table primary keys','teacher answers 24/segment',
                  'positions/jobs/candidate legality','full self-shadow actions when player=fourth','no fallbacks/search errors',
                  'benchmark cash exact on available pairs','corrupt teacher label rejected','corrupt replay rejected']}
    save_json(log/('partial-validation.json' if args.accepted_only else 'smoke-validation.json' if args.smoke else 'validation.json'),summary)
    save_json(log/('partial-benchmark.json' if args.accepted_only else 'smoke-benchmark.json' if args.smoke else 'benchmark.json'),comparisons)
    print(json.dumps(summary),flush=True)

if __name__=='__main__':main()

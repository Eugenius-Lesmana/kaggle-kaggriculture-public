"""Independently replay every edge segment and compare all six published tables."""
import argparse
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
import copy
import csv
import gzip
import json
from pathlib import Path
import time

import pyarrow.parquet as pq
from edge_labels import DAYS, PLAYER, LOG, L1, L3, locations, manifest_path, dependencies
from check_takeover import KEYS
from shadow_labels import metadata, compact, valid_action


def check_one(job):
    kind, eid, signature = job
    _, out, _ = locations(kind)
    audit = json.loads((out/'audit'/f'{eid}.json').read_bytes())
    assert audit['reason']=='kept' and audit['signature']==signature
    row = audit['manifest']
    game, day = str(row['game']), int(row['day'])
    hour = int(row.get('H', 0))
    end = 719 if day==29 else (day+1)*24
    assert day in DAYS and 10301 <= int(game) <= 10324
    assert eid == (int(game)*100+day if kind=='l1' else int(game)*10000+day*100+hour)
    assert row['start_step']==day*24 and row['end_step']==end and row['seat']==0
    expected_files = {row['file'], *((out/t/f'{eid}.parquet').relative_to(L1.ROOT).as_posix() for t in L1.TABLES)}
    assert set(audit['output_hashes'])==expected_files
    assert all(L1.sha(L1.ROOT/p)==h for p,h in audit['output_hashes'].items())
    rep = json.loads(gzip.decompress((L1.ROOT/row['file']).read_bytes()))
    assert L1.sha(L1.ROOT/row['file'])==row['sha256']
    source, digest = L1.source(L3.SOURCE/f'{game}.json')
    mark = rep['ownfarm' if kind=='l1' else 'takeover']
    assert mark['source_sha256']==audit['source_sha256']==digest
    assert rep['info']['seed']==row['seed']==source['info']['seed']
    assert len(rep['steps'])==end-day*24+1
    assert mark['game']==game and mark['day']==day and mark['seat']==0
    if kind=='l1':
        assert mark['turns']==end-day*24 and mark['end_step']==end and mark['terminal']==(day==29)
        assert mark['reset_seed']==row['seed']
    else:
        L3.verify_segment(rep, source)
        for key in ('H','takeover_step','start_step','end_step','player','takeover_cash','takeover_cash_1','takeover_state_sha256'):
            assert mark[key]==row[key], key
        assert mark['teacher_reset_seed']==row['seed'] and mark['player']==PLAYER
    for p in (0,1):
        assert rep['steps'][0][p]['observation']=={**source['steps'][day*24][p]['observation'], 'step':day*24}
    for i,frame in enumerate(rep['steps']):
        step = day*24+i
        assert frame[0]['observation']['step']==step
        assert (frame[0]['observation']['day'],frame[0]['observation']['hour'])==divmod(step,24)
        assert [s['status'] for s in frame]==(['DONE','DONE'] if step==719 else ['ACTIVE','ACTIVE'])
        if i:
            assert frame[1]['action']==source['steps'][step][1]['action']
            valid_action(frame[0]['action'])
    teacher_steps = list(range(day*24+hour,end))
    assert audit['teacher_steps']==teacher_steps and audit['teacher_calls']==len(teacher_steps)
    assert len(audit['teacher_ms'])==len(teacher_steps)
    assert not audit['diagnostics']['fallbacks'] and not audit['diagnostics']['search_errors']
    assert mark['compatibility_events']==audit['compatibility_events']
    for event in audit['compatibility_events']:
        assert event['step'] in teacher_steps and event['helper']=='night_room_value' and not event['changed_unit_commands']
        assert event['teacher_pre_helper_action']==event['returned_action']==rep['steps'][event['step']-day*24+1][0]['action']
    if kind=='l3':
        assert len(audit['player_ms'])==hour
    banks = [f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    assert banks==[row['end_cash_0'],row['end_cash_1']]
    rows, reason = L1.extract(rep, metadata(eid,banks),'split-weeds',segment=True)
    assert rows is not None, reason
    for table,values in rows.items():
        assert values==pq.read_table(out/table/f'{eid}.parquet').to_pylist(),table
        assert len(values)==audit['rows'][table]
        keys = [tuple(r[k] for k in KEYS[table]) for r in values]
        assert len(keys)==len(set(keys)),table
    assert len(rows['market_steps'])==len(rep['steps'])
    assert {r['step'] for r in rows['unit_actions'] if r['seat']==0 and r['unit']==0}==set(range(day*24,end))
    assert sum(r['seat']==0 and r['step']>=day*24+hour and r['took_effect'] for r in rows['unit_actions'])>0
    return dict(game=game,day=day,H=hour,teacher_calls=len(teacher_steps),rows=audit['rows'],events=len(audit['compatibility_events']))


def corruption_checks(kind, eid):
    _,out,_=locations(kind)
    receipt=json.loads((out/'audit'/f'{eid}.json').read_bytes())
    rep=json.loads(gzip.decompress((L1.ROOT/receipt['manifest']['file']).read_bytes()))
    banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
    broken=copy.deepcopy(rep)
    broken['steps'][1][0]['observation']['market']['prices']['WHEAT']+=1
    rows,reason=L1.extract(broken,metadata(eid,banks),'split-weeds',segment=True)
    assert rows is None and reason['reason']=='state_mismatch' and reason['field']=='market'
    if kind=='l3':
        source,_=L1.source(L3.SOURCE/f"{receipt['game']}.json")
        for field in ('opponent','takeover_hash','terminal'):
            broken=copy.deepcopy(rep)
            if field=='opponent':broken['steps'][1][1]['action']={'farmer':['CORRUPTION']}
            elif field=='takeover_hash':broken['takeover']['takeover_state_sha256']='corrupted'
            else:broken['steps'][-1][0]['status']='CORRUPTION'
            try:L3.verify_segment(broken,source)
            except AssertionError:pass
            else:raise AssertionError(f'{field} corruption accepted')
    return True


def main():
    ap=argparse.ArgumentParser(__doc__)
    ap.add_argument('--kind',choices=('l1','l3'),required=True)
    ap.add_argument('--smoke',action='store_true')
    ap.add_argument('--workers',type=int,choices=(1,2),default=2)
    args=ap.parse_args()
    _,out,log=locations(args.kind)
    run=json.loads((log/('smoke.json' if args.smoke else 'full.json')).read_bytes())
    signature,hashes,versions=dependencies(args.kind)
    assert signature==run['signature'] and hashes==run['dependency_hashes'] and versions==run['versions']
    assert run['outcomes']=={'kept':run['segments']}
    assert all(L1.sha(Path(p))==h for p,h in run['source_hashes'].items())
    begun=time.perf_counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        results=list(pool.map(check_one,[(args.kind,eid,signature) for eid in run['receipts']],chunksize=4))
    prefix_pairs=0
    if args.kind=='l3':
        groups=defaultdict(list)
        for r in results:groups[r['game'],r['day']].append(r['H'])
        for (game,day),hours in groups.items():
            assert sorted(hours)==list(L3.HOURS)
            frames=[]
            for h in sorted(hours):
                raw=locations('l3')[0]/f'{game}-d{day}-h{h}.json.gz'
                frames.append(json.loads(gzip.decompress(raw.read_bytes()))['steps'])
            for h,short in zip(sorted(hours)[:-1],frames[:-1]):
                assert short[:h+1]==frames[-1][:h+1],(game,day,h)
                prefix_pairs+=1
    if not args.smoke:
        hours=(0,) if args.kind=='l1' else L3.HOURS
        expected={(str(g),d,h) for g in range(10301,10325) for d in DAYS for h in hours}
        assert {(r['game'],r['day'],r['H']) for r in results}==expected
        manifest=list(csv.DictReader(manifest_path(args.kind).open(encoding='utf-8')))
        expected_rows=[json.loads((out/'audit'/f'{eid}.json').read_bytes())['manifest'] for eid in run['receipts']]
        assert manifest==[{k:str(v) for k,v in r.items()} for r in expected_rows]
        for table in L1.TABLES:
            assert {p.stem for p in (out/table).glob('*.parquet')}=={str(eid) for eid in run['receipts']}
    plumbing=json.loads((LOG/'plumbing.json').read_bytes())
    assert plumbing['day6_frames_identical'] and plumbing['day6_six_tables_identical'] and len(plumbing['recorded_terminal'])==24
    assert corruption_checks(args.kind,run['receipts'][0])
    summary=dict(kind=args.kind,segments=len(results),signature=signature,seconds=time.perf_counter()-begun,
        workers=args.workers,teacher_calls=sum(r['teacher_calls'] for r in results),
        compatibility_events=sum(r['events'] for r in results),prefix_pairs=prefix_pairs,
        rows=dict(sum((Counter(r['rows']) for r in results),Counter())),
        checks=['all source/dependency/artifact hashes','exact source dawn states and opponent commands',
                'every native frame and both private states','all six tables re-extracted identically and keys unique',
                'teacher covers every requested turn without fallback','terminal day 24 frames / 23 actions / DONE',
                'day-6 L1 frames and tables identical','24 recorded day-29 replays reproduce source banks and states',
                'market corruption rejected']+(['all four exact model prefixes','opponent/hash/status corruptions rejected'] if args.kind=='l3' else []))
    L1.save_json(log/('smoke-check.json' if args.smoke else 'full-check.json'),summary)
    print(compact(summary),flush=True)


if __name__=='__main__':main()

"""Apply the approved narrow adapter to ONLY el3/10319 day25; seal the mixed-provenance corpus.
python tools/retry_shadow_compat.py
"""
from collections import Counter
import csv
import gzip
import hashlib
import json
from pathlib import Path
import time

from shadow_labels import (ROOT,REPO,FIELDS,folders,sha,save_json,compact,one,dependencies)
from shadow_compat import overflow_guard
from kagml.opponents import load
import pyarrow as pa
import pyarrow.parquet as pq


def main():
    raw,out,log=folders('template');run=json.loads((log/'full.json').read_bytes())
    parent,base,hashes,versions=dependencies('template')
    assert parent==run['signature'] and base==run['base_signature']
    adapter_hashes={str(p):sha(p) for p in (Path(__file__),REPO/'tools/shadow_compat.py')}
    effective=hashlib.sha256(compact({'parent_signature':parent,'compatibility_hashes':adapter_hashes}).encode()).hexdigest()
    receipts=[json.loads(p.read_bytes()) for p in (out/'audit').glob('*.json')]
    untouched={p:d for r in receipts if r['episode']!=1031925 for p,d in r.get('output_hashes',{}).items()}
    assert all(sha(ROOT/p)==d for p,d in untouched.items()),'existing accepted output changed'
    actor=load('fourth');policy=actor.play.POL;original=policy.night_room_value;events=[]
    actor.play.POL.night_room_value=overflow_guard(original,policy.ANIMALS,events)
    begun=time.perf_counter()
    try:
        result=one((REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10319.json',25,'template',effective))
    finally:
        policy.night_room_value=original
    assert result['reason']=='kept',result
    if result.get('resumed'):
        assert result['compatibility']['adapter_hashes']==adapter_hashes
    else:
        assert len(events)==1 and events[0]['step']==623 and events[0]['animal']=='SHEEP',events
        assert events[0]['teacher_pre_helper_action']==events[0]['returned_action']
        result['compatibility']={'parent_signature':parent,'effective_signature':effective,
            'adapter_hashes':adapter_hashes,'approved_by_user':True,'events':events,
            'meaning':'Teacher model/decoder output is unchanged; its optional overflow helper is bypassed only at the recorded unpriced-animal lookup. This is an explicit helper fallback, not a fully unmodified teacher answer.'}
        target=raw/'10319-d25.json.gz';rep=json.loads(gzip.decompress(target.read_bytes()))
        rep['shadow']['compatibility']={'kind':'unpriced-animal-overflow','steps':[623],'audit_episode':1031925}
        packed=gzip.compress(compact(rep).encode(),compresslevel=6,mtime=0)
        tmp=target.with_suffix('.tmp');tmp.write_bytes(packed);tmp.replace(target)
        result['manifest']['sha256']=sha(target)
        result['output_hashes'][target.relative_to(ROOT).as_posix()]=sha(target)
        event_path=out/'teacher_compatibility/1031925.parquet';event_path.parent.mkdir(exist_ok=True)
        schema=pa.schema([('episode',pa.int64()),('step',pa.int64()),('helper',pa.string()),('original_error',pa.string()),
            ('teacher_pre_helper_action',pa.string()),('returned_action',pa.string()),('our_action',pa.string())])
        values=[{'episode':1031925,'step':e['step'],'helper':e['helper'],'original_error':e['error'],
            'teacher_pre_helper_action':compact(e['teacher_pre_helper_action']),'returned_action':compact(e['returned_action']),
            'our_action':e['our_action']} for e in events]
        tmp=event_path.with_suffix('.tmp');pq.write_table(pa.Table.from_pylist(values,schema=schema),tmp,compression='zstd');tmp.replace(event_path)
        result['output_hashes'][event_path.relative_to(ROOT).as_posix()]=sha(event_path)
        result['rows']['teacher_compatibility']=1
        save_json(out/'audit/1031925.json',result)
    assert all(sha(ROOT/p)==d for p,d in untouched.items()),'adapter changed one of the other 551 segments'
    receipts=[json.loads(p.read_bytes()) for p in (out/'audit').glob('*.json')]
    assert len(receipts)==552 and all(r['reason']=='kept' for r in receipts)
    assert all(r['signature']==(effective if r['episode']==1031925 else parent) for r in receipts)
    assert {(int(r['game']),r['day']) for r in receipts}=={(g,d) for g in range(10301,10325) for d in range(6,29)}
    if not (log/'unmodified-full.json').exists():save_json(log/'unmodified-full.json',run)
    run.update(outcomes={'kept':552},segments=552,repairs=[{'episode':1031925,'effective_signature':effective,
        'compatibility_hashes':adapter_hashes,'seconds':time.perf_counter()-begun,'calls_bypassed':1}],
        segment_signatures={'1031925':effective},unmodified_outcomes={'kept':551,'error':1},
        teacher_calls=sum(r['teacher_calls'] for r in receipts),
        rows=dict(sum((Counter(r['rows']) for r in receipts),Counter())),
        label_counts=dict(sum((Counter(r['label_counts']) for r in receipts),Counter())),
        action_differences=sum(r['action_differences'] for r in receipts),
        market_differences=sum(r['market_differences'] for r in receipts))
    save_json(log/'full.json',run)
    manifest=REPO/'manifests/shadow-template.csv';tmp=manifest.with_suffix('.tmp')
    with tmp.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=FIELDS);w.writeheader();w.writerows(r['manifest'] for r in sorted(receipts,key=lambda r:r['episode']))
    tmp.replace(manifest)
    summary={'episode':1031925,'resumed':result.get('resumed',False),'seconds':time.perf_counter()-begun,
        'unchanged_other_segments':551,'unchanged_output_files':len(untouched),'compatibility':result['compatibility']}
    save_json(log/'repair.json',summary)
    print(compact({k:v for k,v in summary.items() if k!='compatibility'}))

if __name__=='__main__':main()

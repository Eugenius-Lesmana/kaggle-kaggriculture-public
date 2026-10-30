"""Measure the unmodified teacher's previous-action assumption without rewriting labels.
Run after the shadow build, not alongside its two workers:
python tools/check_shadow_memory.py
"""
from collections import Counter
import csv
import gzip
import json
from pathlib import Path

from shadow_labels import ROOT,REPO,folders,slug,sha,save_json
from kagml.opponents import load
import pyarrow.parquet as pq

actor=load('fourth')
with actor._imports():
    import extract_features
    own_flows=extract_features.own_flows
    decoder_settings={k:actor.play._NET.get(k,actor.play.DECODE_DEFAULTS[k]) for k in ('gate_rate','land_rate')}

for name in ('fourth','template','model:ranker-v1'):
    _,out,log=folders(name)
    manifest=list(csv.DictReader((REPO/f'manifests/shadow-{slug(name)}.csv').open()))
    complete=False
    if (log/'full.json').exists():
        run=json.loads((log/'full.json').read_bytes())
        complete=run['outcomes']=={'kept':552}
        if not complete:
            receipts=[json.loads(p.read_bytes()) for p in (out/'audit').glob('*.json')]
            manifest=[r['manifest'] for r in receipts if r['reason']=='kept' and r['signature']==run['signature']]
            assert len(manifest)==run['outcomes'].get('kept',0)
    total=affected=action_mismatch=market_mismatch=0
    differences=Counter();examples=[]
    for row in manifest:
        eid=int(row['episode'])
        rep=json.loads(gzip.decompress((ROOT/row['file']).read_bytes()))
        turns=pq.read_table(out/'teacher_turns'/f'{eid}.parquet').to_pylist()
        # The first answer has no earlier segment-local observation/action pair.
        for i in range(1,24):
            previous,current=rep['steps'][i-1][0]['observation'],rep['steps'][i][0]['observation']
            shadow=json.loads(turns[i-1]['action']);actual=rep['steps'][i][0]['action']
            total+=1;action_mismatch+=shadow!=actual
            market_mismatch+=shadow.get('market',[])!=actual.get('market',[])
            def estimate(action):
                return own_flows([{0:{'observation':previous}},{0:{'observation':current,'action':action}}],1,0)
            proposed_flows,proposed_buys=estimate(shadow)
            executed_flows,executed_buys=estimate(actual)
            delta={g:proposed_flows[g]-executed_flows[g] for g in proposed_flows if proposed_flows[g]!=executed_flows[g]}
            bought_delta={g:proposed_buys[g]-executed_buys[g] for g in proposed_buys if proposed_buys[g]!=executed_buys[g]}
            if delta or bought_delta:
                affected+=1
                differences.update({g:abs(v) for g,v in delta.items()})
                if len(examples)<4:
                    examples.append({'episode':eid,'observed_step':int(row['start_step'])+i,
                                     'flow_delta_proposed_minus_executed':delta,'purchase_delta':bought_delta})
    if name=='fourth':assert affected==action_mismatch==market_mismatch==0
    result={'player':name,'complete_corpus':complete,'decoder_memory_settings':decoder_settings,'segments':len(manifest),'within_segment_transitions':total,
        'previous_full_action_disagreements':action_mismatch,'previous_market_disagreements':market_mismatch,
        'flow_estimate_disagreements':affected,'flow_estimate_disagreement_fraction':affected/total,
        'absolute_estimate_difference_units_by_product':dict(differences),'examples':examples,
        'upstream_sources':{str(p):sha(p) for p in (actor.root/'play.py',actor.root/'bc_train.py',actor.root/'extract_features.py')},
        'meaning':'Same actual observation pair, upstream own_flows called once with the prior proposed teacher action and once with the prior executed player action. Differences isolate the previous-action assumption; neither estimate is asserted to be exact native sales. Labels/memory/policy files are unchanged.'}
    save_json(log/'memory-analysis.json',result)
    print(json.dumps({k:v for k,v in result.items() if k not in ('upstream_sources','examples','meaning')}),flush=True)

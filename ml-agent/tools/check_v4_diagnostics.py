"""Independent terminal-bank, CSV, historical M and complete replay-step checks."""
from collections import Counter
import csv
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from v4_diagnostics import OUT,REPO,load,sha
from v4_guard_audit import signature


def main():
    sources=json.loads((OUT/'sources.json').read_text());summary=json.loads((OUT/'summary.json').read_text());data={}
    for c in sources:
        assert sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'];data[c['group'],c['seed'],c['seat']]=json.loads(Path(c['metrics']).read_bytes())
    pairs=[(s,p) for s in range(20001,20025) for p in (0,1)]
    # Independent balanced-pair SE via 24 seed means, using original metrics rather than extracted diagnostics.
    for r in summary['banks']:
        a,b=r['contrast'].split('_minus_');role=r['role'];values=[]
        for seed,seat in pairs:
            av=data[a,seed,seat]['banks'];bv=data[b,seed,seat]['banks'];v=(av[0]-av[1])-(bv[0]-bv[1]) if role=='margin' else av[0 if role=='ours' else 1]-bv[0 if role=='ours' else 1];values.append(v)
        assert abs(float(np.mean(values))-r['mean'])<1e-8;assert abs(float(np.std(np.asarray(values).reshape(24,2).mean(axis=1),ddof=1)/math.sqrt(24))-r['se'])<1e-8
    checks=[];sig=signature();all_logs=[];all_jobs=[]
    for c in json.loads((OUT/'guard-selection.json').read_text()):
        a=load(c['raw']);b=load(OUT/'guard/replays'/f"{c['seed']}-seat{c['seat']}.json.gz");log=load(OUT/'guard'/f"{c['seed']}-seat{c['seat']}.json.gz");assert log['signature']==sig
        canon=lambda x:hashlib.sha256(json.dumps(x['steps'],sort_keys=True,separators=(',',':')).encode()).hexdigest()
        assert canon(a)==canon(b);checks.append(dict(seed=c['seed'],seat=c['seat'],full_steps_sha256=canon(a),gameplay_sha256=log['gameplay_sha256']))
        for r in log['logs']:
            if r['changed']:
                assert r['network']!=r['guard'];act=a['steps'][r['step']+1][c['seat']]['action'];assert r['guard']==(act['farmer'] if r['unit']==0 else act['hands'][r['unit']-1]);all_logs.append(r)
        jobs=[r for r in log['jobs'] if r['intervened']];keys=[(r['day'],r['kind'],r['x'],r['y'],tuple(r['identity'])) for r in jobs];assert len(set(keys))==len(keys)
        assert all(int(r['success'])+int(r['night_loss'])+int(r['target_removed'])==1 for r in jobs);all_jobs.extend(jobs)
    csvrows=lambda name:list(csv.DictReader((REPO/'reports'/name).open()))
    assert len(csvrows('V4DIAG_GUARD_OVERRIDES.csv'))==len(all_logs)==1785
    assert len(csvrows('V4DIAG_GUARD_JOBS.csv'))==len(all_jobs)==762
    assert sum(r['success'] for r in all_jobs)==635 and sum(r['failed_cost_proxy'] for r in all_jobs)==14072
    old=csvrows('MARKET_PRESSURE_HEADLINE.csv');new=csvrows('V4DIAG_MARKET_PRESSURE.csv');matched=0
    for r in new:
        if r['baseline']=='v3fw' and r['band']=='all':
            m=next(x for x in old if x['baseline']=='v3fw' and x['component']==r['product']);assert abs(float(m['bank_loss_contribution_mean'])-float(r['mean']))<1e-8;assert abs(float(m['bank_loss_contribution_se_seed24'])-float(r['se']))<1e-8;matched+=1
    # Five disjoint band means must add to the all-period cash difference for every contrast and role.
    bands=csvrows('V4DIAG_CASH_BANDS.csv')
    for r in bands:
        if r['band']=='all':assert abs(float(r['mean'])-sum(float(x['mean']) for x in bands if x['contrast']==r['contrast'] and x['role']==r['role'] and x['metric']==r['metric'] and x['band']!='all'))<1e-8
    result=dict(source_hashes_checked=len(sources)*2,original_metric_contrasts_checked=len(summary['banks']),full_step_hashes=checks,old_market_pressure_components_matched=matched,overrides_checked=len(all_logs),unique_guard_jobs_checked=len(all_jobs))
    (OUT/'independent-checks.json').write_text(json.dumps(result),encoding='utf-8');print(json.dumps(result),flush=True)

if __name__=='__main__':main()

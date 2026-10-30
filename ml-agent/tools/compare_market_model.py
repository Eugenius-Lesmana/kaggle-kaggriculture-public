"""Analysis-only comparison of the independent market GRU and P5 head. No fitting or games."""
import argparse,csv,hashlib,json,os,sys,time
from pathlib import Path
from collections import Counter
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml.board_net import load as load_board,QTY_PLAY,QTY_EDGES
from kagml.market_net import load_model,TOKENS
from train_market_net import manifest,sha
from market_model_diagnostics import matching

def counts(steps,true,pred):
    out=[]
    for token in range(28):
        pp=set(map(int,steps[pred[:,token]>0]));tt=set(map(int,steps[true[:,token]>0]));exact=pp&tt
        out.append(Counter(predicted_orders=len(pp),teacher_orders=len(tt),exact=len(exact),
            within2=len(exact)+matching(pp-tt,tt-pp,2),
            teacher_units=int(true[:,token].sum()),predicted_units=int(np.asarray(QTY_PLAY)[pred[:,token]].sum()),
            quantity_class_hits=int(((pred[:,token]==np.searchsorted(QTY_EDGES,true[:,token],side='right')-1)&(true[:,token]>0)).sum())))
    return out

def derived(s):
    d=dict(s)
    for name in ('exact','within2'):
        d[name+'_precision']=s[name]/max(1,s['predicted_orders']);d[name+'_recall']=s[name]/max(1,s['teacher_orders'])
        d[name+'_f1']=2*s[name]/max(1,s['predicted_orders']+s['teacher_orders'])
    d['unit_ratio']=s['predicted_units']/s['teacher_units'] if s['teacher_units'] else None
    return d

def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--limit',type=int,default=0);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:
        assert matching([1,2],[2,3],1)==2
        y=np.zeros((4,28),int);q=y.copy();y[1,0]=1;y[3,0]=1;q[0,0]=1;q[1,0]=1
        s=counts(np.arange(4),y,q)[0];assert s['exact']==1 and s['within2']==1 # locked exact cannot be reused
        q[0,0]=0;q[2,0]=1;s=counts(np.arange(4),y,q)[0];assert s['within2']==2
        print('Timing and quantity checks passed');return
    assert os.environ.get('PYTHONHASHSEED')=='0';torch.set_num_threads(1);data=Path(os.environ['KAGML_DATA'])
    rows=[r for r in manifest(ROOT/'manifests/market-history.csv') if r['split']=='analysis']
    if a.limit:rows=rows[:a.limit]
    assert rows and all(r['split']=='analysis' for r in rows)
    device='cuda' if torch.cuda.is_available() else 'cpu'
    board=load_board(data/'models/board-p5/model.pt',device).eval();gru,meta=load_model(data/'models/market-gru-v1/model.pt',device)
    cal=json.loads((data/'models/market-gru-v1/calibration.json').read_text());assert cal['split']=='analysis2' and cal['model_sha256']==sha(data/'models/market-gru-v1/model.pt')
    bias=torch.tensor(cal['bias'],device=device)
    names=('board-p5','market-gru-v1-raw','market-gru-v1')
    statistics={scope:{name:[Counter() for _ in range(28)] for name in names} for scope in ('all','live6-28')}
    pending=[];turns=0;started=time.perf_counter()
    def flush():
        nonlocal pending,turns
        if not pending:return
        keys=('tiles','units','position','unit_mask','glob')
        z={k:torch.from_numpy(np.concatenate([p[k] for p in pending])).to(device) for k in keys}
        with torch.inference_mode():
            board.encode(z['tiles'].float(),z['units'].float(),z['position'].long(),z['unit_mask'].bool(),z['glob'].float())
            b=board.market_logits().float()
            h=torch.from_numpy(np.concatenate([p['history'] for p in pending])).to(device)
            x=torch.cat([z['glob'].float(),torch.from_numpy(np.concatenate([p['extra'] for p in pending])).to(device)],-1)
            g=gru(h.float(),x.float()).float();gc=g.clone();gc[:,:,0]+=bias
            logits=(b,g,gc)
            predictions=[]
            for v in logits:
                v[:,18:25,1:]=-torch.inf
                predictions.append(v.argmax(-1).cpu().numpy())
        offset=0
        for p in pending:
            n=len(p['step']);turns+=n
            for scope in statistics:
                mask=np.ones(n,bool) if scope=='all' else ((p['step']//24>=6)&(p['step']//24<=28))
                if not mask.any():continue
                for name,pred in zip(names,predictions):
                    for total,value in zip(statistics[scope][name],counts(p['step'][mask],p['truth'][mask],pred[offset:offset+n][mask])):total.update(value)
            offset+=n
        pending=[]
    for index,r in enumerate(rows):
        for file,key in (('file','sha256'),('worker_file','worker_sha256'),('market_file','market_sha256')):assert sha(data/r[file])==r[key]
        with np.load(data/r['worker_file'],allow_pickle=False) as w,np.load(data/r['file'],allow_pickle=False) as h,np.load(data/r['market_file'],allow_pickle=False) as m:
            step=w['step'];assert np.array_equal(step,h['step']) and np.all(np.diff(step)==1)
            ix={int(t):i for i,t in enumerate(m['step'])}
            p={k:w[k] for k in ('tiles','units','position','unit_mask','glob')}
            p.update(history=h['history'],extra=h['extra'],step=step,truth=m['units_issued'][[ix[int(t)] for t in step]])
            pending.append(p)
        if sum(len(p['step']) for p in pending)>=256:flush()
        if (index+1)%500==0:print(json.dumps(dict(segments=index+1,total=len(rows))),flush=True)
    flush()
    result=dict(passed=True,complete=len(rows)==2590,segments=len(rows),turns=turns,seconds=time.perf_counter()-started,
        device=device,method='Event precision/recall: exact timestamp, or exact matches locked plus one-to-one residual matching within 2 turns in the same contiguous segment. Unit totals use QTY_PLAY, before availability/hire caps and overflow/endmask. Raw predictions, no worker teacher-forcing needed for the P5 market encoder.',
        models={name:sha(data/('models/board-p5/model.pt' if name=='board-p5' else 'models/market-gru-v1/model.pt')) for name in names},
        calibration_sha256=sha(data/'models/market-gru-v1/calibration.json'),manifest_sha256=sha(ROOT/'manifests/market-history.csv'),scopes={},test_contents_read=0,evaluation_arrays_read=0,policy_games_started=0)
    records=[]
    for scope,models in statistics.items():
        result['scopes'][scope]={}
        for name,tokens in models.items():
            total=Counter()
            for token,s in enumerate(tokens):
                total.update(s);records.append(dict(scope=scope,model=name,token=':'.join(TOKENS[token]),**derived(s)))
            total['unit_absolute_error']=sum(abs(s['predicted_units']-s['teacher_units']) for s in tokens)
            d=derived(total);d['unit_absolute_error_ratio']=total['unit_absolute_error']/max(1,total['teacher_units'])
            result['scopes'][scope][name]=dict(overall=d,tokens=[derived(s) for s in tokens])
    gate=json.loads((ROOT/'reports/MARKET_TRAIN_ANALYSIS_GATE.json').read_text())
    base=result['scopes']['live6-28']['board-p5'];candidate=result['scopes']['live6-28']['market-gru-v1'];rules=gate['rules'];reasons=[]
    for metric,tolerance in (('exact_f1',rules['exact_f1_drop_max']),('within2_f1',rules['within2_f1_drop_max'])):
        if candidate['overall'][metric]<base['overall'][metric]-tolerance:reasons.append(metric+' drops more than '+str(tolerance))
    if candidate['overall']['unit_absolute_error_ratio']>base['overall']['unit_absolute_error_ratio']+rules['aggregate_unit_absolute_error_increase_max']:reasons.append('aggregate unit error increases clearly')
    for token in gate['focus_tokens']:
        k=[':'.join(t) for t in TOKENS].index(token);b=base['tokens'][k];c=candidate['tokens'][k]
        if c['teacher_units']>=rules['focus_min_teacher_units'] and abs(c['unit_ratio']-1)>abs(b['unit_ratio']-1)+rules['focus_token_unit_error_increase_max']:reasons.append(token+' unit error increases clearly')
    result['live_gate']=dict(passed=not reasons and result['complete'],reasons=reasons,criteria=gate)
    (ROOT/'reports/MARKET_TRAIN_ANALYSIS_CHECKS.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    with (ROOT/'reports/market-train-analysis-tokens.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    print(json.dumps(dict(complete=result['complete'],seconds=result['seconds'],live_gate=result['live_gate'],comparison={n:d['overall'] for n,d in result['scopes']['live6-28'].items()})),flush=True)
if __name__=='__main__':main()

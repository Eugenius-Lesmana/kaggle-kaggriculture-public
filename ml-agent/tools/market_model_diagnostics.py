"""Read-only market timing diagnostic on analysis shards; no policy calls or fitting."""
import argparse,csv,json,time,os,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml.board_net import load,QTY_EDGES,QTY_PLAY

def matching(p,t,w):
    p=sorted(p);t=sorted(t);i=j=n=0
    while i<len(p) and j<len(t):
        if p[i]<t[j]-w:i+=1
        elif t[j]<p[i]-w:j+=1
        else:n+=1;i+=1;j+=1
    return n

def self_test():
    assert matching([1,2],[2,3],1)==2
    assert matching([1,2,3],[2],2)==1
    assert matching([1],[4],2)==0
    assert matching([],[],2)==0
    assert matching([1,4],[2,3],1)==2
    print('Five one-to-one timing checks passed')

def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--self-test',action='store_true');ap.add_argument('--limit',type=int,default=0);ap.add_argument('--max-seconds',type=float,default=300);ap.add_argument('--output',default='.cache/market-campaign/market-timing.json');a=ap.parse_args()
    if a.self_test:self_test();return
    assert os.environ.get('PYTHONHASHSEED')=='0';torch.set_num_threads(1)
    data=Path(os.environ['KAGML_DATA']);rows=[r for r in csv.DictReader((ROOT/'manifests/turns.csv').open()) if r['split']=='analysis']
    assert all(int(r['game']) not in set(range(10320,10325))|set(range(20001,20049)) for r in rows)
    sides={r['worker_file']:r for r in csv.DictReader((ROOT/'manifests/turn-markets.csv').open()) if r['split']=='analysis'}
    rows=rows[:a.limit] if a.limit else rows;device='cuda' if torch.cuda.is_available() else 'cpu';model=load(data/'models/board-p5/model.pt',device).eval()
    calibration=json.loads((data/'models/board-p5/market-cal.json').read_text());bias=torch.tensor(calibration['bias'],device=device)
    stats={name:{group:Counter() for group in ('all','sell','quantity_event')} for name in ('raw','mcal')};by_token={name:[Counter() for _ in range(28)] for name in stats};clock=Counter();hour=Counter();seen=Counter();files=[];pending=[];pending_n=0;turns=0;started=time.perf_counter();complete=True
    def score(steps,true,logits):
        nonlocal turns
        turns+=len(steps);y=np.searchsorted(QTY_EDGES,true,side='right')-1;truth=true>0
        for i,step in enumerate(steps):
            seen[int(step)%4]+=1
            n=int(truth[i,:9].sum());clock[int(step)%4]+=n;hour[int(step)%24]+=n
        raw=logits.argmax(-1).cpu().numpy();cal=logits.clone();cal[:,:,0]+=bias;preds={'raw':raw,'mcal':cal.argmax(-1).cpu().numpy()}
        for name,pred in preds.items():
            for token in range(28):
                pp=set(map(int,steps[pred[:,token]>0]));tt=set(map(int,steps[truth[:,token]]));exact=pp&tt;fp=pp-tt;fn=tt-pp
                groups=[stats[name]['all'],by_token[name][token]]+([stats[name]['sell']] if token<9 else [])
                for s in groups:
                    s.update(pred=len(pp),teacher=len(tt),exact=len(exact),false_positive=len(fp),false_negative=len(fn),quantity_hit=int(((pred[:,token]==y[:,token])&truth[:,token]).sum()))
                    for w in (1,2):
                        add=matching(fp,fn,w);s['one_to_one_extra_'+str(w)]+=add
                        s['near_pred_'+str(w)]+=sum(any(abs(p-t)<=w for t in tt) for p in pp)
                        s['near_teacher_'+str(w)]+=sum(any(abs(p-t)<=w for p in pp) for t in tt)
                        s['fp_near_teacher_'+str(w)]+=sum(any(abs(p-t)<=w for t in tt) for p in fp)
                        interior={int(v) for v in steps if int(v)-w in set(steps) and int(v)+w in set(steps)}
                        s['interior_pred_'+str(w)]+=len(pp&interior);s['interior_near_pred_'+str(w)]+=sum(any(abs(p-t)<=w for t in tt) for p in pp&interior)
                for cls in set(pred[:,token])|set(y[:,token]):
                    if cls<=0:continue
                    cp=set(map(int,steps[pred[:,token]==cls]));ct=set(map(int,steps[y[:,token]==cls]));ce=cp&ct;q=stats[name]['quantity_event'];q.update(pred=len(cp),teacher=len(ct),exact=len(ce),false_positive=len(cp-ct),false_negative=len(ct-cp))
                    for w in (1,2):q['one_to_one_extra_'+str(w)]+=matching(cp-ct,ct-cp,w)
    def flush():
        nonlocal pending,pending_n
        if not pending:return
        keys=('tiles','units','xy','mask','glob');batch={k:torch.from_numpy(np.concatenate([p[k] for p in pending])).to(device) for k in keys}
        with torch.inference_mode():
            model.encode(batch['tiles'].float(),batch['units'].float(),batch['xy'].long(),batch['mask'].bool(),batch['glob'].float());logits=model.market_logits().float()
        offset=0
        for p in pending:
            n=len(p['step']);score(p['step'],p['truth'],logits[offset:offset+n]);offset+=n
        pending=[];pending_n=0
    for index,r in enumerate(rows):
        if time.perf_counter()-started>a.max_seconds:complete=False;break
        side=sides[r['file']];assert side['split']=='analysis'
        path=data/r['file'];mp=data/side['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256'];assert hashlib.sha256(mp.read_bytes()).hexdigest()==side['sha256']
        with np.load(path,allow_pickle=False) as z,np.load(mp,allow_pickle=False) as m:
            step=z['step'];assert np.all(np.diff(step)==1);where={int(t):i for i,t in enumerate(m['step'])};assert all(int(t) in where for t in step)
            truth=m['units_issued'][[where[int(t)] for t in step]];pending.append(dict(tiles=z['tiles'],units=z['units'],xy=z['position'],mask=z['unit_mask'],glob=z['glob'],step=step,truth=truth));pending_n+=len(step)
        files.append(r['file'])
        if pending_n>=256:flush()
    flush()
    def derived(s):
        d=dict(s);d['precision']=s['exact']/max(1,s['pred']);d['recall']=s['exact']/max(1,s['teacher'])
        for w in (1,2):
            add=s['one_to_one_extra_'+str(w)];d['remaining_error_paired_fraction_'+str(w)]=2*add/max(1,s['false_positive']+s['false_negative'])
            if 'near_pred_'+str(w) in s:d['optimistic_window_precision_'+str(w)]=s['near_pred_'+str(w)]/max(1,s['pred']);d['false_positive_near_teacher_fraction_'+str(w)]=s['fp_near_teacher_'+str(w)]/max(1,s['false_positive']);d['interior_window_precision_'+str(w)]=s['interior_near_pred_'+str(w)]/max(1,s['interior_pred_'+str(w)])
        return d
    result=dict(passed=True,complete=complete and len(files)==len(rows),split='analysis',segments=len(files),expected_segments=len(rows),turns=turns,device=device,seconds=time.perf_counter()-started,method='Teacher-state encoding, FP32 inference, no fitting; windows stay within each contiguous shard; exact matches locked before one-to-one residual matching',stats={n:{g:derived(s) for g,s in groups.items()} for n,groups in stats.items()},by_token={n:[derived(s) for s in ss] for n,ss in by_token.items()},teacher_sell_clock=dict(clock),teacher_sell_hour=dict(hour),clock_exposure=dict(seen),worker_files_sha256=hashlib.sha256('\n'.join(files).encode()).hexdigest(),test_contents_read=0,evaluation_arrays_read=0,policy_games_started=0)
    out=ROOT/a.output;out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,separators=(',',':')),encoding='utf8')
    print(json.dumps({k:result[k] for k in ('complete','segments','turns','device','seconds')},separators=(',',':')),flush=True)
    print(json.dumps({n:{g:v for g,v in groups.items() if g in ('all','sell')} for n,groups in result['stats'].items()},separators=(',',':')),flush=True)
if __name__=='__main__':main()

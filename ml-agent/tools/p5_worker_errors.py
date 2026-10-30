"""Bounded analysis-only worker confusion/target diagnostic. No games or policy calls."""
import argparse,csv,json,time,os,sys,hashlib
from pathlib import Path
from collections import Counter,defaultdict
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml.board_net import load
from kagml import board_features as B
DAYS=('6-11','12-17','18-23','24-28','outside');HOURS=('0-11','12-19','20-23')

def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--limit',type=int,default=0);ap.add_argument('--max-seconds',type=float,default=270);a=ap.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0';torch.set_num_threads(1);data=Path(os.environ['KAGML_DATA']);rows=[r for r in csv.DictReader((ROOT/'manifests/turns.csv').open()) if r['split']=='analysis'];rows=rows[:a.limit] if a.limit else rows
    assert all(int(r['game']) not in set(range(10320,10325))|set(range(20001,20049)) for r in rows)
    device='cuda' if torch.cuda.is_available() else 'cpu';model=load(data/'models/board-p5/model.pt',device).eval();n=len(B.COMMANDS);names=['_'.join(c) for c in B.COMMANDS];ops=np.array([c[0] for c in B.COMMANDS]);moves=np.array([B.MOVES.get(c[0],(0,0)) for c in B.COMMANDS])
    conf=np.zeros((5,3,n,n),np.int64);tn=np.zeros((5,3,n),np.int64);th=tn.copy();missing=tn.copy();contexts=defaultdict(Counter);distances=defaultdict(Counter);pending=[];turns=0;files=[];start=time.perf_counter();cpu=time.process_time();complete=True
    def flush():
        nonlocal pending,turns
        if not pending:return
        z={k:np.concatenate([v[k] for v in pending]) for k in pending[0]};pending=[];turns+=len(z['step'])
        t=lambda k:torch.from_numpy(z[k]).to(device)
        with torch.inference_mode(),torch.autocast('cuda',dtype=torch.bfloat16,enabled=device=='cuda'):
            prev=t('command').long().clamp(min=0).masked_fill(~t('unit_mask').bool(),model.cfg.n_commands)
            out=model(t('tiles').float(),t('units').float(),t('position').long(),t('unit_mask').bool(),t('glob').float(),prev,t('target').long().clamp(0,100))
            pred=out[0].float().masked_fill(~t('legal').bool(),-1e9).argmax(-1).cpu().numpy();target=out[1].float().argmax(-1).cpu().numpy()
        valid=z['unit_mask'].astype(bool)&z['command_loss_mask'].astype(bool);ii,uu=np.where(valid);true=z['command'][ii,uu].astype(int);pp=pred[ii,uu];tt=z['target'][ii,uu].astype(int);pt=target[ii,uu]
        step=z['step'][ii].astype(int);day=step//24;hour=step%24;db=np.full(len(ii),4,int)
        for j,(lo,hi) in enumerate(((6,11),(12,17),(18,23),(24,28))):db[(day>=lo)&(day<=hi)]=j
        hb=np.where(hour<12,0,np.where(hour<20,1,2));np.add.at(conf,(db,hb,true,pp),1)
        tile=(tt>=0)&(tt<100)&(pp==true);np.add.at(tn,(db[tile],hb[tile],true[tile]),1);ok=tile&(pt==tt);np.add.at(th,(db[ok],hb[ok],true[ok]),1);lost=tile&(pt==100);np.add.at(missing,(db[lost],hb[lost],true[lost]),1)
        bad=pp!=true
        if not bad.any():return
        ii,uu,true,pp,tt,day,hour=[x[bad] for x in (ii,uu,true,pp,tt,day,hour)];xy=z['position'][ii,uu].astype(int);tiles=z['tiles'][ii,np.clip(xy[:,1],0,9)*10+np.clip(xy[:,0],0,9)]
        has=(tt>=0)&(tt<100);tx=tt%10;ty=tt//10;dist=np.abs(xy[:,0]-tx)+np.abs(xy[:,1]-ty)
        dt=np.abs(xy[:,0]+moves[true,0]-tx)+np.abs(xy[:,1]+moves[true,1]-ty);dp=np.abs(xy[:,0]+moves[pp,0]-tx)+np.abs(xy[:,1]+moves[pp,1]-ty)
        equivalent=has&np.isin(ops[true],list(B.MOVES))&np.isin(ops[pp],list(B.MOVES))&(dt==dist-1)&(dp==dist-1)
        lowwait=has&(dist>=4)&(hour<20)&(np.maximum(tiles[:,27],tiles[:,28])==0)&(((np.isin(ops[true],list(B.MOVES)))&(ops[pp]=='PASS'))|((ops[true]=='PASS')&np.isin(ops[pp],list(B.MOVES))&(dp<dist)))
        urgent=((ops[true]=='WATER')&(tiles[:,22]>0))|((ops[true]=='FEED')&(tiles[:,25]>0));harvest=(ops[true]=='HARVEST')&(tiles[:,7]>0);wrongcrop=(ops[true]=='PLANT')&(ops[pp]=='PLANT')
        for pair in np.unique(true*n+pp):
            sel=true*n+pp==pair;k=(int(pair//n),int(pair%n));s=contexts[k];s.update(count=int(sel.sum()),target_known=int((sel&has).sum()),equivalent_route=int((sel&equivalent).sum()),low_immediate_risk_wait=int((sel&lowwait).sum()),urgent_missed_water_feed=int((sel&urgent).sum()),missed_held_harvest=int((sel&harvest).sum()),wrong_crop=int((sel&wrongcrop).sum()));distances[k].update(map(int,dist[sel&has]))
    for r in rows:
        if time.perf_counter()-start>a.max_seconds or time.process_time()-cpu>270:complete=False;break
        path=data/r['file'];assert hashlib.sha256(path.read_bytes()).hexdigest()==r['sha256']
        with np.load(path,allow_pickle=False) as z:pending.append({k:z[k] for k in ('tiles','units','position','unit_mask','glob','command','target','legal','command_loss_mask','step')})
        files.append(r['file'])
        if sum(len(p['step']) for p in pending)>=256:flush()
    flush();total=conf.sum();assert total>0;diag=np.diagonal(conf,axis1=2,axis2=3);correct=diag.sum();assert int(total)==sum(int(s.sum()) for s in conf)
    scopes=[('all','all',conf.sum((0,1)),tn.sum((0,1)),th.sum((0,1)),missing.sum((0,1)))]
    scopes += [(DAYS[d],'all',conf[d].sum(0),tn[d].sum(0),th[d].sum(0),missing[d].sum(0)) for d in range(5)]
    scopes += [('all',HOURS[h],conf[:,h].sum(0),tn[:,h].sum(0),th[:,h].sum(0),missing[:,h].sum(0)) for h in range(3)]
    scopes += [(DAYS[d],HOURS[h],conf[d,h],tn[d,h],th[d,h],missing[d,h]) for d in range(5) for h in range(3)]
    statistics=[];cells=[]
    for d,h,cm,nt,ht,mt in scopes:
        for teacher in range(n):
            count=int(cm[teacher].sum());hit=int(cm[teacher,teacher]);statistics.append(dict(day_band=d,hour_band=h,teacher=names[teacher],operator=B.COMMANDS[teacher][0],count=count,correct=hit,accuracy=hit/count if count else None,correct_command_tile_targets=int(nt[teacher]),tile_target_hits=int(ht[teacher]),tile_target_accuracy=float(ht[teacher]/nt[teacher]) if nt[teacher] else None,predicted_no_target=int(mt[teacher])))
            for p in range(n):
                if cm[teacher,p]:cells.append(dict(day_band=d,hour_band=h,teacher=names[teacher],predicted=names[p],count=int(cm[teacher,p])))
    for filename,records in [('p5-worker-command-stats.csv',statistics),('p5-worker-confusions.csv',cells)]:
        with (ROOT/'reports'/filename).open('w',encoding='utf8',newline='') as f:w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    top=[]
    for k,s in sorted(contexts.items(),key=lambda x:-x[1]['count'])[:10]:
        vals=distances[k];known=sum(vals.values());median=None
        if known:
            at=(known-1)//2;running=0
            for value,count in sorted(vals.items()):
                running+=count
                if running>at:median=value;break
        harmless=s['equivalent_route']+s['low_immediate_risk_wait'];label='likely harmless route/delay' if harmless>=s['count']/2 else 'plausibly costly / uncertain'
        if s['urgent_missed_water_feed'] or s['missed_held_harvest'] or s['wrong_crop']:label='plausibly costly'
        top.append(dict(teacher=names[k[0]],predicted=names[k[1]],**dict(s),median_teacher_target_distance=median,risk=label))
    result=dict(passed=True,complete=complete and len(files)==len(rows),analysis_segments=len(files),expected_segments=len(rows),turns=turns,decisions=int(total),correct=int(correct),command_accuracy=float(correct/total),tile_target_given_correct_command_count=int(tn.sum()),tile_target_given_correct_command_hits=int(th.sum()),tile_target_given_correct_command_accuracy=float(th.sum()/max(1,tn.sum())),predicted_no_target_given_correct_command=int(missing.sum()),top_errors=top,seconds=time.perf_counter()-start,cpu_seconds=time.process_time()-cpu,device=device,precision='CUDA bfloat16 autocast, matching train_board_net.evaluate',model_sha256=hashlib.sha256((data/'models/board-p5/model.pt').read_bytes()).hexdigest(),manifest_sha256=hashlib.sha256((ROOT/'manifests/turns.csv').read_bytes()).hexdigest(),test_contents_read=0,evaluation_arrays_read=0,policy_games_started=0,teacher_forcing=True,legal_and_command_loss_masks=True)
    (ROOT/'reports/P5_WORKER_ERROR_CHECKS.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf8');print(json.dumps({k:result[k] for k in ('complete','analysis_segments','turns','decisions','command_accuracy','tile_target_given_correct_command_accuracy','seconds','cpu_seconds')},separators=(',',':')),flush=True)
if __name__=='__main__':main()

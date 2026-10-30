"""Separate market trainer: TRAIN fit, analysis checkpoint, analysis2 calibration.
--smoke only checks <=5 sidecars with forward/backward; it never updates model weights.
"""
import argparse,csv,hashlib,json,math,os,random,sys,tempfile,time
from pathlib import Path
import numpy as np
import torch
from torch.nn import functional as F
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml.market_net import MarketNet,HISTORY_FEATURES,CURRENT_FEATURES,VERSION,load_model,save_model
from kagml.board_net import qty_class
from kagml.paths import data_root,models

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def manifest(path):
    rows=list(csv.DictReader(Path(path).open()))
    if not rows:raise ValueError('empty market-history manifest')
    for r in rows:
        if r['split'] not in ('train','analysis','analysis2') or int(r['game']) in set(range(10320,10325))|set(range(20001,20049)):raise ValueError('test/evaluation data is forbidden')
    return rows

def examples(rows):
    root=data_root()
    for r in rows:
        for file,key in (('file','sha256'),('worker_file','worker_sha256'),('market_file','market_sha256')):
            if sha(root/r[file])!=r[key]:raise ValueError('sidecar/worker/label hash changed')
        with np.load(root/r['file'],allow_pickle=False) as h,np.load(root/r['worker_file'],allow_pickle=False) as w,np.load(root/r['market_file'],allow_pickle=False) as m:
            step=h['step'];assert np.array_equal(step,w['step']);index={int(t):i for i,t in enumerate(m['step'])};target=m['units_issued'][[index[int(t)] for t in step]]
            history=h['history'];current=np.concatenate([w['glob'].astype(np.float32),h['extra'].astype(np.float32)],axis=1)
            assert history.shape==(len(step),24,HISTORY_FEATURES) and current.shape==(len(step),CURRENT_FEATURES)
            yield history.astype(np.float32),current,target.astype(np.int64)

def batches(rows,size,device):
    for h,x,y in examples(rows):
        for start in range(0,len(y),size):yield tuple(torch.from_numpy(v[start:start+size]).to(device) for v in (h,x,y))

def fit_scaling(model,rows):
    if not rows or any(r['split']!='train' for r in rows):raise ValueError('scaling requires TRAIN only')
    sums=[np.zeros(HISTORY_FEATURES,np.float64),np.zeros(CURRENT_FEATURES,np.float64)];sq=[x.copy() for x in sums];count=[0,0]
    for h,x,y in examples(rows):
        valid=h[:,:,-1]>0
        for j,v in enumerate((h[valid],x)):
            sums[j]+=v.sum(0);sq[j]+=(v.astype(np.float64)**2).sum(0);count[j]+=len(v)
    if not all(count):raise ValueError('empty TRAIN scaling input')
    for j,name in enumerate(('history','current')):
        mean=sums[j]/count[j];std=np.sqrt(np.maximum(sq[j]/count[j]-mean**2,0)).clip(min=1)
        if j==0:mean[-1]=0;std[-1]=1
        getattr(model,name+'_mean').copy_(torch.tensor(mean,dtype=torch.float32));getattr(model,name+'_std').copy_(torch.tensor(std,dtype=torch.float32))

@torch.inference_mode()
def evaluate(model,rows,batch,device):
    model.eval();loss=0;n=0;predicted=teacher=both=0
    for h,x,y in batches(rows,batch,device):
        logits=model(h,x);target=qty_class(y).clamp(0,10);loss+=float(F.cross_entropy(logits.reshape(-1,11),target.reshape(-1),reduction='sum'));n+=target.numel();p=logits.argmax(-1)>0;t=y>0;predicted+=int(p.sum());teacher+=int(t.sum());both+=int((p&t).sum())
    if not n:raise ValueError('empty validation selection')
    return dict(loss=loss/n,precision=both/max(1,predicted),recall=both/max(1,teacher),turns=n//28)

def calibration_bias(margins,counts):
    margins=np.asarray(margins);out=[]
    for token,n in enumerate(counts):
        values=np.sort(margins[:,token]);n=int(n)
        if n==0:b=float(values[-1])+1e-4
        elif n==len(values):b=float(values[0])-1e-4
        else:b=float((float(values[-n-1])+float(values[-n]))/2)
        out.append(b)
    return out

@torch.inference_mode()
def calibrate(model,rows,batch,device):
    if not rows or any(r['split']!='analysis2' for r in rows):raise ValueError('calibration requires analysis2 only')
    margins=[];counts=np.zeros(28,np.int64)
    for h,x,y in batches(rows,batch,device):
        logits=model(h,x).float();margins.append((logits[:,:,1:].max(-1).values-logits[:,:,0]).cpu().numpy());counts+=(y>0).sum(0).cpu().numpy()
    values=np.concatenate(margins);bias=calibration_bias(values,counts);predicted=(values>np.asarray(bias)).sum(0);return dict(kind=VERSION,split='analysis2',bias=bias,turns=len(values),teacher_positive=counts.tolist(),predicted_positive=predicted.tolist(),count_error=(predicted-counts).tolist())

def smoke(rows,limit,device):
    if len(rows)>5:raise ValueError('smoke supports at most five segments')
    model=MarketNet().to(device);before={k:v.clone() for k,v in model.state_dict().items()};n=0;start=time.perf_counter()
    for h,x,y in batches(rows,32,device):
        model.zero_grad(set_to_none=True);logits=model(h,x);loss=F.cross_entropy(logits.reshape(-1,11),qty_class(y).clamp(0,10).reshape(-1));loss.backward();assert torch.isfinite(loss);n+=1
        if n>=limit:break
    assert n and all(torch.equal(v,before[k]) for k,v in model.state_dict().items())
    with tempfile.TemporaryDirectory() as folder:
        p=Path(folder)/'model.pt';save_model(p,model,dict(smoke_only=True));restored,meta=load_model(p,device);assert meta['smoke_only'] and all(torch.equal(v,restored.state_dict()[k]) for k,v in model.state_dict().items())
    synthetic=np.tile(np.arange(4,dtype=np.float32)[:,None],(1,28));bias=calibration_bias(synthetic,[2]*28);assert all(b==1.5 for b in bias)
    result=dict(passed=True,batches=n,parameters=sum(p.numel() for p in model.parameters()),device=device,seconds=time.perf_counter()-start,real_optimizer_steps=0,weights_unchanged=True,checkpoint_roundtrip=True,calibration_quantile_check=True,nonzero_weight=1,training=False,segments=len(rows))
    path=ROOT/'.cache/prep/trainer-smoke.json';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(json.dumps(result,separators=(',',':')),encoding='utf8');print(json.dumps(result,separators=(',',':')))

def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('name');p.add_argument('--manifest',default='manifests/market-history.csv');p.add_argument('--epochs',type=int,default=4);p.add_argument('--lr',type=float,default=2e-4);p.add_argument('--batch',type=int,default=128);p.add_argument('--require-cuda',action='store_true');p.add_argument('--smoke',action='store_true');p.add_argument('--smoke-batches',type=int,default=3);p.add_argument('--resume',action='store_true',help='resume this exact run from its last completed epoch');a=p.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0'
    if a.epochs<1 or a.batch<1 or not math.isfinite(a.lr) or a.lr<=0:p.error('epochs, batch and learning rate must be positive')
    torch.set_num_threads(1);torch.manual_seed(0);rows=manifest(ROOT/a.manifest);device='cuda' if torch.cuda.is_available() else 'cpu'
    if a.require_cuda and device!='cuda':p.error('CUDA required')
    if a.smoke:smoke(rows,a.smoke_batches,device);return
    groups={s:[r for r in rows if r['split']==s] for s in ('train','analysis','analysis2')}
    if not all(groups.values()):p.error('nonempty TRAIN, analysis and analysis2 are required')
    families={s:{r.get('family',r['game']) for r in rs} for s,rs in groups.items()}
    if any(families[s]&families[t] for s,t in (('train','analysis'),('train','analysis2'),('analysis','analysis2'))):p.error('parent family leakage across splits')
    if a.name in ('.','..') or Path(a.name).name!=a.name or ':' in a.name:p.error('name must be a model directory name')
    out=models()/a.name
    state_path=out/'training-state.pt'
    inputs=dict(manifest=sha(ROOT/a.manifest),trainer=sha(__file__),market_net=sha(ROOT/'src/kagml/market_net.py'),epochs=a.epochs,lr=a.lr,batch=a.batch,nonzero_weight=1)
    if out.exists() and not (a.resume and state_path.exists()):p.error('model directory exists without a resumable state; refusing overwrite')
    model=MarketNet();start_epoch=0;best=math.inf;log=[]
    if a.resume and state_path.exists():
        state=torch.load(state_path,map_location=device,weights_only=True)
        if state['inputs']!=inputs:p.error('resume inputs changed; refusing repin')
        model=model.to(device);model.load_state_dict(state['model']);start_epoch=state['next_epoch'];best=state['best'];log=state['log']
        optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr);optimizer.load_state_dict(state['optimizer'])
    else:
        fit_scaling(model,groups['train']);model=model.to(device);optimizer=torch.optim.AdamW(model.parameters(),lr=a.lr)
        out.mkdir(parents=True)
    def save_state(next_epoch):
        temporary=state_path.with_suffix('.tmp')
        torch.save(dict(inputs=inputs,model=model.state_dict(),optimizer=optimizer.state_dict(),next_epoch=next_epoch,best=best,log=log),temporary);temporary.replace(state_path)
    if not state_path.exists():save_state(0)
    for epoch in range(start_epoch,a.epochs):
        model.train();order=list(groups['train']);random.Random(epoch).shuffle(order)
        for h,x,y in batches(order,a.batch,device):
            optimizer.zero_grad(set_to_none=True);logits=model(h,x);loss=F.cross_entropy(logits.reshape(-1,11),qty_class(y).clamp(0,10).reshape(-1));loss.backward();optimizer.step()
        validation=evaluate(model,groups['analysis'],a.batch,device);log.append(dict(epoch=epoch+1,analysis=validation));print(json.dumps(log[-1]),flush=True)
        if validation['loss']<best:
            best=validation['loss'];save_model(out/'model.pt',model,dict(smoke_only=False,nonzero_weight=1,checkpoint_split='analysis',scaling_split='train',epoch=epoch+1,inputs=inputs))
        save_state(epoch+1)
    model,meta=load_model(out/'model.pt',device);cal=calibrate(model,groups['analysis2'],a.batch,device);cal['model_sha256']=sha(out/'model.pt');(out/'calibration.json').write_text(json.dumps(cal,separators=(',',':')),encoding='utf8');(out/'report.json').write_text(json.dumps(dict(log=log,calibration=cal,families={k:sorted(v) for k,v in families.items()},nonzero_weight=1,inputs=inputs),separators=(',',':')),encoding='utf8')
if __name__=='__main__':main()

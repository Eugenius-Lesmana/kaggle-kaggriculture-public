"""Small analysis-only history, schema and proposed-model cost probe; no games or fitting."""
from pathlib import Path
from collections import Counter
import csv,gzip,json,time,statistics,sys
import numpy as np
import pyarrow.parquet as pq
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
from kagml import board_features as B
from kagml.paths import data_root

def proposal():
    class Market(torch.nn.Module):
        def __init__(self):
            super().__init__();self.history=torch.nn.GRU(46,64,batch_first=True);self.now=torch.nn.Sequential(torch.nn.Linear(148,64),torch.nn.GELU());self.out=torch.nn.Sequential(torch.nn.Linear(128,128),torch.nn.GELU(),torch.nn.Linear(128,28*11))
        def forward(self,h,x):
            _,last=self.history(h);return self.out(torch.cat([last[-1],self.now(x)],-1)).view(-1,28,11)
    return Market()

def main():
    torch.set_num_threads(1);data=data_root();rows=[r for r in csv.DictReader((ROOT/'manifests/turns.csv').open()) if r['split']=='analysis'];assert rows and all(int(r['game']) not in set(range(10320,10325))|set(range(20001,20049)) for r in rows)
    r=rows[0];raw=data/r['raw_file'];start=time.perf_counter();times=[]
    for _ in range(3):
        t=time.perf_counter()
        with gzip.open(raw,'rt',encoding='utf8') as f:rep=json.load(f)
        times.append(time.perf_counter()-t)
    products=B.PRODUCTS;frames=rep['steps'];steps=np.array([f[0]['observation']['day']*24+f[0]['observation']['hour'] for f in frames]);assert np.all(np.diff(steps)==1)
    with np.load(data/r['file'],allow_pickle=False) as z:
        global_values=z['glob'];worker_steps=z['step'];assert global_values.shape[-1]==len(B.GLOBAL_COLUMNS)==121
        for t,glob in zip(worker_steps,global_values):
            obs=frames[int(t)-int(steps[0])][0]['observation']
            for p in products:
                assert glob[B.GLOBAL_COLUMNS.index(p.lower()+'_price')]==obs['market']['prices'][p]
                assert glob[B.GLOBAL_COLUMNS.index(p.lower()+'_market_stock')]==obs['market']['inventory'][p]
    table=data/'datasets/ownfarm';market_path=table/'market_steps'/f"{r['episode']}.parquet";sales_path=table/'sales'/f"{r['episode']}.parquet";table_times=[]
    for _ in range(3):
        t=time.perf_counter();markets=pq.read_table(market_path).to_pylist();sales=pq.read_table(sales_path).to_pylist();table_times.append(time.perf_counter()-t)
    observed={int(s):f[0]['observation'] for s,f in zip(steps,frames)}
    for row in markets:
        for p in products:
            assert row['price_'+p.lower()]==observed[row['step']]['market']['prices'][p]
            assert row['inventory_'+p.lower()]==observed[row['step']]['market']['inventory'][p]
    history=np.zeros((len(frames),46),np.float32)
    for i,f in enumerate(frames):
        obs=f[0]['observation'];history[i,:9]=[obs['market']['prices'][p] for p in products];history[i,9:18]=[obs['market']['inventory'][p] for p in products]
        if i+1<len(frames):
            action=frames[i+1][0].get('action') or {};sold=Counter()
            for o in action.get('market',[]):
                if o and o[0]=='SELL':sold[o[1]]+=int(o[2])
            history[i,18:27]=[sold[p] for p in products];history[i,27:36]=np.array([frames[i+1][0]['observation']['market']['inventory'][p] for p in products])-history[i,9:18]
        history[i,36:45]=1;history[i,45]=1
    t=time.perf_counter()
    for _ in range(100):
        windows=np.zeros((len(worker_steps),24,46),np.float32)
        for i in range(len(worker_steps)):
            last=history[max(0,i-24):i]
            if len(last):windows[i,-len(last):]=last
    feature_per_turn=(time.perf_counter()-t)/100/len(worker_steps)
    assert not windows[0].any() and windows[1,-1,0]==history[0,0]
    model=proposal().eval();h=torch.zeros(1,24,46);x=torch.zeros(1,148)
    with torch.inference_mode():
        assert model(h,x).shape==(1,28,11)
        for _ in range(5):model(h,x)
        t=time.perf_counter()
        for _ in range(100):model(h,x)
        forward=(time.perf_counter()-t)/100
    hours=Counter();total=0
    for row in rows:
        with np.load(data/row['file'],allow_pickle=False) as z:
            ss=z['step'];hours.update(map(int,ss%24));total+=len(ss)
    assert total==37735
    timing=json.loads((ROOT/'reports/MARKET_MODEL_TIMING_CHECKS.json').read_text());timing['hour_exposure']={str(k):v for k,v in sorted(hours.items())};(ROOT/'reports/MARKET_MODEL_TIMING_CHECKS.json').write_text(json.dumps(timing,separators=(',',':')),encoding='utf8')
    result=dict(passed=True,global_features=[dict(index=i,name=n) for i,n in enumerate(B.GLOBAL_COLUMNS)],sample_game=int(r['game']),sample_episode=int(r['episode']),sample_turns=len(worker_steps),raw_read_decode_seconds_median=statistics.median(times),two_parquet_read_seconds_median=statistics.median(table_times),rolling_window_seconds_per_turn=feature_per_turn,estimated_seconds_440k_raw=(statistics.median(times)/len(worker_steps)+feature_per_turn)*440000,estimated_seconds_440k_tables=(statistics.median(table_times)/len(worker_steps)+feature_per_turn)*440000,history_prefix_cost_included=False,parent_history_copy_required_for_segments=True,exact_opponent_sales_available_in_sample=True,opponent_executed_units_sample=sum(s['units'] for s in sales if s['seat']==1),native_market_price_inventory_parity=True,history_mask_causality_check=True,model_parameters=sum(p.numel() for p in model.parameters()),model_cpu_forward_ms=forward*1000,history_shape=[24,46],static_features=148,quantity_output=[28,11],fp16_sidecar_bytes_440k=(24*46+148)*2*440000,analysis_hour_exposure=dict(sorted(hours.items())),test_contents_read=0,evaluation_arrays_read=0,policy_games_started=0,training=False)
    (ROOT/'reports/MARKET_MODEL_DESIGN_CHECKS.json').write_text(json.dumps(result,separators=(',',':')),encoding='utf8');print(json.dumps({k:v for k,v in result.items() if k not in ('global_features','analysis_hour_exposure')},separators=(',',':')),flush=True)
if __name__=='__main__':main()

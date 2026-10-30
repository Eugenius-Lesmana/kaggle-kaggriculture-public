"""Independent complete-manifest tensor checks; native replay/parity is build_turn_dataset --verify."""
import csv
import json
from collections import Counter
from build_turn_dataset import B,ROOT,REPO,sha,tasks,signature
import numpy as np


def main():
    rows=list(csv.DictReader((REPO/'manifests/turns.csv').open()));expected={(s,int(r['game']),int(r['day']),int(r.get('H',0))):r for s,r in tasks()}
    actual={(r['source'],int(r['game']),int(r['day']),int(r['H'])):r for r in rows}
    assert len(actual)==len(rows) and set(actual)==set(expected),'manifest coverage/duplicates'
    totals=Counter();splits=Counter();sources={};maximum=0
    for i,(key,r) in enumerate(actual.items()):
        upstream=expected[key];cut=int(upstream.get('takeover_step',upstream['start_step']));end=int(upstream['end_step']);n=end-cut
        assert n==int(r['turns']) and r['raw_file']==upstream['file'] and r['raw_sha256']==upstream['sha256']
        assert r['encoder_sha256']==sha(REPO/'src/kagml/board_features.py')
        game=int(r['game']);split='train' if game<=10314 or game>=10401 else ('analysis' if game<=10319 else 'test');assert r['split']==split
        f=ROOT/r['file'];assert sha(f)==r['sha256']
        receipt=json.loads((ROOT/'datasets/turns/audit'/r['source']/f"{game}-d{r['day']}-h{r['H']}.json").read_text());assert receipt['signature']==signature() and receipt['manifest']['sha256']==r['sha256'] and receipt['native_tables']==6
        with np.load(f,allow_pickle=False) as packed:
            a={k:packed[k] for k in packed.files}
            assert a['tiles'].shape==(n,100,len(B.TILE_COLUMNS)) and a['units'].shape==(n,14,len(B.UNIT_COLUMNS)) and a['glob'].shape==(n,len(B.GLOBAL_COLUMNS))
            assert all(np.isfinite(a[k]).all() and a[k].dtype==np.float32 for k in ('tiles','units','glob'))
            mask=a['unit_mask'];assert mask.shape==(n,14) and a['legal'].shape==(n,14,44);np.testing.assert_array_equal(a['step'],np.arange(cut,end))
            count=int(mask.sum());assert count==int(r['worker_decisions']);maximum=max(maximum,int(mask.sum(axis=1).max()))
            assert np.all(a['units'][~mask]==0) and np.all(a['command'][~mask]==-1) and not a['legal'][~mask].any()
            command=a['command'];assert np.all((command[mask]>=0)&(command[mask]<44));chosen=np.take_along_axis(a['legal'],np.maximum(command,0)[...,None],axis=2)[...,0]
            np.testing.assert_array_equal(chosen&mask,a['command_loss_mask']);np.testing.assert_array_equal(mask&(a['took_effect']|(command==0)),a['command_loss_mask'])
            np.testing.assert_array_equal(mask&a['amount_applicable']&a['took_effect']&(a['amount']>=1)&(a['amount']<=5),a['amount_loss_mask'])
            for u in range(14):
                present=np.where(mask[:,u])[0];job=np.array([t for t in present if a['took_effect'][t,u] and B.COMMANDS[int(command[t,u])][0] not in (*B.MOVES,'PASS')],dtype=int)
                for t in present:
                    future=job[job>=t]
                    if not len(future):assert a['target'][t,u]==100 and a['target_step'][t,u]==-1
                    else:
                        j=future[0];x,y=a['position'][j,u];assert a['target'][t,u]==y*10+x and a['target_step'][t,u]==a['step'][j] and a['target_command'][t,u]==command[j,u]
                        assert a['target_distance'][t,u]==np.abs(a['position'][t,u]-a['position'][j,u]).sum()
            totals.update(segments=1,turns=n,worker_decisions=count,bytes=f.stat().st_size,issued_noops=int((mask&~a['command_loss_mask']).sum()),amount_above_5=int((mask&a['amount_applicable']&(a['amount']>5)).sum()))
            splits[split]+=n;sources.setdefault(r['source'],Counter()).update(segments=1,turns=n,worker_decisions=count)
        if (i+1)%1000==0:print(json.dumps({'checked_segments':i+1}),flush=True)
    result=dict(totals=totals,splits=splits,sources=sources,max_units=maximum,manifest_sha256=sha(REPO/'manifests/turns.csv'))
    (ROOT/'runs/turns/complete-checks.json').write_text(json.dumps(result),encoding='utf-8');print(json.dumps(result),flush=True)

if __name__=='__main__':main()

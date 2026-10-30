"""Generate and encode one independent seed family per worker; resume all finished outputs."""
import argparse
import json
from multiprocessing import Pool
import os
import plan_games as G
import plan_dataset as D


def one(row):
    result=G.one(row)
    D.encode_seed((int(row['seed']),row['split'],False,False))
    return result


def publish():
    G.collect()
    selected=G.seed_rows();new=[]
    for r in selected:
        result=json.loads((G.RUN/'encoded-seeds'/f"{r['seed']}-full.json").read_text())
        assert len(result['rows'])==90
        assert all(v['split']==r['split'] and int(v['game'])==int(r['seed']) for v in result['rows'])
        new.extend(result['rows'])
    old=D.read_csv(G.RUN/'original-turns.csv')
    fields=list(D.T.FIELDS)
    G.N.manifest(G.REPO/'manifests/turns.csv',fields,[{k:r[k] for k in fields} for r in old+new])
    D.markets(1)
    G.save(G.RUN/'encoding-full.json',dict(segments=len(new),turns=sum(int(r['turns']) for r in new),worker_decisions=sum(int(r['worker_decisions']) for r in new)))


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('stage',choices=('run','encode','publish'));p.add_argument('--lane',type=int,default=1);p.add_argument('--lanes',type=int,default=2);a=p.parse_args()
    assert os.environ.get('PYTHONHASHSEED')=='0'
    if a.stage=='publish':publish();return
    rows=G.seed_rows()[a.lane::a.lanes]
    with Pool(processes=1,maxtasksperchild=1) as pool:
        if a.stage=='run':result=pool.imap_unordered(one,rows)
        else:result=pool.imap_unordered(D.encode_seed,[(int(r['seed']),r['split'],False,False) for r in rows])
        for i,r in enumerate(result):print(json.dumps(dict(lane=a.lane,completed=i+1,total=len(rows))),flush=True)

if __name__=='__main__':main()

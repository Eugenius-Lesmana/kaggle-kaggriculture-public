"""Independent package P schema, split, preservation and native-label audits."""
from collections import Counter
import copy
import csv
import hashlib
import json
import os
from pathlib import Path
import sys
import unittest

import plan_dataset as D
import plan_games as G
import numpy as np

class MarketLabels(unittest.TestCase):
    def test_partial_failed_repeated_orders_and_noop(self):
        orders=[['SELL','WHEAT',7],['HIRE'],['HIRE'],['BUY_PRODUCT','CARROT',3],['BUY_LAND'],['SELL','TOMATO',1],['BUY_SEED','WHEAT',2]]
        rep={'steps':[[{'observation':{'step':0}},{}],[{'action':{'market':orders}},{}]]}
        executed=[3,1,0,0,1,0,0];attempted=[True]*6+[False];cash=[35,-1,0,0,-1000,0,0]
        native=[dict(step=0,seat=0,order_index=i,command=json.dumps(c),units=executed[i],attempted=attempted[i],took_effect=bool(executed[i]),cash_delta=cash[i]) for i,c in enumerate(orders)]
        sales=[dict(step=0,seat=0,order_index=0,product='WHEAT',units=2,price=12,revenue=24),dict(step=0,seat=0,order_index=0,product='WHEAT',units=1,price=11,revenue=11)]
        a=D.market_arrays(rep,0,[0],native,sales)
        self.assertEqual(a['units_issued'][0,D.VID[('SELL','WHEAT')]],7)
        self.assertEqual(a['units_executed'][0,D.VID[('SELL','WHEAT')]],3)
        self.assertEqual(a['units_issued'][0,D.VID[('HIRE',)]],2)
        self.assertEqual(a['units_executed'][0,D.VID[('HIRE',)]],1)
        self.assertFalse(a['order_valid'][0,3]);self.assertFalse(a['order_attempted'][0,6])
        self.assertEqual(a['sale_revenue'].sum(),35);self.assertTrue(a['buy_land_requested'][0])
        self.assertEqual([json.loads(v) for v in a['order_json'][0]],orders)
        self.assertTrue(all(v.dtype.kind!='O' for v in a.values()))

    def test_seat_one_and_empty_turn(self):
        rep={'steps':[[{'observation':{'step':0}},{}],[{'action':{'market':[['HIRE']]}},{'action':{'market':[]}}]]}
        a=D.market_arrays(rep,1,[0],[],[])
        self.assertEqual(a['order_count'].tolist(),[0]);self.assertFalse(a['order_mask'].any());self.assertEqual(a['seat'].tolist(),[1])
        self.assertEqual(a['units_issued'].shape,(1,28))

    def test_seed_split(self):
        rows=G.seed_rows();self.assertEqual(len(rows),60);self.assertEqual(len({r['seed'] for r in rows}),60)
        self.assertEqual(Counter((r['B'],r['split']) for r in rows),Counter({(str(b),s):n for b in range(3) for s,n in [('train',15),('analysis2',5)]}))
        self.assertFalse({int(r['seed']) for r in rows}&G.TEST)
        self.assertEqual(len({r['pair'] for r in rows if r['B']=='0'}),16)
        self.assertEqual(len({r['pair'] for r in rows if r['B']=='1'}),20)
        self.assertEqual(len({r['pair'] for r in rows if r['B']=='2'}),16)

    def test_physical_seat_metadata(self):
        row=dict(source='tfull',file='datasets/turns/tfull/10501-seat1-d0-h0.npz',episode=10501100)
        self.assertEqual(D.teacher_seat(row),1)
        with self.assertRaises(AssertionError):D.teacher_seat(dict(row,episode=10501000))
        self.assertEqual(D.teacher_seat(dict(source='l1bal')),0)

    def test_access_gate(self):
        for seed in G.TEST:
            with self.assertRaises(AssertionError):D.safe(seed)


def audit():
    rows=D.read_csv(D.REPO/'manifests/turns.csv');markets=D.read_csv(D.REPO/'manifests/turn-markets.csv');seed_split={int(r['seed']):r['split'] for r in G.seed_rows()}
    totals=Counter();counts=Counter();market_counts=Counter();coverage={}
    with (G.RUN/'original-turns.csv').open() as f:original=list(csv.DictReader(f))
    retained=[{k:r[k] for k in original[0]} for r in rows if r['source'] not in ('l1bal','tfull')]
    assert retained==original,'Original manifest rows changed'
    assert len(markets)==sum(int(r['game']) not in G.TEST for r in rows)
    by_game={}
    for n,r in enumerate(rows):
        game=int(r['game'])
        if game in G.TEST:continue
        D.safe(game);worker=D.ROOT/r['file'];assert D.T.sha(worker)==r['sha256']
        by_game.setdefault(game,set()).add(r['split'])
        with np.load(worker,allow_pickle=False) as a:
            count=len(a['step']);assert count==int(r['turns']);assert a['unit_mask'].shape==(count,14)
            assert int(a['unit_mask'].sum())==int(r['worker_decisions'])
            assert a['tiles'].shape==(count,100,31) and a['units'].shape==(count,14,19) and a['glob'].shape==(count,121)
            if r['source'] in ('l1bal','tfull'):
                assert r['split']==seed_split[game]
                assert count==(23 if int(r['day'])==29 else 24)
                np.testing.assert_array_equal(a['step'],np.arange(int(r['day'])*24,int(r['day'])*24+count))
                chosen=np.take_along_axis(a['legal'],np.maximum(a['command'],0)[...,None],axis=2)[...,0]
                np.testing.assert_array_equal(chosen&a['unit_mask'],a['command_loss_mask'])
                assert a['unit_mask'].sum(axis=1).max()<=14
        counts[r['source'],r['split']]+=1;totals[r['source'],r['split']]+=count
        if (n+1)%1000==0:print(json.dumps(dict(stage='check-workers',segments=n+1,total=len(rows))),flush=True)
    worker_index={r['file']:r for r in rows if int(r['game']) not in G.TEST}
    assert len(worker_index)==sum(counts.values())
    assert len({(r['source'],r['game'],r['day'],r['H'],D.teacher_seat(r)) for r in rows})==len(rows)
    for i,r in enumerate(markets):
        safe=D.safe(r['game']);p=D.ROOT/r['file'];assert D.T.sha(p)==r['sha256'];w=worker_index[r['worker_file']]
        assert r['worker_sha256']==w['sha256'] and r['raw_sha256']==w['raw_sha256']
        assert r['source']==w['source'] and int(r['game'])==int(w['game']) and r['split']==w['split'] and int(r['seat'])==D.teacher_seat(w)
        with np.load(p,allow_pickle=False) as a:
            assert len(a['step'])==int(r['turns'])
            np.testing.assert_array_equal(a['step'],np.arange(int(r['day'])*24+int(r['H']),int(r['day'])*24+int(r['H'])+int(r['turns'])))
            assert a['units_issued'].shape==(int(r['turns']),28)
            assert np.isfinite(a['order_cash_delta']).all();assert (a['units_executed']>=0).all()
            assert int(a['order_mask'].sum())==int(r['orders']);assert (a['order_mask'].sum(axis=1)==a['order_count']).all()
            assert (a['order_took_effect']==(a['order_executed']>0)).all()
            assert not (a['order_took_effect']&~a['order_attempted']).any()
            assert int(a['units_executed'].sum())==int(r['executed_units'])
            np.testing.assert_array_equal(a['sale_units']*a['sale_unit_price'],a['sale_revenue'])
            sale_counts=np.zeros_like(a['order_executed']);sale_revenue=np.zeros_like(a['order_cash_delta'])
            sale_t=(a['sale_step']-a['step'][0]).astype(int)
            np.add.at(sale_counts,(sale_t,a['sale_order_index']),a['sale_units'])
            np.add.at(sale_revenue,(sale_t,a['sale_order_index']),a['sale_revenue'])
            sell=a['order_mask']&(a['order_token']>=0)&(a['order_token']<9)
            np.testing.assert_array_equal(sale_counts[sell],a['order_executed'][sell])
            np.testing.assert_array_equal(sale_revenue[sell],a['order_cash_delta'][sell])
            assert not sale_counts[~sell].any()
            for token,entry in enumerate(D.VOCAB):
                key=(r['source'],r['split'],int(r['seat']),token);c=coverage.setdefault(key,Counter());issued=a['order_mask']&(a['order_token']==token)
                c.update(requested_units=int(a['units_issued'][:,token].sum()),executed_units=int(a['units_executed'][:,token].sum()),issued_orders=int(issued.sum()),attempted_orders=int((issued&a['order_attempted']).sum()),effective_orders=int((issued&a['order_took_effect']).sum()))
        market_counts[r['source'],r['split']]+=int(r['turns'])
        if (i+1)%2000==0:print(json.dumps(dict(stage='check-markets',segments=i+1,total=len(markets))),flush=True)
    assert all(len(v)==1 for v in by_game.values())
    family_signatures={json.loads((G.RUN/'seeds'/f'{seed}.json').read_text())['signature'] for seed in seed_split}
    assert len(family_signatures)==1,'Teacher dependencies changed during generation'
    assert G.sha(G.METAV4)==G.N.METAV4_SHA
    full_signatures=set()
    for seed in seed_split:
        family=json.loads((G.RUN/'seeds'/f'{seed}.json').read_text())
        full_signatures.update(r['signature'] for r in [family['template'],*family['full_games']])
    assert full_signatures=={G.F.signature('template',str(G.METAV4))},'Full-game sources changed during generation'
    for source,nper in [('l1bal',30),('tfull',60)]:
        assert counts[source,'train']==45*nper and counts[source,'analysis2']==15*nper
        assert totals[source,'train']==45*(719 if source=='l1bal' else 1438)
        assert totals[source,'analysis2']==15*(719 if source=='l1bal' else 1438)
    assert market_counts==totals
    coverage_rows=[dict(source=s,split=p,seat=seat,token=token,op=D.VOCAB[token][0],item=D.VOCAB[token][1] if len(D.VOCAB[token])>1 else '',**dict(c)) for (s,p,seat,token),c in sorted(coverage.items())]
    D.write_csv(D.REPO/'reports/PLAN_MARKET_COVERAGE.csv',coverage_rows)
    assert G.sha(D.REPO/'src/kagml/board_features.py')==json.loads((G.RUN/'inputs.json').read_text())['board_features_sha256']
    result=dict(passed=True,worker_files_checked=sum(counts.values()),market_files_checked=len(markets),sources=[dict(source=s,split=p,segments=n,turns=totals[s,p]) for (s,p),n in sorted(counts.items())],test_contents_read=0,old_worker_hashes_unchanged=True,analysis2_games=15,workers=2,hashseed=0)
    G.save(G.RUN/'checks.json',result);G.save(D.REPO/'reports/PLAN_DATA_CHECKS.json',result);print(json.dumps(result),flush=True)

if __name__=='__main__':
    if '--audit' in sys.argv:audit()
    else:unittest.main()

"""Small causal/decoder tests, reusing only the five analysis smoke segments."""
import copy,csv,hashlib,io,json,sys,tempfile,unittest
from contextlib import redirect_stderr
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'src'),str(ROOT/'tools')]
from kagml.market_net import MarketNet,MarketPolicy,PRODUCTS,TOKENS,issued_orders,save_model
from kagml import net_player as N
import build_market_history as H
import train_market_net as T
from kagml.paths import data_root

class Pipeline(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(1);cls.data=data_root();cls.rows=list(csv.DictReader((ROOT/'.cache/prep/market-history-smoke.csv').open()));assert 0<len(cls.rows)<=5 and all(r['split']=='analysis' for r in cls.rows)
    def test_causality_opponent_independence_and_reference(self):
        for r in self.rows:
            raw=H.replay(str(self.data/r['raw_file']));parent=H.replay(r['parent_file']);seat=int(r['seat']);first=H.physical(raw['steps'][0],seat)
            with np.load(self.data/r['file'],allow_pickle=False) as z:steps=z['step'];hist=z['history'];extras=z['extra']
            expected,extra=H.history_arrays(raw,parent,seat,steps);np.testing.assert_array_equal(hist,expected);np.testing.assert_array_equal(extras,extra)
            index=len(steps)//2;t=int(steps[index]);rawidx=next(i for i,f in enumerate(raw['steps']) if H.physical(f,seat)==t)
            changed=copy.deepcopy(raw)
            for i in range(rawidx+1,len(changed['steps'])):
                changed['steps'][i][seat]['action']={'farmer':['PASS'],'market':[['SELL','WHEAT',999]]}
                for p in PRODUCTS:changed['steps'][i][seat]['observation']['market']['prices'][p]+=9999
            actual,x=H.history_arrays(changed,parent,seat,steps);np.testing.assert_array_equal(actual[:index+1],hist[:index+1]);np.testing.assert_array_equal(x[:index+1],extras[:index+1])
            changed=copy.deepcopy(raw);other=copy.deepcopy(parent)
            for rep in (changed,other):
                for frame in rep['steps']:
                    frame[1-seat]['action']={'farmer':['PASS'],'market':[['SELL','WOOL',99999]]};frame[1-seat]['observation']['private']['shed']={'WOOL':99999}
            actual,x=H.history_arrays(changed,other,seat,steps);np.testing.assert_array_equal(actual,hist);np.testing.assert_array_equal(x,extras)
            timeline={H.physical(f,seat):f for f in parent['steps'] if H.physical(f,seat)<first};timeline.update({H.physical(f,seat):f for f in raw['steps']})
            direct=np.zeros((24,65),np.float32)
            for q in range(max(0,t-24),t):
                before=timeline[q][seat]['observation'];after=timeline[q+1][seat]['observation'];action=timeline[q+1][seat].get('action')
                if q+1==first:action=parent['steps'][first][seat].get('action')
                own=np.zeros(28,np.float32)
                for order in (action or {}).get('market',[]):
                    key=tuple(order[:1] if order[0] in ('HIRE','BUY_LAND') else order[:2])
                    if key in TOKENS:own[TOKENS.index(key)]+=1 if len(key)==1 else max(0,int(order[2]))
                price=np.array([before['market']['prices'][p] for p in PRODUCTS]);stock=np.array([before['market']['inventory'][p] for p in PRODUCTS]);p2=np.array([after['market']['prices'][p] for p in PRODUCTS]);s2=np.array([after['market']['inventory'][p] for p in PRODUCTS]);flag=(price<=1)|(p2<=1)|(stock<=0)|(s2<=0)|(own[17:26]>0)
                direct[q-t+24]=np.r_[price,stock,own,s2-stock,flag.astype(float),1]
            np.testing.assert_array_equal(direct,hist[index]);self.assertEqual(int(hist[index,:,-1].sum()),min(24,t))
            self.assertEqual(H.sha(self.data/r['worker_file']),r['worker_sha256']);self.assertEqual(H.sha(self.data/r['market_file']),r['market_sha256'])
    def test_duplicate_own_orders_and_shapes(self):
        y=issued_orders({'market':[['SELL','WHEAT',2],['SELL','WHEAT',3],['HIRE'],['HIRE'],['BUY_LAND']]});self.assertEqual(y[0],5);self.assertEqual(y[27],2);self.assertEqual(y[26],1)
        model=MarketNet();self.assertEqual(tuple(model(torch.zeros(2,24,65),torch.zeros(2,148)).shape),(2,28,11))
    def test_train_calibration_split_guards(self):
        with self.assertRaises(ValueError):T.calibrate(MarketNet(),self.rows,32,'cpu')
        with patch.object(sys,'argv',['train_market_net.py','must-not-exist','--manifest','.cache/prep/market-history-smoke.csv']),redirect_stderr(io.StringIO()),self.assertRaises(SystemExit) as error:T.main()
        self.assertEqual(error.exception.code,2)
    def test_synthetic_training_scaling_and_calibration(self):
        h=np.ones((2,24,65),np.float32);x=np.ones((2,148),np.float32);y=np.zeros((2,28),np.int64)
        model=MarketNet()
        with patch.object(T,'examples',lambda rows:iter([(h,x,y)])):
            T.fit_scaling(model,[{'split':'train'}])
            self.assertEqual(float(model.current_mean[0]),1)
            with self.assertRaises(ValueError):T.fit_scaling(model,[{'split':'analysis'}])
        with patch.object(T,'batches',lambda *a:iter([(torch.from_numpy(h),torch.from_numpy(x),torch.from_numpy(y))])):
            cal=T.calibrate(model,[{'split':'analysis2'}],2,'cpu');self.assertEqual(cal['split'],'analysis2');self.assertEqual(len(cal['bias']),28)
        before=model.head[-1].weight.detach().clone();optimizer=torch.optim.AdamW(model.parameters(),lr=2e-4);loss=torch.nn.functional.cross_entropy(model(torch.from_numpy(h),torch.from_numpy(x)).reshape(-1,11),torch.zeros(56,dtype=torch.long));loss.backward();optimizer.step();self.assertFalse(torch.equal(before,model.head[-1].weight))
    def test_model_calibration_checkpoint_binding(self):
        with tempfile.TemporaryDirectory() as folder,patch('kagml.paths.models',return_value=Path(folder)):
            d=Path(folder)/'unit';d.mkdir();save_model(d/'model.pt',MarketNet(),{'smoke_only':False});cal={'split':'analysis2','bias':[0.0]*28,'model_sha256':hashlib.sha256((d/'model.pt').read_bytes()).hexdigest()};(d/'calibration.json').write_text(json.dumps(cal));p=MarketPolicy.load('unit');self.assertEqual(p.bias.shape,(28,))
            cal['split']='analysis';(d/'calibration.json').write_text(json.dumps(cal))
            with self.assertRaises(ValueError):MarketPolicy.load('unit')
            cal['split']='analysis2';cal['model_sha256']='0'*64;(d/'calibration.json').write_text(json.dumps(cal))
            with self.assertRaises(ValueError):MarketPolicy.load('unit')
            save_model(d/'model.pt',MarketNet(),{'smoke_only':True})
            with self.assertRaises(ValueError):MarketPolicy.load('unit')
            with self.assertRaises(ValueError):MarketPolicy.load('..')
    def test_optin_filters_history_and_memory_default(self):
        with np.load(self.data/self.rows[0]['file'],allow_pickle=False) as z:t=int(z['step'][0])
        raw=H.replay(str(self.data/self.rows[0]['raw_file']));seat=int(self.rows[0]['seat']);obs=copy.deepcopy(next(f[seat]['observation'] for f in raw['steps'] if H.physical(f,seat)==t))
        class Board:
            cfg=SimpleNamespace(tile_feats=31,unit_feats=19,glob_feats=121,n_commands=44,market=True)
            def act(self,tiles,units,xy,mask,glob,legal,bias=None):
                n=int(mask.sum());legal(0,[],[]);return [0]*n,[100]*n,[1]*n
            def market_logits(self):
                x=torch.zeros(1,28,11);x[:,:,0]=20;return x
        def init(p,*a,**k):p.module=SimpleNamespace(agent=lambda o,c:{'farmer':['PASS'],'hands':[],'market':[]})
        def policy(name):return MarketPolicy(MarketNet(),[20.0]*28)
        with patch.object(N.TemplatePlayer,'__init__',init),patch.object(N.TemplatePlayer,'memory',lambda p:{'fixture':1}),patch.object(N.TemplatePlayer,'restore',lambda p,m:None),patch.object(N,'load',lambda *a,**k:Board()),patch('kagml.market_net.MarketPolicy.load',side_effect=policy) as loader:
            base=N.NetPlayer('board-p5:market:overflow:endmask:endwork');self.assertIsNone(base.market_policy);self.assertFalse(loader.called);self.assertEqual(len(base.memory()),2)
            p=N.NetPlayer('board-p5:market:overflow:endmask:endwork:mkt=unit');events=[];old=p.market_policy.logits;p.market_policy.logits=lambda g:(events.append('market') or old(g));p._overflow_sell=lambda o,a,n:(events.append('overflow') or a);p._end_mask=lambda o,a:(events.append('endmask') or a)
            p(copy.deepcopy(obs));self.assertTrue(p.endwork);self.assertLess(events.index('market'),events.index('overflow'));self.assertLess(events.index('overflow'),events.index('endmask'));mem=p.memory();self.assertEqual(len(mem),4)
            p2=N.NetPlayer('board-p5:market:mkt=unit');p2.restore(mem);np.testing.assert_array_equal(p2.market_policy.history.sequence(),p.market_policy.history.sequence());self.assertEqual(p2.prev_action,p.prev_action)
            early=copy.deepcopy(obs);early.update(day=0,hour=0);p3=N.NetPlayer('board-p5:mkt=unit');p3(early);early['hour']=1;p3(early);self.assertEqual(p3.market_policy.history.last_step,1)

if __name__=='__main__':
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Pipeline))
    proof=dict(passed=result.wasSuccessful(),tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),segments=len(Pipeline.rows),policy_games_started=0,test_contents_read=0,evaluation_arrays_read=0)
    (ROOT/'reports/MARKET_PIPELINE_CHECKS.json').write_text(json.dumps(proof,separators=(',',':')),encoding='utf8');raise SystemExit(not result.wasSuccessful())

"""Small synthetic checks for epoch recovery and independent-model signature pins."""
import sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import torch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import train_market_net as T
import market_train_live as L
from kagml.market_net import load_model

class Controls(unittest.TestCase):
    def test_resume_replays_only_interrupted_epoch(self):
        torch.set_num_threads(1)
        rows=[dict(split=s,game=str(i),family=str(i)) for i,s in enumerate(('train','analysis','analysis2'),1)]
        def examples(selected):
            for _ in selected:
                h=np.zeros((2,24,65),np.float32);h[:,:,-1]=1
                x=np.ones((2,148),np.float32);y=np.zeros((2,28),np.int64);y[:,0]=1
                yield h,x,y
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);manifest=root/'manifest.csv';manifest.write_text('synthetic')
            def invoke(name,resume=False):
                args=['train_market_net.py',name,'--manifest',str(manifest),'--epochs','4','--batch','2']
                if resume:args+=['--resume']
                with patch.object(sys,'argv',args),patch.object(T,'manifest',return_value=rows),patch.object(T,'examples',examples),patch.object(T,'models',return_value=root),patch.object(torch.cuda,'is_available',return_value=False):T.main()
            real=T.evaluate;calls=0
            def interrupt(*args):
                nonlocal calls
                calls+=1
                if calls==2:raise RuntimeError('synthetic interrupted epoch')
                return real(*args)
            with patch.object(T,'evaluate',interrupt):
                with self.assertRaisesRegex(RuntimeError,'interrupted'):invoke('resumed')
            state=torch.load(root/'resumed/training-state.pt',weights_only=True)
            self.assertEqual(state['next_epoch'],1)
            invoke('resumed',True);invoke('uninterrupted')
            a,_=load_model(root/'resumed/model.pt');b,_=load_model(root/'uninterrupted/model.pt')
            self.assertTrue(all(torch.equal(v,b.state_dict()[k]) for k,v in a.state_dict().items()))
            state=torch.load(root/'resumed/training-state.pt',weights_only=True);self.assertEqual(state['next_epoch'],4)
            manifest.write_text('changed')
            with self.assertRaises(SystemExit):invoke('resumed',True)
    def test_signature_includes_separate_weights_and_calibration(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);d=root/'market-gru-v1';d.mkdir();(d/'model.pt').write_bytes(b'weights');(d/'calibration.json').write_bytes(b'cal1')
            with patch.object(L,'models',return_value=root),patch.object(L,'ORIGINAL_SIGNATURE',return_value='original'):
                self.assertEqual(L.signature(L.BASE,'opponent'),'original');first=L.signature(L.PLAYER,'opponent')
                (d/'calibration.json').write_bytes(b'cal2');self.assertNotEqual(first,L.signature(L.PLAYER,'opponent'))
                second=L.signature(L.PLAYER,'opponent');(d/'model.pt').write_bytes(b'changed');self.assertNotEqual(second,L.signature(L.PLAYER,'opponent'))
if __name__=='__main__':unittest.main()

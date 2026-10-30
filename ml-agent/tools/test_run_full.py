"""Regression checks for full-game evidence and fresh file actors (no model inference)."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from run_full import StrictMeter, actor, gameplay, stem, verify
from check_opponents import SB
from unittest.mock import patch

SOURCE=Path(__file__).resolve().parents[2]/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10301.json'


class Checks(unittest.TestCase):
    def test_fallback_is_rejected(self):
        class Bad:
            module=type('Module',(),{'ERRORS':{'count':1,'last':'probe'}})()
            def __call__(self,o,c):return {'farmer':['PASS'],'hands':[],'market':[]}
        with self.assertRaisesRegex(RuntimeError,'fallback'):
            StrictMeter(Bad())({'day':0,'hour':0}, {})

    def test_fresh_actor_memory(self):
        a,b=actor('template',1),actor('template',1)
        a.module._STATES[0]={'probe':1}
        self.assertEqual(b.module._STATES,{})
        self.assertEqual(stem('file:C:/a/main.py',1,0).count('/'),0)

    def test_receipt_and_action_corruption(self):
        import gzip
        r=json.loads(SOURCE.read_bytes());seat=0
        ours=StrictMeter(lambda o,c:r['steps'][o['day']*24+o['hour']+1][0]['action'])
        theirs=StrictMeter(lambda o,c:r['steps'][o['day']*24+o['hour']+1][1]['action'])
        for f in r['steps'][:-1]:
            ours(f[0]['observation'],r['configuration']);theirs(f[1]['observation'],r['configuration'])
        farms=r['steps'][-1][0]['observation']['farms'];banks=[f['money'] for f in farms]
        shops=r['steps'][144][0]['observation']['town']['unlocked_shops'][:2]
        m=dict(name='template',seed=10301,seat=0,signature='fixture',banks=banks,steps=720,statuses=['DONE','DONE'],
               timing=ours.report(),opponent_timing=theirs.report(),gameplay_sha256=gameplay(r),margin=banks[0]-banks[1],
               win=banks[0]>banks[1],tie=banks[0]==banks[1],early_shops=shops,buyers=sum(s in SB for s in shops),
               diagnostics={'fallbacks':0,'search_errors':0})
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/stem('template',10301,0)
            path=Path(str(target)+'.metrics.json')
            with gzip.open(str(target)+'.json.gz','wt') as f:json.dump(r,f)
            path.write_text(json.dumps(m));self.assertEqual(verify(root,'template',10301,0,'fixture')['banks'],banks)
            for key,value in [('banks',[0,0]),('signature','wrong'),('gameplay_sha256','wrong')]:
                bad=copy.deepcopy(m);bad[key]=value;path.write_text(json.dumps(bad))
                with self.assertRaises(AssertionError):verify(root,'template',10301,0,'fixture')


if __name__=='__main__':unittest.main()

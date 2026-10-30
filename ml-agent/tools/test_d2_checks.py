"""D2 checker regressions using local recorded actions, without published policies."""
import copy
import gzip
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from audit_opponents import verify
from check_opponents import Effects, Meter, SB
from kagml.preview import env_from_snapshot, snapshot_from_replay

SOURCE=Path(__file__).resolve().parents[2]/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10301.json'

class Checks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.replay=json.loads(SOURCE.read_bytes())

    def test_effects_ignore_policy_simulation(self):
        import kaggle_environments.envs.kaggriculture.kaggriculture as K
        env=env_from_snapshot(snapshot_from_replay(self.replay,240))
        with patch.object(K,'_apply_unit_action',side_effect=lambda *a,**kw: None):
            with Effects(0) as effects:
                K._apply_unit_action({'simulator_schema':True},{},0,['PASS'])
                self.assertEqual(dict(effects.counts),{})
        original=K._apply_unit_action
        with Effects(0) as effects:
            env.step([{'farmer':['EAST']},{'farmer':['PASS']}])
            self.assertGreater(sum(effects.counts.values()),0)
        self.assertIs(K._apply_unit_action,original)

    def test_activity_and_corruption(self):
        r=self.replay
        meter=Meter(lambda obs,cfg:r['steps'][obs['day']*24+obs['hour']+1][0]['action'])
        for frame in r['steps'][:-1]:meter(frame[0]['observation'],r['configuration'])
        farms=r['steps'][-1][0]['observation']['farms'];banks=[f['money'] for f in farms]
        shops=r['steps'][144][0]['observation']['town']['unlocked_shops'][:2]
        m=dict(name='fifth-n1',control='metav4',seed=10301,seat=0,steps=720,statuses=['DONE','DONE'],timing=meter.report(),
               banks=banks,margin=banks[0]-banks[1],win=banks[0]>banks[1],tie=banks[0]==banks[1],early_shops=shops,
               buyers=sum(s in SB for s in shops),diagnostics={'fallbacks':0,'search_errors':0},exception_tracing=True,exceptions=[])
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'fifth-n1-metav4-10301-seat0.metrics.json'
            with gzip.open(str(path).replace('.metrics.json','.json.gz'),'wt') as f:json.dump(r,f)
            path.write_text(json.dumps(m))
            self.assertGreater(verify(path,'fifth-n1','metav4',10301,0)['non_pass'],0)
            for field,value in [('seed',10302),('margin',999999),('diagnostics',{'fallbacks':1,'search_errors':0})]:
                bad=copy.deepcopy(m);bad[field]=value;path.write_text(json.dumps(bad))
                with self.assertRaises(AssertionError):verify(path,'fifth-n1','metav4',10301,0)
            bad=copy.deepcopy(m);bad['timing']['daily'][0]['non_pass']+=1;path.write_text(json.dumps(bad))
            with self.assertRaises(AssertionError):verify(path,'fifth-n1','metav4',10301,0)

if __name__=='__main__':unittest.main()


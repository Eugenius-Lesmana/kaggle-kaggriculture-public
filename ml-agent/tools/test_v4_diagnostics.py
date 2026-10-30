"""Independent statistics and guard-accounting regressions; python tools/test_v4_diagnostics.py."""
import copy
import math
import unittest
from unittest.mock import patch
from report_v4_diagnostics import stats,ratio
from v4_guard_audit import cost,summarize,LoggedNetPlayer,NetPlayer


class DiagnosticsTests(unittest.TestCase):
    def test_balanced_seed_se(self):
        r=stats([(1,0,0),(1,1,2),(2,0,4),(2,1,6)])
        self.assertEqual(r['mean'],3);self.assertAlmostEqual(r['se'],2)

    def test_unbalanced_cohort_se(self):
        r=stats([(1,0,0),(1,1,0),(2,0,3)])
        self.assertEqual(r['mean'],1);self.assertAlmostEqual(r['se'],4/3)

    def test_singleton_and_zero_denominator(self):
        self.assertIsNone(stats([(1,0,4)])['se']);self.assertIsNone(ratio([(1,0,0),(2,0,0)])['rate'])
        r=ratio([(1,1,2),(2,2,4)]);self.assertEqual(r['rate'],.5);self.assertEqual(r['se'],0)

    def test_guard_wrapper_is_transparent(self):
        tiles=[[None]*10 for _ in range(10)];tiles[0][0]={'kind':'PLANT','crop':'WHEAT','planted_day':4,'consecutive_unwatered':1,'watered_today':False,'yield_units':3}
        obs={'day':6,'hour':23,'farms':[{'farmer':[0,0],'hands':[],'tiles':tiles},{}],'private':{'inventories':[{}],'shed':{}},'market':{'prices':{'WHEAT':13}}};before=copy.deepcopy(obs)
        normal=object.__new__(NetPlayer);normal.guarding={};logged=object.__new__(LoggedNetPlayer);logged.guarding={};logged.logs=[]
        a=normal._apply_guard(obs,0,[['PASS']]);b=logged._apply_guard(obs,0,[['PASS']]);self.assertEqual(a,b);self.assertEqual(normal.guarding,logged.guarding);self.assertEqual(obs,before);self.assertEqual(logged.logs[0]['network'],['PASS']);self.assertEqual(b,[['WATER']])

    def fixture(self,served):
        tile={'kind':'PLANT','crop':'WHEAT','planted_day':4,'consecutive_unwatered':1,'watered_today':served,'yield_units':3};board=[[None]*10 for _ in range(10)];board[0][0]=tile;dawn=copy.deepcopy(board);dawn[0][0]={'kind':'WEED'}
        rep={'steps':{168:[{'observation':{'farms':[{'tiles':dawn},{}]}}]}};ident=['PLANT','WHEAT',4]
        logs=[dict(day=6,unit=u,kind='WATER',x=0,y=0,identity=ident,step=s,changed=True,network=['PASS'],guard=['WATER']) for s,u in ((166,0),(167,0),(167,1))]
        service=[dict(step=167,seat=0,unit=1,kind='WATER',x=0,y=0,identity=ident)] if served else []
        baseline={'services':service,'nights':[{'day':6,'tiles':[board,[]],'prices':{'WHEAT':13}}]}
        with patch('v4_guard_audit.load',return_value=rep):return summarize({'seat':0,'raw':'fixture'},logs,baseline)

    def test_failed_cost_counted_once_per_job(self):
        episodes,jobs=self.fixture(False);self.assertEqual(len(episodes),2);self.assertEqual(len(jobs),1);self.assertEqual(jobs[0]['failed_cost_proxy'],49);self.assertTrue(jobs[0]['night_loss']);self.assertEqual(jobs[0]['active_turns'],3)

    def test_success_any_worker_not_causal_credit(self):
        episodes,jobs=self.fixture(True);self.assertTrue(jobs[0]['success']);self.assertFalse(jobs[0]['night_loss']);self.assertEqual(jobs[0]['failed_cost_proxy'],0);self.assertFalse(episodes[0]['service_by_assigned_worker']);self.assertTrue(episodes[1]['service_by_assigned_worker'])

if __name__=='__main__':unittest.main()

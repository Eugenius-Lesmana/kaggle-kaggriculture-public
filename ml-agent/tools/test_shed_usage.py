"""S: guard test splits, pickup flow/censoring and native observer cleanup on corrupt input."""
import copy
import gzip
import json
import unittest
from shed_usage import DATA,RT,cases,validate_case,followup,observe,context


def turn(step,op,before,after,*,added=None,used=None,deposit=False):
    return dict(step=step,op=op,before=before,after=after,added=added or {},used=used or {},deposit=deposit,exists=True)


class Checks(unittest.TestCase):
    def test_pickup_use_return_and_censoring(self):
        r=[turn(0,'PICKUP',{}, {'WHEAT':3},added={'WHEAT':3}),
           turn(1,'FEED',{'WHEAT':3},{'WHEAT':2},used={'WHEAT':1}),
           turn(2,'DROP',{'WHEAT':2},{},deposit=True)]
        f=followup(r,0,'WHEAT')
        self.assertEqual((f['first_use_lag'],f['left_before_next_drop'],f['removed_at_next_drop']),(1,2,2))
        self.assertTrue(f['clean_cohort'])
        f=followup(r[:1],0,'WHEAT');self.assertIsNone(f['left_before_next_drop']);self.assertEqual(f['use_censor'],'window')
        r=[turn(0,'PICKUP',{}, {'WHEAT':3}),turn(1,'DROP',{'WHEAT':3},{},deposit=True),
           turn(2,'PICKUP',{}, {'WHEAT':1},added={'WHEAT':1}),turn(3,'FEED',{'WHEAT':1},{},used={'WHEAT':1})]
        f=followup(r,0,'WHEAT');self.assertIsNone(f['first_use_lag']);self.assertEqual(f['use_censor'],'returned')

    def test_tool_use_after_depositing_other_goods(self):
        r=[turn(0,'PICKUP',{'MILK':1}, {'WHEAT':3,'MILK':1}),
           turn(1,'PLACE',{'WHEAT':3,'MILK':1},{'WHEAT':3},deposit=True),
           turn(2,'FEED',{'WHEAT':3},{'WHEAT':2},used={'WHEAT':1})]
        f=followup(r,0,'WHEAT')
        self.assertEqual((f['first_use_lag'],f['next_drop_lag'],f['kept_after_next_drop']),(2,1,3))
        self.assertIsNone(f['use_censor'])

    def test_recorded_prefix_restores_inventory_order(self):
        m=next(m for m in cases() if (m['game'],m['day'],m['H'])==(10302,23,8))
        with gzip.open(DATA/m['file'],'rt',encoding='utf8') as f:rep=json.load(f)
        midpoint=rep['steps'][8][1]['observation']['private']
        native=RT.K.interpreter;changed=[]
        def spy(states,env):
            if states[0].observation.step==m['cutoff']:
                actual=states[1].observation.private
                self.assertEqual(actual,midpoint)
                changed.extend(i for i,(a,b) in enumerate(zip(actual['inventories'],midpoint['inventories'])) if list(a)!=list(b))
            return native(states,env)
        RT.K.interpreter=spy
        try:
            _,check,trace=observe(rep,m['cutoff'],m['episode'])
            self.assertEqual(check['reason'],'kept');self.assertTrue(changed)
            self.assertTrue(all(t['step']>=m['cutoff'] for t in trace))
        finally:RT.K.interpreter=native
        bad=copy.deepcopy(rep);bad['steps']=bad['steps'][8:]
        with self.assertRaises(AssertionError):observe(bad,m['cutoff'],m['episode'])

    def test_observed_overnight_return_resolves_unused_quantity(self):
        r=[turn(20,'PICKUP',{}, {'WHEAT':3}),turn(22,'FEED',{'WHEAT':3},{'WHEAT':2},used={'WHEAT':1}),
           {**turn(24,'NIGHT_RETURN',{'WHEAT':2},{},deposit=True),'deposit_kind':'overnight'}]
        f=followup(r,0,'WHEAT')
        self.assertEqual((f['first_use_lag'],f['next_drop_lag'],f['left_before_next_drop'],f['removed_at_next_drop']),(2,4,2,2))
        self.assertEqual(f['next_drop_kind'],'overnight')
        f=followup([r[0],{**r[2],'before':{'WHEAT':3}}],0,'WHEAT')
        self.assertIsNone(f['first_use_lag']);self.assertEqual(f['use_censor'],'overnight_return')

    def test_replenishment_is_not_a_clean_cohort(self):
        r=[turn(0,'PICKUP',{}, {'FERTILIZER':3}),turn(1,'COLLECT_FERTILIZER',{'FERTILIZER':3},{'FERTILIZER':4},added={'FERTILIZER':1}),
           turn(2,'FERTILIZE',{'FERTILIZER':4},{'FERTILIZER':3},used={'FERTILIZER':1}),turn(3,'DROP',{'FERTILIZER':3},{},deposit=True)]
        f=followup(r,0,'FERTILIZER');self.assertFalse(f['clean_cohort']);self.assertEqual(f['additions_before_next_drop'],1)

    def test_demand_and_other_worker_supplies(self):
        farm={'tiles':[[{'kind':'PASTURE','animal':'COW','fed_today':False},{'kind':'PLANT','fertilized_until_day':5},{'kind':'PASTURE'}],
                       [{'kind':'COOP','animal':'GOOSE','fed_today':True},{'kind':'PLANT','fertilized_until_day':3},None]],'hands':[[0,0],[0,1]]}
        private={'inventories':[{'WHEAT':99},{'WHEAT':2,'FERTILIZER':1},{'WHEAT':1}]}
        c=context(farm,private,0,4)
        self.assertEqual((c['needs']['WHEAT'],c['needs']['FERTILIZER'],c['fert_legal']),(1,1,2))
        self.assertEqual((c['other_qty']['WHEAT'],c['other_workers']['WHEAT']),(3,2))
        self.assertEqual((c['needs']['COW'],c['needs']['SHEEP'],c['needs']['GOOSE']),(1,1,0))

    def test_test_game_and_wrong_cutoff_rejected(self):
        m=cases(True)[0]
        for change in ({'game':10320},{'game':10324},{'cutoff':m['cutoff']-1}):
            with self.assertRaises(AssertionError):validate_case({**m,**change})

    def test_corrupt_replay_rejected_and_hooks_restored(self):
        m=cases(True)[0]
        with gzip.open(DATA/m['file'],'rt',encoding='utf8') as f:r=json.load(f)
        r['steps'][1][0]['observation']['farms'][0]['money']+=1
        original_apply,original_interpreter=RT.ORIGINAL['_apply_unit_action'],RT.K.interpreter
        original_night=RT.K._drop_inventories_to_shed
        with self.assertRaises(AssertionError):observe(r,m['cutoff'],m['episode'])
        self.assertIs(RT.ORIGINAL['_apply_unit_action'],original_apply)
        self.assertIs(RT.K._apply_unit_action,original_apply);self.assertIs(RT.K.interpreter,original_interpreter)
        self.assertIs(RT.K._drop_inventories_to_shed,original_night)


if __name__=='__main__':unittest.main()

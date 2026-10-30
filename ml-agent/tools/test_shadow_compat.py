"""Focused adapter boundaries: no generic KeyError swallowing or price invention."""
import unittest
from shadow_compat import overflow_guard

class GuardTests(unittest.TestCase):
    def test_normal_helper_is_unchanged(self):
        def helper(obs,action,info):action['market'].append(['SELL','WHEAT',1]);return 1
        events=[];action={'farmer':['PASS'],'market':[]}
        self.assertEqual(overflow_guard(helper,{'SHEEP'},events)({'day':25,'hour':23},action),1)
        self.assertEqual(action['market'],[['SELL','WHEAT',1]]);self.assertEqual(events,[])
    def test_only_unpriced_animal_bypasses_helper(self):
        def helper(obs,action,info):
            item='SHEEP';minv={'WHEAT':2};lost=['SHEEP'];return minv[item]
        events=[];action={'farmer':['NORTH'],'market':[['SELL','WHEAT',2]]}
        self.assertEqual(overflow_guard(helper,{'SHEEP'},events)({'day':25,'hour':23},action),0)
        self.assertEqual(len(events),1);self.assertEqual(events[0]['teacher_pre_helper_action'],action)
        self.assertEqual(events[0]['returned_action'],action);self.assertFalse(events[0]['changed_unit_commands'])
    def test_nested_animal_error_propagates(self):
        def nested():
            item='SHEEP';minv={};return minv[item]
        def helper(obs,action,info):return nested()
        with self.assertRaises(KeyError):overflow_guard(helper,{'SHEEP'},[])({'day':25,'hour':23},{})
    def test_unrelated_exception_propagates(self):
        def helper(obs,action,info):
            item='WHEAT';minv={};return minv[item]
        with self.assertRaises(KeyError):overflow_guard(helper,{'SHEEP'},[])({'day':25,'hour':23},{})

if __name__=='__main__':unittest.main()

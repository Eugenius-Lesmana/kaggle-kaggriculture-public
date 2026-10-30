"""Calculation regressions; python -m unittest discover -s tools -p test_market_pressure.py."""
import unittest
from report_market_pressure import components,ratio,ratio_delta,stat


class Calculations(unittest.TestCase):
    def test_seed_pairing(self):
        mean,se,_=stat([2,4,6,8])
        self.assertEqual(mean,5)
        self.assertAlmostEqual(se,2)

    def test_ratio_jackknife(self):
        estimate,se=ratio([1,1,5,5],[1,1,1,1])
        self.assertEqual(estimate,3)
        self.assertAlmostEqual(se,2)
        self.assertEqual(ratio([0,0,0,0],[0,0,0,0]),(None,None))

    def test_paired_ratio_jackknife(self):
        result=ratio_delta('delta',[2,4,6,8],[1,1,1,1],[2,2,2,2],[1,1,1,1])
        self.assertEqual(result['delta'],3)
        self.assertAlmostEqual(result['delta_se_seed24'],2)

    def test_exact_price_quantity_accounting(self):
        self.assertEqual(components(4,20,2,14),(12,-6))
        self.assertEqual(components(0,0,3,12),(-12,0))
        self.assertEqual(components(3,12,0,0),(12,0))
        self.assertEqual(components(0,0,0,0),(0,0))

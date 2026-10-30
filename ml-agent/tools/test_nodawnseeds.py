"""Prove that the owned copy differs only by the switch and preserves disabled behavior."""
import copy
import difflib
import json
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from nodawnseeds_bench import REPO,SOURCE
from kagml.preview import TemplatePlayer
from compare_day import make_player


class Checks(unittest.TestCase):
    def test_only_switch_diff(self):
        a=(REPO/'vendor/template_agent/main.py').read_text().splitlines()
        b=(REPO/'agents/template_switches/main.py').read_text().splitlines()
        diff=list(difflib.unified_diff(a,b,n=0))
        plus=[x[1:] for x in diff if x.startswith('+') and not x.startswith('+++')]
        minus=[x for x in diff if x.startswith('-') and not x.startswith('---')]
        self.assertEqual(minus,[]);self.assertEqual(len(plus),3)
        self.assertEqual(plus[0],'import os')
        self.assertIn('KAGML_NO_DAWN_SEEDS',plus[1]);self.assertIn('BUY_SEED',plus[2])

    def test_disabled_and_enabled_recorded_observations(self):
        rep=json.loads((SOURCE/'10301.json').read_bytes())
        a=make_player('template');b=make_player('template:nodawnseeds')
        with patch.dict(os.environ,{'KAGML_NO_DAWN_SEEDS':'0'}):
            for step in range(8*24):
                o=rep['steps'][step][0]['observation']
                self.assertEqual(a(copy.deepcopy(o)),b(copy.deepcopy(o)))
            self.assertEqual(a.memory(),b.memory())
        for step in range(8*24,9*24):
            o=rep['steps'][step][0]['observation']
            want=a(copy.deepcopy(o))
            if o['hour']<3:
                want['market']=[x for x in want['market'] if not (x[0]=='BUY_SEED' and x[1] in ('WHEAT','CARROT'))]
            with patch.dict(os.environ,{'KAGML_NO_DAWN_SEEDS':'1'}):got=b(copy.deepcopy(o))
            self.assertEqual(want,got)
        self.assertEqual(a.module.ERRORS['count'],0);self.assertEqual(b.module.ERRORS['count'],0)


if __name__=='__main__':unittest.main()

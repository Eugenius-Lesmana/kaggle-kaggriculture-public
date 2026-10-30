"""Independent engine checks for package U (no games or policies)."""
from types import SimpleNamespace
import copy
import json
import os
import unittest
from pathlib import Path
import urgent_triage as U

class UrgentChecks(unittest.TestCase):
    def tile(self,item,**changes):
        animal=item in U.K.ANIMALS
        t={'kind':U.K.ANIMALS[item]['structure'] if animal else 'PLANT','yield_units':0}
        t.update({'animal':item,'placed_day':0,'fed_today':False,'consecutive_unfed':0,'cared_today':False,'pending_care_bonus':3} if animal else
                 {'crop':item,'planted_day':0,'watered_today':False,'consecutive_unwatered':0,'fertilized_until_day':20,'max_lifespan_step':-1})
        t.update(changes);return t

    def test_native_production_without_service(self):
        for item,day,expected in [('STRAWBERRY',9,1),('TOMATO',7,1),('COW',7,3)]:
            tile=self.tile(item);obs={'day':day,'market':{'prices':{item:100,'MILK':100}}}
            f=U.risk(tile,0,0,obs);self.assertTrue(f['production']);self.assertFalse(f['survival'])
            animals=item in U.K.ANIMALS
            yes=copy.deepcopy(tile);yes['fed_today' if animals else 'watered_today']=True
            f0={'tiles':[[tile]]};f1={'tiles':[[yes]]}
            if animals:
                U.K._daily_refresh_animals(f0,day);U.K._daily_refresh_animals(f1,day)
            else:
                U.K._daily_refresh_plants(f0,day,24);U.K._daily_refresh_plants(f1,day,24)
            self.assertEqual(f0['tiles'][0][0]['yield_units'],1)
            self.assertEqual(f1['tiles'][0][0]['yield_units']-f0['tiles'][0][0]['yield_units'],f['night_increment'])
            self.assertEqual(f['actual_skip_loss'],expected*100)

    def test_native_survival(self):
        for item,day in [('WHEAT',2),('COW',7)]:
            animal=item in U.K.ANIMALS
            t=self.tile(item,**{'consecutive_unfed' if animal else 'consecutive_unwatered':1})
            f=U.risk(t,0,0,{'day':day,'market':{'prices':{item:100,'MILK':100}}})
            self.assertTrue(f['survival']);farm={'tiles':[[t]]}
            if animal:U.K._daily_refresh_animals(farm,day)
            else:U.K._daily_refresh_plants(farm,day,24)
            self.assertFalse(U.ident(farm['tiles'][0][0],0,0))

    def test_full_production_is_zero_increment(self):
        t=self.tile('COW',yield_units=6)
        f=U.risk(t,0,0,{'day':7,'market':{'prices':{'MILK':100}}})
        self.assertEqual(f['actual_skip_loss'],0)

    def test_seed_schedule_native(self):
        U.pin_weeds(True)
        for seed in (10301,10315,10401,10501,11000,11500):
            farms=[dict(tiles=[['LOCKED']*10 for _ in range(10)]) for _ in range(2)]
            town={'unlocked_shops':[]}
            states=[SimpleNamespace(observation=SimpleNamespace(farms=farms,town=town,private=dict(shed={},inventories=[{}]))) for _ in range(2)]
            env=SimpleNamespace(configuration=SimpleNamespace(),info={'seed':seed})
            for day in range(2,24,3):U.K._end_of_day(states,env,day)
            self.assertEqual(town['unlocked_shops'],U.schedule(seed))

    def test_test_game_gate(self):
        for game in U.TEST:
            with self.assertRaises(AssertionError):U.read_game(Path('does-not-exist'),game)

    def test_native_recorded_segments(self):
        from kagml import replay_tables as R
        rows=U.manifest_rows()
        for source in U.SOURCES:
            r=next(r for r in rows if r['source']==source)
            rep=U.read_game(U.ROOT/r['raw_file'],r['game'])
            banks=[f['money'] for f in rep['steps'][-1][0]['observation']['farms']]
            meta=dict(episode=r['episode'],created='',**{f'{k}_{p}':banks[p] if k=='reward' else -1 for p in (0,1) for k in ('reward','sub','team','rating')})
            result,audit=R.replay(rep,meta,'split-weeds',segment=True)
            self.assertIsNotNone(result,audit)
            e,h,j,c=U.segment(r)
            self.assertEqual(sum(x['served'] for x in e),sum(x['service_order']>0 for x in e))
            self.assertTrue(all(x['hour']>=int(r['H']) for x in h))

if __name__=='__main__':unittest.main()

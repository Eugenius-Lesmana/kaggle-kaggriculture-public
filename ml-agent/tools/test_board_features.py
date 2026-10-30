"""Native rule and history checks: python tools/test_board_features.py."""
import copy
import contextlib
import io
import sys
from pathlib import Path
import unittest
sys.path[:0]=[str(Path(__file__).resolve().parents[1]/'src'),str(Path(__file__).resolve().parent)]
from kagml import replay_tables as RT
with contextlib.redirect_stdout(io.StringIO()),contextlib.redirect_stderr(io.StringIO()):
    from kagml import board_features as B
from kagml.work_data import load_replay
from kagml import work_features as W
from kagml.paths import data_root
import numpy as np

class BoardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rep=load_replay(data_root()/'raw/ownfarm/fourth/10301-d16.json.gz')
        cls.obs=cls.rep['steps'][8][0]['observation']

    def assert_masks(self,obs,u=0,earlier=()):
        saved=copy.deepcopy(obs);mask=B.legal(obs,0,u,list(earlier));self.assertEqual(obs,saved)
        farm,private=B.after_earlier(obs,0,u,list(earlier))
        for i,c in enumerate(B.COMMANDS):
            f,p=copy.deepcopy((farm,private));effect=B.apply(f,p,u,B.decode(i),obs['day'])
            self.assertEqual(bool(mask[i]),effect or c[0]=='PASS',(u,c))

    def test_all_commands_against_native(self):
        for frame in self.rep['steps'][::3]:
            obs=frame[0]['observation']
            for u in range(len(B.positions(obs['farms'][0]))):self.assert_masks(obs,u,[['PASS']]*u)

    def test_corner_and_locked_and_empty(self):
        for pos in ([0,0],[9,9],[4,4],[5,5]):
            for tile in (None,'LOCKED',{'kind':'WEED'}):
                obs=copy.deepcopy(self.obs);obs['farms'][0]['farmer']=pos;obs['farms'][0]['tiles'][pos[1]][pos[0]]=tile;self.assert_masks(obs)

    def test_shared_seed_and_repeated_water(self):
        obs=copy.deepcopy(self.obs);f=obs['farms'][0];f['farmer']=[0,0];f['hands'][0]=[1,0];f['tiles'][0][0]=None;f['tiles'][0][1]=None;obs['private']['seeds']['WHEAT']=1
        self.assert_masks(obs,1,[['PLANT','WHEAT']]);self.assertFalse(B.legal(obs,0,1,[['PLANT','WHEAT']])[B.COMMAND_ID[('PLANT','WHEAT')]])
        f['hands'][0]=[0,0];B.apply(f,obs['private'],0,['PLANT','WHEAT'],obs['day']);self.assert_masks(obs,1,[['WATER']])
        self.assertFalse(B.legal(obs,0,1,[['WATER']])[B.COMMAND_ID[('WATER',)]])

    def test_shed_order_overflow_and_animal(self):
        obs=copy.deepcopy(self.obs);f=obs['farms'][0];f['farmer']=[4,4];f['hands'][0]=[4,4];f['tiles'][4][4]=None;obs['private']['shed']={'WHEAT':99};obs['private']['inventories'][0]={'MILK':2,'WOOL':3};self.assert_masks(obs,1,[['DROP']])
        self.assertTrue(B.legal(obs,0,1,[['DROP']])[B.COMMAND_ID[('PICKUP','MILK')]])
        self.assertFalse(B.legal(obs,0,1,[['DROP']])[B.COMMAND_ID[('PICKUP','WOOL')]])
        f['tiles'][4][4]={'kind':'COOP'};obs['private']['inventories'][0]={'GOOSE':1};obs['private']['shed']={'WHEAT':100};self.assert_masks(obs)
        self.assertTrue(B.legal(obs,0,0,[])[B.COMMAND_ID[('PLACE','GOOSE')]])

    def test_nightly_matches_work_features(self):
        for frame in self.rep['steps'][::3]:
            obs=frame[0]['observation'];h=W.History();h.add(obs,{});ctx=W.context(obs,0,h)
            for y,line in enumerate(obs['farms'][0]['tiles']):
                for x,tile in enumerate(line):
                    if not isinstance(tile,dict) or not (tile.get('kind')=='PLANT' or 'animal' in tile):continue
                    row=W.candidate_rows(obs,0,0,[('HARVEST',y*10+x)],ctx)[0];b=B.tile_values(tile,x,y,obs['day'],obs['day']*24+obs['hour'],obs['market']['prices'])
                    for k in B.TILE_COLUMNS:
                        if k.startswith('n_'):self.assertEqual(b[k],row.get(k,0),k)
                    self.assertEqual(b['next_production'],row['t_next_prod'])

    def test_history_and_padding(self):
        obs=copy.deepcopy(self.obs);obs['hour']=0;obs['step']=obs['day']*24;h=B.History();h.observe(obs,0);a=B.encode(obs,0,h)
        self.assertEqual(a['units'].shape,(14,len(B.UNIT_COLUMNS)));self.assertTrue(np.all(a['units'][~a['unit_mask']]==0))
        nxt=copy.deepcopy(obs);nxt['hour']=1;nxt['step']+=1;f,p=copy.deepcopy((obs['farms'][0],obs['private']));cmd=['EAST'] if f['farmer'][0]<9 else ['WEST'];B.apply(f,p,0,cmd,obs['day']);nxt['farms'][0]=f;nxt['private']=p;h.observe(nxt,0,{'farmer':cmd});a=B.encode(nxt,0,h)
        self.assertEqual(tuple(a['units'][0,15:17]),B.MOVES[cmd[0]])
        with self.assertRaises(ValueError):h.observe(nxt,0)

    def test_fourteen_workers_and_validation(self):
        obs=copy.deepcopy(self.obs);farm=obs['farms'][0]
        farm['hands']=[[4,4] for _ in range(13)];obs['private']['inventories']=[{} for _ in range(14)]
        h=B.History();h.observe(obs,0);self.assertEqual(int(B.encode(obs,0,h)['unit_mask'].sum()),14)
        farm['hands'].append([4,4]);obs['private']['inventories'].append({})
        with self.assertRaises(ValueError):B.encode(obs,0,h)
        with self.assertRaises(ValueError):B.legal(self.obs,0,2,[['PASS']])

    def test_command_masks_multiple_amounts(self):
        obs=copy.deepcopy(self.obs);obs['farms'][0]['farmer']=[4,4];obs['farms'][0]['tiles'][4][4]=None
        obs['private']['shed']={i:3 for i in B.ITEMS};obs['private']['inventories'][0]={i:3 for i in B.ITEMS}
        mask=B.legal(obs,0,0,[])
        for i,c in enumerate(B.COMMANDS):
            if c[0] not in ('PICKUP','PLACE'):continue
            for amount in (1,5,10):
                farm,private=copy.deepcopy((obs['farms'][0],obs['private']))
                self.assertEqual(bool(mask[i]),B.apply(farm,private,0,B.decode(i,amount),obs['day']))

    def test_commands_roundtrip(self):
        self.assertEqual(len(B.COMMANDS),len(set(B.COMMANDS)))
        for i in range(len(B.COMMANDS)):self.assertEqual(B.command_id(B.decode(i,10)),i)
        self.assertEqual(B.decode(B.COMMAND_ID[('PLACE','WHEAT')],10,3),['PLACE','WHEAT',10])
        self.assertEqual(B.decode(B.COMMAND_ID[('PICKUP','WHEAT')],1,2),['PICKUP','WHEAT'])

if __name__=='__main__':unittest.main()

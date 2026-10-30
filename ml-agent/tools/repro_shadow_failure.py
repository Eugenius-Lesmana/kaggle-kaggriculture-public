"""Reproduce the unmodified teacher failure on el3 10319/day25; save evidence on D:."""
import copy
import gzip
import json
import traceback

from shadow_labels import ROOT,REPO,source,player_instance,warm_memories,generate,sha,compact,folders
from kagml.opponents import load

path=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10319.json'
recorded,source_hash=source(path)
player,_=player_instance('template');player.restore(copy.deepcopy(warm_memories(path,'template')[25]))
actor=load('fourth')
class Capture:
    def __init__(self,actor):self.actor=actor;self.observation=None;self.configuration=None
    def __getattr__(self,key):return getattr(self.actor,key)
    def __call__(self,obs,configuration):
        self.observation=copy.deepcopy(obs);self.configuration=copy.deepcopy(dict(configuration))
        return self.actor(obs,configuration)
teacher=Capture(actor)
try:
    generate(recorded,'10319',25,'template',player,teacher)
except Exception as error:
    result={'game':'10319','day':25,'source_sha256':source_hash,'step':teacher.observation['step'],
            'error':f'{type(error).__name__}: {error}','traceback':traceback.format_exc(),
            'observation':teacher.observation,'configuration':teacher.configuration,
            'upstream_hashes':{str(p):sha(p) for p in (actor.root/'policy.py',actor.root/'play.py',actor.root/'weights.pt')}}
    target=folders('template')[2]/'failure-10319-d25.json.gz'
    target.write_bytes(gzip.compress(compact(result).encode(),mtime=0))
    print(json.dumps({k:result[k] for k in ('game','day','step','error')},separators=(',',':')))
    assert isinstance(error,KeyError) and error.args==('SHEEP',),'different failure'
else:raise AssertionError('Teacher failure did not reproduce')

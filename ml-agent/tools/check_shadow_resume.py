"""Prove unchanged self-shadow receipts resume without loading/acting again."""
import json
import time
from shadow_labels import REPO,one,folders,save_json,dependencies

_,_,log=folders('fourth');smoke=json.loads((log/'smoke.json').read_bytes())
assert dependencies('fourth')[0]==smoke['signature']
path=REPO.parent/'Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10301.json'
begun=time.perf_counter();rows=[one((path,d,'fourth',smoke['signature'])) for d in (6,16,28)]
assert all(r['resumed'] and r['reason']=='kept' for r in rows)
result={'segments':3,'resumed':3,'seconds':time.perf_counter()-begun,'signature':smoke['signature']}
save_json(log/'resume-check.json',result);print(json.dumps(result))

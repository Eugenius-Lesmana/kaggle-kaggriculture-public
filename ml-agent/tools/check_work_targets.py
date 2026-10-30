"""W1 independent checks of native fixed-work fertilizer counterfactuals."""
import copy
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kagml.work_targets import Shadow,K,ready,Observer

checks=[]
def wheat():
    t=K._new_plant("WHEAT",0,24);t["yield_units"]=4
    return Shadow(t)

a=wheat();b=Shadow(a.farm["tiles"][0][0])
a.act("FERTILIZE",2)
for q in (a,b):q.act("WATER",2);q.act("HARVEST",2)
assert a.harvested-b.harvested==1
checks.append("fertilize before watering adds one harvested unit")

a=wheat();a.act("WATER",2);b=Shadow(a.farm["tiles"][0][0]);a.act("FERTILIZE",2)
for q in (a,b):q.act("HARVEST",2)
assert a.harvested-b.harvested==0
checks.append("fertilizing after this watering gives no immediate harvested bonus")

a=wheat();b=Shadow(a.farm["tiles"][0][0]);a.act("FERTILIZE",2)
for q in (a,b):q.act("WATER",2);q.refresh(2);q.act("WATER",3);q.act("HARVEST",3)
assert a.harvested-b.harvested==0
checks.append("ordinary later watering catches up at the cap")

a=wheat();a.act("FERTILIZE",2);b=Shadow(a.farm["tiles"][0][0]);a.act("FERTILIZE",2)
for q in (a,b):q.act("WATER",2);q.act("HARVEST",2)
assert a.harvested-b.harvested==0
checks.append("a redundant same-day dose has zero marginal effect")

a=Shadow(K._new_plant("TOMATO",0,24));a.act("WATER",7)
b=Shadow(a.farm["tiles"][0][0]);a.act("FERTILIZE",7)
for q in (a,b):q.refresh(7);q.act("HARVEST",8)
assert a.harvested-b.harvested==1
checks.append("ongoing crop bonus is generated at its scheduled dawn")

t=K._new_plant("MELON",0,24);t["yield_units"]=6
assert ready(t,9)==0 and ready(t,10)==6
checks.append("stored immature crop units are not counted as available")

o=Observer("fixture","fixture",{0:"template"},0);o.step=48
o.farms=[{"tiles":[[copy.deepcopy(t)]]}]
o.dose(0,0,0,t);dose=o.shadows[(0,0,0)][0]
o.finish_dose((0,0,0),dose,50,"window_end",t)
assert o.rows["doses"][0]["censored"] and not o.rows["doses"][0]["complete"]
checks.append("an unfinished follow-up remains censored, not a zero-yield result")
# Framework env.step copies the farm; the observer can still hold the pre-turn tile.
o=Observer("fixture","fixture",{0:"template"},0);o.step=48
t=wheat().farm["tiles"][0][0];o.farms=[{"tiles":[[copy.deepcopy(t)]]}]
o.dose(0,0,0,t);dose=o.shadows[(0,0,0)][0]
dose["shadow"].act("WATER",2);dose["shadow"].act("HARVEST",2);dose["actual"]=6
o.finish_dose((0,0,0),dose,50,"harvested",None)
assert o.rows["doses"][0]["marginal_harvest"]==1 and o.rows["doses"][0]["marginal_held"]==0
checks.append("a harvested crop holds zero goods even when the framework retains a pre-turn farm copy")
print(json.dumps({"passed":len(checks),"checks":checks},indent=2))

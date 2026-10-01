"""Why so little fertilizing? Per day: plants by crop, plants with any fertilizer gain,
plants that qualify as targets, fertilizer carried by workers and in the shed."""
import importlib.util, sys, json
from collections import Counter, defaultdict
from kaggle_environments import make
path, seed = sys.argv[1], int(sys.argv[2])
spec = importlib.util.spec_from_file_location("cand", path); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
agent = [v for v in vars(mod).values() if callable(v)][-1]
log = defaultdict(Counter)
def wrapped(obs, conf):
    act = agent(obs)
    o = dict(obs); day = o["day"]; me = o["farms"][o["player"]]
    if o.get("hour") == 8:   # one snapshot per day, mid-morning
        c = log[day]
        for row in me["tiles"]:
            for t in row:
                if isinstance(t, dict) and t.get("kind") == "PLANT":
                    c["plants " + t["crop"]] += 1
                    g = mod.fertilizer_gain(t, day)
                    if g: c["gain>0 " + t["crop"]] += 1
                    if t.get("fertilized_until_day", -1) >= day: c["already fertilized"] += 1
        for pos in mod.fertilizer_targets(o, True): 
            t = me["tiles"][pos[1]][pos[0]]; c["TARGET " + t["crop"]] += 1
        c["carried"] = sum(i.get("FERTILIZER", 0) for i in o["private"].get("inventories", []))
        c["shed"] = o["private"].get("shed", {}).get("FERTILIZER", 0)
        c["price"] = o["market"]["prices"].get("FERTILIZER", 0)
    return act
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
env.run([wrapped, "agents/ours/h1-substrate-metav4/main.py"])
for day in sorted(log):
    if day % 2 == 0 or day in (7, 9, 11):
        print(day, dict(sorted(log[day].items())))

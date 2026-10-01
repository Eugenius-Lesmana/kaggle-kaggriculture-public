"""Where does each side's money go? Confirmed purchases per category from consecutive observations."""
import sys, json
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

def play(job):
    seed, agent, opp = job
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    env.run([agent, opp]); steps = env.steps
    out = [Counter(), Counter()]
    for i in range(1, len(steps)):
        for side in (0, 1):
            b, a = steps[i-1][side]["observation"], steps[i][side]["observation"]
            fb, fa = b["farms"][side], a["farms"][side]
            act = steps[i][side].get("action") or {}
            orders = (act.get("market") or []) if isinstance(act, dict) else []
            c = out[side]
            # hires: hands added this step (fib cost by hires_today index)
            added = len(fa.get("hands") or []) - len(fb.get("hands") or []) if a["day"] == b["day"] else 0
            if added > 0:
                start = fb.get("hires_today", 0)
                c["hires"] += sum(K._hire_cost(start + k, 1) for k in range(added)); c["hire_count"] += added
            nq = len(fa.get("unlocked_quadrants", [])) - len(fb.get("unlocked_quadrants", []))
            if nq > 0:
                c["land"] += sum(K.LAND_PRICES[len(fb.get("unlocked_quadrants", [])) - 1 + k] for k in range(nq))
            for o in orders:
                if not o: continue
                if o[0] == "BUY_ANIMAL": c["animal_orders"] += 1; c["animals"] += K.ANIMALS[o[1]]["cost"] if isinstance(K.ANIMALS.get(o[1]), dict) and "cost" in K.ANIMALS[o[1]] else 0
                elif o[0] == "BUY_SEED" and len(o) > 2: c["seed_units"] += int(o[2]); c["seed_spend_est"] += int(o[2]) * (K.CROPS[o[1]].get("seed_cost", K.CROPS[o[1]].get("seed_price", 0)) if isinstance(K.CROPS.get(o[1]), dict) else 0)
                elif o[0] == "BUY_PRODUCT" and len(o) > 2: c["buy_" + o[1]] += int(o[2]); c["buy_spend_est"] += int(o[2]) * b["market"]["prices"].get(o[1], 0)
    return [dict(x) for x in out]

if __name__ == "__main__":
    from kaggle_environments.envs.kaggriculture import kaggriculture as K
    print("animal keys", list(K.ANIMALS["COW"].keys())[:12], "| crop keys", list(K.CROPS["WHEAT"].keys())[:14])
    agent, opp = sys.argv[1], sys.argv[2]
    with ProcessPoolExecutor(2) as pool:
        res = list(pool.map(play, [(s, agent, opp) for s in range(7981, 7987)]))
    for side, name in ((0, "ours (v0.10)"), (1, "Metav4")):
        tot = Counter()
        for r in res: tot.update(r[side])
        print(name, {k: round(v / len(res)) for k, v in sorted(tot.items())})

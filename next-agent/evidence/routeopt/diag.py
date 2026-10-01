"""Where does worker time go, and what is left undone? Full-game execution diagnostic.

Per game and phase (days 0-5, 6-11, 12-19, 20-27):
- worker-steps idle / moving / working;
- confirmed productive commands, and waterings the plant did not need;
- service left undone at hour 23: unfed and uncared animals, uncollected fertilizer,
  dying unwatered plants, one-time crops past their last yield day;
- final banks.

  python evaluation/routeopt/diag.py --agent agents/ours/v0.10.0-candidate/main.py \
      --opponent agents/ours/h1-substrate-metav4/main.py --seeds 7601-7610 --workers 2 \
      --out evaluation/routeopt/diag_v010.json
"""
import argparse, json, os, sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repository root
sys.path.insert(0, os.path.join(ROOT, "tools"))
from screen import action_succeeded, parse_seeds  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
PHASES = ((0, 6, "d0_5"), (6, 12, "d6_11"), (12, 20, "d12_19"), (20, 28, "d20_27"))


def phase(day):
    return next(name for lo, hi, name in PHASES if lo <= day < hi)


def water_needed(tile, day):
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
    crop = CROPS[tile["crop"]]
    age = day - tile["planted_day"]
    if tile.get("consecutive_unwatered", 0) >= 1:
        return True
    if not crop["ongoing"]:
        return (crop["max_yield_day"] + 1) // 2 <= age <= crop["max_yield_day"] and tile["yield_units"] < crop["max_yield"]
    since = age + 1 - crop["first_yield_day"]
    return tile.get("fertilized_until_day", -1) >= day and since >= 0 and since % crop["interval"] == 0


def execution(steps, side):
    out = {name: Counter() for _, _, name in PHASES}
    for i in range(1, min(len(steps), 28 * 24 + 1)):
        before, after = steps[i - 1][side]["observation"], steps[i][side]["observation"]
        c = out[phase(before["day"])]
        action = steps[i][side].get("action") or {}
        farm, farm_after = before["farms"][side], after["farms"][side]
        units = [farm["farmer"]] + list(farm.get("hands") or [])
        commands = [action.get("farmer")] + list(action.get("hands") or []) if isinstance(action, dict) else []
        inv_b, inv_a = before["private"].get("inventories", []), after["private"].get("inventories", [])
        rollover = before["day"] != after["day"]
        for order in (action.get("market") or []) if isinstance(action, dict) else []:
            if order and order[0] == "BUY_PRODUCT" and len(order) > 2:
                c["buy_request " + order[1]] += int(order[2])
        for k, (x, y) in enumerate(units):
            command = commands[k] if k < len(commands) and isinstance(commands[k], list) and commands[k] else ["PASS"]
            name = command[0]
            c["worker_steps"] += 1
            if name == "PASS":
                c["idle"] += 1
            elif name in MOVES:
                c["move"] += 1
            else:
                c["work"] += 1
                if name in ("PICKUP", "DROP") or rollover:
                    continue
                ok = action_succeeded(name, farm["tiles"][y][x], farm_after["tiles"][y][x],
                                      inv_b[k] if k < len(inv_b) else {}, inv_a[k] if k < len(inv_a) else {})
                if ok:
                    c["useful"] += 1
                    c[name + "_ok"] += 1
                    if name == "HARVEST":
                        t = farm["tiles"][y][x] if isinstance(farm["tiles"][y][x], dict) else {}
                        product = t.get("crop") or PRODUCT.get(t.get("animal"), "?")
                        b, a = (inv_b[k] if k < len(inv_b) else {}), (inv_a[k] if k < len(inv_a) else {})
                        c["harvest_units " + product] += max(0, a.get(product, 0) - b.get(product, 0))
                    if name == "WATER" and not water_needed(farm["tiles"][y][x], before["day"]):
                        c["water_unneeded"] += 1
                elif ok is not None:
                    c["failed"] += 1
    return out


def coverage(steps, side, out):
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
    for day in range(28):
        i = day * 24 + 23
        if i >= len(steps):
            break
        c = out[phase(day)]
        farm_obs = steps[i][side]["observation"]["farms"][side]
        c["days"] += 1
        c["plots_owned"] += 25 * len(farm_obs.get("unlocked_quadrants", ["NW"]))
        for row in farm_obs["tiles"]:
            for tile in row:
                if tile is None:
                    c["empty_cell_days"] += 1
                elif isinstance(tile, dict) and tile.get("kind") == "WEED":
                    c["weed_cell_days"] += 1
        for row in steps[i][side]["observation"]["farms"][side]["tiles"]:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if "animal" in tile:
                    c["animal_days"] += 1
                    c["animal_days " + tile["animal"]] += 1
                    c["undone_feed"] += not tile["fed_today"]
                    c["undone_care"] += not tile["cared_today"]
                    c["undone_fert_collect"] += bool(tile.get("fertilizer_available"))
                elif tile.get("kind") == "PLANT":
                    crop = CROPS[tile["crop"]]
                    c["plant_days"] += 1
                    c["plant_days " + tile["crop"]] += 1
                    c["fertilized_plant_days"] += tile.get("fertilized_until_day", -1) >= day
                    if water_needed(dict(tile, consecutive_unwatered=0), day):
                        c["window_plant_days"] += 1
                        c["window_watered"] += bool(tile["watered_today"])
                    c["undone_dying_water"] += not tile["watered_today"] and tile["consecutive_unwatered"] >= 1
                    c["undone_overdue_harvest"] += (not crop["ongoing"] and tile["yield_units"] > 0
                                                    and day - tile["planted_day"] >= crop["max_yield_day"])


def play(job):
    seed, side, agent, opponent = job
    from kaggle_environments import make
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    agents = [agent, opponent] if side == 0 else [opponent, agent]
    env.run(agents)
    steps = env.steps
    out = execution(steps, side)
    coverage(steps, side, out)
    final = [s.get("reward") or 0 for s in steps[-1]]
    return {"seed": seed, "side": side, "bank": final[side], "opp_bank": final[1 - side],
            "phases": {k: dict(v) for k, v in out.items()}}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--agent", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--seeds", type=parse_seeds, required=True)
    ap.add_argument("--seats", type=int, default=1)
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jobs = [(s, side, a.agent, a.opponent) for s in a.seeds for side in range(a.seats)]
    with ProcessPoolExecutor(a.workers) as pool:
        rows = list(pool.map(play, jobs))
    json.dump({"agent": a.agent, "opponent": a.opponent, "rows": rows}, open(a.out, "w"))
    tot = {name: Counter() for _, _, name in PHASES}
    for r in rows:
        for k, v in r["phases"].items():
            tot[k].update(v)
    n = len(rows)
    ops = ("FERTILIZE", "COLLECT_FERTILIZER", "FEED", "CARE", "HARVEST", "PLANT", "WATER")
    for k, c in tot.items():
        print(f"{k} per game: " + ", ".join(f"{op.lower()} {c[op + '_ok']/max(1,len(rows)):.0f}" for op in ops))
    print(f"{n} games, bank ratio {sum(r['bank'] for r in rows) / max(1, sum(r['opp_bank'] for r in rows)):.3f}")
    for k, c in tot.items():
        ws = max(1, c["worker_steps"])
        print(f"{k}: idle {c['idle']/ws:5.1%} move {c['move']/ws:5.1%} work {c['work']/ws:5.1%} | useful/game {c['useful']/n:6.1f}"
              f" unneeded water {c['water_unneeded']/n:5.1f} failed {c['failed']/n:5.1f} | undone per animal-day: feed "
              f"{c['undone_feed']/max(1,c['animal_days']):.2f} care {c['undone_care']/max(1,c['animal_days']):.2f} fert "
              f"{c['undone_fert_collect']/max(1,c['animal_days']):.2f}; per plant-day: dying water "
              f"{c['undone_dying_water']/max(1,c['plant_days']):.3f} overdue harvest {c['undone_overdue_harvest']/max(1,c['plant_days']):.3f}")

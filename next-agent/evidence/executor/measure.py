"""Paired executor screen: each arm vs one opponent on identical seeds, both seats.

Per game it records, for days 0-5 and 6-11 separately: confirmed successful commands (checked
against the next observed state, as scripts/screen.py does), idle/move/work worker-steps; the farm
at the start of day 12; the final banks; and the route-follower's own diagnostics.

  python evaluation/executor/measure.py --arm skel=agents/ours/executor-candidate/skel.py \
      --arm route=agents/ours/executor-candidate/main.py --opponent agents/ours/h1-substrate-metav4/main.py \
      --seeds 7101-7130 --workers 4 --out evaluation/executor/raw_metav4.json
  python evaluation/executor/measure.py --replays Team A --out evaluation/executor/team_a_reference.json
"""
import argparse, glob, gzip, importlib.util, json, os, sys, time, uuid
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))  # repository root
sys.path.insert(0, os.path.join(ROOT, "tools"))
from screen import action_succeeded, parse_seeds  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
PRODUCTIVE = ("WATER", "HARVEST", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER", "FERTILIZE", "DIG",
              "BUILD", "PLACE_ANIMAL")
PRICED = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
SKELETON_STEPS = 12 * 24


def water_needed(tile, day):
    """A WATER that kept the plant alive (unwatered yesterday), added yield, or made a live
    fertilizer count; the rest only repeat a watering the plant did not need today."""
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
    crop = CROPS[tile["crop"]]
    age = day - tile["planted_day"]
    if tile.get("consecutive_unwatered", 0) >= 1:
        return True
    if not crop["ongoing"]:
        return (crop["max_yield_day"] + 1) // 2 <= age <= crop["max_yield_day"] and tile["yield_units"] < crop["max_yield"]
    since = age + 1 - crop["first_yield_day"]
    return tile.get("fertilized_until_day", -1) >= day and since >= 0 and since % crop["interval"] == 0


def succeeded(name, before_tile, after_tile, before_inv, after_inv):
    was = before_tile if isinstance(before_tile, dict) else {}
    now = after_tile if isinstance(after_tile, dict) else {}
    if name in ("BUILD_COOP", "BUILD_PASTURE"):
        return before_tile is None and now.get("kind") in ("COOP", "PASTURE")
    if name == "PLACE":
        return "animal" in now and "animal" not in was
    return action_succeeded(name, before_tile, after_tile, before_inv, after_inv)


def execution(steps, side):
    """Worker-step and confirmed-success counts for days 0-5 and 6-11."""
    out = {"d0_5": Counter(), "d6_11": Counter()}
    for i in range(1, SKELETON_STEPS + 1):
        before, after = steps[i - 1][side]["observation"], steps[i][side]["observation"]
        action = steps[i][side].get("action") or {}
        c = out["d0_5" if before["day"] < 6 else "d6_11"]
        farm, farm_after = before["farms"][side], after["farms"][side]
        units = [farm["farmer"]] + list(farm.get("hands") or [])
        commands = [action.get("farmer")] + list(action.get("hands") or []) if isinstance(action, dict) else []
        inv_b, inv_a = before["private"].get("inventories", []), after["private"].get("inventories", [])
        rollover = before["day"] != after["day"]
        for k, (x, y) in enumerate(units):
            command = commands[k] if k < len(commands) and isinstance(commands[k], list) and commands[k] else ["PASS"]
            name = command[0]
            c["worker_steps"] += 1
            if name == "PASS":
                c["idle"] += 1
                continue
            if name in MOVES:
                c["move"] += 1
                continue
            c["work_issued"] += 1
            if name in ("PICKUP", "DROP") or (name == "PLACE" and command[1:2] and command[1] not in ("GOOSE", "COW", "SHEEP")):
                c["shed_op"] += 1
                continue
            if rollover:
                c["unobserved"] += 1
                continue
            ok = succeeded(name, farm["tiles"][y][x], farm_after["tiles"][y][x],
                           inv_b[k] if k < len(inv_b) else {}, inv_a[k] if k < len(inv_a) else {})
            key = "BUILD" if name.startswith("BUILD") else "PLACE_ANIMAL" if name == "PLACE" else name
            if ok:
                c[key + " ok"] += 1
                c["productive"] += 1
                if name == "WATER" and not water_needed(farm["tiles"][y][x], before["day"]):
                    c["WATER unneeded"] += 1
            elif ok is not None:
                c["failed"] += 1
    return {phase: dict(v) for phase, v in out.items()}


def coverage(steps, side):
    """Service left undone at hour 23 of days 6-11 (before the hour-23 command, so a slight overcount)."""
    from kaggle_environments.envs.kaggriculture.kaggriculture import CROPS
    c = Counter()
    for day in range(6, 12):
        obs = steps[day * 24 + 23][side]["observation"]
        for row in obs["farms"][side]["tiles"]:
            for tile in row:
                if not isinstance(tile, dict):
                    continue
                if "animal" in tile:
                    c["animal_days"] += 1
                    c["unfed"] += not tile["fed_today"]
                    c["uncared"] += not tile["cared_today"]
                    c["fertilizer_uncollected"] += tile["fertilizer_available"]
                elif tile.get("kind") == "PLANT":
                    crop = CROPS[tile["crop"]]
                    c["plant_days"] += 1
                    c["dying_unwatered"] += not tile["watered_today"] and tile["consecutive_unwatered"] >= 1
                    c["overdue_unharvested"] += (not crop["ongoing"] and tile["yield_units"] > 0
                                                 and day - tile["planted_day"] >= crop["max_yield_day"])
    return dict(c)


def farm_state(obs, side):
    """The farm at the start of day 12."""
    farm, private = obs["farms"][side], obs["private"]
    state = Counter()
    for row in farm["tiles"]:
        for tile in row:
            if tile == "LOCKED":
                state["locked"] += 1
            elif tile is None:
                state["empty"] += 1
            elif tile.get("kind") == "PLANT":
                state["crop " + tile["crop"]] += 1
                state["crops"] += 1
            elif tile.get("kind") == "WEED":
                state["weeds"] += 1
            elif "animal" in tile:
                state["animal " + tile["animal"]] += 1
                state["animals"] += 1
            else:
                state["empty_structures"] += 1
    prices = obs["market"]["prices"]
    shed = private.get("shed", {})
    state["money"] = farm["money"]
    state["shed_value"] = sum(shed.get(p, 0) * prices.get(p, 0) for p in PRICED)
    state["quadrants"] = len(farm.get("unlocked_quadrants") or [])
    return dict(state)


def load(path):
    spec = importlib.util.spec_from_file_location("arm_" + uuid.uuid4().hex, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_one(job):
    arm, path, opponent, seed, side = job
    from kaggle_environments import make
    module = load(path)
    agents = [module.agent, opponent] if side == 0 else [opponent, module.agent]
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    t0 = time.time()
    env.run(agents)
    steps = env.steps
    banks = [float(s.reward or 0) for s in steps[-1]]
    stats = getattr(module, "EXEC_STATS", {}).get(side, {})
    return {"arm": arm, "seed": seed, "side": side, "own": banks[side], "opp": banks[1 - side],
            "ratio": banks[side] / banks[1 - side] if banks[1 - side] else None,
            "seconds": round(time.time() - t0, 1),
            "script_left_at": getattr(module, "TOP4_SCRIPT_LEFT_AT", {}).get(side),
            "execution": execution(steps, side), "coverage_d6_11": coverage(steps, side), "day12": farm_state(steps[SKELETON_STEPS][side]["observation"], side),
            "route": {str(d): dict(c) for d, c in stats.items()}}


def replay_reference(team):
    rows, seen = [], set()
    for f in sorted(glob.glob(os.path.join(ROOT, "research/intake/replays/24 Sept/*/*.json.gz"))):
        episode = os.path.basename(f).split(".")[0]
        if episode in seen:
            continue
        d = json.load(gzip.open(f, "rt", encoding="utf-8"))
        names = d["info"]["TeamNames"]
        if team not in names:
            continue
        seen.add(episode)
        side = names.index(team)
        steps = d["steps"]
        rows.append({"arm": team, "episode": episode, "side": side,
                     "execution": execution(steps, side), "coverage_d6_11": coverage(steps, side),
                     "day12": farm_state(steps[SKELETON_STEPS][side]["observation"], side)})
        print(episode, flush=True)
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", action="append", default=[], help="name=path")
    ap.add_argument("--opponent")
    ap.add_argument("--seeds", type=parse_seeds)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--alternate-seats", action="store_true",
                    help="one seat per seed (odd seed = P1, even = P2): seat-swapped games are near-duplicates")
    ap.add_argument("--replays")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.replays:
        rows = replay_reference(a.replays)
    else:
        opponent = os.path.abspath(a.opponent)
        arms = [spec.split("=", 1) for spec in a.arm]
        jobs = [(name, os.path.abspath(path), opponent, seed, side)
                for seed in a.seeds for side in (((seed + 1) % 2,) if a.alternate_seats else (0, 1))
                for name, path in arms]
        rows = []
        with ProcessPoolExecutor(max_workers=a.workers) as ex:
            for r in ex.map(run_one, jobs):
                rows.append(r)
                print(f"{r['arm']:>6} seed {r['seed']} p{r['side'] + 1}: {r['own']:>9,.0f} vs {r['opp']:>9,.0f} "
                      f"ratio {r['ratio']:.3f}  {r['seconds']}s", flush=True)
                json.dump({"opponent": a.opponent, "rows": rows}, open(a.out, "w"), separators=(",", ":"))
    json.dump({"opponent": a.opponent, "rows": rows}, open(a.out, "w"), separators=(",", ":"))
    print("wrote", a.out)


if __name__ == "__main__":
    main()

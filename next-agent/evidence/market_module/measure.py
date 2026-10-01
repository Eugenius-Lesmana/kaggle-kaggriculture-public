"""Four-game source instrumentation; record fills, never save raw replays.

python evaluation/market_module/measure.py --seeds 8301 8302 8303 8304 --workers 2
"""
import argparse
import copy
import csv
import json
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def load(path):
    namespace = {"__name__": "market_measure_source"}
    exec(compile(path.read_text(), str(path), "exec"), namespace)
    return namespace


def sells(action):
    result = Counter()
    for order in action.get("market", []):
        if len(order) >= 3 and order[0] == "SELL":
            result[order[1]] += max(0, int(order[2]))
    return result


def play(seed):
    from kaggle_environments import make
    from kaggle_environments.envs.kaggriculture import kaggriculture as engine

    planner = load(ROOT / "agents/ours/v0.10.0-candidate/main.py")
    meta = load(ROOT / "agents/ours/h1-substrate-metav4/main.py")
    tags = defaultdict(Counter)
    fills = defaultdict(lambda: [0, 0])
    state = {"step": 0, "record": True}
    atomic = Counter()
    ordering_before = {}

    def tag(label, before, after, step):
        for item, units in (sells(after) - before).items():
            tags[step][label + ":" + item] += units

    for name, label in (("_r36_reserve", "reservation"), ("_v92_predict", "library_forecast"),
                        ("_v92_predict2", "library_forecast2")):
        original = meta[name]

        def wrap(obs, action, *args, original=original, label=label):
            before = sells(action)
            result = original(obs, action, *args)
            tag(label, before, result, int(obs["step"]))
            return result

        meta[name] = wrap

    original_lead = meta["Chassis"]._sell_lead

    def lead(chassis, action, view, projected, route, step, next_sup):
        before = sells(action)
        result = original_lead(chassis, action, view, projected, route, step, next_sup)
        tag("racepx_lead", before, action, step)
        return result

    meta["Chassis"]._sell_lead = lead
    original_reorder = meta["_r37_reorder_sales"]

    def reorder(obs, action):
        ordering_before[int(obs["step"])] = copy.deepcopy(action.get("market", []))
        return original_reorder(obs, action)

    meta["_r37_reorder_sales"] = reorder
    original_market, original_commit = engine._process_market, engine._commit_unit
    original_hire, original_land = engine._do_hire, engine._do_buy_land
    opening_gain = 0
    ordering_gain = 0
    changed_ordering = 0

    def commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = original_commit(op, item, price, farm, private, market, shed_capacity)
        if ok and state["record"]:
            side = state["farms"][id(farm)]
            row = fills[(state["step"], side, op, item)]
            row[0] += 1
            row[1] += price
        return ok

    def hire(farm, *args):
        before = farm["money"]
        result = original_hire(farm, *args)
        if state["record"]:
            atomic[state["farms"][id(farm)]] += before - farm["money"]
        return result

    def land(farm, *args):
        before = farm["money"]
        result = original_land(farm, *args)
        if state["record"]:
            atomic[state["farms"][id(farm)]] += before - farm["money"]
        return result

    def process(states, env):
        nonlocal opening_gain, ordering_gain, changed_ordering
        state["farms"] = {id(f): i for i, f in enumerate(states[0].observation.farms)}
        snapshot = copy.deepcopy(states)
        original_market(states, env)
        actual = states[0].observation.farms[1]["money"]
        state["record"] = False
        try:
            if state["step"] == 0:
                alternate = copy.deepcopy(snapshot)
                orders = alternate[1].action["market"]
                alternate[1].action["market"] = [["BUY_PRODUCT", "WHEAT", 5]] + [
                    o for o in orders if len(o) < 2 or o[:2] not in
                    (["BUY_PRODUCT", "WHEAT"], ["SELL", "WHEAT"])]
                original_market(alternate, env)
                opening_gain = actual - alternate[0].observation.farms[1]["money"]
            before = ordering_before.get(state["step"])
            orders = snapshot[1].action.get("market", [])
            if before:
                rank = {o[1]: i for i, o in enumerate(before) if len(o) >= 3 and o[0] == "SELL"}
                slots = [i for i, o in enumerate(orders) if len(o) >= 3 and o[0] == "SELL"]
                reordered = sorted((orders[i] for i in slots), key=lambda o: rank.get(o[1], 100))
                alternate = copy.deepcopy(snapshot)
                for i, order in zip(slots, reordered):
                    alternate[1].action["market"][i] = order
                if alternate[1].action["market"] != orders:
                    original_market(alternate, env)
                    ordering_gain += actual - alternate[0].observation.farms[1]["money"]
                    changed_ordering += 1
        finally:
            state["record"] = True

    engine._commit_unit, engine._process_market = commit, process
    engine._do_hire, engine._do_buy_land = hire, land
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)

    def meta_agent(obs, configuration):
        state["step"] = int(obs["step"])
        return meta["agent"](obs, configuration)

    try:
        env.run([planner["agent"], meta_agent])
    finally:
        engine._commit_unit, engine._process_market = original_commit, original_market
        engine._do_hire, engine._do_buy_land = original_hire, original_land
    banks = [s.observation.farms[i]["money"] for i, s in enumerate(env.steps[-1])]
    statuses = [s.status for s in env.steps[-1]]
    assert statuses == ["DONE", "DONE"], statuses
    for side in (0, 1):
        revenue = sum(v[1] for (t, s, op, item), v in fills.items() if s == side and op == "SELL")
        cost = sum(v[1] for (t, s, op, item), v in fills.items() if s == side and op != "SELL")
        assert 3000 + revenue - cost - atomic[side] == banks[side], (seed, side, banks, revenue, cost, atomic)
    return {"seed": seed, "banks": banks, "statuses": statuses,
            "opening_cash_gain_vs_buy5": opening_gain,
            "ordering_cash_gain_vs_inherited_sell_rank": ordering_gain,
            "ordering_changed_turns": changed_ordering,
            "fills": [[t, s, op, item, *v] for (t, s, op, item), v in sorted(fills.items())],
            "tags": {str(t): dict(v) for t, v in tags.items()}}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--seeds", nargs="+", type=int, default=[8301, 8302, 8303, 8304])
    parser.add_argument("--workers", type=int, default=2, choices=(1, 2))
    args = parser.parse_args()
    assert len(args.seeds) <= 4 and all(8301 <= s <= 8400 for s in args.seeds)
    with ProcessPoolExecutor(args.workers) as pool:
        games = list(pool.map(play, args.seeds))
    with (OUT / "fills.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed", "step", "side", "op", "product", "units", "dollars"])
        for game in games:
            writer.writerows([[game["seed"], *row] for row in game.pop("fills")])
    (OUT / "games.json").write_text(json.dumps(games, separators=(",", ":")))
    print(json.dumps([{k: v for k, v in g.items() if k != "tags"} for g in games]))

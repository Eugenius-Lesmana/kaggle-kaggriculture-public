"""Replay-only production capacity, yield, and market-fill audit.

Reads one .json.gz replay at a time. Run from any directory:
python evaluation/production_gap/analyze.py --intake "C:/.../research/intake/replays/29 Sept top"
"""
import argparse
import contextlib
import csv
import gzip
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
PRODUCTS = CROPS + tuple(ANIMALS.values()) + ("FERTILIZER",)
PHASES = ((0, 6, "d0_5"), (6, 12, "d6_11"), (12, 20, "d12_19"), (20, 28, "d20_27"))

with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
    import kaggle_environments.envs.kaggriculture.kaggriculture as engine


def phase(day):
    return next(name for start, stop, name in PHASES if start <= day < stop)


def write_csv(name, rows):
    if not rows:
        return
    with (OUT / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def replay_paths(intake):
    for folder in sorted(intake.iterdir()):
        if not folder.is_dir() or not folder.name.isdigit():
            continue
        identity = int(folder.name)
        index = {int(e["id"]): e for e in json.loads(
            (folder / "episodes.json").read_text(encoding="utf-8"))["episodes"]}
        for path in sorted(folder.glob("*.json.gz")):
            episode = index.get(int(path.name.split(".")[0]))
            if not episode:
                continue
            seats = [i for i, agent in enumerate(episode["agents"])
                     if agent["submissionId"] == identity]
            if len(seats) == 1:
                yield folder.name, path, seats[0]


def ripe_key(x, y, tile):
    if tile.get("kind") == "PLANT":
        return x, y, "PLANT", tile["crop"], tile["planted_day"]
    if "animal" in tile:
        return x, y, "ANIMAL", tile["animal"], tile["placed_day"]
    return None


def shadow(before, actions, configuration, wanted, counts, ripe_since, step_index):
    """Apply field actions, then market orders on copies; count actual fills."""
    market_needed = any(any(isinstance(o, list) and o and o[0] in ("SELL", "BUY_PRODUCT")
                            for o in (a.get("market") or [])) for a in actions)
    seats = (0, 1) if market_needed else (wanted,)
    farms = [None, None]
    privates = [None, None]
    for seat in seats:
        original = before[seat]["farms"][seat]
        tiles = [row.copy() for row in original["tiles"]]
        for position in [original["farmer"]] + list(original.get("hands") or []):
            x, y = position
            if isinstance(tiles[y][x], dict):
                tiles[y][x] = tiles[y][x].copy()
        farms[seat] = {**original, "farmer":original["farmer"].copy(),
                       "hands":[pos.copy() for pos in original.get("hands") or []],
                       "unlocked_quadrants":original["unlocked_quadrants"].copy(), "tiles":tiles}
        private = before[seat]["private"]
        privates[seat] = {**private, "shed":private["shed"].copy(),
                          "seeds":private["seeds"].copy(),
                          "inventories":[inv.copy() for inv in private["inventories"]]}
        commands = [actions[seat].get("farmer", ["PASS"])] + list(actions[seat].get("hands") or [])
        demand = Counter(a[1] for a in commands if isinstance(a, list) and len(a) >= 2 and a[0] == "PLANT")
        blocked = {crop for crop, n in demand.items() if n > privates[seat]["seeds"].get(crop, 0)}
        for worker, command in enumerate(commands):
            if not isinstance(command, list) or not command:
                continue
            if len(command) >= 2 and command[0] == "PLANT" and command[1] in blocked:
                command = ["PASS"]
            pos = engine._farmer_position(farms[seat], worker)
            if pos is None:
                continue
            x, y = pos
            tile = farms[seat]["tiles"][y][x]
            tile = tile if isinstance(tile, dict) else {}
            before_inv = engine._farmer_inventory(privates[seat], worker).copy()
            product = tile.get("crop") or ANIMALS.get(tile.get("animal"))
            key = ripe_key(x, y, tile)
            engine._apply_unit_action(farms[seat], privates[seat], worker, command,
                                      configuration.get("boardSize", 10),
                                      before[0]["day"], configuration.get("turnsPerDay", 24),
                                      configuration.get("shedCapacity", 100))
            if seat != wanted:
                continue
            after_inv = engine._farmer_inventory(privates[seat], worker)
            op = command[0]
            if op == "HARVEST" and product:
                quantity = max(0, after_inv.get(product, 0) - before_inv.get(product, 0))
                if quantity:
                    counts[("harvest", product)] += quantity
                    counts[("harvest_events", product)] += 1
                    delay = (step_index - ripe_since.get(key, step_index)) / configuration.get("turnsPerDay", 24)
                    counts[("delay_days", product)] += max(0, delay)
                    counts[("delay_unit_days", product)] += max(0, delay) * quantity
                    ripe_since.pop(key, None)
            elif op == "COLLECT_FERTILIZER":
                counts[("harvest", "FERTILIZER")] += max(0, after_inv.get("FERTILIZER", 0) - before_inv.get("FERTILIZER", 0))
            elif op == "FEED":
                counts[("consume", "WHEAT")] += max(0, before_inv.get("WHEAT", 0) - after_inv.get("WHEAT", 0))
            elif op == "FERTILIZE":
                counts[("consume", "FERTILIZER")] += max(0, before_inv.get("FERTILIZER", 0) - after_inv.get("FERTILIZER", 0))
    if not market_needed:
        return
    market_before = before[0]["market"]
    market = {**market_before, "inventory":market_before["inventory"].copy(),
              "prices":market_before["prices"].copy()}
    state = [SimpleNamespace(observation=SimpleNamespace(
        farms=farms, market=market, private=privates[seat]), action=actions[seat])
        for seat in (0, 1)]
    env = SimpleNamespace(configuration=configuration)
    fills = [Counter(), Counter()]
    original_commit = engine._commit_unit
    ids = {id(farms[seat]): seat for seat in (0, 1)}

    def tracked_commit(op, item, price, farm, private, market, shed_capacity=100):
        ok = original_commit(op, item, price, farm, private, market, shed_capacity)
        if ok and op in ("SELL", "BUY_PRODUCT"):
            fills[ids[id(farm)]][(op, item)] += 1
        return ok

    engine._commit_unit = tracked_commit
    try:
        engine._process_market(state, env)
    finally:
        engine._commit_unit = original_commit
    counts["market_steps"] += 1
    # Money is unaffected by the later town drain and day refresh.
    return farms, fills


def analyze_game(group, path, seat):
    with gzip.open(path, "rt", encoding="utf-8") as file:
        data = json.load(file)
    steps = data["steps"]
    configuration = data["configuration"]
    by_phase = {name: Counter() for _, _, name in PHASES}
    for day in range(28):
        index = day * 24 + 23
        if index >= len(steps):
            break
        c = by_phase[phase(day)]
        farm = steps[index][seat]["observation"]["farms"][seat]
        c["days"] += 1
        c["plots_owned"] += 25 * len(farm["unlocked_quadrants"])
        for row in farm["tiles"]:
            for tile in row:
                if tile is None:
                    c["empty"] += 1
                elif tile == "LOCKED":
                    continue
                elif tile.get("kind") == "WEED":
                    c["weed"] += 1
                elif tile.get("kind") == "PLANT":
                    product = tile["crop"]
                    crop = engine.CROPS[product]
                    age = day - tile["planted_day"]
                    c[("capacity_days", product)] += 1
                    c["plant_days"] += 1
                    fertilized = tile.get("fertilized_until_day", -1) >= day
                    c[("fert_days", product)] += fertilized
                    c["fert_days"] += fertilized
                    if crop["ongoing"]:
                        since = age + 1 - crop["first_yield_day"]
                        scheduled = since >= 0 and since % crop["interval"] == 0 and since // crop["interval"] < crop["max_yield"]
                        in_window = scheduled
                        planner_window = fertilized and scheduled
                    else:
                        in_window = (crop["max_yield_day"] + 1)//2 <= age <= crop["max_yield_day"]
                        planner_window = in_window and tile.get("yield_units", 0) < crop["max_yield"]
                    if in_window:
                        c[("window_days", product)] += 1
                        c[("watered_days", product)] += bool(tile["watered_today"])
                    if planner_window:
                        c["planner_window_days"] += 1
                        c["planner_window_watered"] += bool(tile["watered_today"])
                elif "animal" in tile:
                    product = ANIMALS[tile["animal"]]
                    c[("capacity_days", product)] += 1
                    c[("capacity_days", "FERTILIZER")] += 1
                    c["animal_days"] += 1
                    c[("fed_days", product)] += bool(tile["fed_today"])
                    c[("cared_days", product)] += bool(tile["cared_today"])
                else:
                    c["empty_structure"] += 1
    ripe_since = {}
    for i in range(1, min(len(steps), 28 * configuration.get("turnsPerDay", 24) + 1)):
        before = [steps[i-1][p]["observation"] for p in (0, 1)]
        after = [steps[i][p]["observation"] for p in (0, 1)]
        c = by_phase[phase(before[0]["day"])]
        active = set()
        for y, row in enumerate(before[seat]["farms"][seat]["tiles"]):
            for x, tile in enumerate(row):
                if isinstance(tile, dict):
                    if tile.get("kind") == "PLANT":
                        c[("exposure_hours", tile["crop"])] += 1
                    elif "animal" in tile:
                        c[("exposure_hours", ANIMALS[tile["animal"]])] += 1
                        c[("exposure_hours", "FERTILIZER")] += 1
                if not isinstance(tile, dict) or tile.get("yield_units", 0) <= 0:
                    continue
                key = ripe_key(x, y, tile)
                if not key:
                    continue
                if tile.get("kind") == "PLANT":
                    age = before[0]["day"] - tile["planted_day"]
                    if age < engine.CROPS[tile["crop"]]["first_yield_day"]:
                        continue
                active.add(key)
                ripe_since.setdefault(key, i-1)
        for key in list(ripe_since):
            if key not in active:
                del ripe_since[key]
        actions = [steps[i][p].get("action") or {} for p in (0, 1)]
        for order in actions[seat].get("market") or []:
            if isinstance(order, list) and len(order) >= 3 and order[0] == "BUY_PRODUCT" and order[1] in ("WHEAT", "FERTILIZER"):
                c[("buy_request", order[1])] += max(0, int(order[2]))
        result = shadow(before, actions, configuration, seat, c, ripe_since, i-1)
        if result:
            farms, fills = result
            if all(round(farms[p]["money"]) == round(after[p]["farms"][p]["money"]) for p in (0, 1)):
                c["market_verified"] += 1
                for (op, product), quantity in fills[seat].items():
                    c[("buy_fill" if op == "BUY_PRODUCT" else "sold", product)] += quantity
            else:
                c["market_unverified"] += 1
    for start, stop, name in PHASES:
        if stop * 24 >= len(steps):
            continue
        opening = holdings(steps[start*24][seat]["observation"])
        closing = holdings(steps[stop*24][seat]["observation"])
        for product in PRODUCTS:
            by_phase[name][("opening_stock",product)] = opening[product]
            by_phase[name][("closing_stock",product)] = closing[product]
    return by_phase


def holdings(observation):
    total = Counter(observation["private"].get("shed") or {})
    for inventory in observation["private"].get("inventories") or []:
        total.update(inventory)
    return total


def planner_rows():
    raw = subprocess.check_output(["git", "show",
        "dev/eugene-claude-routeopt:evaluation/routeopt/production_v010.json"], cwd=ROOT)
    return json.loads(raw)["rows"]


def write_tables(games, include_planner=True):
    rows = []
    for group, game, phases in games:
        for phase_name, c in phases.items():
            for product in PRODUCTS:
                rows.append(dict(group=group, game=game, phase=phase_name, product=product,
                    days=c["days"], plots_owned=c["plots_owned"], empty=c["empty"], weed=c["weed"],
                    empty_structure=c["empty_structure"], plant_days=c["plant_days"],
                    animal_days=c["animal_days"], capacity_days=c[("capacity_days",product)], exposure_hours=c[("exposure_hours",product)],
                    harvested=c[("harvest",product)], harvest_events=c[("harvest_events",product)],
                    yield_per_capacity_day=c[("harvest",product)]/c[("capacity_days",product)] if c[("capacity_days",product)] else 0,
                    watered_window_days=c[("watered_days",product)], window_days=c[("window_days",product)],
                    fertilized_days=c[("fert_days",product)],
                    fed_days=c[("fed_days",product)], cared_days=c[("cared_days",product)],
                    delay_days_sum=c[("delay_days",product)], delay_unit_days_sum=c[("delay_unit_days",product)],
                    buy_requests=c[("buy_request",product)], buy_fills=c[("buy_fill",product)],
                    sold=c[("sold",product)], consumed=c[("consume",product)],
                    opening_stock=c[("opening_stock",product)], closing_stock=c[("closing_stock",product)],
                    conservation_residual=c[("opening_stock",product)]+c[("harvest",product)]+c[("buy_fill",product)]-c[("consume",product)]-c[("sold",product)]-c[("closing_stock",product)],
                    market_verified=c["market_verified"], market_unverified=c["market_unverified"]))
    write_csv("game_product_phase.csv", rows)
    groups = defaultdict(list)
    for group, game, phases in games:
        groups[group].append((game, phases))
        if group != "56640149":
            groups["top_three"].append((game, phases))
    if include_planner:
        planner = []
        for i, row in enumerate(planner_rows()):
            phases = {}
            for name, values in row["phases"].items():
                c = Counter()
                c["days"] = values.get("days", 0)
                c["plots_owned"] = values.get("plots_owned", 0)
                c["empty"] = values.get("empty_cell_days", 0)
                c["weed"] = values.get("weed_cell_days", 0)
                c["plant_days"] = values.get("plant_days", 0)
                c["animal_days"] = values.get("animal_days", 0)
                c["planner_window_days"] = values.get("window_plant_days", 0)
                c["planner_window_watered"] = values.get("window_watered", 0)
                c["fert_days"] = values.get("fertilized_plant_days", 0)
                for product in PRODUCTS:
                    capacity = ("animal_days " + next(a for a,p in ANIMALS.items() if p == product)
                                if product in ANIMALS.values() else "plant_days " + product)
                    if product == "FERTILIZER":
                        c[("capacity_days",product)] = c["animal_days"]
                        c[("harvest",product)] = values.get("COLLECT_FERTILIZER_ok", 0)
                    else:
                        c[("capacity_days",product)] = values.get(capacity, 0)
                        c[("harvest",product)] = values.get("harvest_units " + product, 0)
                    c[("buy_request",product)] = values.get("buy_request " + product, 0)
                c[("consume","WHEAT")] = values.get("FEED_ok", 0)
                c[("consume","FERTILIZER")] = values.get("FERTILIZE_ok", 0)
                phases[name] = c
            planner.append((f"planner/{i}", phases))
        groups["planner_v010"] = planner
    summary = []
    for group, members in sorted(groups.items()):
        for _, _, name in PHASES:
            counters = [phases[name] for _, phases in members]
            n = len(counters)
            c = sum(counters, Counter())
            days = c["days"] / n
            for product in PRODUCTS:
                cap = c[("capacity_days",product)] / n
                produced = c[("harvest",product)] / n
                summary.append(dict(group=group, phase=name, product=product, games=n,
                    days=days, plots_owned=c["plots_owned"]/n/days if days else 0,
                    empty_cells=c["empty"]/n/days if days else 0,
                    weed_cells=c["weed"]/n/days if days else 0,
                    empty_structures=c["empty_structure"]/n/days if days else 0,
                    plant_cells=c["plant_days"]/n/days if days else 0,
                    animals=c["animal_days"]/n/days if days else 0,
                    capacity_cells=cap/days if days else 0, capacity_days=cap,
                    hourly_capacity_cells=c[("exposure_hours",product)]/24/n/days if group != "planner_v010" and days else "",
                    yield_per_exposure_day=c[("harvest",product)]/(c[("exposure_hours",product)]/24) if group != "planner_v010" and c[("exposure_hours",product)] else "",
                    harvested_units=produced, yield_per_capacity_day=produced/cap if cap else 0,
                    water_window_share=c[("watered_days",product)]/c[("window_days",product)] if c[("window_days",product)] else "",
                    fertilized_share=c[("fert_days",product)]/c[("capacity_days",product)] if group != "planner_v010" and product in CROPS and c[("capacity_days",product)] else "",
                    fed_share=c[("fed_days",product)]/c[("capacity_days",product)] if product in ANIMALS.values() and c[("capacity_days",product)] else "",
                    cared_share=c[("cared_days",product)]/c[("capacity_days",product)] if product in ANIMALS.values() and c[("capacity_days",product)] else "",
                    harvest_delay_days=c[("delay_days",product)]/c[("harvest_events",product)] if c[("harvest_events",product)] else "",
                    buy_requests=c[("buy_request",product)]/n,
                    buy_fills=c[("buy_fill",product)]/n if group != "planner_v010" else "",
                    sold=c[("sold",product)]/n if group != "planner_v010" else "",
                    consumed=c[("consume",product)]/n,
                    opening_stock=c[("opening_stock",product)]/n if group != "planner_v010" else "",
                    closing_stock=c[("closing_stock",product)]/n if group != "planner_v010" else "",
                    conservation_residual=(c[("opening_stock",product)]+c[("harvest",product)]+c[("buy_fill",product)]-c[("consume",product)]-c[("sold",product)]-c[("closing_stock",product)])/n if group != "planner_v010" else "",
                    market_verified=c["market_verified"], market_unverified=c["market_unverified"],
                    planner_window_watered_share=c["planner_window_watered"]/c["planner_window_days"] if c["planner_window_days"] else ""))
    write_csv("group_product_phase.csv", summary)
    lookup = {(r["group"],r["phase"],r["product"]):r for r in summary}
    decomposition = []
    if include_planner and "top_three" in groups:
        for _, _, name in PHASES:
            for product in PRODUCTS:
                top, base = lookup["top_three",name,product], lookup["planner_v010",name,product]
                ct, cb = top["capacity_days"], base["capacity_days"]
                yt, yb = top["yield_per_capacity_day"], base["yield_per_capacity_day"]
                gap = top["harvested_units"]-base["harvested_units"]
                cap_effect = (ct-cb)*(yt+yb)/2 if ct and cb else gap
                yield_effect = (yt-yb)*(ct+cb)/2 if ct and cb else 0
                buy_top = top["buy_fills"]
                buy_req_base = base["buy_requests"]
                decomposition.append(dict(phase=name, product=product,
                    harvest_gap=gap, capacity_effect=cap_effect, yield_effect=yield_effect,
                    top_buy_fills=buy_top, planner_buy_requests=buy_req_base,
                    buy_gap_lower=buy_top-buy_req_base, buy_gap_upper=buy_top,
                    top_sold=top["sold"], planner_sold=""))
    write_csv("unadjusted_decomposition.csv", decomposition)
    print(json.dumps({"groups":{key:len(value) for key,value in groups.items()},
                      "market_unverified":{key:sum(c["market_unverified"] for _,phases in value for c in phases.values())
                                           for key,value in groups.items() if key!="planner_v010"}}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    games = []
    for index, (group, path, seat) in enumerate(replay_paths(args.intake)):
        if args.limit and index >= args.limit:
            break
        games.append((group, path.name, analyze_game(group, path, seat)))
        if (index + 1) % 50 == 0:
            print(f"replays {index+1}", flush=True)
    write_tables(games)


if __name__ == "__main__":
    main()


"""Measure shop-conditioned farm layouts from the committed top-four replays.

Run from the repository root: python evaluation/modes/study.py
"""
import collections
import gzip
import json
import os
import sys
from pathlib import Path

import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import adjusted_mutual_info_score, silhouette_score
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import Ridge

COHORT = sys.argv[1] if len(sys.argv) > 1 else "24"
if COHORT not in ("24", "29"):
    raise SystemExit("usage: python evaluation/modes/study.py [24|29]")
ROOT = Path("research/intake/replays/24 Sept") if COHORT == "24" else Path(
    os.environ.get("KAGG_MODES_29_ROOT", r"<repo>/research\intake\replays\29 Sept top")
)
OUT = Path("evaluation/modes") / ("29-sept" if COHORT == "29" else "24-sept")
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("SHEEP", "COW", "GOOSE")
SHOP_PRODUCTS = {
    "YARN_STORE": ("WOOL",),
    "PET_CAFE": ("CARROT",),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
    "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "BAKERY": ("EGG", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"),
}
PRODUCT_TARGET = {
    "WOOL": "SHEEP", "MILK": "COW", "EGG": "GOOSE",
    **{crop: crop for crop in CROPS},
}
FEATURES = (*CROPS, *ANIMALS)
SHOPS = tuple(SHOP_PRODUCTS)
OPEN_DAYS = tuple(range(3, 25, 3))
LAST_PRODUCTION_AGE = {"WHEAT": 4, "CARROT": 3, "TOMATO": 11,
                       "STRAWBERRY": 16, "MELON": 12}


def counts(farm):
    result = collections.Counter()
    tiles = []
    for y, row in enumerate(farm["tiles"]):
        for x, tile in enumerate(row):
            if tile == "LOCKED":
                continue
            if tile is None:
                tiles.append([x, y, None, None, None])
                continue
            kind = tile["kind"]
            crop = tile.get("crop") if kind == "PLANT" else None
            animal = tile.get("animal") if kind in ("COOP", "PASTURE") else None
            result[kind] += 1
            if crop:
                result[crop] += 1
            if animal:
                result[animal] += 1
            tiles.append([x, y, kind, crop or animal, tile.get("planted_day")])
    return result, tiles


def record(obs, team, episode, seat, day):
    farm = obs["farms"][seat]
    counts_, tiles = counts(farm)
    shops = collections.Counter(obs["town"]["unlocked_shops"])
    return {
        "game": f"{team}/{episode}/{seat}", "team": team, "episode": episode,
        "seat": seat, "day": day, "step": day * 24,
        "shops": dict(shops), "demand": {
            product: sum(n for shop, n in shops.items() if product in SHOP_PRODUCTS[shop])
            for product in PRODUCT_TARGET
        },
        "features": {name: counts_[name] for name in FEATURES},
        "plots": len(tiles), "pastures": counts_["PASTURE"],
        "coops": counts_["COOP"], "hands": len(farm["hands"]),
        "money": farm["money"], "tiles": tiles,
    }


def extract():
    opening, daily, skeleton, placement, digs = [], [], [], [], []
    jobs = []
    if COHORT == "29":
        for folder in sorted(ROOT.iterdir()):
            if not folder.is_dir():
                continue
            manifest = folder / "episodes.json"
            if not manifest.exists():
                raise RuntimeError(f"still downloading: {folder}")
            submission = int(folder.name)
            for episode in json.loads(manifest.read_text(encoding="utf-8"))["episodes"]:
                if episode.get("state") != "COMPLETED":
                    continue
                seats = [i for i, a in enumerate(episode["agents"])
                         if a.get("submissionId") == submission]
                if len(seats) != 1:
                    continue
                path = folder / f"{episode['id']}.json.gz"
                if path.exists() and path.stat().st_size:
                    jobs.append((path, None, seats[0], episode["id"]))
    else:
        top_teams = {"Team B", "Team A", "VADIMVASILENKO", "UNKNOWNMOTHERGOOSE"}
        episodes = set()
        for path in sorted(ROOT.rglob("*.json.gz")):
            replay = json.load(gzip.open(path, "rt"))
            episode = replay["info"]["EpisodeId"]
            if episode in episodes:
                continue
            episodes.add(episode)
            for seat, agent in enumerate(replay["info"]["Agents"]):
                team = agent["Name"]
                if "".join(c for c in team.upper() if c.isalnum()) in top_teams:
                    jobs.append((path, team, seat, episode))
    for path, team, seat, episode in jobs:
        try:
            replay = json.load(gzip.open(path, "rt"))
        except (OSError, ValueError) as error:
            print(f"skipping unreadable replay {path}: {error}", file=sys.stderr)
            continue
        if team is None:
            team = replay["info"]["Agents"][seat]["Name"]
        steps = replay["steps"]
        last_free = {}
        land_steps = []
        land_realized = []
        owned_before = None
        hires = collections.Counter()
        early = []
        for step, both in enumerate(steps):
            state = both[seat]
            obs = state["observation"]
            day = obs["day"]
            if obs["hour"] == 0:
                row = record(obs, team, episode, seat, day)
                daily.append({k: v for k, v in row.items() if k != "tiles"})
                if day in OPEN_DAYS:
                    opening.append(row)
            farm_now = obs["farms"][seat]
            owned = len(farm_now["unlocked_quadrants"])
            if owned_before is not None and owned > owned_before:
                land_realized.append(step)
            owned_before = owned
            hires[day] = max(hires[day], len(farm_now["hands"]))
            if step == 0:
                continue
            action = state.get("action") or {}
            act_obs = steps[step - 1][seat]["observation"]
            act_day = act_obs["day"]
            if step <= 144:
                early.append(action)
            for order in action.get("market", []):
                if not order:
                    continue
                if order[0] == "BUY_LAND":
                    land_steps.append(step)
            farm = act_obs["farms"][seat]
            positions = [farm["farmer"], *farm["hands"]]
            actions = [action.get("farmer", ["PASS"]), *action.get("hands", [])]
            for pos, unit_action in zip(positions, actions):
                x, y = pos
                tile = farm["tiles"][y][x]
                op = unit_action[0]
                if op in ("HARVEST", "DIG"):
                    last_free[x, y] = {
                        "op": op, "step": step,
                        "crop": tile.get("crop") if isinstance(tile, dict) else None,
                        "planted_day": tile.get("planted_day") if isinstance(tile, dict) else None,
                    }
                    if op == "DIG":
                        digs.append({"game": row["game"], "day": act_day, "step": step,
                                     "kind": tile.get("kind") if isinstance(tile, dict) else None,
                                     "crop": tile.get("crop") if isinstance(tile, dict) else None,
                                     "age_days": act_day - tile["planted_day"] if isinstance(tile, dict) and tile.get("planted_day") is not None else None,
                                     "max_lifespan_step": tile.get("max_lifespan_step") if isinstance(tile, dict) else None})
                elif op == "PLANT":
                    freed = last_free.get((x, y), {})
                    placement.append({
                        "game": row["game"], "team": team, "step": step, "day": act_day,
                        "crop": unit_action[1], "x": x, "y": y,
                        "preceding": freed.get("op", "NEW_OR_IDLE"),
                        "preceding_crop": freed.get("crop"),
                        "gap_steps": step - freed["step"] if freed else None,
                        "premature_dig": freed.get("op") == "DIG" and freed.get("crop") is not None
                        and freed.get("planted_day") is not None
                        and act_day - freed["planted_day"] < 4,
                    })
                    last_free.pop((x, y), None)
        skeleton.append({"game": row["game"], "team": team, "land_steps": land_steps,
                         "land_realized": land_realized,
                         "hires": dict(hires), "early": early})
    return opening, daily, skeleton, placement, digs


def write_gz(path, rows):
    with gzip.open(path, "wt", encoding="utf-8") as file:
        for row in rows:
            file.write(json.dumps(row, separators=(",", ":")) + "\n")


def loo_r2(rows, feature, with_shops):
    groups = np.array([r["game"] for r in rows])
    teams = sorted({r["team"] for r in rows})
    days = sorted({r["day"] for r in rows})
    x = np.array([[int(r["team"] == t) for t in teams[1:]]
                  + [int(r["day"] == d) for d in days[1:]]
                  + ([r["shops"].get(shop, 0) for shop in SHOPS] if with_shops else [])
                  for r in rows], float)
    y = np.array([r["features"][feature] / r["plots"] for r in rows])
    pred = np.empty_like(y)
    for train, test in GroupKFold(n_splits=min(10, len(set(groups)))).split(x, y, groups):
        pred[test] = Ridge(alpha=1).fit(x[train], y[train]).predict(x[test])
    return round(float(1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)), 3)


def analyze(opening, daily, skeleton, placement, digs):
    x = np.array([[r["features"][f] / r["plots"] for f in FEATURES] for r in opening])
    fits = {}
    for k in range(2, 9):
        model = KMeans(n_clusters=k, n_init=30, random_state=7201).fit(x)
        fits[k] = (model, silhouette_score(x, model.labels_))
    k = max(fits, key=lambda n: fits[n][1])
    model, silhouette = fits[k]
    labels = model.labels_
    sizes = collections.Counter(int(label) for label in labels)
    sorted_sizes = sorted(sizes.values(), reverse=True)
    cover = next(i for i in range(1, k + 1) if sum(sorted_sizes[:i]) >= .8 * len(opening))
    for row, label in zip(opening, labels):
        row["cluster"] = int(label)
    exact = collections.defaultdict(list)
    for row in opening:
        exact[row["day"], tuple(row["shops"].get(s, 0) for s in SHOPS)].append(row["cluster"])
    repeated = [values for values in exact.values() if len(values) >= 2]
    agreement = sum(collections.Counter(v).most_common(1)[0][1] for v in repeated) / sum(map(len, repeated)) if repeated else None
    shop_presence = [tuple(int(row["shops"].get(s, 0) > 0) for s in SHOPS) for row in opening]
    ami = adjusted_mutual_info_score([str(v) for v in shop_presence], labels)
    r2 = {f: {"baseline": loo_r2(opening, f, False), "plus_shops": loo_r2(opening, f, True)} for f in FEATURES}
    group_effect = {}
    for shop, products in SHOP_PRODUCTS.items():
        group_effect[shop] = {}
        for product in products:
            target = PRODUCT_TARGET[product]
            # Same day and team, shop present versus absent; descriptive, not causal.
            diffs = []
            for day in OPEN_DAYS:
                for team in {r["team"] for r in opening}:
                    subset = [r for r in opening if r["day"] == day and r["team"] == team]
                    yes = [r["features"][target] / r["plots"] for r in subset if r["shops"].get(shop, 0)]
                    no = [r["features"][target] / r["plots"] for r in subset if not r["shops"].get(shop, 0)]
                    if yes and no:
                        diffs.append(np.mean(yes) - np.mean(no))
            group_effect[shop][target] = round(float(np.mean(diffs)), 3) if diffs else None
    actions = [s["early"] for s in skeleton]
    majority = [collections.Counter(json.dumps(a[i], sort_keys=True) for a in actions).most_common(1)[0][1] / len(actions) for i in range(144)]
    action_agreement = {str(day): round(float(np.mean(majority[day * 24:(day + 1) * 24])), 3)
                        for day in range(6)}
    land = collections.Counter(tuple(s["land_steps"]) for s in skeleton)
    land_realized = collections.Counter(tuple(s["land_realized"]) for s in skeleton)
    hire_patterns = collections.Counter(tuple(s["hires"].get(day, 0) for day in range(30)) for s in skeleton)
    hire_by_day = {str(day): collections.Counter(s["hires"].get(day, 0) for s in skeleton) for day in range(30)}
    # Step-zero replay action is a placeholder; report real opener agreement from step 1.
    timing = {}
    by_game_day = {(r["game"], r["day"]): r for r in daily}
    for shop, products in SHOP_PRODUCTS.items():
        events = []
        for row in opening:
            day = row["day"]
            previous = by_game_day.get((row["game"], day - 1))
            if not previous or row["shops"].get(shop, 0) <= previous["shops"].get(shop, 0):
                continue
            for product in products:
                target = PRODUCT_TARGET[product]
                start = row["features"][target]
                lag = next((d - day for d in range(day, min(day + 4, 30))
                            if (r := by_game_day.get((row["game"], d))) and r["features"][target] > start), None)
                events.append({"game": row["game"], "day": day, "product": product,
                               "target": target, "lag_days": lag})
        timing[shop] = {"events": len(events), "net_increase_3d": sum(e["lag_days"] is not None for e in events),
                        "median_lag": float(np.median([e["lag_days"] for e in events if e["lag_days"] is not None]))
                        if any(e["lag_days"] is not None for e in events) else None}
    return {"games": len(skeleton), "openings": len(opening), "teams": dict(collections.Counter(s["team"] for s in skeleton)),
            "cluster": {"k_silhouette_best": k, "silhouette": round(float(silhouette), 3),
                        "silhouettes": {str(n): round(float(v[1]), 3) for n, v in fits.items()},
                        "sizes": dict(sizes), "modes_for_80pct_openings": cover,
                        "exact_shop_day_repeated_strata": len(repeated), "exact_shop_day_agreement": round(agreement, 3) if agreement else None,
                        "shop_presence_ami": round(float(ami), 3),
                        "centers": [{f: round(float(v), 3) for f, v in zip(FEATURES, center)} for center in model.cluster_centers_]},
            "held_out_r2": r2, "same_day_team_shop_effect": group_effect, "timing": timing,
            "skeleton": {"step_action_majority_mean_day0_5": round(float(np.mean(majority)), 3),
                         "step_action_majority_min_day0_5": round(min(majority), 3),
                         "action_agreement_by_day": action_agreement,
                         "land_patterns": [{"steps": list(steps), "games": n} for steps, n in land.most_common()],
                         "land_realized_patterns": [{"steps": list(steps), "games": n} for steps, n in land_realized.most_common()],
                         "hire_pattern_count": len(hire_patterns),
                         "hire_by_day": {day: dict(counter) for day, counter in hire_by_day.items()}},
            "placement": {"total": len(placement), "preceding": dict(collections.Counter(p["preceding"] for p in placement)),
                          "preceded_by_crop_dig": sum(p["preceding"] == "DIG" and p["preceding_crop"] is not None for p in placement),
                          "premature_crop_digs": sum(p["premature_dig"] for p in placement),
                          "digs": len(digs), "digs_by_kind": dict(collections.Counter(d["kind"] for d in digs)),
                          "crop_digs_before_final_production": sum(d["crop"] in LAST_PRODUCTION_AGE and d["age_days"] < LAST_PRODUCTION_AGE[d["crop"]] for d in digs),
                          "crop_digs_at_or_after_final_production": sum(d["crop"] in LAST_PRODUCTION_AGE and d["age_days"] >= LAST_PRODUCTION_AGE[d["crop"]] for d in digs)}}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    opening, daily, skeleton, placement, digs = extract()
    result = analyze(opening, daily, skeleton, placement, digs)
    write_gz(OUT / "opening_tiles.jsonl.gz", opening)
    write_gz(OUT / "daily_features.jsonl.gz", daily)
    write_gz(OUT / "placements.jsonl.gz", placement)
    write_gz(OUT / "digs.jsonl.gz", digs)
    write_gz(OUT / "skeleton.jsonl.gz", [{k: v for k, v in row.items() if k != "early"} for row in skeleton])
    (OUT / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("games", "openings", "teams", "cluster", "placement")}, indent=2))


if __name__ == "__main__":
    main()

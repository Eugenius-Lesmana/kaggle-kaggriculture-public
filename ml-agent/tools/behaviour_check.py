"""Test Eugene's replay observations (2026-10-23) on all 552 L1 mornings: template (its recorded day) vs the
4th-place agent (its L1 segment from the same morning), seat 0.

python tools/behaviour_check.py
Per job carried out, records what the tile held before (crop or animal, units waiting), the hour, the product's
price and the worker. Summaries: watering coverage by crop at the end of the day, units waiting when each kind is
harvested or collected, collection vs price, fertilizer by crop, last herd job of the day, how far each worker
roams, and seeds bought by crop.
"""
import csv
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from kagml.paths import data_root, runs  # noqa: E402

EL3 = REPO.parent / "Kaggle-Kaggriculture" / ".scratch" / "template-bench" / "runs" / "el3"
PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
DIRS = {"NORTH": (0, -1), "SOUTH": (0, 1), "EAST": (1, 0), "WEST": (-1, 0)}


def units_of(farm):
    return [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]


def day_rows(frames, game, day, player):
    jobs, roam, end = [], defaultdict(set), {}
    for f, nxt in zip(frames[:24], frames[1:25]):
        obs = f[0]["observation"]
        act = nxt[0]["action"] or {}
        farm = obs["farms"][0]
        prices = obs["market"]["prices"]
        cmds = [act.get("farmer")] + list(act.get("hands") or [])
        for u, (pos, cmd) in enumerate(zip(units_of(farm), cmds)):
            roam[u].add(pos)
            if not cmd or cmd[0] in DIRS or cmd[0] == "PASS":
                continue
            x, y = pos
            t = farm["tiles"][y][x] if 0 <= y < len(farm["tiles"]) and 0 <= x < len(farm["tiles"][0]) else None
            t = t if isinstance(t, dict) else {}
            thing = t.get("crop") or t.get("animal")
            item = t.get("crop") or PRODUCT.get(t.get("animal"))
            jobs.append({"game": game, "day": day, "player": player, "hour": obs["hour"], "unit": u, "kind": cmd[0],
                         "item": cmd[1] if len(cmd) > 1 else None, "on": thing, "waiting": t.get("yield_units"),
                         "price": prices.get(item) if item else None})
        for o in act.get("market") or []:
            if o and o[0] == "BUY_SEED":
                end[f"buy_{o[1].lower()}"] = end.get(f"buy_{o[1].lower()}", 0) + (int(o[2]) if len(o) > 2 else 1)
    last = frames[23][0]["observation"]["farms"][0]     # hour 23, before midnight clears the flags
    plants = [t for row in last["tiles"] for t in row if isinstance(t, dict) and t.get("kind") == "PLANT"]
    for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        mine = [t for t in plants if t.get("crop") == crop]
        end[f"n_{crop.lower()}"] = len(mine)
        end[f"watered_{crop.lower()}"] = sum(bool(t.get("watered_today")) for t in mine)
    animals = [t for row in last["tiles"] for t in row if isinstance(t, dict) and t.get("animal")]
    end["animals"] = len(animals)
    end["animals_waiting_units"] = sum(t.get("yield_units", 0) for t in animals)
    end["roam_tiles_per_worker"] = sum(len(v) for v in roam.values()) / max(1, len(roam))
    return jobs, {"game": game, "day": day, "player": player, **end}


def main():
    jobs, days = [], []
    for r in csv.DictReader(open(REPO / "manifests" / "ownfarm.csv")):
        game, day = r["game"], int(r["day"])
        if not days or days[-1]["game"] != game:
            parent = json.load(open(EL3 / f"{game}.json"))
        seg = json.load(gzip.open(data_root() / r["file"], "rt"))["steps"]
        for player, frames in (("template", parent["steps"][day * 24: day * 24 + 25]), ("fourth", seg)):
            j, d = day_rows(frames, game, day, player)
            jobs += j
            days.append(d)
    out = runs() / "behaviour"
    out.mkdir(parents=True, exist_ok=True)
    J, D = pd.DataFrame(jobs), pd.DataFrame(days)
    J.to_csv(out / "jobs.csv.gz", index=False)
    D.to_csv(out / "days.csv", index=False)
    pd.set_option("display.width", 220)
    print("== Watering coverage at the end of the day (share of each crop's tiles watered)")
    for c in ("strawberry", "tomato", "melon", "wheat", "carrot"):
        g = D.groupby("player")[[f"watered_{c}", f"n_{c}"]].sum()
        print(f"  {c:10s}", {p: f"{g.loc[p, f'watered_{c}'] / max(1, g.loc[p, f'n_{c}']):.0%} of {g.loc[p, f'n_{c}'] / 552:.1f}/day" for p in g.index})
    print("== Harvests per day and units waiting when harvested (by crop)")
    h = J[(J.kind == "HARVEST") & J.on.notna()]
    print(h.groupby(["on", "player"]).agg(per_day=("waiting", lambda s: len(s) / 552), mean_waiting=("waiting", "mean")).round(2).unstack())
    print("== Animal products collected vs price (collections per day; mean price when collected)")
    a = h[h.on.isin(["GOOSE", "COW", "SHEEP"])]
    print(a.groupby(["on", "player"]).agg(per_day=("price", lambda s: len(s) / 552), mean_price=("price", "mean")).round(1).unstack())
    cows = a[a.on == "COW"]
    cows = cows.assign(band=pd.cut(cows.price, [0, 30, 60, 90, 1000]))
    print("  milk collections by price band:"); print(cows.groupby(["band", "player"], observed=False).size().unstack())
    print("== Fertilizer applied, by crop (per day)")
    print((J[J.kind == "FERTILIZE"].groupby(["on", "player"]).size().unstack() / 552).round(2))
    print("== Herd jobs (FEED, CARE): last hour of the day (mean), and units left waiting on animals at night")
    herd = J[J.kind.isin(["FEED", "CARE"])].groupby(["player", "game", "day"]).hour.max().groupby("player").mean().round(1)
    print("  last herd hour", herd.to_dict(), " waiting at night", D.groupby("player").animals_waiting_units.mean().round(1).to_dict())
    print("== Distinct tiles each worker stands on per day (lower = stays in its own area)")
    print("  ", D.groupby("player").roam_tiles_per_worker.mean().round(1).to_dict())
    print("== Seeds bought per day")
    print((D.groupby("player")[[c for c in D if c.startswith("buy_")]].sum() / 552).round(2))


if __name__ == "__main__":
    main()

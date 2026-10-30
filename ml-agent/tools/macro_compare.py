"""Macro comparison over full games: how each player's farm develops day by day against Metav4 (same fresh seeds).

python tools/macro_compare.py template:overnight-g-fresh v3fw:full-v3fw-d628,full-v3fw-d628-b teacher:full-teacher
Each argument is label:run folder(s). Reads each game's replay; our seat is the one the metrics file names.
Per game and day (at dawn, and over the day): cash, planted tiles by crop, animals by kind, land quadrants,
workers hired, seeds and animals bought, units sold by product and the money they brought, and Metav4's cash.
Writes <data>/runs/macro/days.csv and prints day-band means per player.
"""
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import runs  # noqa: E402

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
ANIMALS = ("GOOSE", "COW", "SHEEP")
PRODUCTS = CROPS + ("EGG", "MILK", "WOOL", "FERTILIZER")


def game_days(replay, seat, label, seed):
    steps = replay["steps"]
    rows = []
    for day in range(30):
        i0 = day * 24
        if i0 >= len(steps):
            break
        o = steps[i0][0]["observation"]
        farm = o["farms"][seat]
        tiles = [t for row in farm["tiles"] for t in row if isinstance(t, dict)]
        r = {"player": label, "seed": seed, "seat": seat, "day": day, "cash": farm["money"],
             "opp_cash": o["farms"][1 - seat]["money"], "land": len(farm.get("unlocked_quadrants") or []),
             "crops": sum(t.get("kind") == "PLANT" for t in tiles), "animals": sum(bool(t.get("animal")) for t in tiles),
             "weeds": sum(t.get("kind") == "WEED" for t in tiles)}
        for c in CROPS:
            r[f"crop_{c.lower()}"] = sum(t.get("crop") == c for t in tiles)
        for a in ANIMALS:
            r[f"animal_{a.lower()}"] = sum(t.get("animal") == a for t in tiles)
        sold, bought, revenue, hires, rev = Counter(), Counter(), 0.0, 0, Counter()
        for i in range(i0 + 1, min(i0 + 25, len(steps))):
            act = steps[i][seat]["action"] or {}
            prices = steps[i - 1][0]["observation"]["market"]["prices"]
            for od in act.get("market") or []:
                if not od:
                    continue
                n = int(od[2]) if len(od) > 2 else 1
                if od[0] == "SELL":
                    sold[od[1]] += n
                    revenue += n * prices.get(od[1], 0)
                    rev[od[1]] += n * prices.get(od[1], 0)
                elif od[0] in ("BUY_SEED", "BUY_ANIMAL", "BUY_PRODUCT"):
                    bought[f"{od[0].lower()}_{od[1].lower()}"] += n
                elif od[0] == "HIRE":
                    hires += 1
                elif od[0] == "BUY_LAND":
                    bought["buy_land"] += 1
        r["hires"] = hires
        r["sell_value_issued"] = round(revenue)
        for p in PRODUCTS:
            r[f"sold_{p.lower()}"] = sold[p]
            r[f"rev_{p.lower()}"] = round(rev[p])
        r.update(bought)
        rows.append(r)
    return rows


def main():
    rows = []
    for arg in sys.argv[1:]:
        label, folders = arg.split(":", 1)
        want = None
        if "=" in folders:                      # label:folder[,folder]=player name (folders shared by several players)
            folders, want = folders.split("=", 1)
        for folder in folders.split(","):
            for mf in sorted((runs() / folder).glob("*.metrics.json")):
                m = json.load(open(mf))
                if want and m["name"] != want:
                    continue
                replay = json.load(gzip.open(str(mf).replace(".metrics.json", ".json.gz"), "rt"))
                rows += game_days(replay, m["seat"], label, m["seed"])
    d = pd.DataFrame(rows).fillna(0)
    out = runs() / "macro"
    out.mkdir(parents=True, exist_ok=True)
    d.to_csv(out / "days.csv", index=False)
    d["band"] = pd.cut(d.day, [-1, 5, 11, 17, 23, 29], labels=["0-5", "6-11", "12-17", "18-23", "24-29"])
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    cols = ["cash", "opp_cash", "land", "crops", "animals", "weeds", "hires", "sell_value_issued"] + \
           [f"crop_{c.lower()}" for c in CROPS] + [f"animal_{a.lower()}" for a in ANIMALS]
    print(d.groupby(["band", "player"], observed=True)[cols].mean().round(1).to_string())
    buys = [c for c in d.columns if c.startswith(("buy_", "sold_"))]
    print(d.groupby(["band", "player"], observed=True)[buys].mean().round(2).to_string())
    revs = [c for c in d.columns if c.startswith("rev_")]
    print("issued sell value by product over the whole game (per game):")
    print((d.groupby("player")[revs].sum().div(d.groupby("player").apply(lambda x: len(x[["seed", "seat"]].drop_duplicates())), axis=0)).round(0).T)
    land = d[d.land >= 2].groupby(["player", "seed", "seat"]).day.min().groupby("player").agg(["mean", "count"])
    print("first day with a second quadrant (mean, games):\n", land.round(1))
    land3 = d[d.land >= 3].groupby(["player", "seed", "seat"]).day.min().groupby("player").agg(["mean", "count"])
    print("first day with a third quadrant:\n", land3.round(1))


if __name__ == "__main__":
    main()

"""What each player did with one day, from the same morning: our template agent (its recorded game) against the
4th-place agent (its L1 segment for that morning).

python tools/day_profile.py <tag> --games <dir of our recorded games> [--days 6-28]
Writes <data>/runs/profile/<tag>.csv: one row per game, day and player (seat 0 only).

Per row, at dawn: workers, free / planted / locked tiles, seeds in stock. During the day: unit-turns by kind (work,
walking, PASS), seeds, land, animals and hires bought, units sold. At the next dawn: crops planted that day, crops
lost (planted tiles that disappeared without a harvest that day), free tiles left.
"""
import argparse
import csv
import gzip
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import data_root, runs  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def tiles(obs):
    return [t for row in obs["farms"][0]["tiles"] for t in row]


def profile(frames, day):
    """frames[0] is the dawn observation pair; frames[1..24] carry the actions taken and the states they lead to."""
    dawn = frames[0][0]["observation"]
    end = frames[24][0]["observation"]
    t0, t1 = tiles(dawn), tiles(end)
    row = {"workers": 1 + len(dawn["farms"][0]["hands"]),
           "free": sum(t is None for t in t0),
           "planted0": sum(isinstance(t, dict) and t.get("kind") == "PLANT" for t in t0),
           "locked": sum(t == "LOCKED" for t in t0),
           "seeds0": sum(dawn["private"]["seeds"].values())}
    units, market = Counter(), Counter()
    for f in frames[1:25]:
        a = f[0]["action"] or {}
        for cmd in [a.get("farmer")] + list(a.get("hands") or []):
            k = cmd[0] if isinstance(cmd, list) and cmd else "PASS"
            units["walk" if k in MOVES else k] += 1
        for o in a.get("market") or []:
            if not o:
                continue
            if o[0] in ("BUY_SEED", "SELL", "BUY_ANIMAL", "BUY_PRODUCT"):
                market[f"{o[0]}:{o[1]}"] += int(o[2]) if len(o) > 2 else 1
            else:
                market[o[0]] += 1
    row["unit_turns"] = sum(units.values())
    row["walk"] = units["walk"]
    row["pass"] = units["PASS"]
    row["work"] = row["unit_turns"] - row["walk"] - row["pass"]
    for k in ("WATER", "HARVEST", "PLANT", "DIG", "FEED", "CARE", "FERTILIZE", "COLLECT_FERTILIZER", "PICKUP"):
        row[f"n_{k.lower()}"] = units[k]
    row["seeds_bought"] = sum(v for k, v in market.items() if k.startswith("BUY_SEED"))
    for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
        row[f"buy_{crop.lower()}"] = market[f"BUY_SEED:{crop}"]
    row["land"] = market["BUY_LAND"]
    row["hires"] = market["HIRE"]
    row["animals_bought"] = sum(v for k, v in market.items() if k.startswith("BUY_ANIMAL"))
    row["units_sold"] = sum(v for k, v in market.items() if k.startswith("SELL"))
    row["planted"] = sum(isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("planted_day") == day for t in t1)
    row["free_end"] = sum(t is None for t in t1)
    row["planted_end"] = sum(isinstance(t, dict) and t.get("kind") == "PLANT" for t in t1)
    row["cash"] = end["farms"][0]["money"] - dawn["farms"][0]["money"]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--games", required=True)
    ap.add_argument("--days", default="6-28")
    a = ap.parse_args()
    lo, hi = (int(x) for x in a.days.split("-"))
    seg_dir = data_root() / "raw" / "ownfarm" / "fourth"
    rows = []
    for path in sorted(Path(a.games).glob("*.json")):
        game = path.stem
        rep = json.load(open(path))
        for day in range(lo, hi + 1):
            seg = seg_dir / f"{game}-d{day}.json.gz"
            if not seg.exists():
                continue
            ours = rep["steps"][day * 24: day * 24 + 25]
            theirs = json.load(gzip.open(seg, "rt"))["steps"]
            for name, frames in (("template", ours), ("fourth", theirs)):
                rows.append({"game": game, "day": day, "player": name, **profile(frames, day)})
        print(game, flush=True)
    out = runs() / "profile" / f"{a.tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()

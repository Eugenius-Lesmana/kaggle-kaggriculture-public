"""Summarize crop replacement after shop unlocks from study.py output."""
import collections
import gzip
import json
import sys
from pathlib import Path

from study import OPEN_DAYS, PRODUCT_TARGET, SHOP_PRODUCTS

COHORT = sys.argv[1] if len(sys.argv) > 1 else "24"
if COHORT not in ("24", "29"):
    raise SystemExit("usage: python evaluation/modes/conversion.py [24|29]")
OUT = Path("evaluation/modes") / ("29-sept" if COHORT == "29" else "24-sept")


def read(name):
    return [json.loads(line) for line in gzip.open(OUT / name, "rt", encoding="utf-8")]


def main():
    openings = read("opening_tiles.jsonl.gz")
    plants = read("placements.jsonl.gz")
    digs = read("digs.jsonl.gz")
    by_game = collections.defaultdict(list)
    for plant in plants:
        by_game[plant["game"]].append(plant)
    open_by_game = {(r["game"], r["day"]): r for r in openings}
    result = {}
    for shop, products in SHOP_PRODUCTS.items():
        for product in products:
            target = PRODUCT_TARGET[product]
            if target not in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"):
                continue
            events = []
            for row in openings:
                prior = open_by_game.get((row["game"], row["day"] - 3))
                if row["shops"].get(shop, 0) <= (prior["shops"].get(shop, 0) if prior else 0):
                    continue
                found = [p for p in by_game[row["game"]]
                         if p["crop"] == target and row["step"] <= p["step"] < row["step"] + 72]
                if found:
                    first = min(found, key=lambda p: p["step"])
                    events.append({"lag_steps": first["step"] - row["step"],
                                   "first_source": first["preceding"],
                                   "all_sources": collections.Counter(p["preceding"] for p in found)})
                else:
                    events.append(None)
            observed = [e for e in events if e]
            if events:
                sources = sum((e["all_sources"] for e in observed), collections.Counter())
                result[f"{shop}/{target}"] = {
                    "events": len(events), "any_plant_72h": len(observed),
                    "median_first_lag_steps": sorted(e["lag_steps"] for e in observed)[len(observed) // 2] if observed else None,
                    "first_source": dict(collections.Counter(e["first_source"] for e in observed)),
                    "all_plant_sources": dict(sources),
                }
    result["crop_digs"] = {
        "total": sum(d["crop"] is not None for d in digs),
        "by_crop_age": {crop: dict(collections.Counter(d["age_days"] for d in digs if d["crop"] == crop))
                        for crop in ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")},
    }
    (OUT / "conversion.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

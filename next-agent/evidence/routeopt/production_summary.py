"""Per-phase production summary of a diag.py output (per game): capacity, output per capacity, watering, purchases."""
import csv, json, sys
from collections import Counter
src, out = sys.argv[1], sys.argv[2]
rows = json.load(open(src))["rows"]; n = len(rows)
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON"); ANIMALS = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}
table = []
for ph in ("d0_5", "d6_11", "d12_19", "d20_27"):
    c = Counter()
    for r in rows:
        c.update(r["phases"][ph])
    d = max(1, c["days"] // n)
    rec = {"phase": ph, "games": n, "days": d, "plots_owned": c["plots_owned"] / n / d,
           "empty_cells": c["empty_cell_days"] / n / d, "weed_cells": c["weed_cell_days"] / n / d,
           "planted_cells": c["plant_days"] / n / d, "animals": c["animal_days"] / n / d,
           "window_watered_share": c["window_watered"] / max(1, c["window_plant_days"]),
           "fertilized_share": c["fertilized_plant_days"] / max(1, c["plant_days"])}
    for crop in CROPS:
        cd = c["plant_days " + crop]
        rec[f"cells {crop}"] = cd / n / d
        rec[f"units {crop}"] = c["harvest_units " + crop] / n
        rec[f"units/cell-day {crop}"] = c["harvest_units " + crop] / cd if cd else 0
    for animal, product in ANIMALS.items():
        ad = c["animal_days " + animal]
        rec[f"animals {animal}"] = ad / n / d
        rec[f"units {product}"] = c["harvest_units " + product] / n
        rec[f"units/animal-day {animal}"] = c["harvest_units " + product] / ad if ad else 0
    rec["buy_request WHEAT"] = c["buy_request WHEAT"] / n
    table.append(rec)
with open(out, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(table[0])); w.writeheader()
    for rec in table: w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in rec.items()})
for rec in table:
    print(rec["phase"], {k: round(v, 2) if isinstance(v, float) else v for k, v in rec.items() if k != "phase" and (not isinstance(v, float) or v)})

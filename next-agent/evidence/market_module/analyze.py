"""Rebuild compact market tables from control summaries and measured fills."""
import csv
import json
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")


def write(name, rows):
    with (OUT / name).open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


controls = []
files = sorted((ROOT / "evaluation/routeopt").glob("*_ctrl.json"))
for path in files:
    data = json.loads(path.read_text())
    assert data["candidate"] == "agents/ours/v0.10.0-candidate/main.py"
    assert data["opponent"] == "agents/ours/h1-substrate-metav4/main.py"
    controls.extend(data["rows"])
assert len({(r["seed"], r["side"]) for r in controls}) == len(controls)
rows = []
for product in PRODUCTS:
    for role, prefix in (("planner", "own"), ("metav4", "opp")):
        units = sum(r[prefix + "_sold"][product] for r in controls)
        revenue = sum(r[prefix + "_revenue"][product] for r in controls)
        rows.append(dict(product=product, role=role, games=len(controls),
                         verified_units_game=units / len(controls), verified_revenue_game=revenue / len(controls),
                         verified_price=revenue / units if units else 0,
                         unverified_units_game=sum(r[prefix + "_unverified"][product] for r in controls) / len(controls)))
write("control_products.csv", rows)
fills = list(csv.DictReader((OUT / "fills.csv").open()))
for row in fills:
    for key in ("seed", "step", "side", "units", "dollars"):
        row[key] = int(row[key])
games = json.loads((OUT / "games.json").read_text())
n = len(games)
totals = defaultdict(Counter)
hours = defaultdict(Counter)
for row in fills:
    if row["op"] == "SELL":
        totals[(row["side"], row["product"])].update(units=row["units"], dollars=row["dollars"])
    if row["side"] == 1 and (row["op"] == "SELL" or row["op"] == "BUY_PRODUCT" and row["product"] == "WHEAT"):
        hours[(row["op"], row["product"], row["step"] % 24)].update(units=row["units"], dollars=row["dollars"])
write("fresh_products.csv", [dict(product=p, side=s, games=n, units_game=totals[(s, p)]["units"] / n,
                                  revenue_game=totals[(s, p)]["dollars"] / n,
                                  price=totals[(s, p)]["dollars"] / totals[(s, p)]["units"] if totals[(s, p)]["units"] else 0)
                             for p in PRODUCTS for s in (0, 1)])
write("sale_hours.csv", [dict(op=op, product=p, hour=h, mod4=h % 4, units_game=c["units"] / n,
                              dollars_game=c["dollars"] / n, price=c["dollars"] / c["units"])
                         for (op, p, h), c in sorted(hours.items())])
timing = []
for product in PRODUCTS:
    counts = {h: hours[("SELL", product, h)]["units"] for h in range(24)}
    total = sum(counts.values())
    timing.append(dict(product=product, units_game=total / n,
                       leading_hours=";".join(f"{h}:{counts[h]/total:.1%}" for h in sorted(counts, key=counts.get, reverse=True)[:3]),
                       **{f"mod4_{m}_share": sum(c for h, c in counts.items() if h % 4 == m) / total for m in range(4)},
                       hour0_share=counts[0] / total, hour1_share=counts[1] / total))
write("sale_timing.csv", timing)
wheat = defaultdict(dict)
for row in fills:
    if row["side"] == 1 and row["product"] == "WHEAT" and row["op"] in ("BUY_PRODUCT", "SELL"):
        wheat[(row["seed"], row["step"])][row["op"]] = row
write("wheat_same_turn.csv", [dict(seed=s, step=t, hour=t % 24, bought=v["BUY_PRODUCT"]["units"],
                                  cost=v["BUY_PRODUCT"]["dollars"], sold=v["SELL"]["units"], revenue=v["SELL"]["dollars"])
                              for (s, t), v in sorted(wheat.items()) if "BUY_PRODUCT" in v and "SELL" in v])
index = {(r["seed"], r["step"], r["product"]): r for r in fills if r["side"] == 1 and r["op"] == "SELL"}
mechanisms = defaultdict(Counter)
for game in games:
    for step, tags in game["tags"].items():
        for key, requested in tags.items():
            label, product = key.split(":")
            fill = index.get((game["seed"], int(step), product))
            mechanisms[label]["requested"] += requested
            if fill:
                mechanisms[label].update(turns=1, associated_units=fill["units"], associated_revenue=fill["dollars"])
write("mechanisms.csv", [dict(mechanism=k, tagged_product_turns_game=c["turns"] / n,
                              requested_extra_units_game=c["requested"] / n,
                              affected_turn_units_game=c["associated_units"] / n,
                              affected_turn_revenue_game=c["associated_revenue"] / n)
                         for k, c in sorted(mechanisms.items())])
summary = {"control_files": [p.name for p in files], "control_games": len(controls), "fresh_games": n,
           "mean_banks": [sum(g["banks"][s] for g in games) / n for s in (0, 1)],
           "opening_cash_gain_vs_buy5_game": sum(g["opening_cash_gain_vs_buy5"] for g in games) / n,
           "ordering_cash_gain_vs_inherited_sell_rank_game": sum(g["ordering_cash_gain_vs_inherited_sell_rank"] for g in games) / n}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2))
print(json.dumps(summary))

"""Summarize replay sale tables and identify issued market buy volume."""
import argparse
import csv
import gzip
import json
import statistics
from collections import defaultdict
from pathlib import Path

from analyze import PRODUCTS, replay_paths

OUT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--intake", type=Path, default=Path("<repo>/research/intake/replays"))
INTAKE = parser.parse_args().intake

def read(name):
    return list(csv.DictReader((OUT / name).open(newline="", encoding="utf-8")))

def write(name, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

games = read("games.csv")
behaviour = read("behaviour_games.csv")
top3 = [r for r in games if r["group"] in ("top/56654377", "top/56664798", "top/56666211")]
bases = {
    "top/three": top3,
    "F4+counter": [r for r in games if r["group"] == "F4+counter"],
    "planner/pooled": [r for r in games if r["group"].startswith("planner/")],
}
summary, products = [], []
for group, rows in bases.items():
    n = len(rows)
    bank = sum(float(r["bank"]) for r in rows)/n
    total = sum(float(r[p+"_revenue"]) for r in rows for p in PRODUCTS)/n
    summary.append(dict(group=group, games=n, bank_per_game=bank, revenue_per_game=total))
    for p in PRODUCTS:
        units = sum(float(r[p+"_units"]) for r in rows)/n
        revenue = sum(float(r[p+"_revenue"]) for r in rows)/n
        products.append(dict(group=group, product=p, units_per_game=units,
                             price_per_unit=revenue/units if units else 0,
                             revenue_per_game=revenue, revenue_share=revenue/total))
write("comparison_summary.csv", summary)
write("comparison_products.csv", products)
lookup = {(r["group"],r["product"]):r for r in products}
decomposition = []
for target in ("F4+counter","planner/pooled"):
    for p in PRODUCTS:
        a,b = lookup["top/three",p],lookup[target,p]
        q1,q0 = float(a["units_per_game"]),float(b["units_per_game"])
        p1,p0 = float(a["price_per_unit"]),float(b["price_per_unit"])
        decomposition.append(dict(comparison=f"top/three - {target}", product=p,
                                  revenue_gap=float(a["revenue_per_game"])-float(b["revenue_per_game"]),
                                  unit_effect=(q1-q0)*(p1+p0)/2 if q1 and q0 else float(a["revenue_per_game"])-float(b["revenue_per_game"]),
                                  price_effect=(p1-p0)*(q1+q0)/2 if q1 and q0 else 0))
write("comparison_decomposition.csv", decomposition)
behaviour_groups = {
    "top/all": [r for r in behaviour if r["group"].startswith("top/")],
    "top/three": [r for r in behaviour if r["group"] in ("top/56654377","top/56664798","top/56666211")],
    "top/56640149": [r for r in behaviour if r["group"]=="top/56640149"],
    "F4+counter": [r for r in behaviour if r["group"]=="F4+counter"],
}
behaviour_summary = []
for group, rows in behaviour_groups.items():
    sold = sum(float(r["sold_units"]) for r in rows)
    events = sum(float(r["sale_events"]) for r in rows)
    behaviour_summary.append(dict(group=group, games=len(rows),
        sale_events_per_game=events/len(rows), units_per_event=sold/events,
        median_size_game_mean=statistics.mean(float(r["median_sale_size"]) for r in rows),
        p90_size_game_mean=statistics.mean(float(r["p90_sale_size"]) for r in rows),
        local_high_unit_share=sum(float(r["peak_units"]) for r in rows)/sold,
        day_end_stock=statistics.mean(float(r["mean_day_end_stock"]) for r in rows),
        **{f"phase{k}_share":sum(float(r[f"phase{k}"]) for r in rows)/sold for k in range(4)},
        **{f"h{h:02}_share":sum(float(r[f"h{h:02}"]) for r in rows)/sold for h in range(24)}))
write("behaviour_summary.csv", behaviour_summary)

intent = read("buy_order_intent.csv") if (OUT / "buy_order_intent.csv").exists() else []
for index,(group,path,seat) in enumerate(() if intent else replay_paths(INTAKE)):
    with gzip.open(path,"rt",encoding="utf-8") as file:
        data = json.load(file)
    buys = defaultdict(int)
    for step in data["steps"]:
        action = step[seat].get("action") or {}
        for order in action.get("market") or []:
            if len(order)>=3 and order[0]=="BUY_PRODUCT" and order[1] in ("WHEAT","FERTILIZER"):
                buys[order[1]] += max(0,int(order[2]))
    intent.append(dict(group=group,game=path.stem,
                       wheat_buy_requested=buys["WHEAT"],
                       fertilizer_buy_requested=buys["FERTILIZER"]))
    if (index+1)%200==0:
        print(f"buy orders {index+1}",flush=True)
write("buy_order_intent.csv",intent)
by_group=defaultdict(list)
for row in intent:
    by_group[row["group"]].append(row)
buy_summary=[]
for group,rows in sorted(by_group.items()):
    buy_summary.append(dict(group=group,games=len(rows),
        wheat_buy_requested_per_game=sum(int(r["wheat_buy_requested"]) for r in rows)/len(rows),
        fertilizer_buy_requested_per_game=sum(int(r["fertilizer_buy_requested"]) for r in rows)/len(rows)))
write("buy_order_summary.csv",buy_summary)
print(json.dumps(buy_summary))




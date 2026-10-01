"""Condense phase tables and align harvest counts with the planner diagnostic."""
import csv
import json
import subprocess
from collections import Counter, defaultdict
from pathlib import Path

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON")
PRODUCTS = CROPS + ("EGG", "MILK", "WOOL", "FERTILIZER")
PHASES = ("d0_5", "d6_11", "d12_19", "d20_27")

def read(name):
    return list(csv.DictReader((OUT/name).open(newline="",encoding="utf-8")))

def write(name, rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)

group=read("group_product_phase.csv")
games=read("game_product_phase.csv")
roll=read("rollover_harvest.csv")
lookup={(r["group"],r["phase"],r["product"]):r for r in group}
rollsum=Counter()
for row in roll:
    if row["group"]!="56640149":
        rollsum[(row["phase"],row["product"])]+=int(row["units"])
roll_avg={key:total/355 for key,total in rollsum.items()}
planner=json.loads(subprocess.check_output(["git","show",
    "dev/eugene-claude-routeopt:evaluation/routeopt/production_v010.json"],cwd=ROOT))["rows"]

capacity=[]
for agent in ("top_three","56654377","56664798","56666211","56640149","planner_v010"):
    for name in PHASES:
        rows=[lookup[agent,name,p] for p in PRODUCTS]
        first=rows[0]
        plant_days=sum(float(r["capacity_days"]) for r in rows if r["product"] in CROPS)
        fert_days=sum(float(r["capacity_days"])*float(r["fertilized_share"] or 0)
                      for r in rows if r["product"] in CROPS)
        if agent=="planner_v010":
            phase_rows=[r["phases"][name] for r in planner]
            plant_days=sum(r.get("plant_days",0) for r in phase_rows)/len(phase_rows)
            fert_days=sum(r.get("fertilized_plant_days",0) for r in phase_rows)/len(phase_rows)
        capacity.append(dict(group=agent,phase=name,games=first["games"],days=first["days"],
            plots_owned=first["plots_owned"],planted_cells=first["plant_cells"],
            animal_cells=first["animals"],empty_cells=first["empty_cells"],
            weed_cells=first["weed_cells"],empty_structures=first["empty_structures"],
            yield_window_watered=first["planner_window_watered_share"],
            fertilized_plant_day_share=fert_days/plant_days if plant_days else 0,
            produced_units=sum(float(r["harvested_units"]) for r in rows),
            bought_fills=sum(float(r["buy_fills"] or 0) for r in rows) if agent!="planner_v010" else "",
            sold_units=sum(float(r["sold"] or 0) for r in rows) if agent!="planner_v010" else "",
            discarded_or_overflow=sum(float(r["conservation_residual"] or 0) for r in rows) if agent!="planner_v010" else ""))
write("capacity_summary.csv",capacity)

matched=[]
for name in PHASES:
    for product in PRODUCTS:
        top=lookup["top_three",name,product]
        base=lookup["planner_v010",name,product]
        actual=float(top["harvested_units"])
        rollover=roll_avg.get((name,product),0)
        comparable=actual-rollover
        planner_units=float(base["harvested_units"])
        ct,cb=float(top["capacity_days"]),float(base["capacity_days"])
        yt=comparable/ct if ct else 0
        yb=planner_units/cb if cb else 0
        gap=comparable-planner_units
        capacity_effect=(ct-cb)*(yt+yb)/2 if ct and cb else gap
        yield_effect=(yt-yb)*(ct+cb)/2 if ct and cb else 0
        assert abs(gap-capacity_effect-yield_effect)<1e-6
        top_buy=float(top["buy_fills"] or 0)
        planner_request=float(base["buy_requests"])
        matched.append(dict(phase=name,product=product,
            top_harvest_actual=actual,top_harvest_hour23=rollover,
            top_harvest_comparable=comparable,planner_harvest_diagnostic=planner_units,
            comparable_harvest_gap=gap,capacity_days_top=ct,capacity_days_planner=cb,
            yield_top_comparable=yt,yield_planner_diagnostic=yb,
            capacity_effect=capacity_effect,yield_effect=yield_effect,
            top_buy_fills=top_buy,planner_buy_requests=planner_request,
            buy_gap_lower=top_buy-planner_request,buy_gap_upper=top_buy,
            consumption_gap=float(top["consumed"])-float(base["consumed"]),
            top_sold=float(top["sold"] or 0),
            top_stock_change=float(top["closing_stock"] or 0)-float(top["opening_stock"] or 0),
            top_discarded=float(top["conservation_residual"] or 0)))
write("matched_decomposition.csv",matched)

bad=[r for r in games if float(r["conservation_residual"])<0]
assert not bad, f"negative stock residual: {bad[:1]}"
print(json.dumps({"matched_harvest_gap":sum(r["comparable_harvest_gap"] for r in matched),
                  "capacity_effect":sum(r["capacity_effect"] for r in matched),
                  "yield_effect":sum(r["yield_effect"] for r in matched),
                  "top_hour23_harvest":sum(r["top_harvest_hour23"] for r in matched),
                  "negative_stock_residuals":len(bad)},indent=2))

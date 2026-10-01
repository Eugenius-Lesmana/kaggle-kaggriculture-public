"""Replay-only sale attribution and bank-gap decomposition; one gzip game in memory."""
import argparse
import contextlib
import csv
import gzip
import io
import json
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
            "EGG", "MILK", "WOOL", "FERTILIZER")
HERE = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(HERE / "tools"))
import screen

def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

def replay_paths(intake):
    for folder in sorted((intake / "29 Sept top").iterdir()):
        if not folder.is_dir():
            continue
        identity = int(folder.name)
        episodes = {int(e["id"]): e for e in json.loads(
            (folder / "episodes.json").read_text(encoding="utf-8"))["episodes"]}
        for path in sorted(folder.glob("*.json.gz")):
            episode = episodes.get(int(path.name.split(".")[0]))
            if episode:
                seats = [i for i, agent in enumerate(episode["agents"])
                         if agent["submissionId"] == identity]
                if len(seats) == 1:
                    yield f"top/{identity}", path, seats[0]
    folder = intake / "28 Sept f4"
    episodes = {int(e["id"]): e for e in json.loads(
        (folder / "episodes.json").read_text(encoding="utf-8"))["episodes"]}
    for path in sorted(folder.glob("*.json.gz")):
        episode = episodes.get(int(path.name.split(".")[0]))
        if episode:
            seats = [i for i, agent in enumerate(episode["agents"])
                     if agent["submissionId"] == 56620927]
            if len(seats) == 1:
                yield "F4+counter", path, seats[0]

def planner_rows():
    for arm in ("f1", "f2", "a1"):
        raw = subprocess.check_output(
            ["git", "show", f"dev/eugene-claude-routeopt:evaluation/routeopt/{arm}_ctrl.json"],
            cwd=HERE)
        data = json.loads(raw)
        for index, row in enumerate(data["rows"]):
            yield dict(group=f"planner/{arm}", game=f"{arm}/{index}", bank=row["cand"],
                       sold=row["own_sold"], revenue=row["own_revenue"],
                       unverified=sum(row.get("own_unverified", {}).values()),
                       verified_steps=row.get("verified_steps", 0),
                       unverified_steps=row.get("unverified_steps", 0))

def replay_row(group, path, seat):
    with gzip.open(path, "rt", encoding="utf-8") as file:
        data = json.load(file)
    steps = data["steps"]
    units, revenue = Counter(), Counter()
    sizes = []
    hours = Counter()
    phase = Counter()
    stock = []
    peak_units = 0
    verified = unverified = unverified_units = 0
    hires_today = [0, 0]
    prices = [step[0]["observation"]["market"]["prices"] for step in steps]
    for i in range(1, len(steps)):
        before = [steps[i-1][p]["observation"] for p in (0, 1)]
        after = [steps[i][p]["observation"] for p in (0, 1)]
        if before[0]["day"] != after[0]["day"]:
            hires_today = [0, 0]
        if after[0]["hour"] == 23:
            stock.append(sum(screen.holdings(after[seat])[p] for p in PRODUCTS))
        actions = [steps[i][p].get("action") or {} for p in (0, 1)]
        orders = [a.get("market") or [] for a in actions]
        if not any(orders):
            continue
        budgets = [screen.units_sold(before[p], after[p], actions[p], p)
                   for p in (0, 1)]
        with contextlib.redirect_stderr(io.StringIO()), contextlib.redirect_stdout(io.StringIO()):
            sold, rev, spent = screen.attribute_sales(
                orders, budgets, before[0]["market"]["inventory"],
                money=[before[p]["farms"][p]["money"] for p in (0, 1)])
        valid = [False, False]
        for p in (0, 1):
            atomic, hired = screen.atomic_cost(before[p], after[p], p, hires_today[p], 1)
            hires_today[p] += hired
            priceable = orders[p] and all(
                isinstance(o, list) and o and o[0] in
                ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND", "NOOP")
                for o in orders[p])
            delta = after[p]["farms"][p]["money"] - before[p]["farms"][p]["money"]
            valid[p] = bool(priceable and round(sum(rev[p].values()) - spent[p] - atomic) == round(delta))
        if not orders[seat]:
            continue
        if not valid[seat]:
            unverified += 1
            unverified_units += sum(budgets[seat].values())
            continue
        verified += 1
        for product, quantity in sold[seat].items():
            if quantity <= 0:
                continue
            units[product] += quantity
            revenue[product] += rev[seat][product]
            sizes.append(quantity)
            hour = after[seat]["hour"]
            hours[hour] += quantity
            phase[hour % 4] += quantity
            quote = before[seat]["market"]["prices"].get(product, 0)
            day = after[seat]["day"]
            nearby = [prices[j].get(product, 0) for j in range(max(0, i-4), min(len(steps), i+5))
                      if steps[j][0]["observation"]["day"] == day]
            if nearby and quote >= max(nearby):
                peak_units += quantity
    return (dict(group=group, game=path.stem, bank=data["rewards"][seat],
                 sold=units, revenue=revenue, verified_steps=verified,
                 unverified_steps=unverified, unverified=unverified_units),
            dict(group=group, game=path.stem, sale_events=len(sizes),
                 mean_sale_size=statistics.mean(sizes) if sizes else 0,
                 median_sale_size=statistics.median(sizes) if sizes else 0,
                 p90_sale_size=sorted(sizes)[int(.9*(len(sizes)-1))] if sizes else 0,
                 peak_units=peak_units, sold_units=sum(units.values()),
                 mean_day_end_stock=statistics.mean(stock) if stock else 0,
                 **{f"h{h:02}": hours[h] for h in range(24)},
                 **{f"phase{k}": phase[k] for k in range(4)}))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--intake", type=Path, required=True)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    output = Path(__file__).resolve().parent
    games, behaviours = [], []
    for index, (group, path, seat) in enumerate(replay_paths(args.intake)):
        if args.limit and index >= args.limit:
            break
        game, behaviour = replay_row(group, path, seat)
        games.append(game)
        behaviours.append(behaviour)
        if (index+1) % 100 == 0:
            print(f"replays {index+1}", flush=True)
    games.extend(planner_rows())
    flat = []
    for row in games:
        flat.append(dict(group=row["group"], game=row["game"], bank=row["bank"],
                         verified_steps=row["verified_steps"],
                         unverified_steps=row["unverified_steps"],
                         unverified_units=row["unverified"],
                         **{f"{p}_units": row["sold"].get(p, 0) for p in PRODUCTS},
                         **{f"{p}_revenue": row["revenue"].get(p, 0) for p in PRODUCTS}))
    write_csv(output / "games.csv", flat)
    write_csv(output / "behaviour_games.csv", behaviours)
    grouped = defaultdict(list)
    for row in games:
        grouped[row["group"]].append(row)
    grouped["top/pooled"] = [r for r in games if r["group"].startswith("top/")]
    grouped["planner/pooled"] = [r for r in games if r["group"].startswith("planner/")]
    summary = []
    by_product = []
    for group, rows in sorted(grouped.items()):
        n = len(rows)
        total_revenue = sum(sum(r["revenue"].values()) for r in rows)
        summary.append(dict(group=group, games=n, bank_per_game=sum(r["bank"] for r in rows)/n,
                            revenue_per_game=total_revenue/n,
                            verified_steps=sum(r["verified_steps"] for r in rows),
                            unverified_steps=sum(r["unverified_steps"] for r in rows),
                            unverified_units=sum(r["unverified"] for r in rows)))
        for product in PRODUCTS:
            quantity = sum(r["sold"].get(product, 0) for r in rows)
            revenue = sum(r["revenue"].get(product, 0) for r in rows)
            by_product.append(dict(group=group, product=product,
                                   units_per_game=quantity/n, price_per_unit=revenue/quantity if quantity else 0,
                                   revenue_per_game=revenue/n, revenue_share=revenue/total_revenue if total_revenue else 0))
    write_csv(output / "summary.csv", summary)
    write_csv(output / "products.csv", by_product)
    lookup = {(r["group"], r["product"]): r for r in by_product}
    bank = {r["group"]: r["bank_per_game"] for r in summary}
    decomposition = []
    for target in ("F4+counter", "planner/pooled"):
        for product in PRODUCTS:
            top, base = lookup["top/pooled", product], lookup[target, product]
            qt, qb = top["units_per_game"], base["units_per_game"]
            pt, pb = top["price_per_unit"], base["price_per_unit"]
            decomposition.append(dict(comparison=f"top - {target}", product=product,
                                      revenue_gap=top["revenue_per_game"]-base["revenue_per_game"],
                                      unit_effect=(qt-qb)*(pt+pb)/2 if qt and qb else top["revenue_per_game"]-base["revenue_per_game"],
                                      price_effect=(pt-pb)*(qt+qb)/2 if qt and qb else 0))
    write_csv(output / "decomposition.csv", decomposition)
    print(json.dumps({"replays":len(behaviours),"groups":{k:len(v) for k,v in grouped.items()},
                      "bank":bank}, indent=2))

if __name__ == "__main__":
    main()



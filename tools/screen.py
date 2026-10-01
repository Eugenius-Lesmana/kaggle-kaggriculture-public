"""Fast paired screen: candidate vs opponent across seeds and both seats.

Reports the outcome AND the mechanism metrics this project now selects on:
HARVEST count, realised revenue per unit sold, and end-state prices - not crop
cell-days. See docs/SYNTHESIS_REVISED_STRATEGY_2026-09-19.md.

Usage:
  python scripts/screen.py --candidate agents/ours/v0.9.0-candidate/main.py \
      --opponent agents/public/2026-09-17/kaggriculture-v46.../main.py \
      --seeds 5201-5210 --workers 6
"""
import argparse, json, os, sys, time
from collections import Counter
from concurrent.futures import ProcessPoolExecutor

PRODUCTS = ("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON","EGG","MILK","WOOL")
BASE = {"WHEAT":25,"CARROT":35,"TOMATO":60,"STRAWBERRY":120,"MELON":250,
        "EGG":50,"MILK":160,"WOOL":200}
ANCHOR = 10000

def parse_seeds(s):
    out=[]
    for part in s.split(","):
        if "-" in part:
            a,b = part.split("-"); out.extend(range(int(a), int(b)+1))
        else: out.append(int(part))
    return out

# The engine also lets FERTILIZER be sold. It is not one of the crop/animal
# PRODUCTS above (the joint price table is about those), but it is real revenue
# - we sell a few hundred units a game - so per-player attribution must price
# it or the money check fails and the step is discarded.
SELLABLE = PRODUCTS + ("FERTILIZER",)
LAND_PRICES = (1000, 2000, 4000)
SHED_CAPACITY = 100
MAX_MARKET_ORDERS = 10
ANIMAL_PRODUCT = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def holdings(observation):
    """Everything a player owns: shed plus every worker inventory."""
    total = Counter()
    private = observation["private"]
    total.update(private.get("shed", {}) or {})
    for inventory in private.get("inventories", []) or []:
        total.update(inventory)
    return total


def units_sold(before, after, action, player):
    """Units each product left this player's holdings as a sale, this step.

    Holdings (shed + carried) are immune to intra-step ordering, unlike the
    shed alone: a deposit can land before the market runs. Anything that left
    holdings other than through a non-sale sink was sold.

        sold = held_before + harvested + collected + bought
               - fed - fertilized - held_after

    `collected` and `fertilized` follow the engine's own preconditions, which
    are fully visible in the pre-step state: COLLECT_FERTILIZER adds one unit
    iff the tile holds an animal with fertilizer available; FERTILIZE consumes
    one iff the tile is a plant and that worker is carrying fertilizer (it
    consumes even onto an already-fertilized tile). Each worker acts once per
    step on its own inventory, so the preconditions cannot interfere.
    """
    before_held, after_held = holdings(before), holdings(after)
    farm = before["farms"][player]
    tiles = farm["tiles"]
    inflow, sink = Counter(), Counter()
    positions = [farm["farmer"]] + list(farm.get("hands") or [])
    operations = [action.get("farmer")] + list(action.get("hands") or [])
    inventories = before["private"].get("inventories", []) or []
    for index, ((x, y), command) in enumerate(zip(positions, operations)):
        if not (isinstance(command, list) and command):
            continue
        tile = tiles[y][x] if isinstance(tiles[y][x], dict) else {}
        carried = inventories[index] if index < len(inventories) else {}
        if command[0] == "HARVEST":
            product = tile.get("crop") or ANIMAL_PRODUCT.get(tile.get("animal"))
            if product:
                inflow[product] += tile.get("yield_units", 0) or 0
        elif command[0] == "FEED":
            sink["WHEAT"] += 1
        elif command[0] == "COLLECT_FERTILIZER":
            if "animal" in tile and tile.get("fertilizer_available"):
                inflow["FERTILIZER"] += 1
        elif command[0] == "FERTILIZE":
            if tile.get("kind") == "PLANT" and carried.get("FERTILIZER", 0) >= 1:
                sink["FERTILIZER"] += 1
    for order in action.get("market") or []:
        # Both buyable products. A buy that does not fill overstates the
        # inflow; the caller's money check rejects that step rather than
        # trusting it.
        if (isinstance(order, list) and len(order) >= 3 and order[0] == "BUY_PRODUCT"
                and order[1] in ("WHEAT", "FERTILIZER")):
            inflow[order[1]] += order[2]
    sold = Counter()
    for product in SELLABLE:
        quantity = before_held[product] + inflow[product] - sink[product] - after_held[product]
        if quantity > 0:
            sold[product] = quantity
    return sold


def get_config(env, key, default):
    configuration = getattr(env, "configuration", {}) or {}
    getter = getattr(configuration, "get", None)
    value = getter(key, default) if getter else getattr(configuration, key, default)
    return default if value is None else value


def fib(n):
    """Engine indexing: fib(0) = 1, fib(1) = 1, fib(2) = 2, fib(3) = 3, ..."""
    a, b = 1, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def atomic_cost(before, after, player, hires_today, hand_multiplier):
    """What HIRE and BUY_LAND cost this step, read from what they produced.

    Neither order carries its price in the action, but both leave a visible
    mark: a hire adds a hand, a land purchase unlocks a quadrant. Hire cost is
    the n-th of the DAY, so the caller carries the running count.
    """
    cost = 0
    hired = (len(after["farms"][player].get("hands") or [])
             - len(before["farms"][player].get("hands") or []))
    for offset in range(max(0, hired)):
        cost += hand_multiplier * fib(hires_today + offset)
    unlocked_before = len(before["farms"][player].get("unlocked_quadrants") or [])
    unlocked_after = len(after["farms"][player].get("unlocked_quadrants") or [])
    for index in range(unlocked_before - 1, unlocked_after - 1):
        if 0 <= index < len(LAND_PRICES):
            cost += LAND_PRICES[index]
    return cost, max(0, hired)


def attribute_sales(orders, budgets, inventory, money=None, price_of=None):
    """Price each sold unit by replaying the engine's market lockstep.

    Orders are taken one index at a time; for each unit both players are quoted
    against the *same* pre-commit inventory, then each commits in player order.
    `budgets` caps each player's units per product at what actually left their
    holdings, so an order that outran its stock stops where the engine stopped
    it. Sales at the $1 floor add no supply, so they do not move later quotes.
    """
    from kaggle_environments.envs.kaggriculture.kaggriculture import market_price

    from kaggle_environments.envs.kaggriculture.kaggriculture import ANIMALS, CROPS

    quote = price_of or (lambda item, inv: market_price(item, inv, None))
    inventory = dict(inventory)
    budgets = [Counter(b) for b in budgets]
    units = [Counter(), Counter()]
    revenue = [Counter(), Counter()]
    purse = list(money) if money else [10 ** 9, 10 ** 9]
    spent = [0, 0]

    queues = [[o for o in (q or []) if isinstance(o, list) and o][:MAX_MARKET_ORDERS] for q in orders]
    for index in range(max((len(q) for q in queues), default=0)):
        states = []
        for player, queue in enumerate(queues):
            order = queue[index] if index < len(queue) else None
            valid = (isinstance(order, list) and len(order) >= 3 and isinstance(order[2], int)
                     and order[2] > 0
                     and order[0] in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL"))
            states.append({"type": order[0], "item": order[1], "remaining": order[2]} if valid else None)
        while True:
            quoted = [None, None]
            for player, state in enumerate(states):
                if state is None or state["remaining"] <= 0:
                    continue
                kind, item = state["type"], state["item"]
                if kind == "SELL" and item in SELLABLE:
                    quoted[player] = (kind, item, quote(item, inventory.get(item, 0)), state)
                elif kind == "BUY_PRODUCT" and item in ("WHEAT", "FERTILIZER"):
                    quoted[player] = (kind, item, quote(item, inventory.get(item, 0) - 1), state)
                elif kind == "BUY_SEED" and item in CROPS:
                    quoted[player] = (kind, item, CROPS[item]["seed"], state)
                elif kind == "BUY_ANIMAL" and item in ANIMALS:
                    quoted[player] = (kind, item, ANIMALS[item]["cost"], state)
                else:
                    states[player] = None
            if all(entry is None for entry in quoted):
                break
            committed = False
            for player, entry in enumerate(quoted):
                if entry is None:
                    continue
                kind, item, price, state = entry
                if kind == "SELL":
                    if budgets[player][item] <= 0:
                        states[player] = None          # stock ran out: the order stops here
                        continue
                    budgets[player][item] -= 1
                    units[player][item] += 1
                    revenue[player][item] += price
                    purse[player] += price
                    if price > 1:                      # $1 sales do not add supply
                        inventory[item] = inventory.get(item, 0) + 1
                else:
                    if purse[player] < price:
                        states[player] = None          # cannot afford: the order stops here
                        continue
                    purse[player] -= price
                    spent[player] += price
                    if kind == "BUY_PRODUCT":
                        inventory[item] = inventory.get(item, 0) - 1
                state["remaining"] -= 1
                committed = True
            if not committed:
                break
    return units, revenue, spent


# Issued commands are not outcomes: a PLANT with no seed, a HARVEST on an empty
# tile and a FERTILIZE with an empty inventory are all silent no-ops that still
# appear in the action record. Every count below is confirmed against the next
# observed state instead. See docs/EXPERIMENT_V094_2026-09-20.md.
CONFIRMABLE = ("WATER", "FEED", "CARE", "HARVEST", "PLANT", "DIG",
               "FERTILIZE", "COLLECT_FERTILIZER")


def action_succeeded(operation, before_tile, after_tile, before_inv, after_inv):
    """Did this command change the world? None when it cannot be judged."""
    was = before_tile if isinstance(before_tile, dict) else {}
    now = after_tile if isinstance(after_tile, dict) else {}
    if operation == "WATER":
        return bool(now.get("watered_today")) and not was.get("watered_today")
    if operation == "FEED":
        return bool(now.get("fed_today")) and not was.get("fed_today")
    if operation == "CARE":
        return bool(now.get("cared_today")) and not was.get("cared_today")
    if operation == "FERTILIZE":
        return now.get("fertilized_until_day", -1) > was.get("fertilized_until_day", -1)
    if operation == "DIG":
        return after_tile is None and before_tile is not None
    if operation == "PLANT":
        return now.get("kind") == "PLANT" and was.get("kind") != "PLANT"
    if operation == "COLLECT_FERTILIZER":
        return after_inv.get("FERTILIZER", 0) > before_inv.get("FERTILIZER", 0)
    if operation == "HARVEST":
        return sum(after_inv.values()) > sum(before_inv.values())
    return None


def confirmed_outcomes(before, after, action, player):
    """Count issued/ok/failed/unobserved for one step's commands.

    `action` is the action recorded at the later step: its effect is the
    difference between `before` and `after`.

    Across a day boundary the end-of-day refresh runs first: it clears
    `watered_today`/`fed_today`/`cared_today`, empties worker inventories, and
    can change yield or spawn weeds. Successful hour-23 work is then
    indistinguishable from work that never happened, so those commands are
    reported as `unobserved` rather than guessed either way.
    """
    counts = Counter()
    if not isinstance(action, dict):
        return counts
    rollover = before.get("day") != after.get("day")
    farm = before["farms"][player]
    units = [farm["farmer"]] + list(farm.get("hands") or [])
    operations = [action.get("farmer")] + list(action.get("hands") or [])
    before_inventories = before["private"].get("inventories", [])
    after_inventories = after["private"].get("inventories", [])
    for index, (position, command) in enumerate(zip(units, operations)):
        if not (isinstance(command, list) and command):
            continue
        name = command[0]
        counts[name] += 1
        if name not in CONFIRMABLE:
            continue
        if rollover:
            counts[f"{name} unobserved"] += 1
            continue
        x, y = position
        succeeded = action_succeeded(
            name,
            farm["tiles"][y][x],
            after["farms"][player]["tiles"][y][x],
            before_inventories[index] if index < len(before_inventories) else {},
            after_inventories[index] if index < len(after_inventories) else {},
        )
        if succeeded is not None:
            counts[f"{name} {'ok' if succeeded else 'failed'}"] += 1
    return counts


def run_one(job):
    cand, opp, seed, cand_side = job
    from kaggle_environments import make
    agents = [cand, opp] if cand_side == 0 else [opp, cand]
    env = make("kaggriculture", configuration={"episodeSteps":720,"seed":seed}, debug=False)
    env.run(agents)
    steps = env.steps
    final = steps[-1]
    banks = [float(s.reward or 0) for s in final]
    # mechanism metrics
    hand_multiplier = int(get_config(env, "farmHandCostMult", 1))
    hires_today = [0, 0]
    cmds = Counter(); sold={p:0.0 for p in PRODUCTS}; rev={p:0.0 for p in PRODUCTS}
    # Per-player attribution, replayed from the engine's own market lockstep.
    own_units = Counter(); own_rev = Counter()
    own_unverified = Counter(); opp_unverified = Counter()
    opp_units = Counter(); opp_rev = Counter()
    attribution = Counter()
    prev = steps[0][0]["observation"]["market"]["inventory"]
    for i in range(1,len(steps)):
        obs0 = steps[i][0]["observation"]
        inv, px = obs0["market"]["inventory"], obs0["market"]["prices"]
        for p in PRODUCTS:
            if p in inv and p in prev:
                dd = inv[p]-prev[p]
                if dd>0: sold[p]+=dd; rev[p]+=dd*px.get(p,BASE[p])
        prev = inv
        if steps[i - 1][0]["observation"]["day"] != steps[i][0]["observation"]["day"]:
            hires_today = [0, 0]
        # Per-player sales: units from holdings (order-independent), prices from
        # the engine's own lockstep. A unit sold is attributed to the player
        # whose holdings it left, so a shared market pool is never split by guess.
        befores = [steps[i - 1][p]["observation"] for p in (0, 1)]
        afters = [steps[i][p]["observation"] for p in (0, 1)]
        actions = [steps[i][p].get("action") or {} for p in (0, 1)]
        orders = [list(a.get("market") or []) if isinstance(a, dict) else [] for a in actions]
        if any(orders):
            budgets = [units_sold(befores[p], afters[p], actions[p], p)
                       if isinstance(actions[p], dict) else Counter() for p in (0, 1)]
            u, rv, spent = attribute_sales(
                orders, budgets, befores[0]["market"]["inventory"],
                money=[befores[p]["farms"][p]["money"] for p in (0, 1)])
            # Validate before trusting: on a step whose orders are all SELL,
            # the money delta IS the sale revenue, so the replay can be checked
            # exactly. Steps that fail, or that cannot be priced from the
            # observation (HIRE and BUY_LAND), are counted, never guessed.
            # Each player is verified on its own: when that player's orders are
            # all SELL, its money delta IS its sale revenue, so the replay can
            # be checked exactly. A player whose step does not verify is counted,
            # never guessed. Quotes still account for both players' orders.
            for player in (0, 1):
                # HIRE and BUY_LAND move money by amounts the observation does
                # not price, so those steps cannot be checked and are excluded.
                priceable = orders[player] and all(
                    isinstance(o, list) and o and o[0] in
                    ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND")
                    for o in orders[player])
                atomic, hired = atomic_cost(befores[player], afters[player], player,
                                            hires_today[player], hand_multiplier)
                hires_today[player] += hired
                observed = afters[player]["farms"][player]["money"] - befores[player]["farms"][player]["money"]
                predicted = sum(rv[player].values()) - spent[player] - atomic
                if priceable and round(predicted) == round(observed):
                    attribution["steps verified"] += 1
                    target_units = own_units if player == cand_side else opp_units
                    target_revenue = own_rev if player == cand_side else opp_rev
                    for item, count in u[player].items():
                        target_units[item] += count
                        target_revenue[item] += rv[player][item]
                elif orders[player]:
                    attribution["steps unverified"] += 1
                    attribution["units unverified"] += sum(budgets[player].values())
                    target = own_unverified if player == cand_side else opp_unverified
                    target.update(budgets[player])
        cmds.update(confirmed_outcomes(steps[i - 1][cand_side]["observation"],
                                       steps[i][cand_side]["observation"],
                                       steps[i][cand_side].get("action") or {},
                                       cand_side))
    fin_px = final[0]["observation"]["market"]["prices"]
    tiles = final[0]["observation"]["farms"][cand_side]["tiles"]
    weeds = sum(1 for r in tiles for t in r if isinstance(t,dict) and t.get("kind")=="WEED")
    # `harvest`/`plant`/`fert`/`care` stay ISSUED counts so older evidence files
    # remain comparable; the `*_ok` keys are the confirmed ones to select on.
    return dict(seed=seed, side=cand_side,
                cand=banks[cand_side], opp=banks[1-cand_side],
                harvest=cmds.get("HARVEST",0), plant=cmds.get("PLANT",0),
                fert=cmds.get("FERTILIZE",0), care=cmds.get("CARE",0),
                pass_=cmds.get("PASS",0), weeds=weeds,
                harvest_ok=cmds.get("HARVEST ok",0), plant_ok=cmds.get("PLANT ok",0),
                fert_ok=cmds.get("FERTILIZE ok",0), care_ok=cmds.get("CARE ok",0),
                water_ok=cmds.get("WATER ok",0), feed_ok=cmds.get("FEED ok",0),
                failed=sum(v for k,v in cmds.items() if k.endswith(" failed")),
                unobserved=sum(v for k,v in cmds.items() if k.endswith(" unobserved")),
                sold=sold, rev=rev,
                # Per-player, per-product confirmed sales (new; `sold`/`rev`
                # above remain the joint inventory-delta figures).
                own_sold={p: own_units.get(p, 0) for p in SELLABLE},
                own_revenue={p: own_rev.get(p, 0) for p in SELLABLE},
                opp_sold={p: opp_units.get(p, 0) for p in SELLABLE},
                opp_revenue={p: opp_rev.get(p, 0) for p in SELLABLE},
                own_unverified={p: own_unverified.get(p, 0) for p in SELLABLE},
                opp_unverified={p: opp_unverified.get(p, 0) for p in SELLABLE},
                verified_steps=attribution.get("steps verified", 0),
                unverified_steps=attribution.get("steps unverified", 0),
                unverified_units=attribution.get("units unverified", 0),
                final_px={p:fin_px.get(p,0) for p in PRODUCTS})

# Per-player, per-product sale fields are ISL's primary outcome; they must
# survive into the evidence file, not just the console.
PER_ROW_EVIDENCE = ("own_sold", "own_revenue", "opp_sold", "opp_revenue",
                    "own_unverified", "opp_unverified")


def export_rows(rows):
    """Rows as written to --json: everything except the joint market tables."""
    return [{k: v for k, v in r.items() if k not in ("sold", "rev", "final_px")} for r in rows]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--opponent", required=True)
    ap.add_argument("--seeds", type=parse_seeds, default=parse_seeds("5201-5205"))
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seats", type=int, default=2, help="1 = candidate as P1 only; seats are symmetric in this env")
    ap.add_argument("--label", default="")
    ap.add_argument("--json", default="")
    a = ap.parse_args()

    sides = (0,) if a.seats == 1 else (0, 1)
    jobs = [(a.candidate, a.opponent, s, side) for s in a.seeds for side in sides]
    t0=time.time(); rows=[]
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(run_one, jobs):
            rows.append(r)
            print(f"  seed {r['seed']} p{r['side']+1}: "
                  f"{r['cand']:>9,.0f} vs {r['opp']:>9,.0f}  "
                  f"ratio {r['cand']/r['opp'] if r['opp'] else 0:.3f}", flush=True)

    n=len(rows); wins=sum(1 for r in rows if r["cand"]>r["opp"])
    ratios=sorted(r["cand"]/r["opp"] if r["opp"] else 0 for r in rows)
    mean=lambda k: sum(r[k] for r in rows)/n
    med=ratios[n//2] if n%2 else (ratios[n//2-1]+ratios[n//2])/2
    print()
    print("="*78)
    print(f"{a.label or os.path.basename(os.path.dirname(a.candidate))}  "
          f"{n} games ({len(a.seeds)} seeds x {len(sides)} seat)   {time.time()-t0:.0f}s")
    print("="*78)
    print(f"  record            {wins}/{n}  ({100*wins/n:.0f}%)")
    print(f"  mean bank         {mean('cand'):>10,.0f}  vs opp {mean('opp'):>10,.0f}")
    print(f"  mean ratio        {sum(ratios)/n:.4f}")
    print(f"  median ratio      {med:.4f}")
    print(f"  P10 ratio         {ratios[max(0,int(0.1*n)-1)]:.4f}")
    print(f"  HARVEST  ok/issued{mean('harvest_ok'):>7,.0f} /{mean('harvest'):>7,.0f}")
    print(f"  PLANT    ok/issued{mean('plant_ok'):>7,.0f} /{mean('plant'):>7,.0f}")
    print(f"  FERTILIZE ok/issued{mean('fert_ok'):>6,.0f} /{mean('fert'):>7,.0f}")
    print(f"  CARE     ok/issued{mean('care_ok'):>7,.0f} /{mean('care'):>7,.0f}")
    print(f"  WATER/FEED ok     {mean('water_ok'):>7,.0f} /{mean('feed_ok'):>7,.0f}")
    print(f"  no-ops (confirmed failures)  {mean('failed'):>7,.0f}")
    print(f"  unobserved (day rollover)    {mean('unobserved'):>7,.0f}")
    print(f"  PASS              {mean('pass_'):>10,.0f}")
    print(f"  final weeds       {mean('weeds'):>10,.1f}")
    print()
    print(f"  per-player confirmed sales — units from holdings, prices from the engine lockstep,")
    print(f"  each step checked against the observed money delta and dropped if it disagrees")
    print(f"  ({mean('verified_steps'):,.0f} steps verified, {mean('unverified_steps'):,.0f} not; "
          f"{mean('unverified_units'):,.0f} units a game are therefore NOT in this table)")
    print(f"  {'product':<12}{'our units':>11}{'our $/u':>9}{'our rev':>11}"
          f"{'opp units':>11}{'opp $/u':>9}{'opp rev':>11}{'unverified (ours/opp)':>24}")
    own_total = opp_total = 0.0
    for p in SELLABLE:
        ou = sum(r['own_sold'][p] for r in rows)/n; orv = sum(r['own_revenue'][p] for r in rows)/n
        tu = sum(r['opp_sold'][p] for r in rows)/n; trv = sum(r['opp_revenue'][p] for r in rows)/n
        own_total += orv; opp_total += trv
        uo = sum(r['own_unverified'][p] for r in rows)/n
        ut = sum(r['opp_unverified'][p] for r in rows)/n
        print(f"  {p:<12}{ou:>11.0f}{(orv/ou if ou else 0):>9.0f}{orv:>11,.0f}"
              f"{tu:>11.0f}{(trv/tu if tu else 0):>9.0f}{trv:>11,.0f}{uo:>13.1f} /{ut:>7.1f}")
    print(f"  {'TOTAL':<12}{'':>11}{'':>9}{own_total:>11,.0f}{'':>11}{'':>9}{opp_total:>11,.0f}")
    print()
    print(f"  {'product':<12}{'units(joint)':>13}{'$/unit':>9}{'% base':>8}{'final px':>10}{'% base':>8}")
    for p in PRODUCTS:
        u=sum(r['sold'][p] for r in rows)/n
        rv=sum(r['rev'][p] for r in rows)/n
        fp=sum(r['final_px'][p] for r in rows)/n
        per=rv/u if u else 0
        print(f"  {p:<12}{u:>13.0f}{per:>9.0f}{100*per/BASE[p]:>7.0f}%{fp:>10.0f}{100*fp/BASE[p]:>7.0f}%")
    if a.json:
        with open(a.json,"w",encoding="utf-8") as fh:
            json.dump({"label":a.label,"candidate":a.candidate,"opponent":a.opponent,
                       "seeds":a.seeds,"games":n,"wins":wins,
                       "mean_ratio":sum(ratios)/n,"median_ratio":med,
                       "rows":export_rows(rows)}, fh, indent=1)
        print(f"\n  wrote {a.json}")

if __name__ == "__main__":
    main()

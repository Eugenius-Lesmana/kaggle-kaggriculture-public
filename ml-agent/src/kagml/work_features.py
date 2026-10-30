"""Work-model features (WORK_MODEL_FEATURES.md): context for a decision, then one row per candidate job.

Everything uses what the deciding player could know at that moment: its own observation, earlier observations
(price history, its own sales) and the public farms. The opponent's shed and bags are never used.
"""
import kaggle_environments.envs.kaggriculture.kaggriculture as K

SIZE = 10
CROPS, ANIMALS, SHOPS = K.CROPS, K.ANIMALS, K.SHOPS
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
PRODUCT_OF = {a: ANIMALS[a]["product"] for a in ANIMALS}
SHED_TILES = [(x, y) for y in range(SIZE) for x in range(SIZE) if K._is_shed_adjacent((x, y), SIZE)]
KINDS = ("WATER", "HARVEST", "FEED", "CARE", "COLLECT_FERTILIZER", "FERTILIZE", "PLANT", "DIG", "PICKUP", "DROP",
         "PLACE", "BUILD_COOP", "BUILD_PASTURE")
ITEMS = PRODUCTS + ("GOOSE", "COW", "SHEEP", "GOODS", "")
BIG = 999


def dist(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def to_shed(p):
    return min(dist(p, s) for s in SHED_TILES)


def daily_demand(shops):
    """Units of each product the open shops (and the town centre) consume per day."""
    d = dict.fromkeys(PRODUCTS, 0.0)
    for shop in shops:
        items = SHOPS[shop]
        for item in items:
            d[item] += 6 * (2 if len(items) == 1 else 1)      # every 4 turns, 6 times a day
    for item in K.TOWN_CENTER_PRODUCTS:
        d[item] += 1
    return d


def liquidation(item, units, inventory):
    """What `units` of `item` would fetch if sold now, one at a time into the market."""
    total, inv = 0, inventory
    for _ in range(int(units)):
        total += K.market_price(item, inv)
        inv += 1
    return total


def produce_soon(tile, day, horizon):
    """Rough units a tile will produce within `horizon` days (for 'units coming soon')."""
    if not isinstance(tile, dict):
        return None, 0
    if tile.get("kind") == "PLANT":
        c = CROPS[tile["crop"]]
        age = day - tile["planted_day"]
        if c["ongoing"]:
            n = sum(1 for a in range(age, age + horizon) if a >= c["first_yield_day"] and (a - c["first_yield_day"]) % c["interval"] == 0)
            return tile["crop"], n * (2 if tile.get("fertilized_until_day", -1) >= day else 1)
        return tile["crop"], (c["max_yield"] if age < c["first_yield_day"] <= age + horizon else 0)
    if "animal" in tile:
        a = ANIMALS[tile["animal"]]
        since = day + 1 - tile["placed_day"] - a["first_yield_day"]
        n = sum(1 for k in range(since, since + horizon) if k >= 0 and k % a["interval"] == 0)
        return PRODUCT_OF[tile["animal"]], n * (1 + tile.get("pending_care_bonus", 0))
    return None, 0


class History:
    """What a player remembers from earlier turns: prices, market stock, its own sales."""

    def __init__(self):
        self.prices, self.inventory, self.our_sold, self.positions = [], [], [], []

    def add(self, obs, our_sold_this_step):
        self.prices.append(dict(obs["market"]["prices"]))
        self.inventory.append(dict(obs["market"]["inventory"]))
        self.our_sold.append(our_sold_this_step)
        farm = obs["farms"][obs.get("player", 0)]
        self.positions.append([tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]])

    def previous_position(self, unit, look_back=6):
        """The last different tile this worker stood on in the past few turns (None if it has not moved)."""
        old = getattr(self, "positions", [])
        if not old or unit >= len(old[-1]):
            return None
        now = old[-1][unit]
        for snap in reversed(old[-1 - look_back:-1]):
            if unit < len(snap) and snap[unit] != now:
                return snap[unit]
        return None

    def window(self, item, hours, step, shops):
        """(our units sold, everyone's net units sold) over the last `hours` turns, from the market."""
        lo = max(0, len(self.inventory) - 1 - hours)
        ours = sum(s.get(item, 0) for s in self.our_sold[lo:-1])
        net = 0
        for t in range(lo, len(self.inventory) - 1):
            consumed = 0
            if t % 4 == 0:
                consumed += sum((2 if len(SHOPS[s]) == 1 else 1) for s in shops if item in SHOPS[s])
            if t % 24 == 0 and item in K.TOWN_CENTER_PRODUCTS:
                consumed += 1
            net += self.inventory[t + 1][item] - self.inventory[t][item] + consumed
        return ours, net


def context(obs, seat, history):
    """Features shared by every candidate of every worker at this turn (group H, and per-product tables)."""
    farm, opp = obs["farms"][seat], obs["farms"][1 - seat]
    private, market = obs["private"], obs["market"]
    day, hour = obs["day"], obs["hour"]
    step = day * 24 + hour
    shops = list(obs["town"]["unlocked_shops"])
    tiles = [(y * SIZE + x, t) for y, row in enumerate(farm["tiles"]) for x, t in enumerate(row)]
    owned = [c for c, t in tiles if t != "LOCKED"]
    demand = daily_demand(shops)
    ctx = {"day": day, "hour": hour, "turns_left": 24 - hour, "days_left": 29 - day, "cash": farm["money"],
           "cash_gap": farm["money"] - opp["money"], "hands": len(farm["hands"]), "land": len(farm["unlocked_quadrants"]),
           "empty_cells": sum(1 for c, t in tiles if t is None), "shed_total": sum(private["shed"].values()),
           "opp_cash": opp["money"],
           "early_straw_buyers": sum(s in ("BRUNCH_SPOT", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP", "FARMERS_MARKET") for s in shops[:2])}
    for a in ANIMALS:
        ctx[f"n_{a.lower()}"] = sum(1 for c, t in tiles if isinstance(t, dict) and t.get("animal") == a)
        ctx[f"opp_n_{a.lower()}"] = sum(1 for row in opp["tiles"] for t in row if isinstance(t, dict) and t.get("animal") == a)
    for crop in CROPS:
        ctx[f"n_{crop.lower()}"] = sum(1 for c, t in tiles if isinstance(t, dict) and t.get("crop") == crop)
        ctx[f"opp_n_{crop.lower()}"] = sum(1 for row in opp["tiles"] for t in row if isinstance(t, dict) and t.get("crop") == crop)
        ctx[f"seeds_{crop.lower()}"] = private["seeds"].get(crop, 0)
    for s in SHOPS:
        ctx[f"shop_{s.lower()}"] = shops.count(s)
    # per-product tables used by candidate features
    held_shed = {p: private["shed"].get(p, 0) for p in PRODUCTS}
    held_bags = {p: sum(b.get(p, 0) for b in private["inventories"]) for p in PRODUCTS}
    on_tiles, soon1, soon3, opp_vis = dict.fromkeys(PRODUCTS, 0), dict.fromkeys(PRODUCTS, 0), dict.fromkeys(PRODUCTS, 0), dict.fromkeys(PRODUCTS, 0)
    for c, t in tiles:
        if isinstance(t, dict) and t.get("yield_units"):
            on_tiles[t.get("crop") or PRODUCT_OF.get(t.get("animal"), "")] = on_tiles.get(t.get("crop") or PRODUCT_OF.get(t.get("animal"), ""), 0) + t["yield_units"]
        for horizon, table in ((1, soon1), (3, soon3)):
            prod, n = produce_soon(t, day, horizon)
            if prod:
                table[prod] += n
    for row in opp["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("yield_units"):
                k = t.get("crop") or PRODUCT_OF.get(t.get("animal"), "")
                opp_vis[k] = opp_vis.get(k, 0) + t["yield_units"]
    dawn = history.prices[max(0, len(history.prices) - 1 - hour)] if history.prices else market["prices"]
    today = history.prices[max(0, len(history.prices) - 1 - hour):] or [market["prices"]]
    prod = {}
    for p in PRODUCTS:
        price = market["prices"][p]
        ours4, net4 = history.window(p, 4, step, shops)
        ours24, net24 = history.window(p, 24, step, shops)
        prod[p] = {"price": price, "price_dawn": dawn[p], "price_rel": price / K.MARKET_PARAMS[p]["base"],
                   "price_hi": max(x[p] for x in today), "price_lo": min(x[p] for x in today),
                   "price_chg4": price - (history.prices[-5][p] if len(history.prices) >= 5 else price),
                   "buyers": sum(p in SHOPS[s] for s in shops),
                   "demand_1d": demand[p], "demand_3d": 3 * demand[p], "demand_6d": 6 * demand[p],
                   "demand_rest": demand[p] * max(0, 29 - day + (24 - hour) / 24),
                   "stock_shed": held_shed[p], "stock_bags": held_bags[p], "stock_tiles": on_tiles.get(p, 0),
                   "soon_1d": soon1.get(p, 0), "soon_3d": soon3.get(p, 0),
                   "liquidation": liquidation(p, held_shed[p] + held_bags[p], market["inventory"][p]),
                   "opp_visible": opp_vis.get(p, 0), "market_stock": market["inventory"][p],
                   "our_sold_4h": ours4, "our_sold_24h": ours24,
                   "opp_sold_4h": net4 - ours4, "opp_sold_24h": net24 - ours24}
    ctx["_prod"] = prod
    ctx["_history"] = history
    ctx["_positions"] = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
    return ctx


def candidate_rows(obs, seat, unit, cands, ctx, last_job=None, since_last=BIG):
    """One feature row per candidate job (kind, cell) for this worker."""
    farm, private = obs["farms"][seat], obs["private"]
    day, hour = obs["day"], obs["hour"]
    step = day * 24 + hour
    pos = ctx["_positions"][unit] if unit < len(ctx["_positions"]) else ctx["_positions"][0]
    inv = private["inventories"][unit] if unit < len(private["inventories"]) else {}
    others = [p for i, p in enumerate(ctx["_positions"]) if i != unit]
    shed_d = to_shed(pos)
    prod = ctx["_prod"]

    def tile_of(cell):
        return None if cell == "SHED" else farm["tiles"][cell // SIZE][cell % SIZE]

    def where(cell):
        return min(SHED_TILES, key=lambda s: dist(pos, s)) if cell == "SHED" else (cell % SIZE, cell // SIZE)

    def immediate(kind, item, t):
        """A rough rule value of doing the job now (D6), in dollars."""
        if not isinstance(t, dict):
            if kind == "PLANT" and item in CROPS:
                c = CROPS[item]
                return c["max_yield"] * prod[item]["price"] * (3 if c["ongoing"] else 1) - c["seed"]
            return 0.0
        product = t.get("crop") or PRODUCT_OF.get(t.get("animal"))
        price = prod[product]["price"] if product in prod else 0
        if kind == "HARVEST":
            return t.get("yield_units", 0) * price
        if kind == "WATER":
            return price * (CROPS[t["crop"]]["max_yield"] if t.get("consecutive_unwatered", 0) >= 1 else 1)
        if kind in ("CARE", "FEED"):
            return price * (1 + (t.get("pending_care_bonus", 0) if kind == "FEED" else 0))
        if kind in ("COLLECT_FERTILIZER",):
            return prod["FERTILIZER"]["price"]
        if kind == "FERTILIZE":
            return price
        return 0.0

    jobs = []
    for kind_full, cell in cands:
        kind, _, item = kind_full.partition(":")
        t = tile_of(cell)
        jobs.append((kind, item, cell, t, where(cell), immediate(kind, item, t)))
    values_near = {}
    for kind, item, cell, t, p, v in jobs:
        if cell != "SHED":
            values_near[cell] = values_near.get(cell, 0) + v
    prev = ctx.get("_history").previous_position(unit) if ctx.get("_history") is not None else None
    heading = (pos[0] - prev[0], pos[1] - prev[1]) if prev and prev != pos else None
    job_cells = [(c % SIZE, c // SIZE) for c, v in values_near.items() if v > 0]
    rows = []
    for kind, item, cell, t, p, value in jobs:
        d = dist(pos, p)
        needs = {"FEED": "WHEAT", "FERTILIZE": "FERTILIZER"}.get(kind) or (item if kind == "PLACE" and item in ANIMALS else None)
        detour = d if not needs or inv.get(needs, 0) > 0 else shed_d + to_shed(p)
        r = {"kind": KINDS.index(kind) if kind in KINDS else -1, "item": ITEMS.index(item) if item in ITEMS else -1,
             "dist": d, "detour": detour, "turns_left_after": ctx["turns_left"] - detour - 1,
             "tile_to_shed": 0 if cell == "SHED" else to_shed(p), "on_the_way": d + (0 if cell == "SHED" else to_shed(p)) - shed_d,
             "n_closer": sum(dist(o, p) < d for o in others), "nearest_other": min((dist(o, p) for o in others), default=BIG),
             "cluster_n": sum(1 for c in values_near if c != cell and dist(p, (c % SIZE, c // SIZE)) <= 2),
             "cluster_value": sum(v for c, v in values_near.items() if c != cell and dist(p, (c % SIZE, c // SIZE)) <= 2),
             "value_now": value, "inv_wheat": inv.get("WHEAT", 0), "inv_fert": inv.get("FERTILIZER", 0),
             "inv_goods": sum(n for k, n in inv.items() if k in PRODUCTS and k not in ("WHEAT", "FERTILIZER")),
             "inv_animals": sum(inv.get(a, 0) for a in ANIMALS), "is_farmer": int(unit == 0),
             "last_job": KINDS.index(last_job) if last_job in KINDS else -1, "since_last": since_last}
        # sweeping (diagnosis 2026-10-25): does this job continue my walk, are there more jobs beyond it, and how
        # far is the next job after it
        step_dir = ((p[0] > pos[0]) - (p[0] < pos[0]), (p[1] > pos[1]) - (p[1] < pos[1]))
        r["s_continues"] = (0 if not heading or d == 0 else
                            int(step_dir[0] * heading[0] + step_dir[1] * heading[1] > 0) - int(step_dir[0] * heading[0] + step_dir[1] * heading[1] < 0))
        r["s_beyond"] = sum(1 for c in job_cells if c != p and dist(p, c) <= 3 and dist(pos, c) == d + dist(p, c))
        r["s_next_gap"] = min((dist(p, c) for c in job_cells if c != p), default=BIG)
        # tile state (B, C), urgency (E)
        loss = BIG
        if isinstance(t, dict) and t.get("kind") == "PLANT":
            c = CROPS[t["crop"]]
            age = day - t["planted_day"]
            r.update({"t_age": age, "t_watered": int(t.get("watered_today", False)), "t_dry": t.get("consecutive_unwatered", 0),
                      "t_held": t.get("yield_units", 0), "t_held_frac": t.get("yield_units", 0) / c["max_yield"],
                      "t_fert_days": t.get("fertilized_until_day", -1) - day,
                      "t_next_prod": (c["first_yield_day"] - age) if age < c["first_yield_day"] else ((age - c["first_yield_day"]) % c["interval"] if c["ongoing"] else 0),
                      "t_rot": (t["max_lifespan_step"] - step) if t.get("max_lifespan_step", -1) > 0 else BIG})
            # tonight's outcome under the engine's rules (diagnosis 2026-10-24): dies on a second dry day; ongoing
            # crops produce on set nights, double if fertilized and watered that day
            price = prod[t["crop"]]["price"]
            dry = not t.get("watered_today", False)
            dies = dry and t.get("consecutive_unwatered", 0) >= 1
            ds = day + 1 - t["planted_day"] - c["first_yield_day"]
            prod_tonight = c["ongoing"] and ds >= 0 and ds % c["interval"] == 0 and ds // c["interval"] + 1 <= c["max_yield"]
            fert = t.get("fertilized_until_day", -1) >= day
            r.update({"n_dies_tonight": int(dies), "n_prod_tonight": int(prod_tonight),
                      "n_double_tonight": int(prod_tonight and fert),
                      "n_loss_if_dry": (t.get("yield_units", 0) * price + c["seed"] + (c["max_yield"] - t.get("yield_units", 0)) * price) if dies
                      else (price * (2 if fert else 1) if (dry and prod_tonight) else 0)})
            if t.get("consecutive_unwatered", 0) >= 1 and not t.get("watered_today"):
                loss = 24 - hour
            if t.get("max_lifespan_step", -1) > 0 and t.get("yield_units", 0):
                loss = min(loss, t["max_lifespan_step"] - step)
        elif isinstance(t, dict) and "animal" in t:
            a = ANIMALS[t["animal"]]
            since = day + 1 - t["placed_day"] - a["first_yield_day"]
            tonight = since >= 0 and since % a["interval"] == 0
            r.update({"t_age": day - t["placed_day"], "t_next_prod": 0 if tonight else ((-since) if since < 0 else a["interval"] - since % a["interval"]),
                      "t_fed": int(t.get("fed_today", False)), "t_cared": int(t.get("cared_today", False)),
                      "t_unfed": t.get("consecutive_unfed", 0), "t_bonus": t.get("pending_care_bonus", 0),
                      "t_held": t.get("yield_units", 0), "t_held_frac": t.get("yield_units", 0) / a["max_held"],
                      "t_fert_ready": int(t.get("fertilizer_available", False))})
            price = prod[a["product"]]["price"] if a["product"] in prod else 0
            unfed = not t.get("fed_today", False)
            escapes = unfed and t.get("consecutive_unfed", 0) >= 1
            r.update({"n_prod_tonight": int(tonight), "n_escapes_tonight": int(escapes),
                      "n_full": int(t.get("yield_units", 0) >= a["max_held"]),
                      "n_loss_if_unfed": (a["cost"] + t.get("yield_units", 0) * price) if escapes
                      else (price * (1 + t.get("pending_care_bonus", 0)) if (unfed and tonight) else 0)})
            if not t.get("fed_today") and (t.get("consecutive_unfed", 0) >= 1 or tonight):
                loss = 24 - hour
        r["loss_in"] = loss
        r["deadline"] = int(loss <= ctx["turns_left"])
        # money (D) for the product this job concerns
        product = (t.get("crop") or PRODUCT_OF.get(t.get("animal"))) if isinstance(t, dict) else (item if item in PRODUCTS else None)
        if kind in ("COLLECT_FERTILIZER", "FERTILIZE"):
            product = "FERTILIZER" if kind == "COLLECT_FERTILIZER" else product
        if product in prod:
            r.update({f"p_{k}": v for k, v in prod[product].items()})
        r.update({k: v for k, v in ctx.items() if not k.startswith("_")})
        rows.append(r)
    return rows

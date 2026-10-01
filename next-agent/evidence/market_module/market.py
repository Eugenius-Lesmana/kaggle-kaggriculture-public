"""Generic market rules derived from the Apache-2.0 Metav4/F4 sources.

SPDX-License-Identifier: Apache-2.0
Attribution: Ahmed Berat Ozer, prvsiyan, yhay81, thomastschinkel and the
contributors/notices in agents/ours/h1-substrate-{metav4,f4}/main.py.
No route tapes, opponent identity detection, engine import, or network calls.
Call once per turn. Existing planner orders keep their purchase barriers.
"""
import math

ENABLE_WHEAT_ROUND_TRIP = False  # Opponent-dependent opening; measured -$3 vs v0.10.
ENABLE_PRICE_GATE_LEAD = True
ENABLE_MODEL_LEAD = True
ENABLE_EXPOSURE_ORDERING = True
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
MODEL_ITEMS = ("MILK", "STRAWBERRY", "WOOL")
SHOPS = {
    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),
    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_PARAM_ROWS = (
    (25, 400, "sqrt", .8, "log", .2), (35, 450, "hinge", 1, "sqrt", .7),
    (60, 200, "hinge", .4, "sqrt", .6), (120, 100, "sqrt", .7, "linear", 1.6),
    (250, 300, "log", .2, "sq", 3.6), (50, 332, "hinge", .4, "log", .2),
    (160, 122, "sqrt", .6, "linear", 1.6), (200, 105, "log", .2, "sq", 3.2),
    (100, 200, "linear", .4, "linear", .4),
)
PARAMS = {item: dict(zip(("base", "T", "below_func", "below_target", "above_func", "above_target"), row), I0=10000)
          for item, row in zip(PRODUCTS, _PARAM_ROWS)}
_STATE = {}


def _shape(kind, x, threshold):
    x = max(0, x)
    if kind == "sqrt":
        return math.sqrt(x)
    if kind == "sq":
        return x * x
    if kind == "log":
        return math.log1p(x)
    if kind == "log10":
        return math.log10(1 + x)
    if kind == "hinge":
        return x / threshold + 8 * max(0, x / threshold - 1) ** 2
    if kind != "linear":
        raise ValueError("unknown price shape: " + kind)
    return x


def price(item, inventory, overrides=None):
    """Engine quote, including observation market.params overrides."""
    params = {**PARAMS[item], **(overrides or {}).get(item, {})}
    distance = params["I0"] - inventory
    prefix = "below" if distance > 0 else "above"
    shape = params[prefix + "_func"]
    change = params[prefix + "_target"] * params["base"] * _shape(shape, abs(distance), params["T"]) / _shape(shape, params["T"], params["T"])
    return max(1, round(params["base"] + (change if distance > 0 else -change)))


def drain(item, step, shops):
    """Consumption AFTER market orders at step 0,4,...; town also at 0,24,..."""
    result = int(step % 24 == 0 and item != "FERTILIZER")
    if step % 4 == 0:
        for shop in shops:
            products = SHOPS.get(shop, ())
            if item in products:
                result += 2 if len(products) == 1 else 1
    return result


def exposure(obs, order):
    """Dollars exposed to a hypothetical 8–24 unit rival sale, as in R37."""
    item, quantity = order[1:3]
    stock = obs["private"].get("shed", {})
    quantity = min(quantity, stock.get(item, 0))
    inventory = obs["market"]["inventory"]
    if item not in PARAMS or item not in inventory or quantity <= 0:
        return 0
    animal = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}.get(item)
    rival = obs["farms"][1 - obs["player"]]
    standing = sum(max(0, int(tile.get("yield_units", 0))) for row in rival["tiles"] for tile in row
                   if isinstance(tile, dict) and (tile.get("crop") == item or animal and tile.get("animal") == animal))
    batch = min(24, max(8, standing))
    params = obs["market"].get("params")
    return sum(price(item, inventory[item] + j, params) - price(item, inventory[item] + batch + j, params)
               for j in range(quantity))


def _opening(obs, orders):
    if not ENABLE_WHEAT_ROUND_TRIP or obs["step"] != 0 or obs["private"].get("shed", {}).get("WHEAT", 0):
        return orders
    candidates = [i for i, order in enumerate(orders) if order[:2] == ["BUY_PRODUCT", "WHEAT"]]
    if candidates != [0] or orders[0][2] != 5 or any(o[:2] == ["SELL", "WHEAT"] for o in orders) or len(orders) >= 10:
        return orders
    inventory = obs["market"]["inventory"].get("WHEAT")
    if inventory is None or sum(obs["private"].get("shed", {}).values()) > 80:
        return orders
    params = obs["market"].get("params")
    # Worst-case concurrent wheat buyer; spend only cash beyond planner inputs.
    buy_cost = sum(price("WHEAT", inventory - (2 * j - 1), params) for j in range(1, 21))
    me = obs["farms"][obs["player"]]
    reserve = 500
    hires = me.get("hires_today", len(me.get("hands", [])))
    land = len(me.get("unlocked_quadrants", ["NW"])) - 1
    for order in orders:
        if not order or order[:2] == ["BUY_PRODUCT", "WHEAT"]:
            continue
        if order[0] == "HIRE":
            a, b = 1, 1
            for _ in range(hires):
                a, b = b, a + b
            reserve += a
            hires += 1
        elif order[0] == "BUY_LAND":
            reserve += (1000, 2000, 4000)[min(land, 2)]
            land += 1
        elif order[0] in ("BUY_SEED", "BUY_ANIMAL"):
            costs = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80} if order[0] == "BUY_SEED" else {"GOOSE": 300, "COW": 400, "SHEEP": 500}
            reserve += costs[order[1]] * order[2]
        elif order[0] == "BUY_PRODUCT":
            item, quantity = order[1:3]
            reserve += sum(price(item, obs["market"]["inventory"][item] - (2 * j - 1), params) for j in range(1, quantity + 1))
    if me["money"] < buy_cost + reserve:
        return orders
    index = candidates[0]
    return orders[:index] + [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15]] + orders[index + 1:]


def market_orders(obs, planner_orders):
    """Copy planner orders; add bounded held-stock lead sales and rank SELL blocks.

    Default season: 24 turns/day, 720 steps, 100-item shed, ten order slots.
    Missing market data abstains. Existing purchases, quantities, placeholders,
    and sale/purchase barriers are preserved. No projected worker drops assumed.
    """
    if not isinstance(planner_orders, (list, tuple)) or len(planner_orders) > 10:
        raise ValueError("planner_orders must contain at most ten orders")
    orders = []
    for order in planner_orders:
        if not isinstance(order, (list, tuple)):
            raise ValueError("each market order must be a sequence")
        order = list(order)
        if order and (order[0] not in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND")
                      or order[0] not in ("HIRE", "BUY_LAND") and
                      (len(order) != 3 or not isinstance(order[2], int) or isinstance(order[2], bool) or order[2] < 0)):
            raise ValueError("malformed market order")
        if order:
            allowed = {"SELL": PRODUCTS, "BUY_PRODUCT": ("WHEAT", "FERTILIZER"),
                       "BUY_SEED": PRODUCTS[:5], "BUY_ANIMAL": ("GOOSE", "COW", "SHEEP")}
            if order[0] in allowed and order[1] not in allowed[order[0]] or order[0] in ("HIRE", "BUY_LAND") and len(order) != 1:
                raise ValueError("unknown market item or malformed atomic order")
        orders.append(order)
    market = obs.get("market", {})
    inventory, prices = market.get("inventory", {}), market.get("prices", {})
    if not inventory or not prices:
        return orders
    orders = _opening(obs, orders)
    step, seat = int(obs["step"]), int(obs["player"])
    shops = obs.get("town", {}).get("unlocked_shops", [])
    previous = _STATE.get(seat)
    history = previous["history"] if previous and step == previous["step"] + 1 else {item: [] for item in MODEL_ITEMS}
    if previous and previous["step"] == step - 1:
        for item in MODEL_ITEMS:
            if item in inventory and item in previous["inventory"] and prices.get(item, 0) > 1 and previous["own"].get(item) is not None:
                rival = inventory[item] - previous["inventory"][item] + drain(item, step - 1, previous["shops"]) - previous["own"][item]
                history[item].append(max(0, rival))
                history[item] = history[item][-12:]
    shed = obs["private"].get("shed", {})
    blocked = {order[1] for order in orders if len(order) >= 2 and order[0] in ("SELL", "BUY_PRODUCT", "BUY_ANIMAL")}
    if ENABLE_PRICE_GATE_LEAD and 192 <= step < 696:
        # A live planner will read the smaller shed next turn; no tape debt needed.
        # All held non-input produce is assumed intended for eventual sale.
        for item in PRODUCTS:
            base = (market.get("params") or {}).get(item, {}).get("base", PARAMS[item]["base"])
            if item not in ("WHEAT", "FERTILIZER") and item not in blocked and len(orders) < 10 and shed.get(item, 0) > 0 and prices.get(item, 0) > base:
                orders.append(["SELL", item, shed[item]])
                blocked.add(item)
    hour = step % 24
    if ENABLE_MODEL_LEAD and 144 <= step < 696 and 1 <= hour <= 22:
        for item in MODEL_ITEMS:
            if item in blocked or len(orders) >= 10 or shed.get(item, 0) <= 0 or prices.get(item, 0) <= 1 or item not in inventory:
                continue
            quote = prices[item]
            if hour == 1 and quote < 95:
                peers = [prices.get(other, 0) for other in MODEL_ITEMS if other != item]
                if quote < 20 or quote < 50 and min(peers) < 30 or quote >= 50 and shed[item] < 3 and min(peers) < 30:
                    continue
            recent = history[item][-4:]
            rival = sum(recent) / len(recent) if recent else 0
            inv = inventory[item]
            future = max(0, int(inv + rival + 6 - drain(item, step, shops)))
            if price(item, future, market.get("params")) < price(item, inv, market.get("params")) - .5:
                batch = 10 if hour == 1 or quote >= 100 or 10 <= hour <= 13 and quote >= 30 else 6 if 10 <= hour <= 13 and quote >= 10 else 3
                orders.append(["SELL", item, min(shed[item], batch)])
    if ENABLE_EXPOSURE_ORDERING:
        protected = {o[1] for o in orders if len(o) >= 2 and o[0] == "BUY_PRODUCT"}
        start = 0
        while start < len(orders):
            if len(orders[start]) < 3 or orders[start][0] != "SELL" or orders[start][1] in protected:
                start += 1
                continue
            end = start + 1
            while end < len(orders) and len(orders[end]) >= 3 and orders[end][0] == "SELL" and orders[end][1] not in protected:
                end += 1
            block = orders[start:end]
            if len({o[1] for o in block}) == len(block):
                orders[start:end] = sorted(block, key=lambda order: exposure(obs, order), reverse=True)
            start = end
    own = {}
    for item in MODEL_ITEMS:
        requested = sum(o[2] for o in orders if len(o) >= 3 and o[:2] == ["SELL", item])
        # A planner sale beyond observed shed may rely on a DROP we cannot see.
        bounded = (requested <= shed.get(item, 0) and prices.get(item, 0) > 1
                   and item in inventory and price(item, inventory[item] + requested - 1, market.get("params")) > 1)
        own[item] = requested if bounded else None if requested else 0
    _STATE[seat] = {"step": step, "inventory": dict(inventory), "shops": list(shops), "own": own, "history": history}
    return orders

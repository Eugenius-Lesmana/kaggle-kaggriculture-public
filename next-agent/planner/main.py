"""Kaggriculture V0.8B candidate: efficient deterministic opener."""

import math
from typing import NamedTuple


BOOTSTRAP_HANDS = 4
TURNS_PER_DAY = 24
EPISODE_STEPS = 720
LAST_EXECUTABLE_STEP = EPISODE_STEPS - 2
SHED_CAPACITY = 100
INFINITY = 10**9

# These three constants define a complete experiment without forking the logic.
OPENER_PROFILE = "V08B"        # TOP4 (rejected: -0.034 alone, -0.105 with skeleton) | V08B | V07 | A
LAND_POLICY = "programme"          # top4 | programme | none | fixed | adaptive
HAND_POLICY = "programme"          # top4 | programme | fixed | adaptive
STRATEGY_OVERRIDE = None       # Optional dict or callable(snapshot, observation); TOP4 sets it below.
FIXED_LAND_DAYS = (6, 9)
LAND_PRICES = (1000, 2000, 4000)
LAND_ORDER = ("NE", "SW", "SE")
LIQUIDATE_DAY = 28
ENABLE_CLEAR_FINISHED_ONGOING = True
HARVEST_WAIT_UNTIL_HOUR = 0
FINAL_PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                  "EGG", "MILK", "WOOL", "FERTILIZER")
ACTION_VALUE = 2
MIN_CELL_MARGIN = 8
SWITCH_MARGIN = 0.20
MAX_ANIMALS_PER_FIELD = 5
MAX_HIRES_PER_TURN = 6
LAND_FILL_TARGET = 0.60
OPPONENT_SUPPLY_WEIGHT = 0.50
MAX_CROP_SHARE = 0.35
MAX_LATE_SHOCK_CELLS = 6
ENABLE_BOUNDARY_CROPS = False  # Failed fresh-seed validation; retained for isolated research.
ENABLE_DROP_SALES = False

# V0.6 is promoted phase-by-phase. Unsafe fixed fill/staffing/crop quotas stay
# measurable in shadow while the validated marginal capacity/forecast path runs.
ENABLE_V06_WEED_RECOVERY = True
ENABLE_V06_FILL_GATE = False
ENABLE_V06_HEALTH_STAFFING = False
ENABLE_V06_JOINT_CAPACITY = True
ENABLE_V06_CROP_CAP = False
ENABLE_V06_FULL_CHAIN_VALUATION = True
ENABLE_V06_REGIME_VALUATION = True
ENABLE_V06_SHOP_FORECAST = True
ENABLE_V06_OPPONENT_PENALTY = True

CROP_DATA = {
    "WHEAT": (2, 4, 6, 4, False, 0),
    "CARROT": (2, 3, 4, 3, False, 0),
    "TOMATO": (8, 8, 4, 4, True, 1),
    "STRAWBERRY": (10, 10, 4, 4, True, 2),
    "MELON": (10, 12, 6, 6, False, 0),
}
ANIMAL_DATA = {"GOOSE": (300, "EGG", 4), "COW": (400, "MILK", 6), "SHEEP": (500, "WOOL", 6)}
ANIMAL_TIMING = {"GOOSE": (4, 1), "COW": (8, 2), "SHEEP": (6, 3)}

MARKET_PARAMS = {
    "WHEAT": (25, 10000, 400, "sqrt", 0.80, "log", 0.20),
    "CARROT": (35, 10000, 450, "hinge", 1.00, "sqrt", 0.70),
    "TOMATO": (60, 10000, 200, "hinge", 0.40, "sqrt", 0.60),
    "STRAWBERRY": (120, 10000, 100, "sqrt", 0.70, "linear", 1.60),
    "MELON": (250, 10000, 300, "log", 0.20, "sq", 3.60),
    "EGG": (50, 10000, 332, "hinge", 0.40, "log", 0.20),
    "MILK": (160, 10000, 122, "sqrt", 0.60, "linear", 1.60),
    "WOOL": (200, 10000, 105, "log", 0.20, "sq", 3.20),
    "FERTILIZER": (100, 10000, 200, "linear", 0.40, "linear", 0.40),
}

CROP_ECONOMICS = {
    "WHEAT": (10, 25, 4, 4),
    "CARROT": (20, 35, 3, 3),
    "TOMATO": (50, 60, 4, 11),
    "STRAWBERRY": (100, 120, 4, 16),
    "MELON": (80, 250, 6, 10),
}
SHOP_DEMAND = {
    "BAKERY": {"EGG": 1, "WHEAT": 1},
    "PIZZA_SHOP": {"MILK": 1, "TOMATO": 1, "WHEAT": 1},
    "BRUNCH_SPOT": {"EGG": 1, "WHEAT": 1, "STRAWBERRY": 1},
    "YARN_STORE": {"WOOL": 2},
    "ICE_CREAM_SHOP": {"STRAWBERRY": 1, "MILK": 1, "WHEAT": 1},
    "PET_CAFE": {"CARROT": 2},
    "SMOOTHIE_SHOP": {"STRAWBERRY": 1, "MILK": 1},
    "FARMERS_MARKET": {"WHEAT": 1, "CARROT": 1, "TOMATO": 1, "STRAWBERRY": 1},
}

CROP_PLAN = {
    "WHEAT": ((3, 0), (4, 0), (2, 1), (3, 1), (4, 1), (1, 2), (2, 2),
              (3, 2), (0, 3), (1, 3), (2, 3), (0, 4), (1, 4), (2, 4)),
    "MELON": ((0, 0), (1, 0), (2, 0), (0, 1), (1, 1), (0, 2)),
}
CROP_PLAN_A = {
    "MELON": ((0, 0), (1, 0), (2, 0)),
    "WHEAT": ((2, 2), (3, 2), (0, 3), (1, 3), (2, 3), (0, 4), (3, 0), (4, 0), (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (0, 2), (1, 2)),
    "STRAWBERRY": ((1, 4), (2, 4)),
}
BOOTSTRAP_LAYOUT = CROP_PLAN
PLANT_CUTOFF = {"WHEAT": 25, "CARROT": 26, "TOMATO": 18, "STRAWBERRY": 13, "MELON": 19}
MIDGAME_START_DAY = 3
MIDGAME_FORCED_DAY = 6
MIDGAME_END_DAY = 27
FEED_CELLS = CROP_PLAN["WHEAT"][:7]
FLEXIBLE_CELLS = CROP_PLAN["MELON"] + CROP_PLAN["WHEAT"][7:]
ANIMAL_LAYOUT = {
    (4, 2): "SHEEP", (3, 3): "SHEEP", (4, 3): "GOOSE",
    (3, 4): "COW", (4, 4): "GOOSE",
}
ANIMAL_LAYOUT_A = {
    (4, 2): "SHEEP", (3, 3): "SHEEP", (4, 3): "SHEEP",
    (3, 4): "COW", (4, 4): "COW",
}
SHED_ACCESS = ((4, 4), (5, 4), (5, 5), (4, 5))
QUADRANT_BOUNDS = {"NE": (5, 10, 0, 5), "SW": (0, 5, 5, 10), "SE": (5, 10, 5, 10)}


class Task(NamedTuple):
    priority: int
    operation: str
    target: tuple
    argument: str | None
    owner: int | None
    deadline: int
    reason: str
    quantity: int = 1


# Frozen capital-heavy control retained for direct opener comparisons.
OPENING_FIELD_A = (
    (["PASS"], []),
    (["NORTH"], []),
    (["WEST"], [["PICKUP", "COW"], ["WEST"], ["NORTH"], ["WEST"], ["PICKUP", "COW"]]),
    (["WEST"], [["NORTH"], ["PICKUP", "SHEEP"], ["NORTH"], ["NORTH"], ["BUILD_PASTURE"]]),
    (["PLANT", "MELON"], [["BUILD_PASTURE"], ["PICKUP", "WHEAT"], ["NORTH"], ["PICKUP", "SHEEP"], ["PLACE", "COW"]]),
    (["WATER"], [["PLACE", "COW"], ["WEST"], ["NORTH"], ["PICKUP", "WHEAT"], ["CARE"]]),
    (["WEST"], [["CARE"], ["BUILD_PASTURE"], ["PLANT", "MELON"], ["WEST"], ["WEST"]]),
    (["PLANT", "MELON"], [["WEST"], ["PLACE", "SHEEP"], ["WATER"], ["NORTH"], ["WEST"]]),
    (["WATER"], [["NORTH"], ["FEED"], ["WEST"], ["BUILD_PASTURE"], ["WEST"]]),
    (["EAST"], [["PLANT", "MELON"], ["CARE"], ["WEST"], ["PLACE", "SHEEP"], ["PLANT", "MELON"]]),
    (["EAST"], [["WATER"], ["NORTH"], ["WEST"], ["FEED"], ["WATER"]]),
    (["CARE"], [["WEST"], ["NORTH"], ["WEST"], ["CARE"], ["WEST"]]),
    (["PASS"], [["PLANT", "MELON"], ["NORTH"], ["PLANT", "WHEAT"], ["WEST"], ["PLANT", "MELON"]]),
    (["WEST"], [["WATER"], ["PLANT", "MELON"], ["WATER"], ["NORTH"], ["WATER"]]),
    (["EAST"], [["WEST"], ["WATER"], ["NORTH"], ["NORTH"], ["NORTH"]]),
    (["PASS"], [["PLANT", "MELON"], ["NORTH"], ["PLANT", "WHEAT"], ["PLANT", "MELON"], ["PLANT", "WHEAT"]]),
    (["WEST"], [["WATER"], ["PLANT", "MELON"], ["WATER"], ["WATER"], ["WATER"]]),
    (["EAST"], [["WEST"], ["WATER"], ["EAST"], ["WEST"], ["PASS"]]),
    (["PASS"], [["PLANT", "WHEAT"], ["EAST"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"], ["PASS"]]),
    (["WEST"], [["WATER"], ["PLANT", "MELON"], ["WATER"], ["WATER"], ["EAST"]]),
    (["PASS"], [["PASS"], ["WATER"], ["EAST"], ["PASS"], ["PASS"]]),
    (["PASS"], [["PASS"], ["PASS"], ["PLANT", "WHEAT"], ["PASS"], ["PASS"]]),
    (["PASS"], [["PASS"], ["PASS"], ["WATER"], ["PASS"], ["PASS"]]),
    (["PASS"], [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]),
)


# Replay-derived liquid opening: 14 wheat, 6 melons, 1 cow, 2 sheep, 2 geese.
OPENING_FIELD = (
    (["PASS"], []),
    (["PASS"], [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]),
    (["WEST"], [["WEST"], ["PICKUP", "GOOSE"], ["PICKUP", "GOOSE"], ["WEST"], ["PICKUP", "COW"]]),
    (["WEST"], [["WEST"], ["PICKUP", "SHEEP", 2], ["PICKUP", "WHEAT"], ["WEST"], ["PICKUP", "WHEAT"]]),
    (["WEST"], [["WEST"], ["PICKUP", "WHEAT", 3], ["WEST"], ["WEST"], ["WEST"]]),
    (["WEST"], [["WEST"], ["NORTH"], ["NORTH"], ["WEST"], ["WEST"]]),
    (["NORTH"], [["NORTH"], ["NORTH"], ["BUILD_COOP"], ["PLANT", "WHEAT"], ["BUILD_PASTURE"]]),
    (["PLANT", "WHEAT"], [["PLANT", "WHEAT"], ["BUILD_COOP"], ["PLACE", "GOOSE"], ["WATER"], ["PLACE", "COW"]]),
    (["WATER"], [["WATER"], ["PLACE", "GOOSE"], ["FEED"], ["EAST"], ["FEED"]]),
    (["NORTH"], [["EAST"], ["FEED"], ["CARE"], ["NORTH"], ["CARE"]]),
    (["PLANT", "MELON"], [["NORTH"], ["CARE"], ["PASS"], ["NORTH"], ["WEST"]]),
    (["WATER"], [["PLANT", "WHEAT"], ["WEST"], ["PASS"], ["PLANT", "WHEAT"], ["PLANT", "WHEAT"]]),
    (["NORTH"], [["WATER"], ["BUILD_PASTURE"], ["PASS"], ["WATER"], ["WATER"]]),
    (["PLANT", "MELON"], [["EAST"], ["PLACE", "SHEEP"], ["PASS"], ["EAST"], ["WEST"]]),
    (["WATER"], [["NORTH"], ["FEED"], ["PASS"], ["NORTH"], ["PLANT", "WHEAT"]]),
    (["EAST"], [["PLANT", "WHEAT"], ["CARE"], ["PASS"], ["PLANT", "WHEAT"], ["WATER"]]),
    (["PLANT", "MELON"], [["WATER"], ["NORTH"], ["PASS"], ["WATER"], ["EAST"]]),
    (["WATER"], [["EAST"], ["PLANT", "WHEAT"], ["PASS"], ["NORTH"], ["NORTH"]]),
    (["NORTH"], [["PLANT", "WHEAT"], ["WATER"], ["PASS"], ["PLANT", "MELON"], ["PLANT", "WHEAT"]]),
    (["PLANT", "MELON"], [["WATER"], ["EAST"], ["PASS"], ["WATER"], ["WATER"]]),
    (["WATER"], [["NORTH"], ["BUILD_PASTURE"], ["PASS"], ["EAST"], ["PASS"]]),
    (["WEST"], [["PLANT", "WHEAT"], ["PLACE", "SHEEP"], ["PASS"], ["PLANT", "WHEAT"], ["PASS"]]),
    (["PLANT", "MELON"], [["WATER"], ["FEED"], ["PASS"], ["WATER"], ["PASS"]]),
    (["WATER"], [["PASS"], ["CARE"], ["PASS"], ["PASS"], ["PASS"]]),
)


V07_OPENING_FIELD = (
    (["PASS"], []),
    (["PASS"], []),
)


# Replay-derived V46 day-0 backbone. Shops and weeds cannot diverge this early;
# the adaptive programme takes over after the first reset.
V08B_OPENING_FIELD = (
    (["PASS"], []),
    (["NORTH"], []),
    (["SOUTH"], [["PICKUP", "COW"], ["PASS"], ["NORTH"], ["NORTH"], ["PICKUP", "COW"]]),
    (["PICKUP", "SHEEP"], [["NORTH"], ["PASS"], ["NORTH"], ["NORTH"], ["BUILD_PASTURE"]]),
    (["PICKUP", "WHEAT"], [["BUILD_PASTURE"], ["PASS"], ["NORTH"], ["NORTH"], ["PLACE", "COW"]]),
    (["NORTH"], [["PLACE", "COW"], ["PASS"], ["NORTH"], ["WEST"], ["CARE"]]),
    (["WEST"], [["NORTH"], ["PASS"], ["NORTH"], ["WEST"], ["PICKUP", "SHEEP"]]),
    (["BUILD_PASTURE"], [["NORTH"], ["PASS"], ["PLANT", "MELON"], ["PLANT", "MELON"], ["PICKUP", "WHEAT"]]),
    (["PLACE", "SHEEP"], [["PLANT", "MELON"], ["PASS"], ["WATER"], ["WATER"], ["WEST"]]),
    (["FEED"], [["WATER"], ["PASS"], ["WEST"], ["NORTH"], ["BUILD_PASTURE"]]),
    (["CARE"], [["WEST"], ["PASS"], ["PLANT", "MELON"], ["WEST"], ["PLACE", "SHEEP"]]),
    (["WEST"], [["PLANT", "MELON"], ["PASS"], ["WATER"], ["PLANT", "MELON"], ["FEED"]]),
    (["PLANT", "MELON"], [["WATER"], ["PASS"], ["WEST"], ["WATER"], ["CARE"]]),
    (["WATER"], [["SOUTH"], ["PASS"], ["PLANT", "WHEAT"], ["WEST"], ["WEST"]]),
    (["WEST"], [["WEST"], ["PASS"], ["WATER"], ["PLANT", "WHEAT"], ["WEST"]]),
    (["PLANT", "MELON"], [["PLANT", "MELON"], ["PASS"], ["WEST"], ["WATER"], ["PLANT", "MELON"]]),
    (["WATER"], [["WATER"], ["PASS"], ["PLANT", "WHEAT"], ["WEST"], ["WATER"]]),
    (["PASS"], [["WEST"], ["PASS"], ["WATER"], ["PLANT", "WHEAT"], ["WEST"]]),
    (["PASS"], [["PLANT", "MELON"], ["PASS"], ["PASS"], ["WATER"], ["PLANT", "MELON"]]),
    (["PASS"], [["WATER"], ["PASS"], ["PASS"], ["NORTH"], ["WATER"]]),
    (["PASS"], [["WEST"], ["PASS"], ["PASS"], ["PLANT", "WHEAT"], ["NORTH"]]),
    (["PASS"], [["PLANT", "WHEAT"], ["PASS"], ["PASS"], ["WATER"], ["PLANT", "WHEAT"]]),
    (["PASS"], [["WATER"], ["PASS"], ["PASS"], ["PASS"], ["WATER"]]),
    (["PASS"], [["PASS"], ["PASS"], ["PASS"], ["PASS"], ["PASS"]]),
)

V08B_OPENING_MARKET = (
    [["BUY_PRODUCT", "WHEAT", 7], ["SELL", "WHEAT", 2]],
    [["BUY_PRODUCT", "WHEAT", 30], *[["HIRE"] for _ in range(5)],
     ["BUY_ANIMAL", "COW", 2], ["BUY_ANIMAL", "SHEEP", 2]],
    [["SELL", "WHEAT", 30]],
    [], [], [],
    [["BUY_SEED", "MELON", 2]],
    [["BUY_SEED", "MELON", 1]],
    [],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 2]],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 3]],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 2]],
    [],
    [["BUY_SEED", "WHEAT", 1]],
    [["BUY_SEED", "WHEAT", 2]],
    [], [], [],
)


def opener_field():
    if OPENER_PROFILE == "TOP4":
        return ()       # decide() replays TOP4_SCRIPT behind a position guard
    if OPENER_PROFILE == "V08B":
        return V08B_OPENING_FIELD
    if OPENER_PROFILE == "V07":
        return V07_OPENING_FIELD
    return OPENING_FIELD_A if OPENER_PROFILE == "A" else OPENING_FIELD


def base_crop_plan():
    if OPENER_PROFILE == "TOP4":
        return top4_nw_plan()[0]
    return CROP_PLAN_A if OPENER_PROFILE in {"A", "V07", "V08B"} else CROP_PLAN


def base_feed_cells():
    return base_crop_plan().get("WHEAT", ())


def base_flexible_cells():
    plan = base_crop_plan()
    return tuple(cell for crop, cells in plan.items() if crop != "WHEAT" for cell in cells)


def animal_layout():
    if OPENER_PROFILE == "TOP4":
        return top4_nw_plan()[1]
    return ANIMAL_LAYOUT_A if OPENER_PROFILE in {"A", "V07", "V08B"} else ANIMAL_LAYOUT


def expansion_cells(quadrant):
    """All usable expansion cells, reserving only the quadrant's shed access."""
    x0, x1, y0, y1 = QUADRANT_BOUNDS[quadrant]
    access = next(cell for cell in SHED_ACCESS if x0 <= cell[0] < x1 and y0 <= cell[1] < y1)
    cells = ((x, y) for y in range(y0, y1) for x in range(x0, x1) if (x, y) != access)
    return tuple(sorted(cells, key=lambda cell: (distance(cell, access), cell[1], cell[0])))


def serviceable_expansion_cells(quadrant):
    """Current router work set; four distant cells stay measured reserves."""
    return expansion_cells(quadrant)[:20]


class ProgrammeSpec(NamedTuple):
    name: str
    expansion_animals: dict
    expansion_crops: dict


PROGRAMMES = {
    "GENERAL": ProgrammeSpec(
        "GENERAL",
        {"NE": ("COW", "COW", "GOOSE", "GOOSE"),
         "SW": ("SHEEP", "SHEEP", "SHEEP", "GOOSE", "GOOSE")},
        {"NE": (("STRAWBERRY", 16), ("WHEAT", 4)),
         "SW": (("STRAWBERRY", 13), ("WHEAT", 6))},
    ),
    "DAIRY": ProgrammeSpec(
        "DAIRY",
        {"NE": ("COW",) * 4, "SW": ("COW",) * 5},
        {"NE": (("STRAWBERRY", 16), ("WHEAT", 4)),
         "SW": (("STRAWBERRY", 13), ("WHEAT", 6))},
    ),
    "YARN": ProgrammeSpec(
        "YARN",
        {"NE": ("SHEEP",) * 4, "SW": ("SHEEP",) * 5},
        {"NE": (("STRAWBERRY", 14), ("WHEAT", 6)),
         "SW": (("STRAWBERRY", 11), ("WHEAT", 8))},
    ),
}
PROGRAMME_CHECKPOINT_DAYS = (6, 9)
PROGRAMME_HANDS = {0: 5, 1: 10, 2: 6, 3: 6, 4: 6, 5: 6, 6: 8, 7: 9, 8: 9}


def programme_candidate(obs):
    """Choose a complete compatible route from durable shop demand."""
    shops = obs.get("town", {}).get("unlocked_shops", [])
    yarn = 2 * shops.count("YARN_STORE")
    dairy = sum(shops.count(shop) for shop in
                ("PIZZA_SHOP", "ICE_CREAM_SHOP", "SMOOTHIE_SHOP"))
    if yarn >= 2 and yarn > dairy:
        return "YARN"
    if dairy >= 2 and dairy > yarn:
        return "DAIRY"
    return "GENERAL"


def programme_layout(obs, name):
    """Materialize the selected programme over every unlocked quadrant."""
    spec = PROGRAMMES[name]
    me = obs["farms"][obs["player"]]
    unlocked = set(me.get("unlocked_quadrants", ["NW"]))
    crops = {pos: crop for crop, cells in base_crop_plan().items() for pos in cells}
    animals = dict(animal_layout())
    for quadrant in ("NE", "SW"):
        if quadrant not in unlocked:
            continue
        cells = list(expansion_cells(quadrant))
        herd = spec.expansion_animals[quadrant]
        animal_cells = cells[:len(herd)]
        animals.update(zip(animal_cells, herd))
        cursor = len(herd)
        for crop, amount in spec.expansion_crops[quadrant]:
            for pos in cells[cursor:cursor + amount]:
                crops[pos] = crop
            cursor += amount
    return crops, animals


def available_flexible_cells(obs):
    cells = list(base_flexible_cells())
    for quadrant in obs["farms"][obs["player"]].get("unlocked_quadrants", ["NW"]):
        if quadrant != "NW":
            cells.extend(serviceable_expansion_cells(quadrant))
    return tuple(cells)


def animal_reserve_cells(obs):
    """Temporarily preserve expansion slots while recurring capacity is affordable."""
    if not ENABLE_V06_JOINT_CAPACITY:
        return ()
    if obs.get("day", 0) >= 17:
        return ()
    unlocked = obs["farms"][obs["player"]].get("unlocked_quadrants", ["NW"])
    if max(animal_opportunity(obs, animal)["net"] for animal in ANIMAL_DATA) <= 0:
        return ()
    return tuple(pos for quadrant in unlocked if quadrant != "NW"
                 for pos in serviceable_expansion_cells(quadrant)[:MAX_ANIMALS_PER_FIELD])


def last_executable_step(obs):
    return int(obs.get("episode_steps", EPISODE_STEPS)) - 2


def turns_remaining(obs):
    return max(0, last_executable_step(obs) - obs.get("step", 0))


def liquidation_stage(obs):
    if obs.get("day", 0) < LIQUIDATE_DAY:
        return None
    remaining = turns_remaining(obs)
    return "FINAL" if remaining <= TURNS_PER_DAY else "CLOSEOUT" if remaining <= 3 * TURNS_PER_DAY else "ROLLING"


def nearest_shed_distance(pos):
    return min(distance(pos, access) for access in SHED_ACCESS)


def opening_complete(obs):
    """Use observed milestones, with a day-six recovery fallback."""
    day = obs.get("day", 0)
    if day < MIDGAME_START_DAY:
        return False
    me = obs["farms"][obs["player"]]
    cells = tuple(cell for group in base_crop_plan().values() for cell in group)
    crops = sum(
        isinstance(me["tiles"][y][x], dict) and me["tiles"][y][x].get("kind") == "PLANT"
        for x, y in cells
    )
    animals = sum(
        bool(isinstance(tile_at, dict) and tile_at.get("animal"))
        for row in me["tiles"] for tile_at in row
    )
    return (crops >= 15 and animals >= 4) or day >= MIDGAME_FORCED_DAY


def shop_demand(obs, product):
    """Known daily town drain: center demand plus active shop instances."""
    shops = obs.get("town", {}).get("unlocked_shops", [])
    return 1 + 6 * sum(SHOP_DEMAND.get(shop, {}).get(product, 0) for shop in shops)


def future_shop_demand_range(obs, product, horizon_days):
    """Expected and high extra drain from shops not unlocked yet."""
    if horizon_days <= 0:
        return {"expected": 0, "high": 0, "unlocks": 0}
    weights = [demand.get(product, 0) for demand in SHOP_DEMAND.values()]
    expected_rate = 6 * sum(weights) / len(weights)
    high_rate = 6 * max(weights)
    active_new = 0
    expected = high = unlocks = 0.0
    day = obs.get("day", 0)
    existing = len(obs.get("town", {}).get("unlocked_shops", []))
    for offset in range(1, horizon_days + 1):
        if (day + offset) % 3 == 0 and existing + unlocks < 8:
            active_new += 1
            unlocks += 1
        expected += active_new * expected_rate
        high += active_new * high_rate
    return {"expected": int(round(expected)), "high": int(round(high)),
            "unlocks": int(unlocks)}


def _shape(name, value, throughput):
    value = max(0.0, value)
    if name == "linear":
        return value
    if name == "sq":
        return value * value
    if name == "sqrt":
        return math.sqrt(value)
    if name == "log":
        return math.log1p(value)
    if name == "log10":
        return math.log10(1.0 + value)
    if name == "hinge":
        unit = value / throughput
        return unit + 8 * max(0.0, unit - 1.0) ** 2
    return value


def market_parameters(obs, item):
    base, anchor, throughput, below_shape, below_target, above_shape, above_target = MARKET_PARAMS[item]
    override = obs.get("market", {}).get("params", {}).get(item, {})
    return {
        "base": override.get("base", base), "I0": override.get("I0", anchor),
        "T": override.get("T", throughput),
        "below_func": override.get("below_func", below_shape),
        "below_target": override.get("below_target", below_target),
        "above_func": override.get("above_func", above_shape),
        "above_target": override.get("above_target", above_target),
    }


def forecast_price(obs, item, inventory):
    """Exact engine price curve, including scenario-specific market parameters."""
    params = market_parameters(obs, item)
    base, anchor, throughput = params["base"], params["I0"], params["T"]
    below = inventory < anchor
    name = params["below_func"] if below else params["above_func"]
    target = params["below_target"] if below else params["above_target"]
    amplitude = target * base / _shape(name, throughput, throughput)
    change = amplitude * _shape(name, abs(inventory - anchor), throughput)
    return max(1, int(round(base + change if below else base - change)))


def scheduled_supply_for_player(obs, player, item, horizon_days):
    """Visible output that one farm could produce before a sale checkpoint."""
    if horizon_days <= 0:
        return 0
    day = obs.get("day", 0)
    total = 0
    farms = obs.get("farms", [])
    if player >= len(farms):
        return 0
    for row in farms[player]["tiles"]:
        for tile_at in row:
            if not isinstance(tile_at, dict):
                continue
            if tile_at.get("kind") == "PLANT" and tile_at.get("crop") == item:
                first, max_day, max_yield, _, ongoing, interval = CROP_DATA[item]
                age = day - tile_at.get("planted_day", day)
                if ongoing:
                    first_offset = max(0, first - age)
                    if first_offset <= horizon_days:
                        total += min(max_yield, 1 + (horizon_days - first_offset) // interval)
                elif age + horizon_days >= min(max_day, 10 if item == "MELON" else max_day):
                    total += max(tile_at.get("yield_units", 1), CROP_ECONOMICS[item][2])
            elif tile_at.get("animal") and ANIMAL_DATA[tile_at["animal"]][1] == item:
                first, interval = ANIMAL_TIMING[tile_at["animal"]]
                age = day - tile_at.get("placed_day", day)
                first_offset = max(0, first - age)
                if first_offset <= horizon_days:
                    total += 1 + (horizon_days - first_offset) // interval
    return total


def scheduled_supply(obs, item, horizon_days):
    """Conservative own output expected before a candidate's sale checkpoint."""
    return scheduled_supply_for_player(obs, obs["player"], item, horizon_days)


def opponent_supply_range(obs, item, horizon_days):
    """Low/base/high public opponent output; private shed stock is never inferred."""
    opponent = 1 - obs.get("player", 0)
    visible = scheduled_supply_for_player(obs, opponent, item, horizon_days)
    return {"low": 0, "base": int(round(visible * OPPONENT_SUPPLY_WEIGHT)),
            "high": visible}


def projected_inventory(obs, item, horizon_days=0, added_supply=0):
    inventory = obs.get("market", {}).get("inventory", {})
    if item not in inventory:
        return None
    future_demand = (future_shop_demand_range(obs, item, horizon_days)["expected"]
                     if ENABLE_V06_SHOP_FORECAST else 0)
    opponent_supply = (opponent_supply_range(obs, item, horizon_days)["base"]
                       if ENABLE_V06_OPPONENT_PENALTY else 0)
    return (inventory[item] - shop_demand(obs, item) * horizon_days - future_demand
            + scheduled_supply(obs, item, horizon_days) + opponent_supply + added_supply)


def batch_sale_revenue(obs, item, amount, horizon_days=0, added_supply=0):
    """Revenue from a batch sold one unit at a time after known demand/output."""
    if amount <= 0:
        return 0
    inventory = projected_inventory(obs, item, horizon_days, added_supply)
    if inventory is None:
        return amount * obs.get("market", {}).get("prices", {}).get(item, MARKET_PARAMS[item][0])
    revenue = 0
    for _ in range(amount):
        price = forecast_price(obs, item, inventory)
        revenue += price
        if price > 1:  # Engine does not add a $1 sale to market inventory.
            inventory += 1
    return revenue


def crop_realizable_terms(obs, crop):
    """Yield and sale horizon that still fit before the final executable turn."""
    first_day, max_day, max_yield, unfertilized, ongoing, interval = CROP_DATA[crop]
    runway = max(0, (turns_remaining(obs) - 6) // TURNS_PER_DAY)
    if liquidation_stage(obs) or runway < first_day:
        return {"feasible": False, "yield": 0, "sale_day": first_day,
                "runway": runway}
    if ongoing:
        expected_yield = min(max_yield, 1 + (runway - first_day) // interval)
        sale_day = first_day + (expected_yield - 1) * interval
    else:
        sale_day = min(runway, max_day)
        window_start = (max_day + 1) // 2
        expected_yield = min(unfertilized, 1 + max(0, sale_day - window_start + 1))
    return {"feasible": expected_yield > 0, "yield": expected_yield,
            "sale_day": sale_day, "runway": runway}


def active_crop_terms(obs, crop):
    _, _, expected_yield, occupied_days = CROP_ECONOMICS[crop]
    feasible = obs.get("day", 0) <= PLANT_CUTOFF[crop]
    if not feasible and ENABLE_V06_FULL_CHAIN_VALUATION:
        return crop_realizable_terms(obs, crop)
    return {"feasible": feasible, "yield": expected_yield if feasible else 0,
            "sale_day": occupied_days, "runway": turns_remaining(obs) // TURNS_PER_DAY}


def crop_opportunity(obs, crop, added_supply=0, regime=None):
    seed_cost = CROP_ECONOMICS[crop][0]
    terms = active_crop_terms(obs, crop)
    expected_yield, occupied_days = terms["yield"], terms["sale_day"]
    if not terms["feasible"]:
        return {"crop": crop, "net": -INFINITY, "daily": -INFINITY,
                "sale_day": occupied_days, "revenue": 0, "yield": 0,
                "feasible": False}
    revenue = batch_sale_revenue(obs, crop, expected_yield, occupied_days, added_supply)
    label = regime.get("label") if isinstance(regime, dict) else regime
    label = label if ENABLE_V06_REGIME_VALUATION else None
    if label == "GLUT":
        revenue = int(revenue * 0.90)
    elif label == "TIGHTENING":
        revenue = int(revenue * 1.08)
    elif label == "SCARCITY_SHOCK":
        revenue = int(revenue * 1.12)
    action_cost = ACTION_VALUE * (occupied_days + 2)
    net = revenue - seed_cost - action_cost
    return {"crop": crop, "net": net, "daily": net / occupied_days,
            "sale_day": occupied_days, "revenue": revenue,
            "yield": expected_yield, "feasible": True}


def market_crop_scores(obs, price_movement=None, regimes=None):
    """V0.5 first-cell marginal daily values; retained as the public score API."""
    regimes = regimes or {}
    scores = {crop: crop_opportunity(obs, crop, regime=regimes.get(crop))["daily"]
              for crop in CROP_ECONOMICS}
    return {crop: score for crop, score in scores.items() if score > -INFINITY}


def update_market_history(state, obs):
    """Keep four daily public checkpoints; replace repeated observations per day."""
    history = state.setdefault("market_history", {})
    day = obs.get("day", 0)
    prices = obs.get("market", {}).get("prices", {})
    inventory = obs.get("market", {}).get("inventory", {})
    for item, params in MARKET_PARAMS.items():
        row = {"day": day, "price": prices.get(item, params[0]),
               "inventory": inventory.get(item, params[1])}
        rows = history.setdefault(item, [])
        if rows and rows[-1]["day"] == day:
            rows[-1] = row
        else:
            rows.append(row)
            del rows[:-4]
    return history


def market_regimes(obs, history=None):
    """Classify public market state without converting labels directly to actions."""
    history = history or {}
    result = {}
    for item, params in MARKET_PARAMS.items():
        base, anchor, throughput = params[:3]
        price = obs.get("market", {}).get("prices", {}).get(item, base)
        inventory = obs.get("market", {}).get("inventory", {}).get(item, anchor)
        rows = history.get(item, [])
        prior = rows[-2] if len(rows) >= 2 else {"price": price, "inventory": inventory}
        price_change = price - prior["price"]
        inventory_change = inventory - prior["inventory"]
        if item in CROP_DATA and not crop_realizable_terms(obs, item)["feasible"]:
            label = "TOO_LATE"
        elif price <= max(1, int(base * 0.25)) or inventory >= anchor + throughput // 2:
            label = "GLUT"
        elif (price >= base * 1.5 and price_change > 0) or inventory <= anchor - throughput:
            label = "SCARCITY_SHOCK"
        elif price_change >= max(2, int(base * 0.08)) and inventory_change < 0:
            label = "TIGHTENING"
        else:
            label = "NORMAL"
        result[item] = {"label": label, "price": price, "inventory": inventory,
                        "price_change": price_change,
                        "inventory_change": inventory_change}
    return result


def animal_opportunity(obs, animal, extra_units=0):
    """Conservative remaining-midgame value of one additional housed animal."""
    day = obs.get("day", 0)
    remaining = max(0, MIDGAME_END_DAY - day)
    cost, product, _ = ANIMAL_DATA[animal]
    first, interval = ANIMAL_TIMING[animal]
    outputs = 0 if remaining < first else 1 + (remaining - first) // interval
    sale_day = min(remaining, first + max(0, outputs - 1) * interval)
    product_revenue = batch_sale_revenue(obs, product, outputs, sale_day, extra_units)
    fertilizer_units = max(0, remaining - 1)
    # Collection competes with survival and crop work; credit only a conservative
    # fraction until telemetry can calibrate realized collection.
    fertilizer_revenue = int(0.35 * batch_sale_revenue(
        obs, "FERTILIZER", fertilizer_units, max(1, remaining // 2), extra_units
    ))
    wheat_price = obs.get("market", {}).get("prices", {}).get("WHEAT", 25)
    feed_cost = remaining * wheat_price
    work = 2 * remaining + outputs + first  # feed, collect, harvest, setup/travel allowance
    net = product_revenue + fertilizer_revenue - cost - feed_cost - ACTION_VALUE * work
    return {"animal": animal, "product": product, "net": net,
            "product_revenue": product_revenue, "fertilizer_revenue": fertilizer_revenue,
            "outputs": outputs}


def observed_animal_targets(obs):
    targets = dict(animal_layout())
    for y, row in enumerate(obs["farms"][obs["player"]]["tiles"]):
        for x, tile_at in enumerate(row):
            if isinstance(tile_at, dict) and tile_at.get("animal"):
                targets[(x, y)] = tile_at["animal"]
    return targets


def extend_animal_targets(obs, previous):
    """Fund a bounded batch of recurring capacity without copying a fixed route."""
    me = obs["farms"][obs["player"]]
    unlocked = me.get("unlocked_quadrants", ["NW"])
    per_field = MAX_ANIMALS_PER_FIELD if ENABLE_V06_JOINT_CAPACITY else 1
    limit = len(animal_layout()) + per_field * max(0, len(unlocked) - 1)
    targets = observed_animal_targets(obs) | dict(previous or {})
    if len(targets) >= limit or obs.get("day", 0) >= 17:
        return targets, []
    reserve = 600
    budget = max(0, me.get("money", 0) - reserve)
    used = set(targets)
    positions = []
    reserved = set(animal_reserve_cells(obs))
    for pos in available_flexible_cells(obs):
        if pos in used or not any(pos in expansion_cells(q) for q in unlocked if q != "NW"):
            continue
        tile_at = me["tiles"][pos[1]][pos[0]]
        replaceable = (ENABLE_V06_JOINT_CAPACITY
                       and isinstance(tile_at, dict) and tile_at.get("kind") == "PLANT"
                       and tile_at.get("crop") in CROP_DATA
                       and not CROP_DATA[tile_at["crop"]][4]
                       and obs.get("day", 0) - tile_at.get("planted_day", obs.get("day", 0))
                       >= CROP_DATA[tile_at["crop"]][0])
        empty_capacity = tile_at is None and (
            not ENABLE_V06_JOINT_CAPACITY or pos in reserved
        )
        if empty_capacity or replaceable:
            positions.append(pos)
    choices, added = [], {product: 0 for _, product, _ in ANIMAL_DATA.values()}
    additions_allowed = limit - len(targets) if ENABLE_V06_JOINT_CAPACITY else 1
    while positions and len(targets) < limit and len(choices) < additions_allowed:
        options = [(animal_opportunity(obs, animal, added[ANIMAL_DATA[animal][1]]), animal)
                   for animal in ANIMAL_DATA]
        opportunity, animal = max(options, key=lambda item: (item[0]["net"], item[1]))
        cost, product, _ = ANIMAL_DATA[animal]
        if opportunity["net"] <= 0 or budget < cost:
            break
        position = min(positions, key=lambda pos: (nearest_shed_distance(pos), pos[1], pos[0]))
        targets[position] = animal
        choices.append({"position": position, **opportunity})
        positions.remove(position)
        budget -= cost
        added[product] += opportunity["outputs"]
    return targets, choices


def allocate_flexible_cells(obs, cells, previous=None, regimes=None):
    """Greedily allocate marginal units, updating own projected market impact."""
    previous = previous or {}
    targets, planned, planned_cells, decisions = {}, {crop: 0 for crop in CROP_ECONOMICS}, {
        crop: 0 for crop in CROP_ECONOMICS
    }, []
    crop_limit = (max(4, math.ceil(len(cells) * MAX_CROP_SHARE))
                  if ENABLE_V06_CROP_CAP else INFINITY)
    for position in cells:
        options = {crop: crop_opportunity(obs, crop, planned[crop], (regimes or {}).get(crop))
                   for crop in CROP_ECONOMICS}
        for crop in options:
            regime = (regimes or {}).get(crop, {}).get("label")
            first_yield = CROP_DATA[crop][0]
            late_shock = (regime in {"TIGHTENING", "SCARCITY_SHOCK"}
                          and obs.get("day", 0) >= LIQUIDATE_DAY - max(4, first_yield // 2))
            limit = (min(crop_limit, MAX_LATE_SHOCK_CELLS)
                     if late_shock and ENABLE_V06_REGIME_VALUATION else crop_limit)
            if planned_cells[crop] >= limit:
                options[crop] = {**options[crop], "net": -INFINITY, "daily": -INFINITY}
        best = max(options, key=lambda crop: (options[crop]["daily"], crop))
        choice = best if options[best]["net"] >= MIN_CELL_MARGIN else None
        old = previous.get(position)
        if old in options and options[old]["net"] >= MIN_CELL_MARGIN:
            improvement = options[best]["daily"] - options[old]["daily"]
            if improvement <= max(1, abs(options[old]["daily"]) * SWITCH_MARGIN):
                choice = old
        if choice:
            targets[position] = choice
            planned[choice] += CROP_ECONOMICS[choice][2]
            planned_cells[choice] += 1
        decisions.append({"position": position, "choice": choice or "HOLD_FLEXIBLE",
                          "net": round(options[choice]["net"], 2) if choice else 0})
    return targets, decisions


def marginal_crop_batch_value(obs, cell_count, regimes=None):
    planned = {crop: 0 for crop in CROP_ECONOMICS}
    planned_cells = {crop: 0 for crop in CROP_ECONOMICS}
    crop_limit = (max(4, math.ceil(cell_count * MAX_CROP_SHARE))
                  if ENABLE_V06_CROP_CAP else INFINITY)
    value = 0
    for _ in range(cell_count):
        options = {crop: crop_opportunity(obs, crop, planned[crop], (regimes or {}).get(crop))
                   for crop in CROP_ECONOMICS}
        for crop in options:
            if planned_cells[crop] >= crop_limit:
                options[crop] = {**options[crop], "net": -INFINITY, "daily": -INFINITY}
        choice = max(options, key=lambda crop: options[crop]["net"])
        if options[choice]["net"] < MIN_CELL_MARGIN:
            break
        value += options[choice]["net"]
        planned[choice] += CROP_ECONOMICS[choice][2]
        planned_cells[choice] += 1
    return value


def farm_health_snapshot(obs, desired_cells=None, animal_targets=None, reserved_cells=None):
    """Account for every unlocked cell so idle and blocked capacity stays visible."""
    me = obs["farms"][obs["player"]]
    desired_cells = desired_cells or {}
    animal_targets = animal_targets or {}
    reserved_cells = set(reserved_cells or ())
    for quadrant in me.get("unlocked_quadrants", ["NW"]):
        if quadrant != "NW":
            reserved_cells.update(set(expansion_cells(quadrant))
                                  - set(serviceable_expansion_cells(quadrant)))
    statuses = {}
    for quadrant in me.get("unlocked_quadrants", ["NW"]):
        cells = ((x, y) for y in range(5) for x in range(5)) if quadrant == "NW" else expansion_cells(quadrant)
        for pos in cells:
            tile_at = me["tiles"][pos[1]][pos[0]]
            if isinstance(tile_at, dict) and (tile_at.get("kind") == "PLANT" or tile_at.get("animal")):
                status = "PRODUCTIVE"
            elif isinstance(tile_at, dict) and tile_at.get("kind") == "WEED":
                status = "BLOCKED"
            elif pos in desired_cells or pos in animal_targets or (
                    isinstance(tile_at, dict) and tile_at.get("kind") in {"PASTURE", "COOP"}):
                status = "TRANSITION"
            elif pos in SHED_ACCESS or pos in reserved_cells:
                status = "RESERVED"
            else:
                status = "FLEXIBLE"
            statuses[pos] = status
    counts = {name: sum(status == name for status in statuses.values())
              for name in ("PRODUCTIVE", "TRANSITION", "BLOCKED", "FLEXIBLE", "RESERVED")}
    serviceable = max(1, len(statuses) - counts["RESERVED"])
    return {"counts": counts, "productive_ratio": round(counts["PRODUCTIVE"] / serviceable, 3),
            "planned_ratio": round((counts["PRODUCTIVE"] + counts["TRANSITION"]) / serviceable, 3),
            "blocked_cells": [pos for pos, status in statuses.items() if status == "BLOCKED"],
            "unexplained_flexible_cells": [pos for pos, status in statuses.items() if status == "FLEXIBLE"]}


def apply_strategy_override(snapshot, obs):
    """Validated strategic seam; overrides cannot emit actions or bypass safety."""
    override = STRATEGY_OVERRIDE(snapshot, obs) if callable(STRATEGY_OVERRIDE) else STRATEGY_OVERRIDE
    if not isinstance(override, dict):
        return snapshot
    result = dict(snapshot)
    if override.get("posture") in {"STABILIZE", "PIVOT", "SCALE", "DEFEND"}:
        result["posture"] = override["posture"]
    if isinstance(override.get("desired_cells"), dict):
        valid = {tuple(pos): crop for pos, crop in override["desired_cells"].items()
                 if isinstance(pos, (tuple, list)) and len(pos) == 2 and crop in CROP_DATA}
        result["desired_cells"] = valid
    if isinstance(override.get("animal_targets"), dict):
        valid = {tuple(pos): animal for pos, animal in override["animal_targets"].items()
                 if isinstance(pos, (tuple, list)) and len(pos) == 2 and animal in ANIMAL_DATA}
        result["animal_targets"] = valid
    result["override"] = override.get("name", "custom")
    return result


_strategy_context = {}
_strategy_telemetry = {}


def _v06_strategy_snapshot(obs):
    """Return the cached V0.6 capacity/market plan and V0.4 liquidation state."""
    player, step, day = obs["player"], obs.get("step", 0), obs.get("day", 0)
    prices = obs.get("market", {}).get("prices", {})
    inventory = obs.get("market", {}).get("inventory", {})
    shops = tuple(obs.get("town", {}).get("unlocked_shops", []))
    fingerprint = (step, tuple(sorted(prices.items())), tuple(sorted(inventory.items())), shops)
    state = _strategy_context.get(player)
    if state and state.get("fingerprint") == fingerprint:
        return state["snapshot"]
    if state is None or step == 0 or step <= state.get("step", -1):
        state = {"step": -1, "plan_day": -1, "shops": (), "prices": dict(prices),
                 "market_history": {}, "lifecycle": "BOOTSTRAP"}

    history = update_market_history(state, obs)
    regimes = market_regimes(obs, history)

    if state["lifecycle"] == "BOOTSTRAP" and opening_complete(obs):
        state["lifecycle"] = "MIDGAME"
    entered_liquidation = state["lifecycle"] == "MIDGAME" and day >= LIQUIDATE_DAY
    if entered_liquidation:
        state["lifecycle"] = "LIQUIDATE"
    replan = day <= MIDGAME_END_DAY and (state["plan_day"] != day or state["shops"] != shops)
    animal_choices = []
    allocation_decisions = state.get("allocation_decisions", [])
    if state["lifecycle"] == "MIDGAME" and replan:
        movement = {crop: prices.get(crop, base) - state["prices"].get(crop, prices.get(crop, base))
                    for crop, (_, base, _, _) in CROP_ECONOMICS.items()}
        valuation_regimes = regimes if ENABLE_V06_REGIME_VALUATION else None
        scores = market_crop_scores(obs, movement, valuation_regimes)
        animals, animal_choices = extend_animal_targets(obs, state.get("animal_targets"))
        reserved_animals = set(animal_reserve_cells(obs)) - set(animals)
        flexible = [pos for pos in available_flexible_cells(obs)
                    if pos not in animals and pos not in reserved_animals]
        targets, allocation_decisions = allocate_flexible_cells(
            obs, flexible, state.get("targets"), valuation_regimes
        )
        selected = sorted(set(targets.values()), key=lambda crop: (-scores.get(crop, -INFINITY), crop))
        state.update(plan_day=day, shops=shops, prices=dict(prices), targets=targets,
                     movement=movement, scores=scores, selected=selected,
                     animal_targets=animals, animal_choices=animal_choices,
                     allocation_decisions=allocation_decisions)

    targets = state.get("targets", {pos: "MELON" for pos in base_flexible_cells()})
    animals = state.get("animal_targets", observed_animal_targets(obs))
    animal_reserves = tuple(pos for pos in animal_reserve_cells(obs) if pos not in animals)
    desired = ({pos: "WHEAT" for pos in base_feed_cells() if pos not in animals}
               | {pos: crop for pos, crop in targets.items() if pos not in animals})
    health = farm_health_snapshot(obs, desired, animals, animal_reserves)
    selected = state.get("selected", sorted(set(targets.values())))
    transition = "HANDOFF_TO_V0.4" if entered_liquidation else None
    stage = liquidation_stage(obs)
    snapshot = {
        "lifecycle": state["lifecycle"],
        "posture": stage or ("PIVOT" if state["lifecycle"] == "MIDGAME" and replan else "STABILIZE"),
        "transition": transition,
        "trigger": "V0.4 terminal deadline" if stage else (
            "day/shop checkpoint" if replan else "continue current commitment"),
        "shops": list(shops),
        "market_regimes": regimes,
        "price_movement": state.get("movement", {}),
        "crop_scores": {crop: round(score, 2) for crop, score in state.get("scores", {}).items()},
        "selected_crops": list(selected),
        "desired_cells": desired,
        "animal_targets": animals,
        "animal_reserve_cells": animal_reserves,
        "animal_choice": (state.get("animal_choices") or [None])[0],
        "animal_choices": state.get("animal_choices", []),
        "allocation_decisions": allocation_decisions,
        "held_flexible_cells": sum(d["choice"] == "HOLD_FLEXIBLE" for d in allocation_decisions),
        "farm_health": health,
        "future_shop_ranges": {item: future_shop_demand_range(obs, item, 6)
                               for item in CROP_ECONOMICS},
        "opponent_supply_ranges": {item: opponent_supply_range(obs, item, 6)
                                   for item in MARKET_PARAMS},
        "v06_phases": {
            "A_farm_health_telemetry": "ACTIVE",
            "A_weed_recovery": "ACTIVE" if ENABLE_V06_WEED_RECOVERY else "SHADOW",
            "A_fill_gate": "ACTIVE" if ENABLE_V06_FILL_GATE else "SHADOW",
            "A_health_staffing": "ACTIVE" if ENABLE_V06_HEALTH_STAFFING else "SHADOW",
            "B_joint_capacity": "ACTIVE" if ENABLE_V06_JOINT_CAPACITY else "SHADOW",
            "B_crop_cap": "ACTIVE" if ENABLE_V06_CROP_CAP else "SHADOW",
            "C_full_chain": "ACTIVE" if ENABLE_V06_FULL_CHAIN_VALUATION else "SHADOW",
            "C_regime_valuation": "ACTIVE" if ENABLE_V06_REGIME_VALUATION else "SHADOW",
            "D_shop_forecast": "ACTIVE" if ENABLE_V06_SHOP_FORECAST else "SHADOW",
            "D_opponent_penalty": "ACTIVE" if ENABLE_V06_OPPONENT_PENALTY else "SHADOW",
        },
        "turns_remaining": turns_remaining(obs),
        "land_policy": LAND_POLICY,
        "hand_policy": HAND_POLICY,
    }
    snapshot = apply_strategy_override(snapshot, obs)
    snapshot["farm_health"] = farm_health_snapshot(
        obs, snapshot["desired_cells"], snapshot["animal_targets"],
        snapshot.get("animal_reserve_cells")
    )
    state.update(step=step, fingerprint=fingerprint, snapshot=snapshot)
    _strategy_context[player] = state
    _strategy_telemetry[player] = {
        key: value for key, value in snapshot.items()
        if key not in {"desired_cells", "animal_targets", "allocation_decisions"}
    }
    _strategy_telemetry[player]["desired_crop_counts"] = {
        crop: sum(value == crop for value in snapshot["desired_cells"].values())
        for crop in CROP_DATA
    }
    _strategy_telemetry[player]["desired_animal_counts"] = {
        animal: sum(value == animal for value in snapshot["animal_targets"].values())
        for animal in ANIMAL_DATA
    }
    return snapshot


_programme_context = {}


def boundary_crop_plan(obs, desired, previous):
    """Renew vacant cells once daily; keep live crops and feed commitments intact."""
    me = obs["farms"][obs["player"]]
    result = {pos: previous.get(pos, crop) for pos, crop in desired.items()}
    protected = {pos for pos, crop in desired.items() if crop == "WHEAT"}
    for (x, y), crop in list(result.items()):
        tile = me["tiles"][y][x]
        if isinstance(tile, dict) and tile.get("kind") == "PLANT":
            result[(x, y)] = tile.get("crop", crop)
        elif (x, y) in protected:
            result[(x, y)] = "WHEAT"
    if obs.get("day", 0) < 12 or liquidation_stage(obs):
        return result
    counts = {crop: sum(value == crop for value in result.values()) for crop in CROP_DATA}
    cap = max(1, math.ceil(len(result) * MAX_CROP_SHARE))
    added = {crop: 0 for crop in CROP_DATA}
    for pos in sorted(result, key=lambda p: (nearest_shed_distance(p), p)):
        tile = me["tiles"][pos[1]][pos[0]]
        if pos in protected or not (tile is None or isinstance(tile, dict) and tile.get("kind") == "WEED"):
            continue
        current = result[pos]
        values = {crop: crop_opportunity(obs, crop, added[crop]) for crop in CROP_DATA}
        options = [crop for crop in values if values[crop]["feasible"] and values[crop]["net"] >
                   ACTION_VALUE * (2 * nearest_shed_distance(pos) + 2) and
                   (crop == current or counts[crop] < cap)]
        if not options:
            continue
        best = max(options, key=lambda crop: (values[crop]["daily"], crop))
        if (not values[current]["feasible"] or
                values[best]["daily"] > max(0, values[current]["daily"]) * (1 + SWITCH_MARGIN)):
            counts[current] -= 1
            counts[best] += 1
            result[pos] = best
        added[result[pos]] += values[result[pos]]["yield"]
    return result


def strategy_snapshot(obs):
    """V0.7 checkpoint router; local execution may repair but not churn the programme."""
    player, step, day = obs["player"], obs.get("step", 0), obs.get("day", 0)
    state = _programme_context.get(player)
    if state and state.get("observation") is obs and step == state.get("step"):
        return state["snapshot"]
    if state is None or step < state.get("step", -1) or step == 0:
        state = {"step": -1, "programme": "GENERAL", "checkpoint": -1}
    eligible = [checkpoint for checkpoint in PROGRAMME_CHECKPOINT_DAYS if checkpoint <= day]
    checkpoint = eligible[-1] if eligible else -1
    previous = state["programme"]
    if checkpoint > state["checkpoint"]:
        candidate = programme_candidate(obs)
        # A switch is accepted only at a declared checkpoint and before the
        # second expansion is committed. Existing occupied structures remain
        # authoritative through programme_layout reconciliation below.
        if previous == "GENERAL" or candidate == previous:
            state["programme"] = candidate
        state["checkpoint"] = checkpoint
    desired, animals = programme_layout(obs, state["programme"])
    if ENABLE_BOUNDARY_CROPS:
        if state.get("crop_day") != day:
            state["crops"] = boundary_crop_plan(obs, desired, state.get("crops", {}))
            state["crop_day"] = day
        desired = {pos: state.get("crops", {}).get(pos, crop) for pos, crop in desired.items()}
    for y, row in enumerate(obs["farms"][player]["tiles"]):
        for x, tile_at in enumerate(row):
            if isinstance(tile_at, dict) and tile_at.get("animal"):
                animals[(x, y)] = tile_at["animal"]
                desired.pop((x, y), None)
    health = farm_health_snapshot(obs, desired, animals)
    snapshot = {
        "lifecycle": "BOOTSTRAP" if not opening_complete(obs) else
                     ("LIQUIDATE" if liquidation_stage(obs) else "MIDGAME"),
        "posture": liquidation_stage(obs) or "STABILIZE",
        "transition": f"{previous}->{state['programme']}" if previous != state["programme"] else None,
        "trigger": "programme checkpoint" if checkpoint == day else "continue programme",
        "programme": state["programme"],
        "programme_checkpoint": checkpoint,
        "shops": list(obs.get("town", {}).get("unlocked_shops", [])),
        "desired_cells": desired,
        "animal_targets": animals,
        "animal_reserve_cells": (),
        "selected_crops": sorted(set(desired.values())),
        "farm_health": health,
        "turns_remaining": turns_remaining(obs),
        "land_policy": LAND_POLICY,
        "hand_policy": HAND_POLICY,
    }
    snapshot = apply_release(apply_strategy_override(snapshot, obs), obs)
    state.update(step=step, snapshot=snapshot, observation=obs)
    _programme_context[player] = state
    _strategy_telemetry[player] = {
        "programme": snapshot["programme"],
        "checkpoint": checkpoint,
        "transition": snapshot["transition"],
        "desired_crop_counts": {crop: sum(value == crop for value in desired.values())
                                for crop in CROP_DATA},
        "desired_animal_counts": {animal: sum(value == animal for value in animals.values())
                                  for animal in ANIMAL_DATA},
        "farm_health": health,
    }
    return snapshot


# Late-cell conversion: a cell whose target crop can no longer be planted is
# worth more as CARROT than as an idle tile that weeds. Wheat cannot be crashed
# (log sell curve) and still realises well above base when undersupplied.
ENABLE_LATE_CARROT_RAMP = True


def crop_plan(obs):
    grouped = {crop: [] for crop in CROP_ECONOMICS}
    day = obs.get("day", 0)
    for pos, crop in strategy_snapshot(obs)["desired_cells"].items():
        if (ENABLE_LATE_CARROT_RAMP and crop != "CARROT"
                and day > PLANT_CUTOFF.get(crop, 10 ** 6)
                and day <= PLANT_CUTOFF["CARROT"]):
            crop = "CARROT"
        grouped[crop].append(pos)
    return {crop: tuple(cells) for crop, cells in grouped.items() if cells}


def target_crop(pos, obs=None):
    plan = CROP_PLAN if obs is None else crop_plan(obs)
    return next((crop for crop, cells in plan.items() if pos in cells), None)


def animal_plan(obs):
    return strategy_snapshot(obs)["animal_targets"]


def crop_management_posture(obs, pos, tile_at):
    """Choose whether an existing crop still earns its remaining commitment."""
    crop = tile_at.get("crop")
    desired = target_crop(pos, obs)
    if not crop or desired == crop or strategy_snapshot(obs)["lifecycle"] != "MIDGAME":
        return "CONTINUE"
    day = obs.get("day", 0)
    first, max_day, max_yield, _, ongoing, _ = CROP_DATA[crop]
    age = day - tile_at.get("planted_day", day)
    remaining = max(0, max_day - age)
    current_yield = tile_at.get("yield_units", 0)
    continue_units = max(current_yield, max_yield if not ongoing else current_yield + remaining)
    continue_value = batch_sale_revenue(obs, crop, continue_units, remaining) - ACTION_VALUE * (remaining + 1)
    replacement = crop_opportunity(obs, desired) if desired else {"net": 0}
    current_value = batch_sale_revenue(obs, crop, current_yield, 0)
    pivot_value = current_value + max(0, replacement["net"]) - 2 * ACTION_VALUE
    depressed = obs.get("market", {}).get("prices", {}).get(crop, MARKET_PARAMS[crop][0]) <= max(
        1, MARKET_PARAMS[crop][0] // 10
    )
    if current_yield > 0 and age >= first and depressed and pivot_value > continue_value * 1.20:
        return "EARLY_HARVEST"
    if depressed and pivot_value > continue_value * 1.60 and remaining >= 3:
        return "REPLACE"
    return "CONTINUE"


def animal_operating_posture(obs, tile_at):
    """Keep survival reversible while dropping optional work in a product glut."""
    animal = tile_at.get("animal")
    if not animal or liquidation_stage(obs):
        return "ACTIVE"
    _, product, _ = ANIMAL_DATA[animal]
    first, interval = ANIMAL_TIMING[animal]
    projected = forecast_price(
        obs, product,
        obs.get("market", {}).get("inventory", {}).get(product, MARKET_PARAMS[product][1])
        - shop_demand(obs, product) * interval + scheduled_supply(obs, product, interval),
    )
    base = MARKET_PARAMS[product][0]
    current = obs.get("market", {}).get("prices", {}).get(product, base)
    if current <= max(1, base // 10) and projected < base * 0.25:
        return "MAINTAIN_OPTION"
    if tile_at.get("yield_units", 0) > 0 and current < base * 0.20:
        return "HARVEST_ONLY"
    return "ACTIVE"


# Animal release (docs/MICROTAPE_STUDY_2026-09-28.md §3): the top four stop feeding an
# animal whose product sells far below base (median 15% of its game price), let it
# escape, and plant wheat (71%) or carrot (24%) in the pen.
ANIMAL_RELEASE = False  # neutral on 3-6 diagnostic games; off
RELEASE_RATIO = 0.35
RELEASE_DAYS = (8, 24)
RELEASE_PER_DAY = 99   # new releases committed per day (the top four let ~1 sheep and ~1 cow go a game)
_released = {}


def released_cells(obs):
    state = _released.get(obs["player"])
    step = obs.get("step", 0)
    if state is None or step < state["step"]:
        state = _released[obs["player"]] = {"step": step, "cells": {}}
    state["step"] = step
    return state["cells"]


def release_animal(obs, pos, tile_at):
    """Commit to letting a low-value animal escape; True once committed."""
    cells = released_cells(obs)
    if pos in cells:
        return True
    if not ANIMAL_RELEASE or not RELEASE_DAYS[0] <= obs.get("day", 0) <= RELEASE_DAYS[1]:
        return False
    if sum(d == obs.get("day", 0) for d in cells.values()) >= RELEASE_PER_DAY:
        return False
    product = ANIMAL_DATA[tile_at["animal"]][1]
    base = MARKET_PARAMS[product][0]
    if obs.get("market", {}).get("prices", {}).get(product, base) < RELEASE_RATIO * base:
        cells[pos] = obs.get("day", 0)
        return True
    return False


def apply_release(snapshot, obs):
    """An empty released pen becomes a crop cell: wheat, or carrot when it sells 15% higher."""
    cells = released_cells(obs)
    if not cells:
        return snapshot
    tiles = obs["farms"][obs["player"]]["tiles"]
    prices = obs.get("market", {}).get("prices", {})
    crop = "CARROT" if prices.get("CARROT", 0) >= 1.15 * prices.get("WHEAT", 1) else "WHEAT"
    empty = [pos for pos in cells if not (isinstance(tiles[pos[1]][pos[0]], dict)
                                          and tiles[pos[1]][pos[0]].get("animal"))]
    if not empty:
        return snapshot
    result = dict(snapshot)
    result["animal_targets"] = {p: a for p, a in snapshot["animal_targets"].items() if p not in empty}
    result["desired_cells"] = {**snapshot["desired_cells"],
                               **{pos: snapshot["desired_cells"].get(pos, crop) for pos in empty}}
    return result


def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])


def step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x < tx:
        return ["EAST"]
    if x > tx:
        return ["WEST"]
    if y < ty:
        return ["SOUTH"]
    if y > ty:
        return ["NORTH"]
    return ["PASS"]


def workers(obs):
    me = obs["farms"][obs["player"]]
    inventories = obs["private"].get("inventories", [])
    positions = [me["farmer"]] + me.get("hands", [])
    return [{"index": i, "pos": pos, "inventory": inventories[i] if i < len(inventories) else {}}
            for i, pos in enumerate(positions)]


def end_of_day_step(obs):
    return obs.get("step", 0) + (TURNS_PER_DAY - 1 - obs.get("hour", 0))


def watering_pays(tile, crop, day):
    """Does watering this cell today produce anything beyond survival?

    Engine rules: a plant dies only after two consecutive unwatered days, so a
    cell watered yesterday survives today unwatered. Beyond that,
    - a one-time crop gains yield from the WATER action itself, but only inside
      its yield window (`(max_yield_day + 1) // 2 <= age <= max_yield_day`);
    - an ongoing crop accrues its unit on a production day whether or not it was
      watered; watering only decides whether a live fertilizer application is
      counted (`fertilized = was_watered and fertilized_until_day >= day`).
    """
    if crop not in CROP_DATA:
        return True
    first_day, max_day, max_yield, _, ongoing, interval = CROP_DATA[crop]
    age = day - tile.get("planted_day", day)
    if not ongoing:
        return (max_day + 1) // 2 <= age <= max_day and tile.get("yield_units", 0) < max_yield
    if tile.get("fertilized_until_day", -1) < day:
        return False
    # The refresh scores tomorrow's production at the end of today.
    since_first = age + 1 - first_day
    return (since_first >= 0 and interval and since_first % interval == 0
            and since_first // interval + 1 <= max_yield)


def fertilizer_gain(tile, day):
    """Maximum extra units supplied by one new three-day application."""
    crop = tile.get("crop")
    if crop not in CROP_DATA or tile.get("fertilized_until_day", -1) >= day:
        return 0
    first_day, max_day, max_yield, _, ongoing, interval = CROP_DATA[crop]
    planted = tile.get("planted_day", day)
    if ongoing:
        ticks = 0
        for active_day in range(day, day + 3):
            next_age = active_day + 1 - planted
            if next_age < first_day or (next_age - first_day) % interval:
                continue
            ticks += (next_age - first_day) // interval + 1 <= max_yield
        return ticks
    if crop == "MELON":
        return 0
    window_start = (max_day + 1) // 2
    bonus_days = sum(
        window_start <= active_day - planted <= max_day
        and (active_day != day or not tile.get("watered_today"))
        for active_day in range(day, day + 3)
    )
    normal = min(max_yield, tile.get("yield_units", 1) + bonus_days)
    boosted = min(max_yield, tile.get("yield_units", 1) + 2 * bonus_days)
    return max(0, boosted - normal)


def fertilizer_targets(obs, enabled=True):
    if not enabled or obs.get("day", 0) < 3:
        return {}
    prices = obs.get("market", {}).get("prices", {})
    fertilizer_price = prices.get("FERTILIZER", 100)
    me = obs["farms"][obs["player"]]
    targets = {}
    for y, row in enumerate(me["tiles"]):
        for x, tile in enumerate(row):
            if not (isinstance(tile, dict) and tile.get("kind") == "PLANT"):
                continue
            if crop_management_posture(obs, (x, y), tile) != "CONTINUE":
                continue
            gain = fertilizer_gain(tile, obs.get("day", 0))
            crop_price = prices.get(tile.get("crop"), 0)
            if FERT_PRECISE:
                # Only the top agents' bonus moments (docs/YIELD_DRIVERS_2026-09-30.md), uncharged.
                age = obs.get("day", 0) - tile.get("planted_day", obs.get("day", 0))
                if gain and age in FERT_PRECISE_AGES.get(tile.get("crop"), ()) and gain * crop_price > fertilizer_price:
                    targets[(x, y)] = gain * crop_price - fertilizer_price
                continue
            # One product-price unit is the minimum charge for displacing a
            # worker action; small price-only edges lost the controlled A/B.
            action_charge = 0 if (FERT_PROGRAMME or (FERT_CHAIN and FERT_CHAIN_FREE_ACTION)
                                  or obs.get("day", 0) < FERT_FREE_UNTIL_DAY
                                  or obs.get("day", 0) >= FERT_FREE_FROM_DAY) else crop_price
            # Our own bulk sales drive the price down (quote ~$100 early, realised ~$48 on average).
            if gain and gain * crop_price > fertilizer_price * FERT_PRICE_SCALE + action_charge:
                targets[(x, y)] = gain * crop_price - fertilizer_price
    return targets


def task(priority, operation, target, argument=None, owner=None, deadline=INFINITY, reason=""):
    return Task(priority, operation, target, argument, owner, deadline, reason)


def crop_output_wait_turns(tile_at, day):
    crop = tile_at.get("crop")
    first_day, _, _, _, ongoing, interval = CROP_DATA.get(
        crop, (INFINITY, INFINITY, 0, 0, False, 0)
    )
    age = day - tile_at.get("planted_day", day)
    if not ongoing:
        target_age = first_day
    elif age < first_day:
        target_age = first_day
    else:
        target_age = first_day + (math.floor((age - first_day) / interval) + 1) * interval
    return max(0, target_age - age) * TURNS_PER_DAY


def animal_output_wait_turns(tile_at, day):
    first_day, interval = ANIMAL_TIMING.get(tile_at.get("animal"), (INFINITY, 1))
    age = day - tile_at.get("placed_day", day)
    if age < first_day:
        target_age = first_day
    else:
        target_age = first_day + (math.floor((age - first_day) / interval) + 1) * interval
    return max(0, target_age - age) * TURNS_PER_DAY


def terminal_delivery_deadline(obs, pos):
    return last_executable_step(obs) - nearest_shed_distance(pos) - 1


def output_chain_fits(obs, pos, wait_turns=0):
    unit_list = workers(obs)
    approach = min((distance(worker["pos"], pos) for worker in unit_list), default=INFINITY)
    total = wait_turns + approach + 1 + nearest_shed_distance(pos) + 1
    return total <= turns_remaining(obs)


def make_tasks(obs, use_fertilizer=True):
    me, private = obs["farms"][obs["player"]], obs["private"]
    seeds, unit_list = private.get("seeds", {}), workers(obs)
    tasks, day, hour, step = [], obs.get("day", 0), obs.get("hour", 0), obs.get("step", 0)
    daily_deadline = end_of_day_step(obs)
    stage = liquidation_stage(obs)
    fertilize = fertilizer_targets(obs, use_fertilizer and not stage)
    planned_animals = animal_plan(obs)
    recoverable_cells = set(available_flexible_cells(obs)) | set(base_feed_cells()) | set(planned_animals)

    scheduled_fertilizer, unused_targets = {}, set(fertilize)
    for worker in sorted(unit_list, key=lambda item: item["index"]):
        if worker["inventory"].get("FERTILIZER", 0) <= 0 or not unused_targets:
            continue
        pos = min(unused_targets, key=lambda cell: (distance(worker["pos"], cell), -fertilize[cell], cell))
        tile_at = me["tiles"][pos[1]][pos[0]]
        safe = tile_at.get("watered_today") or (
            tile_at.get("consecutive_unwatered", 0) == 0
            and distance(worker["pos"], pos) + 2 <= TURNS_PER_DAY - hour
        )
        if safe:
            scheduled_fertilizer[pos] = worker["index"]
            unused_targets.remove(pos)

    for y, row in enumerate(me["tiles"]):
        for x, tile_at in enumerate(row):
            pos = (x, y)
            if not isinstance(tile_at, dict):
                continue
            if tile_at.get("kind") == "PLANT":
                crop = tile_at.get("crop") or target_crop(pos, obs)
                first_day, max_day, max_yield, _, ongoing, _ = CROP_DATA.get(
                    crop, (INFINITY, INFINITY, INFINITY, INFINITY, False, 0)
                )
                age = day - tile_at.get("planted_day", day)
                ready = age >= first_day and tile_at.get("yield_units", 0) > 0
                posture = crop_management_posture(obs, pos, tile_at)
                if stage and ready and output_chain_fits(obs, pos):
                    tasks.append(task(-2, "HARVEST", pos,
                                      deadline=terminal_delivery_deadline(obs, pos),
                                      reason="realizable terminal crop value"))
                    continue
                if not stage and posture == "REPLACE":
                    tasks.append(task(0, "DIG", pos, reason="replace uneconomic crop commitment"))
                    continue
                if not stage and posture == "EARLY_HARVEST" and ready:
                    tasks.append(task(-1, "HARVEST", pos, deadline=daily_deadline,
                                      reason="release low-value crop cell for better production"))
                    continue
                if pos in scheduled_fertilizer and posture == "CONTINUE":
                    tasks.append(task(1, "FERTILIZE", pos, owner=scheduled_fertilizer[pos],
                                      deadline=daily_deadline - 1, reason="positive marginal fertilizer value"))
                elif SCHEDULE_FERTILIZE and pos in fertilize and posture == "CONTINUE":
                    # Unowned: any worker may take it, loading from the shed if
                    # it is not already carrying fertilizer.
                    tasks.append(task(1, "FERTILIZE", pos,
                                      deadline=daily_deadline - 1, reason="unassigned fertilizer target"))
                future_fits = not stage or output_chain_fits(
                    obs, pos, crop_output_wait_turns(tile_at, day)
                )
                if (posture == "CONTINUE" and not tile_at.get("watered_today")
                        and stage != "FINAL" and future_fits):
                    window_start = (max_day + 1) // 2
                    yield_day = not ongoing and window_start <= age <= max_day
                    survival = tile_at.get("consecutive_unwatered", 0) >= 1
                    pays = yield_day or watering_pays(tile_at, crop, day)
                    # The closing days run on the legacy path, which does not
                    # water: a skipped day there kills the crop (carrots planted
                    # ~day 26 died at age 2, 10.3 a game, before this guard).
                    if (WATER_ONLY_WHEN_IT_PAYS and not survival and not pays and not stage
                            and day < SCHEDULE_END_DAY - 2):
                        pass
                    else:
                        priority = -1 if survival else (0 if pays else 1)
                        tasks.append(task(priority, "WATER", pos, deadline=daily_deadline,
                                          reason="protect realizable terminal output" if stage else (
                                              "survival" if priority < 0 else "yield-day watering")))
                # A finished ongoing crop (strawberry after its last yield) only
                # decays into a weed. Clear it so the cell can be replanted - V46
                # digs strawberries at age 16; we let them rot and block the cell.
                if (ENABLE_CLEAR_FINISHED_ONGOING and ongoing and not stage
                        and age >= CROP_DATA[crop][0] + CROP_DATA[crop][5] * 3
                        and tile_at.get("yield_units", 0) == 0 and day <= PLANT_CUTOFF["CARROT"] - 1):
                    tasks.append(task(0, "DIG", pos, deadline=daily_deadline,
                                      reason="clear finished ongoing crop for replanting"))
                    continue
                if ready and not stage:
                    if ongoing:
                        # Harvest every production event: waiting for max_yield - 1
                        # strands the final yield (it never reaches the threshold).
                        should_harvest = tile_at.get("yield_units", 0) >= 1
                    else:
                        harvest_age = 4 if crop == "WHEAT" else 10 if crop == "MELON" else max_day
                        if WHEAT_EARLY_HARVEST and crop == "WHEAT" and age >= 3 and tile_at.get("yield_units", 0) >= 4:
                            harvest_age = age   # top four: 4+ units by day 3, one day sooner
                        should_harvest = tile_at.get("yield_units", 0) >= max_yield or age >= harvest_age
                        # Waiting for the day's watering before harvesting at maturity
                        # lost ~28 wheat plants a game: when the water never came, the
                        # plant decayed into a weed at age 5. Only wait while the day
                        # is still young enough for the water to realistically land.
                        if (age == harvest_age and not tile_at.get("watered_today")
                                and obs.get("hour", 0) < HARVEST_WAIT_UNTIL_HOUR):
                            should_harvest = False
                    if should_harvest:
                        lifespan = tile_at.get("max_lifespan_step", -1)
                        deadline = lifespan if lifespan >= step else step + 2 * max(0, tile_at.get("yield_units", 1) - 1)
                        if lifespan < 0:
                            deadline = daily_deadline if tile_at.get("yield_units", 0) >= max_yield - 1 else INFINITY
                        tasks.append(task(0, "HARVEST", pos, deadline=deadline,
                                          reason="harvest before yield decay or capacity loss"))
            elif (tile_at.get("kind") == "WEED" and not stage
                  and (pos in recoverable_cells if ENABLE_V06_WEED_RECOVERY
                       else target_crop(pos, obs) or pos in planned_animals)):
                tasks.append(task(0, "DIG", pos, deadline=daily_deadline,
                                  reason="recover blocked productive capacity"))
            elif tile_at.get("kind") in {"PASTURE", "COOP"} and tile_at.get("animal"):
                animal = tile_at["animal"]
                animal_posture = animal_operating_posture(obs, tile_at)
                feed_priority = -1 if tile_at.get("consecutive_unfed", 0) >= 1 else 0
                next_output_fits = output_chain_fits(
                    obs, pos, animal_output_wait_turns(tile_at, day)
                )
                release = not stage and release_animal(obs, pos, tile_at)
                if (not tile_at.get("fed_today") and stage != "FINAL" and (not stage or next_output_fits)
                        and not release):
                    tasks.append(task(feed_priority, "FEED", pos, deadline=daily_deadline,
                                      reason="protect realizable terminal output" if stage else (
                                          "prevent escape" if feed_priority < 0 else "daily animal feed")))
                max_held = ANIMAL_DATA[animal][2]
                if tile_at.get("yield_units", 0) > 0 and (
                        stage or animal_posture in {"ACTIVE", "HARVEST_ONLY"}):
                    priority = -2 if stage else (0 if tile_at["yield_units"] >= max_held - 1 else 1)
                    tasks.append(task(priority, "HARVEST", pos,
                                      deadline=terminal_delivery_deadline(obs, pos) if stage else (
                                          daily_deadline if priority == 0 else INFINITY),
                                      reason="realizable terminal animal output" if stage else "avoid animal output cap"))
                if (animal_posture == "ACTIVE" and not tile_at.get("cared_today")
                        and stage != "FINAL" and (not stage or next_output_fits) and not release):
                    tasks.append(task(1, "CARE", pos, deadline=daily_deadline - 2, reason="bank care bonus"))
                if tile_at.get("fertilizer_available") and stage != "FINAL":
                    tasks.append(task(0, "COLLECT_FERTILIZER", pos, deadline=daily_deadline,
                                      reason="collect sellable terminal fertilizer" if stage else "collect before daily replacement"))
            elif (not stage and tile_at.get("kind") in {"PASTURE", "COOP"}
                  and pos in released_cells(obs)):
                tasks.append(task(0, "DIG", pos, deadline=daily_deadline, reason="convert released pen to crops"))

    layout = planned_animals
    funded_builds = funded_animal_build_targets(obs, layout)
    for pos, animal in layout.items():
        if not stage and pos in funded_builds:
            operation = "BUILD_COOP" if animal == "GOOSE" else "BUILD_PASTURE"
            tasks.append(task(0, operation, pos, reason="funded animal housing transaction"))

    empty_targets = {
        animal: [pos for pos, wanted in layout.items() if wanted == animal
                 and isinstance(me["tiles"][pos[1]][pos[0]], dict)
                 and me["tiles"][pos[1]][pos[0]].get("kind") == ("COOP" if animal == "GOOSE" else "PASTURE")
                 and not me["tiles"][pos[1]][pos[0]].get("animal")]
        for animal in ANIMAL_DATA
    }
    shed = private.get("shed", {})
    drop_allowed = {worker["index"] for worker in unit_list}
    if stage:
        prices = obs.get("market", {}).get("prices", {})
        room = max(0, SHED_CAPACITY - sum(shed.values()))
        drop_allowed = set()
        carriers = sorted(unit_list, key=lambda worker: -sum(
            worker["inventory"].get(item, 0) * prices.get(item, 1) for item in FINAL_PRODUCTS
        ))
        for worker in carriers:
            amount = sum(worker["inventory"].get(item, 0) for item in FINAL_PRODUCTS)
            if amount and amount <= room:
                drop_allowed.add(worker["index"])
                room -= amount

    for worker in unit_list:
        for animal, targets in empty_targets.items():
            if worker["inventory"].get(animal, 0) > 0 and targets:
                target = min(targets, key=lambda cell: distance(worker["pos"], cell))
                tasks.append(task(-1, "PLACE", target, animal, worker["index"], reason="place purchased animal"))

    carried_animals = {animal: sum(w["inventory"].get(animal, 0) for w in unit_list) for animal in ANIMAL_DATA}
    access_index = 0
    for animal, targets in empty_targets.items():
        needed = min(shed.get(animal, 0), max(0, len(targets) - carried_animals[animal]))
        for _ in range(min(needed, len(SHED_ACCESS))):
            access = SHED_ACCESS[access_index % len(SHED_ACCESS)]
            placement_cost = min(distance(access, target) + 1 for target in targets)
            tasks.append(task(-1, "PICKUP", access, animal,
                              deadline=daily_deadline - placement_cost,
                              reason="animal placement prerequisite"))
            access_index += 1

    hungry = 0 if stage == "FINAL" else sum(
        bool(isinstance(me["tiles"][y][x], dict) and me["tiles"][y][x].get("animal")
             and not me["tiles"][y][x].get("fed_today")) for x, y in layout
        if (x, y) not in released_cells(obs)
    )
    carried_wheat = sum(worker["inventory"].get("WHEAT", 0) for worker in unit_list)
    for i in range(min(shed.get("WHEAT", 0), max(0, hungry - carried_wheat), len(SHED_ACCESS))):
        tasks.append(task(-1, "PICKUP", SHED_ACCESS[i], "WHEAT", deadline=daily_deadline - 1,
                          reason="feed prerequisite"))

    carried_fertilizer = sum(worker["inventory"].get("FERTILIZER", 0) for worker in unit_list)
    for i in range(min(shed.get("FERTILIZER", 0), max(0, len(fertilize) - carried_fertilizer),
                       len(SHED_ACCESS))):
        tasks.append(task(1, "PICKUP", SHED_ACCESS[i], "FERTILIZER",
                          reason="profitable fertilizer prerequisite"))

    if hour < 22 and not stage:
        for crop, cells in crop_plan(obs).items():
            if not active_crop_terms(obs, crop)["feasible"] or seeds.get(crop, 0) <= 0:
                continue
            for pos in cells:
                if me["tiles"][pos[1]][pos[0]] is None:
                    tasks.append(task(0, "PLANT", pos, crop, deadline=daily_deadline - 1,
                                      reason="restore desired crop cell"))

    for worker in unit_list:
        keep_fertilizer = bool(fertilize) and worker["inventory"].get("FERTILIZER", 0) > 0
        excluded = set(ANIMAL_DATA) if stage else {*ANIMAL_DATA, "WHEAT"}
        goods = {item: count for item, count in worker["inventory"].items()
                 if item not in excluded
                 and not (item == "FERTILIZER" and keep_fertilizer) and count > 0}
        if goods and worker["index"] in drop_allowed:
            access = min(SHED_ACCESS, key=lambda cell: distance(worker["pos"], cell))
            latest_departure = last_executable_step(obs) - distance(worker["pos"], access) - 1
            if not stage or stage in {"CLOSEOUT", "FINAL"} or step >= latest_departure:
                tasks.append(task(-3 if stage else 0, "DROP", access, owner=worker["index"],
                                  deadline=last_executable_step(obs) if stage else INFINITY,
                                  reason="terminal carrier recall" if stage else "make goods sellable"))
    return tasks


_commitments = {}


def task_key(candidate):
    return candidate.operation, candidate.target, candidate.argument, candidate.owner


def completion_cost(worker, candidate):
    return distance(worker["pos"], candidate.target) + 1


def eligible(worker, candidate):
    inventory = worker["inventory"]
    if candidate.owner is not None and candidate.owner != worker["index"]:
        return False
    if candidate.operation == "FEED" and inventory.get("WHEAT", 0) <= 0:
        return False
    if candidate.operation == "PLACE" and inventory.get(candidate.argument, 0) <= 0:
        return False
    if candidate.operation == "FERTILIZE" and inventory.get("FERTILIZER", 0) <= 0:
        return False
    return True


def task_rank(obs, worker, candidate):
    cost = completion_cost(worker, candidate)
    return (candidate.priority, candidate.deadline, cost,
            candidate.target[1], candidate.target[0], candidate.operation)


def assign_tasks(obs, use_fertilizer=True, unit_list=None, available=None):
    """Preserve feasible commitments, then globally take the best worker-task pairs."""
    unit_list = workers(obs) if unit_list is None else unit_list
    available = make_tasks(obs, use_fertilizer) if available is None else available
    player = obs["player"]
    context = _commitments.get(player, {})
    if context.get("day") != obs.get("day") or context.get("step", -1) >= obs.get("step", 0):
        context = {"day": obs.get("day"), "step": -1, "tasks": {}}
    previous, assignments, used = context.get("tasks", {}), {}, set()
    remaining_actions = TURNS_PER_DAY - obs.get("hour", 0)
    seed_quota = dict(obs["private"].get("seeds", {}))
    pickup_quota = dict(obs["private"].get("shed", {}))

    def take(index, worker):
        candidate = available[index]
        cost = completion_cost(worker, candidate)
        completion_step = obs.get("step", 0) + cost - 1
        if cost > remaining_actions:
            return False
        if candidate.deadline < INFINITY and completion_step > candidate.deadline:
            return False
        if candidate.operation == "PLANT":
            if seed_quota.get(candidate.argument, 0) <= 0:
                return False
            seed_quota[candidate.argument] -= 1
        if candidate.operation == "PICKUP":
            if pickup_quota.get(candidate.argument, 0) <= 0:
                return False
            pickup_quota[candidate.argument] -= 1
        assignments[worker["index"]] = candidate
        used.add(index)
        return True

    for worker in unit_list:
        old_key = previous.get(worker["index"])
        matches = [i for i, candidate in enumerate(available)
                   if i not in used and task_key(candidate) == old_key and eligible(worker, candidate)]
        if not matches:
            continue
        index = min(matches, key=lambda i: task_rank(obs, worker, available[i]))
        old = available[index]
        if not any(eligible(worker, candidate) and candidate.priority < old.priority
                   for i, candidate in enumerate(available) if i not in used):
            take(index, worker)

    pairs = sorted((task_rank(obs, worker, candidate), worker["index"], i)
                   for i, candidate in enumerate(available)
                   for worker in unit_list
                   if worker["index"] not in assignments and eligible(worker, candidate))
    by_index = {worker["index"]: worker for worker in unit_list}
    for _, worker_index, task_index in pairs:
        if worker_index not in assignments and task_index not in used:
            take(task_index, by_index[worker_index])

    _commitments[player] = {"day": obs.get("day"), "step": obs.get("step", 0),
                            "tasks": {i: task_key(t) for i, t in assignments.items()}}
    return assignments


def action_for(worker, candidate):
    if tuple(worker["pos"]) != candidate.target:
        return step_toward(worker["pos"], candidate.target)
    if candidate.operation == "PICKUP" and candidate.quantity != 1:
        return ["PICKUP", candidate.argument, candidate.quantity]
    return [candidate.operation] if candidate.argument is None else [candidate.operation, candidate.argument]


def animal_count(obs, animal=None):
    me, counts = obs["farms"][obs["player"]], {name: 0 for name in ANIMAL_DATA}
    for row in me["tiles"]:
        for tile_at in row:
            if isinstance(tile_at, dict) and tile_at.get("animal") in counts:
                counts[tile_at["animal"]] += 1
    for inventory in [obs["private"].get("shed", {}), *obs["private"].get("inventories", [])]:
        for name in counts:
            counts[name] += inventory.get(name, 0)
    return counts.get(animal, sum(counts.values()))


def quadrant_occupancy(me, quadrant):
    if quadrant == "NW":
        cells = ((x, y) for y in range(5) for x in range(5))
    else:
        cells = serviceable_expansion_cells(quadrant)
    cells = tuple(cells)
    occupied = sum(me["tiles"][y][x] not in (None, "LOCKED") for x, y in cells)
    return occupied / max(1, len(cells))


def land_fill_plan(obs):
    """Concrete first-wave economics for the next quadrant."""
    me = obs["farms"][obs["player"]]
    unlocked = me.get("unlocked_quadrants", ["NW"])
    index = len(unlocked) - 1
    if index >= 2:
        return None
    quadrant = LAND_ORDER[index]
    cells = serviceable_expansion_cells(quadrant)
    regimes = market_regimes(obs) if ENABLE_V06_REGIME_VALUATION else None
    animal_options = sorted(
        (animal_opportunity(obs, animal) for animal in ANIMAL_DATA),
        key=lambda option: (-option["net"], option["animal"]),
    )
    profitable_animals = [option for option in animal_options if option["net"] > 0]
    capacity_limit = MAX_ANIMALS_PER_FIELD if ENABLE_V06_JOINT_CAPACITY else 1
    animal_slots = min(capacity_limit, len(profitable_animals) * 2)
    crop_cells = cells[animal_slots:]
    crops, decisions = allocate_flexible_cells(obs, crop_cells, regimes=regimes)
    crop_value = sum(decision["net"] for decision in decisions
                     if decision["choice"] != "HOLD_FLEXIBLE")
    baseline_crop_value = marginal_crop_batch_value(obs, len(crop_cells), regimes)
    animal_value = sum(profitable_animals[i % len(profitable_animals)]["net"]
                       for i in range(animal_slots)) if profitable_animals else 0
    animal_capital = sum(ANIMAL_DATA[profitable_animals[i % len(profitable_animals)]["animal"]][0]
                         for i in range(animal_slots)) if profitable_animals else 0
    seed_capital = sum(CROP_ECONOMICS[crop][0] for crop in crops.values())
    planned = len(crops) + animal_slots
    required_hands = max(5, min(11, math.ceil((len(crops) + 3 * animal_slots) / 5) - 1))
    return {
        "quadrant": quadrant,
        "cost": LAND_PRICES[index],
        "planned_cells": planned,
        "total_cells": len(cells),
        "fill_ratio": planned / max(1, len(cells)),
        "crop_cells": len(crops),
        "animal_slots": animal_slots,
        "initial_capital": seed_capital + animal_capital,
        "value": max(crop_value, baseline_crop_value) + animal_value,
        "concrete_value": crop_value + animal_value,
        "baseline_value": baseline_crop_value + animal_value,
        "required_hands": required_hands,
    }


def should_buy_land(obs, policy=None):
    """Return whether the next ordered quadrant clears the selected capacity gate."""
    policy = policy or LAND_POLICY
    if policy == "none" or liquidation_stage(obs):
        return False
    me = obs["farms"][obs["player"]]
    unlocked = me.get("unlocked_quadrants", ["NW"])
    index = len(unlocked) - 1
    if policy == "top4":
        # Top-four schedule: a fixed step just after a shop reveal, funded by the
        # same step's sales (market_actions sells before BUY_LAND).
        return (index < len(TOP4_LAND_STEPS) and obs.get("step", 0) >= TOP4_LAND_STEPS[index]
                and top4_land_funds(obs) >= LAND_PRICES[index])
    if index >= 2:  # The fourth field remains an isolated, rejected experiment.
        return False
    day, money, cost = obs.get("day", 0), me.get("money", 0), LAND_PRICES[index]
    if policy == "programme":
        reserve = 500 if index == 0 else 900
        return day >= PROGRAMME_CHECKPOINT_DAYS[index] and money >= cost + reserve
    if policy == "fixed":
        return day >= FIXED_LAND_DAYS[index] and money >= cost + 250
    if policy != "adaptive":
        return False
    earliest = (5, 12)[index]
    source_quadrant = "NW" if index == 0 else unlocked[-1]
    saturation = quadrant_occupancy(me, source_quadrant)
    if not ENABLE_V06_FILL_GATE:
        crop_value = marginal_crop_batch_value(obs, 19)
        animal_value = max(0, max(animal_opportunity(obs, animal)["net"]
                                  for animal in ANIMAL_DATA))
        reserve = 600 if index == 0 else 2000
        hurdle = 1.25 if index == 0 else 1.75
        return (day >= earliest and money >= cost + reserve and saturation >= 0.6
                and crop_value + animal_value >= cost * hurdle)
    fill = land_fill_plan(obs)
    if not fill or fill["fill_ratio"] < LAND_FILL_TARGET:
        return False
    reserve = 500 if index == 0 else 2000
    hurdle = 1.25 if index == 0 else 1.75
    return (day >= earliest and money >= cost + reserve
            and saturation >= 0.6 and fill["value"] >= cost * hurdle)


def terminal_job_count(obs):
    me = obs["farms"][obs["player"]]
    ready = sum(
        isinstance(tile_at, dict) and tile_at.get("yield_units", 0) > 0
        for row in me["tiles"] for tile_at in row
    )
    loaded = sum(any(inv.get(item, 0) > 0 for item in FINAL_PRODUCTS)
                 for inv in obs["private"].get("inventories", []))
    return ready + loaded


def desired_hand_count(obs, policy=None):
    """Daily hand target for a fixed benchmark or a workload-sized policy."""
    policy = policy or HAND_POLICY
    if turns_remaining(obs) <= 0:
        return 0
    day = obs.get("day", 0)
    stage = liquidation_stage(obs)
    if policy == "top4":
        return TOP4_WORKERS[min(day, len(TOP4_WORKERS) - 1)] - 1
    if policy == "programme":
        return PROGRAMME_HANDS.get(day, LATE_HANDS if day >= 12 else 11)
    if policy == "fixed":
        if day < 5:
            return 5
        if day < 10:
            return 9
        if stage == "FINAL":
            return 3
        if stage == "CLOSEOUT":
            return 7
        return 11
    if stage:
        jobs = terminal_job_count(obs)
        ceiling = 5 if stage == "FINAL" else 9 if stage == "CLOSEOUT" else 11
        return min(ceiling, max(0, math.ceil(jobs / 2)))
    me = obs["farms"][obs["player"]]
    snapshot = strategy_snapshot(obs)
    desired = snapshot["desired_cells"]
    plants = sum(isinstance(tile_at, dict) and tile_at.get("kind") == "PLANT"
                 for row in me["tiles"] for tile_at in row)
    animals = max(animal_count(obs), len(animal_plan(obs)))
    if not ENABLE_V06_HEALTH_STAFFING:
        empty = sum(me["tiles"][y][x] is None for x, y in desired)
        setup = sum(me["tiles"][y][x] is None for x, y in animal_plan(obs))
        workload = plants + 3 * animals + 2 * (empty + setup)
        return max(5, min(11, math.ceil(workload / 5) - 1))
    health = snapshot["farm_health"]["counts"]
    workload = plants + 3 * animals + 2 * (health["TRANSITION"] + health["BLOCKED"])
    return max(5, min(11, math.ceil(workload / 5) - 1))


def capacity_orders(obs):
    me = obs["farms"][obs["player"]]
    money = me.get("money", 0)
    orders = []
    fill_plan = land_fill_plan(obs)
    if should_buy_land(obs):
        land_index = len(me.get("unlocked_quadrants", ["NW"])) - 1
        orders.append(["BUY_LAND"])
        money -= LAND_PRICES[land_index]
    missing_hands = max(0, desired_hand_count(obs) - len(me.get("hands", [])))
    a, b = 1, 1
    costs = []
    for _ in range(me.get("hires_today", len(me.get("hands", [])))):
        a, b = b, a + b
    for _ in range(missing_hands):
        costs.append(a)
        a, b = b, a + b
    for cost in costs[:MAX_HIRES_PER_TURN]:
        if money < cost:
            break
        orders.append(["HIRE"])
        money -= cost
    _strategy_telemetry.setdefault(obs["player"], {}).update({
        "unlocked_land": list(me.get("unlocked_quadrants", ["NW"])),
        "land_purchase_requested": ["BUY_LAND"] in orders,
        "land_fill_plan": fill_plan,
        "desired_hands": desired_hand_count(obs),
        "current_hands": len(me.get("hands", [])),
    })
    return orders


def capacity_order_cost(obs, orders):
    """Reserve cash for land and daily hires before optional production buys."""
    me = obs["farms"][obs["player"]]
    land_index = len(me.get("unlocked_quadrants", ["NW"])) - 1
    hires = me.get("hires_today", len(me.get("hands", [])))

    def fibonacci(index):
        a, b = 1, 1
        for _ in range(index):
            a, b = b, a + b
        return a

    cost = 0
    for order in orders:
        if order[0] == "BUY_LAND" and land_index < len(LAND_PRICES):
            cost += LAND_PRICES[land_index]
            land_index += 1
        elif order[0] == "HIRE":
            cost += fibonacci(hires)
            hires += 1
    return cost


def seed_shortages(obs):
    me, seeds = obs["farms"][obs["player"]], obs["private"].get("seeds", {})
    shortages = {}
    for crop, cells in crop_plan(obs).items():
        if not active_crop_terms(obs, crop)["feasible"]:
            continue
        needed = sum(me["tiles"][y][x] is None or (
            isinstance(me["tiles"][y][x], dict) and me["tiles"][y][x].get("kind") == "WEED"
        ) for x, y in cells)
        if EXEC_SEED_AHEAD:
            # A ready one-time crop is about to be harvested; have its replacement seed on hand.
            day = obs.get("day", 0)
            for x, y in cells:
                t = me["tiles"][y][x]
                if (isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") in CROP_DATA
                        and not CROP_DATA[t["crop"]][4] and (t.get("yield_units") or 0) > 0
                        and day - t.get("planted_day", day) >= CROP_DATA[t["crop"]][0]):
                    needed += 1
        shortages[crop] = max(0, needed - seeds.get(crop, 0))
    return shortages


def stored_item_count(obs, item):
    return (obs["private"].get("shed", {}).get(item, 0)
            + sum(inventory.get(item, 0)
                  for inventory in obs["private"].get("inventories", [])))


def available_animal_count(obs, animal):
    """Placed plus purchased animals; do not repeatedly buy unplaced stock."""
    return animal_count(obs, animal) + stored_item_count(obs, animal)


def funded_animal_build_targets(obs, layout=None):
    """Admit housing only when its animal is already owned and not reserved."""
    layout = layout or animal_plan(obs)
    me = obs["farms"][obs["player"]]
    stock = {animal: stored_item_count(obs, animal) for animal in ANIMAL_DATA}

    # Existing empty structures have first claim on owned animals.
    for (x, y), animal in layout.items():
        tile_at = me["tiles"][y][x]
        kind = "COOP" if animal == "GOOSE" else "PASTURE"
        if (isinstance(tile_at, dict) and tile_at.get("kind") == kind
                and not tile_at.get("animal")):
            stock[animal] = max(0, stock[animal] - 1)

    ready = set()
    for pos, animal in layout.items():
        if me["tiles"][pos[1]][pos[0]] is None and stock[animal] > 0:
            ready.add(pos)
            stock[animal] -= 1
    return ready


def batch_buy_cost(obs, item, amount):
    """Conservative current-turn cost for BUY_PRODUCT's unit-by-unit execution."""
    inventory = obs.get("market", {}).get("inventory", {}).get(item)
    if inventory is None:
        return amount * obs.get("market", {}).get("prices", {}).get(item, MARKET_PARAMS[item][0])
    cost = 0
    for _ in range(max(0, amount)):
        cost += forecast_price(obs, item, inventory)
        inventory -= 1
    return cost


def empty_structure_demand(obs, animal):
    kind = "COOP" if animal == "GOOSE" else "PASTURE"
    me = obs["farms"][obs["player"]]
    return sum(
        wanted == animal and isinstance(me["tiles"][y][x], dict)
        and me["tiles"][y][x].get("kind") == kind
        and not me["tiles"][y][x].get("animal")
        for (x, y), wanted in animal_plan(obs).items()
    )


def funded_material_orders(obs, budget):
    """Buy only affordable programme inputs, prioritizing stalled structures and seeds."""
    budget = max(0, int(budget))
    orders = []
    missing_animals = {
        animal: max(0, sum(wanted == animal for wanted in animal_plan(obs).values())
                    - available_animal_count(obs, animal))
        for animal in ANIMAL_DATA
    }

    # Empty structures are sunk productive capacity, so unblock them first.
    for animal in sorted(ANIMAL_DATA, key=lambda name: (-empty_structure_demand(obs, name), name)):
        cost = ANIMAL_DATA[animal][0]
        amount = min(missing_animals[animal], empty_structure_demand(obs, animal), budget // cost)
        if amount:
            orders.append(["BUY_ANIMAL", animal, amount])
            budget -= amount * cost
            missing_animals[animal] -= amount

    shortages = seed_shortages(obs)
    seed_budget = budget if not any(missing_animals.values()) else int(budget * 0.65)
    quantities = {crop: 0 for crop in shortages}
    ranked = sorted(shortages, key=lambda crop: (
        -crop_opportunity(obs, crop)["daily"], CROP_ECONOMICS[crop][0], crop
    ))
    # Round-robin allocation prevents one expensive block from starving every other field.
    while ranked:
        progressed = False
        for crop in ranked:
            cost = CROP_ECONOMICS[crop][0]
            if quantities[crop] < shortages[crop] and seed_budget >= cost:
                quantities[crop] += 1
                seed_budget -= cost
                budget -= cost
                progressed = True
        if not progressed:
            break
        ranked = [crop for crop in ranked if quantities[crop] < shortages[crop]]
    orders.extend(["BUY_SEED", crop, amount] for crop, amount in quantities.items() if amount)

    # Use remaining cash for future slots, one affordable batch per animal type.
    choices = sorted(ANIMAL_DATA, key=lambda animal: (-animal_opportunity(obs, animal)["net"], animal))
    for animal in choices:
        cost = ANIMAL_DATA[animal][0]
        amount = min(missing_animals[animal], budget // cost)
        if amount:
            orders.append(["BUY_ANIMAL", animal, amount])
            budget -= amount * cost
    return orders


def fit_market_orders(obs, orders, limit=10):
    """Keep capacity, a few cash-releasing sales, then funded production inputs."""
    capacity = [order for order in orders if order[0] in {"BUY_LAND", "HIRE"}]
    sales = [order for order in orders if order[0] == "SELL"]
    essential = [order for order in orders if order[:2] == ["BUY_PRODUCT", "WHEAT"]]
    inputs = [order for order in orders
              if order[0] in {"BUY_SEED", "BUY_ANIMAL"}
              or order[:2] == ["BUY_PRODUCT", "FERTILIZER"]]
    sales.sort(key=lambda order: (-order[2] * obs.get("market", {}).get("prices", {}).get(order[1], 1), order[1]))
    room = max(0, limit - len(capacity))
    reserved_inputs = min(4, len(essential) + len(inputs))
    chosen_sales = sales[:max(0, room - reserved_inputs)]
    result = capacity + chosen_sales
    if LAND_POLICY == "top4" and ["BUY_LAND"] in capacity:
        # Orders run in list order: the same step's sales must land before the purchase.
        result = [o for o in capacity if o != ["BUY_LAND"]] + chosen_sales + [["BUY_LAND"]]
    result.extend((essential + inputs)[:max(0, limit - len(result))])
    if len(result) < limit:
        result.extend(sales[len(chosen_sales):limit - len(result) + len(chosen_sales)])
    return result[:limit]


def projected_shed(obs, unit_actions=None):
    shed = dict(obs["private"].get("shed", {}))
    if not unit_actions:
        return shed
    for worker, action in zip(workers(obs), unit_actions):
        if not action or tuple(worker["pos"]) not in SHED_ACCESS:
            continue
        if action[0] == "PICKUP" and len(action) >= 2:
            item = action[1]
            amount = action[2] if len(action) > 2 else 1
            shed[item] = max(0, shed.get(item, 0) - amount)
            continue
        if action[0] != "DROP":
            continue
        room = max(0, SHED_CAPACITY - sum(shed.values()))
        for item, amount in worker["inventory"].items():
            accepted = min(max(0, amount), room)
            if accepted:
                shed[item] = shed.get(item, 0) + accepted
                room -= accepted
    return shed


def terminal_sell_orders(obs, unit_actions=None):
    shed = projected_shed(obs, unit_actions)
    prices = obs.get("market", {}).get("prices", {})
    products = [item for item in FINAL_PRODUCTS if shed.get(item, 0) > 0]
    products.sort(key=lambda item: (-shed[item] * prices.get(item, 1), item))
    return [["SELL", item, shed[item]] for item in products]


def midgame_sell_quantity(obs, item, amount):
    """Hold only a bounded batch when deterministic drain offers a better quote."""
    if amount <= 0:
        return 0
    me = obs["farms"][obs["player"]]
    shed = obs["private"].get("shed", {})
    current = obs.get("market", {}).get("prices", {}).get(item, MARKET_PARAMS[item][0])
    inventory = obs.get("market", {}).get("inventory", {})
    if item not in inventory or me.get("money", 0) < 500 or sum(shed.values()) >= 85:
        return amount
    tomorrow_inventory = inventory[item] - shop_demand(obs, item) + scheduled_supply(obs, item, 1)
    tomorrow = forecast_price(obs, item, tomorrow_inventory)
    hold = min(12, amount) if tomorrow >= current * 1.15 and current < MARKET_PARAMS[item][0] else 0
    return amount - hold


def market_actions(obs, use_fertilizer=True, unit_actions=None):
    step = obs.get("step", 0)
    if OPENER_PROFILE == "V08B" and step < len(V08B_OPENING_MARKET):
        return V08B_OPENING_MARKET[step]
    if step == 0 and OPENER_PROFILE != "TOP4":
        if OPENER_PROFILE == "V07":
            return [["BUY_ANIMAL", "COW", 1], ["BUY_PRODUCT", "WHEAT", 5]]
        if OPENER_PROFILE == "A":
            return [["BUY_PRODUCT", "WHEAT", 13]]
        return [*[['HIRE'] for _ in range(BOOTSTRAP_HANDS)],
                ["BUY_ANIMAL", "SHEEP", 2], ["BUY_PRODUCT", "WHEAT", 5],
                ["BUY_ANIMAL", "GOOSE", 2], ["BUY_ANIMAL", "COW", 1],
                ["BUY_SEED", "MELON", 6]]
    if step == 1 and OPENER_PROFILE != "TOP4":
        if OPENER_PROFILE == "V07":
            return [["SELL", "WHEAT", 1], *[["HIRE"] for _ in range(BOOTSTRAP_HANDS)],
                    ["BUY_ANIMAL", "COW", 1], ["BUY_ANIMAL", "SHEEP", 3],
                    ["BUY_SEED", "MELON", 6]]
        if OPENER_PROFILE == "A":
            return [["SELL", "WHEAT", 9], ["BUY_SEED", "WHEAT", 7], ["BUY_SEED", "MELON", 12],
                    *[["HIRE"] for _ in range(BOOTSTRAP_HANDS)],
                    ["BUY_ANIMAL", "COW", 2], ["BUY_ANIMAL", "SHEEP", 2]]
        return [["BUY_SEED", "WHEAT", 14]]

    market = capacity_orders(obs)
    if liquidation_stage(obs):
        sells = terminal_sell_orders(obs, unit_actions)
        market.extend(sells)
        _strategy_telemetry.setdefault(obs["player"], {}).update({
            "projected_shed": projected_shed(obs, unit_actions),
            "terminal_sell_orders": sells,
        })
        return market[:10]
    shed = (projected_shed(obs, unit_actions) if ENABLE_DROP_SALES
            else obs["private"].get("shed", {}))
    held_products = {}
    for product in ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"):
        quantity = midgame_sell_quantity(obs, product, shed.get(product, 0))
        if ["BUY_LAND"] in market and LAND_POLICY == "top4":
            quantity = shed.get(product, 0)   # land step: sell stock to fund it
        if quantity:
            market.append(["SELL", product, quantity])
        if shed.get(product, 0) > quantity:
            held_products[product] = shed[product] - quantity

    targets = fertilizer_targets(obs, use_fertilizer)
    carried_fertilizer = sum(inv.get("FERTILIZER", 0) for inv in obs["private"].get("inventories", []))
    fertilizer_reserve = max(0, len(targets) - carried_fertilizer)
    if FERT_PROGRAMME and obs.get("day", 0) < SCHEDULE_END_DAY - 2:
        fertilizer_reserve = max(fertilizer_reserve, FERT_RESERVE)   # keep stock for tomorrow's targets
    fertilizer_surplus = max(0, shed.get("FERTILIZER", 0) - fertilizer_reserve)
    if fertilizer_surplus:
        market.append(["SELL", "FERTILIZER", fertilizer_surplus])

    animals = animal_count(obs)
    wheat_carried = sum(inv.get("WHEAT", 0) for inv in obs["private"].get("inventories", []))
    wheat_total = shed.get("WHEAT", 0) + wheat_carried
    wheat_reserve = max(4, animals * 2)
    if shed.get("WHEAT", 0) > wheat_reserve:
        market.append(["SELL", "WHEAT", shed["WHEAT"] - wheat_reserve])
    wheat_shortage = max(0, animals - wheat_total)
    if wheat_shortage:
        market.append(["BUY_PRODUCT", "WHEAT", wheat_shortage])

    money = max(0, obs["farms"][obs["player"]].get("money", 0)
                - capacity_order_cost(obs, market))
    money -= batch_buy_cost(obs, "WHEAT", wheat_shortage)
    market.extend(funded_material_orders(obs, money))
    fertilizer_total = shed.get("FERTILIZER", 0) + carried_fertilizer
    # Collected fertilizer already exceeds what workers can deliver; buying more only churns cash.
    if BUY_FERTILIZER and targets and fertilizer_total < len(targets):
        market.append(["BUY_PRODUCT", "FERTILIZER", len(targets) - fertilizer_total])
    _strategy_telemetry.setdefault(obs["player"], {}).update({
        "held_products": held_products,
        "animal_postures": {
            f"{x},{y}": animal_operating_posture(obs, tile_at)
            for y, row in enumerate(obs["farms"][obs["player"]]["tiles"])
            for x, tile_at in enumerate(row)
            if isinstance(tile_at, dict) and tile_at.get("animal")
        },
    })
    return fit_market_orders(obs, market)


def decide(obs, use_fertilizer=True):
    step = obs.get("step", 0)
    scripted = top4_scripted_action(obs)
    if scripted is not None:
        return scripted
    opening = opener_field()
    if step < len(opening):
        farmer, hands = opening[step]
        return {"farmer": farmer, "hands": hands, "market": market_actions(obs, use_fertilizer)}
    unit_list, assignments = workers(obs), assign_tasks(obs, use_fertilizer)
    actions = [action_for(worker, assignments[worker["index"]])
               if worker["index"] in assignments else ["PASS"] for worker in unit_list]
    _strategy_telemetry.setdefault(obs["player"], {})["assignments"] = [
        {"unit": index, "operation": candidate.operation, "target": candidate.target,
         "deadline": candidate.deadline, "reason": candidate.reason}
        for index, candidate in sorted(assignments.items())
    ]
    return {"farmer": actions[0], "hands": actions[1:],
            "market": market_actions(obs, use_fertilizer, actions)}


def agent_without_fertilizer(obs):
    return decide(obs, False)


"""Daily service compiler, embedded into the frozen V0.6 agent by the builder."""

SCHEDULE_SCOPE = 'all'
SCHEDULE_CARE_WEIGHT = 1.0
SCHEDULE_WATER_WEIGHT = 1.0
SCHEDULE_DEPOSIT_LIMIT = 70
SCHEDULE_START_DAY = 1
SCHEDULE_END_DAY = 28
SCHEDULE_ANIMALS_ONLY = False
SCHEDULE_RECOVERY = True
SCHEDULE_FERTILIZE = True
# V0.10 execution fixes (docs/TOP4_MIDGAME_RESEARCH_2026-09-24.md §7.1): the top
# teams idle 0-4% of worker time from day 6 and replant in one step; v0.9.4 idled
# 28% while other workers held 6-15 queued jobs, and left planned cells empty.
EXEC_BALANCE = False       # rejected: -0.054 ratio vs V46 (more walking, animals under-served)
EXEC_CHAIN_REPLANT = True  # harvesting a one-time crop plants the next crop in the same visit
EXEC_SEED_AHEAD = False    # neutral (-0.007 +/- 0.011); off
# Soft territories (docs/V010_EXECUTOR_STUDY_2026-09-25.md): top-four workers do 68% of their
# work in one home quadrant and every hire stays busy; ours idled hands 7-11.
EXEC_TERRITORY = False      # rejected: -0.012 alone, -0.040 with balancing (n=360 each)
# Never-idle filler (docs/V010_IDLE_STUDY_2026-09-26.md): top-four workers idle 2% of steps,
# ours 15-21%, with the same ~38% spent walking to jobs. An unassigned worker does the most
# useful job within FILLER_RADIUS steps instead of passing; it never walks far for filler.
EXEC_FILLER = False         # prototype stopped: less idle, same cash (docs/V010_IDLE_STUDY_2026-09-26.md)
FILLER_RADIUS = 2


def filler_job(obs, worker, claimed):
    """The most useful nearby job for an idle worker, or None. Stage-free days only."""
    me = obs['farms'][obs['player']]
    x0, y0 = worker['pos']
    inv = worker['inventory']
    best = None
    for y in range(max(0, y0 - FILLER_RADIUS), min(10, y0 + FILLER_RADIUS + 1)):
        for x in range(max(0, x0 - FILLER_RADIUS), min(10, x0 + FILLER_RADIUS + 1)):
            dist = abs(x - x0) + abs(y - y0)
            if dist > FILLER_RADIUS or (x, y) in claimed:
                continue
            t = me['tiles'][y][x]
            if not isinstance(t, dict):
                continue
            op = None
            if t.get('animal'):
                if t.get('fertilizer_available'):
                    op, rank = 'COLLECT_FERTILIZER', 1
                elif (t.get('yield_units') or 0) > 0:
                    op, rank = 'HARVEST', 0
                elif not t.get('fed_today') and inv.get('WHEAT', 0) > 0:
                    op, rank = 'FEED', 0
                elif t.get('fed_today') and not t.get('cared_today'):
                    op, rank = 'CARE', 2
            elif t.get('kind') == 'PLANT':
                crop = t.get('crop')
                ongoing = CROP_DATA.get(crop, (0, 0, 0, 0, False, 0))[4]
                if ongoing and (t.get('yield_units') or 0) > 0:
                    op, rank = 'HARVEST', 0
                elif inv.get('FERTILIZER', 0) > 0 and fertilizer_gain(t, obs['day']) > 0:
                    op, rank = 'FERTILIZE', 2
                elif not t.get('watered_today'):
                    op, rank = 'WATER', 3
            elif t.get('kind') == 'WEED':
                op, rank = 'DIG', 4
            if op and (best is None or (rank, dist) < best[0]):
                best = ((rank, dist), op, (x, y))
    if best is None:
        return None
    return task(2, best[1], best[2], owner=worker['index'], reason='never-idle filler')
TERRITORY_PENALTY = 6        # extra steps charged for a job outside the worker's home quadrant


def worker_homes(obs, units):
    """Stable home quadrant per worker index, quotas proportional to each quadrant's workload."""
    me = obs['farms'][obs['player']]
    quads = [q for q in ('NW', 'NE', 'SW', 'SE') if q in me.get('unlocked_quadrants', ['NW'])]
    load = {q: 1 for q in quads}
    for y, row in enumerate(me['tiles']):
        for x, t in enumerate(row):
            q = ('N' if y < 5 else 'S') + ('W' if x < 5 else 'E')
            if q in load and isinstance(t, dict):
                load[q] += 3 if t.get('animal') else 1
    total, n = sum(load.values()), len(units)
    quota = {q: int(n * load[q] / total) for q in quads}
    for q in sorted(quads, key=lambda q: -(n * load[q] / total - quota[q]))[:n - sum(quota.values())]:
        quota[q] += 1
    order = [q for q in quads for _ in range(quota[q])]
    return {w['index']: order[i] for i, w in enumerate(sorted(units, key=lambda w: w['index']))}
# V0.10 fertilizer programme (top four apply ~88 a game on days 0-19; v0.10 applied 15).
FERT_PROGRAMME = False       # rejected: -0.032 (carried-only) and labour collapse (shed loads)
FERT_RESERVE = 20
WHEAT_EARLY_HARVEST = False  # harvest wheat at age 3 once 4+ units: -0.002, off
WATER_ONLY_WHEN_IT_PAYS = True
# Loading fertilizer from the shed costs a round trip; carriers hold it already.
SCHEDULE_FERTILIZE_LOAD = False
BUY_FERTILIZER = False
# Morning-route prototype (docs/MICROTAPE_STUDY_2026-09-28.md): the top four fertilize with
# what the same hand collected that day (88%), inside a home quarter (69% of days).
FERT_CHAIN = True      # confirmed +0.015 +/- 0.004 held out (docs/V010_MORNING_ROUTE_2026-09-28.md)
FERT_PRICE_SCALE = 1.0       # value applied fertilizer at this share of its quote
FERT_PRECISE = False         # fertilize only at the top agents' bonus ages
FERT_PRECISE_AGES = {"WHEAT": (2, 3), "STRAWBERRY": (9, 13), "CARROT": (2,), "TOMATO": (7, 10)}
FERT_PIGGYBACK = False       # fertilize only on visits the cell needs anyway (water/harvest/plant)
FERT_FREE_FROM_DAY = 99     # no worker-time charge from this day (top agents fertilize late: docs/YIELD_DRIVERS_2026-09-30.md)
FERT_FREE_UNTIL_DAY = 0      # no worker-time charge before this day (labour is idle early)
FERT_CHAIN_FREE_ACTION = False # rejected: -0.019 +/- 0.006 (fertilizes low-value crops)
ROUTE_ZONES = False    # home-quadrant routes: worse on 3 diagnostic games per plan; off
ZONE_PENALTY = 12
_schedule_memory = {}
_legacy_assign_tasks = assign_tasks


# Replay-learned job priorities (Codex, dev/eugene-codex-jobvalues, docs/JOB_VALUES_2026-09-30.md):
# decision trees imitating the top agents' within-cell order (88.5% held out) and next-cell
# choice (51% top-1). Scored per worker from its route endpoint; priority, not coins.
JOB_VALUES_LEARNED = False
import base64 as _jvb, json as _jvj, zlib as _jvz
_JV_MODEL = _jvj.loads(_jvz.decompress(_jvb.b85decode('c-p0yZ;u?e4aUEVU(Xq&L{U_}N|6^v>(mB}6iA%5K#=d=hYx4wX7_Hdm)72!oz*{5Bqi~u-#`58>-R5TfBx{p?;n2p{OS8|zkL4i!(U{xO}4c)eha>3Q+ztg)HYrGm9>h$r<NZb`ON=on|MxsXX}}*QRgV(SGJzpIDQ@lH3)>{Q}zMR&)UCJx7he<CGqL;r$)8=VtaMu<JGSvhr<1J0r8gf<MZS8;ro|gKL7gVAK(6#*8MoPz+c1PljhU*lKj^FyW>yxzo!=an_fz<zn|JismJ-N?bT1s_D1b&Y?mQ=T*uI}*L5t_$tN||tAw*jpVwaZf6w||9=8>gd@6NHzR~Q}VIDo6HR^A5eN_3X+Uq*^Cw<hn|4F6g&(7`kfdKpV`KRxQEk&S?T%dh&1!4j8#Wkhd%4N&dwGd*kao-xMb!&>L<fnB$5sWikzD>l;+6;XJ1EZ6oShtZ=-(qZI<%_fLfPlF<OAK8nU-)yPHpf`oK*idH)n^?qo;vo;$L8!hsY~ch>${J((xl&4#GR0S?ZY1`m}0vdPB@(EdLT~6TiP5Sc;lC^fB%y1$gRe=hJXlc6}hR!X2M+&o0DXC;}si@Z{}OKt;N={r?tZ&#;0$A-sn5g2pb^!2(~12!YCMNI46y*RA@?eAK1>&gC&NSU?G1_bio+VXFxBxwbdcpvjx=0sO&naOSHEgQkvL(#kvz>*FILp#}r$;bBI?9dE^j(r$hev>DzBS**+Q!7P-mHJ|_Y|KK3Rq`4Sc>Q9icb1FHisO&4M*dkyz2QSWT)-OxN2ZZiy&ZKoN>lewDZFfo_*tTGX^9A*xQkyTUM>iMD}gX8qEq-PsMp$ip6+m$aXq-$2KwE}L1(9xBXSZi2g_Z5BSi!KY#s_<AGM=%Mv8)`(;k>mJ+uq=Uu);inBa?ZkF6pkb5eYAytgiS=32hB7!*ks5oEe57KIW1Ii;5CF2Ot9cMEwiecFg9l+-PO}zbE>J+6V`gpZy_3J<{@r_B65O_6YU`>t7E=Yd7_i{lJ1dh+JG}S8&pV8sIOkCI;YjtX$okkR2{~WnIe}fZS05!nzr@PCmk}hccW?7;uI7<<FJSU`gJW?>=e>Qg%EUNG_)zBF$f%{P)3&{2ysRT%_|KnVgE7KqMw`g!5DRgHq=)tYBBdk%fN_>!4)fFP$VYBs1;6UpeuV$F^)BZ#(~F$@dXW)c0;|>l5N<SyKUX+P}rT3G7x)Jl?#aDr1MvqeK8&sPOGJ0Fe~jJ(`j8SwWVwWsVqSY7$P;rs-b}(vC)WX%V<`UX#1>VPNVl5gyoC$A+46(q)R6x)LQLsj6IPsTF<cncK0LDxTFL^bC~eXxW|fcE=<9~WDKpQb2sLkQLV5U8^eb7@gM)#KK%Uo-`{W3=xoUypQk|n1(Rvae=x7ElYlAms$6z4w^bhDGtcd)40O*~t$vODf9}vJAbX8EXjor4G8-#%06Fv6BgtLY%omGKkM|lwIoMqaKDJkq>TISg?$u_zko7E1?{n?jO#3QNFRjm)p4Pg{uS?;VS^s#w@>Z`$^}4RJc>D8cj2DT&Uh;6=Q~oOq9Cdcr?j8p^v(PiO%<89mAc)rza6JdzlgD+f$u7DMedL}&^cY&NdY|bl)AzH<II6PEkQ<h`&2{ziJ6><2S6MIf>+uF-+~5o{(6juugI|Yu)|7^LNkhBhb|>@sx85Mkwa<wpPx5~37>^<E#;yMwUMxGu@pl2!<>7B=_20E={~z_dTg#V(w0Qfll981BlZ3RAe{f1B73B_`&yfrS02)jsanyr2aAaHFQzS~Q1f*n%&IUMNQSALf3pjvq%y~lCNCb=GjN%*|FiuL+5&%9*QbM0W2+LsrLYh2QXf+R%iSdk231vq{+z%?s#zj(#>~%*;$w7&OCoLf(ea59#Bvi9fJE15+aPNPjnU)y!JEBsna-Fw=?SfYtIo+dyj(#>m`Fw#}>Mu}FtyJ~;nvd9RoI?B&yzF+E`W~p*G{$=g5F1Rw-y#GO?{JLa*vNbji4Hz_0^^Bf2Z#s08w4Q`0x~18BN9mMNs5yEm#Ea)0Q`qyw+jpbFM)S6Z|j_h8I2rO90$}ux-;@<FGviMAUX{~Cg+cW<jq3Id7xVOGae>%9sy?u^<`s@5JI-Rqrl|6#NCqyk(xi_;40FqX=!q8L0^LIVej*;#Him9qgs_~+__$^UV|1r&MG_mW*X)%1I}IsT&e2y6_40-oI?BoGwW`L+1?p&{w~4=#{hPiqzcIc<QB~8`)Y*FY*0zP7WsB*(Fj!m7#=&W5gr|oSNLMSio3M1&5Pj*1*NwlqF6*EfuzMe8bQqxB<w9}05CN(b{U;SDM;L@VPXz5cI#1S*#_{e#)(Os9b*=N2#BrV75nrkUcfFHHDhm9>UV-e3zs4_Ksx6v;98Qm46=cNb%GQMq$~OYd-VdfW@J|of$!{UC7?ldP7nJ~o16pieOAdVgzkCeFv&bx*bX=@XaVUDFO2b;9*C)p(ipf;7XbDf8D);C1s%mG=xjn_LKsq;-hw18IBg2r#fw)!&79l<-`I{bHhUf`44F<X=57p$WyM(-nwJMyDnTO;>AVl<;Mg%a2P=Dt_Yp;y!g~)`pv^L|55BZEC)o^)HaWYFotX;Z*jg2g5wTxftVvOt!4Tv?&>tyOqFZ4kc$?~kF4_$NTlO=fNSiw`L*(w@$Y7$LJKfF(BxcEgU+8HNG{?nuXrx<#hdCEr${1~873zrDD27BqUC-F!9YW_nMmP@8iiI_zLKL<s_pZ*sfv2R1Ga;3#8<<-UXN|QOGuW8v>|7YU0g#?Eq7>^yU~8)sKugG>;jL~ca4gitl^_m^{#OafdjVQ*%u$^Jm|S;TX<Npt?pHoYf4o-gaK>Z@E>|Qk*L^XsC|^6mlx<vScgJD2-xtN;R)tk6wE<b|D;Lw_wFTDD?ltdpR$oMLgo{x!oT<JqT&Mk;>^F11l$Up5wHd&-HNmJUBhboYu;gMeBL;(kFS2~m?^baIZ)+`ioD-BcpaR<lHlDhAuxPY9)=GI78?91Z!!}WNYLmMHl-So=E@G;k+k@BUxnHedtEvSGncN1&vFlMdc53Ps114;>vw5vdYlEvF=V*-DFtEOPkpg3KUw3b{Mo09z1v2S%QDr!o+aBLskd0f`Y_+&0e0K;|AYU3hUrWOlHtxI(`Sq`#zTq@N{vm(-2cx`rZ2')))
_JV_OPS = ('WATER', 'FERTILIZE', 'HARVEST', 'COLLECT_FERTILIZER', 'FEED', 'CARE', 'PLANT', 'DIG')
_JV_CROPS = ('WHEAT', 'CARROT', 'TOMATO', 'STRAWBERRY', 'MELON')
_JV_ANIMALS = ('GOOSE', 'COW', 'SHEEP')
_JV_PRODUCT = {'GOOSE': 'EGG', 'COW': 'MILK', 'SHEEP': 'WOOL'}


def _jv_features(obs, op, target, inventory, position):
    x, y = target
    tile = obs['farms'][obs['player']]['tiles'][y][x]
    tile = tile if isinstance(tile, dict) else {}
    crop, animal = tile.get('crop'), tile.get('animal')
    price = obs['market']['prices'].get(crop or _JV_PRODUCT.get(animal, ''), 0)
    return [_JV_OPS.index(op) if op in _JV_OPS else len(_JV_OPS),
            1 if crop else 2 if animal else 0,
            _JV_CROPS.index(crop) + 1 if crop in _JV_CROPS else 0,
            _JV_ANIMALS.index(animal) + 1 if animal in _JV_ANIMALS else 0,
            obs['day'] - tile.get('planted_day', obs['day']) if crop else 0,
            obs['hour'], tile.get('yield_units', 0),
            int(bool(tile.get('watered_today'))), tile.get('consecutive_unwatered', 0),
            tile.get('fertilized_until_day', -1) - obs['day'],
            int(bool(tile.get('fed_today'))), tile.get('consecutive_unfed', 0),
            int(bool(tile.get('cared_today'))), tile.get('fertilizer_available', 0),
            inventory.get('WHEAT', 0), inventory.get('FERTILIZER', 0),
            sum(inventory.values()), price,
            abs(position[0] - x) + abs(position[1] - y), x, y]


def _jv_tree(tree, row):
    node = 0
    while tree['feature'][node] >= 0:
        node = tree['left'][node] if row[tree['feature'][node]] <= tree['threshold'][node] else tree['right'][node]
    return tree['value'][node]


def learned_value(obs, jobs, unit, position, cache):
    total = 0.0
    for job in jobs:
        if job.operation not in _JV_OPS:
            continue
        key = (job.operation, job.target, unit['index'], position)
        value = cache.get(key)
        if value is None:
            row = _jv_features(obs, job.operation, job.target, unit['inventory'], position)
            value = cache[key] = _jv_tree(_JV_MODEL['within'] if row[18] == 0 else _JV_MODEL['next'], row) * _JV_MODEL['scale']
        total += value
    return total


def schedule_value(obs, jobs):
    tiles = obs['farms'][obs['player']]['tiles']
    prices = obs['market']['prices']
    value = 0
    for job in jobs:
        tile = tiles[job.target[1]][job.target[0]]
        if job.operation == 'FEED':
            value += 2000 if tile.get('consecutive_unfed', 0) else 150
        elif job.operation == 'CARE':
            product = ANIMAL_DATA[tile['animal']][1]
            value += prices.get(product, 50) * SCHEDULE_CARE_WEIGHT
        elif job.operation == 'COLLECT_FERTILIZER':
            value += prices.get('FERTILIZER', 100)
        elif job.operation == 'HARVEST':
            product = tile.get('crop') or ANIMAL_DATA[tile['animal']][1]
            value += prices.get(product, 25) * tile.get('yield_units', 0)
        elif job.operation in {'DIG','PLANT'}:
            value += 100
        elif job.operation == 'FERTILIZE':
            value += fertilizer_gain(tile, obs['day']) * prices.get(tile.get('crop'), 25)
        elif job.operation == 'WATER':
            tile = tile if isinstance(tile,dict) else {}
            value += (2000 if tile.get('consecutive_unwatered', 0) else
                      50 * SCHEDULE_WATER_WEIGHT)
    return value


def schedule_route_fits(obs, worker, route, delay=0):
    clock, pos = obs['step'] + delay, tuple(worker['pos'])
    end = min(end_of_day_step(obs), last_executable_step(obs))
    for job in route:
        clock += distance(pos, job.target) + 1
        if clock - 1 > min(end, job.deadline):
            return False
        pos = job.target
    return True


# Zone sweeps (docs/ZONE_SWEEP_2026-10-01.md): each worker owns an angular sector of the farm around
# the central shed, balanced by expected daily work, and serves it inside-out - shed pickups, then
# the animals near the shed (collect, feed, care), then the crops further out (fertilize, water,
# harvest). Tape-like order on our own layout; the planner's job generation is unchanged.
ZONE_SWEEP = False
LATE_HANDS = 11        # programme hands from day 12 (labour-wall test)
ZONE_ONLY = False      # diagnostic: sectors without reordering
SWEEP_ONLY = False     # diagnostic: reordering without sectors
_ZONE_CENTRE = 4.5


def _sweep_key(cell):
    dx, dy = cell[0] - _ZONE_CENTRE, cell[1] - _ZONE_CENTRE
    ring = int(max(abs(dx), abs(dy)))
    angle = math.atan2(dy, dx)
    return (ring, angle if ring % 2 == 0 else -angle)


def zone_owners(obs, units):
    tiles = obs['farms'][obs['player']]['tiles']
    cells = []
    for y, row in enumerate(tiles):
        for x, tile in enumerate(row):
            if tile == 'LOCKED':
                continue
            work = (3.0 if isinstance(tile, dict) and tile.get('animal') else
                    1.5 if isinstance(tile, dict) and tile.get('kind') == 'PLANT' else 0.3)
            cells.append((math.atan2(y - _ZONE_CENTRE, x - _ZONE_CENTRE), (x, y), work))
    cells.sort()
    order = sorted(u['index'] for u in units) or [0]
    total = sum(c[2] for c in cells) or 1.0
    owners, done = {}, 0.0
    for _, cell, work in cells:
        owners[cell] = order[min(len(order) - 1, int(done / total * len(order)))]
        done += work
    return owners


def _sweep_order(obs, worker, route):
    """Reorder a route inside-out; keep the original unless every check still passes."""
    if len(route) < 3:
        return route
    head, rest = route[:1], route[1:]
    pickups = [t for t in rest if t.operation == 'PICKUP']
    chains, cells = {}, []
    for t in rest:
        if t.operation == 'PICKUP':
            continue
        if t.target not in chains:
            chains[t.target] = []
            cells.append(t.target)
        chains[t.target].append(t)
    new = head + pickups + [t for cell in sorted(cells, key=_sweep_key) for t in chains[cell]]
    if new == route or not schedule_route_fits(obs, worker, new):
        return route
    wheat = worker['inventory'].get('WHEAT', 0)
    fert = worker['inventory'].get('FERTILIZER', 0)
    for t in new:
        if t.operation == 'PICKUP':
            wheat += t.quantity if t.argument == 'WHEAT' else 0
            fert += t.quantity if t.argument == 'FERTILIZER' else 0
        elif t.operation == 'FEED':
            wheat -= 1
        elif t.operation == 'COLLECT_FERTILIZER':
            fert += FERT_CHAIN
        elif t.operation == 'FERTILIZE':
            fert -= 1
        if wheat < 0 or fert < 0:
            return route
    return new


def schedule_compile(obs, units, available, existing):
    """Append whole-cell service chains while reserving feed and worker time."""
    step, end = obs['step'], end_of_day_step(obs)
    routes = {w['index']: list(existing.get(w['index'], [])) for w in units}
    for worker in units:
        if not schedule_route_fits(obs, worker, routes[worker['index']]):
            routes[worker['index']] = []
    claimed = {t.target for route in routes.values() for t in route if t.operation != 'PICKUP'}
    groups = {}
    for t in available:
        allowed = ({'WATER','FEED','CARE','COLLECT_FERTILIZER','HARVEST'}
                   | ({'DIG','PLANT'} if SCHEDULE_RECOVERY else set())
                   | ({'FERTILIZE'} if SCHEDULE_FERTILIZE else set()))
        # An owner names the only worker that can do the job (it holds the
        # fertilizer); it is a routing constraint, not a reason to drop the task.
        if (t.operation not in allowed
                or (t.owner is not None and t.operation != 'FERTILIZE')
                or t.target in claimed):
            continue
        tile = obs['farms'][obs['player']]['tiles'][t.target[1]][t.target[0]]
        if t.operation == 'DIG' and (not isinstance(tile,dict) or tile.get('kind') != 'WEED') and not (
                t.target in released_cells(obs) and isinstance(tile, dict) and not tile.get('animal')):
            continue
        if SCHEDULE_ANIMALS_ONLY and not (isinstance(tile,dict) and tile.get('animal')) and t.operation not in {'DIG','PLANT'}:
            continue
        if SCHEDULE_SCOPE == 'nw' and (t.target[0] >= 5 or t.target[1] >= 5):
            continue
        groups.setdefault(t.target, []).append(t)
    if FERT_PIGGYBACK:
        # Fertilize only as an add-on to a visit the cell needs anyway: a dedicated fertilizing
        # trip costs yield-window watering elsewhere (docs/EARLY_LABOUR_2026-09-30.md, F3b).
        for target, jobs in list(groups.items()):
            if not any(t.operation in {'WATER', 'HARVEST', 'PLANT', 'DIG'} for t in jobs):
                jobs = [t for t in jobs if t.operation != 'FERTILIZE']
                if jobs:
                    groups[target] = jobs
                else:
                    del groups[target]
    # Feed before care; water before harvest. Complete each cell in one visit.
    if SCHEDULE_RECOVERY:
        for target,jobs in list(groups.items()):
            operations = {t.operation for t in jobs}
            if 'DIG' in operations:
                crop = target_crop(target,obs)
                if crop is None or not active_crop_terms(obs,crop)['feasible']:
                    del groups[target]
                    continue
                jobs.append(task(0,'PLANT',target,crop,deadline=end-2,reason='funded recovery planting'))
            if {'DIG','PLANT'} & operations:
                jobs.append(task(0,'WATER',target,deadline=end,reason='complete planting chain'))
    if EXEC_CHAIN_REPLANT:
        tiles = obs['farms'][obs['player']]['tiles']
        for target, jobs in groups.items():
            tile = tiles[target[1]][target[0]]
            if not ('HARVEST' in {t.operation for t in jobs} and isinstance(tile, dict)
                    and tile.get('kind') == 'PLANT' and not CROP_DATA.get(tile.get('crop'), (0,) * 6)[4]):
                continue
            crop = target_crop(target, obs)
            if crop is None or not active_crop_terms(obs, crop)['feasible']:
                continue
            # Harvesting a one-time crop empties the cell: replant it on the same visit.
            jobs.append(task(0, 'PLANT', target, crop, deadline=end - 2, reason='chain replant'))
            jobs.append(task(0, 'WATER', target, deadline=end, reason='chain water'))
    order = {'DIG':-3, 'PLANT':-2, 'FEED':0, 'WATER':0, 'FERTILIZE':1, 'CARE':1, 'COLLECT_FERTILIZER':2, 'HARVEST':3}
    chain_order = {'chain replant': 4, 'chain water': 5}
    groups = {p: sorted([t._replace(deadline=min(t.deadline,end-2)) if t.operation == 'PLANT' else t for t in ts],
                        key=lambda t: chain_order.get(t.reason, order[t.operation])) for p,ts in groups.items()}
    stock = obs['private'].get('shed', {}).get('WHEAT', 0)
    for route in routes.values():
        stock -= sum(t.quantity for t in route if t.operation == 'PICKUP' and t.argument == 'WHEAT')
    fertilizer_stock = obs['private'].get('shed', {}).get('FERTILIZER', 0)
    for route in routes.values():
        fertilizer_stock -= sum(t.quantity for t in route
                                if t.operation == 'PICKUP' and t.argument == 'FERTILIZER')
    seeds = dict(obs['private'].get('seeds',{}))
    for route in routes.values():
        for t in route:
            if t.operation == 'PLANT':
                seeds[t.argument] = seeds.get(t.argument,0)-1
    values = {target:schedule_value(obs,jobs) for target,jobs in groups.items()}
    homes = worker_homes(obs, units) if EXEC_TERRITORY else {}
    zone_homes = worker_homes(obs, units) if ROUTE_ZONES else {}
    endpoints, clocks, feed, carried = {}, {}, {}, {}
    jv_cache = {}
    owners = zone_owners(obs, units) if (ZONE_SWEEP or ZONE_ONLY) else {}
    relaxed = not (ZONE_SWEEP or ZONE_ONLY)
    for w in units:
        index = w['index']
        p, clock, wheat = tuple(w['pos']), step, w['inventory'].get('WHEAT', 0)
        for t in routes[index]:
            clock += distance(p,t.target)+1
            p = t.target
            wheat += t.quantity if t.operation == 'PICKUP' and t.argument == 'WHEAT' else -int(t.operation == 'FEED')
        endpoints[index], clocks[index], feed[index] = p, clock, wheat
        carried[index] = (w['inventory'].get('FERTILIZER', 0)
                          - sum(t.operation == 'FERTILIZE' for t in routes[index])
                          + FERT_CHAIN * sum(t.operation == 'COLLECT_FERTILIZER' for t in routes[index]))
    while groups:
        best = None
        for target,jobs in groups.items():
            planting = next((t.argument for t in jobs if t.operation == 'PLANT' and t.reason != 'chain replant'),None)
            if planting and seeds.get(planting,0) <= 0:
                continue
            chained = next((t.argument for t in jobs if t.reason == 'chain replant'), None)
            if chained and seeds.get(chained, 0) <= 0:
                # No seed left: still harvest, just without the replant.
                jobs = [t for t in jobs if t.reason not in ('chain replant', 'chain water')]
            for w in units:
                index = w['index']
                if not relaxed and owners.get(target, index) != index:
                    continue
                route = list(routes[index])
                # Fertilizing is optional: it rides along with the visit when
                # this worker can supply it, and is dropped when it cannot.
                # It must never stop the cell's real work being routed.
                wjobs = [t for t in jobs
                         if t.owner is None or t.owner == index]
                fertilizing = sum(t.operation == 'FERTILIZE' for t in wjobs)
                load = max(0, fertilizing - carried[index])
                if load and (not SCHEDULE_FERTILIZE_LOAD or load > fertilizer_stock):
                    wjobs = [t for t in wjobs if t.operation != 'FERTILIZE']
                    fertilizing, load = 0, 0
                if not wjobs:
                    continue
                benefit = (learned_value(obs, wjobs, w, endpoints[index], jv_cache) if JOB_VALUES_LEARNED
                           else schedule_value(obs, wjobs))
                p, clock, wheat = endpoints[index], clocks[index], feed[index]
                needed = max(0,sum(t.operation == 'FEED' for t in wjobs)-wheat)
                added = []
                pickup_index = None
                if load:
                    access = min(SHED_ACCESS, key=lambda cell: distance(p, cell))
                    added.append(task(0, 'PICKUP', access, 'FERTILIZER', index, end,
                                      'scheduled fertilizer load')._replace(quantity=load))
                    clock += distance(p, access) + 1
                    p = access
                if needed:
                    if needed > stock:
                        continue
                    # Enlarge an unexecuted loading stop instead of making another trip.
                    pickup_index = next((i for i,t in enumerate(route)
                                         if t.operation == 'PICKUP' and t.argument == 'WHEAT'),None)
                    if pickup_index is None:
                        access = min(SHED_ACCESS,key=lambda cell:distance(p,cell))
                        added.append(task(0,'PICKUP',access,'WHEAT',index,end,'scheduled feed load')._replace(quantity=needed))
                        clock += distance(p,access)+1
                        p = access
                feasible = True
                for t in wjobs:
                    clock += distance(p,t.target)+1
                    p = t.target
                    if clock-1 > min(end,t.deadline):
                        feasible = False
                        break
                if not feasible:
                    continue
                # Marginal time let the worker already nearby chain every job while
                # others idled; finish time hands the job to whoever is free first.
                span = (clock - step) if EXEC_BALANCE else (clock - clocks[index])
                if homes and (('N' if target[1] < 5 else 'S') + ('W' if target[0] < 5 else 'E')) != homes.get(index):
                    span += TERRITORY_PENALTY
                if (zone_homes and (('N' if target[1] < 5 else 'S') + ('W' if target[0] < 5 else 'E')) != zone_homes.get(index)
                        and not any(t.priority < 0 for t in wjobs)):
                    span += ZONE_PENALTY
                score = benefit / max(1, span)
                choice = (score,-clock,-index,target,index,added,wjobs,needed,pickup_index)
                if best is None or choice[:4] > best[:4]:
                    best = choice
        if best is None:
            if not relaxed:
                relaxed = True     # second pass: anyone may take what its zone owner could not fit
                continue
            break
        _,negclock,_,target,index,added,jobs,needed,pickup_index = best
        fertilizer_stock -= sum(t.quantity for t in added
                                if t.operation == 'PICKUP' and t.argument == 'FERTILIZER')
        if pickup_index is not None:
            old = routes[index][pickup_index]
            routes[index][pickup_index] = old._replace(quantity=old.quantity+needed)
        routes[index].extend(added+jobs)
        clocks[index],endpoints[index] = -negclock,target
        feed[index] += needed-sum(t.operation == 'FEED' for t in jobs)
        carried[index] -= sum(t.operation == 'FERTILIZE' for t in jobs)
        carried[index] += FERT_CHAIN * sum(t.operation == 'COLLECT_FERTILIZER' for t in jobs)
        stock -= needed
        for t in jobs:
            if t.operation == 'PLANT':
                seeds[t.argument] -= 1
        del groups[target]
    if ZONE_SWEEP or SWEEP_ONLY:
        for w in units:
            routes[w['index']] = _sweep_order(obs, w, routes[w['index']])
    return routes


def assign_tasks(obs, use_fertilizer=True, unit_list=None, available=None):
    if not SCHEDULE_START_DAY <= obs['day'] < SCHEDULE_END_DAY or liquidation_stage(obs):
        return _legacy_assign_tasks(obs,use_fertilizer)
    units = workers(obs)
    tasks = make_tasks(obs,use_fertilizer)
    player,step,day = obs['player'],obs['step'],obs['day']
    state = _schedule_memory.get(player)
    if state is None or step <= state['step'] or day != state['day']:
        state = {'step':step,'day':day,'routes':{},'pending':{},'confirmed':0,'failed':0}
    live_keys = {task_key(t) for t in tasks}
    # Reconcile in-place service against observed state before advancing the route.
    for w in units:
        index = w['index']
        route = state['routes'].get(index,[])
        pending = state['pending'].get(index)
        if pending is not None and route:
            old,old_inventory,old_tile = pending
            tile = obs['farms'][player]['tiles'][old.target[1]][old.target[0]]
            if old.operation == 'PICKUP':
                success = w['inventory'].get(old.argument,0) >= old_inventory.get(old.argument,0)+old.quantity
            elif old.operation == 'DIG':
                success = tile is None
            elif old.operation == 'PLANT':
                success = isinstance(tile,dict) and tile.get('kind') == 'PLANT' and tile.get('crop') == old.argument
            elif old.operation in {'FEED','CARE','WATER'}:
                flag = {'FEED':'fed_today','CARE':'cared_today','WATER':'watered_today'}[old.operation]
                success = isinstance(tile,dict) and bool(tile.get(flag))
            elif FERT_CHAIN and old.operation == 'FERTILIZE':
                # Judged as a harvest before, which failed and threw the whole route away.
                success = isinstance(tile, dict) and tile.get('fertilized_until_day', -1) >= day
            else:
                item = ('FERTILIZER' if old.operation == 'COLLECT_FERTILIZER' else
                        old_tile.get('crop') or ANIMAL_DATA[old_tile['animal']][1])
                quantity = 1 if old.operation == 'COLLECT_FERTILIZER' else old_tile.get('yield_units',0)
                success = w['inventory'].get(item,0) >= old_inventory.get(item,0)+quantity
            state['confirmed' if success else 'failed'] += 1
            if success:
                route.pop(0)
            else:
                # Repair from current state; never blindly advance a failed command.
                route.clear()
        while route and route[0].operation != 'PICKUP' and task_key(route[0]) not in live_keys:
            route.pop(0)
        state['routes'][index] = route
    state['pending'] = {}
    routes = schedule_compile(obs,units,tasks,state['routes'])
    assignments = {}
    reserved = {t.target for route in routes.values() for t in route if t.operation != 'PICKUP'}
    # Execute stable programmes; spare workers retain the existing builder/repair path.
    for w in units:
        route = routes[w['index']]
        if route:
            assignments[w['index']] = route[0]
    idle = [w for w in units if w['index'] not in assignments]
    if idle:
        loading = sum(t.quantity for r in routes.values() for t in r
                      if t.operation == 'PICKUP' and t.argument == 'WHEAT')
        hungry = sum(t.operation == 'FEED' and t.target not in reserved for t in tasks)
        carried = sum(w['inventory'].get('WHEAT',0) for w in idle)
        quota = min(max(0,hungry-carried),max(0,obs['private'].get('shed',{}).get('WHEAT',0)-loading))
        fallback = []
        for t in tasks:
            # Workers may share shed-access tiles. Reserve production operations,
            # not the physical square needed by unrelated pickup/deposit chains.
            if t.target in reserved and t.operation not in {'PICKUP','DROP'}:
                continue
            if t.operation == 'PICKUP' and t.argument == 'WHEAT':
                if quota <= 0:
                    continue
                quota -= 1
            fallback.append(t)
        reserved_seeds = {}
        for route in routes.values():
            for t in route:
                if t.operation == 'PLANT':
                    reserved_seeds[t.argument] = reserved_seeds.get(t.argument,0)+1
        fallback_obs = {**obs,'private':{**obs['private'],'seeds':{
            crop:max(0,quantity-reserved_seeds.get(crop,0)) for crop,quantity in obs['private'].get('seeds',{}).items()}}}
        assignments.update(_legacy_assign_tasks(fallback_obs,use_fertilizer,unit_list=idle,available=fallback))
    if EXEC_FILLER and not liquidation_stage(obs) and obs['hour'] < 23:
        claimed = {t.target for route in routes.values() for t in route}
        claimed |= {a.target for a in assignments.values()}
        for w in units:
            if w['index'] in assignments:
                continue
            job = filler_job(obs, w, claimed)
            if job is not None:
                assignments[w['index']] = job
                claimed.add(job.target)
    fert_targets = dict(fertilizer_targets(obs, use_fertilizer))
    # Deposit at midnight by default, but free space before overflow or low cash.
    total = sum(obs['private'].get('shed',{}).values()) + sum(sum(w['inventory'].values()) for w in units)
    for w in units:
        index = w['index']
        if total > SCHEDULE_DEPOSIT_LIMIT or obs['farms'][player]['money'] < 500:
            goods = sum(v for k,v in w['inventory'].items() if k not in {'WHEAT',*ANIMAL_DATA})
            if (goods and tuple(w['pos']) in SHED_ACCESS and w['inventory'].get('WHEAT',0) == 0
                    and schedule_route_fits(obs, w, routes[index], delay=1)):
                assignments[index] = task(0,'DROP',tuple(w['pos']),owner=index,reason='scheduled cash or space release')
        # The scheduler never routes FERTILIZE, so a carrier applies it when a
        # route step leaves it standing on a target and the route still fits.
        if (index in assignments and routes[index] and assignments[index] == routes[index][0]
                and routes[index][0].operation != 'FERTILIZE'
                and w['inventory'].get('FERTILIZER',0) > 0 and tuple(w['pos']) in fert_targets
                and schedule_route_fits(obs, w, routes[index], delay=1)):
            assignments[index] = task(0,'FERTILIZE',tuple(w['pos']),owner=index,reason='fertilize en route')
            fert_targets.pop(tuple(w['pos']))
            continue
        if index in assignments and routes[index] and assignments[index] == routes[index][0]:
            t = assignments[index]
            if tuple(w['pos']) == t.target:
                tile = obs['farms'][player]['tiles'][t.target[1]][t.target[0]]
                state['pending'][index] = (t,dict(w['inventory']),dict(tile) if isinstance(tile,dict) else {})
    state.update(step=step,routes=routes)
    _schedule_memory[player] = state
    _strategy_telemetry.setdefault(player,{})['schedule'] = {
        'routes': {str(i): [[t.operation,list(t.target),t.quantity] for t in r] for i,r in routes.items()},
        'confirmed':state['confirmed'],'failed':state['failed']}
    return assignments



# ============================================================================
# TOP4 transplant (docs/TOP3_MACRO_PLAN_2026-09-24.md, TOP4_MIDGAME_RESEARCH_2026-09-24.md).
# Data from the 24 Sept replays of Team A, Team B, Team C and Team D:
# - script: the day 0-5 actions of Team A episode 112920694 (seat 1), the game closest
#   to the per-step majority of all 46; replayed only while every worker stands
#   where that game had it, otherwise the planner takes over for good;
# - layout: the most common content of each cell at the end of each day (at least
#   40 percent of games), used as the planner's crop and animal target for that day;
# - workers: median workers per day.
# ============================================================================
import base64 as _b64, json as _json, zlib as _zlib
_TOP4 = _json.loads(_zlib.decompress(_b64.b85decode('c-qZfVUHZQk^L|Gc|UYLl1(z-6nS$tPPPn5J|iaxfsym!f?VQ2PH;E`_up@)r+237)tjE~(aH%dthb9CvdCh+$L{8v{rla|zyJ7$zx?&?SMUFR_n$v}{L_ygAAi03_Ql(`cOUNW{_BT7|HsddhR0w3^uxzL{&=YO{_fY`{q}b+zWM6w7q9N_?_R$C{_fsB+#k)~zIpw{cQ4;P+Q0wu;l<<s%ZCsDcki11>gB(F_wC|?7dm<S@aomMnW=*>zk2g<cjcEA-%jSYUp_oMdXU()Uw`-2t1o`{IQDnnO|6|gTX;Qxc4~Cpc<wybTOTUV*sB*WAJl}szx(F(n|EJM<5s_Y|M2$R-G{5wD&uAs<2F}F&XHqR_lsZ7ZqT$olRv+Cc=*D{h{GqHd78|Pq1f!s+|_c)a8LKj#W~a7-@SYhC+E=h+rv2T@4kL`_4=E;dwj|S9lN;Ku2BS+j$9q;+t=T@C3k;07}p1Qbr`%7O-J~ge{<Q&kmi}WFjwEaJNZXlO~KnWRg3I=@$TWxdKbGVi(6WBJkO){;97t4Oo#rST95;b!#b^wr=nxK+j7vm5_yFvYq_FVW_m8WHgdb(-P%IgJ<}WdJGU9ZcXfVm>+M3*((?S18rr^(6R^9xn4RY)&yW@u^v$zMgZZVWS7hq~xy8IjeB0E|Q=@8p=MKYfD>y1zTxn=ilP_PtdiC(~-S2+$@aElDufF<sKQn&JTQ;6of1&=rc=P((yRDnKm2o`PRg--pv6Y?RV*IqrmfMU#0qgS^eAu<q5Me)0&83D{+KY1@8(EpND?4KNmessmG(Ws}>Ryy@i`%wviRE(6npH1O<<GE%6J4HuxpAK;2KKZQ3{!PO!8#J&zIlbaL0lTolpy*Riy+ZP>Ea$SknCw|c)A%`?R(E%$(AskJ5$p@3*<T0#c8}ZK+?(%`_k-fx=~o$NMG`I*NsQqo}RorP4QJXw~YSu%bxqBIQ-b&r4j5Skk~FiC0HAO+@M}=?uH<R`vkfFi<z)v1E%(Q|MVNM8y^Ph$Ai}&oow5iiKk0z&)%*+a=5ewSz1<ih8Ok*SJ$u@k{H_#j0`=T{1*cerb}CZ>-2Kdo@{NJL%Q7fVC>qy@A6{0Wg5h@zZ>?Q_xd5jmAlWGh&SAAU*82@LFY~VianUv<>9t{p?n(gY!f7(bY3Ew^%RxZkZH^K_T8Ho-~amI&70qDa*qlAem~9Z=ss={;=V{B@s}^&{M*(wwCcgRp>^!sFfF$^@U#<HRJyQ{KJ`nFa&|q6+#3$j*>dis@j9rkJ&KH5MBXd9sk(X(u|E4Nyt(4Zc~(y2{zdyggRGj9=W=B&6yY}G(~{t(zE_d)^LD*l?s5rS?PU?dXISyiw6ouN1F`n{_;c*_uit8|>~Jq^hPG|KFFq)}{Ejhh_%Cia_PpK49tvOE`fut~K9Jm!R&in$HwV`uvFYw%`<wA=`{B!UztZ2_==I(B#i)yI@yg4u9gkl*E%TL4xP<OcT>zWs=lq~@WuvZ8@YzUs_3^n%rg;B!orXVkK6l*ltZrYo-_qPlo8rlHjMR>Y9r&~xnvE>JzQ}&jZO!M~T<+Rc{iC;*|BMm&q`TeQI$wSK`n;WsdykdZ2%mIcxi-lc0>AR&<$0$;ZHBkM_1P6=amenO-+yd*{r7x#4`J$d+&$#yJgTw#F<jbl+py~m!0NVE?|DA|=vQBTY<xGpVb8yIKX!E)uI%V<Y3}Noma7lTSB_9!-TaC~-|;GSWh!ns;<bL`cH=bNFse<nv}4vUY>2mPnbjG=PnpFSu=reimCxjZ{p<HF@+9(e@aD>ZE<Ul`cff6@>sKM}<ln_7Z8x4>P;B=pyMmkiyL_8-OLLpH6rX7e^gPb(2*v95=9UJxKL&lq^9}gCTbz9l!=7c=v+sG|%EMoAbUxnUY<}pu<B9K;dEDg1Rop#)_}X*LTly1^?O0%R`9Y?*m%Dx&u=!ZSrF+t==Lv2*KocKhT{%d)bKEz+68aoNy*A-%H|w8mpnQ;IAKzR&4YFlSH*_dg%gW=Gtxw#sYs<G~)oggFchlJRY|}sSG1!JPTboXv?t9Yq%!Bw$v-DZ_Xum-FpSF$LxsDz_<t_T{>*(?7FF*bKhrj;er$0}PzR!nSyL<ot`}bw~neWT=dzpUUSDt3uQ{Cjs^HiP|byYd$axBWz?(#g9V=jNP9e&!P++=xLl&6d3wkWqn|Gpfe9E);u<v5imQJyxI+oF63<-=40QI6f^!(2YN^5e`8q1>*Pr;Fufx=N>?PyO45b$oe+9!t_GHhB?eRh~|(n%90lt;eSom_#`i<+xa$s9g7-s65lp^XIX%JY6Yg|IN)w^lu=~`SXJ)iRI_qw$smJ?sGY=mZx3i7Wz+%+>hnwb$Y~(W%+pppRom}5?{U@qnCEQ+VfmDEwHx)?0t&gvMw&H<)?_1lf`51rM$=v|JHNlSj*RqSpT%Pj&%nYn|vX6jxiZ7V7y=LcEY14Jl|8-Laj8fq9=qsV%`}Cm$87Tn?l{>*6nby-R1mZQ7hI>SL)i0b+KC4sIKj(J6x!1o9o(+x`X4NTk6^de{aeCB-ZA#Zd!0x5^Hl=cbWST>ure>CiYt~_m6c4vG)S4`6r9YX9TV}*BwOe`y9n7_n+$KU3HhWmb0<kx2U?ym2WrJ#XPouL|yyLb<?K0$6U%6>!!unp0jS=T^GXNOm*YVdf0hymRz~d_hq@-C7$!I%o&uz{?=zB7Wt{lZE=USt=x08E$*Q9m*aHT75C>$9=%qcE|d?l{JcNEUOtHO^USL9<jU<zImG-f%ae%DvOJ6O^oiv;l=HKL+c>UV;J7T-SGjPPl-+X(T-Yz>m1hbma9j?1*2^517rd2MIc{5B&*h2__td>~XX&whf8Dj+v+byhjdcfCH?8<<bKUgpb!|u8<vP1oH~kaT&8}`<ty`Y*;=}#jfB*2mKmBcb7x9REkN=&&o!}Aa=o)l=sNw4y)%VxwaDDpHhsO+}>%%8}dvN8T@<iqNaDDi;!1>dOO4HL9CC<HN>Mc`m+0{>Uoe$S@Z$@)xG<QaGckpdk^mgdmU;DW=np>l}HJV$axiy+wqq#MjTcf!(H@An@61A47HGiGx+Q-5u7Dll!iiJ@u%*6u7Sonj)pa6gZ015yo05}F9Hfq$UQKLqUf*OS@PjtPUb<nJXW*s!^pjijaI*zl>L-JD(ntIUG!%clsQ=g8xz(y#e4@#n-q+?KG^QM|N)x1&jM$JPt4_67QQld)Bz@=m0V!Mgj_1B56ee{xwUZUtFie94VB^SM{qL)?lvWi}&=w*stR?*8UdRav;Q}i-LFRSQfie6UH%M`urqL)?lGDR;_^fE;+Q}nWmUZ&_}ie9GZWf#4oqE}S(ii%#L=oN}yQPC?ZdPPOAQ1l8#uc+u1ie6FCD-^xrqE}S(3PrC_^a@3<Q1pt5UZLm}ie91U6&JlxMQ>Em8&&j1irz@k8}EzyP*ujJj9nSUiWt?37}bgxX+?~*A`UK#4~>p-4?{3D1XDxspA-vjqy;ys1vk=y8{L9CxV^lpj`0t!fxJk{i$q@d>qOUnc^+Iy3l~OrRaJ*#J&&}WM_SJ#t>=-}b8%PoaP=>*U%#D>6;`#{t6J?<t@cW*z0zv0YPHw<Q5mZ;Hf8L}C{m!R6sRf%Dy2ZB6sRf%Dy2YGDNt1kR7!!WQlL@_RFwjiQlPpNs4fL6r9h<=ICur}Dk-lLdF8JYUHg=%E+wi<iK<fK;AJ8&6M31HmzliG&Wl9X%ao}uWok&7?(UJAN};AwsHqfcltPVCsHqfcDutR#p{7!(sT67|g_=sCrc$U;3N=chrc$U;3N@8NO{Gwy6lyAk8l_NEDby&1noFVPQm9c1HA<mIDb!R7HA<mIDby&18l_NkDb!pFHI+h*Qm9c1HI+h*Qm9c1HA<o8QmDBUYLr5aQmCsG>MDi0N}*0E)G39!N};Y&sH+s}DuudAp{`P>s}$-gg*v5BrxfZcg*v5BS1Ht03Ux}Mu2QH|3U!r2ol>Z~6zVR84*o8$d_r|fs7?vhRYG-2s7?vhDWN(gRCfv0T|#x0P@NL0Q$lr>P@NL0Q$lr0sO}P~yM*eLP+cTcao0xII9xA2pAOfj)-#n3k8|Q%8>uyao#;9ru3dZe{_frDuV1`-{nTKk1}Y7wkpqqDw>aOKDh-db<h}0HNLP(4E7_o+$_9m1HYl*NfuA@J{K$Dwcx8hEEE^PJ*`OfH28CHRDA2M&p_UB_wrqZXu$-hKtBulHrL{?G=Z*wq+5Em@Sq-vU;%e^M`rvSDa^GE6{&ZtQXM+GQo8OO|vSac#`Sp<4K#%PQhhUSd$-A256espKvA<dRn|XG#_a?Eyy`mW$mQC(uKLMS4@NhQyP}qm!+gKvn<N=izZee6YV?$?y$HmF5k=-IgVuQ!VsZj@xQ>&F*t=wwmRx7vK*wx03Hkl($CVb<BZxUHL_tDw$E}M7NOoFaS&@~CV^J~6fEz&wlYn9d}tzB9b(3%8VlR!JaTwG2}W<!ym8@XDQ)ta<+{;&dFW6(7Ty2hYOFEq`Au6fWk23=#&H3nUiplb}e^PAG8A$c?m?@G;su6fWk3A)ChYYe(3LDv{`!<*RfD%QV?oxIK7z3j)^xd#GWW6(7QUGt!847$dkYYe&vw+aWi@Prlib98`d48z7SYz)K3FnnlX<Zf!{rgArxyQ$nw<r%3wBbEDYq2I>+HkoP4n)$;;R-2%kdSwd)c$<WDi;!MKHF;vdAb}nd=pliAK2#8_MOsH`t<u`0wM(mle|en2AmM*L)gZ>^@EMW=Aa~!8L;y(yU?PAd0x%Ik5&@V9{27aB6z+2LmsPgeq_uNTiW0z-0Hy>mCGbIx$?4>sPTuJxou*bh8x$pgDS=Oj7#|Tae@0~THhcH7A8+R#h!Vh*0Hy?ZN&r&=m=eI00Hy>mC4eabffB%!0Hy>mC4eabObG|iM)quEM{00{EyNl)vW7_W%I;Klr*iKt^wnf4HrZj5nAs$@^)SvJ`tGvtF8l7X?=FGOQHwnLWb*Kn$<t4kB#9(RB1w`+k|dHOi6luPNs@>>cxCeBmC2)5mL!QJ$r(v<Mv|P7BxfY%40*K65_5(;++~S5!yoUOM&T|;e_3UlO<Ftmq&OonXC&r~#GJv$$0nzfcRG2elXRL|?QBq-k(e|1T$=I0H1j9ZCU3KMFZ=O!?twTXF=r&^jN~~ZF=r&^jKrLgm@^V{Mq<uLfin_wMq<uLOc4jqM)quE&qnraWY0$StOn26LL`zTi6kbG#3YiKL{cD;biDtd-kZ$UCS7O}f0{(Q9{TQ~?=Ji9vhObY?h^YPt;j=}CQoIWJeFx$(n^-Jk|nKVNh?{>N|v;eC9TL4p(c-nnmiL~S<*_Dw2~#QWJxPo(n@Apk!MaVGp)!|r<R#k{JGO<6z+2LmsPgeq_uNTidHhyN@iNgOe=h@b#gj+r;~R&NvEmR&IUy*nQ4U&%o?AVHGgDw@-}<-vLA2f9*9;l(@JJq$(~j+(@JI*$;={|StK)y<iH}CStK)yWM+}fq>-64GIK-@9FYS@Wafx0IU+MhWafy>9FYS@<iHVGazvIKktIiD$q@(d8ava2Gd(!dr88YR)1@<AI^#$~o&`5~7~JG(a4V8DiX@F9Nux;8D3UaaB#k0TLmosoc@o{^QFJSkH0BfOVr(YIW^!yM$7XVD#vy|o7JN0xYKf~kDk+{yil>qysia6MDMu<1F-g*SM<0dxq%fcGN&Ct3<ULQ`^CUf|Ry!LMpA_a3KEiK&hTr@l{>j_y-OGNwUG__)QkYZ<lS=WVQkYZ<lS*MyDNHJbNu>l*Da;||`1HzEAyz5O86|K=37k=wGm7Ml!kkf<GfJR{5-6fbiYSsIilm4lDWU{MD1i}*WP~Cap-4t3k`bhw#H60Yq@ct`NdTiH0I4pqQ4)X@otRXen3SEE)SZ|Vo|sgg*eD5LlmsAUC^kw0kZKf@auj1dib+9=&5D%8l98Ge8<_#TD#g4kW%A!$R@r8g)-J7z0Y+wkkr`lQ24FFZc{Pi9Ig3d>%j7w=+S#BOU}Oeh(TlO_#k}mryza$V_%b<?<?I#Tud#s`VDt<yG6Rgv03$QN$P6$t1B`(I#^Y@TEyvM+D1|D-3FGnMldICX6=sPsu*AqLF-n#gnI%SMi7~Lm7+7MIEHO%!7$r-Lk|oB#5@TSAQL@A+Sz?qdF-n$@GAxriER#YktCA(EWC^LtGAYY4smn4c%rdFWGAYe6sm(Ge&ax_5qDq#KN-e9BC8S`>q+-ihvSm`UWi_yblx<mMmhi$Y^UAHse|K4Bn@w7~v?`XU%o3GZqB2XczRSG8%e=zNq{Pcu<7F)JGO6;i$}GV;FJqyXd8L<msh6?V%c^9F$}CZtB`UK-^(;}DB`UK-WtOPS5|vq^29~ISB`UK-4J=WaC2C-a$}CX>OVq#;m06-nmZ;1Um06+&mZ*Uxs$_{OS)xjosFEdWV2K)7qDq#ik|nBSi7HuQRvIpPk}^Y+IzwxcA(~_eDLOQ%Iy5OeG^sl@DLgc(JhWMQ=tc`!FG*{b)*`K=v{q?t(n{<g<%re-J4i*MHD(8|Ni;7?v?l4GNjhkf4x~=e8q+~zI%rG>tW`8GRy3(kG!`ftD->;(DALl;z6xPKD-_L36wPZCjYW#qB=$GP{>Iqf82g*Y{>Iqf82cMze`D-#jQuTOe+$^(82ekm{>Iqf0`@n?{uZ#m1?+E({Y_$jW9)B?{ViaB3)tTz_BV<BO=5qO*xv&7w}AakVt<p^-z4@oiTyob|E!O77W!_pE+M~5$d@8nlPX!0GFg*4S(8Fp>jB)mgz+w6Tnb^WOBk1WSd)TSV@0fW{<gLr5WF*1d-1Dz^{aJ>)m>tBmss8TJKs9PbZ40E4AZQDH7|iRsd_b*y&CIYtp}Ly4AU%oHP*eF7rvTTz8XtktxK3@1+1|I)>s2;UIc5bf}PeEwNTm6*wER)Fx>-8vz*p?fN56LPCav#&aE&^_W;wKVY*A0?hMnNVY&yH?g6H|glVbewJu@0OPKBfrh9<tE@4_qfUQfI?h2+cFic}$m<E4+Ck6%67!*uHYJ(xQ!I0WuNNq5rHW;%un1*9vIL5;<IUJM2F*zKQ!!bD=lfxmW=o=pgMso1int}zw@B(3YfiMOI?HClaV^GkJfxlRiwZRw&+A$EcgSEl%+F(dAFjx!>76W5oXa@^{!9rlL5Exzv3@-!*3xP2xXa}o-!D?Wz8W>&;3|0e!#lMp)WN2*YY#?aIz|aoX17l!l2MdCyp1DfrRtVZLFtme3!x$8_gO$S=7|Ag(l0#~TA+^I86p}*<h%qpdPkr~$cb9#4*>{(HN2>)Sw}9mQWx|j$W0*v8DL#f2A47_dA;rg#;$v7qatlb#-(?JwNNy6zrScdikzC4;A?3$l`7!t#lwkqM`Ad{BtBzm3c=P7<yVD>R*zIM<FbU-*q1+^t^EWet6~|!3F<5a7Rvg1Cjv*z+V2LqUVhjsV&hlcgycjGm27T4Dmlwk%a<iluEGY&{is2>2U`a7pK@3(9gB8SJ1u=qx7#5J5CB(3R+^iv<IvRPnH8fkf*(y`6@~|t9p@lKD&{-30Cuz;nTBMa>I*5fK#lnzcVVHzzsTc+VOe4T__{wo95{48BV-^W7KRn86m8&&btxGF|GXgk=uQ-=#U_gTNED835Fm~6ZyHt(97Xf_1;EMph^mXc9>I<puh1B)}5`4oKw6nGstnCGBdl9~*-D`U>i+TMFlA*JKahEl`2;cG^zUJL)c;Pj?V9736vI~~%f+f4~l3lQ57p%|)D|EpMU9dtIvqIOc35Hyj=mG(9S))63H1cq3Xtr{*RVGs9VOJhQ3r#oCQj*pztwmZPp)W~mmR1FxDS&4R;F%aar8pK+9E-%@IqPDVhRTM<hRy~?%M{QuF<MI5E0RRZ#AulqEoTX=_uANNW3S;2jGT#)GX>=If>(IKD-wM@4ibGm4p`TU#8AnSR<NWMENKNxTHz(FNDP%MUj@rokpfh*bQLUJ1xr`qrK|ALRj^VOtW*UnRl!PCc%>>>sR|aRf`zGIVJcXdiWH!db*PgYBh3~8BMVW%icv_#C|EHHR*XW5KOx1Rkm65B@h7CP6H?d-DeQz4b|MGR%K`K<gPxRbLP|H08T2xPUS`nC40@SCF9*=e0rWD1o)l#wOVG;<dYM5lGw5XoJ(gu6Gw9_2dYM5l2hj6!On5maGJ{@b&|}plGJ_rqF2RCJu;3CbxP%v6A~Wc*xDqU`L=K?G!b-5P5-hBQ7goXxE5SNSu#OU}qXg?H;dPW?9VJ*t3D!}9b(CNoC2{~gmQ7A>jA5OO-jnIMD7C^C1$!)l#4K^7rkeO*lGZG(MOq<ID@kjXR)u>d;9d#1R~YxC`Vdlmh{Cv6821X}USZrTjC&>EUJ1BY826;E5K>o&!nju$_X^`)VccU4AqwMO3Ak4n_e#J$uN{Qf4r100dOyK_g8c;hnb=Q<d#n@$D+R$yL3pJg3Iidl0>P?4lmLXR2m~tv!HPh5MIgK)5QTw|wSQpkA6WYbul)mS|G?Tmu=WqE{R3<NPy!H^<BhVj5HywmjjRSl3D8&qG)k=>SnCJY`k@4@l*&HL%06<l$rM#qNR&&`nx$3Y<QQ;r3^+M5PD+s;q(~1V<K)OVIWkU;jFThd<QQ;r3^+M!@D}qu>+hT;2TKVSLdcO3a%6;LksW4{ookgLau(Q;zX<*=K+&t~FfvB+pMe7Z9Vm>9k+YzVJaw4JVmh#x4lJgF7t>*6kYwQ;SU86<fFz6Nz@j;@XbxU92QQk#$RNq`IIuhpERTbi$ART>V0j!^9tW1kf#q=+14xbmBxiXXEv7LnrqMfBLKXj292f(T&iXj&yN152#Ea_tXC$5VaMXAUjkhqc7P7ht2d4Kn)OruC_t1KmFc+;gplc22S{Yquaof_MfVDEPRtDC}z*-qtYrxSOaI^;0tN}G^Ku!L0VW^Cnl~J<>xbreGc$pX~!yW(0FYw>|0{_u3um%jQ0RwBmz#1@k4Hzne8|%HmdN0%fZmjhJYrVi)FL<pNyw(f+cf7!=F0iT#tm=YSb%9k~U{x1b)df~{fmL0o0o-bUGL~#jW92FYTs6Q{4KO7YT4041YJi{`AgBfilF}zg=@WwV2`#`zW0VLABD9c|{1?dJr8e+V8?Yn>EQtXtVBi%nXq*f|+5%RxfR!xpN)~t}3s`^xFF*kcP{0BdumA-tKmiLyAO#&@K?kJf0YTk>AP|5*R}X)#9()KMd<Y)?h&#ejb@+4V@aN9K$Hn1~i-V7ggU@KgpPK$~fA>E>ef;B(AAi34)%!Ai4gB%H$B_)vzsCuH|Cg@)JJqzu=70X_Zy$gE<74Z0U%dVL?*7gU9mCl3-Tm<4|NbBDlQmZ')))
TOP4_SCRIPT = _TOP4["script"]
TOP4_POSITIONS = _TOP4["positions"]
TOP4_WORKERS = _TOP4["workers"]
TOP4_LAYOUT = {}
for _d, _x, _y, _k in _TOP4["layout"]:
    TOP4_LAYOUT.setdefault(_d, {})[(_x, _y)] = _k
TOP4_LAND_STEPS = (150, 220, 254)
TOP4_LAYOUT_TARGET = False
_top4_off_script = {}
TOP4_SCRIPT_LEFT_AT = {}


def top4_nw_plan():
    """The top four's NW layout at the end of day 5 (crops by type, animals by cell)."""
    crops, animals = {}, {}
    for (x, y), kind in TOP4_LAYOUT[5].items():
        if x < 5 and y < 5:
            if kind in ANIMAL_DATA:
                animals[(x, y)] = kind
            else:
                crops.setdefault(kind, []).append((x, y))
    return {crop: tuple(cells) for crop, cells in crops.items()}, animals


def top4_scripted_action(obs):
    if OPENER_PROFILE != "TOP4":
        return None
    player, step = obs["player"], obs.get("step", 0)
    if step == 0:
        _top4_off_script[player] = False
    if step >= len(TOP4_SCRIPT) or _top4_off_script.get(player):
        return None
    farm = obs["farms"][player]
    positions = [list(farm["farmer"])] + [list(p) for p in farm.get("hands") or []]
    if positions != TOP4_POSITIONS[step]:
        _top4_off_script[player] = True
        TOP4_SCRIPT_LEFT_AT[player] = step
        return None
    action = TOP4_SCRIPT[step]
    return {"farmer": list(action["farmer"]), "hands": [list(h) for h in action["hands"]],
            "market": [list(o) for o in action["market"]]}


def top4_land_funds(obs):
    """Cash plus what the stock in the shed would fetch now, with a haircut for price impact."""
    prices = obs.get("market", {}).get("prices", {})
    shed = obs["private"].get("shed", {})
    stock = sum(count * prices.get(item, 0) for item, count in shed.items()
                if item in ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL"))
    return obs["farms"][obs["player"]].get("money", 0) + 0.7 * stock


def top4_override(snapshot, obs):
    """Target today's consensus top-four farm on every unlocked quadrant."""
    me = obs["farms"][obs["player"]]
    unlocked = set(me.get("unlocked_quadrants", ["NW"]))
    quad = lambda x, y: ("N" if y < 5 else "S") + ("W" if x < 5 else "E")
    target = TOP4_LAYOUT.get(min(obs.get("day", 0), 29), {})
    crops, animals = {}, {}
    for (x, y), kind in target.items():
        if quad(x, y) not in unlocked:
            continue
        (animals if kind in ANIMAL_DATA else crops)[(x, y)] = kind
    for y, row in enumerate(me["tiles"]):
        for x, tile_at in enumerate(row):
            if isinstance(tile_at, dict) and tile_at.get("animal"):
                animals[(x, y)] = tile_at["animal"]
                crops.pop((x, y), None)
            elif isinstance(tile_at, dict) and tile_at.get("kind") in ("COOP", "PASTURE"):
                crops.pop((x, y), None)
    for pos in animals:
        crops.pop(pos, None)
    return {"name": "TOP4", "desired_cells": crops, "animal_targets": animals}


if TOP4_LAYOUT_TARGET:
    STRATEGY_OVERRIDE = top4_override

# Keep `agent` last: kaggle-environments' file loader selects the final callable.
def agent(obs):
    return decide(obs, True)


agent.telemetry = _strategy_telemetry



# Generic market module (Codex, dev/eugene-codex-market-module, docs/MARKET_MODULE_2026-10-01.md):
# price-gated lead sales, F4's one-turn price-model lead, marginal-price exposure ordering.
# Kept in its own namespace; wraps the planner's final market orders.
MARKET_MODULE = False
_MM_SRC = '"""Generic market rules derived from the Apache-2.0 Metav4/F4 sources.\n\nSPDX-License-Identifier: Apache-2.0\nAttribution: Ahmed Berat Ozer, prvsiyan, yhay81, thomastschinkel and the\ncontributors/notices in agents/ours/h1-substrate-{metav4,f4}/main.py.\nNo route tapes, opponent identity detection, engine import, or network calls.\nCall once per turn. Existing planner orders keep their purchase barriers.\n"""\nimport math\n\nENABLE_WHEAT_ROUND_TRIP = False  # Opponent-dependent opening; measured -$3 vs v0.10.\nENABLE_PRICE_GATE_LEAD = True\nENABLE_MODEL_LEAD = True\nENABLE_EXPOSURE_ORDERING = True\nPRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")\nMODEL_ITEMS = ("MILK", "STRAWBERRY", "WOOL")\nSHOPS = {\n    "BAKERY": ("EGG", "WHEAT"), "PIZZA_SHOP": ("MILK", "TOMATO", "WHEAT"),\n    "BRUNCH_SPOT": ("EGG", "WHEAT", "STRAWBERRY"), "YARN_STORE": ("WOOL",),\n    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"), "PET_CAFE": ("CARROT",),\n    "SMOOTHIE_SHOP": ("STRAWBERRY", "MILK"),\n    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),\n}\n_PARAM_ROWS = (\n    (25, 400, "sqrt", .8, "log", .2), (35, 450, "hinge", 1, "sqrt", .7),\n    (60, 200, "hinge", .4, "sqrt", .6), (120, 100, "sqrt", .7, "linear", 1.6),\n    (250, 300, "log", .2, "sq", 3.6), (50, 332, "hinge", .4, "log", .2),\n    (160, 122, "sqrt", .6, "linear", 1.6), (200, 105, "log", .2, "sq", 3.2),\n    (100, 200, "linear", .4, "linear", .4),\n)\nPARAMS = {item: dict(zip(("base", "T", "below_func", "below_target", "above_func", "above_target"), row), I0=10000)\n          for item, row in zip(PRODUCTS, _PARAM_ROWS)}\n_STATE = {}\n\n\ndef _shape(kind, x, threshold):\n    x = max(0, x)\n    if kind == "sqrt":\n        return math.sqrt(x)\n    if kind == "sq":\n        return x * x\n    if kind == "log":\n        return math.log1p(x)\n    if kind == "log10":\n        return math.log10(1 + x)\n    if kind == "hinge":\n        return x / threshold + 8 * max(0, x / threshold - 1) ** 2\n    if kind != "linear":\n        raise ValueError("unknown price shape: " + kind)\n    return x\n\n\ndef price(item, inventory, overrides=None):\n    """Engine quote, including observation market.params overrides."""\n    params = {**PARAMS[item], **(overrides or {}).get(item, {})}\n    distance = params["I0"] - inventory\n    prefix = "below" if distance > 0 else "above"\n    shape = params[prefix + "_func"]\n    change = params[prefix + "_target"] * params["base"] * _shape(shape, abs(distance), params["T"]) / _shape(shape, params["T"], params["T"])\n    return max(1, round(params["base"] + (change if distance > 0 else -change)))\n\n\ndef drain(item, step, shops):\n    """Consumption AFTER market orders at step 0,4,...; town also at 0,24,..."""\n    result = int(step % 24 == 0 and item != "FERTILIZER")\n    if step % 4 == 0:\n        for shop in shops:\n            products = SHOPS.get(shop, ())\n            if item in products:\n                result += 2 if len(products) == 1 else 1\n    return result\n\n\ndef exposure(obs, order):\n    """Dollars exposed to a hypothetical 8–24 unit rival sale, as in R37."""\n    item, quantity = order[1:3]\n    stock = obs["private"].get("shed", {})\n    quantity = min(quantity, stock.get(item, 0))\n    inventory = obs["market"]["inventory"]\n    if item not in PARAMS or item not in inventory or quantity <= 0:\n        return 0\n    animal = {"EGG": "GOOSE", "MILK": "COW", "WOOL": "SHEEP"}.get(item)\n    rival = obs["farms"][1 - obs["player"]]\n    standing = sum(max(0, int(tile.get("yield_units", 0))) for row in rival["tiles"] for tile in row\n                   if isinstance(tile, dict) and (tile.get("crop") == item or animal and tile.get("animal") == animal))\n    batch = min(24, max(8, standing))\n    params = obs["market"].get("params")\n    return sum(price(item, inventory[item] + j, params) - price(item, inventory[item] + batch + j, params)\n               for j in range(quantity))\n\n\ndef _opening(obs, orders):\n    if not ENABLE_WHEAT_ROUND_TRIP or obs["step"] != 0 or obs["private"].get("shed", {}).get("WHEAT", 0):\n        return orders\n    candidates = [i for i, order in enumerate(orders) if order[:2] == ["BUY_PRODUCT", "WHEAT"]]\n    if candidates != [0] or orders[0][2] != 5 or any(o[:2] == ["SELL", "WHEAT"] for o in orders) or len(orders) >= 10:\n        return orders\n    inventory = obs["market"]["inventory"].get("WHEAT")\n    if inventory is None or sum(obs["private"].get("shed", {}).values()) > 80:\n        return orders\n    params = obs["market"].get("params")\n    # Worst-case concurrent wheat buyer; spend only cash beyond planner inputs.\n    buy_cost = sum(price("WHEAT", inventory - (2 * j - 1), params) for j in range(1, 21))\n    me = obs["farms"][obs["player"]]\n    reserve = 500\n    hires = me.get("hires_today", len(me.get("hands", [])))\n    land = len(me.get("unlocked_quadrants", ["NW"])) - 1\n    for order in orders:\n        if not order or order[:2] == ["BUY_PRODUCT", "WHEAT"]:\n            continue\n        if order[0] == "HIRE":\n            a, b = 1, 1\n            for _ in range(hires):\n                a, b = b, a + b\n            reserve += a\n            hires += 1\n        elif order[0] == "BUY_LAND":\n            reserve += (1000, 2000, 4000)[min(land, 2)]\n            land += 1\n        elif order[0] in ("BUY_SEED", "BUY_ANIMAL"):\n            costs = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80} if order[0] == "BUY_SEED" else {"GOOSE": 300, "COW": 400, "SHEEP": 500}\n            reserve += costs[order[1]] * order[2]\n        elif order[0] == "BUY_PRODUCT":\n            item, quantity = order[1:3]\n            reserve += sum(price(item, obs["market"]["inventory"][item] - (2 * j - 1), params) for j in range(1, quantity + 1))\n    if me["money"] < buy_cost + reserve:\n        return orders\n    index = candidates[0]\n    return orders[:index] + [["BUY_PRODUCT", "WHEAT", 20], ["SELL", "WHEAT", 15]] + orders[index + 1:]\n\n\ndef market_orders(obs, planner_orders):\n    """Copy planner orders; add bounded held-stock lead sales and rank SELL blocks.\n\n    Default season: 24 turns/day, 720 steps, 100-item shed, ten order slots.\n    Missing market data abstains. Existing purchases, quantities, placeholders,\n    and sale/purchase barriers are preserved. No projected worker drops assumed.\n    """\n    if not isinstance(planner_orders, (list, tuple)) or len(planner_orders) > 10:\n        raise ValueError("planner_orders must contain at most ten orders")\n    orders = []\n    for order in planner_orders:\n        if not isinstance(order, (list, tuple)):\n            raise ValueError("each market order must be a sequence")\n        order = list(order)\n        if order and (order[0] not in ("SELL", "BUY_PRODUCT", "BUY_SEED", "BUY_ANIMAL", "HIRE", "BUY_LAND")\n                      or order[0] not in ("HIRE", "BUY_LAND") and\n                      (len(order) != 3 or not isinstance(order[2], int) or isinstance(order[2], bool) or order[2] < 0)):\n            raise ValueError("malformed market order")\n        if order:\n            allowed = {"SELL": PRODUCTS, "BUY_PRODUCT": ("WHEAT", "FERTILIZER"),\n                       "BUY_SEED": PRODUCTS[:5], "BUY_ANIMAL": ("GOOSE", "COW", "SHEEP")}\n            if order[0] in allowed and order[1] not in allowed[order[0]] or order[0] in ("HIRE", "BUY_LAND") and len(order) != 1:\n                raise ValueError("unknown market item or malformed atomic order")\n        orders.append(order)\n    market = obs.get("market", {})\n    inventory, prices = market.get("inventory", {}), market.get("prices", {})\n    if not inventory or not prices:\n        return orders\n    orders = _opening(obs, orders)\n    step, seat = int(obs["step"]), int(obs["player"])\n    shops = obs.get("town", {}).get("unlocked_shops", [])\n    previous = _STATE.get(seat)\n    history = previous["history"] if previous and step == previous["step"] + 1 else {item: [] for item in MODEL_ITEMS}\n    if previous and previous["step"] == step - 1:\n        for item in MODEL_ITEMS:\n            if item in inventory and item in previous["inventory"] and prices.get(item, 0) > 1 and previous["own"].get(item) is not None:\n                rival = inventory[item] - previous["inventory"][item] + drain(item, step - 1, previous["shops"]) - previous["own"][item]\n                history[item].append(max(0, rival))\n                history[item] = history[item][-12:]\n    shed = obs["private"].get("shed", {})\n    blocked = {order[1] for order in orders if len(order) >= 2 and order[0] in ("SELL", "BUY_PRODUCT", "BUY_ANIMAL")}\n    if ENABLE_PRICE_GATE_LEAD and 192 <= step < 696:\n        # A live planner will read the smaller shed next turn; no tape debt needed.\n        # All held non-input produce is assumed intended for eventual sale.\n        for item in PRODUCTS:\n            base = (market.get("params") or {}).get(item, {}).get("base", PARAMS[item]["base"])\n            if item not in ("WHEAT", "FERTILIZER") and item not in blocked and len(orders) < 10 and shed.get(item, 0) > 0 and prices.get(item, 0) > base:\n                orders.append(["SELL", item, shed[item]])\n                blocked.add(item)\n    hour = step % 24\n    if ENABLE_MODEL_LEAD and 144 <= step < 696 and 1 <= hour <= 22:\n        for item in MODEL_ITEMS:\n            if item in blocked or len(orders) >= 10 or shed.get(item, 0) <= 0 or prices.get(item, 0) <= 1 or item not in inventory:\n                continue\n            quote = prices[item]\n            if hour == 1 and quote < 95:\n                peers = [prices.get(other, 0) for other in MODEL_ITEMS if other != item]\n                if quote < 20 or quote < 50 and min(peers) < 30 or quote >= 50 and shed[item] < 3 and min(peers) < 30:\n                    continue\n            recent = history[item][-4:]\n            rival = sum(recent) / len(recent) if recent else 0\n            inv = inventory[item]\n            future = max(0, int(inv + rival + 6 - drain(item, step, shops)))\n            if price(item, future, market.get("params")) < price(item, inv, market.get("params")) - .5:\n                batch = 10 if hour == 1 or quote >= 100 or 10 <= hour <= 13 and quote >= 30 else 6 if 10 <= hour <= 13 and quote >= 10 else 3\n                orders.append(["SELL", item, min(shed[item], batch)])\n    if ENABLE_EXPOSURE_ORDERING:\n        protected = {o[1] for o in orders if len(o) >= 2 and o[0] == "BUY_PRODUCT"}\n        start = 0\n        while start < len(orders):\n            if len(orders[start]) < 3 or orders[start][0] != "SELL" or orders[start][1] in protected:\n                start += 1\n                continue\n            end = start + 1\n            while end < len(orders) and len(orders[end]) >= 3 and orders[end][0] == "SELL" and orders[end][1] not in protected:\n                end += 1\n            block = orders[start:end]\n            if len({o[1] for o in block}) == len(block):\n                orders[start:end] = sorted(block, key=lambda order: exposure(obs, order), reverse=True)\n            start = end\n    own = {}\n    for item in MODEL_ITEMS:\n        requested = sum(o[2] for o in orders if len(o) >= 3 and o[:2] == ["SELL", item])\n        # A planner sale beyond observed shed may rely on a DROP we cannot see.\n        bounded = (requested <= shed.get(item, 0) and prices.get(item, 0) > 1\n                   and item in inventory and price(item, inventory[item] + requested - 1, market.get("params")) > 1)\n        own[item] = requested if bounded else None if requested else 0\n    _STATE[seat] = {"step": step, "inventory": dict(inventory), "shops": list(shops), "own": own, "history": history}\n    return orders\n'
_MM = {"__name__": "market_module"}
exec(compile(_MM_SRC, "market_module", "exec"), _MM)
_MM_PARENT = [_v for _v in list(globals().values()) if callable(_v)][-1]
globals().pop("agent", None)   # so the wrapper below is the last callable the Kaggle loader picks


def agent(observation, configuration=None):
    action = _MM_PARENT(observation)
    if MARKET_MODULE and isinstance(action, dict):
        try:
            action = dict(action, market=_MM["market_orders"](observation, list(action.get("market") or [])))
        except Exception:
            pass
    return action

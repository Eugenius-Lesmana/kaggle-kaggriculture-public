"""Same morning, different players: from saved mornings of recorded games, let each player run our seat for one
day while the opponent replays its recorded moves, and record how the day ends.

python tools/compare_day.py <tag> <game.json> [<game.json> ...] --players template,recorded --days 8,12,16,20,24
Players: "template" (our pinned agent, memory warmed from the recording), "recorded" (the moves actually played),
or any name accepted by kagml.opponents.load (the published agents, once Codex's loader exists).
Writes <data>/runs/compare/<tag>.csv: one row per game, day and player.

Per row: our cash change over the preview, goods held (shed and bags) and goods already produced on the farm
(units on plants and held by animals), all at the closing prices; value change = cash + both kinds of goods, the opponent's cash change (our selling moves its prices), crops and animals on the farm, crops planted
that day, animals fed and cared for, and how many unit commands of each kind were issued.
"""
import argparse
import csv
import gzip
import json
import sys
import time
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import runs  # noqa: E402
from kagml.preview import (PRODUCTS, TemplatePlayer, env_from_snapshot, pin_weeds,  # noqa: E402
                           snapshot_from_replay)

COUNTED = ("PLANT", "WATER", "HARVEST", "FEED", "CARE", "FERTILIZE", "COLLECT_FERTILIZER", "DIG", "PICKUP",
           "DROP", "PLACE")


class Mix(TemplatePlayer):
    """Template agent with part of its action replaced by another agent's: "units" takes the other agent's worker
    commands (template keeps the market), "market" all its market orders, "sell" only its SELL orders, "buy" only
    its other orders (seeds, animals, land, hires)."""

    def __init__(self, other, half):
        super().__init__()
        from kagml.opponents import load
        self.other, self.half = load(other), half

    def warm_step(self, observation, configuration=None):
        self.module.agent(observation, configuration)

    def restore(self, memory):
        super().restore(memory)
        self.other.reset()

    def __call__(self, observation, configuration=None):
        import copy
        ours = dict(self.module.agent(copy.deepcopy(observation), configuration))
        theirs = self.other(copy.deepcopy(observation), configuration) or {}
        if self.half in ("sell", "buy"):   # only their SELL orders, or only their other orders; theirs listed first
            is_sell = lambda o: bool(o) and o[0] == "SELL"
            want = is_sell if self.half == "sell" else (lambda o: not is_sell(o))
            ours["market"] = ([o for o in theirs.get("market") or [] if want(o)]
                              + [o for o in ours.get("market") or [] if not want(o)])
            return ours
        keys = ("farmer", "hands") if self.half == "units" else ("market",)
        for k in keys:
            ours[k] = theirs.get(k, [] if k != "farmer" else ["PASS"])
        return ours


def make_player(name):
    if name.startswith("mix:"):      # mix:<agent>:units or mix:<agent>:market
        _, other, half = name.split(":")
        return Mix(other, half)
    if name.startswith("net:"):      # net:<model dir>[:dA-B], the whole-board network
        from kagml.net_player import NetPlayer
        return NetPlayer(name.split(":", 1)[1])
    if name.startswith("model"):
        from kagml.model_player import ModelPlayer
        return ModelPlayer(name.split(":", 1)[1] if ":" in name else "ranker-v1")
    if name == "template:nodawnseeds":
        return TemplatePlayer(Path(__file__).resolve().parents[1] / "agents/template_switches/main.py")
    if name in ("template", "recorded"):
        return TemplatePlayer() if name == "template" else "recorded"
    from kagml.opponents import load   # Codex's loader for the published agents
    return load(name)


def goods_value(private, prices):
    return sum((private["shed"].get(k, 0) + sum(b.get(k, 0) for b in private["inventories"])) * prices.get(k, 0)
               for k in PRODUCTS)


PRODUCT_OF = {"GOOSE": "EGG", "COW": "MILK", "SHEEP": "WOOL"}


def on_farm_value(tiles, prices):
    """Goods already produced but still on the farm: units held on plants and by animals, at current prices."""
    return sum(t.get("yield_units", 0) * prices.get(t.get("crop") or PRODUCT_OF.get(t.get("animal")), 0) for t in tiles)


SEED_COST = {"WHEAT": 10, "CARROT": 20, "TOMATO": 50, "STRAWBERRY": 100, "MELON": 80}
ANIMAL_COST = {"GOOSE": 300, "COW": 400, "SHEEP": 500}
LAND_COST = [1000, 2000, 4000]


def assets_at_cost(farm, private):
    """What was bought and is still held, at purchase price: animals (placed or in the shed), seeds, crops in the
    ground (at seed cost), land. Lets a day that invests compare fairly with a day that does not."""
    tiles = [t for row in farm["tiles"] for t in row if isinstance(t, dict)]
    value = sum(ANIMAL_COST.get(t.get("animal"), 0) + SEED_COST.get(t.get("crop"), 0) for t in tiles)
    value += sum(private["shed"].get(a, 0) * c for a, c in ANIMAL_COST.items())
    value += sum(b.get(a, 0) * c for b in private["inventories"] for a, c in ANIMAL_COST.items())
    value += sum(private["seeds"].get(s, 0) * c for s, c in SEED_COST.items())
    return value + sum(LAND_COST[:len(farm.get("unlocked_quadrants") or []) - 1])   # the first quadrant is free


def run_day(snap, player, replay, day, turns=24, SEAT=0):
    """Play `turns` turns from the snapshot for our seat; flags are read on the last turn, before midnight."""
    env = env_from_snapshot(snap)
    start = snap["step"]
    issued = Counter()
    late = None
    for i in range(start + 1, start + turns + 1):
        if i == start + turns:   # last turn of the day: read today's flags before midnight resets them
            obs = env.state[0].observation
            tiles = [t for row in obs.farms[SEAT].tiles for t in row if isinstance(t, dict)]
            late = {"planted": sum(t.get("kind") == "PLANT" and t.get("planted_day") == day for t in tiles),
                    "fed_cared": sum(bool(t.get("animal")) and t.get("fed_today") and t.get("cared_today") for t in tiles)}
        ours = (replay["steps"][i][SEAT]["action"] if player == "recorded"
                else player(env.state[SEAT].observation, env.configuration))
        theirs = replay["steps"][i][1 - SEAT]["action"]
        for cmd in [ours.get("farmer")] + list(ours.get("hands") or []) if isinstance(ours, dict) else []:
            if isinstance(cmd, list) and cmd and cmd[0] in COUNTED:
                issued[cmd[0]] += 1
        env.step([ours, theirs] if SEAT == 0 else [theirs, ours])
    obs = env.state[0].observation
    prices = dict(obs.market.prices)
    farm = obs.farms[SEAT]
    tiles = [t for row in farm.tiles for t in row if isinstance(t, dict)]
    cash0 = snap["obs"][0]["farms"][SEAT]["money"]
    opp0 = snap["obs"][0]["farms"][1 - SEAT]["money"]
    goods = goods_value(env.state[SEAT].observation.private, prices)
    goods0 = goods_value(snap["obs"][SEAT]["private"], prices)
    tiles0 = [t for row in snap["obs"][0]["farms"][SEAT]["tiles"] for t in row if isinstance(t, dict)]
    farm_goods, farm_goods0 = on_farm_value(tiles, prices), on_farm_value(tiles0, prices)
    row = {"cash_change": farm.money - cash0, "goods": round(goods), "value_change": round(farm.money - cash0 + goods - goods0 + farm_goods - farm_goods0), "on_farm": round(farm_goods),
           "opp_cash_change": obs.farms[1 - SEAT].money - opp0,
           "crops": sum(t.get("kind") == "PLANT" for t in tiles), "animals": sum(bool(t.get("animal")) for t in tiles)}
    row["assets_change"] = (assets_at_cost(farm, env.state[SEAT].observation.private)
                            - assets_at_cost(snap["obs"][0]["farms"][SEAT], snap["obs"][SEAT]["private"]))
    row["value_plus_assets"] = row["value_change"] + row["assets_change"]
    row.update(late or {})
    row.update({f"n_{k.lower()}": issued[k] for k in COUNTED})
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("games", nargs="+")
    ap.add_argument("--players", default="template,recorded")
    ap.add_argument("--days", default="8,12,16,20,24")
    ap.add_argument("--turns", type=int, default=24, help="turns per preview (24 = one day)")
    ap.add_argument("--sub", help="Kaggle replays: take over the seat this submission played")
    ap.add_argument("--pinned", action="store_true", help="our own runs (weed draw pinned); omit for Kaggle replays")
    a = ap.parse_args()
    pin_weeds(a.pinned)
    seat_of = {}
    if a.sub:   # Kaggle replays: our seat is the one the given submission played
        for r in csv.DictReader(open(Path(__file__).resolve().parents[1] / "manifests" / "replays.csv")):
            if a.sub in (r["sub_0"], r["sub_1"]):
                seat_of[r["episode"]] = 0 if r["sub_0"] == a.sub else 1
    days = [int(d) for d in a.days.split(",")]
    names = a.players.split(",")
    out = runs() / "compare" / f"{a.tag}.csv"
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in a.games:
        replay = json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path))
        episode = Path(path).name.split(".")[0]
        SEAT = seat_of.get(episode, 0) if a.sub else 0
        players = {n: make_player(n) for n in names}
        memories = {}
        t = time.perf_counter()
        for n, pl in players.items():          # warm each memory-keeping player once, up to the last morning used
            if isinstance(pl, TemplatePlayer):
                memories[n] = {}
                done = 0
                for d in days:
                    for i in range(done, d * 24):
                        obs = replay["steps"][i][SEAT]["observation"]
                        obs.setdefault("step", i)   # Kaggle replays omit step from the second seat's observation
                        getattr(pl, "warm_step", pl)(obs, replay.get("configuration"))
                    done = d * 24
                    memories[n][d] = pl.memory()
        for d in days:
            snap = snapshot_from_replay(replay, d * 24)
            for n, pl in players.items():
                if n in memories:
                    pl.restore(memories[n][d])
                row = {"game": episode, "day": d, "player": n, "seat": SEAT, **run_day(snap, pl, replay, d, a.turns, SEAT)}
                rows.append(row)
        print(f"{episode} (seat {SEAT}): {len(days)} mornings x {len(names)} players in {time.perf_counter() - t:.1f}s")
    with out.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"{len(rows)} rows -> {out}")


if __name__ == "__main__":
    main()

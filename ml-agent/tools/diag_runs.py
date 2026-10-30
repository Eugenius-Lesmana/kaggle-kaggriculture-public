"""Diagnostics D1-D3: record one day turn by turn for several players from the same mornings.

python tools/diag_runs.py <tag> --games 10315,10316 --days 6-28 --players template,model:ranker-own-v1-diag,fourth
Analysis games only (10315-10319); never the test games 10320-10324.
Writes <data>/runs/diag/<tag>/<game>-d<day>-<player>.json.gz with, per turn: hour, each worker's position, command,
bag contents; and per hour: every tile's state (compact) and the value so far. Run with PYTHONHASHSEED=0.
The 4th-place agent is a fresh, seed-reset instance for every morning (as in L1).
"""
import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from compare_day import assets_at_cost, goods_value, make_player, on_farm_value  # noqa: E402
from kagml.paths import runs  # noqa: E402
from kagml.preview import TemplatePlayer, env_from_snapshot, pin_weeds, snapshot_from_replay  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402

EL3 = REPO.parent / "Kaggle-Kaggriculture" / ".scratch" / "template-bench" / "runs" / "el3"
TEST = {10320, 10321, 10322, 10323, 10324}


def tile_sig(t):
    if not isinstance(t, dict):
        return t
    return "|".join(str(t.get(k)) for k in ("kind", "crop", "animal", "yield_units", "watered_today", "fed_today",
                                            "cared_today", "fertilized_until_day", "consecutive_unwatered"))


def value_now(obs, snap0):
    farm, priv = obs["farms"][0], obs["private"]
    prices = obs["market"]["prices"]
    tiles = [t for row in farm["tiles"] for t in row if isinstance(t, dict)]
    return round(farm["money"] + goods_value(priv, prices) + on_farm_value(tiles, prices) + assets_at_cost(farm, priv))


def trace_day(snap, player, replay, day, seed):
    env = env_from_snapshot(snap)
    start = snap["step"]
    if hasattr(player, "reset") and not isinstance(player, TemplatePlayer):
        player.reset(seed)
    turns, hours = [], []
    for i in range(start + 1, start + 25):
        obs = env.state[0].observation
        if obs["hour"] % 1 == 0:
            hours.append({"hour": obs["hour"], "value": value_now(obs, snap),
                          "tiles": [tile_sig(t) for row in obs["farms"][0]["tiles"] for t in row]})
        action = player(obs, env.configuration)
        farm = obs["farms"][0]
        pos = [list(farm["farmer"])] + [list(h) for h in farm["hands"]]
        cmds = [action.get("farmer")] + list(action.get("hands") or [])
        turns.append({"step": i - 1, "hour": obs["hour"], "pos": pos, "cmd": cmds,
                      "bags": [dict(b) for b in obs["private"]["inventories"]],
                      "shed": dict(obs["private"]["shed"]), "market": action.get("market") or []})
        env.step([action, replay["steps"][i][1]["action"]])
    obs = env.state[0].observation
    hours.append({"hour": 24, "value": value_now(obs, snap),
                  "tiles": [tile_sig(t) for row in obs["farms"][0]["tiles"] for t in row]})
    return {"turns": turns, "hours": hours}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tag")
    ap.add_argument("--games", default="10315,10316,10317,10318,10319")
    ap.add_argument("--days", default="6-28")
    ap.add_argument("--players", default="template,model:ranker-own-v1-diag,fourth")
    a = ap.parse_args()
    games = [int(g) for g in a.games.split(",")]
    assert not TEST & set(games), "test games are off limits for diagnostics"
    lo, hi = (int(x) for x in a.days.split("-"))
    days = list(range(lo, hi + 1))
    pin_weeds(True)
    out = runs() / "diag" / a.tag
    out.mkdir(parents=True, exist_ok=True)
    for game in games:
        replay = load_replay(EL3 / f"{game}.json")
        seed = replay["info"]["seed"]
        for name in a.players.split(","):
            if all((out / f"{game}-d{d}-{name.replace(':', '_')}.json.gz").exists() for d in days):
                continue
            pl = make_player(name)
            memories, done = {}, 0
            if isinstance(pl, TemplatePlayer):          # warm memory once, up to each morning
                for d in days:
                    for i in range(done, d * 24):
                        obs = replay["steps"][i][0]["observation"]
                        obs.setdefault("step", i)
                        getattr(pl, "warm_step", pl)(obs, replay.get("configuration"))
                    done = d * 24
                    memories[d] = pl.memory()
            for d in days:
                target = out / f"{game}-d{d}-{name.replace(':', '_')}.json.gz"
                if target.exists():
                    continue
                if d in memories:
                    pl.restore(memories[d])
                rec = trace_day(snapshot_from_replay(replay, d * 24), pl, replay, d, seed)
                with gzip.open(target, "wt") as fh:
                    json.dump({"game": game, "day": d, "player": name, **rec}, fh)
            print(game, name, flush=True)


if __name__ == "__main__":
    main()

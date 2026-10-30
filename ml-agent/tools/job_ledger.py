"""Field-job ledger: every job each player does, with the state of the tile at that moment (analysis mornings).

python tools/job_ledger.py d1
Replays the diag_runs recordings exactly through the engine (as diag_night.py does) and, for every job command that
takes effect, records the tile's state just before it: crop or animal, days dry, whether the crop dies or produces
tonight (double if fertilized), units waiting, fertilized or not, animal fed/cared, production night, escape risk,
the hour, and the worker. Prints per-day counts by job type and by the state of the tile, for each player.
"""
import copy
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from diag_night import EL3, NAMES  # noqa: E402
from kagml.paths import runs  # noqa: E402
from kagml.preview import env_from_snapshot, pin_weeds, snapshot_from_replay  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402
import kaggle_environments.envs.kaggriculture.kaggriculture as K  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST", "PASS"}
FIELD = ("WATER", "FERTILIZE", "HARVEST", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER", "DIG", "BUILD_COOP", "BUILD_PASTURE")


def tile_state(t, day):
    """What matters about a tile for the job done on it, under the engine's overnight rules."""
    if not isinstance(t, dict):
        return {"on": "EMPTY" if t is None else str(t)}
    if t.get("kind") == "PLANT":
        c = K.CROPS[t["crop"]]
        ds = day + 1 - t["planted_day"] - c["first_yield_day"]
        prod = c["ongoing"] and ds >= 0 and ds % c["interval"] == 0 and ds // c["interval"] + 1 <= c["max_yield"]
        return {"on": t["crop"], "dry_days": t.get("consecutive_unwatered", 0), "watered": t.get("watered_today", False),
                "dies_tonight": (not t.get("watered_today")) and t.get("consecutive_unwatered", 0) >= 1,
                "prod_tonight": prod, "fertilized": t.get("fertilized_until_day", -1) >= day,
                "waiting": t.get("yield_units", 0), "max_yield": c["max_yield"]}
    if t.get("animal"):
        a = K.ANIMALS[t["animal"]]
        ds = day + 1 - t["placed_day"] - a["first_yield_day"]
        return {"on": t["animal"], "fed": t.get("fed_today", False), "cared": t.get("cared_today", False),
                "prod_tonight": ds >= 0 and ds % a["interval"] == 0,
                "escapes_tonight": (not t.get("fed_today")) and t.get("consecutive_unfed", 0) >= 1,
                "waiting": t.get("yield_units", 0), "max_yield": a["max_held"]}
    return {"on": t.get("kind")}


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "d1"
    pin_weeds(True)
    rows, replays = [], {}
    for f in sorted((runs() / "diag" / tag).glob("*.json.gz")):
        rec = json.load(gzip.open(f, "rt"))
        who = NAMES.get(rec["player"], rec["player"])
        if who not in ("template", "v3-diag", "net-v4g", "teacher"):
            continue
        replay = replays.setdefault(rec["game"], load_replay(EL3 / f"{rec['game']}.json"))
        snap = snapshot_from_replay(replay, rec["day"] * 24)
        env = env_from_snapshot(snap)
        start = snap["step"]
        for k, t in enumerate(rec["turns"]):
            obs = env.state[0].observation
            farm = obs["farms"][0]
            before = copy.deepcopy(farm["tiles"])
            pos = [tuple(farm["farmer"])] + [tuple(h) for h in farm["hands"]]
            cmds = t["cmd"]
            env.step([{"farmer": cmds[0], "hands": cmds[1:], "market": t["market"]}, replay["steps"][start + 1 + k][1]["action"]])
            after = env.state[0].observation["farms"][0]["tiles"]
            for u, c in enumerate(cmds):
                if not c or c[0] in MOVES or c[0] not in FIELD or u >= len(pos):
                    continue
                x, y = pos[u]
                took = json.dumps(before[y][x], sort_keys=True, default=str) != json.dumps(after[y][x], sort_keys=True, default=str)
                rows.append({"player": who, "game": rec["game"], "day": rec["day"], "hour": obs["hour"], "unit": u,
                             "job": c[0] + (":" + c[1] if c[0] == "PLANT" else ""), "took": took, **tile_state(before[y][x], rec["day"])})
    d = pd.DataFrame(rows)
    out = runs() / "diag" / f"{tag}-summary"
    d.to_csv(out / "job_ledger.csv.gz", index=False)
    m = d.groupby("player").apply(lambda g: g[["game", "day"]].drop_duplicates().shape[0])
    order = [p for p in ("template", "v3-diag", "net-v4g", "teacher") if p in m.index]
    pd.set_option("display.width", 220)
    per = lambda df, by: (df.groupby(["player"] + by).size().unstack(0).div(m, axis=1)[order]).round(2)
    e = d[d.took]
    print("== Jobs per day by type (that took effect)")
    print(per(e.assign(kind=e.job.str.split(":").str[0]), ["kind"]))
    w = e[e.job == "WATER"].copy()
    w["state"] = w.apply(lambda r: "dies tonight" if r.dies_tonight else ("produces tonight" + (" (fertilized)" if r.fertilized else "") if r.prod_tonight else "routine"), axis=1)
    print("\n== WATER per day, by crop"); print(per(w, ["on"]))
    print("\n== WATER per day, by what was at stake tonight"); print(per(w, ["state"]))
    fz = e[e.job == "FERTILIZE"].copy()
    print("\n== FERTILIZE per day, by crop"); print(per(fz, ["on"]))
    fz["when"] = fz.apply(lambda r: "produces tonight" if r.prod_tonight else "not tonight", axis=1)
    print("\n== FERTILIZE per day, producing tonight or not"); print(per(fz, ["when"]))
    h = e[e.job == "HARVEST"].copy()
    print("\n== HARVEST per day, by crop / animal product"); print(per(h, ["on"]))
    h["fill"] = (h.waiting / h.max_yield).clip(0, 1)
    print("\n== HARVEST: share of the maximum waiting when harvested (mean)")
    print(h.groupby(["on", "player"]).fill.mean().unstack()[order].round(2))
    fd = e[e.job.isin(["FEED", "CARE"])].copy()
    fd["state"] = fd.apply(lambda r: "escapes tonight" if r.get("escapes_tonight") is True else ("production night" if r.prod_tonight else "no production tonight"), axis=1)
    print("\n== FEED and CARE per day, by stake"); print(per(fd.assign(k=fd.job + " / " + fd.state), ["k"]))
    pl = e[e.job.str.startswith("PLANT")]
    print("\n== PLANT per day, by crop"); print(per(pl, ["job"]))
    print("\n== Job commands that did not take effect, per day"); print(per(d[~d.took].assign(kind=d.job.str.split(":").str[0]), ["kind"]))


if __name__ == "__main__":
    main()

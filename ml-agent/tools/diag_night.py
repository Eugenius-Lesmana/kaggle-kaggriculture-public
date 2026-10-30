"""Two checks on the diag_runs recordings (analysis games only), by replaying the recorded actions exactly:

1. Split the overnight value change (hour 23 -> next dawn) into real change (cash, units of goods and produce valued
   at the hour-23 prices, purchases at cost) and price change (units held at dawn x the overnight price move).
2. Which animals and crops each player leaves unfed / uncared / unwatered at hour 23, and whether skipping them
   was free under the engine's rules: an animal only escapes after 2 unfed days in a row and only produces on its
   production days; a crop only dies after 2 unwatered days in a row; ongoing crops only produce on set days, and
   fertilizer only doubles a yield on a watered production day.

python tools/diag_night.py d1
"""
import gzip
import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from compare_day import ANIMAL_COST, PRODUCT_OF, assets_at_cost  # noqa: E402
from kagml.paths import runs  # noqa: E402
from kagml.preview import env_from_snapshot, pin_weeds, snapshot_from_replay  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402
import kaggle_environments.envs.kaggriculture.kaggriculture as K  # noqa: E402

EL3 = REPO.parent / "Kaggle-Kaggriculture" / ".scratch" / "template-bench" / "runs" / "el3"
NAMES = {"template": "template", "model:ranker-own-v1-diag": "v2-diag", "fourth": "teacher", "model:ranker-v3s-fw": "v3-diag", "net:board-v1": "net-v1", "net:board-v4:guard": "net-v4g"}
PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")


def units(obs):
    """Units of each product held (shed, bags) and waiting on the farm."""
    u = {p: obs["private"]["shed"].get(p, 0) + sum(b.get(p, 0) for b in obs["private"]["inventories"]) for p in PRODUCTS}
    for row in obs["farms"][0]["tiles"]:
        for t in row:
            if isinstance(t, dict) and t.get("yield_units"):
                p = t.get("crop") or PRODUCT_OF.get(t.get("animal"))
                u[p] = u.get(p, 0) + t["yield_units"]
    return u


def replay_day(rec, replay):
    """Re-run the recorded day exactly; return the observations at hour 23 (before its action) and next dawn."""
    snap = snapshot_from_replay(replay, rec["day"] * 24)
    env = env_from_snapshot(snap)
    start = snap["step"]
    at23 = None
    for k, t in enumerate(rec["turns"]):
        if k == 23:
            at23 = json.loads(json.dumps(env.state[0].observation, default=dict))
        cmds = t["cmd"]
        ours = {"farmer": cmds[0], "hands": cmds[1:], "market": t["market"]}
        env.step([ours, replay["steps"][start + 1 + k][1]["action"]])
    return at23, json.loads(json.dumps(env.state[0].observation, default=dict))


def skipped(obs, day):
    out = []
    next_day = day + 1
    for y, row in enumerate(obs["farms"][0]["tiles"]):
        for x, t in enumerate(row):
            if not isinstance(t, dict):
                continue
            dist = abs(x - 4) + abs(y - 4)
            if t.get("animal"):
                a = K.ANIMALS[t["animal"]]
                ds = next_day - t["placed_day"] - a["first_yield_day"]
                out.append({"what": t["animal"], "kind": "animal", "unfed": not t["fed_today"],
                            "uncared": not t["cared_today"], "safe_one_day": t["consecutive_unfed"] == 0,
                            "production_night": ds >= 0 and ds % a["interval"] == 0,
                            "full": t["yield_units"] >= a["max_held"], "dist_shed": dist})
            elif t.get("kind") == "PLANT":
                c = K.CROPS[t["crop"]]
                ds = next_day - t["planted_day"] - c["first_yield_day"]
                prod = c["ongoing"] and ds >= 0 and ds % c["interval"] == 0 and ds // c["interval"] + 1 <= c["max_yield"]
                out.append({"what": t["crop"], "kind": "crop", "unwatered": not t["watered_today"],
                            "safe_one_day": t["consecutive_unwatered"] == 0, "production_night": prod,
                            "fertilized": t.get("fertilized_until_day", -1) >= day, "dist_shed": dist})
    return out


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "d1"
    pin_weeds(True)
    parts, skips, replays = [], [], {}
    for f in sorted((runs() / "diag" / tag).glob("*.json.gz")):
        rec = json.load(gzip.open(f, "rt"))
        g, day, who = rec["game"], rec["day"], NAMES[rec["player"]]
        replay = replays.setdefault(g, load_replay(EL3 / f"{g}.json"))
        o23, o24 = replay_day(rec, replay)
        p23, p24 = o23["market"]["prices"], o24["market"]["prices"]
        u23, u24 = units(o23), units(o24)
        cash = o24["farms"][0]["money"] - o23["farms"][0]["money"]
        produce = sum((u24[p] - u23[p]) * p23[p] for p in PRODUCTS)
        assets = assets_at_cost(o24["farms"][0], o24["private"]) - assets_at_cost(o23["farms"][0], o23["private"])
        price = sum(u24[p] * (p24[p] - p23[p]) for p in PRODUCTS)
        parts.append({"game": g, "day": day, "player": who, "cash": cash, "produce_at_old_prices": produce,
                      "assets": assets, "real": cash + produce + assets, "price_move": price})
        for s in skipped(o23, day):
            skips.append({"game": g, "day": day, "player": who, **s})
    P, S = pd.DataFrame(parts), pd.DataFrame(skips)
    out = runs() / "diag" / f"{tag}-summary"
    P.to_csv(out / "night_parts.csv", index=False)
    S.to_csv(out / "night_skips.csv.gz", index=False)
    pd.set_option("display.width", 220)
    print("== Check 1: overnight value change split (mean per morning)")
    order = [q for q in ("template", "v3-diag", "net-v1", "net-v4g", "teacher") if q in set(P.player)]
    print(P.groupby("player")[["cash", "produce_at_old_prices", "assets", "real", "price_move"]].mean().T[order].round(0))
    for c in ["real", "price_move", "produce_at_old_prices"]:
        p = P.pivot_table(index=["game", "day"], columns="player", values=c)
        print(f"  {c:22s}" + "".join(f"  {q}-teacher {(p[q] - p['teacher']).mean():7.0f} ({(p[q] - p['teacher']).sem():.0f})" for q in order if q != "teacher"))
    report_skips(S)


def report_skips(S, mornings=115):
    for c in ("unfed", "uncared", "safe_one_day", "production_night", "full", "unwatered", "fertilized"):
        if c in S:
            S[c] = S[c].astype("boolean")
    A = S[S.kind == "animal"].copy()
    A["free"] = A.safe_one_day & ~A.production_night
    per = lambda df: (df.groupby("player").size() / mornings).reindex([q for q in ("template", "v3-diag", "net-v1", "net-v4g", "teacher") if q in set(S.player)]).round(2).to_dict()
    print("\n== Check 2a: animals at hour 23, per morning")
    print("  animals:", per(A))
    print("  unfed:", per(A[A.unfed]))
    print("    of which free to skip (fed yesterday, no production tonight):", per(A[A.unfed & A.free]))
    print("    unfed on a production night (production lost):", per(A[A.unfed & A.production_night]))
    print("    unfed a second day (animal escapes):", per(A[A.unfed & ~A.safe_one_day]))
    print("  fed but already full (feeding gave nothing that night):", per(A[~A.unfed & A.full]))
    print("  fed on a non-production night that was safe to skip:", per(A[~A.unfed & A.free]))
    print("  uncared while fed:", per(A[A.uncared & ~A.unfed]))
    C = S[S.kind == "crop"].copy()
    C["free"] = C.safe_one_day & ~C.production_night
    print("\n== Check 2b: crops at hour 23, per morning")
    print("  crops:", per(C))
    print("  unwatered:", per(C[C.unwatered]))
    print("    of which free to skip (watered yesterday, no production tonight):", per(C[C.unwatered & C.free]))
    print("    unwatered on a production night:", per(C[C.unwatered & C.production_night]))
    print("      of which fertilized (double yield lost):", per(C[C.unwatered & C.production_night & C.fertilized]))
    print("    unwatered a second day (crop dies):", per(C[C.unwatered & ~C.safe_one_day]))
    print("  watered although free to skip:", per(C[~C.unwatered & C.free]))

if __name__ == "__main__":
    main()

"""Analyse the diag_runs recordings (analysis games only): D1 drift by hour, D2 jobs on the way and shed use,
D3 coordination. Paired by morning; means with standard errors.

python tools/diag_analyse.py d1
"""
import gzip
import itertools
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import runs  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
SHED_ITEMS = ("PICKUP", "DROP")
NAMES = {"template": "template", "model:ranker-own-v1-diag": "v2-diag", "fourth": "teacher", "model:ranker-v3s-fw": "v3-diag", "net:board-v1": "net-v1", "net:board-v4:guard": "net-v4g"}


def d(p, q):
    return abs(p[0] - q[0]) + abs(p[1] - q[1])


def worker_seqs(turns):
    """Per worker: list of (turn index, position, command)."""
    seqs = defaultdict(list)
    for k, t in enumerate(turns):
        for u, (p, c) in enumerate(zip(t["pos"], t["cmd"])):
            seqs[u].append((k, tuple(p), c if isinstance(c, list) and c else ["PASS"]))
    return seqs


def day_stats(rec):
    turns = rec["turns"]
    seqs = worker_seqs(turns)
    s = defaultdict(float)
    tiles_by_worker = {}
    for u, seq in seqs.items():
        jobs = [(k, p, c) for k, p, c in seq if c[0] not in MOVES and c[0] != "PASS"]
        s["worker_turns"] += len(seq)
        s["jobs"] += len(jobs)
        s["moves"] += sum(c[0] in MOVES for _, _, c in seq)
        s["pass"] += sum(c[0] == "PASS" for _, _, c in seq)
        tiles_by_worker[u] = {p for _, p, _ in seq}
        field = [(k, p, c) for k, p, c in jobs if c[0] not in SHED_ITEMS and c[0] != "PLACE"]
        for (k0, p0, _), (k1, p1, c1), (k2, p2, _) in zip(field, field[1:], field[2:]):
            if d(p0, p2) >= 3 and p1 not in (p0, p2):
                s["trip_jobs"] += 1
                s["on_the_way"] += d(p0, p1) + d(p1, p2) <= d(p0, p2) + 2
        for k, p, c in jobs:
            if c[0] == "PICKUP":
                s["pickups"] += 1
                s[f"pickup_amount_{c[1]}"] += int(c[2]) if len(c) > 2 else 1
                s[f"pickups_{c[1]}"] += 1
            elif c[0] == "DROP":
                s["drops"] += 1
            elif c[0] == "PLACE" and len(c) > 1 and c[1] not in ("GOOSE", "COW", "SHEEP"):
                s["places"] += 1
    s["carried_per_worker_turn"] = sum(sum(b.values()) for t in turns for b in t["bags"]) / max(1, s["worker_turns"])
    ws = [w for w in tiles_by_worker.values() if len(w) > 1]
    s["tiles_per_worker"] = np.mean([len(w) for w in ws]) if ws else np.nan
    jac = [len(a & b) / len(a | b) for a, b in itertools.combinations(ws, 2)]
    s["area_overlap"] = np.mean(jac) if jac else np.nan
    near = 0
    for t in turns:
        ps = [tuple(p) for p in t["pos"] if d(tuple(p), (4, 4)) > 2]       # ignore the crowd around the shed
        near += sum(d(a, b) <= 1 for a, b in itertools.combinations(ps, 2))
    s["near_pairs_per_turn"] = near / len(turns)
    worked = defaultdict(set)
    for u, seq in seqs.items():
        for k, p, c in seq:
            if c[0] in ("WATER", "HARVEST", "FERTILIZE", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER"):
                worked[p].add(u)
    s["tiles_shared_by_workers"] = sum(len(v) > 1 for v in worked.values()) / max(1, len(worked))
    return s


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "d1"
    folder = runs() / "diag" / tag
    recs = {}
    for f in sorted(folder.glob("*.json.gz")):
        r = json.load(gzip.open(f, "rt"))
        recs[(r["game"], r["day"], NAMES.get(r["player"], r["player"]))] = r
    mornings = sorted({(g, dd) for g, dd, _ in recs})
    players = [p for p in ("template", "v3-diag", "net-v1", "net-v4g", "teacher") if any(k[2] == p for k in recs)]
    print(f"{len(mornings)} mornings, players {players}")

    # D1: value gained by hour, and how many tiles differ from the teacher's farm at the same hour
    rows = []
    for g, dd in mornings:
        t_hours = recs[(g, dd, "teacher")]["hours"]
        for p in players:
            hrs = recs[(g, dd, p)]["hours"]
            v0 = hrs[0]["value"]
            for h, th in zip(hrs, t_hours):
                diff = sum(a != b for a, b in zip(h["tiles"], th["tiles"]))
                rows.append({"game": g, "day": dd, "player": p, "hour": h["hour"], "gain": h["value"] - v0,
                             "tiles_diff_vs_teacher": diff})
    D1 = pd.DataFrame(rows)
    piv = D1.pivot_table(index=["game", "day", "hour"], columns="player", values="gain")
    gap = pd.DataFrame({f"{q} - teacher": piv[q] - piv["teacher"] for q in players if q != "teacher"}).groupby("hour").agg(["mean", "sem"]).round(0)
    print("\n== D1: value gained since dawn, minus the teacher's, by hour (mean, standard error)")
    print(gap.loc[[4, 8, 12, 16, 20, 24]])
    td = D1.pivot_table(index="hour", columns="player", values="tiles_diff_vs_teacher").round(1)
    print("\n== D1: tiles that differ from the teacher's farm at the same hour (of 100)")
    print(td.loc[[1, 4, 8, 12, 16, 20, 24], [q for q in players if q != "teacher"]])

    # D2 and D3: per morning and player
    stats = pd.DataFrame([{"game": g, "day": dd, "player": p, **day_stats(recs[(g, dd, p)])}
                          for g, dd in mornings for p in players])
    per = stats.groupby("player")
    show = lambda cols: per[cols].mean().T[players].round(2)
    stats["on_the_way_share"] = stats.on_the_way / stats.trip_jobs
    stats["jobs_per_worker_turn"] = stats.jobs / stats.worker_turns
    stats["moves_per_job"] = stats.moves / stats.jobs
    for c in [c for c in stats if c.startswith("pickup_amount_")]:
        item = c.split("_")[-1]
        stats[f"per_pickup_{item}"] = stats[c] / stats[f"pickups_{item}"].replace(0, np.nan)
    per = stats.groupby("player")
    print("\n== D2: work and walking (per morning)")
    print(per[["worker_turns", "jobs", "moves", "pass", "jobs_per_worker_turn", "moves_per_job"]].mean().T[players].round(2))
    print("\n== D2: jobs on the way (share of field jobs, between two other jobs at least 3 tiles apart, within one step of the route)")
    print(per[["trip_jobs", "on_the_way", "on_the_way_share"]].mean().T[players].round(3))
    print("\n== D2: shed use (per morning)")
    cols = ["pickups", "drops", "places", "carried_per_worker_turn"] + sorted(c for c in stats if c.startswith("per_pickup_"))
    print(per[cols].mean().T[players].round(2))
    print("\n== D3: coordination (per morning)")
    print(per[["tiles_per_worker", "area_overlap", "near_pairs_per_turn", "tiles_shared_by_workers"]].mean().T[players].round(3))
    # paired differences with standard errors for the key measures
    print("\n== Paired differences (v2-diag minus teacher; template minus teacher): mean (standard error)")
    for c in ["jobs", "moves", "on_the_way_share", "pickups", "drops", "carried_per_worker_turn", "tiles_per_worker",
              "area_overlap", "near_pairs_per_turn", "tiles_shared_by_workers"]:
        p = stats.pivot_table(index=["game", "day"], columns="player", values=c)
        print(f"  {c:26s}" + "".join(f"  {q} {(p[q] - p['teacher']).mean():8.3f} ({(p[q] - p['teacher']).sem():.3f})" for q in players if q != "teacher"))
    out = runs() / "diag" / f"{tag}-summary"
    out.mkdir(parents=True, exist_ok=True)
    D1.to_csv(out / "d1_hourly.csv.gz", index=False)
    stats.to_csv(out / "d2_d3_per_morning.csv", index=False)


if __name__ == "__main__":
    main()

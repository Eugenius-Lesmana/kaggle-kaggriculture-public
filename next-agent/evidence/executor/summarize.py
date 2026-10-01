"""Summarize measure.py output: paired ratio changes vs skel, execution in days 0-5 / 6-11,
the farm at day 12, and the route-follower's visit diagnostics.

  python evaluation/executor/summarize.py RAW.json[.gz] [--reference evaluation/executor/team_a_reference.json] --out SUMMARY.json
"""
import argparse, gzip, json, math
from collections import Counter

OPS = ("WATER", "HARVEST", "PLANT", "FEED", "CARE", "COLLECT_FERTILIZER", "FERTILIZE", "DIG", "BUILD", "PLACE_ANIMAL")
DAY12 = ("crops", "animals", "empty", "weeds", "empty_structures", "quadrants", "money", "shed_value")
VISITS = ("visits_served", "visits_skipped_nothing", "visits_arrived_nothing", "visits_locked",
          "visits_abandoned", "visits_unreached")


def mean_ci(values):
    n = len(values)
    m = sum(values) / n
    sd = math.sqrt(sum((v - m) ** 2 for v in values) / (n - 1)) if n > 1 else 0.0
    return round(m, 4), round(1.96 * sd / math.sqrt(n), 4)


def execution(rows, phase):
    c = Counter()
    for r in rows:
        c.update(r["execution"][phase])
    n, steps = len(rows), c["worker_steps"] or 1
    out = {op: round(c[op + " ok"] / n, 1) for op in OPS}
    out.update(productive=round(c["productive"] / n, 1),
               productive_excl_unneeded_water=round((c["productive"] - c["WATER unneeded"]) / n, 1),
               water_unneeded=round(c["WATER unneeded"] / n, 1),
               failed=round(c["failed"] / n, 1), shed_ops=round(c["shed_op"] / n, 1),
               worker_steps=round(c["worker_steps"] / n, 1),
               idle_share=round(c["idle"] / steps, 3), move_share=round(c["move"] / steps, 3))
    return out


def day12(rows):
    c = Counter()
    for r in rows:
        c.update({k: v for k, v in r["day12"].items() if isinstance(v, (int, float))})
    return {k: round(c[k] / len(rows), 1) for k in DAY12} | {
        k: round(c[k] / len(rows), 1) for k in sorted(c) if k.startswith(("crop ", "animal "))}


def coverage(rows):
    rows = [r for r in rows if r.get("coverage_d6_11")]
    if not rows:
        return None
    c = Counter()
    for r in rows:
        c.update(r["coverage_d6_11"])
    return {"games": len(rows), **{k: round(v / len(rows), 1) for k, v in sorted(c.items())}}


def route(rows, days):
    c = Counter()
    for r in rows:
        for d, stats in r.get("route", {}).items():
            if int(d) in days:
                c.update(stats)
    if not c:
        return None
    reached = c["visits_served"] + c["visits_skipped_nothing"] + c["visits_arrived_nothing"]
    ops = c["route_op"] + c["fallback_op"]
    n = len(rows)
    return {"per_game": {k: round(c[k] / n, 1) for k in ("visits_total", *VISITS, "route_op", "route_wait",
                                                        "route_move", "fallback_op", "fallback_move", "fallback_idle")},
            "nothing_to_do_share": round((c["visits_skipped_nothing"] + c["visits_arrived_nothing"]) / reached, 3) if reached else None,
            "arrived_for_nothing_share": round(c["visits_arrived_nothing"] / reached, 3) if reached else None,
            "locked_share": round(c["visits_locked"] / c["visits_total"], 3) if c["visits_total"] else None,
            "unreached_share": round(c["visits_unreached"] / c["visits_total"], 3) if c["visits_total"] else None,
            "fallback_share_of_ops": round(c["fallback_op"] / ops, 3) if ops else None,
            "nothing_to_do_by_kind": {k[9:]: round(v / n, 1) for k, v in c.most_common() if k.startswith("nothing: ")}}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("raw", nargs="+")
    ap.add_argument("--reference")
    ap.add_argument("--control", default="skel")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    rows, opponents = [], []
    for path in a.raw:
        d = json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path))
        opponents.append(d["opponent"])
        rows.extend(d["rows"])
    arms = sorted({r["arm"] for r in rows}, key=lambda arm: (arm != a.control, arm))
    by = {(r["arm"], r["seed"], r["side"]): r for r in rows}
    keys = sorted({(r["seed"], r["side"]) for r in rows if all((arm, r["seed"], r["side"]) in by for arm in arms)})
    summary = {"opponents": opponents, "paired_games": len(keys), "control": a.control, "arms": {}}
    for arm in arms:
        rs = [by[(arm, *k)] for k in keys]
        ratio = mean_ci([r["ratio"] for r in rs])
        delta = mean_ci([by[(arm, *k)]["ratio"] - by[(a.control, *k)]["ratio"] for k in keys])
        left = [r["script_left_at"] for r in rs]
        summary["arms"][arm] = {
            "games": len(rs), "wins": sum(r["own"] > r["opp"] for r in rs),
            "mean_ratio": ratio, "ratio_change_vs_control": delta,
            "own_bank_change_vs_control": round(sum(by[(arm, *k)]["own"] / by[(a.control, *k)]["own"] - 1 for k in keys) / len(keys), 4),
            "mean_own_bank": round(sum(r["own"] for r in rs) / len(rs)), "mean_opp_bank": round(sum(r["opp"] for r in rs) / len(rs)),
            "opener_script_left_at": {"stayed_on_script": sum(v is None for v in left),
                                      "left_day0_1": sum(v is not None and v < 48 for v in left),
                                      "left_day2_5": sum(v is not None and v >= 48 for v in left)},
            "execution_d0_5": execution(rs, "d0_5"), "execution_d6_11": execution(rs, "d6_11"),
            "day12": day12(rs), "coverage_d6_11": coverage(rs), "route_d6_11": route(rs, range(6, 12)), "route_d0_5": route(rs, range(0, 6)),
            "seconds_per_game": round(sum(r["seconds"] for r in rs) / len(rs), 1)}
    if a.reference:
        ref = json.load(open(a.reference))["rows"]
        summary["reference"] = {"team": ref[0]["arm"], "games": len(ref),
                                "execution_d0_5": execution(ref, "d0_5"), "execution_d6_11": execution(ref, "d6_11"),
                                "day12": day12(ref), "coverage_d6_11": coverage(ref)}
    json.dump(summary, open(a.out, "w"), indent=1)
    cols = [(arm, summary["arms"][arm]) for arm in arms]
    if a.reference:
        cols.append((summary["reference"]["team"] + " (replays)", summary["reference"]))
    print(f"paired games: {len(keys)}  opponents: {opponents}")
    print("| metric | " + " | ".join(name for name, _ in cols) + " |")
    print("|---" * (len(cols) + 1) + "|")
    line = lambda label, f: print(f"| {label} | " + " | ".join(f(c) for _, c in cols) + " |")
    line("ratio vs opponent", lambda c: f"{c['mean_ratio'][0]:.3f} ± {c['mean_ratio'][1]:.3f}" if "mean_ratio" in c else "-")
    line("paired ratio change vs skel", lambda c: f"{c['ratio_change_vs_control'][0]:+.3f} ± {c['ratio_change_vs_control'][1]:.3f}" if "mean_ratio" in c else "-")
    for phase in ("execution_d6_11", "execution_d0_5"):
        for key in ("productive", "productive_excl_unneeded_water", *OPS, "failed", "idle_share", "move_share"):
            line(f"{phase[-5:]} {key}", lambda c: str(c[phase][key]))
    for key in summary["arms"][arms[0]]["day12"]:
        line(f"day 12 {key}", lambda c: str(c["day12"].get(key, 0)))
    for name, c in cols:
        if c.get("coverage_d6_11"):
            print("coverage d6-11", name, json.dumps(c["coverage_d6_11"]))
    r = summary["arms"].get("route", {}).get("route_d6_11")
    if r:
        print("\nroute d6-11:", json.dumps(r))


if __name__ == "__main__":
    main()

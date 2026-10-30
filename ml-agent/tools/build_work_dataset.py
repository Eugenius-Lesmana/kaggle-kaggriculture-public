"""Build a work-model dataset from top-team replays: per decision, the teacher's job plus sampled other candidates.

python tools/build_work_dataset.py <name> --subs 56711476,56722220,... --games-per-sub 10 --negatives 30
Writes <data>/datasets/work/<name>/<episode>.parquet (one file per game and seat) and a summary line per game.
Negatives: the 15 nearest other candidates plus 15 random ones, so the model sees both close calls and far jobs.
"""
import argparse
import json
import random
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import data_root  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from kagml.work_data import candidates, job_of, load_replay  # noqa: E402
from kagml.work_features import History, candidate_rows, context, dist  # noqa: E402


def game_rows(con, episode, seat, path, negatives, rng, history=None, offset=0, label_from=None):
    """Rows for one game (or one day segment: frame i is absolute step offset+i; `history` already warmed).
    With `label_from` (L3 takeovers), only decisions from that step on are kept: the teacher's, not our model's;
    every worker gets a fresh decision at the takeover."""
    replay = load_replay(path)
    steps = replay["steps"]
    acts = con.sql(f"select step, unit, x, y, command, took_effect from unit_actions where episode={episode} and seat={seat} order by step, unit").fetchall()
    sold = defaultdict(Counter)
    for step, product, units in con.sql(f"select step, product, sum(units) from sales where episode={episode} and seat={seat} group by step, product").fetchall():
        sold[step][product] += units
    by_unit = defaultdict(list)
    for step, unit, x, y, cmd, took in acts:
        by_unit[unit].append((step, x, y, cmd, took))
    # decision points per unit (as in work_data.decisions), with label and the unit's previous job
    decisions = defaultdict(list)          # step -> [(unit, label, last_kind, since_last)]
    for unit, rows in by_unit.items():
        jobs = [(s, job_of(cmd, x, y)) for s, x, y, cmd, took in rows if took and x is not None]
        jobs = [(s, j) for s, j in jobs if j is not None]
        present = {s for s, x, *_ in rows if x is not None}
        starts = {s for s in present if (s - 1) not in present or (s - 1) // 24 != s // 24} | {s + 1 for s, _ in jobs}
        if label_from is not None:
            starts = {s for s in starts if s >= label_from} | ({label_from} & present)
        k = 0
        for s in sorted(starts):
            while k < len(jobs) and jobs[k][0] < s:
                k += 1
            if k < len(jobs) and jobs[k][0] // 24 == s // 24 and s in present:
                prev = jobs[k - 1] if k > 0 and jobs[k - 1][0] // 24 == s // 24 else None
                decisions[s].append((unit, jobs[k][1], prev[1][0].split(":")[0] if prev else None, s - prev[0] if prev else 999))
    history, out = history or History(), []
    for s in range(offset, offset + len(steps) - 1):
        obs = steps[s - offset][seat]["observation"]
        obs.setdefault("step", s)
        history.add(obs, sold.get(s - 1, Counter()))
        if s not in decisions:
            continue
        ctx = context(obs, seat, history)
        for unit, label, last_kind, since in decisions[s]:
            cands = candidates(obs, seat, unit)
            if label not in cands:
                continue
            others = [c for c in sorted(cands, key=str) if c != label]   # fixed order (hash seed)
            pos = ctx["_positions"][unit] if unit < len(ctx["_positions"]) else ctx["_positions"][0]
            near = sorted(others, key=lambda c: dist(pos, (4, 4) if c[1] == "SHED" else (c[1] % 10, c[1] // 10)))[:negatives // 2]
            rest = [c for c in others if c not in set(near)]
            chosen = [label] + near + rng.sample(rest, min(len(rest), negatives - len(near)))
            rows = candidate_rows(obs, seat, unit, chosen, ctx, last_kind, since)
            for i, r in enumerate(rows):
                r.update({"episode": episode, "seat": seat, "step": s, "unit": unit, "label": int(i == 0)})
            out.extend(rows)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--subs", default="56711476")
    ap.add_argument("--games-per-sub", type=int, default=10)
    ap.add_argument("--negatives", type=int, default=30)
    a = ap.parse_args()
    con = connect()
    rng = random.Random(0)
    out_dir = data_root() / "datasets" / "work" / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    raw = data_root() / "raw" / "replays"
    for sub in [int(x) for x in a.subs.split(",")]:
        games = con.sql(f"select episode, case when submission_0={sub} then 0 else 1 end from games where submission_0={sub} or submission_1={sub} "
                        f"order by hash(episode) limit {a.games_per_sub}").fetchall()
        for episode, seat in games:
            target = out_dir / f"{episode}-{seat}.parquet"
            if target.exists():
                continue
            t = time.perf_counter()
            path = next(raw.glob(f"*/{episode}.json.gz"))
            rows = game_rows(con, episode, seat, path, a.negatives, rng)
            cols = sorted({k for r in rows for k in r})
            table = pa.table({c: [r.get(c) for r in rows] for c in cols})
            pq.write_table(table, target, compression="zstd")
            print(json.dumps({"sub": sub, "episode": episode, "seat": seat, "rows": len(rows),
                              "decisions": sum(r["label"] for r in rows), "seconds": round(time.perf_counter() - t, 1)}), flush=True)


if __name__ == "__main__":
    main()

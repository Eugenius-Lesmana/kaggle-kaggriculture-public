"""Work-model dataset from the L1 day segments: the 4th-place agent's job choices on our own farm.

python tools/build_ownfarm_dataset.py <name> [--negatives 30] [--games 10301,10302]
Writes <data>/datasets/work/<name>/<game>-d<day>.parquet, same columns as build_work_dataset.py, plus `game`.
The price and sales history before each morning comes from our recorded game (sales = our issued SELL orders,
as the model player sees them at play time); inside the day, from the segment's own sales table.
"""
import argparse
import csv
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from build_work_dataset import game_rows  # noqa: E402
from kagml.paths import data_root, datasets  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402
from kagml.work_features import History  # noqa: E402

EL3 = REPO.parent / "Kaggle-Kaggriculture" / ".scratch" / "template-bench" / "runs" / "el3"


def warm_history(parent, seat, upto):
    """History over our recorded game's turns before `upto`, with our issued SELL orders as our sales."""
    h = History()
    for s in range(upto):
        obs = parent["steps"][s][seat]["observation"]
        prev = parent["steps"][s][seat]["action"] or {} if s > 0 else {}
        sold = Counter({o[1]: int(o[2]) for o in prev.get("market") or [] if o and o[0] == "SELL" and len(o) > 2})
        h.add(obs, sold)
    return h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("name")
    ap.add_argument("--negatives", type=int, default=30)
    ap.add_argument("--games", default="")
    ap.add_argument("--source", default="ownfarm", choices=("ownfarm", "takeover", "ownfarm-edge", "takeover-edge"),
                    help="ownfarm (L1) or takeover (L3: labels from the takeover on); -edge: days 0-5 and 29 (package E)")
    ap.add_argument("--player", default="model:ranker-own-v1", help="L3: the player that played before the takeover")
    a = ap.parse_args()
    l3 = a.source.startswith("takeover")
    slug = a.player.replace(":", "-")
    con = connect(datasets() / a.source / slug if l3 else datasets() / a.source)
    manifest = f"{a.source}-{slug}.csv" if l3 else f"{a.source}.csv"
    rng = random.Random(0)
    out_dir = data_root() / "datasets" / "work" / a.name
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_by_game = {}
    for r in csv.DictReader(open(REPO / "manifests" / manifest)):
        if not a.games or r["game"] in a.games.split(","):
            rows_by_game.setdefault(r["game"], []).append(r)
    for game, segs in rows_by_game.items():
        parent = load_replay(EL3 / f"{game}.json")
        for r in segs:
            target = out_dir / (f"{game}-d{r['day']}-h{r['H']}.parquet" if l3 else f"{game}-d{r['day']}.parquet")
            if target.exists():
                continue
            t = time.perf_counter()
            seat, start = int(r["seat"]), int(r["start_step"])
            rows = game_rows(con, int(r["episode"]), seat, data_root() / r["file"], a.negatives, rng,
                             history=warm_history(parent, seat, start), offset=start,
                             label_from=int(r["takeover_step"]) if l3 else None)
            for row in rows:
                row["game"] = int(game)
                row["source"] = 3 if l3 else 1   # L1 or L3; for analysis only, never a feature
            cols = sorted({k for row in rows for k in row})
            pq.write_table(pa.table({c: [row.get(c) for row in rows] for c in cols}), target, compression="zstd")
            print(json.dumps({"game": game, "day": r["day"], "H": r.get("H"), "rows": len(rows), "decisions": sum(x["label"] for x in rows),
                              "seconds": round(time.perf_counter() - t, 1)}), flush=True)


if __name__ == "__main__":
    main()

"""Score a ranker against EVERY legal job on the L1 day segments (the 4th-place agent's choices on our farm).

python tools/eval_ownfarm.py <model dir name> [--games 10320,...] [--days 8,16,24]
Default games are the held-out ones (10320-10324, never used for training own-farm rankers).
Reports top-1 / top-3 overall, by job kind, and a nearest-job baseline.
"""
import argparse
import csv
import json
import random
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "tools"))
from build_ownfarm_dataset import EL3, warm_history  # noqa: E402
from build_work_dataset import game_rows  # noqa: E402
from kagml.paths import data_root, datasets, models  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402
from kagml.work_features import KINDS  # noqa: E402

HELD_OUT = "10320,10321,10322,10323,10324"

ap = argparse.ArgumentParser()
ap.add_argument("model")
ap.add_argument("--games", default=HELD_OUT)
ap.add_argument("--days", default="8,12,16,20,24")
a = ap.parse_args()
booster = lgb.Booster(model_file=str(models() / a.model / "model.txt"))
feats = json.load(open(models() / a.model / "features.json"))
con = connect(datasets() / "ownfarm")
segs = {(r["game"], r["day"]): r for r in csv.DictReader(open(REPO / "manifests" / "ownfarm.csv"))}
labs = []
for game in a.games.split(","):
    parent = load_replay(EL3 / f"{game}.json")
    for day in a.days.split(","):
        r = segs[(game, day)]
        seat, start = int(r["seat"]), int(r["start_step"])
        df = pd.DataFrame(game_rows(con, int(r["episode"]), seat, data_root() / r["file"], 10 ** 6, random.Random(0),
                                    history=warm_history(parent, seat, start), offset=start))
        for c in feats:
            if c not in df:
                df[c] = np.nan
        df["_s"] = booster.predict(df[feats].astype(np.float32))
        df["_b"] = -df["dist"] * 1000 + df["value_now"]
        g = df.groupby(["step", "unit"])
        df["_r"], df["_rb"], df["_n"] = (g["_s"].rank(ascending=False, method="first"),
                                         g["_b"].rank(ascending=False, method="first"), g["_s"].transform("size"))
        lab = df[df.label == 1]
        labs.append(lab[["kind", "_r", "_rb", "_n"]].assign(game=game, day=int(day)))
    print(game, flush=True)
lab = pd.concat(labs)
rep = {"model": a.model, "games": a.games, "days": a.days, "decisions": len(lab),
       "median_candidates": int(lab._n.median()),
       "top1": round(float((lab._r == 1).mean()), 3), "top3": round(float((lab._r <= 3).mean()), 3),
       "nearest_baseline_top1": round(float((lab._rb == 1).mean()), 3),
       "top1_by_kind": {KINDS[int(k)] if 0 <= k < len(KINDS) else str(k): round(float((v._r == 1).mean()), 3)
                        for k, v in lab.groupby("kind")},
       "top1_by_day": {int(d): round(float((v._r == 1).mean()), 3) for d, v in lab.groupby("day")}}
print(json.dumps(rep, indent=1))
out = data_root() / "runs" / "eval-ownfarm"
out.mkdir(parents=True, exist_ok=True)
(out / f"{a.model}.json").write_text(json.dumps(rep, indent=1))

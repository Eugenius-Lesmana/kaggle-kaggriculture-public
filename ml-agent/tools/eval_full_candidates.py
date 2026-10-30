"""Score a trained ranker against EVERY legal job (not sampled ones) on held-out games.

python tools/eval_full_candidates.py <model dir name> <dataset name> [n_games] [every_kth_decision]
Uses the same held-out games as train_ranker.py (same seed and split rule).
"""
import json
import random
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from kagml.paths import data_root, models  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from build_work_dataset import game_rows  # noqa: E402

model_name, dataset = sys.argv[1], sys.argv[2]
n_games = int(sys.argv[3]) if len(sys.argv) > 3 else 2
every = int(sys.argv[4]) if len(sys.argv) > 4 else 4
mdir = models() / model_name
booster = lgb.Booster(model_file=str(mdir / "model.txt"))
feats = json.load(open(mdir / "features.json"))
files = sorted((data_root() / "datasets" / "work" / dataset).glob("*.parquet"))
games = sorted({int(f.stem.split("-")[0]) for f in files})
rng = np.random.default_rng(0)
test_games = sorted(rng.choice(games, size=max(1, len(games) // 5), replace=False))[:n_games]
con = connect()
raw = data_root() / "raw" / "replays"
hits, hits3, n, sizes = 0, 0, 0, []
for episode in test_games:
    seat = int(next(f for f in files if f.stem.startswith(str(episode))).stem.split("-")[1])
    path = next(raw.glob(f"*/{episode}.json.gz"))
    rows = game_rows(con, episode, seat, path, 10 ** 6, random.Random(0))
    df = pd.DataFrame(rows)
    keys = df[["step", "unit"]].drop_duplicates().iloc[::every]
    df = df.merge(keys, on=["step", "unit"])
    for c in feats:
        if c not in df:
            df[c] = np.nan
    df["_s"] = booster.predict(df[feats].astype(np.float32))
    df["_r"] = df.groupby(["step", "unit"])["_s"].rank(ascending=False, method="first")
    lab = df[df.label == 1]
    hits += int((lab._r == 1).sum()); hits3 += int((lab._r <= 3).sum()); n += len(lab)
    sizes += df.groupby(["step", "unit"]).size().tolist()
    print(f"{episode}: {len(lab)} decisions, top-1 {float((lab._r == 1).mean()):.3f}, top-3 {float((lab._r <= 3).mean()):.3f}", flush=True)
print(f"ALL: {n} decisions against every legal job (median {int(np.median(sizes))} candidates): "
      f"top-1 {hits / n:.3f}, top-3 {hits3 / n:.3f}")

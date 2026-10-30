"""D5: where v2-diag disagrees with the teacher, against every legal job (L1, analysis games 10315-10319 only).

python tools/diag_d5.py
For each decision: the teacher's job kind and the model's; for disagreements, whether our features can tell the two
jobs apart at all (identical feature vectors = indistinguishable), and how far apart they are in value and distance.
"""
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
from kagml.paths import data_root, datasets, models, runs  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402
from kagml.work_features import KINDS  # noqa: E402

GAMES = {"10315", "10316", "10317", "10318", "10319"}
m = models() / "ranker-own-v1-diag"
booster, feats = lgb.Booster(model_file=str(m / "model.txt")), json.load(open(m / "features.json"))
con = connect(datasets() / "ownfarm")
rows = []
for r in csv.DictReader(open(REPO / "manifests" / "ownfarm.csv")):
    if r["game"] not in GAMES:
        continue
    parent = load_replay(EL3 / f"{r['game']}.json")
    seat, start = int(r["seat"]), int(r["start_step"])
    df = pd.DataFrame(game_rows(con, int(r["episode"]), seat, data_root() / r["file"], 10 ** 6, random.Random(0),
                                history=warm_history(parent, seat, start), offset=start))
    for c in feats:
        if c not in df:
            df[c] = np.nan
    X = df[feats].astype(np.float32)
    df["_s"] = booster.predict(X)
    for (step, unit), g in df.groupby(["step", "unit"]):
        best = g.loc[g._s.idxmax()]
        lab = g[g.label == 1].iloc[0]
        same = bool((X.loc[best.name].fillna(-1e9) == X.loc[lab.name].fillna(-1e9)).all())
        rows.append({"game": r["game"], "day": int(r["day"]), "hour": step % 24, "teacher_kind": KINDS[int(lab.kind)],
                     "model_kind": KINDS[int(best.kind)], "right": best.name == lab.name, "indistinguishable": same,
                     "value_teacher": lab.value_now, "value_model": best.value_now,
                     "dist_teacher": lab.dist, "dist_model": best.dist, "candidates": len(g)})
    print(r["game"], r["day"], flush=True)
d = pd.DataFrame(rows)
out = runs() / "diag" / "d5"
out.mkdir(parents=True, exist_ok=True)
d.to_csv(out / "decisions.csv.gz", index=False)
w = d[~d.right]
print(f"\n{len(d)} decisions, top-1 {d.right.mean():.3f}; wrong {len(w)}")
print(f"wrong but indistinguishable in our features: {w.indistinguishable.mean():.1%}")
print(f"wrong, same job kind as the teacher's (other tile): {(w.teacher_kind == w.model_kind).mean():.1%}")
print("\n== Wrong decisions: teacher's kind (rows) vs model's kind (columns), counts")
print(pd.crosstab(w.teacher_kind, w.model_kind, margins=True))
print("\n== Wrong decisions with a different kind: value and distance, teacher's job vs model's job (means)")
k = w[w.teacher_kind != w.model_kind]
print(k[["value_teacher", "value_model", "dist_teacher", "dist_model"]].mean().round(1))
print("\n== Top-1 by teacher's job kind")
print(d.groupby("teacher_kind").right.agg(["mean", "size"]).round(3))

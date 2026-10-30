"""D1 (drift, from data): v2-diag's agreement with the teacher on the analysis games, in the teacher's own days (L1)
against the days our model played first (L3, by takeover hour), split by hour of day. Sampled job lists (teacher's
job + 30 others), the same for both, so the two are comparable. Analysis games 10315-10319 only.
"""
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import data_root, models  # noqa: E402

GAMES = range(10315, 10320)
m = models() / "ranker-own-v1-diag"
booster, feats = lgb.Booster(model_file=str(m / "model.txt")), json.load(open(m / "features.json"))
out = []
for name, tag in (("own-v1", "L1"), ("own-l3", "L3")):
    for f in sorted((data_root() / "datasets" / "work" / name).glob("*.parquet")):
        if int(f.stem.split("-")[0]) not in GAMES:
            continue
        d = pd.read_parquet(f)
        for c in feats:
            if c not in d:
                d[c] = np.nan
        d["_s"] = booster.predict(d[feats].astype(np.float32))
        d["_r"] = d.groupby(["episode", "step", "unit"])["_s"].rank(ascending=False, method="first")
        lab = d[d.label == 1]
        h = int(f.stem.split("-h")[1]) if "-h" in f.stem else 0
        out.append(pd.DataFrame({"src": tag, "H": h, "hour": lab.step % 24, "top1": lab._r == 1}))
r = pd.concat(out)
r["band"] = pd.cut(r.hour, [-1, 3, 7, 11, 15, 19, 23], labels=["0-3", "4-7", "8-11", "12-15", "16-19", "20-23"])
print("decisions:", r.groupby("src").size().to_dict())
print("== top-1 by hour of day (L1 = teacher's own day; L3 = after our model played the first H hours)")
print(r.groupby(["band", "src"], observed=True).top1.mean().unstack().round(3))
print("== L3 by takeover hour")
print(r[r.src == "L3"].groupby("H").top1.agg(["mean", "size"]).round(3))

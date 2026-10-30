"""Train the first work-model ranker (LightGBM, ranking objective) and report offline agreement with the teacher.

python tools/train_ranker.py <dataset name> [--drop col1,col2]
Games are split 80/20 (by game, never by turn). One decision = one group; label 1 = the teacher's job.
Reports top-1 / top-3 agreement on held-out games overall, by job kind and by day band, beside a simple baseline
(nearest job, ties broken by rule value). Note: candidates are sampled (teacher's job + 30 others), so agreement
here is higher than over every legal job; the bench in full play is the real test.
"""
import argparse
import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import data_root, models  # noqa: E402
from kagml.work_features import KINDS  # noqa: E402

ID = ["episode", "seat", "step", "unit", "label", "game", "source"]


def topk(df, score, k):
    df = df.assign(_s=score)
    df["_r"] = df.groupby(["episode", "seat", "step", "unit"])["_s"].rank(ascending=False, method="first")
    return df[df.label == 1]["_r"].le(k)


ap = argparse.ArgumentParser()
ap.add_argument("name")
ap.add_argument("--drop", default="")
ap.add_argument("--negatives", type=int, default=10)
ap.add_argument("--suffix", default="", help="appended to the model name")
ap.add_argument("--out", default="", help="model directory name (default ranker-<name><suffix>)")
ap.add_argument("--weight-mode", default="broad", choices=("broad", "narrow"),
                help="broad: any job on a crop/animal that dies, escapes or produces tonight; narrow: only watering such a crop "
                     "or feeding such an animal (plus fertilize, plant, build in both)")
ap.add_argument("--weight-costly", type=int, default=1, help="count decisions whose teacher job is costly to get wrong this many times "
                "(fertilize, plant, build, or a crop/animal that dies, escapes or produces tonight)")
ap.add_argument("--exclude-games", default="", help="games dropped entirely (never trained on, never scored)")
ap.add_argument("--test-games", default="", help="held-out games (own-farm data: split by original game)")
a = ap.parse_args()
files = sorted(f for n in a.name.split("+") for f in (data_root() / "datasets" / "work" / n).glob("*.parquet"))   # "+" pools datasets
rng = np.random.default_rng(0)


def load(f):
    """Read one game compactly: float32 features, and at most `--negatives` other candidates per decision."""
    d = pd.read_parquet(f)
    key = d.groupby(["episode", "seat", "step", "unit"], sort=False).ngroup().to_numpy()
    keep = d.label.to_numpy() == 1
    neg = np.flatnonzero(~keep)
    order = rng.permutation(len(neg))
    neg = neg[order]
    taken = pd.Series(key[neg]).groupby(key[neg]).cumcount().to_numpy() < a.negatives
    keep[neg[taken]] = True
    d = d[keep]
    for c in d.columns:
        if c not in ID and d[c].dtype != np.float32:
            d[c] = d[c].astype(np.float32)
    return d


df = pd.concat([load(f) for f in files], ignore_index=True)
df = df.sort_values(["episode", "seat", "step", "unit"]).reset_index(drop=True)
split = "game" if "game" in df else "episode"
if a.exclude_games:
    df = df[~df[split].isin({int(g) for g in a.exclude_games.split(",")})].reset_index(drop=True)     # own-farm segments share states within a game: split by game
games = sorted(df[split].unique())
test_games = (set() if a.test_games == "none" else {int(g) for g in a.test_games.split(",")} if a.test_games
              else set(rng.choice(games, size=max(1, len(games) // 5), replace=False)))
feats = [c for c in df.columns if c not in ID and c not in set(filter(None, a.drop.split(",")))]
train, test = df[~df[split].isin(test_games)], df[df[split].isin(test_games)]
if a.weight_costly > 1:      # repeat costly training decisions (as separate groups) so the ranker counts them more; test rows untouched
    keys = ["episode", "seat", "step", "unit"]
    lab = train[train.label == 1]
    costly = lab.kind.isin([KINDS.index(k) for k in ("FERTILIZE", "PLANT", "BUILD_COOP", "BUILD_PASTURE") if k in KINDS])
    if a.weight_mode == "broad":
        for c in ("n_dies_tonight", "n_prod_tonight", "n_escapes_tonight"):
            if c in lab:
                costly |= lab[c].fillna(0) > 0
    else:
        urgent = lambda c: lab[c].fillna(0) > 0 if c in lab else False
        costly |= (lab.kind == KINDS.index("WATER")) & (urgent("n_dies_tonight") | urgent("n_prod_tonight"))
        costly |= (lab.kind == KINDS.index("FEED")) & (urgent("n_escapes_tonight") | urgent("n_prod_tonight"))
    pick = lab[costly][keys].assign(_c=1)
    extra = train.merge(pick, on=keys)
    copies = [extra.drop(columns="_c").assign(unit=extra.unit + 1000 * k) for k in range(1, a.weight_costly)]
    print(f"costly decisions repeated x{a.weight_costly}: {len(pick)} of {len(lab)}", flush=True)
    train = pd.concat([train] + copies, ignore_index=True).sort_values(keys).reset_index(drop=True)
group = lambda d: d.groupby(["episode", "seat", "step", "unit"], sort=False).size().to_numpy()
model = lgb.LGBMRanker(objective="lambdarank", n_estimators=400, learning_rate=0.05, num_leaves=63,
                       min_child_samples=50, subsample=0.8, subsample_freq=1, colsample_bytree=0.8, verbose=-1)
model.fit(train[feats], train.label, group=group(train), categorical_feature=["kind", "item", "last_job"])
if test.empty:                # final model on every allowed game: save it, no offline report
    out = models() / (a.out or f"ranker-{a.name}{a.suffix}")
    out.mkdir(parents=True, exist_ok=True)
    model.booster_.save_model(str(out / "model.txt"))
    json.dump(feats, open(out / "features.json", "w"))
    (out / "report.json").write_text(json.dumps({"games": len(games), "decisions": int((train.label == 1).sum()), "features": len(feats)}, indent=1))
    print(f"saved {out} ({len(games)} games)")
    sys.exit(0)
score = model.predict(test[feats])
base = -test["dist"] * 1000 + test["value_now"]
lab = test[test.label == 1]
report = {"games": len(games), "test_games": len(test_games), "decisions_test": int(len(lab)), "features": len(feats),
          "top1": float(topk(test, score, 1).mean()), "top3": float(topk(test, score, 3).mean()),
          "baseline_top1": float(topk(test, base, 1).mean()), "baseline_top3": float(topk(test, base, 3).mean())}
t1 = topk(test, score, 1)
report["top1_by_kind"] = {KINDS[int(k)] if 0 <= k < len(KINDS) else str(k): round(float(t1[lab.kind == k].mean()), 3)
                          for k in sorted(lab.kind.unique())}
report["top1_by_days"] = {f"{lo}-{lo + 5}": round(float(t1[(lab.day >= lo) & (lab.day < lo + 6)].mean()), 3) for lo in (0, 6, 12, 18, 24)}
imp = pd.Series(model.booster_.feature_importance("gain"), index=feats).sort_values(ascending=False)
report["top_features"] = {k: round(float(v / imp.sum()), 3) for k, v in imp.head(15).items()}
out = models() / (a.out or f"ranker-{a.name}{a.suffix}")
out.mkdir(parents=True, exist_ok=True)
model.booster_.save_model(str(out / "model.txt"))
(out / "report.json").write_text(json.dumps(report, indent=1))
json.dump(feats, open(out / "features.json", "w"))
print(json.dumps(report, indent=1))

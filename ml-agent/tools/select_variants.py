"""Compare ranker variants on the analysis games (one-day and three-day), against v2-diag, the template and the
teacher. Template and teacher rows come from Codex's D4/D6 runs on the same mornings and the same value formula.

python tools/select_variants.py <one-day tags, comma-separated> <three-day tags, comma-separated> [baseline player]
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import runs  # noqa: E402

one, three = sys.argv[1].split(","), sys.argv[2].split(",")
base = sys.argv[3] if len(sys.argv) > 3 else "model:ranker-own-v1-diag"
cmp = runs() / "compare"
d1 = pd.concat([pd.read_csv(cmp / f"{t}.csv") for t in one])
d3 = pd.concat([pd.read_csv(cmp / f"{t}.csv") for t in three])
codex = pd.read_csv(runs() / "diag" / "d4-d6" / "daily_rows.csv")
ref1 = codex[(codex.diagnostic == "D6") & (codex.relative_day == 1) & codex.arm.astype(str).isin(["1", "2"])]
ref1 = ref1.assign(player=ref1.arm.astype(str).map({"1": "template", "2": "teacher"}), day=ref1.morning)
ref3 = codex[(codex.diagnostic == "D4") & (codex.relative_day == 3) & codex.arm.isin(["A", "C"])]
ref3 = ref3.assign(player=ref3.arm.map({"A": "template", "C": "teacher"}), day=ref3.morning,
                   value_plus_assets=ref3.cumulative_value_plus_assets)
for name, d, ref in (("ONE DAY", d1, ref1), ("THREE DAYS", d3, ref3)):
    keys = set(map(tuple, d[["game", "day"]].drop_duplicates().values))
    ref = ref[[(g, dd) in keys for g, dd in zip(ref.game, ref.day)]]
    allp = pd.concat([d[["game", "day", "player", "value_plus_assets"]], ref[["game", "day", "player", "value_plus_assets"]]])
    p = allp.pivot_table(index=["game", "day"], columns="player", values="value_plus_assets").dropna()
    lead = (p["teacher"] - p["template"]).mean()
    print(f"\n== {name}: {len(p)} mornings; teacher's lead over the template {lead:.0f}")
    for c in p.columns:
        x, y = p[c] - p["template"], p[c] - p[base]
        print(f"  {c:30s} mean {p[c].mean():7.0f}  vs template {x.mean():6.0f} (se {x.sem():3.0f})  vs {base.split(':')[-1]} "
              f"{y.mean():6.0f} (se {y.sem():3.0f})  share of teacher's lead {x.mean() / lead:5.0%}")
cols = ["n_water", "n_fertilize", "n_plant", "planted", "n_harvest", "n_feed", "n_care", "n_pickup", "n_drop", "fed_cared"]
print("\n== One day, work per day")
print(d1.groupby("player")[cols].mean().round(1).T)

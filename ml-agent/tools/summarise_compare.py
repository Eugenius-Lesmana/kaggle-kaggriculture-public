"""Paired summary of a same-morning comparison: player B minus player A on the same game and morning, by day.

python tools/summarise_compare.py <tag> [A] [B]      (defaults: A = recorded, B = template)
"""
import csv
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import runs  # noqa: E402

tag = sys.argv[1]
A = sys.argv[2] if len(sys.argv) > 2 else "recorded"
B = sys.argv[3] if len(sys.argv) > 3 else "template"
rows = list(csv.DictReader(open(runs() / "compare" / f"{tag}.csv")))
by = {(r["game"], r["day"], r["player"]): r for r in rows}
cols = ["value_change", "cash_change", "opp_cash_change", "planted", "fed_cared", "n_harvest", "n_water", "n_plant"]
diff = defaultdict(lambda: defaultdict(list))
for (g, d, p), r in by.items():
    if p == B and (g, d, A) in by:
        for c in cols:
            diff[int(d)][c].append(float(r[c]) - float(by[(g, d, A)][c]))


def fmt(x):
    if len(x) < 2:
        return "n/a"
    return f"{st.mean(x):+.0f} ({st.stdev(x) / len(x) ** 0.5:.0f})"


print(f"{tag}: {B} minus {A}, same game and morning; mean (SE)")
print("day  n    " + "  ".join(f"{c:>16}" for c in cols))
for d in sorted(diff):
    n = len(diff[d]["value_change"])
    print(f"{d:>3} {n:>3}    " + "  ".join(f"{fmt(diff[d][c]):>16}" for c in cols))

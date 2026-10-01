"""Verify the H1 counter evidence and regenerate summary.json.

Checks: candidate = frozen substrate bytes + appended overlay ending in the loader pop;
every cell has 120 games (seeds 6301-6360 x 2 seats) with no duplicates; guard cells are
bank-identical to the substrate. Reports counter vs substrate on identical games.
Run from the repo root: python evaluation/h1_counter/verify.py
"""
import glob, json, os
from collections import defaultdict

ROOT = "evaluation/h1_counter"
sub = open("agents/ours/h1-substrate-metav4/main.py", "rb").read()
cand = open("agents/ours/h1-counter-candidate/main.py", "rb").read()
assert cand.startswith(sub), "substrate prefix changed"
assert cand.rstrip().endswith(b'agent = globals().pop("agent")'), "loader pop missing"

rows = defaultdict(dict)                     # (arm, opponent) -> {(seed, side): row}
for f in glob.glob(f"{ROOT}/*_vs_*_63*.json"):
    arm, rest = os.path.basename(f).split("_vs_", 1)
    opp = rest.rsplit("_63", 1)[0]
    for r in json.load(open(f))["rows"]:
        key = (r["seed"], r["side"])
        assert key not in rows[(arm, opp)], f"duplicate {arm} {opp} {key}"
        rows[(arm, opp)][key] = r
GUARDS = {"farming_score", "two_coins", "cloning"}
summary = []
for opp in sorted({o for _, o in rows}):
    c, s = rows.get(("counter", opp), {}), rows.get(("substrate", opp), {})
    assert len(c) == 120 and len(s) == 120 and c.keys() == s.keys(), f"{opp}: {len(c)}/{len(s)} games"
    W = lambda d: (sum(r["cand"] > r["opp"] for r in d.values()), sum(r["cand"] < r["opp"] for r in d.values()),
                   sum(r["cand"] == r["opp"] for r in d.values()))
    gained = sum(s[k]["cand"] <= s[k]["opp"] and c[k]["cand"] > c[k]["opp"] for k in c)
    lost = sum(s[k]["cand"] > s[k]["opp"] and c[k]["cand"] <= c[k]["opp"] for k in c)
    identical = sum(c[k]["cand"] == s[k]["cand"] and c[k]["opp"] == s[k]["opp"] for k in c)
    if opp in GUARDS:
        assert identical == 120, f"guard {opp} not identical"
    summary.append(dict(opponent=opp, counter_wlt=W(c), substrate_wlt=W(s), wins_gained=gained, wins_lost=lost,
                        identical_games=identical,
                        counter_mean_lead=round(sum(r["cand"] - r["opp"] for r in c.values()) / 120, 1),
                        substrate_mean_lead=round(sum(r["cand"] - r["opp"] for r in s.values()) / 120, 1)))
json.dump({"seeds": "6301-6360", "seats": 2, "rows": summary}, open(f"{ROOT}/summary.json", "w"), indent=2)
for r in summary:
    print(f"{r['opponent']:15} counter W-L-T {r['counter_wlt']}  substrate {r['substrate_wlt']}  gained {r['wins_gained']:3} lost {r['wins_lost']:2}"
          f"  identical {r['identical_games']:3}  lead {r['substrate_mean_lead']:>8} -> {r['counter_mean_lead']:>8}")
print("all checks passed")

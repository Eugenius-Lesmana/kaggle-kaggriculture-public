"""Paired bank-ratio change of arm B vs arm A on identical seeds/seats (scripts/screen.py JSON outputs)."""
import json, statistics, sys
a, b = (json.load(open(p))["rows"] for p in sys.argv[1:3])
ka = {(r["seed"], r["side"]): r["cand"] / max(1, r["opp"]) for r in a}
kb = {(r["seed"], r["side"]): r["cand"] / max(1, r["opp"]) for r in b}
d = [kb[k] - ka[k] for k in ka if k in kb]
m, se = statistics.mean(d), statistics.stdev(d) / len(d) ** 0.5
print(f"n={len(d)} ratio A {statistics.mean(ka.values()):.3f} B {statistics.mean(kb.values()):.3f} | change {m:+.3f} +/- {1.96*se:.3f}"
      f" | wins A {sum(r['cand']>r['opp'] for r in a)} B {sum(r['cand']>r['opp'] for r in b)}")

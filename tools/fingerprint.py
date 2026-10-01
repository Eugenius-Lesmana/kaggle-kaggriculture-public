"""Does each replay player run the public (Metav4/V46) tape family, or something else?

Usage: python research/tools/fingerprint.py "<replay glob>"   (default: 22 Sept replays)
Accepts .json and .json.gz.

Tape agents replay pre-searched per-step actions. Before day 6 (step 144) the
family's router always uses route 0, so the opening is a clean fingerprint;
after it, the best-matching of the 41 routes is reported.
"""
import glob, gzip, json, re, sys, zlib, base64
from collections import Counter, defaultdict

src = open("agents/ours/h1-substrate-metav4/main.py", encoding="utf-8").read()
m = re.search(r"_R108_DATA=json\.loads\(zlib\.decompress\(base64\.b85decode\('([^']+)'\)", src)
bundle = json.loads(zlib.decompress(base64.b85decode(m.group(1))))
routes = {int(k): [bundle["actions"][i] for i in ids] for k, ids in bundle["routes"].items()}


def units(action):
    if not isinstance(action, dict):
        return []
    return [action.get("farmer") or ["PASS"]] + list(action.get("hands") or [])


def match(played, tape, lo, hi):
    hit = tot = 0
    for step in range(lo, hi):
        p, t = units(played[step]), units(tape[step - 1] if step - 1 < len(tape) else {})
        n = min(len(p), len(t))
        for a, b in zip(p[:n], t[:n]):
            tot += 1
            hit += (a == b)
    return hit / tot if tot else 0.0


rows = []
by_team = defaultdict(list)
pattern = sys.argv[1] if len(sys.argv) > 1 else "research/intake/replays/22 Sept/*.json"
for f in sorted(glob.glob(pattern, recursive=True)):
    d = json.load(gzip.open(f, "rt", encoding="utf-8") if f.endswith(".gz") else open(f, encoding="utf-8"))
    names = d["info"]["TeamNames"]; rewards = d["rewards"]
    for p in (0, 1):
        played = [d["steps"][i][p].get("action") for i in range(len(d["steps"]))]
        opening = match(played, routes[0], 1, 144)
        best_route, best = max(((r, match(played, t, 144, 648)) for r, t in routes.items()), key=lambda x: x[1])
        rows.append((f.split("\\")[-1].split("/")[-1][:-5], names[p], rewards[p], rewards[1 - p], opening, best_route, best))
        by_team[names[p]].append((opening, best))

print(f"{'replay':<11}{'team':<22}{'bank':>9}{'opp bank':>10}{'opening vs tape':>17}{'best route d6-27':>18}")
for r in rows:
    print(f"{r[0]:<11}{r[1][:21]:<22}{r[2]:>9,.0f}{r[3]:>10,.0f}{r[4]:>16.0%}{('r'+str(r[5])):>8}{r[6]:>9.0%}")
print("\nper team (games, mean opening match, mean mid-game match):")
for team, v in sorted(by_team.items(), key=lambda kv: -len(kv[1])):
    print(f"  {team[:28]:<30}{len(v):>3}   opening {sum(a for a,_ in v)/len(v):>5.0%}   mid-game {sum(b for _,b in v)/len(v):>5.0%}")

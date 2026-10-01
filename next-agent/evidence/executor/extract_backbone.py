"""Extract Team A's per-hand backbone routes (days 0-11) and the literal tape of episode 112920694.

A hand's day is cut into *visits*: maximal runs of non-move commands on one cell (PASS does not
break a run, a move does). The backbone route of (hand slot k, day d) is the medoid over Team A's
games of the visit-cell sequence, under the micro-tape study's tolerant edit similarity
(same cell 0, adjacent cell 0.5, else 1; docs/MICROTAPE_STUDY_2026-09-28.md).

Usage (from the repo root):
  python evaluation/executor/extract_backbone.py
Writes evaluation/executor/team_a_backbone.json and evaluation/executor/team_a_tape_112920694.json.
"""
import glob, gzip, json, os
from collections import defaultdict

DAYS = 12
MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
TAPE_EPISODE = "112920694"
OUT = os.path.dirname(os.path.abspath(__file__))


def fuzzy_lev(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            d = abs(ca[0] - cb[0]) + abs(ca[1] - cb[1])
            sub = 0 if d == 0 else 0.5 if d == 1 else 1
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + sub))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b), 1)


def visits(records):
    """records: [(hour, cell, cmd)] in hour order -> [{"c": cell, "ops": [...], "h": hour}]."""
    out, run = [], None
    for hour, cell, cmd in records:
        op = cmd[0]
        if op in MOVES:
            run = None
            continue
        if op == "PASS":
            continue
        if run is None or tuple(run["c"]) != tuple(cell):
            run = {"c": list(cell), "ops": [], "h": hour}
            out.append(run)
        run["ops"].append(" ".join(str(x) for x in cmd))
    return out


def main():
    games, seen = [], set()
    tape = None
    for f in sorted(glob.glob("research/intake/replays/24 Sept/*/*.json.gz")):
        ep = os.path.basename(f).split(".")[0]
        if ep in seen:
            continue
        d = json.load(gzip.open(f, "rt", encoding="utf-8"))
        names = d["info"]["TeamNames"]
        if "Team A" not in names:
            continue
        seen.add(ep)
        p = names.index("Team A")
        S = d["steps"]
        per = defaultdict(list)
        for i in range(1, DAYS * 24 + 1):
            b = S[i - 1][p]["observation"]
            a = S[i][p].get("action") or {}
            farm = b["farms"][p]
            pos = [farm["farmer"]] + list(farm.get("hands") or [])
            cmds = [a.get("farmer")] + list(a.get("hands") or [])
            for k, c in enumerate(pos):
                cmd = cmds[k] if k < len(cmds) and isinstance(cmds[k], list) and cmds[k] else ["PASS"]
                per[(k, b["day"])].append((b["hour"], tuple(c), cmd))
        games.append({"ep": ep, "routes": {key: visits(recs) for key, recs in per.items()}})
        if ep == TAPE_EPISODE:
            tape = {"episode": ep, "player": p,
                    "actions": [S[i][p].get("action") for i in range(1, DAYS * 24 + 1)],
                    "positions": [[S[i][p]["observation"]["farms"][p]["farmer"]]
                                  + list(S[i][p]["observation"]["farms"][p].get("hands") or [])
                                  for i in range(0, DAYS * 24)]}
        print(ep, "Team A seat", p)

    backbone, diag = {}, []
    for d in range(DAYS):
        for k in range(20):
            cands = [(g["ep"], g["routes"][(k, d)]) for g in games if g["routes"].get((k, d))]
            if not cands:
                continue
            cells = [[tuple(v["c"]) for v in r] for _, r in cands]
            sims = [[fuzzy_lev(a, b) if i != j else 0 for j, b in enumerate(cells)] for i, a in enumerate(cells)]
            n = len(cands)
            score = [sum(row) / max(1, n - 1) for row in sims]
            best = max(range(n), key=lambda i: score[i])
            pairs = [sims[i][j] for i in range(n) for j in range(i + 1, n)]
            backbone[f"{k},{d}"] = cands[best][1]
            diag.append({"k": k, "day": d, "games": n, "medoid_episode": cands[best][0],
                         "medoid_mean_sim": round(score[best], 3),
                         "mean_pair_sim": round(sum(pairs) / len(pairs), 3) if pairs else None,
                         "visits": len(cands[best][1])})
    json.dump({"source": "Team A, research/intake/replays/24 Sept (deduplicated by episode)",
               "games": [g["ep"] for g in games], "routes": backbone, "diagnostics": diag},
              open(os.path.join(OUT, "team_a_backbone.json"), "w"), separators=(",", ":"))
    json.dump(tape, open(os.path.join(OUT, "team_a_tape_112920694.json"), "w"), separators=(",", ":"))
    for row in diag:
        if row["day"] >= 6:
            print(row)


if __name__ == "__main__":
    main()

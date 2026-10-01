"""Which known agent is this ladder player running? Replay its observations through candidates.

For each player-game in the replays and each candidate agent file, a fresh copy of the agent
is fed that player's observations step by step; its action is compared with the action the
player actually took. An exact copy of a deterministic agent reproduces every step.

Usage: python research/tools/reproduce.py "<replay glob>" [--steps N] [--min-fp 90]
Output: one line per player-game with the best-matching candidate, worker-action and market-order
match rates, and the first divergence step; plus a summary. Writes evaluation/census/reproduce.json.
"""
import argparse, glob, gzip, importlib.util, json, os, sys
from collections import Counter
from multiprocessing import Pool

CANDIDATES = {
    "metav4": "agents/ours/h1-substrate-metav4/main.py",
    "more_wheat": "agents/public/2026-09-20/kaggriculture-more-wheat-smarter-sales/main.py",
    "farm_2945": "agents/public/2026-09-20/kaggriculture/main.py",
    "wonderful_life": "agents/public/2026-09-20/a-wonderful-life/main.py",
    "smaller_shock": "agents/public/2026-09-20/kaggriculture-a-smaller-market-shock/main.py",
    "v46": "agents/public/2026-09-17/kaggriculture-v46-first-turn-microstructure-and-s/main.py",
}


def load_agent(path, tag):
    spec = importlib.util.spec_from_file_location(f"cand_{tag}_{os.getpid()}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Exactly the Kaggle loader's rule (kaggle_environments.agent.get_last_callable):
    # the last callable defined in the file, whatever its name.
    return [v for v in vars(module).values() if callable(v)][-1]


def norm(a):
    if not isinstance(a, dict):
        return None, None
    units = [a.get("farmer") or ["PASS"]] + [h or ["PASS"] for h in (a.get("hands") or [])]
    return json.dumps(units), json.dumps(sorted(json.dumps(o) for o in (a.get("market") or [])))


def job(args):
    path, player, steps, cand, cands = args
    CANDIDATES.update(cands)
    d = json.load(gzip.open(path, "rt", encoding="utf-8") if path.endswith(".gz") else open(path, encoding="utf-8"))
    config = d.get("configuration", {})
    try:
        agent = load_agent(CANDIDATES[cand], cand)
    except Exception as exc:
        return path, player, cand, None, None, None, f"load: {exc}"[:80]
    n = min(steps, len(d["steps"]) - 1)
    wk = mk = 0
    first = None
    for s in range(n):
        obs = dict(d["steps"][s][player]["observation"])
        obs.setdefault("step", s)   # replays omit "step" from the second seat's observation
        want = d["steps"][s + 1][player].get("action")
        try:
            got = agent(obs, config)
        except Exception as exc:
            return path, player, cand, wk / max(1, s), mk / max(1, s), s, f"error: {exc}"[:80]
        gw, gm = norm(got); ww, wm = norm(want)
        wk += gw == ww; mk += gm == wm
        if first is None and (gw != ww or gm != wm):
            first = s
    return path, player, cand, wk / n, mk / n, first, ""


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern")
    ap.add_argument("--steps", type=int, default=719)
    ap.add_argument("--workers", type=int, default=14)
    ap.add_argument("--candidates", default=",".join(CANDIDATES))
    ap.add_argument("--extra", action="append", default=[], help="name=path of an extra candidate agent")
    ap.add_argument("--out", default="evaluation/census/reproduce.json")
    ap.add_argument("--skip-team", default="", help="skip players whose team name contains this text (e.g. our own)")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    for item in a.extra:
        name, path = item.split("=", 1)
        CANDIDATES[name] = path
        a.candidates += "," + name if name not in a.candidates.split(",") else ""
    files = sorted(glob.glob(a.pattern, recursive=True))
    names = {}
    jobs = []
    for f in files:
        d = json.load(gzip.open(f, "rt", encoding="utf-8") if f.endswith(".gz") else open(f, encoding="utf-8"))
        for p in (0, 1):
            names[(f, p)] = d["info"]["TeamNames"][p]
            if a.skip_team and a.skip_team in names[(f, p)]:
                continue
            for c in a.candidates.split(","):
                jobs.append((f, p, a.steps, c, dict(CANDIDATES)))
    with Pool(a.workers) as pool:
        res = pool.map(job, jobs, chunksize=1)
    best = {}
    for f, p, c, wk, mk, first, err in res:
        if wk is None:
            continue
        score = (wk + mk) / 2
        if (f, p) not in best or score > best[(f, p)][1]:
            best[(f, p)] = (c, score, wk, mk, first, err)
    out = []
    for (f, p), (c, score, wk, mk, first, err) in sorted(best.items()):
        exact_all = sorted(rc for rf, rp, rc, rw, rm, _, _ in res if (rf, rp) == (f, p) and rw and rw > 0.999 and rm > 0.999)
        rates = {rc: [round(rw, 4), round(rm, 4)] for rf, rp, rc, rw, rm, _, _ in res if (rf, rp) == (f, p) and rw is not None}
        out.append(dict(replay=os.path.basename(f), player=p, team=names[(f, p)], best=c, worker_match=round(wk, 4),
                        market_match=round(mk, 4), first_divergence=first, note=err, exact_candidates=exact_all, rates=rates))
    os.makedirs(os.path.dirname(a.out) or ".", exist_ok=True)
    json.dump(out, open(a.out, "w"), indent=1)
    for r, ((f, p), (c, score, wk, mk, first, err)) in zip(out, sorted(best.items())):
        exact_all = r["exact_candidates"]
        print(f"{os.path.basename(f):>16} P{p+1} {names[(f, p)][:24]:24} best {c:15} workers {wk:6.1%} market {mk:6.1%} first diff {first}  exact: {','.join(exact_all)}")
    exact = Counter(r["best"] for r in out if r["worker_match"] > 0.999 and r["market_match"] > 0.999)
    near = Counter(r["best"] for r in out if r["worker_match"] > 0.95 and not (r["worker_match"] > 0.999 and r["market_match"] > 0.999))
    print(f"\n{len(out)} player-games. Exact reproduction (all steps): {dict(exact)}; close (>95% workers): {dict(near)}")

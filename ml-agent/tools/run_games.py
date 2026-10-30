"""Paired games against a fixed opponent: python tools/run_games.py <tag> [seeds...]
Env: AGENT_MAIN (default vendor/template_agent/main.py), OPPONENT (main.py path or fifth-n1/fifth-nflow/fourth, required),
WORKERS (1 or 2, default 2). Results go to <data>/runs/<tag>/ on the external drive. Weed draws are pinned so the shops depend on the seed alone."""
import json, os, sys, shutil, time, importlib.util
from multiprocessing import Pool
here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(here, "src"))
from kagml.paths import runs
from kagml.opponents import NAMES, load
def one(args):
    tag, seed = args
    from kaggle_environments import make
    import random, kaggle_environments.envs.kaggriculture.kaggriculture as K
    if not getattr(K, "_pinned", False):   # evaluation only: weeds take one draw per farm, so the shop draw depends on the seed alone
        orig = K._spawn_weeds
        K._spawn_weeds = lambda farm, n, chance, rng: orig(farm, n, chance, random.Random(rng.random()))
        K._pinned = True
    tpl = os.path.join(runs(), tag, "main.py")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
    opponent = os.environ["OPPONENT"]
    if opponent in NAMES:
        opponent = load(opponent)
        opponent.reset(seed)
    env.run([tpl, opponent])
    d = env.toJSON(); st = d["steps"]; json.dump(d, open(os.path.join(runs(), tag, f"{seed}.json"), "w"))
    spec = importlib.util.spec_from_file_location(f"tpl{seed}", tpl); mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    errors = 0; slow = 0.0; last = ""
    for i in range(len(st) - 1):
        o = st[i][0]["observation"]
        try:
            t = time.perf_counter(); mod._agent_impl(o); slow = max(slow, time.perf_counter() - t)
        except Exception as e: errors += 1; last = repr(e)[:80]
    drought = rot = lost = 0; ne = None
    for i in range(1, len(st)):
        b, a = st[i - 1][0]["observation"]["farms"][0], st[i][0]["observation"]["farms"][0]
        if ne is None and len(a["unlocked_quadrants"]) >= 2: ne = i
        for y in range(10):
            for x in range(10):
                p, q = b["tiles"][y][x], a["tiles"][y][x]
                if isinstance(p, dict) and isinstance(q, dict):
                    if p.get("kind") == "PLANT" and q.get("kind") == "WEED":
                        if (i - 1) % 24 == 23 and p.get("consecutive_unwatered", 0) >= 1 and not p.get("watered_today"): drought += 1
                        else: rot += 1
                    if p.get("animal") and not q.get("animal") and (i - 1) // 24 < 27 and (i - 1) % 24 == 23 and p.get("consecutive_unfed", 0) >= 1 and not p.get("fed_today"): lost += 1
    f = st[-1][0]["observation"]["farms"]
    shops = ",".join(x[:4] for x in st[700][0]["observation"]["town"]["unlocked_shops"])
    return f"RESULT {tag} {seed} shops {shops} bank {int(f[0]['money'])} opp {int(f[1]['money'])} NE step {ne} drought {drought} rot {rot} animals lost<27 {lost} errors {errors} {last} slowest {slow:.2f}s"
if __name__ == "__main__":
    workers = int(os.environ.get("WORKERS", 2))
    if workers not in (1, 2):
        raise SystemExit("WORKERS must be 1 or 2")
    tag = sys.argv[1]; os.makedirs(os.path.join(runs(), tag), exist_ok=True)
    shutil.copy(os.environ.get("AGENT_MAIN", os.path.join(here, "vendor", "template_agent", "main.py")), os.path.join(runs(), tag, "main.py"))
    seeds = [int(x) for x in sys.argv[2:]] or list(range(10301, 10313))
    with Pool(workers) as pool:
        for line in pool.imap(one, [(tag, s) for s in seeds]): sys.stdout.write(line + "\n"); sys.stdout.flush()

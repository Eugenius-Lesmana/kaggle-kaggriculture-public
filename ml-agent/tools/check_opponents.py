"""D2 reproducible held-out checks. At most two game workers; all evidence on D:.
python tools/check_opponents.py strength --metav4 <main.py> [--seeds 10301 ...]
python tools/check_opponents.py join --replay <game.json>
python tools/check_opponents.py cold <name>
"""
import argparse
import collections
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import statistics
import sys
import time

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from kagml.opponents import NAMES, load
from kagml.paths import runs

SB = {"ICE_CREAM_SHOP", "BRUNCH_SPOT", "SMOOTHIE_SHOP", "FARMERS_MARKET"}


def file_actor(path):
    spec = importlib.util.spec_from_file_location("_d2_control", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.agent


class Meter:
    def __init__(self, actor):
        self.actor, self.times = actor, []
        self.daily = collections.defaultdict(collections.Counter)
        self.progress = None

    def __call__(self, observation, configuration):
        start = time.perf_counter()
        action = self.actor(observation, configuration)
        self.times.append((time.perf_counter() - start) * 1000)
        row = self.daily[int(observation["day"])]
        row["turns"] += 1
        if self.progress and (int(observation["day"]) * 24 + int(observation["hour"])) % 24 == 0:
            progress = Path(self.progress)
            temporary = progress.with_suffix(".tmp")
            temporary.write_text(json.dumps({"step": int(observation["day"]) * 24 + int(observation["hour"]), "last_ms": self.times[-1]}))
            temporary.replace(progress)
        for command in [action.get("farmer", [])] + list(action.get("hands") or []):
            if command and command[0] != "PASS":
                row["non_pass"] += 1
                row["op_" + command[0]] += 1
        row["market_orders"] += len(action.get("market") or [])
        return action

    def report(self):
        return {"turns": len(self.times), "median_ms": statistics.median(self.times),
                "max_ms": max(self.times), "turn_ms": self.times,
                "daily": dict(self.daily)}


class Exceptions:
    """Raise/handled events, filtered to upstream files. Enabled on one full
    proof game per policy and joins; unmonitored games supply speed estimates.
    """
    def __init__(self, root, enabled=True):
        self.root, self.enabled = str(root), enabled
        self.counts = collections.Counter()

    def event(self, kind, code, offset, exception):
        if code.co_filename.startswith(self.root):
            key = (str(Path(code.co_filename).relative_to(self.root)), code.co_name,
                   kind, type(exception).__name__, str(exception)[:300])
            self.counts[key] += 1

    def __enter__(self):
        if self.enabled:
            sys.monitoring.use_tool_id(4, "kagml-d2")
            for kind, flag in (("raised", sys.monitoring.events.RAISE),
                               ("handled", sys.monitoring.events.EXCEPTION_HANDLED)):
                sys.monitoring.register_callback(4, flag,
                    lambda code, offset, exc, kind=kind: self.event(kind, code, offset, exc))
            sys.monitoring.set_events(4, sys.monitoring.events.RAISE | sys.monitoring.events.EXCEPTION_HANDLED)
        return self

    def __exit__(self, *args):
        if self.enabled:
            sys.monitoring.set_events(4, 0)
            sys.monitoring.free_tool_id(4)

    def report(self):
        return [dict(file=k[0], function=k[1], kind=k[2], type=k[3], message=k[4], events=v)
                for k, v in sorted(self.counts.items())]


def one(job):
    name, control, path, seed, seat, out = job
    from kagml.preview import pin_weeds
    from kaggle_environments import make
    pin_weeds(True)
    actor = load(name)
    actor.reset(seed)
    baseline = file_actor(path)
    meter = Meter(actor)
    meter.progress = str(Path(out) / f"progress-{os.getpid()}.json")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed, "actTimeout": 30, "runTimeout": 7200}, debug=False)
    players = [meter, baseline] if seat == 0 else [baseline, meter]
    start = time.perf_counter()
    traced = seed == 10301 and seat == 0 and control == "metav4"
    with Exceptions(actor.root, enabled=traced) as exceptions:
        env.run(players)
    replay = env.toJSON()
    farms = replay["steps"][-1][0]["observation"]["farms"]
    banks = [farms[seat]["money"], farms[1-seat]["money"]]
    shops = replay["steps"][144][0]["observation"]["town"]["unlocked_shops"][:2]
    result = {"name": name, "control": control, "seed": seed, "seat": seat,
              "banks": banks, "margin": banks[0]-banks[1], "win": banks[0] > banks[1],
              "tie": banks[0] == banks[1], "buyers": sum(s in SB for s in shops),
              "early_shops": shops, "statuses": [s.status for s in env.state],
              "steps": len(env.steps), "seconds": time.perf_counter()-start,
              "load_seconds": actor.load_seconds, "exception_tracing": traced, "timing": meter.report(),
              "diagnostics": actor.diagnostics(), "exceptions": exceptions.report()}
    target = Path(out) / f"{name}-{control}-{seed}-seat{seat}"
    with gzip.open(str(target)+".json.gz", "wt", encoding="utf8", compresslevel=1) as f:
        json.dump(replay, f, separators=(",", ":"))
    if result["steps"] != 720 or result["statuses"] != ["DONE", "DONE"] or len(meter.times) != 719:
        raise RuntimeError(f"Incomplete game: {target}: {result['statuses']}, {len(meter.times)} turns")
    temporary = Path(str(target)+".metrics.tmp")
    temporary.write_text(json.dumps(result, separators=(",", ":")))
    temporary.replace(Path(str(target)+".metrics.json"))
    return {k: v for k, v in result.items() if k not in ("timing", "exceptions", "diagnostics")}


class Effects:
    """Native unit effects; the pinned engine's interpreter loop carries seat i."""
    def __init__(self, seat):
        self.seat, self.counts = seat, collections.Counter()

    def __enter__(self):
        import kaggle_environments.envs.kaggriculture.kaggriculture as K
        from kagml.replay_tables import snapshot
        self.K, self.original = K, K._apply_unit_action

        def apply(farm, private, unit, action, *args, **kwargs):
            # Policy simulators can call this hook with their own state/schema.
            # Only the real preview state is eligible for effect measurement.
            caller = sys._getframe(1)
            tracked = caller.f_code is K.interpreter.__code__ and caller.f_locals.get('i') == self.seat
            before = snapshot(farm, private, unit) if tracked else None
            result = self.original(farm, private, unit, action, *args, **kwargs)
            if tracked and isinstance(action, list) and action and action[0] != "PASS":
                self.counts["attempted_" + action[0]] += 1
                if before != snapshot(farm, private, unit):
                    self.counts["effective_" + action[0]] += 1
            return result

        K._apply_unit_action = apply
        return self

    def __exit__(self, *args):
        self.K._apply_unit_action = self.original


def join(replay_path, out):
    from kagml.preview import snapshot_from_replay, env_from_snapshot, pin_weeds, summary
    replay = json.loads(Path(replay_path).read_text())
    pin_weeds(True)
    results = []
    for name in NAMES:
        actor = load(name)
        for step in (240, 384, 600):
            for seat in (0, 1):
                actor.reset(10301)
                env = env_from_snapshot(snapshot_from_replay(replay, step))
                before = summary(env)[seat]
                meter = Meter(actor)
                effects = Effects(seat)
                with Exceptions(actor.root) as exceptions:
                    for i in range(step+1, min(step+24,719)+1):
                        actions = [replay["steps"][i][p]["action"] for p in (0,1)]
                        actions[seat] = meter(env.state[seat].observation, env.configuration)
                        # Do not hook the policy's private planning simulator.
                        with effects:
                            env.step(actions)
                after = summary(env)[seat]
                results.append({"name":name,"step":step,"seat":seat,"before":before,"after":after,
                                "timing":meter.report(),"diagnostics":actor.diagnostics(),
                                "exceptions":exceptions.report(),"effects":dict(effects.counts)})
                (out/"join.json").write_text(json.dumps(results,indent=2))
    (out/"join.json").write_text(json.dumps(results,indent=2))
    print(json.dumps([{k:v for k,v in r.items() if k not in ("timing","exceptions")} for r in results]))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode", choices=("strength", "join", "cold"))
    ap.add_argument("name", nargs="?", choices=NAMES)
    ap.add_argument("--metav4", type=Path)
    ap.add_argument("--replay", type=Path)
    ap.add_argument("--tag", default="d2-opponents-2026-10-17")
    ap.add_argument("--seeds", nargs="+", type=int, default=list(range(10301,10313)))
    ap.add_argument("--part", type=int, choices=(0,1), help="seed parity shard; use one worker per shard")
    ap.add_argument("--workers", type=int, choices=(1,2), default=2)
    a = ap.parse_args()
    out = runs()/a.tag
    out.mkdir(parents=True,exist_ok=True)
    if a.mode == "cold":
        start=time.perf_counter()
        actor=load(a.name)
        from kaggle_environments import make
        env=make("kaggriculture", configuration={"seed":10301}); env.reset(2)
        meter=Meter(actor); action=meter(env.state[0].observation,env.configuration)
        row={"name":a.name,"load_seconds":actor.load_seconds,"total_seconds":time.perf_counter()-start,
             "timing":meter.report(),"action":action,"diagnostics":actor.diagnostics()}
        (out/f"cold-{a.name}.json").write_text(json.dumps(row,indent=2))
        print(json.dumps(row));return
    if a.mode == "join":
        join(a.replay,out);return
    if not a.metav4 or not a.metav4.is_file():
        ap.error("--metav4 must point to the reference main.py")
    controls={"metav4":a.metav4,"template":REPO/"vendor/template_agent/main.py"}
    manifest={k:{"path":str(v),"sha256":hashlib.sha256(v.read_bytes()).hexdigest()} for k,v in controls.items()}
    (out/"controls.json").write_text(json.dumps(manifest,indent=2))
    jobs=[(n,c,str(p),s,seat,str(out)) for s in a.seeds for n in NAMES
          for c,p in controls.items() for seat in (0,1)
          if not (out/f"{n}-{c}-{s}-seat{seat}.metrics.json").exists()]
    if a.part is not None:
        if a.workers != 1:
            ap.error("--part requires --workers 1 (two shards total)")
        jobs = [job for job in jobs if job[3] % 2 == a.part]
    from multiprocessing import Pool
    with Pool(a.workers) as pool:
        for i,row in enumerate(pool.imap_unordered(one,jobs),1):
            print(f"{i}/{len(jobs)} "+json.dumps(row),flush=True)


if __name__ == "__main__":
    main()

"""Does the model player carry out the jobs it picks? One day from saved mornings, every worker every turn.

python tools/exec_check.py <game.json> --days 24 [--model ranker-v1]
Per turn and worker: position, the target job, the command sent, and whether the worker moved or the job left
the target list. Summary: blocked moves (position unchanged after a move), job commands that did not complete
(same target and command again next turn), PASS turns, walking per completed job vs straight-line distance.
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.model_player import ModelPlayer  # noqa: E402
from kagml.paths import runs  # noqa: E402
from kagml.preview import env_from_snapshot, pin_weeds, snapshot_from_replay  # noqa: E402
from kagml.work_data import load_replay  # noqa: E402

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}


def positions(obs, seat):
    f = obs["farms"][seat]
    return [tuple(f["farmer"][:2]) if isinstance(f["farmer"], list) else (f["farmer"]["x"], f["farmer"]["y"])] + \
        [tuple(h[:2]) if isinstance(h, list) else (h["x"], h["y"]) for h in f["hands"]]


ap = argparse.ArgumentParser()
ap.add_argument("game")
ap.add_argument("--days", default="24")
ap.add_argument("--model", default="ranker-v1")
a = ap.parse_args()
pin_weeds(True)
replay = load_replay(a.game)
player = ModelPlayer(a.model)
log, done = [], 0
for day in [int(d) for d in a.days.split(",")]:
    for i in range(done, day * 24):
        obs = replay["steps"][i][0]["observation"]
        obs.setdefault("step", i)
        player.warm_step(obs, replay.get("configuration"))
    done = day * 24
    player.restore(player.memory())
    env = env_from_snapshot(snapshot_from_replay(replay, day * 24))
    prev = None
    for i in range(day * 24 + 1, day * 24 + 25):
        obs = env.state[0].observation
        action = player(obs, env.configuration)
        targets = dict(player.targets)
        pos = positions(obs, 0)
        cmds = [action["farmer"]] + list(action.get("hands") or [])
        state0 = json.dumps([obs["farms"][0]["tiles"], obs["private"]], sort_keys=True, default=list)
        units0 = [json.dumps([obs["farms"][0]["tiles"][p[1]][p[0]], obs["private"]["inventories"][u] if u < len(obs["private"]["inventories"]) else None], sort_keys=True, default=list) for u, p in enumerate(pos)]
        env.step([action, replay["steps"][i][1]["action"]])
        nobs = env.state[0].observation
        after = positions(nobs, 0)
        units1 = [json.dumps([nobs["farms"][0]["tiles"][p[1]][p[0]], nobs["private"]["inventories"][u] if u < len(nobs["private"]["inventories"]) else None], sort_keys=True, default=list) for u, p in enumerate(pos)]
        for u, cmd in enumerate(cmds):
            log.append({"day": day, "step": i - 1, "unit": u, "pos": pos[u] if u < len(pos) else None,
                        "after": after[u] if u < len(after) else None, "cmd": cmd,
                        "target": list(targets.get(u, ("", ""))),
                        "changed": u < len(units1) and u < len(units0) and units0[u] != units1[u]})
out = runs() / "exec-check" / f"{Path(a.game).stem}-d{a.days.replace(',', '_')}.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(log, default=list))

c = Counter()
for e in log:
    k = e["cmd"][0] if e["cmd"] else "PASS"
    c["turns"] += 1
    if k in MOVES:
        c["moves"] += 1
        c["blocked_moves"] += e["pos"] == e["after"]
    elif k == "PASS":
        c["pass"] += 1
    else:
        c["jobs_sent"] += 1
        c["jobs_no_visible_effect"] += not e["changed"]
        if not e["changed"]:
            c["no_effect:" + k] += 1
by_unit = {}
for e in log:
    by_unit.setdefault((e["day"], e["unit"]), []).append(e)
repeats = 0
for seq in by_unit.values():
    for x, y in zip(seq, seq[1:]):
        k = x["cmd"][0] if x["cmd"] else "PASS"
        if k not in MOVES and k != "PASS" and x["cmd"] == y["cmd"] and x["pos"] == y["pos"]:
            repeats += 1
c["same_job_command_repeated"] = repeats
print(json.dumps(dict(c), indent=1))
print("log ->", out)

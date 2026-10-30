"""Work-model data: decisions, labels and candidate jobs from a recorded game (step 1 of PLAN_WORK_MODEL.md).

A decision is a worker at a turn where it starts heading for a new job: its first turn of the day, or the turn
after it carried out a job. The label is the next job it actually carried out (a non-move action that took
effect, from the D1 `unit_actions` table) and where. Candidates are every job the engine would allow on the
worker's farm at that moment, not filtered by our rules.

A job is written as (kind, cell): kind like "WATER", "PLANT:WHEAT", "PICKUP:WHEAT", "PLACE:COW", "DROP";
cell is the tile index y*10+x, or "SHED" for jobs done at the shed.
"""
import json
import gzip
from pathlib import Path

import kaggle_environments.envs.kaggriculture.kaggriculture as K

MOVES = {"NORTH", "SOUTH", "EAST", "WEST"}
SIZE = 10
CROPS = tuple(K.CROPS)
ANIMALS = tuple(K.ANIMALS)


def load_replay(path):
    path = str(path)
    return json.load(gzip.open(path, "rt") if path.endswith(".gz") else open(path))


def job_of(command, x, y):
    """The job a non-move command performs, as (kind, cell); None for moves and PASS."""
    cmd = json.loads(command) if isinstance(command, str) else command
    if not cmd or cmd[0] in MOVES or cmd[0] == "PASS":
        return None
    op = cmd[0]
    item = cmd[1] if len(cmd) > 1 else None
    at_shed = K._is_shed_adjacent((x, y), SIZE)
    if op == "PLANT":
        return (f"PLANT:{item}", y * SIZE + x)
    if op == "PICKUP":
        return (f"PICKUP:{item}", "SHED")
    if op == "DROP":
        return ("DROP", "SHED")
    if op == "PLACE":
        if item in ANIMALS and not at_shed:
            return (f"PLACE:{item}", y * SIZE + x)
        return ("PLACE:GOODS", "SHED") if at_shed else (f"PLACE:{item}", y * SIZE + x)
    return (op, y * SIZE + x)


def candidates(obs, seat, unit):
    """Every job the engine allows for this worker now (or after one shed trip), as a set of (kind, cell)."""
    farm = obs["farms"][seat]
    private = obs["private"]
    inv = private["inventories"][unit] if unit < len(private["inventories"]) else {}
    shed, seeds = private["shed"], private["seeds"]
    has = lambda item: inv.get(item, 0) > 0 or shed.get(item, 0) > 0
    out = set()
    for y, row in enumerate(farm["tiles"]):
        for x, t in enumerate(row):
            if t == "LOCKED":
                continue
            c = y * SIZE + x
            if t is None:
                out |= {(f"PLANT:{crop}", c) for crop in CROPS if seeds.get(crop, 0) > 0}
                out |= {("BUILD_COOP", c), ("BUILD_PASTURE", c)}
                continue
            kind = t.get("kind")
            if kind == "WEED":
                out.add(("DIG", c))
            elif kind == "PLANT":
                out.add(("DIG", c))
                if not t.get("watered_today"):
                    out.add(("WATER", c))
                if t.get("yield_units", 0) > 0:
                    out.add(("HARVEST", c))
                if has("FERTILIZER"):
                    out.add(("FERTILIZE", c))
            elif "animal" in t:
                if not t.get("fed_today") and has("WHEAT"):
                    out.add(("FEED", c))
                if not t.get("cared_today"):
                    out.add(("CARE", c))
                if t.get("yield_units", 0) > 0:
                    out.add(("HARVEST", c))
                if t.get("fertilizer_available"):
                    out.add(("COLLECT_FERTILIZER", c))
            else:   # an empty coop or pasture
                out.add(("DIG", c))
                for a in ANIMALS:
                    if K.ANIMALS[a]["structure"] == kind and has(a):
                        out.add((f"PLACE:{a}", c))
    out |= {(f"PICKUP:{item}", "SHED") for item, n in shed.items() if n > 0}
    if any(n > 0 for n in inv.values()):
        out |= {("DROP", "SHED"), ("PLACE:GOODS", "SHED")}
    return out


def decisions(replay, seat, actions):
    """Yield (step, unit, label, candidate set) for one seat of one game.

    `actions`: rows (step, unit, x, y, command, took_effect) for this episode and seat, any order.
    """
    by_unit = {}
    for step, unit, x, y, command, took in sorted(actions, key=lambda r: (r[1], r[0])):
        by_unit.setdefault(unit, []).append((step, x, y, command, took))
    steps = replay["steps"]
    for unit, rows in by_unit.items():
        jobs = [(s, job_of(cmd, x, y)) for s, x, y, cmd, took in rows if took and x is not None]
        jobs = [(s, j) for s, j in jobs if j is not None]
        present = [s for s, x, *_ in rows if x is not None]
        starts = {s for s in present if (s - 1) not in present or (s - 1) // 24 != s // 24}   # first turn of a day
        starts |= {s + 1 for s, _ in jobs}
        k = 0
        for s in sorted(starts):
            while k < len(jobs) and jobs[k][0] < s:
                k += 1
            if k >= len(jobs) or jobs[k][0] // 24 != s // 24 or s not in present:
                continue      # no further job today: the worker only walked or waited
            obs = steps[s][seat]["observation"]
            yield s, unit, jobs[k][1], candidates(obs, seat, unit)

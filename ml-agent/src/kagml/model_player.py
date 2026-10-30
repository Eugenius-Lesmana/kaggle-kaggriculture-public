"""An agent whose workers are run by the learned ranker; the template agent keeps the plan and market orders.

Each turn: the template agent is asked for its full action (so its plan and market orders stay as they are); its
worker commands are then replaced. A worker without a target asks the ranker for its best job among every legal
job not already taken by an earlier worker this turn, keeps that target until it is done or no longer possible,
walks the shortest way to it and does it on arrival. A job that needs something from the shed (wheat to feed,
fertilizer, an animal to place) first sends the worker to pick it up.
"""
import json
from collections import Counter

import lightgbm as lgb
import numpy as np
import pandas as pd

from kagml.paths import models
from kagml.preview import TemplatePlayer
from kagml.work_data import candidates
from kagml.work_features import ANIMALS, CROPS, PRODUCTS, SHED_TILES, History, candidate_rows, context, dist

NEEDS = {"FEED": "WHEAT", "FERTILIZE": "FERTILIZER"}
SALE = ("CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL")     # goods carried only to be sold


def step_toward(pos, target):
    x, y = pos
    tx, ty = target
    if x != tx:
        return ["EAST"] if tx > x else ["WEST"]
    if y != ty:
        return ["SOUTH"] if ty > y else ["NORTH"]
    return ["PASS"]


class ModelPlayer(TemplatePlayer):
    def __init__(self, model_name="ranker-v1"):
        """`model_name` may carry options after colons: "redecide" (choose again every turn instead of keeping a
        target until it is done, so jobs on the way can be taken) and "fetch" (carry from the shed what all the
        open jobs of that kind need, not at most 4)."""
        super().__init__()
        model_name, *opts = model_name.split(":")
        self.redecide, self.fetch_all, self.keep = "redecide" in opts, "fetch" in opts, "keep" in opts
        self.shed, self.plan = "shed" in opts, "plan" in opts
        self.desired = {}
        window = next((o[1:] for o in opts if o.startswith("d") and "-" in o), None)    # "d6-28": ranker only on those days
        self.days = tuple(int(x) for x in window.split("-")) if window else None
        d = models() / model_name
        self.booster = lgb.Booster(model_file=str(d / "model.txt"))
        self.features = json.load(open(d / "features.json"))
        self.reset_work()

    def reset_work(self):
        self.history = History()
        self.targets = {}            # unit -> (kind, cell) chosen job
        self.last = {}               # unit -> (kind, step) of its previous job
        self.pending_sales = Counter()
        self.day = None

    def restore(self, memory):
        super().restore(memory[0] if isinstance(memory, tuple) else memory)
        if isinstance(memory, tuple):
            self.history = memory[1]
        self.targets, self.last, self.pending_sales, self.day = {}, {}, Counter(), None

    def memory(self):
        import copy
        return (super().memory(), copy.deepcopy(self.history))

    def warm_step(self, observation, configuration=None):
        """Used while rebuilding memory from a recording: update the template and the price history only."""
        self.module.agent(observation, configuration)
        self.history.add(observation, Counter())

    def _command(self, unit, job, pos, inv, obs, legal=()):
        kind, cell = job
        base, _, item = kind.partition(":")
        need = NEEDS.get(base) or (item if base == "PLACE" and item in ANIMALS else None)
        if need and inv.get(need, 0) == 0:                      # fetch it first
            shed = min(SHED_TILES, key=lambda s: dist(pos, s))
            if pos != shed:
                return step_toward(pos, shed)
            want = 3 if self.shed else 4
            if self.fetch_all and need not in ANIMALS:      # enough for every open job of this kind
                want = max(1, sum(1 for c in legal if c[0].partition(":")[0] == base))
            n = 1 if need in ANIMALS else min(obs["private"]["shed"].get(need, 0), want)
            return ["PICKUP", need, max(1, n)]
        target = min(SHED_TILES, key=lambda s: dist(pos, s)) if cell == "SHED" else (cell % 10, cell // 10)
        if pos != target:
            return step_toward(pos, target)
        if base == "PLANT":
            wanted = self.desired.get(cell)
            if self.plan and wanted in CROPS and obs["private"]["seeds"].get(wanted, 0) > 0:
                return ["PLANT", wanted]
            return ["PLANT", item]
        if base == "PICKUP":
            n = 1 if item in ANIMALS else min(obs["private"]["shed"].get(item, 0), 3 if self.shed else 4)
            return ["PICKUP", item, max(1, n)]
        if base == "PLACE" or base == "DROP":
            if base == "PLACE" and item != "GOODS":
                return ["PLACE", item]
            if self.shed and inv.get("WHEAT", 0) and self._uncovered_feed(obs, unit) > 0:
                goods = {k: n for k, n in inv.items() if n > 0 and k in SALE}
                if goods:                                           # keep the wheat; unload the largest good
                    k = max(goods, key=goods.get)
                    return ["PLACE", k, goods[k]]
            if self.keep:
                tools = {k for k, n in NEEDS.items() if any(c[0].partition(":")[0] == k for c in legal)}
                goods = {k: n for k, n in inv.items() if n > 0 and k not in {NEEDS[t] for t in tools}}
                if len(goods) == 1 and len(goods) < len([k for k, n in inv.items() if n > 0]):
                    (k, n), = goods.items()
                    return ["PLACE", k, n]
            return ["DROP"]
        return [base]

    @staticmethod
    def _wasteful_shed_job(job, inv):
        """Shed jobs the teacher almost never does: unloading with nothing to sell; fetching what is carried."""
        kind = job[0]
        if kind in ("DROP", "PLACE:GOODS"):
            return not any(n > 0 for k, n in inv.items() if k in SALE)
        if kind in ("PICKUP:WHEAT", "PICKUP:FERTILIZER"):
            return inv.get(kind.split(":")[1], 0) > 0
        return False

    @staticmethod
    def _uncovered_feed(obs, unit):
        """Animals not yet fed today, minus wheat carried by the other workers."""
        unfed = sum(1 for row in obs["farms"][obs["player"]]["tiles"] for t in row
                    if isinstance(t, dict) and t.get("animal") and not t.get("fed_today"))
        others = sum(b.get("WHEAT", 0) for i, b in enumerate(obs["private"]["inventories"]) if i != unit)
        return unfed - others

    def __call__(self, observation, configuration=None):
        obs = observation
        seat = obs["player"]
        action = dict(self.module.agent(obs, configuration))          # plan and market orders from the template
        if obs["day"] != self.day:
            self.day, self.targets = obs["day"], {}
        if self.days and not self.days[0] <= obs["day"] <= self.days[1]:
            self.history.add(obs, self.pending_sales)
            self.pending_sales = Counter({o[1]: int(o[2]) for o in action.get("market", []) if o and o[0] == "SELL" and len(o) > 2})
            return action
        self.history.add(obs, self.pending_sales)
        self.pending_sales = Counter({o[1]: int(o[2]) for o in action.get("market", []) if o and o[0] == "SELL" and len(o) > 2})
        ctx = context(obs, seat, self.history)
        positions = ctx["_positions"]
        if self.plan:                       # the template's layout for today (computed on a copy of its memory)
            import copy
            try:
                self.desired = self.module._desired(obs, copy.deepcopy(self.module._STATES[seat]))
            except Exception:
                self.desired = {}
        step = obs["day"] * 24 + obs["hour"]
        taken, commands = set(), []
        for unit, pos in enumerate(positions):
            inv = obs["private"]["inventories"][unit] if unit < len(obs["private"]["inventories"]) else {}
            legal = candidates(obs, seat, unit)
            job = self.targets.get(unit)
            if self.redecide or job is None or job not in legal or job in taken:
                options = [c for c in sorted(legal, key=str) if c not in taken or c[1] == "SHED"]   # fixed order: ties no longer depend on the hash seed
                if self.shed:
                    options = [c for c in options if not self._wasteful_shed_job(c, inv)] or options
                if not options:
                    commands.append(["PASS"])
                    continue
                last_kind, last_step = self.last.get(unit, (None, -999))
                rows = candidate_rows(obs, seat, unit, options, ctx, last_kind, step - last_step)
                frame = pd.DataFrame(rows)
                for c in self.features:
                    if c not in frame:
                        frame[c] = np.nan
                scores = self.booster.predict(frame[self.features].astype(np.float32))
                job = options[int(np.argmax(scores))]
                self.targets[unit] = job
            taken.add(job)
            cmd = self._command(unit, job, pos, inv, obs, legal)
            if cmd[0] not in ("NORTH", "SOUTH", "EAST", "WEST", "PASS") and cmd[0] != "PICKUP" or (cmd[0] == "PICKUP" and job[0].startswith("PICKUP")):
                self.targets.pop(unit, None)                          # the job is done this turn
                self.last[unit] = (job[0].split(":")[0], step)
            commands.append(cmd)
        action["farmer"], action["hands"] = commands[0], commands[1:]
        return action

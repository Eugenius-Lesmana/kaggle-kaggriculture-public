"""Preview harness: load one moment of a game into a fresh engine and let any players continue from it.

A snapshot is everything the engine needs at a step: both seats' observations (farms, market, town, each seat's
private inventory) and the game's seed (the town and weeds draw from it). Players are callables
`act(observation, configuration) -> action`, or the string "recorded" to replay a recorded game's moves.

Typical use:
    snap = snapshot_from_replay(replay, step=240)
    ours = TemplatePlayer(); ours.warm(replay, seat=0, upto=240)
    end = play(snap, [ours, "recorded"], steps=24, replay=replay)
"""
import copy
import importlib.util
import itertools
import random
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.utils import structify
import kaggle_environments.envs.kaggriculture.kaggriculture as K

from kagml.paths import REPO

PRODUCTS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON", "EGG", "MILK", "WOOL", "FERTILIZER")
_ORIG_WEEDS = K._spawn_weeds


def pin_weeds(on: bool):
    """Our own runs pin the weed draw (one draw per farm) so shops depend on the seed alone; Kaggle replays do not."""
    K._spawn_weeds = ((lambda farm, n, chance, rng: _ORIG_WEEDS(farm, n, chance, random.Random(rng.random())))
                      if on else _ORIG_WEEDS)


def snapshot_from_replay(replay: dict, step: int) -> dict:
    steps = replay["steps"]
    return {"seed": replay["info"]["seed"], "step": step,
            "obs": [copy.deepcopy(steps[step][p]["observation"]) for p in (0, 1)]}


def snapshot_from_env(env) -> dict:
    return {"seed": env.info["seed"], "step": int(env.state[0].observation.step),
            "obs": [copy.deepcopy(dict(env.state[p].observation)) for p in (0, 1)]}


def env_from_snapshot(snap: dict):
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": snap["seed"]}, debug=False)
    env.reset(2)
    for p in (0, 1):
        env.state[p].observation = structify(copy.deepcopy(snap["obs"][p]))
        env.state[p].observation.player = p
    for key in ("farms", "market", "town"):      # the engine shares these objects between the seats
        env.state[1].observation[key] = env.state[0].observation[key]
    env.state[1].observation.step = snap["step"]
    env.steps = [env.steps[0]] * snap["step"] + [env.state]   # the framework counts turns by its history length
    return env


def play(snap: dict, players: list, steps: int, replay: dict | None = None):
    """Continue the game from `snap` for `steps` turns with the given players; returns the engine at the end."""
    env = env_from_snapshot(snap)
    start = snap["step"]
    for i in range(start + 1, min(start + steps, 719) + 1):
        actions = []
        for p, player in enumerate(players):
            if player == "recorded":
                actions.append(replay["steps"][i][p]["action"])
            else:
                actions.append(player(env.state[p].observation, env.configuration))
        env.step(actions)
        if env.done:
            break
    return env


def summary(env, prices: dict | None = None) -> list[dict]:
    """Per seat: cash, goods held (shed and bags) at current prices, crop and animal counts, hands, land."""
    obs = env.state[0].observation
    prices = prices or dict(obs.market.prices)
    out = []
    for p in (0, 1):
        farm, private = obs.farms[p], env.state[p].observation.private
        held = {k: private["shed"].get(k, 0) + sum(b.get(k, 0) for b in private["inventories"]) for k in PRODUCTS}
        tiles = [t for row in farm.tiles for t in row if isinstance(t, dict)]
        out.append({"cash": farm.money, "goods": sum(held[k] * prices.get(k, 0) for k in PRODUCTS),
                    "crops": sum(t.get("kind") == "PLANT" for t in tiles),
                    "animals": sum(bool(t.get("animal")) for t in tiles),
                    "hands": len(farm.hands), "land": len(farm.unlocked_quadrants)})
    return out


class TemplatePlayer:
    """Our rule-based template agent as a player, with its memory (module-level _STATES) kept per instance."""
    _ids = itertools.count()

    def __init__(self, path: str | Path = REPO / "vendor" / "template_agent" / "main.py"):
        spec = importlib.util.spec_from_file_location(f"template_{next(self._ids)}", path)
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    def __call__(self, observation, configuration=None):
        return self.module.agent(observation, configuration)

    def warm(self, replay: dict, seat: int, upto: int):
        """Rebuild the agent's memory by showing it the recorded observations before `upto` (actions discarded)."""
        for i in range(upto):
            obs = replay["steps"][i][seat]["observation"]
            obs.setdefault("step", i)   # Kaggle replays omit step from the second seat's observation
            self(obs, replay.get("configuration"))

    def memory(self):
        return copy.deepcopy(self.module._STATES)

    def restore(self, memory):
        self.module._STATES.clear()
        self.module._STATES.update(copy.deepcopy(memory))

"""D2 loader contract: cached weights, isolated imports, cold clocks and RNG.
python tools/test_opponents.py <recorded-game.json>
"""
import copy
import json
from pathlib import Path
import sys
import types

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from kagml.opponents import load, NAMES
import torch

replay = json.loads(Path(sys.argv[1]).read_text())
paths = sys.path[:]
old = sys.modules.get("model")
sentinel = types.ModuleType("model")
sys.modules["model"] = sentinel
checks = []
try:
    before = torch.random.get_rng_state().clone()
    players = {name: load(name) for name in NAMES}
    assert torch.equal(before, torch.random.get_rng_state()), "loading changed host RNG"
    for name, actor in players.items():
        assert actor is load(name), "weights reloaded"
        weight = actor.play._NET["m"] if actor.play else actor.actor.policy
        for seat in (0,1):
            obs = copy.deepcopy(replay["steps"][240][seat]["observation"])
            obs["player"] = seat
            actor.reset(10301)
            first = actor(obs, replay["configuration"])
            # A stale seat-1 shared clock must not silently become a PASS.
            obs["step"] = 0
            actor.reset(10301)
            before = torch.random.get_rng_state().clone()
            second = actor(obs, replay["configuration"])
            assert first == second, (name, seat, "reset/clock mismatch")
            assert torch.equal(before, torch.random.get_rng_state()), "call changed host RNG"
            assert sys.path == paths and sys.modules["model"] is sentinel, "import leakage"
            assert weight is (actor.play._NET["m"] if actor.play else actor.actor.policy)
            assert not actor.diagnostics()["fallbacks"]
            assert first.get("market") or any(c and c[0] != "PASS" for c in
                [first.get("farmer", [])] + list(first.get("hands") or [])), "only PASS"
            checks.append({"name":name,"seat":seat,"threads":actor.threads,"action":first})
finally:
    if old is None:
        sys.modules.pop("model",None)
    else:
        sys.modules["model"] = old
print(json.dumps({"checks":checks,"passed":len(checks)},indent=2))

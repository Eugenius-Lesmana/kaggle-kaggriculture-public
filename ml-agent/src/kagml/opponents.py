"""Held-out CPU policies; upstream code and weights stay on D:.
load(name) caches one actor per process. reset(seed) clears game memory, not weights.
Calls are serialized to isolate the packages' colliding absolute import names.
"""
import importlib.util
import os
import sys
import threading
import time
from contextlib import contextmanager
from functools import cache
from kagml.paths import data_root

NAMES = ("fifth-n1", "fifth-nflow", "fourth")
_FOLDERS = {
    "fifth-n1": ("fifth-place/n1-main-sprinkle", "primitive-bc-v1-deploy-v9-decode"),
    "fifth-nflow": ("fifth-place/nflow-main-wash8014", "n-flow-deploy"),
    "fourth": ("fourth-place/fourth-place-model", None),
}
_LOCK = threading.RLock()


class Opponent:
    def __init__(self, name):
        self.name = name
        self.threads = 2 if name == "fifth-n1" else 1
        folder, deploy = _FOLDERS[name]
        self.root = data_root() / "opponents" / folder
        if not (self.root / "main.py").is_file():
            raise FileNotFoundError(f"Unpack the {name} archive into {self.root}")
        self.paths = ([self.root / "work/runs/maintainer" / deploy, self.root / "src"]
                      if deploy else [self.root])
        self.names = {p.stem for p in (data_root() / "opponents").rglob("*.py")}
        self.names.update(("farm_neat", "pbc_agent", "_kagml_published"))
        self.modules = {}
        begun = time.perf_counter()
        os.environ["CUDA_VISIBLE_DEVICES"] = ""
        for key in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
            os.environ[key] = "1"
        import torch
        torch.set_num_threads(self.threads)
        try:
            torch.set_num_interop_threads(1)
        except RuntimeError:
            pass
        with self._imports(), torch.random.fork_rng(devices=[]):
            if deploy:
                spec = importlib.util.spec_from_file_location("_kagml_published", self.paths[0] / "agent.py")
                module = importlib.util.module_from_spec(spec)
                sys.modules[spec.name] = module
                spec.loader.exec_module(module)
                self.actor = module.make_agent(str(self.root / "policy.pt"), seed=0,
                                               temperature=0.0, threads=self.threads, log=False,
                                               decode={"mode": "greedy"})
                self.actor._ensure_loaded()
                self.play = None
            else:
                import play
                play._load(str(self.root / "weights.pt"), device="cpu")
                self.play = play
                self.actor = play.agent
        self.load_seconds = time.perf_counter() - begun
        self.reset()

    def _owned(self, name):
        return name.split(".")[0] in self.names

    @contextmanager
    def _imports(self):
        with _LOCK:
            previous = {k: v for k, v in sys.modules.copy().items() if self._owned(k)}
            paths = sys.path[:]
            for key in previous:
                del sys.modules[key]
            sys.modules.update(self.modules)
            sys.path[:0] = [str(p) for p in self.paths]
            try:
                yield
            finally:
                self.modules = {k: v for k, v in sys.modules.copy().items() if self._owned(k)}
                for key in self.modules:
                    del sys.modules[key]
                sys.modules.update(previous)
                sys.path[:] = paths

    def reset(self, seed=0):
        """Start an independent game/preview without reloading weights."""
        import torch
        with self._imports():
            if self.play:
                self.play._reset_flow()
                self.rng = torch.Generator(device="cpu").manual_seed(seed).get_state()
            else:
                self.actor._states.clear()
                self.actor.generator.manual_seed(self.actor.seed)
            self.last_steps = {}

    def __call__(self, observation, configuration=None):
        import torch
        # Direct engine seat-1 observations can omit or retain a stale shared step.
        # day/hour are updated for both seats by the interpreter.
        step = int(observation["day"]) * 24 + int(observation["hour"])
        observation = {**observation, "step": step}
        seat = int(observation["player"])
        with self._imports():
            if torch.get_num_threads() != self.threads:
                torch.set_num_threads(self.threads)
            if seat in self.last_steps and step != self.last_steps[seat] + 1:
                if self.play:
                    self.play._FLOW.pop(seat, None)
                else:
                    self.actor._states.pop(seat, None)
            if self.play:
                outer_rng = torch.random.get_rng_state()
                torch.random.set_rng_state(self.rng)
                try:
                    action = self.actor(observation, configuration)
                finally:
                    self.rng = torch.random.get_rng_state()
                    torch.random.set_rng_state(outer_rng)
            else:
                action = self.actor(observation, configuration)
                if self.actor.last_fallback:
                    raise RuntimeError(f"{self.name} upstream PASS fallback: {self.actor.last_error}")
            self.last_steps[seat] = step
            return action

    def diagnostics(self):
        if self.play:
            return {"fallbacks": 0, "search_errors": 0}
        return {"fallbacks": self.actor.fallbacks, "errors": list(self.actor.errors),
                "search_errors": self.actor.search_errors,
                "search_error_log": list(self.actor.search_error_log)}


@cache
def load(name):
    """Return act(observation, configuration) for fifth-n1, fifth-nflow or fourth."""
    if name not in NAMES:
        raise ValueError(f"Unknown opponent {name!r}; choose from {', '.join(NAMES)}")
    return Opponent(name)

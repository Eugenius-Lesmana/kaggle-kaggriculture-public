"""Load one moment of a recorded game straight into a fresh engine (no earlier moves), then play a day forward.
python tools/snapshot_probe.py <game.json> [step]
Checked 2026-10-17 on run el3 seed 10301 from steps 240, 400 and 600: snapshot loads in 5-8 ms, one day forward
0.3-0.4 s, both players' cash identical to the recording. Two details matter: the daily random draws use the
game's info.seed, and the framework counts turns by the length of its history, so the history is padded."""
import json, random, sys, time, copy
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kaggle_environments.utils import structify

orig = K._spawn_weeds
K._spawn_weeds = lambda farm, n, chance, rng: orig(farm, n, chance, random.Random(rng.random()))
rep = json.load(open(sys.argv[1])); st = rep['steps']; N = int(sys.argv[2]) if len(sys.argv) > 2 else 240

env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": rep['info']['seed']}, debug=False)
env.reset(2)
t = time.perf_counter()
for p in (0, 1):                                   # the snapshot: each seat's observation at step N
    env.state[p].observation = structify(copy.deepcopy(st[N][p]['observation']))
env.state[1].observation.farms = env.state[0].observation.farms      # the engine shares these between seats
env.state[1].observation.market = env.state[0].observation.market
env.state[1].observation.town = env.state[0].observation.town
env.steps = [env.steps[0]] * N + [env.state]       # the framework counts turns by the length of its history
print('snapshot loaded in %.3fs' % (time.perf_counter() - t))
t = time.perf_counter()
for i in range(N + 1, N + 25):
    env.step([st[i][p]['action'] for p in (0, 1)])
print('one day forward %.2fs' % (time.perf_counter() - t))
for p in (0, 1):
    print('seat', p, 'money', env.state[0].observation.farms[p].money, 'recorded', st[N + 24][0]['observation']['farms'][p]['money'])

"""Preview probe (Stage 1 groundwork): rebuild a recorded game from its actions, copy it at day 10, play one day forward.
python tools/preview_probe.py <game.json>   (our own runs; uses the game's info.seed and the runner's weed pin)
First result 2026-10-17 on run el3 seed 10301: 240 steps rebuilt exactly (0 money mismatches) in 1.8 s; copying the
game with deepcopy 1.7 s (too slow, to replace); one day forward 0.2 s with recorded actions."""
import json, time, copy, random, sys
from kaggle_environments import make
import kaggle_environments.envs.kaggriculture.kaggriculture as K
orig = K._spawn_weeds
K._spawn_weeds = lambda farm, n, chance, rng: orig(farm, n, chance, random.Random(rng.random()))  # same pin as the runner
rep = json.load(open(sys.argv[1])); seed = rep['info']['seed']; st = rep['steps']
env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed}, debug=False)
env.reset(2)
t = time.perf_counter(); bad = 0
for i in range(1, 241):                       # replay recorded actions through day 9
    acts = [st[i][p]['action'] for p in (0, 1)]
    env.step(acts)
    for p in (0, 1):
        if abs(env.state[0].observation.farms[p].money - st[i][0]['observation']['farms'][p]['money']) > 0.5: bad += 1
print('replayed 240 steps in %.2fs, money mismatches %d' % (time.perf_counter() - t, bad))
t = time.perf_counter(); fork = copy.deepcopy(env); print('fork (deepcopy) %.3fs' % (time.perf_counter() - t))
t = time.perf_counter()
for i in range(241, 265):                     # one day forward on the fork, same recorded actions
    fork.step([st[i][p]['action'] for p in (0, 1)])
print('one day forward on the fork %.2fs; money ours %s vs recorded %s' % (time.perf_counter() - t,
      fork.state[0].observation.farms[0].money, st[264][0]['observation']['farms'][0]['money']))

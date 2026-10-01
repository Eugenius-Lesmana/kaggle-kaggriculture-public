# V0.10: transplanting the top-four plan into our planner — result

Date: 2026-09-25
Status: **transplant rejected; our planner cannot execute the top-four plan.**
- Candidate: `agents/ours/v0.10.0-candidate/` on `dev/eugene-claude-v010`, with every
  transplant module behind a flag.
- Control: the confirmed v0.10.0, i.e. v0.9.4 + replanting on the harvest visit
  (`docs/V010_EXECUTION_FIX_2026-09-25.md`).
- Evidence: `evaluation/v010_top4/`.
- Protocol: tuning seeds 6141–6200, both seats, vs Metav4, More Wheat and V46.
  n = 360 per arm. Metric: the paired change in the ratio of our bank to the
  opponent's (± 95%).

## What was built

- **Opener:** the day 0–5 actions of Team A episode 112920694, the game closest to the
  per-step majority of all 46. They are replayed while every worker stands where that
  game had it. Our planner reproduces the rest: the day-5 farm matched **100%** in
  every test game.
- **Skeleton:**
  - land at steps 150 / 220 / 254, funded by selling on the same step;
  - their worker count per day;
  - the planner's crop and animal target on each day set to the top four's consensus
    farm for that day (the most common content of each cell). Mid-game layout
    matched 82–91%.
- **Fertilizer programme:** load fertilizer from the shed for fertilize jobs; keep a
  reserve; no action surcharge in the value threshold; harvest wheat at age 3.

## Results

| arm | ratio change | own bank |
|---|---:|---:|
| full skeleton (opener + land + layout + hands) | **−0.105 ± 0.009** | −12% |
| opener only (their days 0–5, then our planner) | **−0.034 ± 0.009** | −5% |
| hands only (their worker schedule) | −0.001 ± 0.004 | −2% |
| wheat at age 3 | −0.002 ± 0.001 | 0% |
| fertilize anything carried (lower threshold) | **−0.032 ± 0.004** | −4% |
| sell-hold on wool / milk / strawberry | −0.005 ± 0.002 | −1% |

**Fertilizer programme and worker balancing on top of the skeleton** (3 diagnostic
seeds only; not worth a full screen):
- **Fertilizer:** applications rose to 82–85 a game (theirs: 88), but harvests fell
  from 217 to 158, collections from 193 to 121, and geese collapsed from 5 to 1.
  Day-19 cash fell from $39k to $27k.
- **Worker balancing:** only added walking (51–54% of worker turns). Cash was no
  better.

## Why it fails

With the same 12–13 workers, the top four do more of everything (days 6–19, per game):

| | top four | us, running their plan |
|---|---:|---:|
| harvests | 237 | 158–217 |
| fertilizer collections | 249 | 121–193 |
| care visits | 224 | 109–190 |
| fertilizings | 88 | 15–85 |
| idle worker turns | 2% | 7–15% |

Their plan is labour-dense and only pays when all of it is executed:
- the strawberries have to be fertilized to reach 2 units per harvest (we got 1.2);
- the animals have to be serviced, or they stop producing;
- the land and cash have to be put to work at once.

Our scheduler's routing (greedy, per cell, walking to the shed for every load) cannot
supply that labour. Every piece we moved over made us worse, because it created work
we could not do well. **The top four's edge is their executor as much as their plan.**
That matches everything since 22 Sept: plan features never transferred on their own.

## What this means

- Our planner is at ~0.68 of Metav4's bank, and the modules tested here move it by at
  most ±3 points. **The planner route cannot reach Metav4's level before the deadline.**
- The **route-112 re-fit of Metav4** (+3.6% on tuning, `docs/ROUTE_REFIT_2026-09-23.md`)
  remains our strongest submission candidate. It needs its pre-registered
  confirmation before submission.
- Reproducing the top-four plan would need a new executor: a batched, route-planned
  worker scheduler. That is a multi-day build with uncertain payoff.

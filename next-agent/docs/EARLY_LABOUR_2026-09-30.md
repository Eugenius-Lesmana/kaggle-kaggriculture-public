# Where our planner's worker time goes, and three early-labour experiments

Date: 2026-09-30
Branch: `dev/eugene-claude-routeopt`
Status: **measurement plus negative results.** The route-optimiser premise is refuted, and
three production tweaks are neutral.

## 1. Diagnostic (`evaluation/routeopt/diag.py`)

Our planner, v0.10, played 10 games against Metav4 (seeds 7601–7610, 2 workers).
Service left undone at hour 23 counts unfed or uncared animals, dying unwatered plants and
overdue harvests.

| phase | idle | walking | working | useful actions / game | left undone at 23:00 |
|---|---:|---:|---:|---:|---|
| days 0–5 | **52%** | 23% | 25% | 207 | feed 7%, others ≤ 4% |
| days 6–11 | **29%** | 36% | 36% | 460 | ~none |
| days 12–19 | 13% | 44% | 43% | 856 | care 7% |
| days 20–27 | 6% | 47% | 47% | 937 | care 14% |

The top-four plan on the same executor (`skel`) gives the same picture:
- idle 47% on days 0–5 and 28% on days 6–11;
- more work later (997 and 1,092 useful actions per game);
- nothing left undone;
- but a **lower bank**, 0.617 of the opponent's against 0.701.

**Reading:**
- The executor completes almost every job that falls due.
- Walking (36–47%) matches Team A's replays (~47%, `docs/EXECUTOR_PROTOTYPE_2026-09-29.md`).
- The gap to the top agents is early idle time. Team A idles about 3% on days 6–11.
- A route optimiser would free time the plan has no work for.
- This refutes the diagnosis in `docs/V010_TOP4_TRANSPLANT_2026-09-25.md` that our executor
  was labour-bound.
- Hiring is cheap: the n-th hire of a day costs fib(n), so about $376 for 12 hands. The
  idle labour is unused potential, not wasted wages.

## 2. Fertilizer (`evaluation/routeopt/fert_probe.py`)

**Flows per game:**
- about 300 units collected;
- about 45 applied: 0 on days 0–5, **2 on days 6–11**, about 21 on days 12–19 and about 22 on
  days 20–27;
- the rest sold.

**Why days 6–11 see almost none** (probe, seed 7601):
- The wheat on the farm (15–25 plants) would gain from fertilizer, but fertilizer quotes
  **$100 → $68**. That exceeds the 1–2 extra wheat units it adds (about $38 each).
- Strawberries only gain from day 14.
- The quote falls to $2 by day 28 as both players sell. The realised average is about $48.

**Experiments** (80 games each, paired on identical seeds and seats against Metav4):

| arm | seeds | applications / game | ratio change |
|---|---|---:|---:|
| no worker-time charge before day 12 | 7611–7650 | about 4 on days 6–11 (was 2) | −0.003 ± 0.008 |
| no charge before day 20 | 7611–7650 | — | −0.014 ± 0.009 |
| fertilizer valued at 0.5 × quote | 7651–7690 | 60 (was 46) | **+0.009 ± 0.010** |
| 0.5 × quote and no charge before day 12 | 7651–7690 | 74 | −0.016 ± 0.014 |

**Reading:**
- Early fertilizer really does sell for about $90–100.
- Using it on wheat gives up high-value sales.
- More fertilizing does not turn idle early labour into money on our farm.

## 3. More animals (`A1`, seeds 7691–7730)

The change adds two animals per bought plot (taken from strawberry cells) and raises the cap
from 5 to 7.

| | v0.10 | A1 |
|---|---:|---:|
| ratio change | — | −0.012 ± 0.020 |
| eggs / milk / wool sold | 70 / 130 / 158 | 102 / 155 / 180 |
| strawberries / wheat sold | 161 / 310 | 130 / 250 |
| revenue / game | $100.6k | $98.9k |

More animal products do not pay for the strawberries they displace and the wheat they eat.

## Conclusion

The planner is at a local optimum for its structure:
- execution is not the limit;
- simple levers on fertilizer and herd size are neutral.

The early-game difference from the top agents is in the **plan itself**, i.e. what exists
on days 0–10. For example, their day-0 strawberries produce from day 10.

The open question is why the top-four plan, run on our executor, earns less despite doing
more work.

Flags in `agents/ours/v0.11.0-candidate`:
- `FERT_PRICE_SCALE` (1.0), off by default;
- `FERT_FREE_UNTIL_DAY` (0), off by default.

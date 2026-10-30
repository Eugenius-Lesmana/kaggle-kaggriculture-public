# Micro fixes, all-days model and the market pressure (2026-10-25)

**Plain answer.** None of the micro fixes improves on v3-fw, alone or combined; the all-days model is worse than
using v3-fw on days 6-28 only. **v3-fw on days 6-28 stays the best agent** (share of Metav4's bank 0.966 in full
games). Codex found that Metav4's missing 17,000 against the teacher is lower prices for strawberries, milk and
wool, caused by the teacher bringing more of them to market earlier: a production-volume gap, not a trick.

## 1. Micro fixes (same morning, one day, 105 analysis mornings, models trained on the 14 training games)

Value per day against v3s-fw (v3-fw's recipe, 14 games):

| Change | vs v3-fw | What changed in the work |
|---|---:|---|
| Shed rule (teacher's habits, package S) | +19 (se 35) | drops 4.6 -> 2.6 a day (teacher 2.7); pickups 12.3 -> 11.5 (teacher 8.8) |
| Sweep features (continue the last move, jobs further along, distance to the next job) | -6 (se 44) | none clear |
| Sweep features + narrow costly-decision weighting | +31 (se 40) | none clear |
| Planting follows the template's layout | -1 (se 22) | none clear |
| **All combined** (sweep + plan + shed) | **-124 (se 47)** | clearly worse |

- 147 of 148 shed actions on 9 test days were jobs the ranker chose itself, not the fetch rule.
- The sweep features separate the teacher's choices in the data (open jobs further along: 4.0 for its pick vs
  1.4 for alternatives) but the retrained ranker does not play measurably better.
- Reading: inside the current design (one worker at a time picks a job, then walks there) these levers are
  exhausted. The teacher's workers still beat ours by +369 a day under our own plan (measured earlier).

## 2. All-days model (Codex's package E data)

840 teacher day-runs for days 0-5 and 29 (L1-edge 168, L3-edge 672; all validated). v3e-fw = v3-fw's recipe plus
32,713 decisions from those days, used on every day.

Full games, fresh seeds 20001-20024, both seats, against Metav4:

| Player | Our bank | Metav4 | Share | Wins | Median / max ms per turn |
|---|---:|---:|---:|---:|---:|
| Teacher | 114,908 | 80,661 | 1.425 | 48/48 | 85 / 1,992 |
| **v3-fw, days 6-28** | **94,640** | **98,009** | **0.966** | **16/48** | 341 / 1,263 |
| v3e-fw, all days | 90,095 | 103,708 | 0.869 | 4/48 | 457 / 2,109 |
| Template | 92,322 | 101,720 | 0.908 | 4/48 | 9 / 249 |

v3e-fw against v3-fw (days 6-28), paired by seed: bank -4,545 (se 1,092), margin -10,243 (se 1,420), better on
1 of 24 seeds. Even with teacher examples, letting the ranker run days 0-5 and 29 loses against the template's
tuned opener there.

**Time per turn:** the ranker's slowest turns exceed one second (v3-fw on days 6-28: up to 1.26 s; v3e-fw up to
2.1 s). The median is well under. Whether occasional slow turns fit the competition's overage allowance has not
been checked.

## 3. Market pressure (Codex, package M)

Metav4 ends 17,349 (se 1,880) lower against the teacher than against v3-fw:

| Product | Metav4's loss |
|---|---:|
| Strawberry | 5,256 |
| Milk | 4,648 |
| Wool | 4,005 |
| Wheat, tomato, fertilizer, carrot, melon, egg | 3,570 |
| Spending (offset) | -130 |

- Mechanism: Metav4 sells nearly the **same quantities at lower prices** (price effect -17,673; quantity +195).
  By day 18 the teacher's matchup has about 22 more strawberries, 10 more milk and 8 more wool in market stock;
  prices stay lower through days 18-29. Not a shop-stock race and not order position.
- Timing: most of the loss is on days 18-23 (8,399) and 24-29 (6,266).
- So the teacher's margin lead and its own extra income come from the same thing: **more strawberries, milk and
  wool, produced and sold earlier**.

## 4. What this means

- The per-worker job ranker has reached its ceiling: v3-fw on days 6-28 (share 0.966).
- The remaining gap is production volume of premium goods (strawberries, milk, wool) earlier in the season. That
  is partly the plan (crop mix and herd: the template's choices) and partly the workers (the teacher's workers
  still do +369 a day more under our plan).
- Options: (a) the plan stage (crop mix, herd, timing, learned from the teacher's or top teams' games); (b) a
  per-turn model that moves all workers together, as the teacher does; (c) your top-team layout fallback.

Evidence: `runs/compare/s1*.csv`, `s2*.csv`, `sel*.csv`; `runs/full-v3e/`, `runs/full-v3fw-d628*/`,
`runs/full-teacher/`; Codex: `reports/MARKET_PRESSURE_*.csv`, `handoff/2026-10-2X-codex-to-claude-market-pressure.md`,
`handoff/2026-10-2X-codex-to-claude-edge-days.md`.

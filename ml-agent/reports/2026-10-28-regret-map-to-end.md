# Regret map, final-bank version (2026-10-28)

**Answer:** swapping one of our days for the teacher's day gains on average ~640 in final margin, spread across
all days; no situation predicts the costly days well, but **hours 12-20 lose money in every phase of the game**.

Setup: `tools/regret_map.py --to-end`, best agent `net:board-p4:market:overflow:endmask:endwork`, 12 games
(src-best-eval, seeds 20001-20012, seat 0), days 6, 8, ... 28, takeover hours 0/12/20. After the day, a fresh
teacher plays both branches to the end against the opponent tape. Metric `final_margin` (teacher's day minus ours).
Rows: `<data>/runs/regret-end-12/rows.csv`. Analysis: scratchpad `regret_report.py`.

## Measured

| days  | sum over sampled days, per game | se    |
|-------|---------------------------------|-------|
| 6-11  | 2,466                           | 933   |
| 12-17 | 1,218                           | 917   |
| 18-23 | 2,350                           | 1,268 |
| 24-28 | 1,662                           | 666   |
| all 12 sampled days | 7,696             | 2,271 |

Only every second day was sampled. Largest single day: 20 (1,561, se 481).

Within the day (per game-day):

| days  | hours 0-12 | hours 12-20 | hours 20-24 |
|-------|-----------:|------------:|------------:|
| 6-11  | 532        | 366         | -76         |
| 12-17 | 11         | 375         | 20          |
| 18-23 | 289        | 689         | -195        |
| 24-28 | 22         | 474         | 57          |

Afternoon (12-20) overall: 476 per game-day, se 140. Hours 20-24 are fine (overflow and end rules work).

- Spread out: the top 20% of game-days hold 56% of positive regret; we beat the teacher on 33% of game-days.
- Morning situation barely predicts cost (all |r| <= 0.14).
- The gain is our own bank (teacher's day: our final +660 a day on average); fifth-nflow's final barely moves.
- Teacher minus ours, rest of the day:
  - on costly days it plants tomatoes (2.1 against 0.2) and buys tomato seeds;
  - it waters more, feeds and cares less, fertilises more and sells more wool;
  - every afternoon it buys about 1.5 fewer wheat seeds than we do.

## Caveats

12 games and one seat. A single day's change moves the final bank by about ±3k, so only the aggregates are usable.
These games are on evaluation seeds: use them for diagnosis only, never as training labels.

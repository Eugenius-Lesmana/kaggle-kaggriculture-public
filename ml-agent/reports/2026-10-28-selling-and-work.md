# Selling and work after rules — 2026-10-28

**The teacher earns +9,314 more sale revenue/game in this sample: +1,456 from volume and +7,858 from realized prices by the exact decomposition below.** The ruled agent still discards 2.69 product units at night per game, versus 1.00 for the teacher.

The tables below separate remaining native-measured overflow, sale volume, realized prices and work mix. Comparisons use seeds 20001–20008, both seats: 16 ruled-agent games and 16 teacher games against live fifth-nflow. They are full-game comparisons on each player’s own farm, not shared-prefix policy interventions. Daily-best capture is a hindsight/depth-limited benchmark.

| Product | Teacher revenue minus ours | Volume component | Price component |
| --- | --- | --- | --- |
| WHEAT | -432 | +7 | -439 |
| CARROT | +2,056 | +2,407 | -351 |
| TOMATO | +2,425 | +2,642 | -217 |
| STRAWBERRY | +1,351 | +822 | +529 |
| MELON | -303 | -460 | +157 |
| EGG | +2,978 | +3,098 | -120 |
| MILK | +1,200 | -2,818 | +4,019 |
| WOOL | +146 | -2,013 | +2,159 |
| FERTILIZER | -108 | -2,230 | +2,122 |

The largest realized-price gaps are milk and wool: the teacher sells fewer units of both, at higher average prices. Its late farm also holds fewer cows/sheep. These are different full-game farm and market paths, so the price component is not a measured gain from sale timing alone. The restricted earlier-delivery scenario below adds only 639 coins/game before displaced work and market reactions; it supports a targeted test rather than explaining the whole revenue gap.

The revenue decomposition is exact: ΔQ×(Pa+Pb)/2 + ΔP×(Qa+Qb)/2. Prices are unit-weighted over the full season. Price effects include different endogenous market paths and mix across days, not just tactical sale timing. When one side has zero units, the other side’s price is used only as an accounting convention; no missing observed price is invented in the table.

## Units sold, actual prices and capture of daily best

| Product | Role | Units/game | Revenue/game | Actual average price | Revenue / daily-best notional |
| --- | --- | --- | --- | --- | --- |
| WHEAT | ruled | 573.69 | 16,929.75 | 29.51 | 96.45% |
| WHEAT | nflow-vs-ruled | 618.25 | 18,032.12 | 29.17 | 96.59% |
| WHEAT | teacher | 573.94 | 16,497.75 | 28.74 | 96.74% |
| WHEAT | nflow-vs-teacher | 640.38 | 18,370.25 | 28.69 | 96.60% |
| CARROT | ruled | 108.69 | 4,585.88 | 42.19 | 96.19% |
| CARROT | nflow-vs-ruled | 157.25 | 6,637.56 | 42.21 | 96.21% |
| CARROT | teacher | 167.50 | 6,641.88 | 39.65 | 94.63% |
| CARROT | nflow-vs-teacher | 145.19 | 5,727.06 | 39.45 | 94.32% |
| TOMATO | ruled | 139.44 | 8,879.50 | 63.68 | 96.35% |
| TOMATO | nflow-vs-ruled | 166.56 | 11,031.19 | 66.23 | 96.76% |
| TOMATO | teacher | 181.38 | 11,304.75 | 62.33 | 95.76% |
| TOMATO | nflow-vs-teacher | 164.75 | 10,110.00 | 61.37 | 95.44% |
| STRAWBERRY | ruled | 182.75 | 23,087.38 | 126.33 | 89.99% |
| STRAWBERRY | nflow-vs-ruled | 182.12 | 24,370.69 | 133.81 | 92.48% |
| STRAWBERRY | teacher | 189.19 | 24,438.75 | 129.18 | 91.35% |
| STRAWBERRY | nflow-vs-teacher | 175.75 | 22,551.25 | 128.31 | 91.11% |
| MELON | ruled | 73.56 | 14,557.44 | 197.89 | 91.31% |
| MELON | nflow-vs-ruled | 70.69 | 14,382.19 | 203.46 | 91.38% |
| MELON | teacher | 71.25 | 14,254.38 | 200.06 | 89.08% |
| MELON | nflow-vs-teacher | 74.50 | 14,860.75 | 199.47 | 89.11% |
| EGG | ruled | 216.56 | 9,377.25 | 43.30 | 98.93% |
| EGG | nflow-vs-ruled | 286.19 | 12,476.56 | 43.60 | 98.89% |
| EGG | teacher | 288.50 | 12,355.06 | 42.83 | 98.87% |
| EGG | nflow-vs-teacher | 284.75 | 12,156.88 | 42.69 | 98.89% |
| MILK | ruled | 242.06 | 21,909.06 | 90.51 | 84.21% |
| MILK | nflow-vs-ruled | 222.12 | 23,755.19 | 106.95 | 88.88% |
| MILK | teacher | 213.69 | 23,109.44 | 108.15 | 87.84% |
| MILK | nflow-vs-teacher | 220.25 | 22,962.75 | 104.26 | 88.30% |
| WOOL | ruled | 131.75 | 13,728.06 | 104.20 | 77.14% |
| WOOL | nflow-vs-ruled | 105.31 | 13,878.12 | 131.78 | 86.08% |
| WOOL | teacher | 113.94 | 13,874.19 | 121.77 | 84.10% |
| WOOL | nflow-vs-teacher | 107.50 | 13,442.94 | 125.05 | 84.50% |
| FERTILIZER | ruled | 293.44 | 12,565.62 | 42.82 | 95.26% |
| FERTILIZER | nflow-vs-ruled | 247.56 | 12,461.50 | 50.34 | 96.72% |
| FERTILIZER | teacher | 245.75 | 12,457.81 | 50.69 | 96.44% |
| FERTILIZER | nflow-vs-teacher | 252.44 | 12,500.38 | 49.52 | 96.21% |

Capture is total actual revenue divided by Σ(day units × that game’s maximum observed day price), including actual unit executions from both seats. It is not an unweighted mean of daily percentages. A large batch depresses the price while it sells, and first-unit quotes cannot be applied to all its units.

## Goods still discarded

Both DROP and night transfer losses are directly instrumented in native replay. For every product/day/seat, opening + harvested + bought − sold − consumed − closing must equal the measured two discard paths. Day 29 has no end-of-day refresh in the terminal game, so its night discard is absent, not an observed night of zero waste.

| Product | Ours night units/game | Teacher night units/game | Ours manual DROP | Teacher manual DROP |
| --- | --- | --- | --- | --- |
| WHEAT | 1.12 | 0.31 | 1.50 | 0.00 |
| CARROT | 0.06 | 0.31 | 0.50 | 0.00 |
| TOMATO | 1.00 | 0.00 | 0.25 | 0.00 |
| STRAWBERRY | 0.12 | 0.31 | 0.12 | 0.00 |
| MELON | 0.00 | 0.00 | 0.00 | 0.00 |
| EGG | 0.00 | 0.06 | 0.38 | 0.00 |
| MILK | 0.31 | 0.00 | 0.00 | 0.00 |
| WOOL | 0.06 | 0.00 | 0.12 | 0.00 |
| FERTILIZER | 0.00 | 0.00 | 0.06 | 0.00 |

| Day | Ours night discarded units/game | Teacher night discarded units/game |
| --- | --- | --- |
| 0 | 0.00 | 0.00 |
| 1 | 0.00 | 0.00 |
| 2 | 0.00 | 0.00 |
| 3 | 0.00 | 0.00 |
| 4 | 0.00 | 0.00 |
| 5 | 0.00 | 0.00 |
| 6 | 0.00 | 0.00 |
| 7 | 0.00 | 0.00 |
| 8 | 0.00 | 0.00 |
| 9 | 0.00 | 0.00 |
| 10 | 0.00 | 0.00 |
| 11 | 0.00 | 0.00 |
| 12 | 0.00 | 0.00 |
| 13 | 0.56 | 0.00 |
| 14 | 0.00 | 0.00 |
| 15 | 0.00 | 0.00 |
| 16 | 0.00 | 0.06 |
| 17 | 0.44 | 0.19 |
| 18 | 0.25 | 0.31 |
| 19 | 0.06 | 0.00 |
| 20 | 0.00 | 0.00 |
| 21 | 0.00 | 0.00 |
| 22 | 0.00 | 0.00 |
| 23 | 0.00 | 0.25 |
| 24 | 0.00 | 0.00 |
| 25 | 0.25 | 0.00 |
| 26 | 0.50 | 0.00 |
| 27 | 0.62 | 0.00 |
| 28 | 0.00 | 0.19 |

The full product-by-day detail is in the discarded CSV; counts include both cohorts’ opponents too.

## Hour-23 sales and next-morning prices

These are actual final post-rule sales, priced per unit by the native matcher. Raw actions cannot identify exactly which units were added by overflow, since the rule also enlarges existing SELL orders. The “risk” column identifies sales on turns where the rule’s observable overflow forecast was positive; it is not a claim that every such sale was caused by the rule.

| Product | Hour23 units/game | Actual average price | Next-morning quote (unit weighted) | Own day-best (unit weighted) | Risk-turn share of units |
| --- | --- | --- | --- | --- | --- |
| WHEAT | 24.31 | 27.53 | 27.32 | 29.60 | 93.83% |
| CARROT | 14.69 | 43.75 | 43.55 | 45.05 | 96.60% |
| TOMATO | 10.62 | 63.70 | 63.34 | 66.46 | 95.29% |
| STRAWBERRY | 56.31 | 83.34 | 72.39 | 101.77 | 99.78% |
| MELON | 0.38 | 97.50 | 89.00 | 144.00 | 100.00% |
| EGG | 35.44 | 42.08 | 42.02 | 42.56 | 93.12% |
| MILK | 31.88 | 49.20 | 43.73 | 70.24 | 98.82% |
| WOOL | 38.88 | 52.84 | 34.88 | 99.11 | 100.00% |
| FERTILIZER | 77.50 | 17.84 | 17.14 | 20.36 | 93.15% |

## Would earlier drop-off earn more?

Existing games cannot establish the causal gain of a worker rule. We provide a frozen-trajectory scenario: at hour18 find goods in bags whose workers are within four moves of a shed tile, clip to that night’s sold quantity, and split the candidate units over hours18–22. Each chunk is repriced down the native sale-price curve at that recorded turn’s inventory. This assumes free earlier delivery and shed room, preserves observed market trajectories, ignores the displaced jobs, and does not enforce arrival times within those five turns. It is an optimistic diagnostic scenario, not an executable schedule, rigorous bound or prediction. Wheat/fertilizer may be needed for consumption and need extra caution.

| Product | Candidate units/game | Scenario revenue/game | Proportional actual night revenue | Scenario difference |
| --- | --- | --- | --- | --- |
| WHEAT | 23.56 | 671.44 | 648.81 | 22.62 |
| CARROT | 7.38 | 328.88 | 324.89 | 3.99 |
| TOMATO | 5.69 | 368.88 | 360.73 | 8.15 |
| STRAWBERRY | 14.69 | 1,610.56 | 1,448.51 | 162.05 |
| MELON | 0.38 | 38.81 | 36.56 | 2.25 |
| EGG | 19.94 | 849.38 | 842.48 | 6.90 |
| MILK | 12.88 | 813.25 | 684.28 | 128.97 |
| WOOL | 11.06 | 1,004.94 | 738.30 | 266.64 |
| FERTILIZER | 43.31 | 990.69 | 953.55 | 37.14 |

A positive scenario gap supports testing earlier delivery; a negative or small gap weakens a blanket “sell earlier” rule. It does not say whether the lost worker jobs or the reacting opponent would erase the gap. Claude should test a worker-behaviour change separately; no new games were run for this task.

## Effective work and farm mix

Counts are per game in each requested band. Idle means PASS including implicit omitted-hand PASS; ineffective non-PASS is separate. Farm mix is mean tiles at the dawn of each day in the band, not cumulative purchases or all-turn exposure.

| Work metric | 6–11 ours / teacher | 12–17 ours / teacher | 18–23 ours / teacher | 24–29 ours / teacher |
| --- | --- | --- | --- | --- |
| effective_CARE | 81.56 / 84.00 | 119.19 / 112.00 | 109.88 / 97.19 | 49.19 / 57.12 |
| effective_COLLECT_FERTILIZER | 92.94 / 93.38 | 141.81 / 138.19 | 143.06 / 132.44 | 131.75 / 108.75 |
| effective_FEED | 81.50 / 83.75 | 122.75 / 114.94 | 117.31 / 103.31 | 77.56 / 68.62 |
| effective_FERTILIZE | 10.19 / 12.06 | 74.06 / 79.19 | 80.44 / 83.94 | 82.38 / 82.94 |
| effective_HARVEST | 33.94 / 34.94 | 139.44 / 150.81 | 162.31 / 182.25 | 174.62 / 202.62 |
| effective_WATER | 248.06 / 256.19 | 358.19 / 359.75 | 313.25 / 329.12 | 285.44 / 299.00 |
| idle | 107.94 / 83.38 | 35.94 / 31.44 | 26.31 / 23.62 | 33.00 / 44.19 |
| ineffective_nonpass | 0.00 / 3.75 | 0.00 / 2.50 | 0.00 / 1.38 | 0.00 / 2.62 |
| plant_CARROT | 1.00 / 1.38 | 4.44 / 5.06 | 15.88 / 24.62 | 17.19 / 19.50 |
| plant_MELON | 2.12 / 2.88 | 0.00 / 0.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| plant_STRAWBERRY | 16.25 / 16.94 | 5.25 / 5.00 | 0.00 / 0.00 | 0.00 / 0.00 |
| plant_TOMATO | 10.69 / 11.94 | 7.00 / 9.56 | 2.69 / 2.88 | 0.00 / 0.00 |
| plant_WHEAT | 47.31 / 46.69 | 50.50 / 43.94 | 54.94 / 54.31 | 37.00 / 30.12 |

| Farm type | 6–11 ours / teacher | 12–17 ours / teacher | 18–23 ours / teacher | 24–29 ours / teacher |
| --- | --- | --- | --- | --- |
| animal_COW | 8.96 / 8.65 | 10.68 / 9.36 | 10.53 / 8.41 | 10.26 / 6.81 |
| animal_GOOSE | 3.41 / 3.95 | 7.59 / 9.25 | 7.47 / 9.18 | 7.19 / 8.91 |
| animal_SHEEP | 3.23 / 3.00 | 5.76 / 4.64 | 7.27 / 5.28 | 6.02 / 3.78 |
| crop_CARROT | 0.10 / 0.10 | 1.54 / 2.15 | 5.12 / 8.00 | 10.64 / 13.05 |
| crop_MELON | 10.81 / 10.02 | 2.29 / 2.58 | 0.12 / 0.19 | 0.00 / 0.00 |
| crop_STRAWBERRY | 16.26 / 18.82 | 24.15 / 25.76 | 20.99 / 20.66 | 6.92 / 5.75 |
| crop_TOMATO | 2.45 / 3.80 | 12.21 / 13.61 | 15.82 / 18.28 | 7.11 / 10.19 |
| crop_WHEAT | 11.04 / 11.14 | 32.46 / 30.02 | 26.76 / 24.34 | 34.27 / 30.55 |

## Sources and checks

Source raw hashes and worker/protected-code hashes are pinned in `runs/after-rules-20261028/profiles-inputs.json`. All cases use 720 recorded frames and native replay; cash, stock-flow and price/volume identities are checked. These eight evaluation seeds are never training labels. No test contents10320–10324, policy/encoder changes, pushes or submissions. Worker cap4 follows Eugene’s explicit override. Night-sales attribution and frozen-market scenario limitations above remain material.

- [Sales](2026-10-28-selling-sales.csv), [summary](2026-10-28-selling-summary.csv), [volume/price identity](2026-10-28-selling-volume-price.csv).
- [Discarded by product/day](2026-10-28-selling-discarded.csv), [hour23 executions](2026-10-28-selling-hour23.csv), [earlier scenario](2026-10-28-selling-early-scenario.csv).
- [Work](2026-10-28-selling-work.csv), [farm mix](2026-10-28-selling-farms.csv), [checks](AFTER_RULES_SELLING_CHECKS.json).

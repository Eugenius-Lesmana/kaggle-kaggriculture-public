# Animal mix — 2026-10-28

**Reject `herdcap`: paired margin -3,749 coins/game (seed SE 1,556); share 0.852, 0/48 wins.** Best remains `net:board-p4:market:overflow:endmask:endwork`.

Our bank changes +7,709/game (SE 1,173); fifth-nflow’s bank changes +11,458 (SE 1,840). Difference of these bank changes equals the margin result. The retention rule was positive paired gain of at least about2SE; this version fails.

All48 games use evaluation seeds20001–20024 bothseats against live fifth-nflow, unchanged opponent and frozen P4 weights. The default ruled agent was first replayed at seed20001seat0 and its exact gameplay hash matched the specified control. Four game workers, PYTHONHASHSEED=0. No test contents or evaluation tuning.

## Fixed rule and training-only cap derivation

The opt-in market-side cap clips cows/sheep purchases above ceil(median teacher end-of-day placed+stored+carried holdings), by day. Already placed animals, inventory animals and earlier same-turn purchase orders count. Geese are unchanged; no substitution or selling existing livestock. All90 cap inputs are teacher full games on45 plan TRAIN seeds, bothseats, against Metav4. No20001–20024 cap inputs. Transferring that teacher size to our farm/opponent can fail; the observed loss does not disprove all animal-mix interventions.

An animal retained after a shrinking daily cap is not removed; only new purchases are clipped. This can leave empty structures/plans and inputs designed for the original mix. We did not retune on these evaluation results.

## Existing-game descriptive daily comparison

The following tables compare16 ruled P4 games and16 teacher games against fifth-nflow, seeds20001–20008 bothseats. They are descriptive and were never used to derive caps. Held counts are placed animals at dawn; training caps instead use total holdings at day end. Purchases are native executed units; sale prices are unit-weighted revenue/units. Full30-day values are supplied in the linked CSVs.

| Day | Agent | Cows | Sheep | Geese | Cows bought | Sheep bought | Geese bought | Milk units / price | Wool units / price | Egg units / price |

| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |

| 0 | ruled | 0.00 | 0.00 | 0.00 | 2.00 | 3.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 0 | teacher | 0.00 | 0.00 | 0.00 | 2.00 | 3.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 1 | ruled | 2.00 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 1 | teacher | 2.00 | 3.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 2 | ruled | 2.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 2 | teacher | 2.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 3 | ruled | 3.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 3 | teacher | 3.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 4 | ruled | 4.00 | 3.00 | 0.00 | 1.00 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 4 | teacher | 4.00 | 3.00 | 0.00 | 1.75 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 5 | ruled | 5.00 | 3.00 | 0.00 | 1.50 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 5 | teacher | 5.75 | 3.00 | 0.00 | 0.75 | 0.00 | 0.00 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 6 | ruled | 6.50 | 3.00 | 0.00 | 2.50 | 0.25 | 2.31 | 0.00 / NA | 18.00 / 191.00 | 0.00 / NA |

| 6 | teacher | 6.50 | 3.00 | 0.00 | 2.25 | 0.00 | 1.94 | 0.00 / NA | 18.00 / 191.00 | 0.00 / NA |

| 7 | ruled | 8.69 | 3.25 | 2.31 | 0.12 | 0.00 | 0.06 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 7 | teacher | 8.50 | 3.00 | 1.94 | 0.12 | 0.00 | 0.38 | 0.00 / NA | 0.00 / NA | 0.00 / NA |

| 8 | ruled | 8.81 | 3.25 | 2.31 | 0.25 | 0.00 | 0.62 | 9.62 / 200.71 | 0.00 / NA | 0.00 / NA |

| 8 | teacher | 8.88 | 3.00 | 2.31 | 0.12 | 0.00 | 1.69 | 12.00 / 202.21 | 0.00 / NA | 0.00 / NA |

| 9 | ruled | 9.00 | 3.25 | 2.94 | 1.06 | 0.00 | 2.12 | 1.19 / 210.05 | 10.50 / 121.97 | 0.00 / NA |

| 9 | teacher | 9.00 | 3.00 | 3.88 | 0.50 | 0.00 | 2.69 | 0.00 / NA | 12.00 / 117.01 | 0.00 / NA |

| 10 | ruled | 10.06 | 3.25 | 5.06 | 0.62 | 0.12 | 2.81 | 5.75 / 205.76 | 0.00 / NA | 0.00 / NA |

| 10 | teacher | 9.50 | 3.00 | 6.31 | 0.00 | 0.00 | 2.56 | 6.12 / 198.09 | 0.00 / NA | 0.00 / NA |

| 11 | ruled | 10.69 | 3.38 | 7.81 | 0.00 | 0.00 | 0.00 | 5.81 / 199.98 | 0.19 / 82.33 | 3.31 / 52.36 |

| 11 | teacher | 9.50 | 3.00 | 9.25 | 0.00 | 0.00 | 0.00 | 6.75 / 194.88 | 0.00 / NA | 3.19 / 52.45 |

| 12 | ruled | 10.62 | 3.38 | 7.69 | 0.06 | 2.25 | 0.00 | 10.44 / 183.98 | 3.75 / 51.13 | 6.69 / 52.33 |

| 12 | teacher | 9.50 | 3.00 | 9.25 | 0.00 | 1.81 | 0.00 | 17.25 / 176.50 | 2.50 / 54.75 | 4.81 / 52.53 |

| 13 | ruled | 10.69 | 5.44 | 7.69 | 0.00 | 0.31 | 0.00 | 10.94 / 164.15 | 2.19 / 91.60 | 6.19 / 49.32 |

| 13 | teacher | 9.50 | 4.81 | 9.25 | 0.00 | 0.00 | 0.00 | 10.19 / 162.50 | 0.06 / 161.00 | 8.19 / 51.24 |

| 14 | ruled | 10.69 | 5.88 | 7.56 | 0.00 | 0.50 | 0.00 | 24.50 / 142.72 | 3.81 / 119.85 | 7.56 / 50.04 |

| 14 | teacher | 9.50 | 4.81 | 9.25 | 0.00 | 0.00 | 0.00 | 21.25 / 133.29 | 2.94 / 154.04 | 13.31 / 49.13 |

| 15 | ruled | 10.69 | 6.38 | 7.56 | 0.00 | 0.38 | 0.00 | 8.12 / 92.70 | 2.56 / 139.98 | 11.88 / 47.45 |

| 15 | teacher | 9.50 | 4.81 | 9.25 | 0.00 | 0.38 | 0.00 | 6.44 / 100.48 | 3.62 / 122.53 | 15.81 / 47.91 |

| 16 | ruled | 10.69 | 6.69 | 7.56 | 0.00 | 0.12 | 0.00 | 8.69 / 94.07 | 1.06 / 128.59 | 15.25 / 46.24 |

| 16 | teacher | 9.19 | 5.19 | 9.25 | 0.00 | 0.00 | 0.00 | 9.38 / 105.97 | 2.06 / 159.55 | 18.88 / 45.28 |

| 17 | ruled | 10.69 | 6.81 | 7.50 | 0.00 | 0.00 | 0.00 | 11.94 / 67.21 | 4.19 / 148.46 | 11.88 / 44.09 |

| 17 | teacher | 9.00 | 5.19 | 9.25 | 0.00 | 0.00 | 0.00 | 7.25 / 83.84 | 3.62 / 164.67 | 16.31 / 43.86 |

| 18 | ruled | 10.62 | 6.81 | 7.50 | 0.00 | 0.44 | 0.00 | 7.62 / 74.07 | 3.56 / 141.04 | 13.81 / 43.69 |

| 18 | teacher | 8.81 | 5.19 | 9.25 | 0.12 | 0.25 | 0.00 | 9.69 / 81.95 | 9.88 / 128.15 | 17.12 / 42.57 |

| 19 | ruled | 10.62 | 7.31 | 7.50 | 0.00 | 0.19 | 0.00 | 5.44 / 75.59 | 3.81 / 111.46 | 11.31 / 42.48 |

| 19 | teacher | 8.81 | 5.44 | 9.25 | 0.00 | 0.00 | 0.00 | 8.06 / 70.40 | 4.00 / 95.06 | 14.44 / 42.19 |

| 20 | ruled | 10.50 | 7.44 | 7.50 | 0.00 | 0.00 | 0.00 | 10.81 / 70.24 | 6.19 / 93.19 | 13.75 / 42.30 |

| 20 | teacher | 8.38 | 5.38 | 9.19 | 0.00 | 0.00 | 0.00 | 11.00 / 65.75 | 3.56 / 108.68 | 16.25 / 41.91 |

| 21 | ruled | 10.50 | 7.44 | 7.50 | 0.00 | 0.00 | 0.00 | 9.62 / 66.09 | 9.19 / 84.20 | 11.50 / 41.85 |

| 21 | teacher | 8.31 | 5.38 | 9.19 | 0.00 | 0.00 | 0.00 | 8.56 / 68.71 | 6.06 / 86.84 | 14.56 / 41.40 |

| 22 | ruled | 10.50 | 7.38 | 7.44 | 0.00 | 0.00 | 0.00 | 9.56 / 66.78 | 3.31 / 73.40 | 12.69 / 41.27 |

| 22 | teacher | 8.25 | 5.31 | 9.12 | 0.00 | 0.00 | 0.00 | 9.38 / 70.73 | 4.38 / 76.27 | 17.88 / 41.29 |

| 23 | ruled | 10.44 | 7.25 | 7.38 | 0.00 | 0.00 | 0.00 | 11.94 / 63.31 | 5.81 / 81.61 | 11.06 / 41.32 |

| 23 | teacher | 7.88 | 5.00 | 9.06 | 0.00 | 0.00 | 0.00 | 8.56 / 75.29 | 4.50 / 93.83 | 15.69 / 40.89 |

| 24 | ruled | 10.44 | 7.19 | 7.38 | 0.00 | 0.00 | 0.00 | 9.19 / 44.47 | 6.88 / 70.66 | 11.12 / 41.16 |

| 24 | teacher | 7.44 | 5.00 | 9.06 | 0.00 | 0.00 | 0.00 | 10.56 / 75.63 | 6.06 / 78.79 | 16.00 / 40.82 |

| 25 | ruled | 10.38 | 6.88 | 7.38 | 0.00 | 0.00 | 0.00 | 10.38 / 71.25 | 2.56 / 96.85 | 12.19 / 41.14 |

| 25 | teacher | 7.12 | 4.75 | 9.00 | 0.00 | 0.00 | 0.00 | 8.88 / 68.86 | 3.81 / 80.57 | 15.56 / 40.85 |

| 26 | ruled | 10.25 | 6.50 | 7.25 | 0.00 | 0.00 | 0.00 | 11.44 / 41.16 | 5.38 / 108.62 | 12.44 / 40.99 |

| 26 | teacher | 6.75 | 4.31 | 8.94 | 0.00 | 0.00 | 0.00 | 10.88 / 84.82 | 5.62 / 109.76 | 13.00 / 40.51 |

| 27 | ruled | 10.19 | 6.44 | 7.19 | 0.00 | 0.00 | 0.00 | 11.69 / 65.65 | 15.88 / 90.04 | 11.88 / 40.78 |

| 27 | teacher | 6.62 | 4.31 | 8.94 | 0.00 | 0.00 | 0.00 | 9.94 / 71.74 | 8.56 / 108.64 | 18.94 / 40.46 |

| 28 | ruled | 10.19 | 6.06 | 7.12 | 0.00 | 0.00 | 0.00 | 15.88 / 53.21 | 8.06 / 85.15 | 12.81 / 40.45 |

| 28 | teacher | 6.56 | 4.31 | 8.88 | 0.00 | 0.00 | 0.00 | 11.25 / 65.67 | 5.50 / 103.19 | 20.62 / 40.32 |

| 29 | ruled | 10.12 | 3.06 | 6.81 | 0.00 | 0.00 | 0.00 | 31.50 / 25.43 | 14.88 / 40.28 | 19.25 / 40.45 |

| 29 | teacher | 6.38 | 0.00 | 8.62 | 0.00 | 0.00 | 0.00 | 10.31 / 59.02 | 7.19 / 117.86 | 27.94 / 40.06 |

[Daily game-level inputs](2026-10-28-animal-mix-daily.csv), [daily summary](2026-10-28-animal-mix-summary.csv), [training caps and90 source hashes](ANIMAL_MIX_TRAIN_CAPS.json), [paired checks](ANIMAL_MIX_CHECKS.json).

The opt-in implementation remains available for reproducibility; it is not part of the best agent. This test does not identify the benefit of replacing livestock with crops or geese, which was not attempted.

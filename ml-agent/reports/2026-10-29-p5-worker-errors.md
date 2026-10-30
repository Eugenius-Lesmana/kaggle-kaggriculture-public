# P5 worker errors — near-target direction choices dominate the largest cells

**The ten largest counted disagreements are direction substitutions near the teacher's target, not missed WATER/FEED commands.** Command accuracy is 91.81% on the NN's live days 6–28. Across the complete analysis tensor it is 91.99% over 454,593 masked worker decisions; the network is not used live on the additional days 0–5 and 29.

This is teacher-forced imitation accuracy, not a bank-loss estimate. Many legal alternative actions can be harmless or even better than the label. The largest cells below are plausibly costly because median target distance is only one or two tiles, but their monetary effect has not been measured with games.

## Command and target-head accuracy

Days 6–28 only. PICKUP/PLACE aggregate item variants here; PLANT keeps each crop separate. The linked CSVs retain every original command and all counts.

| Teacher command/group | Decisions | Correct command | Correct-command tile-target cases | Tile-target accuracy | Wrong tile target |
| --- | ---: | ---: | ---: | ---: | ---: |
| PASS | 15,801 | 91.89% | 1,044 | 39.94% | 627 |
| NORTH | 38,795 | 86.71% | 33,180 | 92.72% | 2,415 |
| SOUTH | 39,801 | 87.07% | 33,968 | 93.35% | 2,258 |
| EAST | 41,431 | 85.37% | 34,800 | 86.17% | 4,812 |
| WEST | 37,043 | 85.31% | 31,061 | 87.85% | 3,773 |
| WATER | 103,828 | 98.43% | 102,200 | 99.73% | 277 |
| HARVEST | 33,011 | 91.52% | 30,211 | 98.40% | 483 |
| FEED | 18,606 | 97.29% | 18,101 | 99.49% | 93 |
| CARE | 20,423 | 97.66% | 19,946 | 99.56% | 88 |
| PLANT_WHEAT | 16,090 | 89.39% | 14,383 | 99.08% | 133 |
| PLANT_CARROT | 5,931 | 89.07% | 5,283 | 99.43% | 30 |
| PLANT_TOMATO | 1,738 | 67.49% | 1,173 | 99.32% | 8 |
| PLANT_STRAWBERRY | 3,829 | 87.15% | 3,337 | 99.55% | 15 |
| PLANT_MELON | 124 | 79.84% | 99 | 92.93% | 7 |
| PICKUP | 3,083 | 81.06% | 2,499 | 96.44% | 89 |
| DROP | 3,165 | 95.39% | 3,019 | 99.54% | 14 |
| PLACE | 3,770 | 97.29% | 3,668 | 99.59% | 15 |
| BUILD_COOP | 966 | 95.45% | 922 | 99.35% | 6 |
| BUILD_PASTURE | 1,486 | 97.85% | 1,454 | 98.35% | 24 |
| FERTILIZE | 21,766 | 93.39% | 20,328 | 99.33% | 137 |
| COLLECT_FERTILIZER | 21,729 | 94.97% | 20,635 | 99.23% | 159 |
| DIG | 4,081 | 90.96% | 3,712 | 98.25% | 65 |

A tile target is scored only when the command is correct, the command/unit masks permit evaluation, and the teacher target is an actual tile (0–99). The no-future-job sentinel 100 is excluded from this conditional tile accuracy. Across all analysis days, that accuracy is 95.99% (382,638/398,605); 1,266 of those actual-tile cases instead predict sentinel100.

The target head is a training/planning helper. A correct command with a wrong helper target need not change this worker's immediate action. Predicted targets do enter later workers' decision context in free play, so their effect cannot be priced from this table alone.

## Day and hour breakdown

| Teacher command/group | Days 6–11 | Days 12–17 | Days 18–23 | Days 24–28 |
| --- | ---: | ---: | ---: | ---: |
| PASS | 93.11% | 89.55% | 92.04% | 90.92% |
| NORTH | 88.60% | 86.68% | 85.63% | 85.64% |
| SOUTH | 88.57% | 88.00% | 86.33% | 85.32% |
| EAST | 87.84% | 85.67% | 83.94% | 83.89% |
| WEST | 84.84% | 86.34% | 84.64% | 85.19% |
| WATER | 99.09% | 98.29% | 98.19% | 98.32% |
| HARVEST | 90.47% | 91.22% | 90.93% | 92.82% |
| FEED | 97.18% | 98.68% | 97.78% | 94.66% |
| CARE | 98.68% | 98.70% | 97.04% | 95.76% |
| PLANT_WHEAT | 88.31% | 93.05% | 90.84% | 82.56% |
| PLANT_CARROT | 43.55% | 74.16% | 88.93% | 91.64% |
| PLANT_TOMATO | 76.60% | 60.46% | 40.11% | NA |
| PLANT_STRAWBERRY | 91.80% | 74.33% | 33.70% | NA |
| PLANT_MELON | 79.84% | NA | NA | NA |
| PICKUP | 82.88% | 78.84% | 76.77% | 78.20% |
| DROP | 92.02% | 95.60% | 98.35% | 96.71% |
| PLACE | 96.80% | 99.64% | 98.08% | 100.00% |
| BUILD_COOP | 95.54% | 91.67% | NA | NA |
| BUILD_PASTURE | 96.61% | 99.56% | 100.00% | 100.00% |
| FERTILIZE | 89.85% | 94.43% | 92.19% | 94.16% |
| COLLECT_FERTILIZER | 96.55% | 95.88% | 94.37% | 93.20% |
| DIG | 85.91% | 85.64% | 91.76% | 92.44% |

| Teacher command/group | Hours 0–11 | Hours 12–19 | Hours 20–23 |
| --- | ---: | ---: | ---: |
| PASS | 68.37% | 85.74% | 93.57% |
| NORTH | 87.55% | 86.21% | 86.70% |
| SOUTH | 87.27% | 87.39% | 86.24% |
| EAST | 84.74% | 86.09% | 84.21% |
| WEST | 85.79% | 85.63% | 84.12% |
| WATER | 98.52% | 98.59% | 98.16% |
| HARVEST | 90.21% | 91.90% | 91.84% |
| FEED | 97.90% | 97.00% | 95.15% |
| CARE | 97.66% | 98.22% | 95.61% |
| PLANT_WHEAT | 89.32% | 89.27% | 89.63% |
| PLANT_CARROT | 89.27% | 90.81% | 84.58% |
| PLANT_TOMATO | 56.92% | 66.73% | 70.16% |
| PLANT_STRAWBERRY | 87.64% | 88.13% | 82.25% |
| PLANT_MELON | 100.00% | 82.41% | 60.00% |
| PICKUP | 82.30% | 81.14% | 64.71% |
| DROP | 96.66% | 93.52% | 96.18% |
| PLACE | 98.31% | 96.82% | 95.65% |
| BUILD_COOP | 93.18% | 97.13% | 89.19% |
| BUILD_PASTURE | 97.44% | 98.86% | 94.26% |
| FERTILIZE | 94.44% | 94.34% | 91.57% |
| COLLECT_FERTILIZER | 94.95% | 95.32% | 93.21% |
| DIG | 89.83% | 91.90% | 90.06% |

| Day / hour band | Decisions | Command accuracy |
| --- | ---: | ---: |
| 6-11 / 0-11 | 23,580 | 92.68% |
| 6-11 / 12-19 | 49,227 | 91.93% |
| 6-11 / 20-23 | 27,764 | 92.26% |
| 12-17 / 0-11 | 27,608 | 92.51% |
| 12-17 / 12-19 | 57,822 | 92.35% |
| 12-17 / 20-23 | 32,553 | 91.90% |
| 18-23 / 0-11 | 28,311 | 91.52% |
| 18-23 / 12-19 | 59,097 | 91.40% |
| 18-23 / 20-23 | 33,388 | 91.17% |
| 24-28 / 0-11 | 22,771 | 91.48% |
| 24-28 / 12-19 | 47,511 | 91.44% |
| 24-28 / 20-23 | 26,865 | 91.32% |

The [command-statistics CSV](p5-worker-command-stats.csv) supplies exact denominators and conditional target counts for every teacher command at overall, day-only, hour-only and day×hour scopes. The [confusion CSV](p5-worker-confusions.csv) supplies what is predicted for every teacher command at the same scopes. The `outside` day bucket contains 0–5 and29 for completeness; it is excluded from the live-window tables above. Do not add rows from overlapping scopes.

## Ten biggest error cells

Ranked by error count over the complete analysis tensor; the second count isolates the days when P5 actually uses its worker network. Context statistics refer to the complete-analysis cells.

| Teacher → predicted | All-analysis errors | Of these, days 6–28 | Median teacher target distance | Equally short route cases | Assessment |
| --- | ---: | ---: | ---: | ---: | --- |
| EAST → NORTH | 1,650 | 1,631 | 1 | 409 | Plausibly costly routing; some alternatives may be harmless |
| SOUTH → EAST | 1,547 | 1,519 | 1 | 65 | Plausibly costly routing; some alternatives may be harmless |
| NORTH → EAST | 1,507 | 1,487 | 1 | 68 | Plausibly costly routing; some alternatives may be harmless |
| SOUTH → WEST | 1,477 | 1,441 | 1 | 63 | Plausibly costly routing; some alternatives may be harmless |
| EAST → SOUTH | 1,469 | 1,443 | 1 | 297 | Plausibly costly routing; some alternatives may be harmless |
| WEST → SOUTH | 1,469 | 1,435 | 1 | 303 | Plausibly costly routing; some alternatives may be harmless |
| NORTH → WEST | 1,395 | 1,366 | 1 | 66 | Plausibly costly routing; some alternatives may be harmless |
| WEST → NORTH | 1,339 | 1,306 | 1 | 339 | Plausibly costly routing; some alternatives may be harmless |
| EAST → WEST | 1,261 | 1,244 | 2 | 0 | Plausibly costly routing; some alternatives may be harmless |
| WEST → EAST | 1,236 | 1,217 | 2 | 0 | Plausibly costly routing; some alternatives may be harmless |

“Equally short” means both distinct moves reduce Manhattan distance to the teacher's labelled target by one. Those cases are plausible harmless route variations; it is not proof that their full plans have equal value. The remaining cases are not certified harmless by this test. The target is a teacher-derived helper reference, not a measured future-money outcome.

Missed held harvest, imminent water/feed loss and wrong crop plantings are the more direct potential-money errors. None is in the ten largest individual cells by count. Frequency alone therefore does not rank lost coins; rare harvest or feed errors can matter more than common movement differences. PASS versus a far-away move with time to spare is marked as low immediate risk by the diagnostic, but none of those cells enters this top ten.

## Scope and checks

The single GPU evaluation covered all 2,590 analysis segments / 37,735 turns. It took 56.73s wall and 24.42s process CPU, using one CPU thread and CUDA bfloat16 autocast as in `train_board_net.evaluate`. Earlier workers' true commands and helper targets are teacher-forced; prediction argmax uses stored legal masks, and command scoring uses `unit_mask & command_loss_mask`. Padding and illegal/masked teacher labels are excluded.

Repeated forks share analysis parent families; these are descriptive counts, not independent game trials. No test 10320–10324 contents, evaluation 20001–20048 arrays, policy games or worker-model updates. [Checks and top-cell context](P5_WORKER_ERROR_CHECKS.json), [diagnostic source](../tools/p5_worker_errors.py). Input worker hashes, model hash and manifest hash are recorded. Band totals, confusion totals and target-subset counts reconcile.

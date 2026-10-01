# Route backbones and cell-local action replay

Date: 2026-09-29. Analysis only; no engine games were run.

## Input and method

- 39 player-games from the committed 24 September top-four folders; 536 from the four 29 September submission folders (56640149 Team E, 56654377 Team B, 56664798 Team A, 56666211 Team F). The newer player's seat comes from each folder's `episodes.json`, never from the folder name alone.
- `evaluation/backbones/routes.csv.gz` records every visited cell and full command for each hand on each day. Hand 0 is the farmer; hands 1+ are hire order. For similarity, the backbone is the ordered **worked-cell** sequence (including repeats); the gap measure uses the full observed walk (21–24 turns, depending on hire time).
- Each team/hand/day is grouped either without shops or by the set of open demand groups: wool (`YARN_STORE`), carrot (`PET_CAFE`, `FARMERS_MARKET`), tomato/milk (`PIZZA_SHOP`), strawberry/milk (`ICE_CREAM_SHOP`, `SMOOTHIE_SHOP`), egg (`BAKERY`, `BRUNCH_SPOT`). Groups can co-occur. Groups with one route are omitted from stability estimates.
- The backbone is an observed route selected to maximize mean order similarity to group members. On groups with over 24 distinct routes, the search considers the 12 most common and up to 12 reproducibly sampled candidates, so these are **approximate medoids**. The 24 September medoids are exact. `medoids.csv` includes both worked cells and the source game's full walk.
- Measures match `MICROTAPE_STUDY_2026-09-28.md`: fuzzy edit similarity of worked cells (neighbor substitution costs 0.5), edit similarity of consecutive 2×2 blocks, and dynamic-time-warp mean Manhattan gap between full walks. Higher order/blocks and lower gap are better. Stability is the member-weighted mean similarity to its group medoid, including the medoid member itself.

## Backbone stability

| Cohort | Days | Routes | Ungrouped order / blocks / gap | Shop-group order / blocks / gap | Shop-group coverage |
|---|---:|---:|---:|---:|---:|
| 24 Sept | 6–11 | 2,501 | .686 / .740 / .714 | .812 / .845 / .440 | 1,182 (47%) |
| 24 Sept | 12–19 | 3,930 | .454 / .545 / 1.737 | .632 / .696 / 1.084 | 1,492 (38%) |
| 29 Sept | 6–11 | 34,171 | .507 / .583 / 1.271 | .608 / .668 / .982 | 33,734 (99%) |
| 29 Sept | 12–19 | 52,588 | .418 / .535 / 1.743 | .511 / .605 / 1.418 | 50,792 (97%) |

The same-member ungrouped baselines for shop-grouped routes are .692 / .748 / .683 and .457 / .549 / 1.710 on 24 September, then .508 / .584 / 1.266 and .419 / .536 / 1.735 on 29 September. Thus the 29 September split raises order by .100 early and .092 late; the gap falls by .284 and .317 cells. Part of that lift is mechanical: more, smaller groups produce better in-sample medoids. These numbers do not isolate a predictive effect of shop labels.

There is strong team variation. Team E's 29 September routes remain comparatively tight (.616 order / .764 gap early; .542 / .943 late). Team B is .392 / 1.762 early and .335 / 2.198 late; Team A .485 / 1.433 and .350 / 2.237; Team F .506 / 1.270 and .398 / 1.940. All four have a recognizable medoid, but a single daily route is a much weaker description of the latter three, especially after day 11.

### 24 versus 29 September

Only Team B and Team A are in both cohorts. To reduce the 10-versus-100+ game imbalance, `era_check.py` draws five reproducible 10-game samples from each newer team and recomputes medoids:

| Team | Days | 24 Sept order / blocks / gap | 29 Sept, 10-game mean |
|---|---:|---:|---:|
| Team B | 6–11 | .643 / .705 / .883 | .439 / .501 / 1.660 |
| Team B | 12–19 | .479 / .571 / 1.585 | .387 / .483 / 2.146 |
| Team A | 6–11 | .731 / .776 / .602 | .501 / .568 / 1.454 |
| Team A | 12–19 | .483 / .574 / 1.521 | .387 / .474 / 2.206 |

Both teams show less repeatable paths in the newer replays even at equal sample size. This is descriptive: the competition seeds, opponents, and likely submission versions differ. Their service mix changed less. Team B's watering was 18.5% versus 19.0% of turns; Team A's was 18.7% versus 16.5%, while its animal care and fertilizer collection rose modestly.

## State-driven action reproduction

The tested cell-local priority is: on crops, water if dry, fertilize if carried and not active, harvest if product is held; on occupied animal tiles, collect available fertilizer, feed if carrying wheat, harvest held product, then care; on empty cells, plant the first available seed; otherwise move/pass. It sees the prior observation's tile and that hand's inventory. It does not look ahead, optimize price, or use a route-specific action tape. Accuracy compares the **full command**, including a crop argument for `PLANT`. Movement and `PASS` are counted as a single `GO` choice; the rule does not choose a direction.

| Replay set | All hand turns | Nonmovement commands | Core farming commands |
|---|---:|---:|---:|
| 24 Sept | 52.9% of 147,036 | 60.4% of 82,492 | 68.1% of 73,152 |
| 29 Sept | 52.3% of 1,988,106 | 61.3% of 1,092,963 | 68.7% of 974,831 |

| Actual core command | 24 Sept exact match | 29 Sept exact match |
|---|---:|---:|
| `WATER` | 100% | 100% |
| `COLLECT_FERTILIZER` | 100% | 100% |
| `PLANT` (crop included) | 65.2% | 69.9% |
| `HARVEST` | 47.5% | 47.9% |
| `FEED` | 25.5% | 42.9% |
| `CARE` | 23.6% | 26.4% |
| `FERTILIZE` | 11.6% | 4.2% |

The perfect `WATER` and almost-perfect `COLLECT_FERTILIZER` scores show that their immediate tile conditions are visible; they do not make the combined rule reliable. Across both cohorts it predicts water for 54,598 actual fertilizations; fertilizer collection for 77,785 feeds and 74,618 care actions; and water for 30,289 harvests. It also selects the wrong crop on 24,723 plantings. Movement past a serviceable cell is another large disagreement. `PICKUP`, `DROP`, `PLACE`, construction, and `DIG` need shed, inventory, economic, or lifecycle decisions absent from this local rule.

## Verdict

Observed medoid backbones can be extracted, particularly for early days and Team E. Shop grouping improves descriptive fit, but a route chosen only by the open-shop set is not yet validated for an unseen game. A bare local action priority does not reproduce the top agents well enough to treat route order plus cell state as a faithful executor: multiple jobs on the same cell require sequencing and economic context. A prototype should test held-out route selection and explicit multi-visit service priorities before treating this as a copyable tape.

Reproduce with `python evaluation/backbones/analyze.py`, then `python evaluation/backbones/summarize.py` and `python evaluation/backbones/era_check.py`. Detailed compact tables are in `evaluation/backbones/`.

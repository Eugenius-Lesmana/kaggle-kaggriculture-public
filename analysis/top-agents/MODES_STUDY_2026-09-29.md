# Top-four farm modes at shop openings

**Verdict: partially.** Shop demand predicts several product allocations, and agents usually replant freed plots promptly. The farms do **not** settle into a small set of discrete layouts determined by shop groups. The 24 September and 29 September cohorts cluster mainly by season phase; by day 12 every game in each cohort falls in one broad cluster despite different shop draws. A mode-switching agent should use overlapping product-demand signals to allocate individual freed plots. The opener, land and hire skeleton needs a version-specific template: it changed materially by 29 September.

## Data and method

`evaluation/modes/study.py` reads two cohorts separately:

| Cohort | Top-agent player-games | Opening snapshots | Seat selection |
|---|---:|---:|---|
| Committed 24 Sept | 46 in 39 episodes (Team B 15, Team A 11, Team C 10, Team D 10) | 368 | Top-four agent name; both seats count when eligible |
| Local 29 Sept | 536 (Team E 181, Team B 140, Team A 108, Team F 107) | 4,288 | `episodes.json` submission ID matching the folder; four completed episodes lacked a replay file |

The 29 September source replays are **not committed**. Each output sits under `evaluation/modes/24-sept/` or `29-sept/`. `opening_tiles.jsonl.gz` records every owned tile's coordinates, content, crop and planted day, plus exact shop counts, animal counts, owned plots, structures, hands and bank at the start of days 3, 6, 9, 12, 15, 18, 21 and 24. `daily_features.jsonl.gz` supports conversion timing. Action records are aligned to the *preceding* observation; a replay's action and observation at the same index describe a completed transition.

The installed engine's `SHOPS` table confirms all named shops, but the proposed groups need **overlap corrections**: `FARMERS_MARKET` buys wheat, carrot, tomato **and strawberry**; `BRUNCH_SPOT` buys egg, wheat **and strawberry**. `PIZZA_SHOP` buys milk, tomato and wheat; `ICE_CREAM_SHOP` buys strawberry, milk and wheat. Thus `FARMERS_MARKET` also contributes tomato/strawberry demand, and `BRUNCH_SPOT` contributes strawberry demand. `PET_CAFE` buys only carrot, `YARN_STORE` only wool, `SMOOTHIE_SHOP` strawberry/milk, and `BAKERY` egg/wheat. The table is at `kaggle_environments/envs/kaggriculture/kaggriculture.py:103-111` in the installed package. Each shop instance is counted, including duplicates.

The layout vector is the share of owned plots occupied by each of five crops and three animal types. K-means tests 2–8 clusters with 30 starts and selects by silhouette, separately per cohort. The descriptive shop effects compare farms of the same team and day with and without each shop. The predictive check uses 10 folds grouped by player-game, fitting plot share from team and opening day, then from those plus eight shop counts. These are associations, not causal effects: shop draws overlap, prices vary and game histories differ.

## Modes and shop consistency

On 24 September, three clusters win by silhouette (0.489; two clusters score 0.480):

| Cluster | Opening snapshots | Typical layout | Days |
|---|---:|---|---|
| 2 | 64 | melon 36%, wheat 20%, strawberry 17%, sheep 14% | all day 3; 18 at day 9 |
| 0 | 74 | strawberry 41%, melon 34%, sheep 10% | all day 6; 28 at day 9 |
| 1 | 230 | wheat 27%, strawberry 27%, tomato 10%, carrot 6% | **all games on days 12–24** |

The two largest clusters cover **304/368 (82.6%) opening snapshots**. On 29 September, two clusters win (silhouette 0.400) and both are needed to cover 80% of openings: the larger holds 3,136/4,288 (73.1%). **Across games at a fixed opening**, one mode covers at least 80% on every day except old-cohort day 9 (two needed); the newer day-9 majority is 456/536 (85%). This is not evidence for shop modes: one cluster alone covers all games at day 24 in either cohort. The exact shop-count signature and day repeat in 101 old and 633 new strata; within-stratum cluster agreement is 99.6% and 97.5%, but day nearly determines the label. Shop-presence signature versus cluster has low adjusted mutual information (0.171 old, 0.136 new). At day 9, Yarn Store is present in 14/18 old games in the melon/sheep branch versus 3/28 in the other; on 29 September it is 75/80 versus 107/456. The clusters capture this early allocation fork, then merge as land and crop maturity change.

Shops still explain **within-cluster allocations**. Held-out prediction of plot share improves as follows:

| Feature | 24 Sept R²: base → shops | 29 Sept R²: base → shops | Same-day/team association, old → new |
|---|---:|---:|---|
| Carrot | 0.183 → **0.649** | 0.380 → **0.637** | Pet Café +7.2 → +5.4 percentage points |
| Tomato | 0.620 → **0.803** | 0.381 → **0.490** | Pizza +3.7 → +2.9 |
| Strawberry | 0.456 → **0.753** | 0.574 → **0.779** | Ice Cream +3.3 → +4.8 |
| Sheep | 0.218 → **0.610** | 0.145 → **0.627** | Yarn +5.7 → +6.3 |
| Cow | 0.080 → **0.490** | 0.527 → **0.764** | Ice Cream +3.2 → +2.7 |
| Goose | 0.480 → 0.572 | 0.335 → 0.530 | Bakery +1.2 → +2.0 |
| Wheat | 0.745 → 0.794 | 0.693 → 0.770 | common backbone |
| Melon | 0.982 → 0.992 | 0.976 → 0.976 | calendar phase |

The signs for wool/sheep, Pet Café/carrot, Pizza/tomato and dairy/cow persist in the newer cohort. Egg shops show a weaker goose response. The study does not isolate price responses from shop responses.

## Conversion timing and how plots free up

For each newly opened shop instance, a target's first **net count increase** at the next daily snapshots occurs one day later in the responding cases. Examples over the first three days: Yarn/sheep 18/44 events, Pet Café/carrot 25/39, Pizza tomato or cow 54/102 product-events, Ice Cream strawberry or cow 70/147. Non-response can mean the target was already allocated, a duplicate shop opened, or the agent chose another product. The product-event denominator counts each product a shop buys, so shared products are deliberately repeated.

Action-level first target planting after an opening is faster: Pet Café carrot in 25/39 openings, median 15 replay steps; Pizza tomato in 23/34, median 14 steps; Ice Cream strawberry in 29/49, median 10 steps. Within those 72-step windows, the first plant followed a **harvest** in 19/25, 8/23 and 18/29 respectively. The rest used a vacant plot, except 2 Pet Café and 6 Pizza cases following `DIG`.

Across all 13,527 observed plantings, 8,158 (60%) followed `HARVEST`, 3,595 (27%) used a new or idle plot, and 1,774 (13%) followed `DIG`. Of 1,277 digs of crop tiles, **1,217 occurred at or after the crop's final scheduled production day**: chiefly strawberry at age 16 (834) and tomato at age 11 (383). Only 60 crop digs were earlier. Thus conversion is usually at harvest, on unused land, or after an ongoing crop finishes production. Clearing a still-producing crop is rare, not absent. A preceding action is associated by tile; 1,692 of the 1,774 `DIG`-followed plantings replant within 24 steps.

The newer cohort confirms the mechanism at much larger scale. Of **147,908** plantings, 93,619 (63%) follow harvest, 37,445 (25%) use a new/idle plot and 16,844 (11%) follow dig. Of 12,715 crop digs, 11,688 (92%) are at or after final scheduled production; 1,027 (8%) are earlier, mostly strawberry at ages 12–15. First target planting after an opening: Pet Café carrot 322/540 events, median 16 steps; Pizza tomato 131/523, median 16; Ice Cream strawberry 374/564, median 10. First plant follows harvest in 244/322, 86/131 and 227/374 respectively. Net target-count growth in responding cases still first appears at the next daily snapshot (median one day). The Pizza tomato planting fraction falls from 68% to 25%, partly because Team E runs virtually no tomatoes; the shop association remains positive within day/team.

## Fixed skeleton

The exact *full action dict* at a given replay step is identical to the across-game majority 67.5% of the time on day 0, then 44.5%, 40.4%, 17.3%, 17.7%, 20.8% on days 1–5. This strict measure includes every hand and market order; small inventory or routing differences break a match. It qualifies the earlier “fully deterministic opener” description: the route and resource schedule are recognisable, but exact full actions are not universal.

Land timing is much tighter. All 46 unlock NE at replay transition step **150**. SW is unlocked at 220 in 29 games, 222 in 15, 218 in one and 225 in one. SE is unlocked in 40 games: 254 in 14, 255 in 25 and 253 in one; six do not unlock it. Hands (excluding the farmer) reach 4 in every game on day 0, 6 in every game on days 2–3 and 5, 8–9 on days 6–7, 9 in 44/46 on day 8, and 10–13 on day 10. The precise daily hire schedule varies after day 3; `summary.json` retains its full distribution.

### What changed by 29 September

The newer four share an economic theme but **not one identical skeleton**. Full-action majority agreement on days 0–5 is 31.9%, 24.4%, 37.3%, 21.0%, 16.5%, 11.1% across 536 games. Team B hires four hands on day 0 in all 140 games; Team E, Team A and Team F hire five in all 396 of theirs. On day 6, 535/536 have nine hands. At day 8, 374 have ten and 155 have nine.

The land clock moved earlier and became team-specific. Team B's common path is NE **149**, SW **199**, SE **250** (67/140); Team A and Team F usually unlock NE **148**, SW **199**, often stopping at 75 plots. Team E usually unlocks NE **146**, SW around **199–202**, also often stopping at 75 plots. By day 12 the newer cohort averages **82.4 owned plots** versus **96.7** in the old one; by day 24 it is 82.9 versus 96.7. Team B still owns all 100 plots in the newer games, while Team A averages 81.3 and Team E/Team F about 75. The common 24 September land script therefore does not transfer intact.

There is also a pronounced early livestock change: cow plot share on day 6 rises from **8.0% to 20.6%**. This is visible within retained teams: Team B 8.0% → 19.4%, Team A 8.0% → 21.7%. At day 18, the newer cohort uses fewer tomato plots (6.5% versus 12.4%) and more wheat (25.1% versus 21.0%); the tomato difference mixes lineage choices, since Team E runs virtually none while Team B's tomato share rises. At day 24, carrot share is 15.3% versus 10.8%. `comparison.json` records each team and opening day, so the aggregate changes can be separated from the change in top-four membership.

## Limits and next use

The 29 September folders had completed `episodes.json` manifests, but four completed episodes had no replay file and were excluded. The cohorts use different team mixes and likely different versions for Team B/Team A, so time and identity effects cannot be separated cleanly. This measurement tests layout feasibility, not a runnable policy or 30 September submission. The useful interface for a later agent is a **version-specific opener and land/hire schedule** plus per-product demand counts and current farm state, with reassignment when a tile is harvested or a mature ongoing crop is dug. Whole-farm cluster labels add little after day 12.

Reproduce each cohort with `python evaluation/modes/study.py 24` and `python evaluation/modes/study.py 29`, then `python evaluation/modes/conversion.py 24`, `python evaluation/modes/conversion.py 29` and `python evaluation/modes/compare.py`. The 29 September script reads the local intake path supplied for this study; set `KAGG_MODES_29_ROOT` to override it on another machine. No local screens were run.

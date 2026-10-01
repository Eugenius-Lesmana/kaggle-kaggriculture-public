# Where the top three's extra units come from

Date: 2026-09-30

Branch: `dev/eugene-codex-production-gap`
Scope: existing replays and planner diagnostics only; no games or seeds run.

## Verdict

**Both capacity and yield matter; resale does not explain the observed production lead.** Across days 0–27, the three non-trading top submissions produce **2,112 units/game** in the replay audit, against **1,357 units/game** in Claude's v0.10 planner diagnostic. The planner diagnostic omits hour-23 actions at day rollover. Removing the same **52 top-agent units/game** gives a like-for-like **+703 harvested units/game**: **+382 (54%) from occupied cell/animal-days** and **+320 (46%) from harvest per occupied day**. The adjusted top output is 2,059 units/game, **52% above** the planner's diagnostic count. These are production units across crops, animal products, and collected fertilizer, not gross market sales.

The lead appears after day 6 and is concentrated in days **12–27** (+656 of the +703 units). The top farms buy land earlier, use more cells, keep more animals, and leave fewer owned tiles empty. Their late wheat, strawberry, carrot, and melon harvests also yield more per occupied day. Their animals have *slightly lower* per-animal-day product yield than the planner; the extra eggs, milk, and fertilizer come from more animals.

The three top agents actually fill **133 wheat product buys/game** through day 27 and no fertilizer buys. Claude's planner data record **154 requested wheat buys/game**, not successful fills. Thus the top-minus-planner purchase contribution is bounded from **−21 to +133 units/game**; its exact value is unavailable. The separate trading submission fills **3,511 product buys/game**, mainly wheat and fertilizer, and must not be pooled into a farm-production estimate.

## Data and accounting

- Top replays: 355 player-games from submission IDs `56654377` (140), `56664798` (108), and `56666211` (107). The analyzed seat matches the folder ID in `episodes.json`. Submission `56640149` (181 games) is reported separately.
- Planner comparison: 40 v0.10 games on `dev/eugene-claude-routeopt` at `f673cce`, from `evaluation/routeopt/production_v010.json`. They used different opponents and seeds from the public replays, so comparisons are descriptive.
- Phases: days 0–5, 6–11, 12–19, and 20–27. Each replay is decompressed alone. Capacity is the same hour-23 daily snapshot used by Claude's diagnostic. The tables also provide **hourly occupied cell-days** for the top agents, which are less sensitive to intra-day harvest and replanting. The planner has only daily capacity snapshots.
- Harvest and fertilizer collection are measured from the engine's field-action effects. The market is replayed with the engine's order rules on copied state; successful `BUY_PRODUCT` and `SELL` units count only after the replayed bank matches the recorded bank. **All relevant market steps for the top three verified**; one step failed for the trading submission and contributes no market fills or sales.
- The top-three stock equation balances: opening stock + harvest + buys − feed/fertilizer use − sales − closing stock leaves **3.7 units/game** through day 27, all nonnegative by game/product/phase. This residual reflects shed overflow or other discards. It is small beside the 703-unit production gap.

## Capacity by phase

Values are average owned cells or occupied cells **per day**. Each pair is **top three / planner**. "Watered" uses Claude's yield-window definition; "fertilized" is the share of plant-days with active fertilizer. Detailed crop and animal counts, including weeds and empty structures, are in [group_product_phase.csv](../../evidence/production_gap/group_product_phase.csv).

| Phase | Owned plots | Planted cells | Animal cells | Empty cells | Yield-window watered | Fertilized plant-days |
|---|---:|---:|---:|---:|---:|---:|
| Days 0–5 | 25 / 25 | 17.9 / 17.3 | 6.7 / 4.7 | 0.4 / 3.0 | 100% / 90% | 0% / 0% |
| Days 6–11 | 70 / 62.5 | 50.2 / 47.0 | 17.3 / 10.1 | 2.5 / 5.0 | 95.5% / 94.3% | 4.5% / 1.3% |
| Days 12–19 | 86.8 / 75 | 64.7 / 54.9 | 21.2 / 14.0 | 0.9 / 6.0 | 93.5% / 89.6% | 32.9% / 13.1% |
| Days 20–27 | 86.8 / 75 | 62.2 / 51.8 | 19.8 / 14.0 | 3.6 / 8.7 | 92.6% / 92.7% | 40.6% / 14.9% |

The extra animal capacity is especially clear in the goose line: **7.3 versus 1.5 geese/day** in each late phase. Cows are **7.8 versus 5.2** on days 12–19; sheep are **6.0 versus 7.3**, so wool is not the source of the animal lead. Tomato capacity averages **8.4 and 8.3 cells/day** in the two late phases; the planner has none. By days 20–27 the top agents also use **28.7 wheat cells/day versus 22.8**.

Top crop watering in the actual bonus/production window is high for most crops, though tomatoes are around 81–86%. The planner-comparable aggregate watering shares are close after day 6. Fertilizer differs much more: top plants are fertilized on 33–41% of late plant-days versus 13–15% for the planner. The top wheat yield on the matched daily denominator is **1.51 vs 1.07** units/cell-day on days 12–19 and **1.34 vs 0.89** on days 20–27. Strawberry is **0.44 vs 0.33** and **0.98 vs 0.68**. Top wheat is harvested on average **1.9 days after first ripeness** in both late phases; the planner file has no comparable harvest-delay measure. These observations support a crop-yield difference, but they do not isolate fertilizer from harvest age or other market conditions.

## Capacity × yield decomposition

For each product and phase, `H = C × Y`: harvested units/game, occupied cell- or animal-days/game, and harvested units per occupied day. The exact symmetric split is `ΔH = ΔC × (Ytop + Yplanner)/2 + ΔY × (Ctop + Cplanner)/2`. When the planner has no capacity for a product, all new output is assigned to capacity. Top hour-23 harvests are removed only for this comparison, matching the planner diagnostic. Values below are **units/game across days 0–27**; the full phase/product table is [matched_decomposition.csv](../../evidence/production_gap/matched_decomposition.csv).

| Product | Extra harvested | Capacity effect | Yield effect | Top confirmed product buys | Planner buy requests |
|---|---:|---:|---:|---:|---:|
| Wheat | +173 | +7 | +166 | 133 | 154 |
| Carrot | +44 | +6 | +38 | 0 | 0 |
| Tomato | +72 | +72 | 0 | 0 | 0 |
| Strawberry | +46 | −8 | +55 | 0 | 0 |
| Melon | +18 | −57 | +75 | 0 | 0 |
| Egg | +168 | +181 | −12 | 0 | 0 |
| Milk | +44 | +58 | −14 | 0 | 0 |
| Wool | −9 | −25 | +17 | 0 | 0 |
| Fertilizer | +146 | +149 | −3 | 0 | 0 |
| **Total** | **+703** | **+382** | **+320** | **133** | **154** |

The phase split shows when the edge develops:

| Phase | Harvest gap | Capacity effect | Yield effect |
|---|---:|---:|---:|
| Days 0–5 | −14 | −20 | +7 |
| Days 6–11 | +60 | +71 | −11 |
| Days 12–19 | +296 | +164 | +132 |
| Days 20–27 | +360 | +168 | +192 |

Eggs (+168) and collected fertilizer (+146) are predominantly **animal count**. Tomato (+72) is an **absent planner crop**. Wheat (+173), strawberries (+46), carrots (+44), and melons (+18) are predominantly **yield per occupied day**; the melon yield effect offsets fewer late melon cells. Product effects can be negative and should be retained when interpreting the totals.

## Purchases, sales, and stock

Through day 27, the top three harvest **2,112 units/game**, successfully buy **133 wheat units**, sell **1,551 units**, and discard or overflow **3.7 units**. They consume 384 wheat units in feeding and 216 fertilizer units in application; stock growth and phase timing account for much of the remaining difference between production and sales. Wheat purchases are feed supply as well as potential resale, so gross wheat sales cannot be called home-grown production.

The planner's diagnostic supplies **harvest**, **feed**, **fertilizer use**, and **buy requests**, but no confirmed buy fills, per-phase sales, or phase-boundary stock. Therefore the table above is an exact **harvested-unit** decomposition, while the resale term is a bound. It is not an exact decomposition of the full-season sold-unit gap from MARKET_EDGE_2026-09-30.md on `dev/eugene-codex-market-edge`. If every planner wheat request filled, top buys are 21 fewer; if none filled, top buys are 133 more. Neither extreme can account for the 703-unit harvested lead.

The separate trader `56640149` harvests **2,045 units/game** but fills **3,511 product buys** and sells **4,871 units** by day 27. Of its buys, **2,890 are wheat** and **621 fertilizer**. Its bought-product turnover explains its exceptional gross sales. Its late owned area averages 75 cells rather than the other top agents' 87, so it is a distinct strategy, not evidence that the three-agent farm produces 4,871 units.

## Reproduction and limits

[analyze.py](../../evidence/production_gap/analyze.py) writes the per-game, per-phase [game_product_phase.csv](../../evidence/README.md#files-not-included) and group table. [rollover.py](../../evidence/production_gap/rollover.py) measures omitted hour-23 harvests. [summarize.py](../../evidence/production_gap/summarize.py) writes [capacity_summary.csv](../../evidence/production_gap/capacity_summary.csv) and the matched decomposition. All read compressed replays in place; no replay file is copied or committed.

Capacity × yield is an accounting identity, not an experiment. The day-end capacity denominator can be distorted when a crop is harvested and replanted within a day; hourly exposure for top agents is provided alongside it. The planner lacks hourly exposure, harvest delay, confirmed purchases, per-phase sales, and stock snapshots. Different opponent markets and seeds also prevent treating the measured differences as a causal transplant result. The strongest supported next hypothesis is **more early animal and tomato capacity, followed by higher late crop yield from the existing plan and care schedule**.

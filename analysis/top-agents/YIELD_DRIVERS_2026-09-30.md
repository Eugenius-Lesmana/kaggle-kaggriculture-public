# Why top crop cells yield more

Date: 2026-09-30

Branch: `dev/eugene-codex-yield-drivers`
Scope: existing 29 September replays only. No games or seeds were run.

## Verdict

**Fertilizer applied in the yield window is the strongest measured driver of the top three's wheat and strawberry yield.** On days 12–27, 78% of their wheat bonus-window plant-days and 94% of their strawberry production-window plant-days are both watered and fertilized. Water alone is already frequent (97% and 98% of those windows). Most fertilizer is timed to the crop's first useful day: wheat age 2, strawberry ages 9 and 13. Strawberry's three-day fertilizer dose covers both scheduled production days at ages 9/11 or 13/15.

Keeping **the top agents' planting, watering, harvest, dig, and survival path fixed**, then removing fertilizer's yield bonus reduces late wheat from 1.44 to **0.97 units per day-end crop cell-day** and strawberry from 0.642 to **0.329**. Claude's v0.10 planner diagnostic reports **0.98 wheat** and **0.439 strawberry** on the same day-end denominator. The top fertilizer bonus is **192 wheat and 104 strawberry units/game**; on the same capacity denominator, those gains are 103% and 155% of the *observed rate gaps*. This shows the bonus is large enough to cover the gaps in magnitude; it does **not** measure the top-minus-planner fertilizer effect, because the planner also fertilizes and its file lacks crop-level timing or per-plant lifecycles.

Within the top replays, a simple crop-specific regression on complete late-ending plants adds 0.616 R² for wheat and 0.417 for strawberry beyond plant lifetime, window opportunities, planting day, and submission. A Shapley split of that *within-top added fit* assigns wheat 0.526 to watered-and-fertilized window days, 0.072 to watered window days, and 0.018 to harvest delay. Strawberry assigns 0.303, 0.086, and 0.027. These are explanatory associations among top plants, **not percentages of the planner gap**. Replanting is usually immediate (median one hour after the previous plant ends); it raises occupied capacity rather than units per occupied cell-day.

## Population and measurement

The 355 top-three player-games are submission `56654377` (140), `56664798` (108), and `56666211` (107); the analyzed seat matches the folder's submission ID in `episodes.json`. Trading submission `56640149` is excluded. One gzip replay is decompressed at a time. [plant_lifecycles.csv](../../evidence/README.md#files-not-included) has **86,905 planted-cell records with any exposure on days 12–27**. It follows each plant from planting through harvest, dig, weed, or replay end and records active hours, watered/fertilized days, yield-window overlap, harvested units, first-ripeness delay, remaining stock, and the next planting gap. Ongoing crops can have several harvests; replay-end records are censored.

Field actions are applied to a copy of the observed farm with the installed Kaggriculture engine. The measured late harvest total for **every crop** and the **72,306 successful late fertilizer applications** reconcile exactly with the prior production audit on `dev/eugene-codex-production-gap` at `49e9a14`. The comparator is Claude's 40-game v0.10 phase diagnostic on `dev/eugene-claude-routeopt`; both aggregate rates use its day-end capacity definition. [production_reference.csv](../../evidence/yield_drivers/production_reference.csv) preserves the 20 phase/crop rows used here, so the summary script needs no other branch. Hourly exposure rates for the top replays are also provided because day-end snapshots can miss harvest/replant turnover.

## Crop lifecycles and late yield

The first five columns below average over plants that produced at least one unit on days 12–27; final units are **total observed harvest per plant**, including harvests outside those days. Delay is days from first positive harvestable stock to the harvest action, averaged per harvest. Replant gap is the median among plants that ended on days 12–27 and were replanted before replay end. Full plant records preserve the individual values and censor flags.

| Crop | Late-harvested plants | Watered / yield-window days | Fertilized days | Harvested units / plant | Harvest delay | Replant gap |
|---|---:|---:|---:|---:|---:|---:|
| Wheat | 42,083 | 2.32 / 2.37 | 1.93 | 4.94 | 1.91 d | 1 h |
| Carrot | 12,285 | 1.70 / 1.72 | 1.05 | 3.26 | 1.40 d | 1 h |
| Tomato | 4,569 | 3.56 / 3.94 | 4.28 | 7.23 | 0.79 d | 1 h |
| Strawberry | 10,808 | 3.79 / 3.87 | 5.66 | 7.45 | 0.76 d | 1 h |
| Melon | 1,559 | 4.73 / 5.01 | 0.41 | 5.99 | 0.32 d | 7 h |

These yield-window days follow the game rules: for one-time crops, ages from `ceil(max_yield_day/2)` through `max_yield_day`; for ongoing crops, the watering day before scheduled production. A wheat plant starts with one harvestable unit, gains one from watering in its window, and gains a second on a watered day with active fertilizer, capped at six. Strawberry gets one per scheduled production, doubled to two with both water and fertilizer, with held stock capped at four. The top strawberry mean of 7.45 harvested units per plant is close to the four-event, eight-unit maximum.

| Crop, days 12–27 | Top actual / cell-day | Top with fertilizer bonus removed | Planner actual / cell-day | Top late water + fertilizer overlap | Top fertilizer gain / game |
|---|---:|---:|---:|---:|---:|
| Wheat | 1.441 | 0.968 | 0.981 | 77.9% | 192.1 |
| Strawberry | 0.642 | 0.329 | 0.439 | 94.2% | 103.7 |

The same result holds across top submissions: wheat window overlap rises from 71.9% (`56654377`) to 81.1% (`56664798`) and 86.2% (`56666211`), while their hourly wheat rates rise from 1.35 to 1.53 and 1.57. Strawberry overlap is 90.9%, 95.0%, and 97.9%, with hourly rates 0.615, 0.625, and 0.643. These cross-submission associations reinforce the mechanism without isolating it from route and planting differences. [crop_summary.csv](../../evidence/yield_drivers/crop_summary.csv) and [submission_crop_summary.csv](../../evidence/yield_drivers/submission_crop_summary.csv) include the other crops, both denominators, and the full precision values.

Using every occupied hour instead of day-end snapshots gives pooled top rates of **1.455 wheat** and **0.626 strawberry** units/cell-day, close to the 1.441 and 0.642 values above. The yield finding is therefore not mainly a snapshot-denominator artifact.

## Fit: which plant factors track yield?

For each crop, the response is harvested units divided by occupied days for complete plants that ended on days 12–27 and harvested at least once. Ordinary least squares includes controls for occupied lifetime, number of production-window opportunities per occupied day, planting day, and submission. Added factors are watered-window days per occupied day, watered **and** fertilized-window days per occupied day, and delay after first ripeness. Shapley averaging over all factor orders allocates the added R², so shared signal is split rather than assigned entirely to the first variable.

| Crop | Plants | Control R² | Full R² | Added R²: water | Added R²: water + fertilizer | Added R²: delay |
|---|---:|---:|---:|---:|---:|---:|
| Wheat | 42,083 | 0.316 | 0.932 | 0.072 | **0.526** | 0.018 |
| Strawberry | 8,462 | 0.474 | 0.891 | 0.086 | **0.303** | 0.027 |

The fitted fertilizer-overlap coefficient is +0.85 wheat and +1.07 strawberry units per occupied day for one additional overlap day per occupied day. The wheat water coefficient is +0.72; delay is −0.03 per day after controlling for lifetime and care. The variables are correlated, and plants in the same replay are not independent. [factor_regression.csv](../../evidence/yield_drivers/factor_regression.csv) includes every crop's fit. The fixed-action bonus estimate above uses the game rule directly and is the stronger evidence for fertilizer's magnitude.

## When and where fertilizer is applied

There are **72,306 successful applications on days 12–27**, or 203.7/game. The median application is day 21, hour 15. Hours 12–17 contain many applications; hour 23 is the single busiest hour (4,582, 6.3%). For an ongoing crop that was watered, hour-23 fertilizer is still active when scheduled production fires at daily refresh. Days 15, 19, and 24 are large application days. The full day × hour × crop counts are in [fertilizer_day_hour.csv](../../evidence/yield_drivers/fertilizer_day_hour.csv); each action's position, worker, crop age, and source is in [fertilizer_actions.csv](../../evidence/README.md#files-not-included).

| Crop | Late applications | Most common crop ages | Purpose |
|---|---:|---|---|
| Wheat | 36,521 | age 2: 27,283 (75%); age 3: 4,589 | age 2 dose spans wheat's age 2–4 bonus window |
| Strawberry | 19,891 | ages 9 and 13: 17,992 (90%) | each dose spans two scheduled production days |
| Carrot | 8,661 | age 2: 5,669 | covers carrot's age 2–3 bonus window |
| Tomato | 7,025 | ages 7 and 10: 4,716 | covers scheduled production on following days |
| Melon | 208 | age 6: 162 | uncommon late melon treatment |

Successful applications are classified from each worker's fertilizer inventory flow. **Direct** means fertilizer collected from an animal and carried to a plant without a shed handoff; **shed** means fertilizer picked up from storage. If direct and shed units are mixed in the same inventory, the consumed unit cannot be identified. Unknown includes mixed-source carryover after such a use or an untracked starting inventory.

| Source, days 12–27 | Applications | Share |
|---|---:|---:|
| Direct from collection | 58,687 | 81.2% |
| Picked up from shed | 10,607 | 14.7% |
| Mixed or unknown | 3,012 | 4.2% |

For wheat, 88.8% of applications are certainly direct; for strawberry, 64.8% are direct and 24.6% are shed. The top three made no fertilizer product purchases in the previous market audit, so shed fertilizer is previously collected stock. [fertilizer_age_source.csv](../../evidence/yield_drivers/fertilizer_age_source.csv) and [fertilizer_source.csv](../../evidence/yield_drivers/fertilizer_source.csv) give the complete breakdown.

## Interpretation and limits

The no-fertilizer calculation applies the same observed watering and harvest schedule with only fertilizer's yield increment removed. It preserves crop survival and future actions, so it is a **fixed-action yield attribution**, not a forecast of a redesigned agent. In particular, low-yield plants could decay sooner and a real agent could replant or sell differently. Fertilizer's measured contribution to top output can exceed the observed top-planner gap because the planner also receives some fertilizer gain; its crop-specific timing and gain are unavailable. The regression describes variation **within top plants** and does not identify a causal percentage of the cross-agent gap.

The immediate experiment for Claude is a matched-game planner change that moves collected fertilizer directly to wheat at age 2 and strawberry at ages 9/13, while recording crop-level active fertilizer on scheduled days, harvest timing, and bank effects. The planner diagnostic should emit per-plant or at least per-crop yield-window care to quantify the cross-agent decomposition. Existing replays alone support **fertilizer placement and timing as the leading explanation**, with high baseline watering and rapid replanting helping keep that bonus productive.

Reproduce: `python evaluation/yield_drivers/analyze.py --intake "<repo>/research/intake/replays/29 Sept top"`, then `python evaluation/yield_drivers/summarize.py`. Both scripts read the compressed replays in place; no replay is copied or committed.

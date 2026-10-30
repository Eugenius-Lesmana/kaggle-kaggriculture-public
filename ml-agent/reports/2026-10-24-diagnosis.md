# Diagnosis: why ranker v2 does not play like the 4th-place agent (2026-10-24)

Seven possible causes were raised by Eugene on 2026-10-24. Each was given a measurement and a decision rule
**before** any result was seen. This report applies those rules. No fix has been made yet.

## How the diagnostics were run (leakage guards)

- The 24 bench games are split: training 10301-10314, **analysis 10315-10319**, test 10320-10324. Every
  diagnostic used the analysis games only; the test games were not opened.
- The model under diagnosis is **v2-diag** (`ranker-own-v1-diag`): the same model as v2, retrained on the 14
  training games only, so the analysis mornings are new to it.
- **D0, determinism:** job lists are now sorted, so ties no longer depend on Python's hash seed; the same mornings
  give identical results under two different seeds (12/12), and Codex's runs repeat exactly (21/21).
- All comparisons are paired by morning (same start, same recorded opponent moves); means with standard errors
  (se). "Clearly" = a difference at least about twice its standard error.
- Value = cash + goods held and waiting on the farm at current prices + purchases still held at cost, as in all
  earlier benches. Replays of recorded actions reproduce the recorded values exactly.

## Summary

| # | Eugene's suspected cause | Verdict | Size |
|---|---|---|---|
| 1 | 75% accuracy, errors compound (drift) | **Real but secondary** | Agreement drops 2-5 points in our model's own states; the value gap does not grow during the day |
| 2 | Task manager: tunnel vision, shed rules | **Shed: confirmed, small. Tunnel vision: not supported** | About 8 extra shed turns a day; walking per job already equals the teacher's |
| 3 | Re-deciding is flawed, not the idea of jobs on the way | **Agreed** | Re-deciding every turn: -659 a day (120 mornings) |
| 4 | The teacher looks further ahead than one day | **Not supported as hidden future value; but its lead grows when it plays several days in a row** | Teacher day 1 then template: no extra gain on days 2-3 (+96, se 124); teacher all three days: lead grows from +619 to about +1,000 and +1,350 a day |
| 5 | Our plan and purchases cost us | **Confirmed, moderate** | Template's first 3 hours (purchases, positions): -191 a day (se 49), about a quarter of the teacher's lead |
| 6 | Our training ignores how the teacher decides | **Partly: the features can see the difference, but the model weights them wrongly** | 0% of wrong choices are indistinguishable; worst at fertilize (60%), plant (63%), build (32-55%) |
| 7 | We copy what to do, not how (routes, coordination) | **Not supported for v2** | v2-diag does as many jobs with as little walking as the teacher; coordination measures nearly equal |

**The main finding is a priorities problem with crops.** v2-diag spends its time on animals and lets crops
that matter go dry: it misses more than twice as many crops that would have produced that night (2.9 vs 1.3 a
day) and lets more crops die (3.8 vs 2.6 a day), while serving animals better than the teacher (fewer unfed,
fewer runaways). About three quarters of the teacher's daily lead appears overnight, and it is real produce
(-702 a night at unchanged prices), not price movements (-52).

## Details by diagnostic

### D1: drift (cause 1)

- Agreement with the teacher (sampled job lists, analysis games): in the teacher's own day 81-83% by hour band; in
  days our model played first (L3) 77-80%; by takeover hour 81.2% (hour 4), 80.3% (8), 78.9% (12), 76.9% (16).
  Thousands of decisions per cell, so these drops are clear.
- Value gained since dawn, v2-diag minus teacher: hour 4 -266 (se 28), 8 -245, 12 -166, 16 -142, 20 -183, next
  dawn -757 (se 91). The gap does **not** grow during the day; most of it appears overnight.
- Tiles that differ from the teacher's farm grow from 7 (hour 4) to 35 (night); template 8 to 40.
- **Rule** (gap grows steadily and agreement falls): agreement falls, the gap does not grow. Drift is real but
  secondary; correction rounds (L3) remain useful but are not the main cure.

### Overnight split and what is left undone (follow-up to D1)

| Overnight change, v2-diag minus teacher | Mean (se) |
|---|---:|
| Produce at the 11pm prices | -702 (90) |
| Price movement at midnight | -52 (18) |
| Real change in total | -529 (90) |

| At hour 23, per day | Template | v2-diag | Teacher |
|---|---:|---:|---:|
| Animals unfed | 5.6 | 2.8 | 5.0 |
| ...on a production night (produce lost) | 1.1 | 0.3 | 1.2 |
| ...for a second day (animal escapes) | 0.3 | 0.1 | 0.4 |
| Crops unwatered | 25.0 | 27.8 | 23.8 |
| ...safely (watered yesterday, nothing due tonight) | 21.0 | 21.6 | 20.1 |
| ...on a production night | 2.6 | **2.9** | **1.3** |
| ...on a fertilized production night (double yield lost) | 0.5 | **0.8** | 0.3 |
| ...for a second day (crop dies) | 1.5 | **3.8** | 2.6 |

Engine rules behind these (read from the game code): a crop dies after two unwatered days in a row; an animal
escapes after two unfed days; strawberries and tomatoes produce only on set days, and fertilizer doubles a yield
only if the plant is watered that day; animals produce only on their production days.

Correction to an earlier statement: the teacher does **not** skip animals cleverly; it neglects animals more than
v2-diag, including costly cases. Its advantage is on the crop side.

### D2 and D3: execution, shed, coordination (causes 2 and 7)

| Per day | Template | v2-diag | Teacher |
|---|---:|---:|---:|
| Jobs done | 153 | 178 | 177 |
| Walking moves | 124 | 108 | 105 |
| Walking per job | 0.85 | 0.63 | 0.61 |
| Shed pickups / drops | 7.5 / 1.4 | 13.8 / 5.5 | 8.8 / 2.7 |
| Wheat per pickup | 3.1 | 3.9 | 3.0 |
| Tiles each worker covers | 9.9 | 8.7 | 8.7 |
| Area overlap between workers | 0.063 | 0.063 | 0.050 |
| Workers within one tile of each other, per turn | 1.76 | 1.62 | 1.54 |

- **Rules:** shed amounts and timing differ clearly (pickups +5.0, se 0.3; drops +3.2, se 0.4): learn shed
  decisions. Overlap differs by 0.013 (se 0.002), clear but tiny; proximity +0.08 (se 0.07), not clear:
  coordination is not a main cause.
- The "jobs on the way" measure did not separate the players (about 98% for all) and needs redesigning; with
  walking per job already equal, there is little left for it to explain.

### D4: looking ahead (cause 4), by Codex

105 mornings (analysis games, days 6-26). A = template three days; B = teacher day 1, then template; C = teacher
three days.

| B - A | Mean (se) |
|---|---:|
| Day 1 | +619 (59) |
| Day 2 | +13 (79) |
| Day 3 | +83 (87) |
| Days 2+3 | +96 (124) |
| Cumulative after day 3 | +679 (139) |

Arm C's value gain per day: 5,812 / 6,217 / 6,282 against A's 5,194 / 5,206 / 4,932, so the teacher's lead
grows to about +1,000 and +1,350 a day when it keeps playing.

- **Rule** (B clearly above A on days 2-3): **not met.** The teacher's day leaves no hidden value that pays on
  later days; the one-day value does not mislead in that sense, and its day-1 lead is kept, not lost.
- New finding: the lead **compounds when the teacher controls several days in a row** (its own states, its own
  plan). Single-day benches understate how far apart the agents end up; benches for new versions should include
  a multi-day run.

### D5: error analysis (cause 6)

20,261 decisions on the analysis games, scored against every legal job: top-1 74.1%.

- Wrong choices whose features are identical to the teacher's choice: **0%**. Our features can tell the jobs apart.
- 34% of wrong choices are the right kind of job on another tile; 66% a different kind.
- Agreement by the teacher's job: care 97%, water 81%, harvest 70%, collect fertilizer 68%, feed 66%, pickup
  66%, plant 63%, fertilize 60%, build coop 32%, build pasture 55%.
- Most common swaps: the teacher fertilizes and the model waters (190), the teacher harvests and the model waters
  (176).
- When the kind differs, the teacher's job is worth slightly less right now (165 vs 175), at the same distance.
- **Rule** (wrong choices look the same in our features): not met. The model has the information but weighs it
  differently; the training, not the features, is the first suspect. Explicit features for "this crop dies
  tonight if not watered" and "this crop produces tonight (double if fertilized)" may still help, since the
  current ones (`t_dry`, `t_next_prod`, `t_fert_days`) encode them only indirectly.

### D6: our start of the day (cause 5), by Codex

115 mornings (analysis games, days 6-28). 1 = template; 2 = teacher; 3 = template hours 0-3, then teacher;
4 = teacher workers with template market orders all day.

| Comparison | Mean (se) |
|---|---:|
| 2 - 1 (teacher's lead) | +744 (82) |
| 3 - 2 (cost of our first 3 hours) | **-191 (49)** |
| 4 - 2 (cost of our market orders all day) | -161 (30) |

In its first three hours the template buys 6.6 wheat and 1.3 carrot seeds per morning; the teacher buys none.

- **Rule** (arm 3 clearly below arm 2): **met.** Our start of day costs about a quarter of the teacher's lead;
  bringing parts of the plan stage forward (dawn seed buying) is justified, but it is not the main cause.

## What this implies for fixes (proposals, not yet approved)

Ranked by measured size:

1. **Crop priorities in the ranker.** Train v3 on L1 + L3 (already decided) and check specifically whether it
   closes the crop gap: production nights missed, crops dying, fertilizer applied. If not enough: (a) add explicit
   "dies tonight" / "produces tonight" / "double tonight" features; (b) weight training decisions by what a
   mistake costs (fertilize and plant choices count more), since the model sees the difference but undervalues it.
2. **Our start of day and market orders** (-191 and -161 a day): test the template without its dawn wheat and
   carrot seed buying; this is a plan-stage rule and cheap to bench.
3. **Shed decisions** (about 8 turns a day): learn pickup amounts from the teacher instead of the fixed rule.
4. **Benches:** add a three-day run for every new version, since the teacher's lead compounds over days.
5. **Drift:** handled by the correction rounds already planned (stop rule A+).

Not recommended now: routing, jobs-on-the-way logic, coordination changes, or the per-turn whole-team redesign;
the measurements do not point to them for v2.

## Evidence

- D1-D3 recordings: `<data>/runs/diag/d1/`; summaries `runs/diag/d1-summary/`
  (`d1_hourly.csv.gz`, `d2_d3_per_morning.csv`, `night_parts.csv`, `night_skips.csv.gz`).
- D1 agreement: `tools/diag_d1_agreement.py`. D5: `runs/diag/d5/decisions.csv.gz`, `tools/diag_d5.py`.
- D4/D6 (Codex): `reports/DIAG_D4.csv`, `reports/DIAG_D6.csv`, `reports/DIAG_D4_D6_CHECKS.json`, runs under
  `<data>/runs/diag/d4-d6/`.
- Tools: `tools/diag_runs.py`, `tools/diag_analyse.py`, `tools/diag_night.py`.

# Route-follower executor prototype: can copied route order close the execution gap?

Date: 2026-09-29
Status: **measured; verdict negative.** Research only; this does not change the submission.
- Branch: `dev/eugene-claude-executor`, from `dev/eugene-claude-v010`.
- Candidate: `agents/ours/executor-candidate/`.
- Evidence: `evaluation/executor/`.
- It builds on:
  - `docs/MICROTAPE_STUDY_2026-09-28.md`: routes repeat across games;
  - `docs/V010_TOP4_TRANSPLANT_2026-09-25.md`: their plan on our executor scored −0.105;
  - `docs/TOP3_MACRO_PLAN_2026-09-24.md`.

## Question

The mode-switching tape agent would run a fixed skeleton through a "copied route order +
state-driven action" executor. Each hand walks the top agent's backbone route and, at each
cell, does whatever that cell needs. This prototype tests whether that executor closes the
execution gap in days 0–11, where Team A's routes are most stable.

## What was built

1. **Backbone extraction** (`evaluation/executor/extract_backbone.py`, output in
   `team_a_backbone.json`).
   - Inputs: all 11 Team A player-games in `research/intake/replays/24 Sept/`, de-duplicated by
     episode.
   - Each hand's day is cut into *visits*: runs of non-move commands on one cell.
   - For each hand slot and day 0–11, the route is the **medoid** across games of the
     visit-cell sequence. Similarity is the micro-tape study's tolerant edit similarity.
   - Mean pairwise similarity on days 6–11 is 0.2–1.0, typically 0.55–0.85. Day 7 is the
     loosest.
   - Also written: the literal day 0–11 tape of episode 112920694 (`team_a_tape_112920694.json`).
2. **Three arms**, each built from the untouched skel control (`skel.py`, sha256 `3453980c…`,
   a copy of `.cache/variants/skel/main.py`). `build.py` generates `main.py` and `tape.py`.
   - **(a) skel:** the TOP4 opener script (days 0–5, behind a position guard), land at steps
     150/220/254, TOP4 hands, the TOP4 layout target, and our planner's scheduler as the
     executor.
   - **(b) route** (`main.py`): same skeleton and same planner market. Every worker move
     comes from the route-follower while day ≤ 11 and the opener script is off.
     - **Order:** walk the medoid route for this worker's slot and day.
     - **Action at each cell** (state-driven, Team A's own rules measured from the replays):
       - plants: fertilize if carrying fertilizer and it adds ≥ 2 units (≥ 1 on ongoing
         crops); water if unwatered; harvest when ripe (wheat and carrot at first yield,
         one day later if the fertilizer is still live; melon at 6 units);
       - empty cell: plant the layout crop, or build the structure when carrying the animal;
       - weed: dig;
       - animal: feed if carrying wheat, then care if fed, collect fertilizer, harvest;
       - shed-access cell: pick up wheat for the rest of the route's unfed animals, deposit
         goods, pick up animals the route will place.
     - **Fallbacks:**
       - skip a visit with nothing to do, judged from afar;
       - skip a visit in a locked quadrant;
       - wait one step if another hand is working the cell;
       - when the route is exhausted, serve the nearest cell that needs something.
     - **Seeds:** bought just in time for the next two visits.
     - **From day 12:** the planner runs exactly as in skel.
   - **(c) tape** (`tape.py`): Team A episode 112920694's day 0–11 actions played verbatim,
     market included. There is no state logic and no guard. From day 12 the planner runs as
     in skel.
3. **Measurement** (`evaluation/executor/measure.py`, `summarize.py`).
   - Commands are counted as successful only when confirmed by the next observed state.
   - "Productive" counts successful water, harvest, plant, feed, care, collect, fertilize,
     dig, build and place.
   - "Unneeded water" is a successful WATER on a plant that was watered yesterday, outside
     its yield window, and without live fertilizer.
   - Other outputs: idle and move shares, the farm at the start of day 12, the final bank
     ratio, the route-follower's visit diagnostics, and the service left undone at hour 23.
   - Team A's own figures come from the same code run on its 11 replays.

**Protocol.**
- Seeds 7101–7200 only, 4 workers.
- Opponents: the Metav4 substrate (`agents/ours/h1-substrate-metav4/main.py`, seeds
  7101–7200) and V46 (seeds 7101–7160).
- Each seed is played in one seat: odd seeds as P1, even seeds as P2. So both seats are
  covered, paired across arms on identical seed and seat.
- Seat-swapped games are near-duplicates. On seeds 7101 and 7102 both seats gave identical
  banks for skel and route, so running both seats would halve the information for the same
  compute.
- n = 100 paired games per arm vs Metav4 and 60 per arm vs V46. Intervals are ± 95%.

## Results

### Bank ratio (primary)

| paired vs skel | vs Metav4 (n = 100) | vs V46 (n = 60) |
|---|---:|---:|
| skel, ratio to opponent | 0.601 ± 0.010 | 0.630 ± 0.016 |
| **route**, change | **−0.012 ± 0.014** | **−0.014 ± 0.011** |
| **tape**, change | **−0.063 ± 0.016** | −0.007 ± 0.034 |

### Execution in days 6–11, per game, vs Metav4

The Team A column is its 11 replays. Figures vs V46 are within a few percent for skel and route;
see `summary_v46.md`.

| days 6–11 | skel | route | tape | Team A |
|---|---:|---:|---:|---:|
| productive actions | 469 | 507 | 402 | 600 |
| … excluding unneeded water | **469** | **393** | 385 | **570** |
| unneeded water | 0 | 114 | 17 | 30 |
| feed / care / collect fertilizer | 61 / 64 / 55 | 49 / 47 / 51 | 56 / 59 / 54 | 76 / 78 / 81 |
| plant / harvest / fertilize | 57 / 27 / 0 | 55 / 29 / 14 | 40 / 27 / 11 | 71 / 37 / 14 |
| build + place animal | 19 | 25 | 21 | 33 |
| commands that did nothing | 0 | 0 | **232** | 2 |
| idle share of worker-steps | 28.8% | **6.3%** | 5.9% | 2.7% |
| move share | 35.0% | **52.3%** | 44.1% | 47.3% |

### Farm at the start of day 12, vs Metav4

| | skel | route | tape | Team A |
|---|---:|---:|---:|---:|
| crops / animals | 61.2 / 14.7 | 52.7 / 15.8 | 33.4 / 12.1 | 67.6 / 20.8 |
| empty cells / weeds | 22.5 / 0.2 | 27.9 / 2.6 | 19.8 / 5.6 | 11.5 / 0.0 |
| quadrants owned | 4.0 | 4.0 | **3.0** | 4.0 |
| money / shed value | $4,313 / $3,914 | $2,010 / $2,430 | $1,619 / $3,688 | $6,355 / $4,019 |

Against V46 the pattern is the same:
- day-12 crops: skel 57.1, route 50.1, tape 48.7;
- day-12 money: skel $3,281, route $3,334, tape $5,003;
- the tape executed much better against V46: 553 productive actions, 81 failed commands and
  80 feeds.

### Route diagnostics, days 6–11

Route arm, per game; vs Metav4 unless noted (vs V46 it is the same within 1 point).
- **Visits:** Team A's backbone has 388 visits per game.
  - 240 served;
  - **88 had nothing to do on our farm**: 70 judged from afar and 18 found on arrival. That is
    **27% of the visits reached**;
  - **45 fell in quadrants we did not yet own (12%)**;
  - 14 were not reached before midnight (3.5%).
- **Fallback:** hands exhausted their route early. Fallback work then made up 22% of all
  commands, at the cost of 317 fallback moves per game (22% of all worker-steps).
- **What the idle visits were** (20-game diagnostic, `summary_diag.json`):
  - 33 a game: Team A watered or harvested a plant that on our farm needed nothing;
  - 26: Team A serviced an animal on a cell that is empty on our farm;
  - 10: Team A did shed work we did not need;
  - 7: our animal there was already fed, cared for and collected.
- **Service left undone at hour 23** (same 20 games; animal-days / unfed / uncared):
  - skel: 64 / 3.2 / 0.8;
  - route: 64 / **15.3** / **17.3**;
  - Team A: 97 / 21.5 / 20.1.
  - The route-follower serves animals at Team A's rate, feeding about 77% of animal-days. Team A
    does not feed on the placement day. Our planner feeds 95%.
  - Team A's lead in feeding comes from having 50% more animal-days, which is capital, not
    execution.

### The literal tape

The tape does not run as Team A's game.
- Team A's opener spends cash to about $0. At step 24, Team A's day-1 hires need about $4. Against
  Metav4 we hold **$1**, so only 1 of the hires goes through, **in all 100 games**.
- From there the tape commands hands we do not have and cells that differ: 232 no-op commands
  a game in days 6–11.
- Against Metav4 the fourth quadrant (SE) is not bought by day 12 in **any** game: 3
  quadrants at day 12.
- Against V46 the tape reached 4 quadrants in 25 of 60 games. In those games it was +0.057
  vs skel, and −0.052 in the other 35. This split is post hoc and conditioned on an outcome,
  so it is only descriptive.
- Skel's opener guard also trips **at the same step in every game**:
  - step 25 vs Metav4, from the same $1 (one hire instead of three);
  - step 97 vs V46, day 4; the cause was not checked.
  So in arms (a) and (b), most of days 0–5 were already run by the respective executor, not
  the script.

## Verdict

**No: route-following does not close the execution gap. On the measure that matters it
widens it.**
- **Idle time: closed.** The idle share fell from 28.8% to 6.3%, which closes about 87% of the
  idle gap to Team A (2.7%).
- **Useful work: fell.** Excluding unneeded water, productive actions fell from 469 to 393 a
  game (−16%). The gap to Team A grew from about 100 to about 177 actions a game.
- **Where the freed time went:**
  - walking: moves rose from 35% to 52% of worker-steps;
  - 114 unneeded waterings a game;
  - animal service fell to Team A's per-animal rate on a farm with fewer animals.
- **Day 12:** 7–9 fewer crops, more empty cells and weeds, and about $3.8k less cash plus
  shed stock, against either opponent.
- **Bank ratio:** no effect beyond noise, and if anything worse: −0.012 ± 0.014 vs Metav4 and
  −0.014 ± 0.011 vs V46.
- **The literal tape** is worse still vs Metav4 (−0.063 ± 0.016), because Team A's zero-cash
  opener cannot survive a different market by day 1.

**What breaks** (largest first):
1. **The route is Team A's farm, not ours.** 27% of the visits we reach need nothing (Team A's
   animals we do not have, plants already watered). 12% are in land we have not bought yet,
   because our land comes later than Team A's fixed steps. Hands finish early and fall back to
   roaming for the nearest need, and that need is mostly watering that is not needed.
2. **The ~77% feeding rate is copied along with the order.** Our own planner feeds 95%.
3. **Clock mismatch.** Team A's visits to new quadrants are timed to its land steps. When our
   purchase lands later, those planting visits are skipped as locked, and only the fallback
   plants the quadrant. Result: day-12 empty cells of 28–30 against Team A's 11.5.
4. **Cash fragility.** Team A's day-0 plan leaves about $0. A $3 difference in day-0 prices
   removes hires on day 1, which breaks both the literal tape and skel's opener guard.

**What this means for the mode-switching tape agent:**
- The executor gap is not closed by copying order. Team A's routes are efficient *for Team A's
  farm state*. Transplanted without that state, the order costs walking and buys nothing.
- A route executor would have to be planned from **our** farm state each morning, with Team A's
  order used as a prior at most, not a script. It would also need the skeleton's capital
  (animals, land on time) to match. The day-12 farm gap (animals 15 vs 21, cash $2–4k vs
  $6.4k) is at least as large as the execution gap.

## Caveats

- One executor design was measured. Fallbacks and thresholds were fixed before the screen
  and were not tuned on these seeds.
- The rule "water if unwatered" follows the brief. A "water only if needed" variant might
  recover some of the 114 unneeded waterings a game. That was not measured.
- Team A's figures come from ladder games against other opponents, so they are a reference,
  not a paired arm.
- The diagnostic breakdown (idle-visit kinds, coverage) is from 20 of the 100 Metav4 games.
  It was re-run with a stats-only rebuild of `main.py`. All 60 of those games reproduced the
  main run's banks exactly, so the behaviour is identical.

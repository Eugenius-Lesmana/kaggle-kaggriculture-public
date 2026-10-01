# Micro tapes, fertilizer chains, animal release and zones in the top four

Date: 2026-09-28
Status: **measurement.** It tests Eugene's replay reading (27 Sept): each hand runs a
"micro tape" (a backbone route that varies a little), inside a zone, with an adaptive
layer and value-weighted urgent jobs (e.g. letting a low-value animal escape).
It corrects `docs/V010_IDLE_STUDY_2026-09-26.md` §1, which compared a hand's route day to
day and so could not see a tape.

- Tools (untracked): `.cache/micro_study.py` (numbers) and `.cache/micro_pics.py`
  (path pictures).
- Inputs:
  - the top four (Team A, Team B, Team C, Team D), 46 player-games from
    `research/intake/replays/24 Sept/`;
  - our F1 + counter on the ladder, 96 player-games from `research/intake/replays/27 Sept ours/`;
  - our planner, 6 local games each vs V46 on seeds 5791–5796:
    - "our plan" = `.cache/variants/v010_chain`;
    - "their plan" = `.cache/variants/skel`.
- Engine facts used:
  - hands are hired each day and dismissed at midnight, and every inventory is emptied into
    the shed at midnight;
  - `DROP` empties a worker's whole inventory;
  - an unfed animal still produces its base unit and only escapes after 2 unfed days; its
    coop or pasture stays.

## 1. Micro tapes: confirmed, but across games, not day to day

A hand's day is compared with another day under three tolerant measures:
- **order:** edit similarity of the worked cells, where an adjacent cell counts half;
- **blocks:** the order of 2×2 areas visited;
- **gap:** the mean distance in cells between two walks, allowing pauses and detours.

"Shuffled" is the same cells in random order.

| same hand, same day, another game | order (shuffled) | blocks (shuffled) | gap |
|---|---:|---:|---:|
| **top four**, days 6–11 | **0.57** | **0.67** | **0.61 cells** |
| **top four**, days 12–19 | **0.28** | **0.40** | **1.60** |
| F1 (a true tape), days 6–19 | 1.00 (0.29) | 1.00 (0.33) | 0.00 |
| our planner on their plan, days 12–19 | 0.08 | 0.17 | 2.96 |
| our planner on our plan, days 12–19 | 0.11 | 0.20 | 2.24 |

Within one game, a hand's route barely repeats from one day to the next:
- top four: order 0.11 against a shuffled 0.07, and the same for F1 and for us;
- the tape F1 scores 0.00 on this measure too.

**Reading:**
- A tape repeats **across games** (same hand, same day), not across days. The 26 Sept
  day-to-day test could not detect it.
- The top four sit between a tape and our planner: an identical backbone early, which
  loosens as shops diverge, but is still clearly recognisable in days 12–19.
- Our planner loses its shape after day 11.
- **Pictures:** Team A's hand 8 on day 14 follows the same route in all 5 games drawn (out west
  along row 3 collecting fertilizer, then up to the NW corner to water and harvest).
  Hand 5 on day 12 matches in 4 of 5 games.

## 2. Fertilizer chains: confirmed

| | fertilizings / game | from fertilizer the same hand collected from an animal that day | collected fertilizer that gets applied |
|---|---:|---:|---:|
| **top four** | **210** (90 on days 6–19) | **88%**, median 9 steps later, 3 cells away | **41%** |
| F1 | 114 | 23% (77% from shed pickups) | 7% |
| our planner, their plan | 37 | 88% | 9% |
| our planner, our plan | 35 | 50% | 6% |

- The top four fertilize with what they just collected, on the same trip.
- We collect plenty, but 77–79% of it goes back to the shed at midnight unused.
- The earlier "fertilize anything carried" rule (−0.032, `docs/V010_TOP4_TRANSPLANT_2026-09-25.md`)
  was opportunistic. Their chain is planned into the route: animals first, then crops.

## 3. Letting animals go: confirmed, with a correction

**Top four:**
- **2.6 escapes per game on days 0–24** (56 sheep, 47 cows, 16 geese across 46 games), plus
  6.9 per game in the endgame (days 25+).
- At each escape, the animal's product was selling at a **median 15% of its usual price for
  that game**; 77% were below half.
- **2 days later the pen cell holds wheat (71%) or carrot (24%).** Pens are converted to crops,
  not restocked with another animal.

**F1 and our planner:** no escapes before day 25.

## 4. Zones: a home quarter with regular trips out, not rotation

| | days in the hand's usual quarter (median) | day-to-day switch of main quarter |
|---|---:|---:|
| top four | **69%** | 47% |
| F1 | 54% | 59% |
| our planner | 50–57% | 57–65% |

The shed sits at the corner of all four quarters, so animal work around it inflates the
switch rate.

## What this means for an adaptive planner

The three layers in Eugene's model now have evidence:
1. **Backbone:** a route template for each hand and day: start at the shed, service the
   animals on the way out (collect fertilizer, feed, care), fertilize, harvest and water the
   crops in the zone with what was collected, and finish at the rim. It is re-planned each
   morning from the farm and the shops.
2. **Adaptive:** crop and animal choices follow shops and prices
   (`docs/TOP4_MIDGAME_RESEARCH_2026-09-24.md` §4–5).
3. **Urgent jobs weighted by value:**
   - feed only animals whose product is worth it;
   - when a product's price falls below about half its usual level, let the animal go and
     plant wheat or carrot in the pen.

Caveat: our planner's figures are from 6 local games per arm.

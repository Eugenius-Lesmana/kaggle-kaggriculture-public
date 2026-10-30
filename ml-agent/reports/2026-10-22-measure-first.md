# Measure first: where the 4th-place agent's lead on our farm comes from (2026-10-22)

**Answer: the workers.** From the same morning on our farm, the 4th-place agent's worker commands alone, under
our template's plan and market orders, recover 80% of its lead. Its market orders alone (selling, buying, or
both) are worth nothing. Our plan does not block better work.

## Swap test (24 games, mornings 8/12/16/20/24, 120 mornings, one day each, opponent replays its moves)

Value = cash change + goods held and on the farm at closing prices + purchases still held at cost (animals,
seeds, crops in the ground, land), so a day that invests is not scored as a loss.

| Player | Value per day | vs template | Better on | Crops planted | Water | Fertilize |
|---|---:|---:|---:|---:|---:|---:|
| Template | 4,909 | | | 9 | 51 | 8 |
| 4th-place agent | 5,852 | **+942** (se 53) | 94% | 15 | 59 | 13 |
| Template + 4th-place **workers** | 5,665 | **+756** (se 46) | 93% | 14 | 58 | 13 |
| Template + 4th-place **market orders** | 4,869 | -40 (se 34) | 53% | 10 | 51 | 8 |
| Template + 4th-place **sell orders** only | 4,890 | -19 (se 28) | 61% | 9 | 51 | 8 |
| Template + 4th-place **buy orders** only | 4,817 | -92 (se 30) | 32% | 9 | 50 | 8 |

Evidence: `<data>/runs/compare/mixA.csv`, `mixB.csv`; tool `tools/compare_day.py` (players
`mix:fourth:units|market|sell|buy`).

## Day profile (all 552 mornings, days 6-28, from L1)

Same dawn state for both (checked: zero mismatches). Per day: same unit-turns (286) and hires (11.5); the 4th-place
agent does **22 more work turns (+14%) and walks 20 fewer (-16%)**, plants 15 vs 12 crops, fertilizes 12 vs 6,
waters 58 vs 52, and buys fewer seeds (8 vs 14) while planting more, so seed stock was not the limit.
Evidence: `<data>/runs/profile/l1.csv`; tool `tools/day_profile.py`.

## What this settles

| Suspect | Verdict |
|---|---|
| Our plan or seed buying caps the work | **No.** Under our plan the 4th-place workers plant 14 vs 9 and gain +756/day |
| Selling is the gap | **No.** Its sell orders are worth -19/day on our farm |
| Learning or execution fault in our model player | Open: next check |
| Habits do not transfer across layouts | Open: next check (ranker v1 on the 4th-place agent's choices on our farm) |

Decision 1 therefore stays with option A (worker model), and the plan layer can wait.

## Mornings with the biggest gap (for watching)

Game/day, 4th-place minus template value: 10313 d24 (+2,844), 10315 d20 (+2,517), 10303 d24 (+2,199),
10312 d20 (+2,145), 10321 d20 (+2,025), 10313 d8 (+2,015). Template: day N of
`.scratch/template-bench/runs/el3/<game>.json` (competition repository); 4th place:
`<data>/raw/ownfarm/fourth/<game>-d<N>.json.gz`.

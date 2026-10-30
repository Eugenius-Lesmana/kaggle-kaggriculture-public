# Why fifth-nflow earns more against board-p1 than against the teacher (2026-10-26)

**Plain answer:** mostly **production volume**, not selling tactics. Against fifth-nflow, the teacher sells more of
almost every product than board-p1 (eggs +34%, tomatoes +36%, wheat +22%, strawberries +21%, milk +14%) from about
the same purchases. Both farms sell into one shared market where every unit sold lowers the price, so the teacher's
extra volume both earns it more (+14,700 revenue a game) and lowers fifth-nflow's prices (-13,200 for fifth-nflow).
Together that is the 27,752 margin gap. One timing effect on top: board-p1 sells wool at 104 while fifth-nflow gets
143 in the same games (the teacher and fifth-nflow both get about 120).

Source: `tools/market_compete.py` on `runs/nflow-p1` and `runs/nflow-teacher`, 48 paired games (seeds 20001-20024,
both seats); per-game rows `<data>/runs/diag-market/nflow-p1-vs-teacher.csv`. Sales and purchases
are re-simulated exactly from the replays.

## Sales per game (mean)

| Product | board-p1 units | board-p1 price | Teacher units | Teacher price | fifth-nflow revenue vs p1 | fifth-nflow revenue vs teacher |
|---|---:|---:|---:|---:|---:|---:|
| Wheat | 462 | 30 | 564 | 29 | 16,752 | 17,872 |
| Carrot | 166 | 37 | 186 | 40 | 6,614 | 6,706 |
| Tomato | 107 | 62 | 145 | 61 | 8,280 | 8,065 |
| Strawberry | 184 | 148 | 222 | 134 | 32,925 | 27,614 |
| Melon | 71 | 201 | 69 | 203 | 14,376 | 14,709 |
| Egg | 210 | 44 | 281 | 43 | 11,657 | 11,859 |
| Milk | 170 | 112 | 193 | 104 | 24,626 | 19,831 |
| Wool | 129 | 104 | 129 | 119 | 18,674 | 14,979 |
| Fertilizer | 221 | 52 | 245 | 51 | 13,341 | 12,443 |
| **Revenue** | | **121,411** | | **136,111** | **147,245** | **134,078** |

Purchases are close: animals, land, wheat and seed spending 28,766 (board-p1) against 29,133 (teacher); board-p1 buys
more geese (13 against 9) yet sells fewer eggs (210 against 281).

## What it points to

1. **Output per animal and per field** (eggs from fewer geese, more tomatoes, wheat, strawberries): workers and care
   or feeding bonuses, crop mix and replanting. This is worker and plan work (correction round 3, package M).
2. **Sale timing for wool and milk**: smaller, and a market-head question.

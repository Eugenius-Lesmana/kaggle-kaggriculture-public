# Sell split: which causes explain the 9.6k (2026-10-30)

Follows `reports/2026-10-30-sell-diagnosis.md`.

**Answer:** board-p5 sells 10,325 a game worse than the teacher against fifth-nflow's prices in the same market (se 873):
- **Crashed-market sales on days 6-28: +4,216 (se 632).** These are units sold at ≤ 25% of the base price, mostly on
  days 20-28. The network plays these days.
- **Day-29 dump: +2,780 (se 327).** Most of it is in the first hours of day 29. The template plays this day.
- **Ordinary sales two or more hours after a shop pull: +3,810 (se 626).** Our own price in this slot is the same as the
  teacher's (0.98 against 0.99 of base). The difference is fifth-nflow getting better prices in our games: it wins the race.
- **Sales right after a pull: −481 (se 490).** Here we are no worse.

Crashed and day-29 sales together are 7.0k of the 10.3k. Both can be targeted by rules without learning.

## Method
- Tool `tools/sell_diagnosis.py --no-ceiling` now also writes `sales.csv`: one row per sale with its step, units,
  price, quote and hours since the last shop pull of that product. Run `<data>/runs/sell-split`.
  Split: scratchpad `split.py`.
- Same 48 paired games as the diagnosis (`nflow-teacher` against `nflow-p5-best`, seeds 20001-20024, both seats).
- Loss of a sale = (fifth-nflow's mean unit price for that product in that game − our price) × units. Summed, this gives
  exactly the diagnosis numbers: teacher −746, board-p5 9,580 a game.
- Each sale gets one category, checked in this order: day 29; crashed (price ≤ 25% of base); right after a pull (the
  first hour after the town took that product); other.

## Results (per game)
| Category | Units teacher → p5 | Loss teacher → p5 | Change (se) | Price / base teacher → p5 |
|---|---|---:|---:|---|
| Right after a pull | 379 → 359 | −877 → −1,358 | −481 (490) | 1.01 → 1.06 |
| 2+ h after a pull | 1,317 → 1,172 | −9,216 → −5,406 | +3,810 (626) | 0.99 → 0.98 |
| Crashed, days 6-28 | 118 → 166 | 6,596 → 10,812 | +4,216 (632) | 0.16 → 0.11 |
| Day 29 | 221 → 211 | 2,752 → 5,532 | +2,780 (327) | 0.78 → 0.68 |
| **Total** | 2,034 → 1,908 | −746 → 9,580 | **+10,325 (873)** | |

### Crashed sales
- By product (p5 loss / teacher loss): wool 3,456 / 2,705, fertilizer 2,595 / 1,557, strawberry 2,444 / 780, milk
  2,257 / 1,498.
- Units (p5 / teacher): fertilizer 70 / 46, milk 35 / 28, strawberry 27 / 11, wool 34 / 34.
- By day: days 13-19 1,465 / 1,166; days 20-24 4,852 / 2,953; days 25-28 4,402 / 2,394. The excess is late game.

### Day 29
- By hour (p5 / teacher): hours 0-5 86 units, loss 2,658 / 53 units, 659; hours 12-17 3 units / 46 units; hours 18-23
  about equal (117 / 115 units, loss 2,470 / 1,419).
- Crashed units on day 29: 49 / 22. Milk 22 / 11 and wool 12.5 / 6 units.
- The template sells a large batch at dawn. The teacher spreads its sales over the day, so shop pulls absorb them.

### Ordinary sales
- The teacher beats fifth-nflow's mean price by 9.2k a game in this slot. board-p5 beats it by 5.4k, at the same price
  level.
- The biggest change is strawberry: −1,962 → −342. p5 sells 62 strawberries right after a pull, against the teacher's 111.

## What this means
1. **Day 29 first.** It is the template's day and the last day, so a change cannot compound into later days. Spread
   the day-29 sales over the shop pulls and avoid crashed prices until the last hours. Target: up to 2.8k.
2. **A price floor on days 20-28:** hold units whose price is ≤ 25% of base unless the shed is near full. Target: up
   to 4.2k. Risk: held units move to later sales or to day 29.
3. **The post-pull race (3.8k)** is the hardest to fix and the only part that needs the opponent's timing. It comes
   later.

Measured here: the split. Not measured: what a rule recovers in live games. That needs runs.

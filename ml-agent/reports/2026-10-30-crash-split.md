# Crashed-sales split: how much a days 20-28 sell rule could recover (2026-10-30)

**Answer:** little. Of board-p5's extra 4,216 a game in crashed sales on days 6-28 (`reports/2026-10-30-sell-split.md`):
- 2,438 is more units sold into crashed markets: strawberry 1,182, fertilizer 825, milk 397;
- 769 is the yardstick (fifth-nflow's mean price is higher in our games);
- 1,008 is a lower price on those sales (wool 427).

Holding the crashed units for up to 24 h would add at most 1,695 a game, against the teacher's 615 on the same test.
That is about 1.1k more than the teacher, as an upper bound that ignores our own price impact and shed room. Fertilizer
never recovers (no shop buys it). A rule recovering a few hundred cannot be confirmed: changing days 20-28 changes the
network's later play, and those runs have had se 600-1,100.

## Method
Scratchpad `crash.py` on `runs/sell-split` (the 48 paired games, teacher → board-p5), with the market path re-read from
each replay. A sale is crashed when its price is ≤ 25% of base; day 29 is excluded (see `reports/2026-10-30-end29.md`).

## Results (per game)
| Product | Crashed units | Gap | More units | Yardstick | Lower price | Price teacher → p5 |
|---|---|---:|---:|---:|---:|---|
| Strawberry | 10.7 → 26.9 | 1,664 | 1,182 | 266 | 215 | 20 → 12 |
| Fertilizer | 45.5 → 69.6 | 1,038 | 825 | 14 | 199 | 14 → 11 |
| Milk | 27.6 → 34.9 | 759 | 397 | 197 | 165 | 27 → 23 |
| Wool | 33.6 → 34.0 | 750 | 32 | 291 | 427 | 31 → 19 |
| **Total** | | **4,216** | **2,438** | **769** | **1,008** | |

Holding test: for each crashed unit, the best later quote of that product (no own impact, no shed limit).

| | Crashed revenue | Best within 4 h | Within 24 h | By game end |
|---|---:|---:|---:|---:|
| Teacher | 2,700 | +21 | +615 | +2,324 |
| board-p5 | 2,580 | +352 | +1,695 (wool 886, strawberry 553, milk 256, fertilizer 0) | +4,050 |

Supply and town drain, days 20-28, units a game:
- Milk: ours 86, fifth-nflow 86, drain 161 (teacher's games: 84 / 83 / 158).
- Wool: ours 51, fifth-nflow 48, drain 102 (47 / 43 / 94).
- Strawberry: ours 130, fifth-nflow 116, drain 214 (116 / 109 / 206).
- Fertilizer: ours 69, fifth-nflow 52, drain 24 (50 / 54 / 10). The fertilizer price falls from 26 to 7 in both runs.

The late markets are close to balance in both runs. Our total supply is not much larger than the teacher's. The crashes
are short dips in which board-p5 sells bursts, mostly strawberry and wool.

## Decision
No days 20-28 floor rule for now. Its realistic gain is a few hundred a game, below what 96 games can detect when the
late game changes. The sell-timing work netted `end29` (+98). The rest of the selling gap is the opponent getting the
good prices first and our stock mix, not when we press sell.

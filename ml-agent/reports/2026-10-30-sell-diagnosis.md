# Sell diagnosis: why board-p5 earns less from what it sells (2026-10-30)

**Answer:** mostly price, not volume, and the price loss is about selling at the wrong moment.
- Over a full game, board-p5's sales earn 7,833 a game less than the teacher's (se 940): about three quarters price
  (−5,983), one quarter volume (−1,850).
- **In the same game, with the same shared market, board-p5 gets 9,580 a game less for its units than fifth-nflow gets
  per unit (se 808).** The teacher gets 746 a game more than fifth-nflow (se 305).
- The loss is in strawberry (2.9k), wool (2.3k), milk (2.1k), fertilizer (1.3k) and melon (0.7k).
- The causes are: missing the moment right after a town shop buys; more units sold into a crashed market; and more
  selling on the last day.
- The causes are not: holding goods too long, the size of our own batches, or unsold stock.

## Data and method
- Tool `tools/sell_diagnosis.py`. Run `<data>/runs/sell-diag` (rows.csv). Summary: scratchpad
  `sell_report.py`.
- 48 paired games: `nflow-teacher` and `nflow-p5-best`, seeds 20001-20024, both seats, against fifth-nflow. This is
  diagnosis only; nothing is trained or tuned on these seeds.
- Every game is re-simulated with the replay extractor, which gives the exact price of each unit sold.
- Engine facts (kaggle-environments 1.32.7):
  - A product's price depends only on the shared market stock. Every unit sold by either player adds 1, except sales
    at a price of 1.
  - Only town consumption brings the stock back down: every 4 hours each unlocked shop takes its products (2 units for
    a one-product shop), and the town center takes 1 of each non-fertilizer product per day.
  - The final score is money, so unsold stock is worth nothing.

## Results (per game, teacher → board-p5)

| Product | Units | Price per unit | Revenue gap | of which volume | of which price | Market level at sale | Sold right after a shop pull | Units at ≤ 25% of base | Sold on day 29 |
|---|---|---|---:|---:|---:|---|---|---|---|
| Wheat | 564 → 479 | 28.7 → 29.6 | −2,005 | −2,449 | +444 | 29.0 → 29.9 | 20% → 34% | 0 → 0 | 96 → 82 |
| Carrot | 186 → 148 | 39.7 → 41.3 | −1,281 | −1,508 | +227 | 40.6 → 42.1 | 11% → 25% | 0 → 0 | 40 → 24 |
| Tomato | 145 → 127 | 61.4 → 61.4 | −1,161 | −1,162 | +1 | 63.0 → 62.6 | 5% → 17% | 0 → 0 | 14 → 13 |
| Strawberry | 222 → 226 | 133.6 → 124.8 | −1,376 | +607 | −1,982 | 137.8 → 131.3 | **59% → 32%** | **12 → 33** | 15 → 18 |
| Melon | 69 → 75 | 203.4 → 194.7 | +665 | +1,313 | −648 | 209.4 → 199.4 | 4% → 11% | 0 → 0 | 0 → 0 |
| Egg | 281 → 244 | 43.1 → 43.3 | −1,550 | −1,599 | +49 | 43.3 → 43.5 | 8% → 19% | 0 → 0 | 26 → 20 |
| Milk | 193 → 203 | 103.6 → 96.7 | −385 | +1,036 | −1,421 | 109.8 → 101.9 | **72% → 59%** | **32 → 51** | **11 → 22** |
| Wool | 129 → 133 | 118.7 → 110.0 | −658 | +494 | −1,153 | 125.6 → 120.3 | **50% → 29%** | 37 → 42 | **6 → 12** |
| Fertilizer | 245 → 272 | 51.1 → 45.6 | −82 | +1,417 | −1,499 | 52.0 → 46.6 | 2% → 7% | **58 → 89** | 12 → 19 |
| **Total** | | | **−7,833** | **−1,850** | **−5,983** | | | | |

- **Volume:** we sell fewer cheap crops (wheat, carrot, tomato, egg) and more of the expensive goods. That's the
  worker side.
- **Our own batches are not the problem.** The price drop from our own units within a step (quote minus received) is
  within 2-3 coins of the teacher's, against a 6-10 coin gap in market level.
- **We don't hold goods too long.** Mean hours from shed to sale are about the same or shorter (strawberry 10 against
  13, egg 8 against 12). Neither player leaves stock unsold.
- **The race against fifth-nflow is lost:**
  - fifth-nflow sells right after shop pulls about as often as the teacher (strawberry 55-59%, milk 71-72%);
  - in board-p5's games it gets the high post-pull price first, and board-p5 sells into what it leaves;
  - fifth-nflow's sales revenue is 5,668 a game higher in board-p5's games than in the teacher's (se 636), at better
    prices: strawberry 138 against 133, milk 107 against 101, wool 128 against 120.

### Same game, same market: our price against fifth-nflow's
Per game: (fifth-nflow's price per unit − ours) × our units.

| Product | Teacher | board-p5 |
|---|---:|---:|
| Strawberry | −315 | 2,947 |
| Wool | 181 | 2,260 |
| Milk | −250 | 2,143 |
| Fertilizer | −165 | 1,310 |
| Melon | 3 | 705 |
| Others | −200 | 215 |
| **Total** | **−746 (se 305)** | **9,580 (se 808)** |

### Timing ceiling
The most our own sales could earn by re-timing alone. It uses the exact price formula, our units' shed arrival times,
and fifth-nflow's sales and the shop pulls held fixed. Shed capacity is ignored. It is optimistic, because fifth-nflow
would react.

| Window | Teacher | board-p5 |
|---|---:|---:|
| within 4 h of arrival (or by the real sale) | +3,816 | +5,641 |
| within 24 h | +8,070 | +10,899 |

## What this means
The selling problem is when, not how much. A sell-only fix should target three things:
1. selling into the hour right after a shop pull, before fifth-nflow does;
2. not selling into a crashed market (the near-worthless strawberry, milk, wool and fertilizer sales);
3. the last-day dump of milk, wool and fertilizer.

Measured here: the size of the loss and its signs. Not measured: how much of the 9.6k each of the three causes
explains. That needs a per-sale breakdown (a small extension of the tool).

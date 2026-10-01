# Market edge: production volume, not sale pricing

Date: 2026-09-30  
Branch: `dev/eugene-codex-market-edge`  
Scope: replay analysis only; no games or seeds used.

## Verdict

The top agents' edge over our v0.10 planner is **units available to sell, not better realized prices**. For the three top submissions without heavy product trading, the final bank averages **$112,910**, versus **$79,330** for our planner (+$33,580/game). Confirmed sale revenue differs by **+$39,640/game**: **+$41,423 from units** and **−$1,783 from price** under the symmetric decomposition below. Against F4 + counter, the same top three have a **+$14,441 bank gap**, but only **+$7,505 sale revenue gap** (**+$8,791 units; −$1,286 price**). Other spending and receipts account for the residual; this is an accounting comparison, not a causal treatment effect.

The fourth top submission, `56640149`, has a distinct trading pattern: **3,470 confirmed wheat units sold/game** and **3,569 wheat units requested in `BUY_PRODUCT` orders/game**. It also requests 745 fertilizer units/game. Its gross sale revenue is $264,667/game but its bank is $110,143/game, close to the other top agents. Including it in a pooled "top four" gross-sales comparison would count purchased product turnover as a farming advantage. The all-four tables are retained for completeness; the three-agent comparison drives the production-versus-pricing verdict.

## Samples and attribution

- **Top:** 536 player-games from the four 29 September folders (181 / 140 / 108 / 107). The analyzed seat matches that folder's submission ID in `episodes.json`.
- **F4 + counter:** 239 matching-seat player-games from `28 Sept f4` (submission `56620927`).
- **Our planner:** 240 v0.10 control rows across `f1_ctrl`, `f2_ctrl`, `a1_ctrl` on `dev/eugene-claude-routeopt`, each against Metav4. These contain per-product `own_sold` and `own_revenue`, but no order timing or end-of-day stock.
- Replays are loaded one gzip file at a time. Sales use the holdings delta and one-unit market lockstep in `scripts/screen.py`; a step contributes only when replayed money matches the observed bank change. `NOOP` market orders are treated as no-ops. Unverified candidate units average **40/game** for the top three, **36/game** for F4, **1/game** for the planner, and **339/game** for the trading top agent. No unverified unit is assigned revenue.
- Prices are realized sale revenue divided by confirmed units. Revenue shares use the nine listed products, including fertilizer. The groups played different opponents and seeds; gaps below are descriptive, not paired estimates.

## Product mix

Each cell is **units sold/game · realized $/unit · share of confirmed sale revenue**. "Top all" includes the high-turnover submission; "top three" excludes only `56640149`.

| Product | Top all (536) | Top three (355) | F4 + counter (239) | Planner (240) |
|---|---:|---:|---:|---:|
| Wheat | 1,511 · $34.6 · 29% | 512 · $32.6 · 12% | 545 · $40.4 · 17% | 308 · $35.2 · 11% |
| Carrot | 168 · $43.4 · 4% | 159 · $44.2 · 5% | 125 · $50.1 · 5% | 84 · $56.1 · 5% |
| Tomato | 60 · $73.1 · 2% | 91 · $73.1 · 5% | 13 · $212.0 · 2% | 0 · — · 0% |
| Strawberry | 217 · $143.2 · 17% | 223 · $140.5 · 22% | 245 · $116.5 · 22% | 164 · $140.2 · 23% |
| Melon | 72 · $197.5 · 8% | 71 · $198.8 · 10% | 72 · $201.6 · 11% | 54 · $183.6 · 10% |
| Egg | 248 · $44.5 · 6% | 245 · $44.9 · 8% | 78 · $50.1 · 3% | 81 · $51.0 · 4% |
| Milk | 190 · $109.5 · 11% | 188 · $110.5 · 15% | 199 · $111.5 · 17% | 134 · $131.5 · 18% |
| Wool | 140 · $139.2 · 11% | 135 · $144.7 · 14% | 154 · $112.9 · 13% | 145 · $125.3 · 18% |
| Fertilizer | 471 · $45.7 · 12% | 241 · $52.6 · 9% | 321 · $46.0 · 11% | 249 · $47.1 · 12% |

The top three sell far more egg and tomato than F4, and more wheat, strawberry, melon, egg, and milk than our planner. F4 sells more strawberry, milk, wool, fertilizer, and slightly more wheat than the top three, but earns less overall.

## Selling behaviour

A sale event is one verified product's units sold in one turn, aggregated across that turn's orders. Stock is shed plus carried non-seed items at observation hour 23, averaged across days and games. "Local high" means the pre-sale displayed price equals the maximum displayed price within ±4 observations on the same day; it is a descriptive window measure, not an optimal-execution counterfactual.

| Group | Sale events/game | Units/event | Local-high unit share | Day-end stock |
|---|---:|---:|---:|---:|
| Top all | 612 | 5.0 | 70.9% | 59.0 |
| Top three | 430 | 4.3 | 76.1% | 59.5 |
| Trading top `56640149` | 970 | 5.6 | 67.5% | 58.0 |
| F4 + counter | 282 | 6.2 | **80.1%** | 50.5 |

The typical game median sale size is 2.9 units for the top three and 3.9 for F4; the corresponding within-game 90th percentile averages 9.8 and 14.2. F4 makes fewer, larger sales and more often hits a local price high.

The engine drains shop inventory after turns whose step number is divisible by 4; the daily town drain is after steps divisible by 24. An action recorded at observation **hour 2** is the first opportunity after the hour-1 observation reflects a drain. **29.7%** of top-three units and **41.9%** of F4 units sell at the first post-shop-drain phase (hours 2, 6, 10, 14, 18, 22). At the first post-daily-drain hour 2, the shares are **10.0%** and **21.1%** respectively. The top three sell **14.5%** at hour 23, versus F4's **3.2%**. F4's timing is at least as price-aware by these measures.

## Revenue and bank decomposition

For each product with positive volume on both sides, let `Q` be units/game and `P` realized $/unit. The exact symmetric split is:
`unit effect = (Q_top − Q_base) × (P_top + P_base)/2`;
`price effect = (P_top − P_base) × (Q_top + Q_base)/2`.
Their sum is the sale revenue gap. When a baseline sold zero units, its price is undefined, so the entire entry revenue is assigned to units (tomato versus planner). Values below are **$/game**, rounded; each cell is **revenue gap (unit effect, price effect)**.

| Product | Top three − F4 | Top three − planner |
|---|---:|---:|
| Wheat | −5,316 (−1,202, −4,114) | +5,877 (+6,922, −1,045) |
| Carrot | +798 (+1,626, −828) | +2,347 (+3,787, −1,440) |
| Tomato | +3,834 (+11,047, −7,212) | +6,627 (+6,627, $0) |
| Strawberry | +2,860 (−2,779, +5,639) | +8,349 (+8,280, +69) |
| Melon | −475 (−276, −199) | +4,192 (+3,248, +943) |
| Egg | +7,101 (+7,939, −839) | +6,869 (+7,865, −995) |
| Milk | −1,348 (−1,157, −192) | +3,107 (+6,503, −3,396) |
| Wool | +2,094 (−2,490, +4,584) | +1,305 (−1,418, +2,723) |
| Fertilizer | −2,042 (−3,918, +1,875) | +966 (−392, +1,358) |
| **Total sale revenue** | **+7,505 (+8,791, −1,286)** | **+39,640 (+41,423, −1,783)** |
| **Final bank gap** | **+14,441** | **+33,580** |
| **Other net bank effects** | **+6,936** | **−6,060** |

For **all four** top agents pooled, the gross revenue gap is +$49,682 versus F4 (+$53,391 units, −$3,709 price) and +$81,816 versus the planner (+$85,657 units, −$3,840 price). Much of that gross volume is the trading agent's purchased wheat and fertilizer; its purchase costs sit in the "other" bank effects. Requested buy quantities are order intent, not confirmed fills.

## Files and limits

`evaluation/market_edge/analyze.py` reproduces replay attribution and the all-four tables; `summarize.py` adds the non-turnover comparison, behaviour summary, and requested-buy counts. `games.csv`, `products.csv`, `decomposition.csv`, `behaviour_games.csv`, `behaviour_summary.csv`, `comparison_*.csv`, and `buy_order_*.csv` are the measured tables. Inputs stay in place; no replay was copied or committed.

The planner controls are vs Metav4, while the public replays have assorted opponents. Price differences therefore combine strategy, opponent demand, and market state. Observed unit sales combine farm production, held stock liquidation, and purchased product resale; the purchase-order scan identifies the largest resale outlier but does not reconstruct net trade profit. The strongest supported conclusion is that **better sale prices and timing do not explain the bank lead**. The planner's missing early production mix remains the main place to investigate.



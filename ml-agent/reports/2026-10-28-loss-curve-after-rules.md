# Loss curve after rules — 2026-10-28

**The largest remaining window is days 12-21: +10,147 coins/game (paired-seed SE 1,431) recovered by the teacher.** The exact cash contributions follow.

**Current agent: `net:board-p4:market:overflow:endmask:endwork`.** The table below gives the largest remaining cash contributions per window. These estimates use eight independent evaluation seeds, both seats; positive means the teacher intervention improves our final margin.

| Window | Margin gain/game (seed SE) | Largest cash contributions |
| --- | --- | --- |
| 12-21 | +10,147 (1,431) | opponent net effect +4,884; later own net +1,834; spending saved +1,771 |
| 22-27 | +2,702 (695) | later own net +1,827; our window sales +1,134; opponent net effect -131 |
| 28-29 | +287 (463) | our window sales +631; opponent net effect -362; spending saved +18 |

All 48 requested handover games are complete, plus two exact fresh-process repeat checks. The teacher takes over at day 12, 22 or 28 and plays the remainder including day 29 itself; our rules do not wrap its actions. Controls are the same seed/seat games from `runs/nflow-p4-ovf-end-ew`. This updates the old unruled P4 diagnosis; it does not compare the new and old policies on different farms as if they shared a morning.

| Teacher from day | Gain vs ruled baseline/game | Paired-seed SE |
| --- | --- | --- |
| 12 | +13,136 | 1,324.80 |
| 22 | +2,989 | 510.86 |
| 28 | +287 | 462.60 |

## Cash split that adds exactly

| Window | Our sales Δ | Spend saving | Later own net Δ | Opponent during | Opponent later | Total | Residual |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 12-21 | +1,658 | +1,771 | +1,834 | +2,318 | +2,566 | +10,147 | 0.00 |
| 22-27 | +1,134 | -130 | +1,827 | -859 | +729 | +2,702 | 0.00 |
| 28-29 | +631 | +18 | +0 | -362 | +0 | +287 | 0.00 |

Every pair is identical through the window-start morning. Windows are handover12 vs handover22 (12–21), handover22 vs handover28 (22–27), and handover28 vs the ruled baseline (28–29). All 48 pair prefixes and terminal margins are checked, and the window gains telescope to handover12 minus baseline for every seed and seat. Later own net is realized subsequent revenue minus spending. Both branches use the teacher later, but its memory, cash, inventory and reacting market/opponent can differ; it is not a pure farm-layout causal effect.

## Production, selling and directly measured discarded stock

| Window | Harvest/collection Δ value | Own-best timing Δ | Market frontier Δ | Inventory release Δ | Buyback input value Δ | Consumption saving Δ | Discard saving Δ | Own sales Δ |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12-21 | +3,114 | +123 | -877 | -452 | -989 | +685 | +52 | +1,658 |
| 22-27 | +322 | +1,730 | +452 | -467 | -76 | +271 | -1,098 | +1,134 |
| 28-29 | +1,601 | -79 | +1,490 | -2,284 | +0 | +33 | -129 | +631 |

For each product/day, both branches use the same reference C: the maximum observed price across the pair, including executed unit prices from both seats. Revenue is produced×C + bought-input×C − consumed×C − discarded×C − (closing-held−opening-held)×C plus sale-timing and market-frontier gaps. The native hooks directly count both night overflow and DROP discards; their sum must equal the stock-flow depletion remainder for every product/day/seat. Thus this update checks actual discard units rather than leaving the old inferred remainder unclassified. Their marked value is a diagnostic inside the sales bridge, not extra cash added to sales again. Add the cash table’s spend/later/opponent terms to this production-to-sales row to recover final margin exactly.

Daily best is a hindsight opportunity benchmark, not an executable price for an entire batch. Timing is actual revenue minus sold units times that branch’s own day-best; the frontier term records differences between its own day-best and the pair’s C. Prices are endogenous to both players. Opponent effects include its spending; this does not identify a specific sale as causing a particular opponent price change.

## Per-product in-window detail

| Window | Product | Harvested Δ units | Sold Δ units | Revenue Δ | Timing Δ | Frontier Δ |
| --- | --- | --- | --- | --- | --- | --- |
| 12-21 | WHEAT | -7.31 | -9.75 | -460 | -1 | -108 |
| 12-21 | CARROT | 6.25 | 2.56 | +111 | -2 | -8 |
| 12-21 | TOMATO | 10.31 | 5.88 | +379 | -31 | -11 |
| 12-21 | STRAWBERRY | 4.75 | 3.69 | +489 | -158 | -169 |
| 12-21 | MELON | 0.69 | 0.69 | +100 | +4 | -11 |
| 12-21 | EGG | 4.19 | 3.62 | +150 | -13 | -2 |
| 12-21 | MILK | 3.06 | 2.06 | +505 | +61 | -224 |
| 12-21 | WOOL | 2.38 | -1.12 | +437 | +208 | -373 |
| 12-21 | FERTILIZER | -10.06 | -5.88 | -54 | +56 | +29 |
| 22-27 | WHEAT | -5.31 | -1.44 | -23 | -18 | -113 |
| 22-27 | CARROT | 22.50 | 11.38 | +472 | -8 | -28 |
| 22-27 | TOMATO | 1.38 | -1.38 | -86 | +16 | -12 |
| 22-27 | STRAWBERRY | 1.69 | -11.94 | +534 | +717 | +492 |
| 22-27 | MELON | 0.00 | 0.00 | +0 | +0 | +0 |
| 22-27 | EGG | -2.81 | -2.94 | -114 | +4 | -2 |
| 22-27 | MILK | -10.62 | -6.88 | +207 | +213 | +97 |
| 22-27 | WOOL | -3.19 | -5.88 | +152 | +772 | -14 |
| 22-27 | FERTILIZER | -1.38 | -19.81 | -8 | +33 | +32 |
| 28-29 | WHEAT | 30.25 | 8.00 | +161 | -22 | +19 |
| 28-29 | CARROT | 11.06 | 0.00 | +2 | -7 | +2 |
| 28-29 | TOMATO | 1.62 | -1.19 | -40 | +12 | +1 |
| 28-29 | STRAWBERRY | 2.25 | -0.62 | +89 | +27 | +144 |
| 28-29 | MELON | 0.00 | 0.00 | +0 | +0 | +0 |
| 28-29 | EGG | 0.12 | -4.31 | -173 | +0 | +0 |
| 28-29 | MILK | 2.00 | -8.81 | +161 | +54 | +458 |
| 28-29 | WOOL | -0.62 | -4.06 | +464 | -147 | +860 |
| 28-29 | FERTILIZER | -1.00 | -6.25 | -34 | +4 | +6 |

## Evidence and limits

The SE averages the two seats within each of eight seeds before estimating dispersion. No test contents 10320–10324 are read. These seeds 20001–20008 are evaluation only. Worker count is four by Eugene’s explicit override of the handoff’s original two-worker limit. An owned wrapper invokes unchanged `run_full.one/verify` in fresh processes; protected player/training/encoding/vendor files are unchanged. Teacher code and weights remain on D:.

- [Curve](2026-10-28-loss-after-rules-curve.csv), [paired monetary bridges](2026-10-28-loss-after-rules-paired.csv), [window summary](2026-10-28-loss-after-rules-summary.csv).
- [Product and opponent detail](2026-10-28-loss-after-rules-products.csv), [spending](2026-10-28-loss-after-rules-spending.csv), [work](2026-10-28-loss-after-rules-work.csv), [planting](2026-10-28-loss-after-rules-planting.csv).
- [Boundary assets](2026-10-28-loss-after-rules-assets.csv), [boundary crops](2026-10-28-loss-after-rules-boundary-crops.csv), [source hashes](2026-10-28-loss-after-rules-sources.csv), [checks](AFTER_RULES_LOSS_CHECKS.json).

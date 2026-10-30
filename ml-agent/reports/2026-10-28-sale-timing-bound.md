# Sale timing on recorded markets — 2026-10-28

**The recorded-market timing oracle adds +4,946 sale coins/game (paired-seed SE 311) with recorded shed availability. Giving it the whole day’s goods from dawn raises the ceiling to +9,011.** These are conditional hindsight revenue benchmarks, not measured full-game margin improvements.

Uses the 16 existing ruled-P4 games in `runs/nflow-p4-ovf-end-ew`, seeds20001–20008, both seats. Each product/day retains exactly its recorded sold quantity. No policy games, training or protected code changes.

## Benchmark definition and scope

Start-of-turn inventory is reset to that turn’s recorded market. Within a turn we use the actual engine price function and per-unit simultaneous quoting: a sale at price1 does NOT increase supply; purchases reduce supply; both seats quote before either commits. Fifth-nflow’s recorded order slots and executed quantities, and our recorded product purchases, are fixed. Counterfactual prices do not change fills, solvency, worker behaviour or the next turn’s recorded inventory. Thus this is a recorded-path/recorded-fill benchmark, not a self-consistent counterfactual season with opponent cash and inventory feedback.

The oracle chooses a turn, order slot and quantity, with at most one positive SELL per product/turn, matching the current market head. We verify that the baseline also has at most one. Products are optimized independently, so summed schedules may conflict with the joint10-order limit. Day29 has23 actionable turns. Costs, purchases, terminal margin and opponent gains are not added to our sale-revenue gain.

The stock-aware variant constrains cumulative sales using recorded post-worker/pre-market shed stock and unchanged purchases/flows. It cannot sell goods before their recorded arrival in the shed. Intermediate worker-order effects, changed discard/capacity outcomes and cross-product conflicts are not simulated, so its schedule is still an optimistic conditional benchmark. The free-stock ceiling additionally grants the entire fixed daily quantity from dawn. Dynamic programming finds the exact optimum in each stated model, including nonlinear per-unit depth and floor effects.

## Per product, coins per game

| Product | Actual sales | Stock-aware timing gain | Seed SE | Free-stock gain | Match fifth gain on covered cells | Covered units |
| --- | --- | --- | --- | --- | --- | --- |
| WHEAT | 16,929.8 | +209.9 | 20.1 | +305.7 | -15.4 | 98.2% |
| CARROT | 4,585.9 | +44.4 | 10.2 | +96.6 | -1.4 | 92.8% |
| TOMATO | 8,879.5 | +117.8 | 16.0 | +154.4 | +1.9 | 96.8% |
| STRAWBERRY | 23,087.4 | +1,123.1 | 254.5 | +1,601.2 | +656.7 | 98.1% |
| MELON | 14,557.4 | +143.6 | 29.4 | +1,086.0 | +51.1 | 88.5% |
| EGG | 9,377.2 | +65.3 | 9.7 | +73.2 | -17.2 | 99.0% |
| MILK | 21,909.1 | +1,261.6 | 184.9 | +2,304.5 | +1,010.9 | 98.3% |
| WOOL | 13,728.1 | +1,731.0 | 577.4 | +3,021.9 | +1,308.3 | 86.5% |
| FERTILIZER | 12,565.6 | +249.6 | 17.4 | +367.2 | +137.8 | 97.7% |

## Day bands, coins per game

| Days | Actual sales | Stock-aware timing gain | Seed SE | Free-stock gain | Match fifth gain on covered cells | Covered units |
| --- | --- | --- | --- | --- | --- | --- |
| 0-5 | 3,262.8 | +3.4 | 0.8 | +39.3 | +0.2 | 93.4% |
| 6-11 | 25,045.5 | +86.8 | 27.7 | +1,735.8 | -36.6 | 96.9% |
| 12-17 | 34,902.2 | +785.1 | 72.5 | +1,827.2 | +542.8 | 96.3% |
| 18-23 | 31,526.9 | +1,640.6 | 148.0 | +2,239.9 | +864.6 | 96.2% |
| 24-29 | 30,882.6 | +2,430.4 | 258.6 | +3,168.5 | +1,761.8 | 97.4% |

## Matching fifth-nflow’s capture

Matching its same-game/product/day capture changes revenue by +3,133/game on cells covering 96.7% of our sold units. Where it sold nothing, capture is undefined: no gain is imputed for those cells. The reported gain is only the subtotal on covered cells, not an estimate for uncovered goods.

For each product/day, the common hindsight day-best includes both seats’ actual unit executions and recorded displayed quotes. Capture = actual revenue/(units×day-best). Matching fifth’s capture therefore gives our units×its average realized unit price on that same market/day. Negative gains are retained. This arithmetic transfer does not respect the depth cost of our batch size and can exceed an executable timing result; it is not another feasible oracle schedule.

## Interpretation

A learned selling experiment is worth testing first on wool, milk and strawberry: they account for 83.2% of this model’s stock-aware headroom. Days18–29 account for 82.3%. These priorities come from the benchmark; they are not expected realized gains.

The learned seller’s timing opportunity on unchanged recorded deliveries is bounded by this model’s 4,946 coins/game headroom; the larger free-stock number additionally requires earlier availability/delivery assumptions. These quantities size a selling-policy experiment; they do not establish that a learned policy will attain the oracle, or that market reactions and work costs preserve its gain. Realized-price differences in the earlier teacher comparison include product mix and different market paths, so that entire gap cannot be called timing loss.

## Verification and evidence

All16 original action traces are replayed natively (six tables each). Every product/day’s original unit count and revenue is reconstructed exactly with the market primitive, including floor1 supply suppression. Every oracle path is backtracked: unit totals, availability constraints, path revenue and baseline dominance are checked. Small independent exhaustive-search and native-auction tests cover both seats, purchases and floor prices. SEs average both seats within each of eight seeds; they do not treat16 games as16 independent samples.

[Daily product cells](2026-10-28-sale-timing-daily.csv), [product/band summary](2026-10-28-sale-timing-summary.csv), [stock-aware schedules](2026-10-28-sale-timing-schedules.csv), [checks](SALE_TIMING_BOUND_CHECKS.json).

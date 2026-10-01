# Generic market module — 2026-10-01

## Verdict

The portable mechanisms are a price curve, marginal-price exposure ordering,
an above-base held-stock sale gate, and F4's bounded one-turn price forecast.
The wheat opening is a fixed same-turn round trip, not a drain-timed arbitrage:
it **lost $3/game versus buying only the five retained units** in this sample.
It is included behind a default-OFF flag.

Metav4's melon premium accompanies **earlier native deliveries/sales**. In four
new games it sold 72 melons/game, almost all on day 10; our first sale was day
11. None of Metav4's instrumented lead/reservation/forecast additions involved
melon. The standalone module cannot sell stock still in the field or carried
by workers; these results do not establish that market timing alone recovers
the roughly $60/melon gap.

`evaluation/market_module/market.py` is delivered but **not wired into the
planner**. No integrated module bank gain has been measured.

## Evidence and accounting

- Branch `dev/eugene-codex-market-module`, based on routeopt `c02d09e`.
- Read-only Metav4 SHA256 `9d63494603f88219857a3101d7dc19cc750ded04e5886732ee428580326967d9`;
  F4 `55be5d5f124c8daaaa63c1a29ba4aab096004909666f04748007603c67b7d2a8`.
  `source_audit.json` records live initial actions and final MODELPX bindings.
- Seven routeopt controls: `a1`, `f1`, `f2`, `f3`, `jv`, `jvc`, `jvd`, all
  `*_ctrl.json`: **560 unique seed/seat games**, v0.10 versus Metav4. Their
  consecutive-observation sale accounting separates verified units/revenue
  from unverified units. Weighted prices below use verified fills only.
- **Four new games**, seeds 8301–8304, v0.10 seat 0, Metav4 seat 1, two workers.
  Instrumented actual engine unit commits, including buys. Each seat's ledger
  reconciles exactly: $3000 + sales − purchases − hiring − land = final bank.
  Mean banks: v0.10 **$75,433**, Metav4 **$115,290.75**. Both DONE in all games.
  Only compact transaction fills and summaries were saved, no raw replays.
- No F4 gameplay, module gameplay, large screen, or additional seeds run.

Engine order matters: market fills precede that turn's town consumption.
Shops drain at steps divisible by 4; town also drains at steps divisible by 24.
Thus hour 0 is **before** the daily and shop drain; hour 1 is immediately after
it. Likewise hour modulo 4 = 0 is before a shop drain, modulo 4 = 1 is after
the preceding turn's drain. Each duplicate shop consumes independently;
single-product shops consume two units. Fertilizer has no town/shop drain.
BUY_PRODUCT quotes at inventory minus one; SELL quotes at current inventory.
At the $1 floor a sale does not increase market inventory.

## 1. Wheat round trip and replenishment

| Source | Live opening at step 0 / hour 0 | Retained wheat |
|---|---|---:|
| Metav4 `_v9_opening` | BUY_PRODUCT 20, then SELL 15 | 5 |
| F4 final override | BUY_PRODUCT 8, SELL 3, BUY_SEED WHEAT 1 | 5 |

These are fixed quantities with no profit/low-price gate. Both legs happen
before any drain, in the same action. An older embedded tape has BUY13,
BUY30, SELL30 and a next-turn SELL13/BUY5: **that is not the live opening**.
Runtime initial-observation audit confirms the table above.

In all four games Metav4 bought 20 for $577 and sold 15 for $438. Net cash
outlay $139, retaining five wheat. Reprocessing the same market state with
the opponent action fixed and BUY5 alone costs $136: **−$3/game incremental
cash**. This is a same-step counterfactual, not a full-season intervention.
Against an unchanged market a buy/resell traversal is cash-neutral; concurrent
orders can change the result.

Later buys are physical supply and tape prefunding, not a generic buy-low
schedule:

- `_r95_reserve`: buffer six plus upcoming 48-turn pickup/scheduled-sale needs;
  YARN_STORE instances add SE sheep feed needs. `_r95_replenish` trims days
  10–11 replenishment while retaining same-turn buy/sell combinations.
- `_r97_supply`: projected worker actions and next tape pickup shortages;
  retains sales, augments/adds buys when budget permits, sometimes prefunds
  two turns because the next order book is full.
- `_r127_priority`, steps 144–694: first-slot wheat buy for exact next-turn
  pickup shortage. Uses conservative concurrent-buy cost, funded-input and
  overflow checks. It depends on future tape jobs and is not ported.

Measured later/all wheat buying: **150.25 units/$5,053.25 per game**, average
filled buy lot 3.51 units. Unit shares at hour modulo 4 = 0/1/2/3 are
37.4%/8.7%/35.1%/18.8%; no fixed post-drain buy rule.
`wheat_same_turn.csv` identifies four later same-turn combinations across the
four games: step254 BUY5/SELL5; step278 BUY3/SELL1; step215 BUY9/SELL3;
step575 BUY16/SELL1. The BUY5/SELL5 costs/revenues were both $175. Wheat is
fungible and feeds animals; subtracting all buy costs from wheat sale revenue
would not measure resale profit.

## 2. Sale timing, price gate, and melon evidence

There is no universal per-product sale-hour calendar. Native route deliveries,
scheduled sales, stock, prices and lead rules interact. Measured Metav4 hours
below are unit-weighted across four games; full hour rows are in
`sale_hours.csv` and fractions in `sale_timing.csv`.

| Product | Three largest sale hours (% of units) | Before shop drain, h%4=0 | After prior shop drain, h%4=1 |
|---|---|---:|---:|
| Wheat | 0 (19.5), 1 (17.4), 3 (12.5) | 37.3% | 26.4% |
| Carrot | 1 (56.4), 19 (15.2), 20 (9.8) | 14.1% | 56.4% |
| Tomato | 22 (43.8), 23 (23.8), 15 (12.5) | 7.5% | 0.0% |
| Strawberry | 21 (22.5), 0 (13.8), 19 (13.6) | 18.1% | 41.7% |
| Melon | 10 (29.2), 11 (16.7), 0 (12.5) | 25.0% | 20.8% |
| Egg | 1 (58.9), 0 (16.1), 22 (5.3) | 18.5% | 63.6% |
| Milk | 0 (22.2), 1 (13.8), 21 (12.2) | 37.5% | 37.5% |
| Wool | 1 (16.0), 0 (14.1), 21 (9.6) | 20.8% | 43.9% |
| Fertilizer | 0 (32.2), 1 (32.2), 2 (6.9) | 38.9% | 41.2% |

Metav4 `_v9_racepx_lead`, the final `Chassis._sell_lead`, advances a **next
tape sale by one turn** when projected/held stock exists and quote is strictly
above base. It skips step%4=0, imminent 72-turn unlock boundaries and terminal
steps. Despite earlier parent exclusions, the final blocked-path branch can
include wheat/fertilizer. `_r36_reserve` and later RACE wrappers, steps192–695,
release above-base projected stock against future tape sale quantities, stopping
at future pickups/buys. The source records sale debts to suppress subsequent
scheduled sales; dynamic lookahead ranges from a few to 40+ turns.

The generic port sells **observed held non-input produce** above base during
steps192–695 if the planner has no sale/buy of that product. It assumes that
stock is ultimately intended for sale. It excludes wheat/fertilizer and
does not need tape debt: a live planner reads the reduced shed next turn.
This is a broader held-stock adaptation, not a reproduction of tape lookahead.

### Prices on identical seed/seat controls

| Product | v0.10 verified weighted $/unit | Metav4 verified weighted $/unit |
|---|---:|---:|
| Wheat | 35.31 | 38.30 |
| Carrot | 53.77 | 61.98 |
| Tomato | — | 265.97 |
| Strawberry | 142.53 | 134.57 |
| Melon | **183.60** | **243.70** |
| Egg | 50.75 | 50.22 |
| Milk | 141.86 | 149.34 |
| Wool | 126.89 | 131.09 |
| Fertilizer | 47.09 | 48.96 |

The original F1/F2/A1 240 games give melon $183.61 versus $243.89. The seven
controls extend the same comparison. Metav4 also has unverified sale units
(melon 7.41/game in the full controls); these are excluded from price ratios,
not treated as zero-price sales. See `control_products.csv` for every product's
verified and unverified units.

In four exact-ledger games, melon prices are **$183.39 versus $242.22**.
Metav4 sells roughly 60 units/game during day10 hours8–15 and the remaining
12 late day10/day11 hour0; our first sale is day11 hour0, with further batches
on days15–16 and25–27. Metav4's day10 hourly weighted quotes decline from
about $269.5 at hour9 to $229.5 at hour15, and its day11 hour0 batch gets
$220.2. Our day11 first batch gets about $201.4.

Applying the fresh price difference to our 53.75 melon units is approximately
**$3,163/game of descriptive price premium**. This is not a causal estimate:
production/delivery dates, quantities, shared inventories and subsequent prices
also differ. Instrumented Metav4 lead rules added **zero melon sales** in this
sample. Earlier harvest versus delivery was not separately measured.

## 3. F4 MODELPX / Step758 family

**Metav4 contains no MODELPX family** (`modelpx_apply=null`, no hours). Its
attributable realised MODELPX usage/revenue in these games is zero because the
mechanism is absent; this does not measure F4's benefit.

Step758 initially covers hours12–22, steps144–695, MILK/STRAWBERRY/WOOL.
The final F4 binding is `_s758_apply = _s804_apply`, hours **1–22**:

1. Infer rival supply from public inventory change + assumed preceding drain
   − our own sales. Clamp samples at zero, average the latest four.
2. Predict next inventory as `max(0, int(I + average + 6 - draw))`. The six
   units are a hypothetical supply scenario, not recovered rival shed stock.
3. Sell only if next model price < current model price − 0.5, current quote >1,
   available stock exists and there is no existing sale of that product.
4. Hours2–22: cap10 when quote>=100, or hours10–13 quote>=30; otherwise cap6
   at hours10–13 quote>=10; otherwise cap3.
5. Hour1 cap10: quote>=95 allowed; quote50–94 requires held stock>=3 **or**
   both other model-product quotes>=30; quote20–49 requires both other
   quotes>=30; quote<20 skips. Use live code's threshold20, not stale comment80.

The original forecast's drain approximation is **one at step%4=0 plus one
daily**, independent of actual shop product demand. The port uses actual
duplicate-aware product drains instead. It tracks consecutive turns rather
than collecting history only in eligible lead hours. Missing turns/restarts
reset history. Planned own sales are credited only when observed shed and
price-floor checks support them; projected worker DROP fills are unknown.
Rival flow remains an estimate, not hidden inventory reconstruction.

F4 prepends lead orders and reruns its global order optimiser. The module adds
only into free slots and reorders safe contiguous SELL blocks: it does not
displace purchases or borrow future tape stock.

## 4. Other price models and measured dollars

`_r37_market_price` reproduces the engine's marginal product curves.
`_r37_quote_priority` ranks sale quantities by **dollars lost if a rival lot
arrives first**, not headline quote times quantity:

`sum(P(I+j) - P(I+rival_lot+j), j=0..held_sale_quantity-1)`

Visible ripe output gives a hypothetical rival lot bounded8–24. Later OR2
tracks rival harvested-minus-inferred-sold stock, up to30. Some slot swaps
require $20 margin and tape debts. `_v44y`/F4 order-closure models also predict
specific clone actions. Those identity/tape-dependent mechanisms are excluded.

Four-game exact-engine, fixed-opponent same-step counterfactuals compare final
Metav4 orders with the inherited SELL rank captured before R37; non-sale
positions and quantities stay fixed. Difference: **+$27/game** (seed values
$90,$2,$16,$0), 22.5 changed turns/game. This measures the collective final
ordering versus inherited rank, **not isolated R37 causality**, a full-game
bank gain, or the standalone module's effect.

Metav4 `_v92_predict` uses a learned replay library to forecast supply/sales.
It added sales in the pilot; `_v92_predict2` added none. Learned assets and
opponent/library dependencies are excluded from the standalone module.

| Source hook | Tagged product-turns/game | Added requested units/game | Revenue of affected actual fills/game |
|---|---:|---:|---:|
| Reservation/RACE gate | 28.25 | 223.75 | **$20,795.00** |
| One-turn RACEPX lead | 16.00 | 56.25 | **$2,078.75** |
| Library forecast | 4.50 | 30.25 | **$3,034.75** |

These are **associated gross sale dollars, not incremental bank edge**.
Hooks tag positive order additions; final fills may mix with native sales or
other hooks. They can overlap and must not be added as profits. Reservation
includes $5,065.25/game wheat; its non-input affected revenue is $15,729.75.
One-turn lead is mostly wheat ($2,005.75), plus carrot ($73). Library forecast
is milk ($974.50), strawberry ($105.50), wool ($1,954.75). No melon in any.
Only the opening and ordering comparisons above have local cash
counterfactuals; other mechanisms have no identified causal $/game estimate.

## Module contract and checks

Call `market_orders(obs, planner_orders)` once per turn. Returns copied orders;
does not mutate the observation or planner book. Flags:

| Flag | Default |
|---|---|
| `ENABLE_WHEAT_ROUND_TRIP` | False |
| `ENABLE_PRICE_GATE_LEAD` | True |
| `ENABLE_MODEL_LEAD` | True |
| `ENABLE_EXPOSURE_ORDERING` | True |

Existing quantities, purchases, placeholders and purchase barriers are
preserved. Existing full ten-slot books gain no orders. Reordering applies to
contiguous distinct-product SELL blocks, protecting products bought that turn.
New sales use observed shed only; no worker-drop/harvest assumptions. Invalid
order shapes/items/counts or books over ten slots raise ValueError. Missing
market data abstains. Default timing/caps assume 24-hour days, 720-turn season,
100-item shed and ten market slots; price parameters can come from observation.
History is small per-seat in-memory state; interleaved games in one process
need separate module instances. For ablations, set flags before running.

**16 unit tests passed**, including 82 price comparisons against the installed
engine, duplicate drains, hour1 tiers, floor/stock bounds, history resets,
input preservation, ten slots, duplicate sales, placeholders and optional
opening funding. The four instrumentation games completed with exact ledgers.

Reproduce checks / rebuild tables (no gameplay):

```powershell
python -m unittest discover -s evaluation/market_module -p test_market.py
python evaluation/market_module/analyze.py
```

Reproduce the bounded pilot, only if new games are explicitly wanted:

```powershell
python evaluation/market_module/measure.py --seeds 8301 8302 8303 8304 --workers 2
```

`measure.py` limits invocations to four seeds in8301–8400 and workers1–2.
`audit.py --f4-source <path>` pins live source state using an initial observation
only. Derived tables, fills and pinned summaries live in
`evaluation/market_module/`; raw replay data and local Graphify outputs are
not deliverables. Claude should integrate and test components separately;
the above-base gate assumes sale intent and could override planner price holds.

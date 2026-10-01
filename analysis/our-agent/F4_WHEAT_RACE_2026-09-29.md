# F4 wheat round-trip race

Date: 2026-09-29. Status: **PASS on the specified paired gate**. No promotion or submission.

## Engine and parent trace

The Kaggle 1.32.7 market quotes both players against the same pre-commit
inventory for each unit in a market-order slot. `BUY_PRODUCT WHEAT` quotes at
inventory minus one. A later `SELL WHEAT` order in the *same turn* therefore
sees the inventory reduction from both players' buys. Being player 1 rather
than player 2 does not win a same-slot quote; moving the sell into the first
lifted-price slot does.

`evaluation/f4_wheat/trace_reproduce.py` runs the real engine on seed 6827,
loads the F4+counter through `get_last_callable`, replays every observed state
through that same loader, and asserts all **719** issued actions match the
recorded engine actions. The compact layer trace is `trace_6827.json`:

| Step | Tape / parent | Relevant layer |
|---|---|---|
| 327 | tape and final both `BUY_PRODUCT WHEAT 63` | `Chassis.act` |
| 328 | tape has no wheat order; final `SELL WHEAT 72` | `_r36_reserve` advances the future tape sale |
| 329 | tape `SELL WHEAT 63`; final no sale | existing suppression pays the R36 debt |

Other parent layers matter to the full chain. `_r95_replenish` may trim a wheat
buy on days 10–11 to protect the feed reserve; a later queue compactor drops
zero-quantity orders. `step752_guarded_same_side_market_compact_agent` merges
adjacent wheat buys, `_ORDER_PARENT` / `_OR2` move market slots, and the F4
fixed-sell closures can reorder sales. The appended overlay reads the **final**
parent order, not an intermediate wrapper result. A diagnostic attempt to wrap
an earlier callable was rejected because it could perturb the chain; the
real-replay equality assertion is the trace guard.

The older `LADDER_F1_2026-09-27.md` simplifies episode 113883512: its raw replay
shows our F1+counter sold **40 wheat at step 328 and 23 at 329**, not only 23
at 329. The fork sold 70 at 328. That historical example motivated the race;
it is not a F4 performance test.

## Overlay

`agents/ours/h1-counter-f4-wheat-candidate/main.py` is the exact F4+counter
source byte prefix plus one appended layer; its Apache notices are copied
unchanged and the Kaggle loader selects the final `agent`. The layer:

1. Requires F4's existing mirror-family detection, a positive current wheat
   buy, no current wheat sell, and a free market-order slot.
2. Finds an unsold tape wheat sale within ten turns, stopping at an intervening
   wheat pickup or buy. It never changes the tape's worker commands or wheat
   buy quantity; a reserve-trimmed buy is **not** blindly restored.
3. Checks shed capacity, then models the current order lockstep and the next
   mirrored sale with the engine's price curve and known town/shop wheat drain.
   It abstains if its own modeled sale revenue falls or the relative edge is
   below one coin.
4. Appends `SELL WHEAT` after the buy and records an `r36_debts` entry for the
   original tape-sale step, so the existing parent suppression cannot sell
   those units twice.

`evaluation/f4_wheat/mechanism_6827.py` independently plays the *candidate*
against its parent through the engine. In that game both buy 63 at step 327,
but the candidate sells 63 immediately. At step 328 it sells 9 while the
parent sells 72; at 329 neither sells. The candidate's bank lead grows from
$425 before step 327 to $568 before step 329, then to $7,394 at game end.
The first $143 is the local race effect; the larger final difference includes
downstream policy and market responses. `mechanism_6827.json` contains only the
three-step state/action summary.

## Paired evaluation

All performance screens use seeds **6801–6880 only**, both seats, 40 seeds × 2
= 80 games per cell. `6801–6840` was exploratory; the capacity-guarded final
bytes use fresh `6841–6880` for the gate. Every candidate arm has an identical
seed/seat parent arm. `evaluation/f4_wheat/compare.py` checks the keys and
prints win changes plus paired margin changes. A previously used seed 5901
was inspected during mechanism prototyping; it was not a selection screen and
is not used in the committed performance evidence.

Exploratory F4+counter cell: 36–4–40 vs the parent's 4–4–72, +32 paired wins,
zero paired margin declines, +$428.82 mean paired margin. This is **not** the
final version's gate because the shed-cap guard was added afterward.

Final candidate vs parent, `6841–6880`:

| Opponent | Candidate W–L–T | Parent W–L–T | Gained / lost wins | Mean paired margin gain |
|---|---:|---:|---:|---:|
| F4+counter | **48–0–32** | 0–0–80 | **48 / 0** | +$301.27 |
| F4 | **78–0–2** | 76–0–4 | **2 / 0** | +$301.27 |
| F1 | 66–14–0 | 66–14–0 | 0 / 0 | $0 |
| Metav4 | 74–6–0 | 74–6–0 | 0 / 0 | $0 |
| More Wheat | 76–4–0 | 76–4–0 | 0 / 0 | $0 |
| F2 (herd-safe-v3) | **70–10–0** | 68–12–0 | **2 / 0** | +$48.70 |
| Farming Score | 76–4–0 | 76–4–0 | 0 / 0 | $0 |

F1, Metav4, More Wheat and Farming Score are **exactly identical** in all 80 paired final
margins, not just equal aggregate wins. F2 improves ten paired margins and
leaves the other 70 unchanged; no paired margin declines. F2 is the 25 Sept notebook
extraction `herd-safe-v3-experimental-risk-aware-feed/main.py`, SHA256
`4f8637a3e33348b98f531de246d353f5d2955b2f85480e3fd02bf4a7874f0d01`;
the screen uses an ignored local `.cache/nb25/` copy, not a committed public
agent. The winner is determined from final bank; `screen.py`'s incomplete
sale-attribution rows do not affect the win counts.

## Verdict and boundary

**PASS:** 48 new wins and no lost wins against F4+counter; two new wins and no
lost wins against F4. No tested guard loses wins. The overlay is a measured counter to
F4-family near-ties, not a general wheat-arbitrage policy or a claim that it
detects every unseen ladder fork. The mirror model is a selection heuristic;
its guarantees are limited to the tested opponent panel and standard engine
configuration.

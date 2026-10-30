# Market model groundwork — history and timing without changing the worker model

**Build a separate, small market model with a full causal history; keep the existing worker encoder and arrays.** Current features already contain prices, market stock, dawn/high/low summaries and a four-hour price change. The missing inputs are the detailed recent trajectory, explicit shop phase, and a carefully labelled public pressure proxy—not exact opponent sales, which are unavailable at play time.

The calibrated head's 76.44% precision rises to 89.77% with permissive ±2-turn matching, but distinct one-to-one retiming repairs only 11.01% of its remaining presence errors under the conservative matching rule below. Proximity is substantial; it is not a measured revenue gain. This is analysis-only groundwork: no model was trained, no new feature dataset was built, and no policy games were started by these probes.

## What the 121 global features actually contain

The authoritative implementation is [board_features.py](../src/kagml/board_features.py), declarations at lines 30–35 and encoding at lines 184–203. [The feature contract](BOARD_FEATURES.md) and [the indexed probe output](MARKET_MODEL_DESIGN_CHECKS.json) agree.

| Information | Exact global indices | Present / missing |
| --- | --- | --- |
| Day/hour and end clocks | 0–4 | Current `day`, `hour`, game/day time left. Shop phase is inferable from hour; no explicit modulo-four feature. |
| Money | 5–7 | Our bank, opponent bank, gap. These do not identify the opponent's sales. |
| Our shed | 11, 16–27 | Total and all 12 item counts. Seed stock is 28–32. Carried inventory is in unit features, not these globals. |
| Current sale price | 33+8k, k=0…8 | All nine products. |
| Shared market inventory | 34+8k | All nine public product stocks; this is already present. |
| Price history summaries | 35+8k to 38+8k | Dawn, high today, low today and four-turn price change. No raw last-24 sequence or one/two-turn slopes. |
| Relative price and demand | 39+8k, 40+8k | Price/base and current daily demand for each product. |
| Opponent farm summary | 105–112 | Five crop counts and three animal counts; no recent sale series or visible product-yield totals. |
| Shops | 113–120 | Counts of eight shop types, including duplicates. No explicit next-purchase clock. |

Indices 33–104 are 72 market features: nine products × eight columns. [History](../src/kagml/work_features.py) already stores public prices/inventory and our issued sale memory; `board_features.History` inherits it, but globals export only the summaries above. Its own-sale memory is an issued-order proxy, not executed fills; the current dictionary construction can also overwrite duplicate same-product SELL entries. Treat the existing window residual as a proxy rather than an exact opponent-sale reconstruction.

Useful additions: the last 24 physical turns of public prices/stocks and their changes, our own aggregated issued orders, explicit shop phase/time to next consumption, our carried stock, public opponent held yield, and an uncertainty flag where inventory changes cannot identify supply. Own crop/animal production timing is already available in tile features; a standalone model should retain a small pooled forecast rather than discard it. The clock measurements below support including phase and deadlines; they do not prove the teacher's entire decision rule.

## Can recorded data supply history without new games?

**Yes for prices and recorded offline sales, with parent-prefix reconstruction.** Raw replays have both action streams and public market snapshots. Existing per-source `market_steps` tables contain prices/inventories by physical step; `sales` tables contain executed units by seat/product/order/price. The sample analysis episode 1031506 has both tables under `datasets/ownfarm/`. All 25 market snapshots matched its raw replay prices and stocks exactly; its recorded opponent sold 25 units.

Do not assume all data is in the original `datasets/d1` root. [build_turn_dataset.py](../tools/build_turn_dataset.py) maps each source to its own table root and parent lineage. The sample is absent from d1 but present in ownfarm. No replay of the engine or policy is needed to read existing snapshots/sales.

For a feature at step t, use pre-action market state t and only completed orders from steps <t. In these recordings the action stored in the next frame is the action taken at the current step; confusing the two leaks the target. A teacher takeover needs the unchanged parent prefix before the fork and then that segment's own history. Warm the preceding 24 turns across days; do not reset at dawn or silently pad every fragment as if it were game start. Use a validity mask only for genuinely unavailable history. Align sidecars by episode, seat and physical step.

**Exact recorded opponent fills must not be a deployed input.** They can be recovered offline from sales tables, but live observations hide the opponent's private stock and actions. Inventory deltas mix both players, town consumption, purchases and floor-price behavior. Use observable net stock drift/pressure plus uncertainty flags; exact opponent sales can be an offline diagnostic or auxiliary target. A model trained with true opponent-sales inputs would have a serving mismatch.

### Measured cost, not a bulk run

A short probe on one 24-turn analysis segment measured:
- Gzip read/JSON decode: median 15.15 ms; two Parquet tables: 6.01 ms.
- Rolling 24-turn window construction: 2.05 microseconds/turn.
- Straight 440k-turn core projections: 1.85 minutes via cached tables, 4.65 via gzip. These exclude parent-prefix retrieval, cold-disk effects, validation and output writes.

Use **10–20 minutes as a provisional single-process build budget** with cached parent histories and batched output, then profile a representative source mix. That is a planning allowance, not a measured full-build time. The pinned manifest currently has 373,315 TRAIN turns in 20,799 segments; 440k is the requested sizing assumption. Smaller correction fragments and full-game sources have different file overhead.

The proposed full inputs occupy 2.20 GB at raw float32 for 440k turns; reusing the existing 121 globals lowers the incremental sidecar to 1.99 GB before compression. A normalized float16 representation could halve this, but raw cash must remain float32: it exceeds float16's finite range. Do not rewrite existing worker arrays. The probe checked padding/causality, sample table parity and shapes; complete parent-prefix coverage is not yet audited.

## Proposed model and training

A market-only model can be **87,284 parameters**, about 0.35 MB of float32 weights:
- Temporal input: 24 × 46. Per product: price, market stock, our issued-sale quantity, public stock drift, ambiguity flag (9 × 5), plus a shared validity mask.
- Current input: 148 = existing globals 121 + carried items 12 + shop-phase one-hot 4 + deadline flags 2 + public opponent held yield 9.
- Shared temporal GRU(46→64), current MLP(148→64), concatenate, MLP(128→128), output 28 × 11 quantity logits. Pool our near-term production into current features in a later measured variant; that would change the 148-input size.
- Use the existing 28-token order vocabulary and 11 quantity classes, ordinary cross-entropy with **non-zero weight 1**, then per-token calibration on a separate calibration split. Preserve the seven unsupported BUY_PRODUCT tokens as forced no-order at deployment. Quantized quantity representatives remain an additional source of unit-count error.

An untrained shape/parameter probe measured 1.44 ms per single CPU inference, one thread. This is a small synthetic forward benchmark, excluding feature extraction and decoding, not a live latency guarantee.

Use training-source rows only; group every source/correction descendant of a parent seed into the same split. Keep the existing analysis families for diagnostic/model-selection reporting, and reserve disjoint parent families (for example the established analysis2 families) for calibration before live testing. Fit scaling on TRAIN only. The present calibrated P5 diagnostic reuses the analysis split on which its bias was fitted, so it is not a fresh generalization estimate. Never train/tune on 20001–20048 or read 10320–10324. No training is authorized by this groundwork report.

### NetPlayer integration proposal

An opt-in `mkt=<model>` would load the market-only weights and a 24-turn observation buffer without replacing the worker network. In the existing call flow, replace only the `_market_orders(n)` result after worker decoding; retain current token ordering, the 10-order cap, quantity mapping, hire cap and engine/budget/inventory checks. Use that market model's own calibration, not the board-p5 calibration a second time.

Keep the existing post-order filters, especially overflow and endmask. Endwork remains in worker legality/decoding as before; a separate market head must not bypass it. The buffer advances once for every real observation, including days outside the network window; reset it only for a new game and preserve it in memory/restore. Day-29 template behavior remains unchanged unless separately authorized. No `src/kagml` integration was made; the fresh-seed game sources remain frozen.

## How much remaining error is timing?

We evaluated all **37,735 analysis turns in 2,590 segments**, using the unchanged P5 board encoding and FP32 CUDA market logits; the full diagnostic took 100.5 seconds. Raw and already-calibrated predictions use identical teacher states. No fitting, test contents, evaluation arrays or policy calls.

| Head | Exact precision / recall | Precision within ±1 / ±2 | One-to-one residual repair ±1 / ±2 |
| --- | --- | --- | --- |
| P5 raw | 68.03% / 84.17% | 81.39% / 85.78% | 5.77% / 9.39% |
| P5 calibrated | 76.44% / 76.39% | 86.69% / 89.77% | 6.62% / 11.01% |

The permissive precision accepts any same-token teacher event within the window, even when many predictions reuse one teacher event. After calibration, **56.57% of exact false positives** have a teacher event within ±2 turns (43.52% within ±1). This reproduces the broad “roughly half are near a teacher order” observation.

The stricter test locks exact matches, then finds one-to-one pairs among residual false positives/negatives within each window. Calibrated totals are 23,757 predicted order events, 23,770 teacher events, 18,159 exact overlaps, 5,598 false positives and 5,611 false negatives. Only 371 additional distinct pairs match at ±1 and 617 at ±2: 6.62% / 11.01% of residual mismatch cells can be paired this way.

This is a conservative within-fragment diagnostic, not a causal fraction of recoverable revenue. Windows never cross a fragment/fork or missing observation; locking exact matches can exclude other possible reassignment. Interior-only permissive ±2 precision is 89.75%, close to the 89.77% all-row result. These checks avoid using an unobserved neighboring fragment.

For SELL tokens alone, calibrated precision/recall are 77.86%/77.77%; one-to-one residual repair is 5.33%/9.31% at ±1/±2. If a match must also preserve the non-zero **quantity class**, overall one-to-one residual repair falls to 5.22%/7.96%. Matching counts does not resolve quantity mistakes.

### Teacher selling and the shop clock

| Step mod 4 | Observed turns | Teacher SELL token events | Events / observed turn |
| --- | ---: | ---: | ---: |
| 0 | 9,440 | 2,144 | 0.227 |
| 1 | 9,440 | 5,785 | 0.613 |
| 2 | 9,440 | 4,691 | 0.497 |
| 3 | 9,415 | 3,365 | 0.357 |

Phase 1 contains 36.19% of teacher SELL events on about one quarter of observed turns, consistent with selling after the shop consumption tick. It is not an exclusive schedule: most SELL events occur on other phases. These are issued SELL-token events, not executed units or revenue.

| Hour | Observed turns | Teacher SELL token events | Events / observed turn |
| --- | ---: | ---: | ---: |
| 20 | 2,590 | 542 | 0.209 |
| 21 | 2,590 | 1,766 | 0.682 |
| 22 | 2,590 | 2,723 | 1.051 |
| 23 | 2,565 | 1,995 | 0.778 |

The late-day pattern remains after dividing by observed-turn exposure; multiple products can produce more than one event per turn. Hour 22 is stronger than hour 23 in this sample. Phase and deadline features are justified candidates, but these observational rates do not establish that forcing sales onto a clock tick improves profit; the earlier fixed-clock selling rule already failed a live test.

## Evidence and reproducibility

[Timing counts](MARKET_MODEL_TIMING_CHECKS.json), [feature inventory and cost probe](MARKET_MODEL_DESIGN_CHECKS.json), [diagnostic](../tools/market_model_diagnostics.py), [history/model probe](../tools/market_model_history_probe.py). The diagnostic includes five matching edge-case checks; both probes are read-only and start no games.

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
python tools/market_model_diagnostics.py --self-test
python tools/market_model_diagnostics.py --max-seconds 300 --output reports/MARKET_MODEL_TIMING_CHECKS.json
python tools/market_model_history_probe.py
```

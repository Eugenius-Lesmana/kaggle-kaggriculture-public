# L2 shadow-label schema and use

The player acts on our seat (0) for one day from each el3 morning; seat 1 replays its recorded commands. The fourth-place teacher observes the same actual player trajectory on a separate deep copy every turn. Its answer is recorded, never substituted for the player action. Both actors reset at each independent segment; template/model memory is warmed from recorded observations exactly as in compare_day, with model price history and cleared worker targets.

## Run

```powershell
python tools/shadow_labels.py --player fourth --smoke --workers 2
python tools/check_shadow.py --player fourth --smoke --workers 2
python tools/shadow_labels.py --player template --smoke --workers 2
python tools/check_shadow.py --player template --smoke --workers 2
python tools/shadow_labels.py --player model:ranker-v1 --smoke --workers 2
python tools/check_shadow.py --player model:ranker-v1 --smoke --workers 2
python tools/shadow_labels.py --player template --workers 2
python tools/check_shadow.py --player template --workers 2
```

Full generation requires passing current-code fourth and selected-player smoke builds on unchanged source files. At most two worker processes; independent checks are run after the generator, never alongside its pool. No policy or vendor edits. Any inference exception, malformed answer or diagnostics failure rejects a segment; there is no replacement PASS. Resume requires matching source/dependency signatures and compressed replay plus every Parquet shard SHA256. Partial output is unpublished until the audit receipt succeeds. Final validation recomputes all six native tables and every label join.

Names `template`, `fourth`, and `model:<model name>` use compare_day's player interface; the self-shadow player is a separate Opponent instance because load('fourth') is cached. Model folder/manifest slugs replace ':' with '-' (e.g. `model-ranker-v1`). Split by ORIGINAL GAME when training, including parent/sibling recordings; synthetic episode IDs do not create independent games.

## Paths and grain

All large outputs live below the configured data root (`<data>`).

- `raw/shadow/<player>/<game>-d<day>.json.gz`: `env.toJSON()` with placeholder history removed: 25 frames, original morning plus 24 actual transitions. Original `info.seed` preserved; `shadow` adds player/teacher/source provenance. Teacher answers are separate tables. ACTIVE endpoint banks are intermediate outcomes.
- `datasets/shadow/<player>/<table>/<episode>.parquet`: Zstandard Arrow tables. `episode = int(game)*100+day`, independently namespaced per player folder. D1 table schemas and absolute steps are unchanged.
- `datasets/shadow/<player>/audit/<episode>.json`: source and output hashes, dependency signature, row counts, diagnostics, timing and label counts. `reason=kept` marks acceptance.
- `runs/shadow/<player>/`: smoke/full build receipts, independent validation, benchmark comparisons and memory analysis. Logs stay on D:.
- Tracked `manifests/shadow-<player>.csv`: same fields as L1 (`game,day,seat,file,sha256,end_cash_0,end_cash_1,episode,seed,start_step,end_step`). Smoke contains three rows; full replaces this atomically with 552.

`step=s` describes the pre-decision state at absolute step s; executed actions are at replay-local frame `s-start_step+1`, observations at frame `s-start_step`. Teacher label positions are from that SAME pre-decision observation. Seeds/market orders are processed in native engine order; this tool does not infer positions after a hire or execute shadow purchases.

| Table | Primary key | Additional fields |
|---|---|---|
| `teacher_turns` | episode, step | `action`: complete teacher action as JSON; `milliseconds`: wall time for teacher call plus answer copy |
| `teacher_actions` | episode, step, unit | `seat=0`, `x,y`: actual unit position, `exists`, `command`: teacher unit command JSON, `job`: JSON `[kind,cell]` from work_data.job_of or NULL, `job_legal`: membership in work_data.candidates |
| `teacher_market_orders` | episode, step, order_index | `command`: every proposed market order JSON, preserving order and quantities, including any capped/ineffective proposal |
| six D1 tables | unchanged | `games`, `market_steps`, `farm_daily`, `unit_actions`, `sales`, `market_orders` for what ACTUALLY played, BOTH seats |

`unit=0` is the farmer; hands start at 1 and reset daily. Every existing unit has a label each turn: omitted teacher hand commands are explicit PASS. Extra commands for nonexistent units retain NULL position, exists=false, job=NULL and job_legal=false. Moves and PASS have job=NULL and job_legal=NULL; do not put them in the mapped-job legality denominator. A mapped job's cell is an integer tile index or the string SHED, preserved in JSON.

**Legality means the existing candidate-job definition**, which includes jobs feasible after fetching supplies from the shed. It is not proof of immediate native execution, requested-quantity validity, coordinated shared-resource validity, optimality or a next-job routing label. D1 took_effect describes only actual player/opponent actions. Teacher orders are labels, never successful sales. Local submission/team/rating fields are -1; the date is empty.

## Memory limitation

Unmodified teacher memory stores its previous proposed action and combines that with the next ACTUAL observation for flow accounting. That action may not have executed. Current legality still uses the current actual observation; flow features can retain counterfactual assumptions. Market rate-gate and land accumulators are relevant only if enabled; the memory audit records the loaded configuration. These are raw stateful shadow labels, not a teacher with corrected memory. No memory is silently rewritten to the player's executed action. Inspect the dated handoff and memory audit for measured disagreement; high candidate legality alone does not prove the hidden features are accurate.

Teacher code/weights remain on D:, not copied into this repository. Fourth-place model licence is CC BY 4.0; preserve its notices and credit in downstream write-ups.


## Explicit compatibility event (approved 2026-10-23)

The raw full attempt rejects game 10319/day25 when the teacher's optional night_room_value helper tries to price a sheep. The approved retry is `python tools/retry_shadow_compat.py`; it wraps only that helper, preserves its pre-helper model/decoder action on the precise unpriced-animal KeyError, and records the omitted optional sales adjustment. No price or worker command is invented, and other errors propagate. Teacher sources, weights, shared loader and the other 551 outputs are unchanged.

`datasets/shadow/template/teacher_compatibility/1031925.parquet` is a sparse provenance companion, keyed by episode/step. Columns: helper, original_error, teacher_pre_helper_action (full action JSON), returned_action (full action JSON), our_action. LEFT JOIN it to labels on (episode,step). Only episode 1031925, step 623 is marked. It is an explicit helper bypass; do not call the entire corpus fully unmodified. For strict raw-teacher analysis exclude this turn or segment. The returned action equals the pre-helper teacher action; the original teacher's final answer is unavailable because it crashed.

The replay shadow.compatibility marker, audit compatibility.events, source hashes and per-segment effective signature provide the same distinction. The original failed run is retained as runs/shadow/template/unmodified-full.json; the completed full.json lists the one repair and all other original signatures. The checker validates the companion event and exact 551-output preservation evidence. Raw-generator resume does not silently reuse a differently signed adapted segment; use the explicit retry tool to reseal that segment. `python tools/test_shadow_compat.py` checks the guard boundaries.

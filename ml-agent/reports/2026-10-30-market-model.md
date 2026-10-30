# Market model — 2026-10-30

**Do not replace P5’s market head. The trained market model shows a clear analysis regression; live games were skipped as required.**


Exact F1 fell from **74.63% to 61.74%**; ±2-turn F1 fell from **77.00% to 66.51%**. Aggregate token-unit error improved slightly, but that does not offset the missed-order regression.

The current P5 baseline remains `net:board-p5:market:overflow:endmask:endwork`. No board-p6 combination was tested.

## Build and training

Full causal history build `market-v1` completed in about 2h27m (01:50–04:17 UTC); all selected TRAIN/analysis/analysis2 rows are represented. Test and endval rows were excluded before opening arrays. Existing worker/market arrays were hash-checked and not rewritten. No true opponent sales, opponent private stock, step-t action or future observations are model inputs.

| Split | Segments | Turns | Parent seed families |
| --- | ---: | ---: | ---: |
| train | 26,649 | 439,825 | 107 |
| analysis | 2,590 | 37,735 | 5 |
| analysis2 | 1,350 | 32,355 | 15 |

The 90,932-parameter GRU/MLP uses 24×65 causal history and 148 current features. Four CUDA epochs, AdamW lr2e-4, batch option 128, non-zero weight 1. Batches stay within each segment, so most are smaller than 128. Scaling/fitting use TRAIN only; lowest analysis cross-entropy chooses the checkpoint; count calibration uses analysis2 only and is bound to the checkpoint SHA. Seed families are disjoint across these splits.

| Epoch | Analysis CE | Raw event precision | Raw event recall |
| --- | ---: | ---: | ---: |
| 1 | 0.069307 | 78.36% | 17.73% |
| 2 | 0.061980 | 76.23% | 37.04% |
| 3 | 0.059078 | 79.12% | 39.39% |
| 4 | 0.057151 | 80.06% | 42.36% |

The GPU was checked with `nvidia-smi` and the trainer process list before training; Claude’s `train_board_net.py` blocks startup. Exact-input epoch recovery preserves completed epochs and refuses changed manifests/code/options. The completed build was retained through a launcher repair: Windows PowerShell lacked `Get-FileHash`; all old owned processes had exited and all 22 pins were unchanged before restarting the same scripts with bundled PowerShell. Training waited for Claude and ran 05:21–06:26 UTC, including TRAIN scaling and calibration. Logs: `.cache/market-train/training.stdout.log`, `gpu-before-training.log`, and `training-supervisor.stderr.log` (the recovered launch failure).

## Teacher-state analysis comparison

All 2,590 analysis segments / 37,735 turns were scored. Main comparison below restricts decisions to NN days 6–28. Complete-analysis figures and all 28 token totals are in the [checks](MARKET_TRAIN_ANALYSIS_CHECKS.json) and [token CSV](market-train-analysis-tokens.csv). P5 is its original market head, without mcal. GRU raw and analysis2-calibrated outputs are both shown.

| Model | Exact precision | Exact recall | ±2 precision | ±2 recall | Total normalized absolute token-unit error |
| --- | ---: | ---: | ---: | ---: | ---: |
| board-p5 | 67.25% | 83.83% | 69.39% | 86.49% | 0.194 |
| market-gru-v1-raw | 79.64% | 41.61% | 84.67% | 44.24% | 0.512 |
| market-gru-v1 | 63.72% | 59.88% | 68.64% | 64.50% | 0.173 |

Exact means the same token is positive on the same turn; it does not require the same quantity class. The ±2 score locks exact matches, then matches remaining predicted/teacher events one-to-one within two turns of the same contiguous segment; it never reuses a teacher event. Forks/boundaries are not joined. Quantity-class hits are reported separately in the CSV.

Unit totals use the shared QTY_PLAY representatives before availability, hire cap, ten-order truncation and overflow/endmask. They measure head over-ordering potential, not executed sales or profit. BUY_LAND’s runtime decoder emits one order for any positive class.

| Token, days 6–28 | Teacher units | P5 head units | Calibrated GRU units | P5 / teacher | GRU / teacher |
| --- | ---: | ---: | ---: | ---: | ---: |
| SELL:WOOL | 5,262 | 6,685 | 4,080 | 1.270 | 0.775 |
| BUY_SEED:WHEAT | 4,062 | 5,485 | 2,675 | 1.350 | 0.659 |
| BUY_SEED:TOMATO | 564 | 831 | 559 | 1.473 | 0.991 |
| BUY_ANIMAL:GOOSE | 303 | 408 | 307 | 1.347 | 1.013 |
| BUY_ANIMAL:SHEEP | 208 | 295 | 223 | 1.418 | 1.072 |
| BUY_LAND | 124 | 151 | 105 | 1.218 | 0.847 |

## Predeclared analysis gate

[Criteria](MARKET_TRAIN_ANALYSIS_GATE.json) were fixed before training/results: reject a decline greater than 2 percentage points in exact or ±2 F1, an increase greater than 0.10 in total normalized absolute token-unit error, or more than 0.25 additional absolute unit-ratio error in any of the six focus tokens with at least 20 teacher units. No parameters or calibration were tuned on evaluation seeds.

Gate: **failed**.
- exact_f1 drops more than 0.02
- within2_f1 drops more than 0.02

This is analysis-based checkpoint selection and a repeated validation comparison, not an untouched generalization test. Label matching on recorded teacher farms does not establish live bank gain; production, availability and opponent reactions can change.

## Conditional live evaluation

No policy games were started. Task2 was skipped because the analysis gate failed. There is no live or pooled keep claim.

## Reproducibility and boundaries

Exact commands:

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python tools/build_market_history.py --full --splits train,analysis,analysis2 --tag market-v1 --manifest manifests/market-history.csv
python tools/train_market_net.py market-gru-v1 --manifest manifests/market-history.csv --epochs 4 --lr 2e-4 --batch 128 --require-cuda --resume
python tools/compare_market_model.py
python tools/market_train_live.py
```

The live runner refuses to start games after a failed analysis gate and implements the fixed fresh-stage/pooled conditions. Supporting [final verification](MARKET_TRAIN_FINAL_CHECKS.json), [live checks](MARKET_TRAIN_LIVE_CHECKS.json), [history manifest](../manifests/market-history.csv), [comparison code](../tools/compare_market_model.py). Weights/calibration remain on D: in `models/market-gru-v1`; no model arrays/raw games/caches are committed.

New branch `dev/eugene-codex-market-train-20261030` from master `1f85c4007a512c403bc25a6a5c880e1159dc8a2c`. Main working copy, master source and other worktrees were not edited. Seeds 20001–20048 evaluation-only; no training/tuning on them; no test 10320–10324 contents, pushes, submissions or attribution lines.

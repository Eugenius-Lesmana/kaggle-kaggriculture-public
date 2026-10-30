# Market pipeline â€” small prototype ready for tomorrow's full run

**Built the causal sidecar builder, independent GRU/MLP trainer and opt-in `mkt=<model>` path in this worktree.** Five analysis segments (84 turns) passed causal/reference tests. Three tiny forward/backward batches passed with zero optimizer steps on recorded data and unchanged weights. No full sidecar build or real training was run.

**Default play hash passed:** `6a665ffecd0ce844a4037018fdb1117e459a61e328822283d4d37c71a97dc6fd`. The single replay started only after swap completion and controller exit, and used 179.89s CPU.

## What is implemented

- [build_market_history.py](../tools/build_market_history.py): parent-prefix warm-up, physical-step joins, float32 history/extra sidecars, source hashes and unchanged worker/market arrays. Default builds at most five analysis segments; a full build requires explicit `--full`. Parent/fork state mismatches fail instead of substituting another farm.
- [market_net.py](../src/kagml/market_net.py): a shared causal history implementation for offline encoding and live play, plus the separate market network. It uses public market snapshots and our own past issued orders only.
- [train_market_net.py](../tools/train_market_net.py): unweighted quantity cross-entropy (non-zero weight 1), TRAIN-only scaling/fitting, checkpoint selection on analysis, and count-bias calibration on analysis2 only. Parent families must be disjoint across splits. Existing model directories are never overwritten. Calibration records achieved counts and tie error and is bound to the selected checkpoint hash.
- [NetPlayer opt-in](../src/kagml/net_player.py): `mkt=<model>` changes only the market logits used by the existing decoder. It preserves token order, quantity classes, hire cap and ten-order cap. Unsupported BUY_PRODUCT tokens are forced to no-order. Existing overflow/endmask filters and endwork legality remain in place. The market buffer advances even outside the NN day window; memory/restore includes it and the previous actual action. Day 29 remains the template path. Combining board-head `mcal` with `mkt=` is rejected to avoid applying the wrong calibration.

The history is **24Ã—65**, rather than the earlier design's 24Ã—46: it includes all 28 own order tokens, not only the nine SELL quantities. Each completed interval contains 9 prices, 9 public stocks, 28 own issued-order counts, 9 stock deltas, 9 censor/own-buy flags and a validity mask. At step t the most recent row describes interval tâˆ’1; no step-t action or future observation enters it. Duplicate own orders are summed. Stock drift remains a public proxy, never exact opponent sales.

Current input is 148: the existing 121 globals plus 12 carried-item totals, 4 shop-phase indicators, 2 deadline flags and 9 public opponent-held product totals. The 64-wide GRU/MLP has **90,932 parameters** and outputs 28Ã—11 quantity logits with the existing quantity vocabulary. All raw numerical data remain float32; cash is not cast to float16. At 440k turns, the incremental raw sidecar is about 2.79 GB before compression when reusing the existing 121 globals.

## What was tested tonight

Exactly five unique analysis segments were built: l1, l1-edge, l3-edge, l3-net1, l3-net2. They include a day 0 start, a warmed day 6 start and H12 fork prefixes. They were reused for the tests; no further segment dataset was built.

The 6 pipeline checks cover:
- independent reconstruction of each tested history from recorded public snapshots and our own action stream;
- changing the step-t action and later actions/observations leaves step-t and earlier features unchanged;
- changing opponent actions/private stock leaves every feature unchanged;
- exact warm-up/validity masks across parent/segment boundaries, unchanged existing worker and market-label hashes, duplicate-order aggregation and model shapes;
- TRAIN-only scaling and analysis2-only calibration guards, calibration/checkpoint binding, and a checkpoint round trip;
- opt-in versus default loading, marketâ†’overflowâ†’endmask ordering, endwork flag/legality path, outside-window history advancement and memory/restore;
- one synthetic-tensor optimizer update, separate from recorded data. The recorded-data smoke uses backward passes only and verifies every parameter/buffer remains unchanged.

The trainer smoke processed 3 tiny batches on cuda in 0.93s including its checks. It does not save a deployable model. All 15 currently declared sources have an existing first-example parent path by metadata checks; only the five selected analysis segments were encoded/causally tested. Full source coverage and full training quality remain tomorrow's work.

## Tomorrow's explicit commands

Run these from this worktree only after the swap load has cleared and full work is authorized:

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
$env:OMP_NUM_THREADS='1'
$env:MKL_NUM_THREADS='1'
python tools/build_market_history.py --full --splits train,analysis,analysis2 --tag market-v1 --manifest manifests/market-history.csv
if ($LASTEXITCODE -ne 0) { throw 'History build failed' }
python tools/train_market_net.py market-gru-v1 --manifest manifests/market-history.csv --epochs 4 --lr 2e-4 --batch 128 --require-cuda
```

The builder is single-process, read-only toward original arrays, parent-locality sorted and resumable through exact existing-sidecar comparisons. Allow **10â€“30min** for the full build, based on the prior cached-read estimate plus parent/writing/65-channel overhead. Allow **10â€“30min** for four GPU epochs and calibration initially. These are planning ranges, not measured full runs; the tiny smoke cannot establish full-dataset I/O throughput. Recheck source coverage and family separation before fitting. A full train/calibration split shortage or overlap fails explicitly.

After training, the prototype player string is:
`net:board-p5:market:overflow:endmask:endwork:mkt=market-gru-v1`.
No live comparison or submission is authorized by this prep handoff. A trained model must still be evaluated separately; this report claims pipeline mechanics only.

Reproduce the small checks without full work:

```powershell
python tools/build_market_history.py --splits analysis --limit 5 --diverse --tag prep-20261029-smoke --manifest .cache/prep/market-history-smoke.csv
python tools/test_market_pipeline.py
python tools/train_market_net.py prep-smoke --manifest .cache/prep/market-history-smoke.csv --smoke --smoke-batches 3 --require-cuda
```

## Evidence and boundaries

[Pipeline checks](MARKET_PIPELINE_CHECKS.json), [default-play proof](PREP_DEFAULT_PLAY_CHECK.json), [worker diagnostic](2026-10-29-p5-worker-errors.md). The tiny trainer proof and smoke manifest are under this worktree's ignored `.cache/prep/`; sidecars are on D: under `datasets/market-history/prep-20261029-smoke/`. No model weights, arrays, raw recordings or caches are staged.

Branch `dev/eugene-codex-prep-20261029`, exact base `9fd8dbec13b737202531cded5887762e40c1965c`. Only this worktree changed; main/master and other worktrees were not edited. One light process at a time, no bulk jobs, no full training, no test-game contents or evaluation training/tuning, no pushes/submissions or attribution lines. The compatibility replay is the only permitted game, gated on completed swap work.

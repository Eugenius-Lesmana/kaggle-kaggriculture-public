# Endgame models — 2026-10-28

**Do not retain the end16 switch: +460 margin/game (paired-seed SE 316), below the two-SE threshold of 633.** Our bank rises 893/game (SE 265); fifth-nflow's rises 433 (SE 250). Share 0.876, 1/48 wins, 17/24 seed pairs improve. All 48 games and final checks passed. Best remains `net:board-p4:market:overflow:endmask:endwork`.

The result is a small positive estimate with insufficient evidence under the retention rule. Better teacher-command imitation did not establish a reliable live gain. The candidate was selected before live games using held-out accuracy; no evaluation retuning or optional end24 benchmark was performed.

| Model | Days | Held-out segments | Command decisions | Command accuracy |
| --- | --- | --- | --- | --- |
| board-p4 |16–29|308|87,554|89.260%|
| board-end16 |16–29|308|87,554|90.873%|
| board-p4 |24–29|132|34,644|86.791%|
| board-end16 |24–29|132|34,644|89.219%|
| board-end24 |24–29|132|34,644|88.988%|

End16 gains 1.613 percentage points over P4 on 16–29 and 2.428 points on24–29. End24 gains 2.197 points on24–29. **Selection criterion, fixed before live evaluation:** highest command accuracy on the identical common 24–29 rows; end16 wins 89.219% vs 88.988%, and also improves its native 16–29 window. The difference is small; this selection does not establish a meaningful live strength difference.

## Data and CUDA training

11 of 107 parent seed families are reserved entirely, bothseats and alldays, as `endval` using the 11 smallest SHA256(`endval-v1:seed`)values. Validation 308 segments / 7,370 turns; training 96 families / 2,679 segments / 64,104 turns for day16–29. Day24–29 training 1,152 segments / 27,456 turns, validation 132 / 3,146 turns. All worker/market/raw metadata splits agree; only split/purpose metadata changes, never arrays. Nine previously approved whole-segment capacity exclusions remain documented. This is a fine-tuning holdout: P4 pretraining may include these seeds via other sources, so it is not a pristine full-project generalization test.

Both models train 4 epochs with CUDA required, initialized from immutable P4 weights, market enabled, lr 2e-4. Existing P4 scaling is retained. Best validation-command-accuracy checkpoints are evaluated alongside P4 on exactly the same rows. No test 10320–10324 contents or final evaluation seeds20001–20024 enter training or validation.

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
python tools/train_board_net.py board-end16 --sources l1end --day-min 16 --day-max 29 --validation-split endval --require-cuda --init board-p4 --market --epochs 4 --lr 2e-4
python tools/train_board_net.py board-end24 --sources l1end --day-min 24 --day-max 29 --validation-split endval --require-cuda --init board-p4 --market --epochs 4 --lr 2e-4
```

The trainer now supports day filters applied before file lists, nonempty training/validation checks, an opt-in validation split and CUDA requirement. Existing flag defaults remain; no board_net, encoder, vendor or run_full edits. Models and weights stay on D:.

## Player and live test

`end16=board-end16` loads and warms the extra network only when requested, switches both worker and market predictions from day 16 through 28 using the same observation history, and keeps day 29 template. The existing overflow/endmask/endwork rules still run. A 60-day boundary/default selection check passes. Before variant live games, the default ruledP4 seed 20001 seat 0 game reproduced the original gameplay hash exactly: `b00f862412276747f60a068fa906c0d34c9971b376fc7a94f42fa39fd1906cbb`.

Selected test string: `net:board-p4:market:overflow:endmask:endwork:end16=board-end16`. Run `nflow-p4-end16`:48 games, seeds20001–20024, both seats against live fifth-nflow, four game workers maximum, PYTHONHASHSEED=0. No rejected herdcap/onlinesell options. Report paired margin and each bank change over 24 seed means; retain only positive margin gain at about 2 SE. All 48 completed games have 720 steps, both statuses DONE, and no recorded policy/opponent errors. Standard errors use 24 seed means, averaging both seats within each seed. The paired gain equals our bank change minus the opponent's bank change.

[Validation metrics](ENDGAME_MODEL_VALIDATION.json), [selection fixed before live games](ENDGAME_MODEL_SELECTION.json), [training/checkpoint checks](ENDGAME_TRAINING_CHECKS.json), [family split](ENDGAME_VALIDATION_SPLIT.json), [held seeds](../manifests/endgame-validation.csv), [capacity exclusions](../manifests/ownfarm-endgame-excluded.csv).

## Final live comparison

| Measure | Change per game | Paired-seed SE |
| --- | ---: | ---: |
| Our bank | +893.33 |265.39|
| Opponent bank | +433.13 |249.64|
| Margin | +460.21 |316.27|

The original baseline share is 0.871 with 0/48 wins; the end16 candidate share is 0.876 with 1/48 wins. Share is total our bank divided by total opponent bank, not a win probability. Neither rejected herd caps nor the rejected online seller is enabled.

The detached queue stopped unexpectedly after 32 games, with no traceback or recorded cause. After confirming its supervisor/controller/workers were absent and frozen inputs unchanged, only the 16 unfinished games were resumed. All 48 then passed the original final integrity checks; no source, weights or input pins were changed. The queue exited before this report.

`ENDGAME_TRAINING_CHECKS.json` is the historical pre-live training snapshot: its `policy_games_started:false` field describes that earlier point. [Final live checks](ENDGAME_LIVE_CHECKS.json) record the completed 48-game evaluation and current decision. Models remain on D:; baseline P4 is untouched. No pushes or submissions.

Reproduce the comparison with `PYTHONHASHSEED=0`, `KAGML_DATA=<data>` and `PYTHONPATH=src`:

```powershell
python tools/paired_runs.py nflow-p4-ovf-end-ew nflow-p4-end16
python -c "import sys,json; sys.path.insert(0,'tools'); from next_reports import paired; print(json.dumps(paired('nflow-p4-end16')))"
```

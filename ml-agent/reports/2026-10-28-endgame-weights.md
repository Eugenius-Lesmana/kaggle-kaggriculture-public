# Endgame weights — 2026-10-28

**No `board-end1` weights were trained: the existing CLI can select `l1end`, but cannot select days 24–29, and `l1end` has no validation split. Command accuracy is unavailable, not 0%.** No training or encoding tool was edited.

The current master is `b991ec812b6148cd5b9361c85fcf0eac0f34a8fd`. `tools/train_board_net.py` supports `--sources`, `--init`, `--market`, `--epochs` and `--lr`; it has no day or alternative-manifest argument. It filters the source before constructing its `train`, `analysis` and `analysis2` file lists. The already published original `l1end` metadata contains 1,284 day-24–29 segments, all `train`: zero `analysis` and zero `analysis2`. The now-published extension makes that source 2,987 segments, all train, spanning days16–29 with nine approved capacity exclusions. Its day24–29 subset remains the original1,284 train-only segments.

This is the existing supported command, **not run because it does not meet the requested day/validation constraints**:

```powershell
$env:PYTHONHASHSEED='0'
python tools/train_board_net.py board-end1 --sources l1end --init board-p4 --market --epochs 4 --lr 2e-4
```

After extension publication it would include days 16–23. Its empty validation loop would return `decisions=0` and `command_acc=0/max(1,0)`, which is not a measured validation accuracy. GPU availability does not resolve either data issue; the laptop exposes an RTX 3070 Laptop GPU.

## Exact preparation needed

1. Supply a frozen input-manifest view containing only `l1end`, days 24–29, plus nonempty validation labels on separate seed families. An isolated metadata snapshot lets the trainer remain byte-for-byte unchanged. Existing rows must retain their splits unless a new seed reservation is explicitly agreed; new validation labels must not use test games 10320–10324 or evaluation seeds 20001–20024.
2. Alternatively, a maintainer can add `--day-min` / `--day-max` and filter `rows` by inclusive `int(r["day"])` before constructing `files`. This still requires actual nonempty validation rows; a CLI filter alone cannot create them. Reject an empty training or validation selection rather than reporting a denominator-clamped zero as accuracy.
3. Require CUDA before starting the above command. The unmodified trainer chooses CUDA when available and otherwise silently falls back to CPU. A launcher can fail its CUDA preflight without editing the trainer.

With those proposed day arguments implemented, the intended command would be:

```powershell
$env:PYTHONHASHSEED='0'
python -c "import torch; assert torch.cuda.is_available(), 'CUDA required'"
python tools/train_board_net.py board-end1 --sources l1end --day-min 24 --day-max 29 --init board-p4 --market --epochs 4 --lr 2e-4
```

`--day-min` and `--day-max` are proposed additions, not current flags. No new model, player switch, training split, label generation or policy evaluation was invented to bypass these constraints. Claude can supply the data view/validation choice and add the player switch before testing.

[Checks](ENDGAME_WEIGHTS_CHECKS.json). Only manifest metadata and source were inspected; no test contents or private weights were copied.

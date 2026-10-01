# Replay-derived job values

`value.py` is the standalone planner adapter. `schedule_value(obs, jobs)` accepts
the same two arguments as v0.10's hand-set implementation. Each job needs
`operation`, `target`, and `owner` fields. The function returns the sum of
learned scores; `rank_cell_jobs(obs, jobs, unit_index)` orders commands on the
current tile. It leaves job eligibility, deadlines, resource reservations,
and dependent chains such as `HARVEST → PLANT → WATER` to the planner.

The bundled `model.json` contains small decision trees. Inference uses only
Python's standard library. Scores represent observed action priority, not
economic coin value. The next-cell tree scores travel jobs; the within-cell
tree scores a hand already on the target. Avoid interpreting the `scale` as
coins or mixing these scores with the old hand-set numbers.

From the repository root:

```powershell
python evaluation/jobvalues/train.py
python -m unittest evaluation.jobvalues.test_value
```

Training requires scikit-learn. It reads the committed 24 September replays
and the uncommitted 29 September archive at the absolute `NEW` path in
`train.py`. The game-level split and measured results are in `results.json`.

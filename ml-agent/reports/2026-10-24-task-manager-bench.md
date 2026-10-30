# Task-manager test: does the way workers carry out jobs explain ranker v2's weak play? (2026-10-24)

**No.** Same 120 mornings (24 games x days 8/12/16/20/24, one day each); value per day as in
`reports/2026-10-22-measure-first.md`. Ranker v2 = model `ranker-own-v1` (trained on L1).

| Variant | vs template (all) | vs v2 (all) | vs v2 (held-out 10320-10324) |
|---|---:|---:|---:|
| v2 as is | -68 (se 56) | 0 | 0 |
| v2 + keep (unload goods without dropping needed wheat) | -83 (se 58) | -15 (se 26), better on 29% | +19 (se 72) |
| v2 + redecide (choose again every turn) | -727 (se 81) | -659 (se 76), better on 19% | -784 (se 217) |

Keep removes some drops (6.4 -> 5.3 a day) but changes nothing in value. Re-deciding makes workers switch
targets and water less (43 vs 51 a day). Fetching for all open jobs changed nothing on the smoke mornings.
The shortfall is in which jobs v2 chooses, so the next step is the correction round (L3, v3).

Evidence: `<data>/runs/compare/tmA.csv`, `tmB.csv`, `v2benchA.csv`, `v2benchB.csv`, `mixA.csv`, `mixB.csv`.

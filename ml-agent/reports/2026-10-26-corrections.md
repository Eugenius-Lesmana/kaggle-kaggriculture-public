# Corrections to earlier reports (2026-10-26)

Found by Codex in package U and confirmed in the engine (`kaggriculture.py`, `_daily_refresh_plants` and
`_daily_refresh_animals`, kaggle-environments 1.32.7):

1. **An unwatered ongoing crop (strawberry, tomato) still produces its base unit on a production night if it
   survives**; watering only enables the fertilizer bonus (+1). A crop dies only after two dry days in a row.
2. **An unfed animal still produces its base unit on a production day if it survives**; feeding only releases the
   banked care bonus. An animal escapes only after two unfed days in a row.

**What this changes:**

- `reports/2026-10-24-diagnosis.md`, `reports/2026-10-25-gap-table.md` and `reports/2026-10-26-board-network.md`
  described crops "unwatered on a night they would produce" and animals "unfed on a production night" as
  **lost production**. The real loss is only the fertilizer bonus (crops) or the care bonus (animals). The counts
  stand; their cost was overstated. The rows "fertilized, double yield lost" were the costly part and remain right.
- Crop deaths (two dry days) and animal escapes (two unfed days) were described correctly and remain the real
  losses.
- The ranker features `n_loss_if_dry` / `n_loss_if_unfed` (`src/kagml/work_features.py`) overstate the
  production-night loss in the same way. They are model inputs, so the model learned its own weighting; they are
  kept unchanged so the trained models stay valid, but they should not be read as money at stake.
- The conclusions drawn from those rows (the teacher prioritises crops; the guard was over-protective) are not
  affected in direction; the measured full-game results are unaffected.

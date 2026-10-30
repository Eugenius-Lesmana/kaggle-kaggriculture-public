# Turn-dataset counts (package N)

Non-test teacher turns only: 4,598 segments, 69,977 turns,
807,118 worker decisions; 763,784 change native state.
All test games 10320-10324 were filtered before opening tensors. Counts include train and analysis;
L3 begins at its takeover. See `turns-sizes.csv` for each source.

Issued non-PASS no-ops: 1,998. They remain in arrays; command-loss mask excludes them.
PASS is a valid stay choice even though native state does not change. Amounts above five:
36; exact values retained, excluded from the five-class amount loss.

## Movement and targets

288,184 effective moves have a future effective job. 395 move away from that job's tile;
287,789 move toward it. `turns-walking.csv` separates destination job, distance and rough value.
Consecutive walking pairs with targets: 74,618; target changes: 0.
The target is the next *observed* effective job, so it cannot change across uninterrupted walking by
construction. This is not evidence that the teacher never changes hidden intention. Intention/diversion
frequency is unidentifiable from issued commands alone; away moves are only an observable proxy.

Of 414,492 intermediate jobs with a later job, 69,397 have nonzero legs
from anchor to job and job to later job; 63,045 lie on a Manhattan shortest path
and 62,913 also have an observed movement count equal to that shortest distance.
Anchor = previous effective job, or first teacher position if none (left-censored, explicitly flagged).
The current job and next later job must differ; repeated care/feed on the same tile do not count.
These observed on-path jobs do not prove a prior intended target.

## Reading the CSVs

- `turns-command-mix.csv`: exact command including item, issued count, native effect, source, overall/hour/day band.
- `turns-worker-order.csv`: absolute slot and relative farmer/early/middle/late hand groups; job mix and
  sum of distance to next effective job (divide by future_jobs for its mean). Relative groups split hand
  ordinal into thirds separately each turn. These are associations, not causal coordination effects.
- `turns-amounts.csv`: exact requested quantity, context applicability, native effect and units transferred.
  `amount_applies=False` includes animal placement (native always places one) and invalid field placement.
- `turns-walking.csv`: toward/away counts plus consecutive walking target comparisons. Distance uses Manhattan
  geometry (locked land is passable); value is the existing work_features immediate-dollar heuristic, not
  realized profit. Value/distance refer to the future job, never encoder inputs.
- `turns-on-path.csv`: intermediate-job geometry and observed shortest movement, grouped by job and censoring.
- `turns-sizes.csv`: compressed NPZ bytes and non-test source totals. Each worker present before the turn counts
  once, including implicit PASS; newly hired hands appear next turn. No nonexistent workers are counted.

Rerun: `PYTHONHASHSEED=0 python tools/report_turn_dataset.py` (set KAGML_DATA to the external data root).

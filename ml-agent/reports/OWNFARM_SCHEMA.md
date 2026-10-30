# Own-farm fourth-place day segments (L1)

These labels show the fourth-place policy on our template farm in 24 standard `el3` games, seat 0, mornings
6 through 28 inclusive. The opponent uses its recorded moves. Workers are capped at two; data and logs stay
under the configured data root (`<data>` on this machine).

```powershell
python tools/ownfarm_labels.py --smoke --workers 2
python tools/check_ownfarm.py --smoke
python tools/ownfarm_labels.py --workers 2
python tools/check_ownfarm.py
```

The smoke uses game 10301 on days 6, 16 and 28. Full generation requires a passing smoke with identical source
code and teacher hashes. Generation resumes verified receipts by dependency, source and compressed-segment
hashes, requiring all six table shards. Re-running the full command also checks all completed input hashes.
`check_ownfarm.py --smoke` applies only before the full corpus exists in the same output directory.

- Replays: `raw/ownfarm/fourth/<game>-d<day>.json.gz`.
- Tables: `datasets/ownfarm/<table>/<episode>.parquet`, the six unchanged D1 schemas in `D1_SCHEMA.md`.
- Receipts: `datasets/ownfarm/audit/<episode>.json`, including state reconciliation, effective commands,
  both banks, teacher-call timings, source hashes and loader diagnostics.
- Run evidence: `runs/ownfarm-fourth/{smoke,full,validation,benchmark}.json`; failed smoke summaries retained
  as `smoke-attempt1.json` and `smoke-attempt2.json`.
- Tracked manifest: `manifests/ownfarm.csv`. `file` is relative to the data root; SHA256 covers the compressed
  bytes. `end_cash_0/1` are bank balances, not rewards or within-day earnings.

Each replay is `env.toJSON()` with padded preview history removed. It has 25 frames: the initial morning
snapshot and 24 transitions, ending at the next dawn. `info.seed` is retained; `ownfarm` records provenance,
the takeover seat, day, original start step, teacher and reset seed. Seat 1's missing observation `step` is
supplied by the existing preview harness; all other snapshot fields match the source exactly. Original
turn numbers remain: day `d` has pre-action frames `24*d` through `24*d+23`, plus the closing frame `24*(d+1)`.
Segment statuses remain ACTIVE. No earlier repeated placeholder frames are stored.

`episode = int(game) * 100 + day` is a synthetic unique segment ID. Submission/team/rating fields are -1,
and `date` is empty because these are local counterfactuals. `games.bank_0/1`, `winner` and closing `shops`
describe the segment's endpoint, not a completed game's outcome. Use the manifest to distinguish these rows.
The extractor requires explicit `replay(..., 'split-weeds', segment=True)` to initialize from a snapshot;
its default still initializes a full game and requires terminal DONE status. All states, statuses, rewards,
private inventories and cash bridges are checked through the native engine, as in D1.

The fourth-place actor resets with the source game's `info.seed` for EVERY segment. Weights remain cached per
worker. The pinned weed convention is enabled for generation and re-extraction. Direct actor exceptions fail
the segment; no replacement action is supplied. Every accepted segment has 24 calls and effective own unit
actions; opponent commands are checked against the original recording on all 24 transitions. No edits to
`vendor/`, `preview.py`, `opponents.py` or upstream policy files are needed.

For training, group splits by ORIGINAL GAME, including the parent replay and every segment from it: sibling
mornings share states and must not cross train/test boundaries. Both seats' actions are extracted, but only
seat 0 is the fourth-place teacher; seat 1 is the recorded opponent. Join actions and features on the same
absolute `step`. Labels include `took_effect` and actual execution-price `sales`; keep unsuccessful issued
actions distinguishable. Closing banks, `games` outcomes and future dawn rows must not enter decision features.

```python
import sys
sys.path.insert(0, 'src')
from kagml.paths import datasets
from kagml.replay_tables import connect
con = connect(datasets() / 'ownfarm')
print(con.sql('SELECT count(*) FROM unit_actions WHERE seat=0 AND took_effect').fetchone())
```

`check_ownfarm.py` verifies manifest hashes, original snapshots, seeds, recorded opponent actions, status,
frame coverage, table counts and keys, cash/sale bridges, acting teacher and row timing. It rejects a corrupted
segment and an implicit segment; it also rebuilds an existing full Kaggle game with tables identical to D1
and rejects an incomplete full game. For each of the 120 overlapping mornings in `runs/compare/rev24.csv`,
`benchmark.json` records our and the opponent's within-day cash differences from that benchmark. It does not
require agreement: the old benchmark did not explicitly reset each segment's seeded sampler. Actual agreement
is reported in validation results.

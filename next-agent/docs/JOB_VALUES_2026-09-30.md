# Replay-learned job priorities

Date: 2026-09-30. Branch: `dev/eugene-codex-jobvalues`.

## Verdict

**Pass as an imitation model; hold for game testing before planner adoption.** The
within-cell tree exceeds the cell rule on held-out multi-job states, including
F1 for every command. The next-cell tree strongly exceeds nearest due job
overall, but it misses almost every next-cell `CARE` choice. No game screens
were run, so neither score establishes a coin or win-rate gain.

## Data and split

- 39 top-agent player-games from the committed 24 September top-four replays;
  536 from the local, uncommitted 29 September top-four archive. The latter
  seats come from each submission folder's `episodes.json`.
- 557 distinct episode IDs (33 old, 524 new). A fixed 80/20 split hashes
  cohort and episode ID, keeping duplicated downloads and opposite seats of
  the same game together. Player-game counts: 463 train, 112 test.
- The backbones `routes.csv.gz` was checked for action order and provenance.
  Training reads the replay observations because the route CSV does not store
  the full tile, inventory, and market state.
- Deterministic hash sampling covers all hours. Model inputs are command,
  crop/animal, age, tile status and urgency counters, hand inventory, hour,
  price, position, and Manhattan distance. No outcome or future action is an
  input. The future action is used only as the training label.

## Within-cell order

Only states with at least two currently executable crop or animal service
commands enter this test. Both methods choose among the same commands. The
reference rule takes water before fertilize before harvest on crops, and
fertilizer collection before feed before harvest before care on animals.

| Held-out multi-job decisions | Learned | Cell rule |
|---|---:|---:|
| Top-1, 22,270 decisions | **88.5%** | 60.1% |
| Top-3 | 99.7% | — |

The previously reported **68.7%** cell-rule result covers *all* 29 September
core farming actions, including single-job states and planting. This test's
60.1% rule score is the comparable denominator for multi-job ordering. The
learned 88.5% exceeds both numbers, but the 68.7% figure is not a matched
comparison.

| Actual command | n | Learned recall | Rule recall | Learned F1 | Rule F1 |
|---|---:|---:|---:|---:|---:|
| WATER | 8,708 | 95.5% | 100.0% | **96.7%** | 84.8% |
| FERTILIZE | 2,051 | 92.2% | 1.7% | **87.1%** | 2.9% |
| HARVEST | 2,667 | 72.6% | 11.6% | **80.0%** | 18.1% |
| COLLECT_FERTILIZER | 3,044 | 78.6% | 100.0% | **82.3%** | 56.9% |
| FEED | 3,200 | 100.0% | 40.2% | **85.0%** | 51.7% |
| CARE | 2,600 | 75.8% | 0.0% | **81.8%** | 0.0% |

The rule's perfect water and fertilizer-collection recall comes from selecting
those commands excessively; its precision is 73.6% and 39.8%, respectively.
The learned model is more selective. Training used 91,979 decisions; the
deterministic sample contained 114,249 multi-job decisions across both splits.

## Next-cell choice

A choice starts when a hand moves after work or at day start. The label is its
next crop/animal service command within 12 turns on the same day. Candidates
are currently due service jobs on all farm tiles; the hand must already carry
the input needed for feed or fertilize. This excludes construction, planting,
pickup/drop, and destinations whose job only becomes due later. Of 28,591
sampled starts, 26,519 had the observed job among current candidates (92.8%).
The score below is conditional on that coverage.

| Held-out choices | Learned | Nearest due job |
|---|---:|---:|
| Top-1, 5,280 choices | **51.0%** | 6.6% |
| Top-3 | **74.4%** | — |

| Actual next command | n | Learned top-1 | Nearest top-1 |
|---|---:|---:|---:|
| WATER | 2,373 | 60.7% | 7.1% |
| FERTILIZE | 756 | 51.7% | 13.2% |
| HARVEST | 654 | 33.3% | 5.2% |
| COLLECT_FERTILIZER | 518 | 38.8% | 0.2% |
| FEED | 801 | 54.9% | 1.4% |
| CARE | 178 | **0.6%** | 19.7% |

The model uses location and crop age heavily; hour, inventory, urgency, and
price also appear in its fitted splits. The nearest baseline is weak because
many due jobs compete across a full farm. The held-out test is imitation,
not a test of whether a different next cell would earn more coins.

## Deliverable and use

`evaluation/jobvalues/value.py` exposes `schedule_value(obs, jobs)` with the
v0.10 signature and `rank_cell_jobs(obs, jobs, unit_index)` for local command
order. `model.json` holds 64-leaf and 96-leaf decision trees (7.3 KB); runtime
uses the Python standard library. `train.py` reproduces the fit with
scikit-learn; `results.json` has exact counts and precision/recall. The model
scores observed priority, not economic value. Preserve planner eligibility,
deadlines, inventory reservations, and dependent action chains.

Next gate: integrate behind a switch in a new planner candidate and screen on
seeds 7801–8000 with both seats and at most two workers. Keep the hand-set
planner as control. Pay particular attention to animal care and actual bank
ratio before replacing the hand-set values. No seeds from that range were used
here.

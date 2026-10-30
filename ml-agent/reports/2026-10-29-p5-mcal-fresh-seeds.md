# Keep P5; reject market calibration — fresh-seed confirmation

**Keep board-p5 over P4; reject `mcal`.** P5 improves margin by **+4,604/game (SE 1,074)** on fresh seeds and **+3,536 (SE 692)** over all 48 seed pairs. Calibration changes margin by **−1,453 (SE 822)** on fresh seeds and **−27 (SE 616)** pooled. All 96 fresh primary games and four repeats passed audit.

The fixed rule requires a pooled margin of at least two SE and a positive fresh-seed estimate. P5 passes both: pooled 5.11 SE, fresh positive. Calibration fails both: its fresh estimate is negative and pooled gain is below its 1,232.22 two-SE threshold. The retained player is `net:board-p5:market:overflow:endmask:endwork`, without `:mcal`.

## Paired comparisons

Candidate minus baseline, coins per game. Standard errors use seed means after averaging both seats; pooled estimates use all 48 seed means.

| Comparison | Sample | Seed pairs | Margin change | SE | Our bank change | SE | Opponent bank change | SE |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| P5 − P4 | Fresh 20025–20048 | 24 | +4,604.35 | 1,074.21 | +4,212.79 | 967.78 | -391.56 | 774.27 |
| P5 − P4 | Pooled 20001–20048 | 48 | +3,536.15 | 692.11 | +3,342.69 | 634.97 | -193.46 | 520.56 |
| P5 − P4 | Old 20001–20024 | 24 | +2,467.94 | 839.40 | +2,472.58 | 803.35 | +4.65 | 710.35 |
| mcal − P5 | Fresh 20025–20048 | 24 | -1,452.81 | 822.39 | -1,356.40 | 727.33 | +96.42 | 629.13 |
| mcal − P5 | Pooled 20001–20048 | 48 | -26.72 | 616.11 | -180.09 | 559.17 | -153.38 | 424.19 |
| mcal − P5 | Old 20001–20024 | 24 | +1,399.38 | 835.59 | +996.21 | 792.81 | -403.17 | 578.06 |

For P5 over P4, pooled improvement is primarily our bank rising 3,342.69/game; fifth-nflow's bank falls 193.46. For calibration over P5, pooled changes are our bank −180.09 and the opponent −153.38. Their difference is the near-zero −26.72 margin. Fresh calibration mainly reduces our bank (−1,356.40), while the opponent gains 96.42.

| Sample | Agent | Games | Share | Wins |
| --- | --- | ---: | ---: | ---: |
| Fresh | P4 | 48 | 0.883971 | 0/48 |
| Fresh | P5 | 48 | 0.926263 | 1/48 |
| Fresh | mcal | 48 | 0.912864 | 0/48 |
| Pooled | P4 | 96 | 0.877511 | 0/96 |
| Pooled | P5 | 96 | 0.910365 | 2/96 |
| Pooled | mcal | 96 | 0.909986 | 1/96 |
| Old | P4 | 48 | 0.870917 | 0/48 |
| Old | P5 | 48 | 0.894201 | 1/48 |
| Old | mcal | 48 | 0.907047 | 1/48 |

Share is total our bank / total opponent bank, not win probability. P5 improves substantially over P4 while still trailing fifth-nflow overall: pooled share 0.910 and 2/96 wins. The comparisons support relative improvement against this opponent, not general dominance.

## Fixed decision and interpretation

The protocol was committed before fresh results in `e2755ae`. For each change separately: retain only if all 24 fresh seeds, both seats and agents, are complete, the pooled 48-seed-pair margin is ≥2 SE, and the fresh-only margin is positive. No selection uses share or wins; no threshold, model or calibration was changed after seeing these results.

P5's pooled two-SE threshold is 1,384.23; the gain is 3,536.15. Calibration's old estimate was +1,399.38 (SE 835.59), but its fresh estimate reversed sign and the pooled result is −26.72 (SE 616.11). This test rejects this fixed calibration, rather than establishing why it failed. Improved teacher-forced order precision/count matching in the [groundwork report](2026-10-29-market-model-design.md) did not translate into a retained live gain. No calibration was refitted on evaluation seeds.

For a seed, average candidate-minus-baseline bank changes over seats 0 and 1; margin change equals our bank change minus the opponent's. Compute the sample standard deviation of those seed means divided by sqrt(N), with N=24 or 48. Pooled SEs are recalculated from all 48 observations, not averaged from the two sample SEs. Both sets have equal weight per seed. The old P5 estimate reproduces the handoff: +2,467.9375, SE 839.3952853.

The [96-row contrast/seed table](2026-10-29-p5-mcal-seed-pairs.csv) permits independent recalculation. All means and SEs were checked with a separate sum-of-squares implementation. Scenarios agree across all three agents and both seats within every seed. No failed, repeated or partial game was substituted into an estimate.

## Runs and evidence

Exact player strings:

- P4: `net:board-p4:market:overflow:endmask:endwork`.
- P5: `net:board-p5:market:overflow:endmask:endwork`.
- mcal: `net:board-p5:market:overflow:endmask:endwork:mcal`.

Fresh tags are `nflow-p5-best-s2` and `nflow-p5-mcal-s2`, 48 games each on 20025–20048, both seats, against live fifth-nflow. They ran sequentially through the unchanged `tools/run_full.py` with three workers maximum, `PYTHONHASHSEED=0` and `KAGML_DATA=<data>`. Both run-integrity audits accepted 48 primary games, zero rejects, and two matching repeats. Primary games have 720 steps, both statuses DONE and no policy/opponent errors.

Permitted controls only: `nflow-p4-ovf-end-ew-s2` for fresh P4, plus `nflow-p4-ovf-end-ew`, `nflow-p5-best` and `nflow-p5-mcal` for 20001–20024. Claude's old calibration run was complete before pooling. All 192 cached control receipts/replays were checked with `run_full.verify` using their original stored signatures and unchanged metric hashes; no control policy game was rerun. Together with the new audits, this covers 288 distinct primary games.

The fresh P5 seed 20001 seat 0 compatibility replay matched the completed old P5 control before fresh games:
`6a665ffecd0ce844a4037018fdb1117e459a61e328822283d4d37c71a97dc6fd`.
The compatibility game and four new repeats are excluded from all estimates.

Data evidence is under `<data>/runs/` in the six exact tags above. Campaign inputs, frozen comparator hashes and gate evidence are under `p5-mcal-confirm-20261029/`. [Final checks](P5_MCAL_FRESH_CHECKS.json) preserve decisions, precise estimates, audits, hashes and coverage.

## Isolation and completion

Source `3768e0023c66ed6d944ed293480f25a6ecff8285` includes the calibration commit c39ae9c. Work is isolated to approved branch `dev/eugene-codex-market-20261029` in new worktree `kaggriculture-ml-market-20261029`; the pre-existing requested market branch/worktree was preserved. Runtime, shared encoder, runner, template/vendor, P5 weights and calibration are unchanged. All 153 initial source/model/opponent pins and 192 control-metric pins passed final checks.

Eugene's requested pause preserved 36 completed P5 games. On explicit resume, original pins and drive identity were rechecked; the same queue completed the remaining games. Ignored launcher failure handling was repaired before the long run, without changing a policy, calibration or frozen pin. Only completed valid receipts enter the final comparison. All owned game and replay-audit processes have exited.

Task 2 was completed in `e2755ae`: [market-model design](2026-10-29-market-model-design.md), [timing evidence](MARKET_MODEL_TIMING_CHECKS.json), [feature/cost evidence](MARKET_MODEL_DESIGN_CHECKS.json). No market model was trained or integrated. No test-game 10320–10324 contents, evaluation training/tuning, main/other-worktree changes, pushes, submissions or attribution lines. The retained string is reported here; no other best-agent or runtime file was edited.

# planner/main.py (v0.11 research candidate)

Our adaptive planner, built up since early September. With every research switch at its default it plays exactly
as v0.10. Against Metav4 it ends with about 0.70 of that agent's bank.

Experiments: [`../docs/EXPERIMENT_LOG.md`](../docs/EXPERIMENT_LOG.md). Overview: [`../README.md`](../README.md).
SHA-256 of `main.py`: `35b035a0f991d543a86eac9020bec5a5a6122a006ca956b65b8f4541a58ca8d8` (team names in two
comments anonymised).

The file ends with a small wrapper so that the last callable is the entry point Kaggle's loader runs:
`globals().pop("agent", None)` followed by `def agent(...)`.

## Switches

| Switch | Default | What it does | Result when on (paired, 80 games unless noted) |
|---|---|---|---|
| `FERT_CHAIN` | `True` | Fertilize with what the same worker just collected | **+0.015 ± 0.004** on held-out seeds (kept) |
| `FERT_PRICE_SCALE` | 1.0 | Value fertilizer at this share of its quote | 0.5 → +0.009 ± 0.010 |
| `FERT_FREE_UNTIL_DAY` | 0 | No worker-time charge for fertilizing before this day | 12 → −0.003 ± 0.008 |
| `FERT_FREE_FROM_DAY` | 99 | Same, from this day on | no result recorded |
| `FERT_PRECISE` | `False` | Fertilize only at the top agents' bonus ages | −0.016 ± 0.008 |
| `FERT_PIGGYBACK` | `False` | Fertilize only on visits a cell needs anyway | −0.053 ± 0.009 |
| `FERT_PROGRAMME` | `False` | Load fertilizer from the shed for fertilize jobs | −0.032 ± 0.004 (rejected) |
| `FERT_CHAIN_FREE_ACTION` | `False` | No action surcharge on chained fertilizing | −0.019 ± 0.006 (rejected) |
| `JOB_VALUES_LEARNED` | `False` | Job values from decision trees trained on top-agent moves | +0.005 ± 0.007 (240 games) |
| `ZONE_SWEEP`, `ZONE_ONLY`, `SWEEP_ONLY` | `False` | Angular sectors per worker, inside-out reorder | sectors lose; reorder alone about neutral (6 games) |
| `LATE_HANDS` | 11 | Programme hands from day 12 | 13 → −0.037 ± 0.009 |
| `MARKET_MODULE` | `False` | Market rules derived from Metav4 / F4: price curve, exposure ordering, held-stock sale gate | **+0.006 ± 0.003**, by lowering the opponent's income; unconfirmed |

Capacity flags (`CAPACITY_*`) are not in this file. They lived on a separate experiment branch and lost in a
four-game smoke ([`../docs/CAPACITY_MODULE_2026-09-30.md`](../docs/CAPACITY_MODULE_2026-09-30.md)).

## Attribution

The planner is our own code. The embedded market module (`_MM_SRC`) derives from Apache-2.0 sources; its header
names Ahmed Berat Ozer, prvsiyan, yhay81 and thomastschinkel and points at the notices in the agent file in
[`../../agent/`](../../agent/). The learned job-value trees were trained on top-team replays by Codex; the
training script is [`../evidence/jobvalues/train.py`](../evidence/jobvalues/train.py). See the repository
[`NOTICE`](../../NOTICE).

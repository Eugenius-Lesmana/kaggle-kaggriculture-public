# Next agent (unfinished)

We are building a second agent that is **not** a fork of the Metav4 / F1 / F4 tape family: our own planner,
informed by what the top teams do. **We did not finish it before the deadline.** It is still being worked on.
This folder is the honest state of that work: what exists, what we measured, and what is missing.

> **Current level:** in paired games against Metav4, our planner ends with about **0.70 of Metav4's bank**
> (about $82k against $117k, 560 games). It does not beat the agents in [`agent/`](../agent/).

## What exists

[`planner/main.py`](planner/main.py) (v0.11 research candidate) is a single-file adaptive planner, built up
since 7 September. It is the planner of record for every experiment below. Every research switch is **off by
default**. In that state it plays exactly as our v0.10.

- **Greedy day scheduler.** `schedule_compile` builds each worker's day as a list of whole-cell service chains
  (water, harvest, feed, care, plant, fertilize), ranked by benefit per time span, appended one after another.
  `schedule_value` holds the hand-set job values.
- **Programmes** (`PROGRAMMES`, `PROGRAMME_HANDS`, `LAND_POLICY = "programme"`): which animals and crops go in
  each quadrant, how many workers to hire each day, and when to buy land.
- **Fertilizer** (`fertilizer_targets`, `fertilizer_gain`): applies collected fertilizer where it adds the
  most yield. A "chain" rule (fertilize with what the same worker just collected) was confirmed at
  +0.015 ± 0.004 on held-out seeds.
- **Research switches**, all `False` / neutral: precise fertilizer timing, free fertilizing, learned job values
  (`JOB_VALUES_LEARNED`: decision trees trained on about 2 million top-agent worker turns), zone sweeps,
  late hires, and a market module (`MARKET_MODULE`).

## What we found

1. **Execution is not the limit.** On our own farm, almost every job that falls due is done and walking time
   (36–47%) matches the top teams'. What differs is that our workers are **idle early**: 52% of worker time on
   days 0–5 and 29% on days 6–11, because the plan has no work for them.
   ([`EARLY_LABOUR`](docs/EARLY_LABOUR_2026-09-30.md))
2. **The top teams make more, and sell it at about the same price.** About 52% more units a game: 54% from more
   cells and animals, 46% from higher yield per cell, most of it from fertilizer timed to the yield window.
   ([`PRODUCTION_GAP`](../analysis/top-agents/PRODUCTION_GAP_2026-09-30.md),
   [`MARKET_EDGE`](../analysis/top-agents/MARKET_EDGE_2026-09-30.md),
   [`YIELD_DRIVERS`](../analysis/top-agents/YIELD_DRIVERS_2026-09-30.md))
3. **Copying them does not work, because the answers depend on the situation.**
   - The top plan on our executor lost: −0.085. About $13.5k of that is the *opponent* gaining, because the
     products we stopped selling raised its prices. ([`PLAN_VS_MARKET`](docs/PLAN_VS_MARKET_2026-09-30.md))
   - Copied route order, acting on each cell's state, did not help (−0.012 ± 0.014), and a literal 12-day action tape
     broke on day 1: we held $1 where the tape needs about $4, so only one of its three hires went through.
     ([`EXECUTOR_PROTOTYPE`](docs/EXECUTOR_PROTOTYPE_2026-09-29.md))
   - The top fertilizer recipe lost: fertilizing displaced yield-window watering (90% → 65%), so the bonus was
     lost.
   - Job priorities learned from their moves were neutral: +0.005 ± 0.007 over 240 games.
4. **The gap is structural.** Of about 22 single changes, one is a small gain waiting for confirmation. The
   rest are neutral or negative. The full table is in [`docs/EXPERIMENT_LOG.md`](docs/EXPERIMENT_LOG.md).

The reason, in our reading: the top agents' seasons were **optimised as one piece, offline**: the opener, land
steps, hires, layout and routes were tuned together, probably by testing many variants. Our planner makes
step-by-step decisions from hand-set values. A piece of their plan does not work without the rest.

## What is missing

A way to produce a **whole-season plan that fits our own farm and our own opponents**. See
[`ROADMAP.md`](ROADMAP.md): search for it offline with real games as the judge, record the best games as a
tape, and use the planner as the **bridge**: when a game drifts from the tape, the planner takes over from the
current state.

## Folder map

| Path | Contents |
|---|---|
| [`planner/`](planner/) | The v0.11 planner and its flag list. |
| [`docs/`](docs/) | Dated notes: [`EXPERIMENT_LOG`](docs/EXPERIMENT_LOG.md) (start here), and the notes behind each result. |
| [`evidence/routeopt/`](evidence/routeopt/) | Result files for the paired experiments, `diag.py` (full-game diagnostic), `paired.py`. |
| [`evidence/`](evidence/) | Also: executor prototype, learned job values, capacity module, market module. |
| [`ROADMAP.md`](ROADMAP.md) | What is next, in order, with the measurement that decides each step. |

## Run it

```bash
pip install kaggle-environments==1.32.7
python tools/screen.py --candidate next-agent/planner/main.py --opponent agent/main.py \
    --seeds 9001-9040 --seats 2 --workers 2 --json out.json
python next-agent/evidence/routeopt/diag.py --help        # full-game idle / walking / useful-action breakdown
```

Opponents for planner experiments were the public Metav4 agent (not redistributed here) and, for guards, F4-based
agents. `agent/main.py` is the strongest opponent available in this repository.

## Method

Every experiment is paired: the same seeds and seats for the change and its control (80 games, 2 workers).
We report the change in our bank's ratio to the opponent's (± 95%), and for plan changes also our bank and
the opponent's bank separately. A result is confirmed on fresh seeds before a switch is kept.

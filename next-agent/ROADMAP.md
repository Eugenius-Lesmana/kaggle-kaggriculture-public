# Roadmap

This is a plan, not a result. Order matters: each step produces what the next one needs, and each ends in a
measurement that decides whether to continue.

## Goal

A distinct agent, not a fork of the Metav4 / F1 / F4 family, that **beats them in paired games**. We do not need
to beat the top four. The first target is to move the planner clearly past its 0.70 baseline against Metav4.
The stretch target is parity or better.

## Why a generator, and what "tape" and "bridge" mean

The agents that beat us play a **tape**: a whole-season plan that was optimised offline as one piece. Copying
their moves fails because their moves answer *their* situation: their layout, cash, shops and opponent (see
[`docs/EXPERIMENT_LOG.md`](docs/EXPERIMENT_LOG.md), sections 1 and 2). The step that is missing is a way to make a
tape that fits **our** farm.

- **Tape** = the recording of our own planner's best games, after its 20–30 big decisions have been tuned
  together by an automatic search. The decisions: land steps, hires per day, animals per quadrant, crop mix by
  day and shop, fertilizer ages, sale hours.
- **Bridge** = the planner itself. When the farm or the cash drifts from what the tape expects, the planner takes
  over from the current state instead of continuing a script that no longer fits. It is adaptive, so it is
  always able to do that.

## Steps

### 0. Confirm the market module (small)

It scored +0.006 ± 0.003 on 80 games, by lowering the opponent's income, not raising ours. Re-run on fresh
seeds (at least 160 games, seeds not used in [`EXPERIMENT_LOG`](docs/EXPERIMENT_LOG.md)).
**Keep it on only if the gain is repeated** with an interval that excludes zero.

### 1. Make the plan a parameter vector

Move the hand-set numbers in `planner/main.py` (`PROGRAMMES`, `PROGRAMME_HANDS`, land steps, fertilizer ages,
`LATE_HANDS`, sale hours) into one JSON-loadable "genome". **Done when** the default genome reproduces the
current planner's games exactly, seed for seed.

### 2. Search offline, with real games as the judge

- Search method: successive halving, then local refinement, or CMA-ES over the genome.
- Evaluation: 20 games per trial against a fixed panel (Metav4, F1, F2, the final agent in [`agent/`](../agent/)).
  Report our bank and the opponent's bank separately; do not accept a gain that is only an opponent loss.
- Budget: a few hundred trials. At about 10 s a game and 2 workers, that is 10–15 hours of laptop time.
- A resumable log lands in `evidence/search/`, one line per trial.
- **Decision:** continue only if the best genome beats the default by more than the noise on a held-out set of
  seeds. Otherwise the search space is wrong; widen it before spending more compute.

### 3. Record tapes and write the bridge

- Record the best genome's games as tapes. Per day: each worker's moves and market orders.
- Write a **drift detector**: compare the observed farm (cells, animals, cash) to the tape's expected state each
  step, and hand control to the planner when they differ beyond a tolerance.
- **Decision:** the tape-plus-bridge agent must beat the genome-planner on fresh seeds. If it does not, the plan
  is not the bottleneck and the bridge adds no value.

### 4. Confirm and write up

- Fresh seeds, both seats, at least 160 games per opponent. Paired against the final agent in
  [`agent/`](../agent/) and the older families.
- Update [`docs/EXPERIMENT_LOG.md`](docs/EXPERIMENT_LOG.md). A negative result is a result.

## Not planned

- More single-switch tweaks to the current planner. 21 of about 22 were neutral or negative.
- Copying the top teams' routes or action tapes onto our executor ([`EXPERIMENT_LOG`](docs/EXPERIMENT_LOG.md),
  sections 1 and 2).

## Log

Real work only. One line per day, newest last.

- **2026-10-01.** This repository assembled from the working repository. Market-module confirmation (step 0)
  not yet run.

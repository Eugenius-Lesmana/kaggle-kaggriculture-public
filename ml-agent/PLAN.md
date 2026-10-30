# Kaggriculture: a hybrid agent that looks ahead (plan, revised 2026-10-17)

Status (2026-10-26): **whole-board network board-v4 (no guard) on days 6-28 beats Metav4 in full games (share 1.119, 44/48 wins on fresh seeds); held-out opponents not yet tested; see `reports/2026-10-26-board-network.md`.** Earlier status: Stage 0. This revision replaces the 2026-10-16 plan (kept in git history and in the
competition repository's `docs/ML_AGENT_PLAN_2026-10-16.md`).

## 1. Goal

Beat the Metav4 family **comfortably** (Metav4, F1, F4, the counter versions, our earlier agents and the coded
submissions we can run) **without over-fitting to them**, at a cost a solo player can afford, in a way that is our
own work. Beating the top machine-learning teams is not the goal.

| Level | Target, every setup, paired seeds, by scenario |
|---|---|
| Good | Our own bank above the template agent's (0.913 of Metav4) |
| Target | Share of the opponent's bank above 1.0 and more than half of paired games won |
| Comfortable | Clearly above 1.0 against the **held-out** opponents too, not only the ones we tuned on |

## 2. Why the template agent stalled

It plans the farm reasonably well and recovers waste well, but it hands out worker time one step at a time from
hand-set scores and judges each job only by today's value. Every fix that needed worker time took it from other
work. It also has no way to set its many numbers (hands, land timing, herd size, sale quantities) except by hand,
and no way to look a day ahead.

## 3. Design: five roles

| Role | Job | Filled by |
|---|---|---|
| **Propose** | A few sensible plans for today: what to grow and where, herd, land, hires; the opener | Our rules first; then patterns learned from top teams' replays |
| **Judge** | Score each proposal by what it leads to, a day or more ahead | Our farm simulated exactly with the game engine, plus a **stand-in opponent** modelled as market pressure |
| **Tune** | Set the small numbers | Black-box optimisation over many games |
| **Guard** | Things that must not happen (starvation, overflow, goods left at the end), unless the Judge shows breaking them pays | Rules |
| **Speed up** | Make good choices without simulating every time | A small model trained on the Judge's choices |

**No over-fitting.** The Judge never sees an opponent's code: it previews against a stand-in that represents the
opponent only through the shared market (how much of each product it will sell and when), estimated from what is
visible in the current game. Opponents are split:

| Used while building and tuning | Held out until the final tests |
|---|---|
| Metav4, F1, our template agent | F4, the counter versions, older public agents, coded submissions, any runnable top agent, fresh seeds |

A change counts only if it also holds against the held-out group.

**Decision 2026-10-22 (Eugene): the 4th-place agent is our teacher and progress yardstick, never an opponent in
reported results.** We learn its worker choices on our own farm, where it can be asked what it would do in the
states our agent reaches (labels plus correction loop), and every bench reports the share of its same-morning
lead we have closed. Results against it are not evidence of strength. The two 5th-place agents stay held out
permanently; using any held-out agent as a teacher needs an explicit decision. Its licence (CC BY 4.0) requires
credit in the write-up; its code stays on the data drive and is never copied into ours.

**Decision 2026-10-22 (Eugene): how the worker model proceeds** (measurement: `reports/2026-10-22-measure-first.md`,
the 4th-place workers alone are worth +$756 of its +$942 a day on our farm, its market orders nothing).
- Ranker v2 and the correction rounds learn from the 4th-place agent on our farm **only**. Top-team data comes back
  later, after the plan layer (mix, herd, layout, market) has been learned.
- Target before moving on: our workers do about as much work as its workers, in a similar order (work turns,
  job mix, agreement with its choices), and close **at least half of its lead in money (+$470 a day)**.
- Correction rounds use all 552 mornings (24 games x days 6-28); more if the results call for it.
- If the execution check shows walking mistakes, route-finding is fixed before any retraining.
- **Decision 2026-10-24 (Eugene), correction rounds:** v3 trains on L1 + L3 pooled with equal weight per
  decision (L3 = the 4th-place agent taking over from our model's states mid-day; leaning on L3 more may come
  later). Same held-out games 10320-10324 throughout. Stop rule "A+": at most two correction rounds (v3, v4);
  stop after round 1 if v3 gains less than +$100 a day over v2 on the bench; if v4 reaches +$350 to +$469 a day,
  one polish retrain without new data (heavier L3 weight, sharper features such as the price signal for
  collecting animal products), then stop or proceed; below +$350, stop and take the fallback.
- **Decision 2026-10-25 (Eugene): v3-fw is the baseline for days 6-28 only** (template workers outside them); next steps
  for workers and the plan stage wait for a breakdown of where the teacher still leads.
- **Fallback if this bears no fruit:** put our agent into the top teams' own replays (same-morning test on their
  farms) and compare with their recorded day, so it learns their habits on their layouts; then copy those
  layouts; then learn how to reach them (the planting plan).

**Top teams as the anchor.** Proposals come from patterns in their games (layouts, mixes, timings in similar
situations); the Judge moves away from them only when the preview clearly shows it pays. Their play is our source
of ideas, credited, never their code.

**Learned opener.** The opener adapts to cash and opponent like the rest of the game; it is part of Propose, not a
frozen script. End-of-game selling stays as rules.

## 4. What the write-ups taught us (read 2026-10-15 and 2026-10-17)

| Lesson | Source (final rank) | Use here |
|---|---|---|
| A planner that schedules each tile's future as a dated **project** (plant, water, fertilize, harvest, with inputs and outputs), combines projects with **labour shadow prices** and **market marginal values**, checks routes, plans at dawn and revises hourly | 28th | The model for our Judge: cheaper than simulating everything, and it looks days ahead |
| A **learned opening** (days 0-9) handing over to the planner, with the planner's trackers warmed on the opening's history | 28th | Our learned opener and handover |
| Value a farm by the work and income still ahead, not by cash | 28th | The Judge's score |
| **Choose the teacher by a consistent strategy**: compare submissions by what they plant and when, whether they buy land, how they earn; mixing strategies averages them into nonsense | 27th, 7th, 4th | Pick teacher submissions before learning any patterns |
| Validation loss does not predict playing strength; judge by games | 27th, 48th, 7th | Every model is chosen by paired games |
| A 0.86M-parameter model cloned from 611 games beat a community heuristic 85% of the time; about $30 of GPU | 48th | Small models and modest data are enough for our target |
| Reinforcement learning helped but was unstable ("policy basins": training polishes familiar patterns, rarely finds new ones) | 48th, 7th | Keep it optional and late |
| Label what the engine executed, not what was ordered; guard states the teacher never visited (feed guard) | 4th, 7th | Labels and guards |
| The engine pairs both players' market orders by position in the list: whoever lists a product first sells it first (worth $0.4-0.6k a game against the top 3) | 4th | A cheap selling rule to test early |
| Keep two or three ideas alive, each with a fallback, a current best and an experiment | 5th | How we run the project |

Runnable strong agents may exist: the 5th-place repository includes its submitted archives, and the 4th-place
team published its trained agent. If their licences allow, they become held-out opponents (not targets).

## 5. Stages and stop points

### Stage 0: data and teacher (about 2 weeks)

- Replays on the external drive (6,532 top-team games; see `manifests/replays.csv`), plus the reference team's
  earlier submission 56701470.
- Exact replay through the engine: which actions took effect (labels), and each seat's actual sales by product and
  hour (the stand-in opponent's training data).
- Tables as Parquet on the drive, queried with DuckDB.
- **Teacher choice:** profile submissions by strategy (land days, crop mix by day, herd, how money is earned) and
  pick consistent ones, as the 27th-place team did.

### Stage 1: preview harness and a first Judge (about 2 weeks)

- Copy a game at any morning; simulate our farm forward a day (or more) with the stand-in opponent; measure speed
  and check the preview against what actually happened.
- First Judge: a handful of rule-based plan variants each morning (for example more animals or more crops, land
  now or tomorrow, one more hire). Does looking ahead beat the template agent on the tuning group, then on the
  held-out group?
- Stop: if the preview is too slow or too inaccurate to rank plans, fix that before anything else.

### Stage 2: proposals from the top teams, and the stand-in opponent

- Learn plan patterns from the chosen teacher (gradient-boosted models first): what to plant where and when, herd
  and land decisions, the opener.
- Opponent sales model: from what is visible, how much of each product the opponent sells per hour.
- The Judge ranks these proposals.
- Stop: if learned proposals do not beat rule-based ones in games, keep the rules.

### Stage 3: tuning and the work layer

- Tune the small numbers over many games (tuning group only).
- Replace the step-by-step job scoring with project-based work planning in the style of the 28th-place planner, or
  a learned ranker over all legal jobs; decide by games.

### Stage 4: speed up and optional learning from its own play

- Train a small model on the Judge's choices; optional reinforcement fine-tune only if the rest works.

Final test at every stage that counts: paired games against the held-out opponents, by scenario.

## 6. Timeline (part-time)

| Weeks | Stage |
|---|---|
| 1-2 | Stage 0 |
| 3-4 | Stage 1 |
| 5-7 | Stage 2 |
| 8-10 | Stage 3 |
| 11+ | Stage 4, write-up before the January deadlines |

## 7. Working rules

- Code and small results in git; replays, tables and models on the external drive (`src/kagml/paths.py`).
  Backup (decision 2026-10-22): push to a private GitHub repository once Eugene has created it; no remote yet.
- The template agent stays pinned in `vendor/`; changes go in our own copy behind switches.
- Every claim is measured with paired seeds, both banks reported, split by scenario, held-out opponents checked.
- Write-ups are reading only, credited; no code from repositories without a licence.
- Split: Claude builds the harness, Judge and agent; Codex does data, replay checks and evaluation; Eugene chooses
  the teacher, studies the top teams' patterns and watches games where the agent and the teacher disagree.

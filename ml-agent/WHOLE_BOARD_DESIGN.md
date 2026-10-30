# Whole-board network for our workers: first design (2026-10-25, for review)

Decision (Eugene, 2026-10-25): skip the in-between per-turn tree model and go straight to a whole-board network;
the plan costs us too (from replay review) but is not measured now. Baseline to beat: **v3-fw on days 6-28**.

## 1. Goal and scope

- **v1 controls the workers only**, on days 6-28, exactly where v3-fw works now. The template keeps the plan
  and the market orders, and the workers on days 0-5 and 29. That keeps one change at a time and makes the
  result directly comparable with v3-fw and with the +369 a day that the teacher's workers make over ours.
- **Later versions** add heads for the daily plan (seeds, animals, sales), then all days; the same network can
  grow into your three plan levels (section 10).
- We learn the 4th-place agent's **behaviour** (credited, CC BY 4.0), never its code or weights. Its published
  description told us the shape that works (one network over the whole board; for each worker in turn, a target
  and a job), not how to build it; our design below is our own.

## 2. What the network sees each turn (input)

Everything is a set of tokens; each token type has its own small encoder, then all tokens go into one shared
transformer, so every decision is made with the whole farm in view.

| Token | Count | Features |
|---|---:|---|
| Our tiles | 100 | kind (empty, locked, weed, crop type, pen/coop with animal type), crop age and days to next yield, units waiting / maximum, watered today, days dry, fertilized for how long, animal fed / cared today, days unfed, care bonus; **tonight's outcome** (dies / produces / doubles / escapes, loss if left: the features that helped v3); coordinates |
| Workers | up to 13 | position, bag contents, farmer or hand, last move direction, turns since last job |
| Global | 1 | day, hour, turns left, cash, prices and market stock of all 9 products, shed contents, seeds in stock, workers hired today, land owned, opponent's cash and visible farm counts |

**Position matters most for routing**, so attention gets a learned bias by distance between tokens (tile to tile,
worker to tile), not just coordinates as numbers.

## 3. What it outputs (per worker, in order)

Decided **worker by worker within a turn**, as the engine applies them and as the teacher does; each worker sees
the whole board **and the decisions already given to the workers before it this turn** (no two workers chasing
the same job, the shed and seeds shared correctly).

| Head | Output | Label (from the teacher's play) |
|---|---|---|
| Command (main) | stay, north, south, east, west, or a legal job on the current tile (water, harvest, plant + crop, fertilize, feed, care, collect fertilizer, dig, build, pickup / drop / place at the shed) | the command the teacher issued that took effect |
| Target (helper) | a tile, or stay | the tile of the worker's next job (known in hindsight); trains the network to hold an intention, so it does not flicker the way re-deciding v3 did |
| Amount | 1-5, for pickups and shed placements | the teacher's amount |

Illegal choices are masked out before choosing (the engine's own rules, the same legality as the current
candidate list). At play time the command head decides; the target head only helps learning.

## 4. Model

- Per-token-type encoders into width 128, one transformer of about 4-6 layers and 4 heads over about 115
  tokens, distance-based attention bias.
- A small decoder per worker: attends to the board and to embeddings of the earlier workers' decisions this turn.
- Size about 1-3 million weights: small enough for CPU play within the time limit (the teacher's larger network
  takes 85-190 ms a turn on this laptop), big enough for about a million training decisions.

## 5. Data

| Source | Turns played by the teacher | Worker decisions (about) |
|---|---:|---:|
| L1 (its own days on our farm, days 6-28) | 13,248 | 150,000 |
| L3 round 1 (after v2 played part of the day) | 30,912 | 340,000 |
| L3 round 2 (after v3-fw) | 30,912 | 340,000 |
| Edge days 0-5 and 29 (L1 + L3) | 13,320 | 140,000 |

Only the teacher's turns are labels (in L3, from the takeover on). More can be generated cheaply with the
existing tools. Split by game, as now: training 10301-10314, analysis 10315-10319, test 10320-10324 (test used
only to report, never to choose).

**Codex builds the turn-level dataset** (section 9): one record per turn with every token's features, each
worker's label and its legality mask, checked against the engine.

## 6. Training

- Copying (cross-entropy on command, target and amount; the earlier workers' true decisions fed in while
  training), on the laptop GPU (RTX 3070, 8 GB): a model this size trains in hours, not days.
- **Cloud is not needed for v1.** If it ever is, Kaggle notebooks give about 30 free GPU hours a week and Google
  Colab is similar; the cost is uploading the dataset (a few GB).
- Correction rounds afterwards with the takeover tool (our network plays part of the day, the teacher takes over).
- Learning from game outcomes (as the teacher did after copying) is a much later, optional step.

## 7. How it is judged (in this order)

1. **Offline**, analysis games: command agreement with the teacher per job kind; how often the predicted target
   is kept while walking (stability).
2. **Same morning, workers only** (template plan and market orders), analysis mornings: share of the +369 a day
   closed. Pass mark for v1: **beat v3-fw's workers**; target: close at least half.
3. **Full games**, fresh seeds, both seats, days 6-28: against v3-fw, the template and Metav4; then the held-out
   5th-place agents.
4. Time per turn on CPU: median under 300 ms, no turn over 1 s.

## 8. Milestones and stop rule

| Milestone | Content | Estimate |
|---|---|---|
| M0 | This design reviewed; Codex's turn dataset built and checked | 2-3 days |
| M1 | Model and training; offline numbers | 3-4 days |
| M2 | Player (template plan + network workers); same-morning bench | 1-2 days |
| M3 | One correction round; full games | 2-3 days |

**Stop rule:** if v1 does not beat v3-fw's workers on the same-morning test after one correction round, stop and
rethink before investing further. v3-fw stays the baseline throughout.

## 9. Work split

- **Codex:** the turn-level dataset (tensors per turn, labels, legality masks, checks against the engine); the
  counting tables for this design (command mix, how often the teacher changes target mid-walk, how often it does a
  job on the way, worker-by-worker order effects); more teacher data if the first model needs it.
- **Claude:** model, training, decoding with masks, the player, benches, correction rounds, reports.

## 10. Assumptions to challenge

1. Copying the teacher's per-turn commands with a whole-board view will reproduce most of its worker advantage,
   even though its hidden memory (flow tracker, market accumulators) is not visible to us.
2. About a million decisions is enough data for a network this size; if not, we generate more.
3. Deciding workers in order, each seeing the earlier ones' decisions, gives the coordination the teacher has.
4. The template's plan and market orders are a fair test bed: the network learns from the teacher's choices on
   the template's farms (L1/L3), so it should cope with them.
5. Later, the same network can take over the daily plan (seeds, animals, sales) and then the farm shape: your
   three plan levels, learned rather than hand-built.

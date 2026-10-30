# Plan and market heads for the whole-board network: first design (2026-10-26)

Agreed order (Eugene, 2026-10-26): workers are near their ceiling under the template's plan (board-v5: 81% of the
teacher's workers' edge on the same mornings, level with v4 in full games); the remaining full-game gap (about
26,000 margin a game) is mostly the plan. In the teacher's architecture the plan **is** its market output plus its
workers' choice of what to plant and build where. Our network already chooses the workers' crops and builds; this
adds the market output.

## What the heads decide

Every turn, for each of the 28 order tokens of Codex's vocabulary (`reports/PLAN_MARKET_VOCAB.csv`): sell per
product (9), buy seed per crop (5), buy animal per kind (3), buy product (wheat, fertilizer), buy land, hire. Each
token's output is a **quantity class**: 0, 1, 2, 3, 4, 5, 6-7, 8-10, 11-15, 16-25, 26+ (played as 0, 1, 2, 3, 4,
5, 6, 9, 13, 20, 30). Unsupported tokens (buy product other than wheat and fertilizer) are fixed at 0.

Measured from the teacher's orders (600 training day-runs): about half of all turns have at least one order;
sells are frequent and sized (wheat median 8, up to about 50 per order), seed and animal purchases small (1-2),
hiring comes in batches (median 6 workers in one turn).

## Model

- One extra head on the **global token** after the shared transformer (it has attended to every tile, worker and
  the market): an MLP to 28 x 11 logits. Trained **jointly** with the worker heads, starting from board-v5's
  weights, so the market and workers share one view of the farm (as the teacher does).
- Labels: the teacher's issued quantities (`units_issued`; the engine trims requests it cannot fill, as it does for
  the teacher). Turns without a market label (none now except where noted in the manifest) train the workers only.
- Loss: cross-entropy per token, averaged; non-zero labels counted more (they are rare) so the head does not learn
  "never order anything".

## Play

- Option `market` on the player (`net:<model>:market`): on network days (6-28 at first), the network's orders
  replace the template's: **sells first, then buys** (a sale can finance a purchase; the engine processes orders in
  list order), at most 10 orders, quantities from the class played values.
- The template's orders stay on days 0-5 and 29 until the opener and endgame models exist.

## How it is judged

1. Offline, on **analysis** (old) and **analysis2** (15 scenario-balanced seeds) separately: per token, how often
   the network orders when the teacher does, and the size class agreement.
2. Full games on fresh seeds 20001-20024 and on the 15 analysis2 seeds, both seats, against Metav4: share, wins,
   margin, **by scenario**; against board-v5 (template market) paired by seed.
3. If it helps: a correction round with the market on (the teacher takes over our plan's situations), then the
   held-out opponents.

## Assumptions to challenge

1. Copying the teacher's orders on **our** farms (L1/L3) plus its own full games is enough to learn its plan; the
   plan only pays off if the workers carry it out, and both are trained together.
2. Quantity classes per token (no explicit budget) are good enough; the engine refuses what we cannot afford.
3. Replacing the template's market on days 6-28 only, while it keeps the opener and endgame, does not create a
   mismatch at the handovers (day 6 and day 29).

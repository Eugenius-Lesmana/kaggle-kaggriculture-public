# Next step: the three options in detail, for review (2026-10-25)

Starting point: **v3-fw on days 6-28** (template plan, template market orders, template workers on days 0-5 and
29). Full games vs Metav4: share 0.966, 16/48 wins. Teacher: 1.425, 48/48. Each option below lists what we know
(measured), what I am **assuming** (please challenge these), the work, how it is judged, and when to stop.

## Facts all three options rest on

| # | Fact | Evidence |
|---|---|---|
| F1 | Under our plan and market orders, the teacher's **workers** beat ours by +369 a day (se 54) on the same mornings | D6 arm 4 vs v3s-fw, 105 analysis mornings |
| F2 | The teacher's **market orders alone** add little within a day (+152 a day over its workers under our orders; swap test: its market orders on our farm -40) | D6, swap test |
| F3 | The teacher's lead **grows when it keeps control for several days** (+619, about +1,000, about +1,350 a day); one teacher day followed by the template leaves no extra value | Codex D4 |
| F4 | In full games the teacher plants **more strawberries early** (19.5 vs 12.4 tiles on days 6-11), keeps **12-14 tomato tiles** mid-game, has **more geese**, switches to **carrots** at the end; land and hires are identical | `reports/2026-10-25-gap-table.md` |
| F5 | Metav4 loses 17,349 a game against the teacher through **lower prices** for strawberries, milk and wool on days 18-29; the teacher's matchup has about 22 more strawberries, 10 more milk and 8 more wool in market stock by day 18 | Codex M |
| F6 | Tweaks inside the per-worker job ranker (shed rule, sweep features, weighting, planting from the plan, more data rounds) no longer move value | `reports/2026-10-25-micro-fixes.md` |
| F7 | Learned workers on days 0-5 lose to the template's opener even with teacher examples | v3e-fw full games |

---

## Option A: the plan stage (crop mix, herd, timing)

**Goal.** Produce more strawberries, milk and wool, and produce them earlier (F4, F5); keep our v3-fw workers.

**What changes.** Only the plan: which seeds and animals the template buys and when, and its layout (which crop or
pen on which tile). Workers stay v3-fw on days 6-28; market selling stays the template's at first.

**Approach, in two steps.**

- **A1, quick probes (rules, about 2-3 days).** Change one plan decision at a time in our own copy of the
  template (never `vendor/`), shaped on what the teacher does (F4):
  1. more strawberry tiles on days 6-11;
  2. more geese (and check cows/sheep: milk and wool are two of the three products in F5);
  3. keep tomato tiles mid-game;
  4. switch empty tiles to carrots in the last days.
  Each probe is judged in full games. This tells us which plan levers are worth anything before building a model.
- **A2, learned plan (about 1-2 weeks, only if A1 shows the plan matters).** Learn the plan decisions from the
  teacher's own games: which crop for each empty tile, which animals to buy on which day, how many seeds. Data:
  the teacher's full games (we can run as many as needed; it plays from day 0 with its own plan) plus L1/L3
  (its market orders on our farm). The model replaces the template's buying and layout; the template's selling
  stays until shown otherwise.

**How it is judged.**
- **Full games only** (F3: plan effects compound over days; one-day tests cannot see them; F2 shows they look
  like nothing within one day). Fresh seeds, both seats, against Metav4.
- Choose on seeds 20001-20012, confirm on 20013-20024 (new seeds, so a change is not fitted to one set), then the
  held-out opponents (the two 5th-place agents) before calling anything a result.
- Report: our bank, Metav4's bank, share, margin, wins; plus strawberries / milk / wool in market by day 18 (F5).

**Assumptions to challenge.**
1. The plan is a large part of the remaining full-game gap. Evidence: F4, F5. Counter-evidence: F1 says a large
   part is workers; the two are entangled (more strawberry tiles only pay if they are watered and harvested).
2. v3-fw's workers cope with a different plan. They learned from the teacher's choices on the template's farm;
   a different crop mix and herd is a new situation (drift again). If not, A needs new L1/L3 data on the new plan.
3. Copying the teacher's plan shape helps **our** agent; the teacher's plan may only pay with the teacher's
   workers.
4. Rules first is acceptable here even though the template stalled on hand rules: the probes are to learn which
   levers matter, not to be the final plan.

**Stop rule (proposal).** If no single A1 probe improves full-game margin by at least about 2,000 (about twice its
standard error) on the confirmation seeds, the plan is not the lever right now; go to B.

---

## Option B: a per-turn model that moves all workers together

**Goal.** Close the +369 a day worker gap (F1) by copying how the teacher actually moves its team, which the
job ranker cannot express (F6): sweeping along rows, jobs on the way, workers keeping their own areas,
coordination.

**What changes.** The workers' controller. Instead of "each worker picks a destination job, then walks", the model
outputs **every worker's command every turn** (a move or a job on the current tile), deciding all workers together.

**Approach, in two steps.**

- **B1, local per-turn model (about 1 week).** For each worker each turn, predict the teacher's actual command:
  one of {north, south, east, west, stay} or the job on the current tile (water, harvest, fertilize, feed, ...).
  Features: the worker's surroundings (tiles within a few steps: what needs doing and by when), the v3-fw
  ranker's preferred destination (so long-range intent is kept), where the other workers are and what they
  were just told this turn (workers decided one after another, so later workers see earlier ones' moves).
  Model: gradient-boosted trees, as now. Data: every executed teacher turn in L1, L3 (two rounds) and the edge
  sets: about 70,000 turns x about 12 workers. Correction rounds as before (L3 with the new player).
- **B2, whole-board neural model (weeks, only if B1 falls short).** One network sees the whole farm and outputs
  all workers' commands, as the 4th-place model does. CPU only on this laptop; slower to train and iterate.

**How it is judged.**
- First, same-morning worker-only test (template plan and market orders, as F1): share of the +369 closed.
  Target: at least half (+185 a day) on the analysis mornings, then the test games.
- Then full games on days 6-28 against v3-fw, same protocol as A.
- Per-turn time must stay within the limit (today's ranker already has occasional turns over one second).

**Assumptions to challenge.**
1. The teacher's per-turn behaviour is learnable from what we can see. Its own memory (flow tracker, market
   accumulators) is hidden from us; Codex found it changes its answers in our states.
2. Deciding workers one after another, each seeing the earlier ones' moves, is enough coordination; the
   teacher decides them jointly.
3. B1 does not simply rebuild the same ceiling as the ranker (F6). The difference is that it learns the step,
   not just the destination; if the steps it learns are still "walk to the best job", nothing changes.
4. This is still "our own work": we learn the teacher's behaviour (CC BY 4.0, credited), never its code.
5. The gap is worth the effort: about 8,500 a game before compounding (F1 x 23 days), against weeks of work.

**Stop rule (proposal).** If B1 does not close at least a third of the +369 on the analysis mornings after one
correction round, do not start B2 without a new decision.

---

## Option C: top-team layouts (last resort)

Put our agent into the top teams' own replays (same-morning test on their farms), learn their habits on their
layouts, then copy the layouts, then learn how to reach them. Kept as the last option, as you said: it moves
away from our own farm and depends on recordings that cannot be asked questions (no correction rounds).

---

## How A and B fit together

- They change different parts of the agent (plan vs workers) and can be measured separately: A in full games
  with v3-fw workers, B in same-morning worker-only tests under the template plan.
- Their effects are entangled (F5 needs both more premium crops **and** the work to grow them). If both work,
  the workers must be re-trained on the new plan's situations at the end.
- My suggested order, for you to judge: **A1 probes first** (a few days, cheap, and they test the macro story
  Codex measured), **then B1**. If A1 shows nothing, B1 straight away.
- Codex can run all full-game probes (its tool, 2 workers) while I build B1, so both move in parallel.

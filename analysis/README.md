# Analysis

Dated lab notes from the competition (September 2026). They are copied **unchanged** from our working
repository, except that a few links now point into this repository. Each note was true when written. **Later
notes supersede earlier ones**; the corrections are listed at the bottom.

Top-ranked leaderboard teams are anonymised as **Team A–G**. The same letter is the same team in every note and
evidence file. Kaggle episode and submission IDs are kept as evidence references.

Method, in one paragraph: every comparison is **paired**: the same seeds, both seats, 80 games per cell, with a
fresh seed range to confirm anything we kept. We report our bank and the opponent's bank separately, because
markets are shared and a change can win by lowering the opponent's income. Replays were replayed through the
real engine, and each step was checked against the recorded bank before any number was counted.

## Path map

The notes use the working repository's paths.

| In the notes | Here |
|---|---|
| `agents/ours/h1-counter-f4-racewheat-look10-snipe-candidate/` | [`agent/`](../agent/) |
| `agents/ours/v0.11.0-candidate/` | [`next-agent/planner/`](../next-agent/planner/) |
| `evaluation/…` | [`evidence/…`](../evidence/) (planner experiments: [`next-agent/evidence/`](../next-agent/evidence/)) |
| `scripts/screen.py`, `research/tools/…` | [`tools/`](../tools/) |
| `research/intake/…` (replays, notebooks) | not published |
| `.cache/…` (scratch scripts) | not published; the scripts that matter are in `evidence/*/` |
| `dev/eugene-…` branches | working-repository branches. Their notes and evidence are copied here. |

## `leaderboard/`: who is on the ladder, and why we lose

| Note | What it shows |
|---|---|
| [`LEADERBOARD_CENSUS_2026-09-26`](leaderboard/LEADERBOARD_CENSUS_2026-09-26.md) | 137 mid-ladder teams. About 80% play the Metav4 tape family; none run an exact public file. F1 was the strongest public agent that week. |
| [`LADDER_F1_2026-09-27`](leaderboard/LADDER_F1_2026-09-27.md) | Why F1 + counter stalled: near-copies that **sell a step earlier**. Local stand-ins beat us ~90%, reproducing the ladder. Maximum selling costs wins against older families. |
| [`H1_COUNTER_F4_2026-09-27`](leaderboard/H1_COUNTER_F4_2026-09-27.md) | F4 beats F1 head to head but beats older families less reliably: results are non-transitive. |
| [`F4_RACE_2026-09-29`](leaderboard/F4_RACE_2026-09-29.md) | F4 + counter against the live ladder: close F4 forks are the problem (15–25–1). Copying their edits fails. The race fix and the wheat overlay win 66–14. |
| [`F4_RACE_LOOKAHEAD_2026-09-29`](leaderboard/F4_RACE_LOOKAHEAD_2026-09-29.md) | The look-ahead dose (3, 6, 10, 20, 40, 720): where more selling stops paying. |

## `our-agent/`: the layers we added

| Note | What it shows |
|---|---|
| [`H1_COUNTER_2026-09-25`](our-agent/H1_COUNTER_2026-09-25.md) | The counter: why the engine's market order gives an edge to a player that best-responds to the mirror's *final* orders. 116–4 against Metav4 clones; no change elsewhere. |
| [`H1_COUNTER_F1_2026-09-26`](our-agent/H1_COUNTER_F1_2026-09-26.md) | The same counter ported onto F1: 77–3 against the F1 mirror, no change against F2 or Metav4. |
| [`F4_WHEAT_RACE_2026-09-29`](our-agent/F4_WHEAT_RACE_2026-09-29.md) | The wheat round-trip: a same-turn sale at the lifted price. 48 new wins and none lost against F4 + counter. |

## `top-agents/`: what the top teams do

| Note | Main finding |
|---|---|
| [`TOP3_MACRO_PLAN_2026-09-24`](top-agents/TOP3_MACRO_PLAN_2026-09-24.md) | The top four share one lineage: the same day-0 opener in all 46 games, land bought at steps 150 / 220 / 254, cells replanted the next step, shop-triggered product modules. |
| [`TOP4_MIDGAME_RESEARCH_2026-09-24`](top-agents/TOP4_MIDGAME_RESEARCH_2026-09-24.md) | Land timing, an animal core around the shed with strawberries on the rim, how they react to new shops and to prices. |
| [`TOP3_MARKET_BEHAVIOUR_2026-09-24`](top-agents/TOP3_MARKET_BEHAVIOUR_2026-09-24.md) | What they buy and sell, and when: sales on a fixed schedule by product and hour, cash run to $0, fertilizer never bought. |
| [`MICROTAPE_STUDY_2026-09-28`](top-agents/MICROTAPE_STUDY_2026-09-28.md) | A worker's route repeats **across games, not across days**. Fertilizer is applied on the trip where it was collected. Animals are let go when their product falls below ~15% of its usual price. |
| [`MODES_STUDY_2026-09-29`](top-agents/MODES_STUDY_2026-09-29.md) | There are no discrete shop modes. Shop demand tilts product shares (carrot, tomato, sheep) and conversion happens at harvest. The opener and land schedule changed between 24 and 29 September. |
| [`ROUTE_BACKBONES_2026-09-29`](top-agents/ROUTE_BACKBONES_2026-09-29.md) | A route "backbone" can be extracted, but a bare cell-state rule reproduces only ~68% of core actions. |
| [`PRODUCTION_GAP_2026-09-30`](top-agents/PRODUCTION_GAP_2026-09-30.md) | Where the top agents' extra units come from: +703 units a game, 54% from capacity and 46% from yield per occupied day. |
| [`MARKET_EDGE_2026-09-30`](top-agents/MARKET_EDGE_2026-09-30.md) | Their edge over our planner is **units to sell, not prices**: +$41.4k from units and −$1.8k from price. A fourth top team wins on product trading. |
| [`YIELD_DRIVERS_2026-09-30`](top-agents/YIELD_DRIVERS_2026-09-30.md) | Fertilizer timed to the yield window is the strongest measured driver of top wheat and strawberry yield. |

## Corrections between notes

- **"Execution gap".** The 24 and 25 September notes ([`TOP3_MACRO_PLAN`](top-agents/TOP3_MACRO_PLAN_2026-09-24.md),
  [`V010_TOP4_TRANSPLANT`](../next-agent/docs/V010_TOP4_TRANSPLANT_2026-09-25.md)) said our planner wasted worker
  time and could not execute the top plan. The 30 September full-game diagnostic
  ([`EARLY_LABOUR`](../next-agent/docs/EARLY_LABOUR_2026-09-30.md)) shows it completes almost every job that
  falls due. The idle time is early, where the plan has no work. The gap is in the plan.
- **"The opener is fully deterministic".** [`MODES_STUDY`](top-agents/MODES_STUDY_2026-09-29.md) qualifies it:
  exact full actions match the majority 67.5% of the time on day 0 and 17–45% on days 1–5. The route and resource
  schedule are recognisable, and the schedule changed by 29 September.
- **Submission advice.** [`LADDER_F1`](leaderboard/LADDER_F1_2026-09-27.md) recommended F4 + counter.
  [`F4_RACE`](leaderboard/F4_RACE_2026-09-29.md) replaced that with race + wheat, and
  [`F4_RACE_LOOKAHEAD`](leaderboard/F4_RACE_LOOKAHEAD_2026-09-29.md) with look-ahead 10. The final agent adds the
  snipe lines ([`agent/README.md`](../agent/README.md)). The ladder confirmed none of these steps: race + wheat rated
  about 1,898, look-ahead 10 1,872.3 and look-ahead 10 + snipe 1,776.9 (both unsettled), against about 2,100–2,200 for F4 + counter.
- **"Metav4 is outdated".** True on 26 September. It was superseded by F1, then F4, within days.
- **The counter's value.** It gains only against exact copies of its own base, and the census found none. It is
  insurance, not a ladder gain ([`H1_COUNTER`](our-agent/H1_COUNTER_2026-09-25.md)).

The planner experiments are in [`next-agent/`](../next-agent/).

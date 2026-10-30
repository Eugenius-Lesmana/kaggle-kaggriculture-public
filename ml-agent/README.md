# ML agent: a hybrid agent at 0.91 of a 5th-place bank (2026-10-30)

After the competition we built a second agent: our rule-based template plans the farm and a transformer, trained by
imitating the 4th-place agent, runs the workers and the market. This folder holds its write-up, code and design notes.
It is chapter 4, the final result, of the [main README](../README.md); chapters 1-3 cover the competition, our
planner and the template agent.

**Result.** Our final agent, `net:board-p5:market:overflow:endmask:endwork:end29`, finishes with **0.913 of the bank of
fifth-nflow** (the published 5th-place agent) over 78 full games: 96,943 against 106,188 a game, 3 wins. Our
rule-based template agent, the starting point, reached 0.695 against the same opponent. The 4th-place agent we learned
from reaches 1.020 (42 of 48 wins).

| Agent | Share of fifth-nflow's bank | Wins | Games |
|---|---:|---:|---:|
| Template (rules only) | 0.695 | 0 | 48 |
| board-v5 (network runs the workers) | 0.776 | 0 | 48 |
| board-p2 (+ network market orders, correction round) | 0.800 | 0 | 48 |
| board-p4 (+ two correction rounds against fifth-nflow) | 0.839 | 0 | 48 |
| board-p4 + end-of-game rules | 0.871 | 0 | 48 |
| board-p5 (+ focused correction round) | 0.910 | 2 | 96 |
| **board-p5 + day-29 sell rule (final)** | **0.913** | 3 | 78 |
| Teacher (4th place, for reference) | 1.020 | 42 | 48 |

Share = our total bank / the opponent's total bank over the same games. All games use seeds 20001-20048, both seats,
against live fifth-nflow.

## 1. Starting point

During the competition we built a rule-based agent (the "template"): it plans the farm (what to plant, which animals,
when to buy land), scores worker jobs step by step, and sells by fixed rules. After the competition it stalled at
0.913 of Metav4's bank, a strong public agent, and 0.695 of fifth-nflow's. The published write-ups showed why: the top
teams ran neural policies trained on replays, some with self-play reinforcement learning, not hand-written rules
(`reports/2026-10-22-teacher-strength.md`).

The project goal was to keep the parts of the template that work and learn the rest from a top agent.

## 2. What we built

**A hybrid agent.**
- **Days 0-5 and day 29:** the template plays. It opens the farm well and liquidates at the end.
- **Days 6-28:** a whole-board network decides every worker's command and the market orders.
- **After the network:** a few rules that every top team also found worth adding (section 4).

**The network** (`src/kagml/board_net.py`, `src/kagml/board_features.py`): a transformer over 100 tile tokens, up to 14
worker tokens and one global token, with attention biased by distance on the board. Workers decide in order, and each
sees the earlier workers' choices this turn, so two workers do not chase the same job. A second head on the global
token sets the market orders (28 order types, 11 quantity classes). Final size: width 192, 6 layers, 2.4 M weights.

**The teacher.** The 4th-place agent (published under CC BY 4.0) was used as a black box only: it plays our saved game
states and its choices become training labels. Its code was never copied into our agent.

**Training: imitation plus correction rounds (a DAgger-style loop).**
1. Copy the teacher's choices from its own games and from games where it takes over our farm.
2. Let our agent play; at chosen moments the teacher takes over for a few hours and we record what it would have done
   from our own (imperfect) positions.
3. Train on all of it, starting from the previous model; repeat.

Five rounds took us from board-v5 to board-p5 (`reports/2026-10-26-board-p2.md`,
`reports/2026-10-27-overnight-n1-n2.md`, `reports/2026-10-29-n3-focus.md`).

**Evaluation.** Every change is played over 48 full games (24 seeds × both seats) against live fifth-nflow and compared
seed by seed with the previous best. A change is kept only if the pooled margin is at least 2 standard errors above
zero and it is also positive on 24 fresh seeds (20025-20048) that played no part in choosing it
(`reports/2026-10-29-p5-mcal-fresh-seeds.md`).

## 3. What worked

| Change | Gain in margin a game (se) | Evidence |
|---|---:|---|
| Network runs the workers instead of the template's job scoring | share 0.695 → 0.776 | `reports/2026-10-26-status-summary.md` |
| Network places the market orders | +8,493 vs Metav4 (1,421) | `reports/2026-10-26-board-p1.md` |
| Correction rounds against fifth-nflow (p2 → p4) | +4,972 (1,560) | `reports/2026-10-27-overnight-n1-n2.md` |
| Sell what would be thrown away at night (overflow) | +3,130 | `reports/2026-10-28-rules-on-board-p4.md` |
| No purchases or work that cannot pay back before the end (endmask, endwork) | +340, +426 | same |
| Focused correction round on the costly afternoon hours (p4 → p5) | +3,536 pooled over 96 games (692) | `reports/2026-10-29-p5-mcal-fresh-seeds.md` |
| Day 29: sell right after each town purchase, spread over the day (end29) | +98 (40) | `reports/2026-10-30-end29.md` |

## 4. What did not work

Most mid-game rules lost money. The kept rules all act at the end of the day or the end of the game.

| Tried | Result (margin a game, se) |
|---|---:|
| Sell shop goods only right after the town buys (all days) | −2,774 (1,226) |
| Sell on a rising price (onlinesell) | −4,394 (1,186) |
| Buy wheat feed only for animals the stock cannot cover | −766 (1,318) |
| Sell orders sorted by price | −49 |
| Play-time logit adjustment | −442 |
| Market-head calibration (matching the teacher's order rate) | −27 pooled (616) |
| A separate endgame model from day 16 | +415 pooled (253), not confirmed |
| Another correction round (board-p6) | +618 pooled (661), new seeds −154 |
| A separate history-based market model (GRU) | failed its offline gate (order F1 61.7% vs 74.6%) |

Evidence: `reports/2026-10-28-rules-on-board-p4.md`, `reports/2026-10-28-online-selling.md`,
`reports/2026-10-29-market-calibration.md`, `reports/2026-10-30-n4-round.md`, `reports/2026-10-30-market-model.md`.

After board-p5, imitation stopped improving: the next correction round and the new market model both failed.

## 5. Where the remaining gap is

Against the teacher's games, our margin is about 13k a game lower: our bank is 7.4k lower and fifth-nflow earns 5.9k
more in our games (the market is shared, so the teacher's selling hurts fifth-nflow and ours does not).

- **Workers and market contribute about equally.** Swapping in one teacher day recovers about the same from its
  worker moves as from its market orders (+199 and +168 a game-day). Most of that gain is the opponent earning less
  (`reports/2026-10-30-swap-test.md`).
- **Selling.** Our units earn 9.6k a game less than fifth-nflow's in the same markets (the teacher's earn 0.7k more).
  Split by cause (`reports/2026-10-30-sell-split.md`, `-end29.md`, `-crash-split.md`):
  - fifth-nflow sells first after the town buys and takes the high prices (3.8k);
  - we sell more units into crashed late-game markets (4.2k), mostly because the farm produces more milk, wool,
    strawberries and fertilizer late in the game;
  - day 29 (2.8k), almost all inherited from earlier days.
- **Timing rules cannot recover much.** Of the 2.8k day-29 loss, only 0.6k was timing within the day, and the rule got
  about 0.1k. Holding crashed late-game sales could recover at most about 1.1k more than the teacher, an upper bound,
  below what our tests can detect. The rest is farm composition and fifth-nflow's own timing, which depend on
  decisions across the whole game.

## 6. Next step: reinforcement learning, and what it would cost

The method that got the top teams past this point is reinforcement learning from game results: start from the imitated
network, play many games, and push its choices toward those that led to better final banks. The 1st-place team
alternated imitation with self-play PPO over about 8.3 million games on about 7 A100 and 20 A30 GPUs on average. After
one imitation round, their model needed about 60,000 self-play games to become stronger than before
([1st-place post](https://www.kaggle.com/competitions/kaggriculture/discussion/745073)).

**Speed prototype** (`tools/batch_selfplay.py`, measured on this laptop: 16 CPU cores, RTX 3070 laptop GPU):
- The old evaluation setup plays about 110 games an hour on 8 workers. Of a 241 s game, 165 s is fifth-nflow's network
  and 55 s ours, both on the CPU, one game at a time; the engine is about 20 s.
- The prototype plays our agent against itself, many games in lockstep, with one batched GPU pass per turn. On 4 check
  games it reproduces the normal agent's final banks exactly.
- **Result: 1,058 games an hour on 8 processes**, about 10× the old setup. The remaining cost is CPU work, mostly the
  template planner (about 10 s of 14 s a game), which still runs on days 6-28 although its moves there are replaced.
  Skipping it would probably give about 1,500 games an hour (not tested).

**Estimate (not measured).** At 10-15k games a night, a first gain might appear after 50-100k games (3-7 nights), and
0.94-0.95 would probably need 200k-500k games (weeks), plus about a week of building the training loop. Self-play
might also not transfer to beating fifth-nflow. We stopped here.

## 7. Caveats

- One opponent. The final agent was measured against fifth-nflow only, not against Metav4 or the other 5th-place
  agent.
- Selection. Most keep or drop decisions were made on seeds 20001-20024; fresh seeds 20025-20048 confirmed the main
  ones (board-p5 and end29).
- The end29 run was stopped at 78 of 96 games; 38 seeds have both seats.
- Shared markets make the opponent's bank depend on our selling, so a share change can come from either side.

## What is in this folder

```
README.md               this write-up
WHOLE_BOARD_DESIGN.md   design of the whole-board network
PLAN_HEADS_DESIGN.md    design of the market head
PLAN.md, PLAN_WORK_MODEL.md, WORK_MODEL_FEATURES.md   the original plan and the earlier job-ranker stage
src/kagml/              the agent: network (board_net.py), encoder (board_features.py), player and rules (net_player.py)
tools/                  training, correction rounds (takeover_labels.py), full games (run_full.py), paired
                        comparison (paired_runs.py), diagnostics, the RL speed prototype (batch_selfplay.py)
reports/                dated lab notes behind every number above
vendor/template_agent/  the rule-based template agent the hybrid builds on (ours, Apache-2.0)
```

Not included: model weights, training datasets, replays and game results (tens of GB), and the published agents of
other teams (download them from their authors). The code expects them under a data folder set with `KAGML_DATA`
(see `src/kagml/paths.py`); `<data>` in the notes means that folder.

## Credits

- Teacher: the 4th-place team's published agent (CC BY 4.0), used as a black-box labeller.
- Opponent: the 5th-place team's published agent (MIT), used for evaluation only; "fifth-nflow" is our label for it.
- Lessons on post-network rules and selling from the published write-ups of places 1, 3-7, 9 and 10.
- Built with Claude (Anthropic) and Codex (OpenAI) as coding agents; all results come from our own measured runs.

# Status summary (2026-10-26, evening)

## Goal

A hybrid agent (template rules plus a learned whole-board network) reaching a bank share of **0.9 or more against the
top agents** (the 4th-place teacher, the 5th-place agents fifth-nflow and fifth-n1). Metav4 is now only a quick check.

## Where we are: full games, seeds 20001-20024, both seats (48 games each)

| Agent | vs Metav4 share | vs Metav4 wins | vs fifth-nflow share | vs fifth-nflow wins |
|---|---:|---:|---:|---:|
| Template | 0.908 | 4 | 0.695 | 0 |
| board-v5 (network workers, template market) | 1.125 | 40 | 0.776 | 0 |
| board-p1 (+ network market orders) | 1.221 | 46 | 0.774 | 0 |
| **board-p2 (+ correction round 3)** | **1.242** | 45 | **0.800** | 0 |
| Reference (template days 0-5 and 29, teacher days 6-28) | 1.401 | 48 | 1.011 | 34 |
| Teacher | 1.425 | 48 | 1.020 | 42 |

Against fifth-n1: board-v5 0.753, template 0.684 (0 wins each). One board-p1 game against the teacher: 0.856.

## Where the gap is (package M Step B, Claude's computation from Codex's games; Codex's report pending)

| Difference (margin a game, se over seeds) | vs fifth-nflow | vs Metav4 |
|---|---:|---:|
| Teacher's own opener and liquidation (teacher minus reference) | 955 (532) | 1,556 (338) |
| **Our middle game, days 6-28 (reference minus board-p2)** | **23,620 (1,667)** | 11,802 (1,334) |

**The opener and liquidation are worth about 1,000-1,500 a game; the middle game is the whole gap.**

## Why (diagnosis and package M Step A)

- **Production volume** (`2026-10-26-market-competition.md`): against fifth-nflow the teacher sells 14-36% more of
  most products from about the same purchases; its extra volume also lowers fifth-nflow's prices in the shared market.
- **Plan agreement in our own positions** (Step A: the teacher's shadow decision at every turn of board-p1's games,
  days 6-28): market orders agree far less than offline, and least against fifth-nflow.

| | Recall | Precision | Size class hit |
|---|---:|---:|---:|
| Offline, analysis2 (teacher-like positions) | 0.806 | 0.715 | |
| Our games vs Metav4 | 0.662 | 0.608 | 0.707 |
| Our games vs fifth-nflow | **0.491** | **0.558** | 0.613 |

  Biggest disagreements (vs fifth-nflow): the teacher would sell **milk, melons, strawberries and tomatoes** when we
  hold them (recall 0.24-0.37) and would sell **less wheat** than we do (precision 0.31); it would buy more sheep.
  Shadow units repeat across turns while we hold stock, so read them as direction, not money. Builds and plantings
  mostly agree; we plant more wheat (155 against 129 a game) and fewer tomatoes (18 against 23).
- All our teacher data so far is the teacher playing **Metav4**; agreement drops against a strong opponent.

## Next steps (proposed)

1. **Step C** (Codex, queued): market labels for correction round 3; then board-p3 with market corrections in our
   own positions.
2. **Teacher data against strong opponents** (Codex): teacher full games against fifth-nflow and fifth-n1, and
   teacher days on our farms against fifth-nflow; then a correction round with fifth-nflow as the opponent.
3. **Deprioritise** the endgame and opener models (about 1,000-1,500 a game); package E stays paused.
4. Later: reinforcement learning on top, if copying stops improving.

# Whole-board network, first night (2026-10-25 to 26)

**Plain answer.** The whole-board network now runs our workers clearly better than the job ranker, and our agent
**beats Metav4 over full games for the first time**. **board-v4 with the end-of-day guard** (one correction round,
Codex's extra farms) reaches a **share of 1.085 of Metav4's bank and wins 38 of 48 games** on fresh seeds; its
margin is +10,992 a game over v3-fw (se 1,796), better on 22 of 24 seeds. That passes the plan's **"Target"**
level (share above 1.0, more than half the games won) against Metav4; the held-out opponents are not tested yet.

## 1. What was built

- **Codex N:** board encoder (`src/kagml/board_features.py`), legal-command masks checked against the engine,
  turn dataset: 88,392 teacher turns, 1,019,354 worker decisions; encoding about 1.2 ms a turn.
- **Codex N2:** 48 new template games (seeds 10401-10448, training only) and the teacher's days on them: 26,496
  turns, 315,782 decisions.
- **Claude:** the network (`src/kagml/board_net.py`: token encoders, distance-biased transformer, decisions worker
  by worker with the earlier workers' choices), GPU training (`tools/train_board_net.py`), the player
  (`src/kagml/net_player.py`, template plan and market, network workers on days 6-28), the end-of-day guard,
  and one correction round with the takeover tool (2,208 segments, 387,103 decisions, all validated).

## 2. Models

| Model | Size | Data | Command / target agreement (analysis turns) |
|---|---|---|---|
| board-v1 | width 128, 4 layers, 0.9 M weights | N | 83.2% / 84.8% |
| board-v2 | width 192, 6 layers, 2.2 M | N | 86.9% / 86.5% |
| board-v3 | as v2 | N + correction round | 87.7% / 87.5% * |
| board-v4 | as v2 | N + correction round + N2 | 89.3% / 88.9% * |

\* larger analysis set (includes the correction round's analysis games), so not directly comparable with v1/v2.

## 3. Same-morning bench (105 analysis mornings, one day, template plan and market)

| Player | vs template | vs v3-fw | Share of the teacher's lead |
|---|---:|---:|---:|
| v3-fw (job ranker, 14-game version) | +98 (se 55) | 0 | 16% |
| board-v1 | -643 (se 86) | -741 (se 99) | -104% |
| board-v1 + guard | -351 (se 78) | -449 (se 83) | -57% |
| board-v2 | +102 (se 61) | +4 (se 72) | 16% |
| board-v2 + guard | +146 (se 64) | +48 (se 70) | 24% |
| **board-v3 + guard** (after the correction round) | **+272 (se 66)** | **+174 (se 61)** | **44%** |
| Teacher | +619 (se 59) | +521 (se 54) | 100% |

**Why the guard:** board-v1 played as well as the teacher during the day but lost overnight: animals escaping
(1.17 a day vs the teacher's 0.44), animals unfed on production nights (2.37 vs 1.23), crops dying (3.41 vs 2.57).
Copying turn by turn misses rare end-of-day jobs (the 4th-place team's write-up mentions the same "feed
guard"). The guard sends the nearest free worker to an animal about to escape or a crop about to die when the day
is running out.

## 4. Full games (fresh seeds 20001-20024, both seats, against Metav4)

| Player | Our bank | Metav4 | Share | Wins | Margin vs v3-fw (days 6-28) |
|---|---:|---:|---:|---:|---:|
| Template | 92,322 | 101,720 | 0.908 | 4/48 | -6,029 (se 1,186) |
| v3-fw, days 6-28 | 94,640 | 98,009 | 0.966 | 16/48 | 0 |
| board-v2 + guard | 94,791 | 94,786 | 1.000 | 22/48 | +3,375 (se 1,664), better on 16/24 seeds |
| board-v3 + guard | 96,502 | 91,999 | 1.049 | 33/48 | +7,872 (se 1,463), better on 19/24 |
| **board-v4 + guard** | **97,067** | **89,444** | **1.085** | **38/48** | **+10,992 (se 1,796), better on 22/24** |
| Teacher | 114,908 | 80,661 | 1.425 | 48/48 | +37,616 (se 1,724) |

board-v4 against board-v3: margin +3,120 (se 1,635), better on 17 of 24 seeds; same-morning +22 a day (se 63).
board-v4 is chosen as the new best agent. Its slowest turn in 48 games: 405 ms (none over 1 s).

**Time per turn:** network turns take 22-58 ms on CPU. All 48 turns over 1 s in the board-v2 games were the
first network turn of each game (day 6, hour 0: the guard imported the job-ranker module and LightGBM on first
use, about 4 s); fixed, the first turn now takes 22 ms.

## 5. Bugs found and fixed tonight

- 16-bit storage overflowed raw features (cash above 65,504): NaN losses; data kept in 32-bit.
- The trainer selected training games by number and left out the 48 new N2 farms (10401-10448); board-v3 was
  trained without them; the trainer now uses the dataset's split column (board-v4 includes them).
- The takeover tool accepted only `model:` players; it now accepts `net:` players.

Same-morning bench for board-v4 + guard: +294 a day over the template (se 64), +196 over v3-fw (se 67), 48% of
the teacher's lead.

## 6. Next steps (for decision)

1. **Held-out opponents** (PLAN.md: a result counts only if it holds there): board-v4 + guard against the two
   5th-place agents, F4 and the counter versions, full games on fresh seeds. Needed before "Comfortable".
2. **A second correction round** with board-v4 (the first one moved the bench from +48 to +174 a day).
3. **All days**: the turn dataset already holds teacher examples for days 0-5 and 29; a network trained on them
   could replace the template's workers there (the job ranker failed at this; the network may not).
4. **The plan stage** (crop mix, herd, daily buying): the network can grow heads for it (design section 10).
5. **Submission readiness**: package the agent (network weights, encoder, template) and check its time and size
   inside the competition's limits.

## 7. Guard ablation (2026-10-26, after package V)

Codex's guard audit (package V) found the guard replaced about 10 worker commands a day, more than half of them
jobs the network was about to do. Measured without it:

| board-v4 | Same morning vs template (105 analysis mornings) | Full games: share / wins | Margin vs v3-fw |
|---|---:|---:|---:|
| with the guard | +294 (se 64) | 1.085 / 38 of 48 | +10,992 (se 1,796) |
| **without the guard** | **+327 (se 61)** | **1.119 / 44 of 48** | **+13,876 (se 1,749)** |

Without minus with, full games paired by seed: margin **+2,884 (se 854)**, better on 18 of 24 seeds; own bank
+1,804 (se 1,016); Metav4 -1,079 (se 464). Same morning: +32 a day (se 39). **board-v4 without the guard is the new
best agent.** After the correction round the network handles urgent jobs itself; the 4th-place agent likewise has no
worker guard, only structural ones (feed wheat on hand, end haul, sell-all, night overflow). A market-side feed
guard (`net:<model>:feedguard`) is implemented and kept for testing; it did not trigger on test mornings.

## 8. Correction round 2 (board-v4 without the guard), board-v5 (2026-10-26)

2,208 takeover segments from board-v4's own states (no guard), 387,072 decisions; board-v5 trained on all data
(114,122 training turns), 89.7% command agreement on the (larger) analysis set.

| | Same morning vs template | Teacher's workers ahead by | Full games: share / wins |
|---|---:|---:|---:|
| board-v4 (no guard) | +327 (se 61) | +140 (se 44) | 1.119 / 44 of 48 |
| **board-v5** | **+377 (se 58)** | **+90 (se 31)** | **1.125 / 40 of 48** |

v5 minus v4: same morning +50 a day (se 40); full games margin +589 (se 934), own bank +682 (se 1,142), better on
13 of 24 seeds. **In full games the two are level.** The workers now reach 81% of the teacher's workers' edge on the
same mornings; further worker rounds are unlikely to move full games much. The remaining gap is the plan.

# Overnight 2026-10-27: correction rounds against fifth-nflow (N1, N2), board-p3 and board-p4

**Plain answer:** after two correction rounds against fifth-nflow, **board-p4 reaches share 0.839 against fifth-nflow
(board-p2 0.800), margin +4,972 a game (se 1,560), better on 18 of 24 seeds**; still 0 of 48 wins (banks 91,484
against 109,065 a game). board-p3, after round N1 alone, was level with board-p2 (30 games). The target of 0.9 is
not reached. Metav4 was not checked.

## What ran (00:20-08:40, measured; the last evaluation ran 20 minutes past the 8-hour limit)

| Step | Result |
|---|---|
| Source games N1: board-p2 vs fifth-nflow, 30 plan training seeds, seat 0 | share 0.813, 0 wins |
| Correction round N1 (`--late`: hours 4/8/12/16 on days 6-21, every 2 hours 2-18 on days 22-28) | 3,810 / 3,810 kept, check passed; 53,322 turns (`l3-n1`); one 17-unit segment left out |
| Codex: market labels for round 3 (`l3-p1`, Step C) and N1 (`l3-n1`) | imported into master (2b05f9c, ecd3d45) |
| board-p3 = board-p2 + `l3-p1` market labels + `l3-n1` worker labels, 4 epochs | command accuracy 91.22% / 92.76% (board-p2 90.87% / 92.33%) |
| Source games N2: board-p3 vs fifth-nflow, the other 15 plan training seeds | share 0.857, 0 wins (different seeds from N1; not comparable) |
| Correction round N2 | 1,905 / 1,905 kept, check passed; 26,670 turns (`l3-n2`) |
| board-p4 = board-p3 + `l3-n1` market labels + `l3-n2` worker labels, 4 epochs | command accuracy 91.43% / 92.94% |
| board-p3 full games vs fifth-nflow | 30 of 48 (seeds 20001-20015, both seats); stopped to leave time for board-p4 |
| board-p4 full games vs fifth-nflow | 48 of 48; slowest turn 450 ms |
| Metav4 check | not run (no time) |

`l3-n2` market labels were not ready; board-p4 trained without them.

## Full games against fifth-nflow (seeds 20001-20024; paired by seed and seat with board-p2)

`tools/paired_runs.py nflow-p2 nflow-p3 nflow-p4`

| Agent | Games | Share | Share of board-p2 on the same games | Wins | Margin minus board-p2 (se) | Seeds better |
|---|---:|---:|---:|---:|---:|---:|
| board-p2 | 48 | 0.800 | | 0 | | |
| board-p3 (round N1) | 30 | 0.811 | 0.809 | 0 | +68 (2,253) | 7/15 |
| **board-p4 (rounds N1 + N2)** | 48 | **0.839** | 0.800 | 0 | **+4,972 (1,560)** | 18/24 |

board-p4 against board-p3 on the same 30 games: +3,469 (se 2,252), 11 of 15 seeds better. Runs: `runs/nflow-p3`
(partial), `runs/nflow-p4`.

## What the correction rounds changed (board-p3 against board-p2, same 30 games, `tools/gap_profile.py`)

Per game, summed over each band (tiles and animals per day):

| | Days 6-11 | 12-17 | 18-23 | 24-29 |
|---|---:|---:|---:|---:|
| Revenue p2 / p3 | 25,169 / 25,195 | 33,923 / 33,950 | 32,748 / **31,419** | 27,550 / **29,624** |
| Empty tiles p2 / p3 (reference 15.2 on days 24-29) | 4.8 / 3.1 | 2.3 / 1.3 | 5.4 / 2.9 | 27.0 / **12.0** |
| Idle unit-turns p2 / p3 (reference 38) | 101 / 129 | 45 / 48 | 45 / 35 | 124 / **54** |
| Crop tiles p2 / p3 | 40.8 / 39.6 | 75.6 / 68.8 | 71.5 / 66.4 | 48.6 / 56.2 |
| Geese p2 / p3 | 4.1 / 3.9 | 7.5 / 7.5 | 7.4 / 7.5 | 6.2 / 7.2 |
| Cows p2 / p3 | 7.1 / 7.1 | 7.5 / 7.3 | 7.4 / 7.3 | 5.8 / 7.1 |
| Spending p2 / p3 | 17,495 / 16,010 | 5,236 / 4,963 | 4,040 / 3,942 | 3,789 / 5,227 |

The rounds fixed what they targeted: in days 24-29, empty fields and idle workers came down to about the reference's
level and fewer animals were lost (+2,075 revenue). The middle days lost part of it: fewer crop tiles in days 12-23
(tomatoes 11.4 to 9.5) and 1,330 less revenue in days 18-23; more spending late. Net margin: no change.

## Layout (Codex package L, `reports/2026-10-27-layout-structure.md` on `dev/eugene-codex-overnight`)

- **Grouping: supported.** board-p2 has more separate patches per crop than the teacher late in the game (day 24
  wheat 3.9 against 2.7 patches, tomato 7.7 against 5.9; day 29 wheat 8.3 against 5.1) and fewer same-crop
  neighbours.
- **Block against snake: not supported as a general rule** (bounding-box fill about the same; the teacher's
  perimeter/area slightly lower).
- **Animal tower: partly supported, cows only:** 61% of board-p2's cow areas are towers (3+ rows, at most 2 columns)
  against 30% of the teacher's; geese and sheep are not towers in either. The teacher spreads geese over 4.8 columns
  against 3.1.
- Teacher animal spread goes with shorter fertilizer trips (adjusted r = -0.41), not with less idle; observational.
- All board-p2 FEED and CARE commands take effect; lost animals come from missed service, not failed commands.
- Nearest-empty planting: the teacher picks the nearest empty tile more often than board-p2 (89% against 82%), so
  "plants the nearest tile" does not explain our scatter.

## Next steps (proposed)

1. **board-p4 is the new best agent** (0.839 against fifth-nflow). Check it against Metav4 and fifth-n1 (not run).
2. **Profile board-p4** like board-p3 above: did N2 also keep the late-game fix while recovering days 12-23?
3. **More rounds of the same kind work:** a third round from board-p4 (N3) on the plan training seeds (all 45 are
   now used once; the states differ because the agent differs), plus `l3-n2` market labels from Codex.
4. **Layout:** the measured problems are crop grouping (more patches) and cow towers. Candidate fix: teacher
   takeovers aimed at planting and building choices, or a planting-target term in the network; not designed yet.
5. Codex's package E (endgame) on board-p2 against fifth-nflow is unfinished (40 source games, 61 play-outs).

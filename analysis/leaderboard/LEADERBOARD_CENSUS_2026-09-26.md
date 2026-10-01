# Mid-ladder census and the new Metav4 successors

Date: 2026-09-26
Status: **measurement.** Supersedes the "exact Metav4 copies" assumption behind
`docs/H1_COUNTER_2026-09-25.md`.
- Inputs: `research/intake/replays/25 Sept Mid/`, 139 replays (278 player-games,
  137 teams) from ranks ~50–500; `research/intake/notebooks/25 Sept/`, 10 public
  notebooks.
- Tools: `research/tools/fingerprint.py` (worker-move match against the Metav4 tape)
  and `research/tools/reproduce.py`. The second replays each player's observations
  through a fresh copy of a candidate agent and compares actions step by step.
  Calibrated on a local game: exact copies reproduce 100% of all 719 steps, in both
  seats. Replays omit `step` from the second seat's observation; the tool restores it.
- Evidence: `evaluation/census/`.

## 1. Who is on the mid-ladder

| family (by best reproduction) | teams (of 137) |
|---|---:|
| close fork of **More Wheat** (older base, no RACE/V44Y) | 56 |
| close fork of **Metav4** / its successors F1–F2 | 43 |
| a different family (under 50% worker match with every candidate) | 18 |
| partial matches | 20 |
| **exact copy of any public agent** | **0** |

- **About 80% of teams play the Metav4 tape family**, but nobody runs an exact
  public file.
- The Metav4-like teams already differ from step 0–2: a different first wheat trade,
  and on average about 26 worker-steps and 92 market-steps a game.
- Only 3 of 62 Metav4-like player-games played identically to Metav4 through
  step 216.

## 2. The 25 Sept public notebooks

| agent | what it is | vs Metav4 (80 games, seeds 6261–6300) |
|---|---|---:|
| **F1** = cha22-agent = demand-preserving-turn-sale-timing = master-engine-v3 = multi-route (byte-identical) | Metav4 successor, +EXP402/410 | **F1 wins 78–2** |
| F3 = kaggriculture (25 Sept) | plays identically to F1 (F1 vs F3 = 6–6–68 ties) | F3 wins 78–2 |
| F2 = herd-safe-v3 | Metav4 successor, +EXP389/402/410 | F2 wins 77–3; F1 beats F2 72–8 |
| God's Mode: Hacked Stores | Farming Score V2 + an overlay that infers the game seed from weed draws and steers the next shop | Metav4 wins 73–7 |
| MarketShock-M1-WR1K (a-song-of-ice-and-fire) | Metav4 lineage; **broken as published** (the last callable is an installer, so the Kaggle loader runs the wrong function) | intended agent: Metav4 wins 71–9 |
| what-2600-farms, x-ray-your-agent | analysis notebooks, no agent | — |

**F1 is the strongest public agent we have**, and it is published four times. The
F1 and God's Mode agents were decoded statically: each payload was checked against
its notebook's SHA-256, and no notebook code was executed.

## 3. Consequences

- **Metav4 is outdated.** A Metav4 base, with or without the counter, loses about
  97% of games to F1/F3.
- **The counter must sit on F1.** Ported unchanged onto F1: against the F1 mirror,
  77–3 vs 6–6–68 (+71 wins, 0 lost); no change against F2 or Metav4
  (`evaluation/h1_counter_f1/`). The confirmation is in
  `docs/H1_COUNTER_F1_2026-09-26.md`.
- **The counter's ladder payoff is uncertain.** It only engages against agents that
  play identically to its own base through day 9, and the census found no exact
  copies. Its value is insurance: it gains against any F1 copy and costs nothing
  anywhere else.

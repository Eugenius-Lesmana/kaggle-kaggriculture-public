# Learned job values, and why the top-four plan earns less on our executor

Date: 2026-09-30
Branch: `dev/eugene-claude-routeopt`
Status: **measurement.** It follows `docs/EARLY_LABOUR_2026-09-30.md`.

## 1. Codex's replay-learned job values: neutral

The module comes from Codex (`dev/eugene-codex-jobvalues`, `docs/JOB_VALUES_2026-09-30.md`).
It embeds decision trees trained to imitate the top agents' job priorities: 88.5% held-out
within-cell accuracy, and 51% for choosing the next cell. It sits behind
`JOB_VALUES_LEARNED` in `agents/ours/v0.11.0-candidate`.
- Each job is scored for the specific worker, from that worker's route endpoint.
- Scores are cached per compile.

Results against Metav4, paired, 80 games per block, 2 workers:

| seeds | change |
|---|---:|
| 7801–7840 | +0.018 ± 0.014 |
| 7841–7880 | +0.005 ± 0.012 |
| 7881–7920 | −0.007 ± 0.012 |
| **pooled, n = 240** | **+0.005 ± 0.007** |

**Neutral.** The first block was chance, and the switch stays off. This is consistent with
execution not being the limit.

## 2. Top-four plan vs our plan (seeds 7611–7650, 80 games, identical seats)

The top-four plan is `skel`, played on our executor.

| per game | v0.10 | top-four plan | change |
|---|---:|---:|---:|
| our revenue | $98.5k | $104.3k | +$5.8k |
| our spending (revenue + $3k − bank) | $23.8k | $31.2k | +$7.4k |
| **our bank** | $77.7k | $76.1k | −$1.6k (−2%) |
| **opponent (Metav4) bank** | $112.4k | $125.9k | **+$13.5k (+12%)** |
| bank ratio | 0.689 | 0.604 | −0.085 ± 0.020 |

**Our products:**
- The top-four plan sells fewer wheat (173 vs 303), strawberries (126 vs 170) and wool
  (80 vs 121).
- It sells more eggs (196 vs 94), milk (179 vs 142) and tomatoes (44 vs 0).
- Per-unit prices are similar.

**The opponent's gain, by product:**

| product | opponent's price/unit, our plan → top-four plan | opponent revenue change |
|---|---|---:|
| wool | $110 → $163 | **+$8.9k** |
| milk | $136 → $152 | +$3.5k |
| strawberry | $145 → $153 | +$2.1k |
| wheat | $38 → $40 (and 566 → 373 units) | −$6.5k |
| others | | −$4.1k |

## Reading

- The transplant's −0.085 is mostly **market interaction**, not our own loss.
  - Earlier land and more animals cost $7.4k and earn $5.8k back, so our own loss is −2%.
  - Selling fewer units of the opponent's products, especially wool, raises its prices
    (+48% on wool) and adds $13.5k to its bank.
- Markets are shared. Every unit we do not sell raises the opponent's price, and ranking
  is relative, so product choice must count its effect on the opponent's prices, not only
  our own revenue.
- The top-four plan was tuned for their field. Against a Metav4-type opponent it gives up
  that opponent's key products.
- Bank ratio against one tape opponent mixes our own production with this interaction.
  Future plan tests should report our bank and the opponent's separately.

Evidence:
- `evaluation/routeopt/f1_ctrl.json`, `f1_skel.json`;
- `evaluation/routeopt/jv*_*.json`.

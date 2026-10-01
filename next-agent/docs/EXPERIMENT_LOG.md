# Experiment log: what we tried on the planner

Every row is a **paired** experiment: the same seeds and seats for the change and its control, against the
public Metav4 agent unless noted. The metric is the **change in our bank's ratio to the opponent's** (our bank
÷ opponent's bank, so 0.70 means we end with 70% of its money), with a 95% interval. The control sits at
about 0.69–0.71 in every block. Negative means the change made things worse.

Result files are in [`../evidence/routeopt/`](../evidence/routeopt/). Rows in the same block share one control, so
differences within a block are less noisy than across blocks, but the rows are not independent samples.
To recompute any row:

```bash
python next-agent/evidence/routeopt/paired.py next-agent/evidence/routeopt/f3_ctrl.json next-agent/evidence/routeopt/f3_F3a.json
```

## 1. Transplanting the top-four plan ([`V010_TOP4_TRANSPLANT`](V010_TOP4_TRANSPLANT_2026-09-25.md))

360 games per arm, seeds 6141–6200, against Metav4, More Wheat and V46.

| Change | Result |
|---|---:|
| Full skeleton: their opener, land steps, layout, worker schedule | **−0.105 ± 0.009** |
| Their opener only (days 0–5), then our planner | −0.034 ± 0.009 |
| Their worker schedule only | −0.001 ± 0.004 |
| Harvest wheat at age 3 | −0.002 ± 0.001 |
| Fertilize anything a worker carries | −0.032 ± 0.004 |
| Hold wool / milk / strawberry back when the price is low | −0.005 ± 0.002 |

## 2. Copying routes and moves ([`EXECUTOR_PROTOTYPE`](EXECUTOR_PROTOTYPE_2026-09-29.md))

Seeds 7101–7200, one seat per seed. 100 games against Metav4 and 60 against V46. The control is the full
top-four plan on our executor (0.601 and 0.630).

| Change | vs Metav4 | vs V46 |
|---|---:|---:|
| Workers walk the top team's median route and act on each cell's state | −0.012 ± 0.014 | −0.014 ± 0.011 |
| A literal 12-day action tape of one top game, market included | −0.063 ± 0.016 | −0.007 ± 0.034 |

Of the route visits reached, 27% found nothing to do on our farm and 12% fell in quadrants we did not yet own.
Useful actions on days 6–11 fell from 469 to 393 a game once unneeded watering is excluded.
The literal tape broke on day 1: we held $1 where the tape needs about $4, so only one of its three day-1
hires went through, in all 100 games, and the farm never matched the one the tape was recorded on.

## 3. Early labour: fertilizer and herd size ([`EARLY_LABOUR`](EARLY_LABOUR_2026-09-30.md))

80 games per row.

| Change | Seeds | Result |
|---|---|---:|
| Fertilizing is free of worker-time cost before day 12 | 7611–7650 | −0.003 ± 0.008 |
| …before day 20 | 7611–7650 | −0.014 ± 0.009 |
| Fertilizer valued at half its market quote | 7651–7690 | **+0.009 ± 0.010** |
| …and free before day 12 | 7651–7690 | −0.016 ± 0.014 |
| Two more animals per bought plot, cap 7 | 7691–7730 | −0.012 ± 0.020 |

## 4. Top-four plan vs ours, including the market ([`PLAN_VS_MARKET`](PLAN_VS_MARKET_2026-09-30.md))

Seeds 7611–7650, 80 games.

| | v0.10 | top-four plan | change |
|---|---:|---:|---:|
| Our bank | $77.7k | $76.1k | −$1.6k |
| **Opponent's bank** | $112.4k | $125.9k | **+$13.5k** |
| Ratio | 0.689 | 0.604 | −0.085 ± 0.020 |

Most of the loss is the opponent gaining. We sold fewer of the products it sells too, so its prices rose
(wool +48%). Markets are shared.

## 5. Learned job values ([`JOB_VALUES`](JOB_VALUES_2026-09-30.md), [`PLAN_VS_MARKET`](PLAN_VS_MARKET_2026-09-30.md))

Decision trees trained on about 2 million top-agent worker turns: 88.5% held-out accuracy on the next job in a
cell, 51% on the next cell. Used to score each job for each worker.

| Seeds | Result |
|---|---:|
| 7801–7840 | +0.018 ± 0.014 |
| 7841–7880 | +0.005 ± 0.012 |
| 7881–7920 | −0.007 ± 0.012 |
| **pooled, 240 games** | **+0.005 ± 0.007** |

## 6. Fertilizer recipe, hands, zones, market module

All on seeds 7941–7980, one shared control (`f3_ctrl.json`), 80 games each.

| Change | Result | Note |
|---|---:|---|
| **F3a**: the top-agent fertilizer recipe, version a | −0.039 ± 0.009 | |
| **F3b**: version b | −0.059 ± 0.009 | Fertilizing displaced yield-window watering: 90% → 65% of window plant-days watered, so the bonus was lost. `diag_F3b.json`. |
| **F3c**: fertilize only on visits a cell needs anyway | −0.053 ± 0.009 | |
| **F4t**: fertilize only at the top agents' bonus ages (wheat 2–3, strawberry 9 and 13) | −0.016 ± 0.008 | `FERT_PRECISE` |
| **H13**: 13 hands from day 12 (default 11) | −0.037 ± 0.009 | `LATE_HANDS` |
| F3b + H13 | −0.061 ± 0.012 | |
| **MM**: the market module | **+0.006 ± 0.003** | Our bank −$0.2k, opponent −$1.5k: it works by lowering the opponent's income. **Needs confirmation on fresh seeds.** `MARKET_MODULE` |

Zone and sweep (diagnostic runs, 6 games each, `diag_zone_*.json`):

| Change | Result |
|---|---|
| Angular sectors per worker (`ZONE_SWEEP`) | Walking rises from 44% to 51% of worker time; ratio 0.653 against 0.700. |
| Inside-out reorder alone (`SWEEP_ONLY`) | About neutral. |

## 7. Codex modules

| Change | Result | Note |
|---|---|---|
| Capacity module ([`CAPACITY_MODULE`](CAPACITY_MODULE_2026-09-30.md)): buy the fourth quadrant from day 10, add shop-triggered geese and tomatoes, hire 14 hands | Our bank −$8.4k, opponent +$12.9k (4 games, seeds 8001–8004) | Not wired in by default. Too few games to call. |
| Market module ([`MARKET_MODULE`](MARKET_MODULE_2026-10-01.md)): price curve, exposure ordering, held-stock sale gate | See row **MM** above | The same-turn wheat opening *lost $3 a game* against buying only the five wheat units kept, so it is off. |

## Reading

- **21 of about 22 changes did not help.** The one exception, MM, is small and sells less of the opponent's
  income rather than raising ours.
- Fertilizer is the clearest case. The top agents fertilize at the right age and are rewarded. When our planner
  fertilizes more, it takes workers from watering inside the same window and loses more than it gains.
- Several results are about the *opponent*. Ratios against one fixed opponent mix our own production with
  market interaction. Report both banks.

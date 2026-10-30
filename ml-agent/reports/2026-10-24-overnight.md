# Overnight results (2026-10-24 to 25)

**Plain answer.** In full games against Metav4 on 24 fresh seeds (both seats), **v3-fw used only on days 6-28**
(the days its training data covers; the template's own workers outside them) beats the template: bank **+2,319**
(se 1,069), margin over Metav4 **+6,029** (se 1,186), better on **21 of 24 seeds**; share of Metav4's bank
**0.966** against the template's **0.908**; wins **16/48** against 4/48. That passes the plan's "Good" level
(above the template) but not yet the "Target" (share above 1.0 and more than half the games won).
The preview-bench stop rule A+ ended the correction rounds after round 2 (v4 no better than v3).

## 1. Correction rounds (preview benches)

Details of round 1 in `reports/2026-10-24-round1-v3.md`.

| Model | Data | Test games, one day vs template (105 mornings) | Three days vs template (25 mornings) |
|---|---|---:|---:|
| v2 | L1 | -293 (se 57) | -824 (se 314) |
| **v3-fw** | L1 + L3 (v2's states), crop features, costly decisions x2 | **+23 (se 49)** | **+367 (se 242)** |
| v4-fw | + L3 round 2 (v3-fw's states) | -10 (se 55); vs v3-fw -33 (se 46) | +365 (se 294); vs v3-fw -1 (se 254) |
| Teacher | | +590 (se 56) | +3,300 (se 326) |

Stop rule A+: round 1 passed (+316 a day over v2, needed +100); round 2 gave nothing, and v4 is far below the
+350 needed for the polish step, so **the correction rounds stop here**, as agreed. Round 2 data (2,208 takeover
days from v3-fw's states, all validated, no teacher crashes) is kept on D: (`takeover/model-ranker-v3-fw`).

## 2. Full games against Metav4 (the real target)

Fresh seeds 20001-20024, both seats, Codex's `tools/run_full.py` (package G); template and v2 games are Codex's.

| Player | Our bank | Metav4 bank | Share | Wins | Median / max ms per turn |
|---|---:|---:|---:|---:|---:|
| Template | 92,322 | 101,720 | 0.908 | 4/48 | 9 / 249 |
| v2 (all days) | 82,560 | 102,984 | 0.802 | 2/48 | 476 / 1,588 |
| v3-fw (all days) | 69,381 | 134,843 | 0.515 | 0/48 | 254 / 1,253 |
| **v3-fw, days 6-28** | **94,640** | **98,009** | **0.966** | **16/48** | 341 / 1,263 |

Paired by seed against the template (24 seed means):

| Player | Bank | Metav4's bank | Margin | Seeds better |
|---|---:|---:|---:|---:|
| v2 | -9,761 (1,471) | +1,264 (936) | -11,026 (1,736) | 1/24 |
| v3-fw, all days | -22,941 (1,845) | +33,123 (2,089) | -56,064 (2,346) | 0/24 |
| **v3-fw, days 6-28** | **+2,319 (1,069)** | **-3,710 (1,017)** | **+6,029 (1,186)** | **21/24** |

- By seat: days 6-28 share 0.964 (seat 0) and 0.967 (seat 1); template 0.911 and 0.904.
- By scenario (early strawberry buyers 0/1/2): bank +2,908 / +46 / +4,568 against the template.
- **Using the ranker on all days is a disaster**: on days 0-5 (no training data there) the farm never gets
  going and Metav4 gains 33,000. The day window fixes this: the model is only trusted where it has data.
- Metav4 earns 3,710 less against the windowed model: our farm competes better in the shared market.
- **Speed caveat:** the ranker takes 341 ms per turn (median) and up to 1.3 s; the template 9 ms. Whether this
  fits the competition's time allowance has not been checked.
- Correction to an overnight message: my first summary of these games read the bank fields in the wrong order;
  the figures above are re-computed and match Codex's published template numbers exactly.

## 3. Codex packages (all merged)

- **G, full-game bench:** `tools/run_full.py`, 96 games; template share 0.908, v2 0.802.
- **H, template without dawn wheat/carrot seed buying:** no effect (full games -53, se 84); the template buys
  the same seeds later in the day. D6's start-of-day cost is not the dawn seed purchases.
- **S, teacher's shed use:** usually fetches 3 wheat, 3 fertilizer or 1 animal (65% of pickups exactly);
  smaller wheat pickups in recovery states (2.3 vs 2.9); returns wheat to the shed mainly when it also carries
  goods to sell (72%), almost never otherwise. v3-fw still makes 12 pickups and 5 drops a day against 9 and 3.

## 4. Decisions for Eugene

1. **Accept v3-fw (days 6-28) as the new best agent** and keep it as the baseline for every next step?
2. **What next for the workers**, since the correction rounds have stopped:
   - (a) cheap targeted fixes inside the current design: the shed rule from package S; extend the day window
     with data for days 0-5 and 29 (L1/L3 only cover days 6-28, so the opening and last day need their own
     teacher data);
   - (b) your fallback: top-team layouts;
   - (c) the per-turn whole-team model (weeks).
3. **The plan stage** (crop mix, land, herd, market): the teacher's lead compounds over several days (D4), and
   the preview gap to the teacher is still about +570 a day, much of it outside the workers' control.
4. **Speed:** check the competition's per-turn time limit before relying on the ranker.

Evidence: `<data>/runs/full-v3fw*/`, `runs/overnight-g-fresh/`, `runs/compare/v4test*.csv`,
`runs/compare/test*.csv`; models `ranker-v3-fw`, `ranker-v4-fw`.

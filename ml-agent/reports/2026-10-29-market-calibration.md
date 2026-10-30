# Market calibration `mcal` on board-p5 (2026-10-29)

**Answer:** +1,399 margin a game over board-p5 (se 836, 1.7 se), share 0.907. That is positive, but below 2 se on
these seeds. The decision waits for Codex's fresh-seed run (20025-20048) and the pooled rule fixed in
`handoff/2026-10-29-claude-to-codex-market.md`.

## Diagnosis
Teacher-forced, analysis split; scratchpad `market_diag.py`.
- The market head's exact precision is 0.68, but 0.86 within ±2 turns: about half of the error is timing.
- The rest is over-ordering, from the 4× non-zero weight in `market_loss` plus argmax decoding. Units against the
  teacher: wool sells +26%, wheat seeds +33%, tomato seeds +48%, geese +35%, sheep +36%, land +23%.
- The teacher trades all day: sells peak at hours 21-23 and after the town shops (9, 13, 17); seed buys at hours 12-20.

## Calibration
- **Method:** a per-token bias on the class-0 ("no order") logit, chosen so the model orders each token as often as
  the teacher on the analysis split (scratchpad `market_cal.py`). File:
  `<data>/models/board-p5/market-cal.json`.
- **Effect on the analysis split:** precision/recall 0.681/0.841 → 0.764/0.763, and volumes match the teacher's.
  Wheat sells come in under (32,082 against 35,356).
- **Player option:** `mcal` (commit c39ae9c). Default play is unchanged: seed 20001 seat 0 replays with the same
  gameplay hash (`runs/hash-p5-default`).

## Live result
48 games, seeds 20001-20024, both seats, against fifth-nflow; run `nflow-p5-mcal` against `nflow-p5-best`; 24 seed
means.

| Margin change | se | Our bank change | se | fifth-nflow change | se | Share | Wins | Seeds better |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| +1,399 | 836 | +996 | 793 | -403 | 578 | 0.907 | 1/48 | 15/24 |

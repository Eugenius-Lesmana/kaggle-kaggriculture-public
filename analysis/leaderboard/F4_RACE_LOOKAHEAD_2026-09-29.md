# Race look-ahead: the second-slot candidate

Date: 2026-09-29
Status: **look 10 recommended for the second slot; look 20 is the aggressive alternative.**
It builds on `docs/F4_RACE_2026-09-29.md`.

The base is the 29 Sept submission, race + wheat (`h1-counter-f4-racewheat-candidate`,
submission 56677627). Its Step809 advances the native tape's pure-cash sales of the next
**3** turns. The variants change only `_S809_LOOK`; all other one-line ideas were rejected.
80 games per cell, both seats.

## One-line screens vs the submission (seeds 6921–6960)

| variant | W–L–T |
|---|---:|
| look 6 | 58–16–6 |
| lead seller uncapped at quote ≥ 100 | 9–11–60 |
| race from step 144 instead of 216 | 3–3–74 |
| fertilizer added to the advanced items | **35–45** ✗ |
| yarn maps keep the V39 route (no V92 override) | 7–13–60 |

## Dose (each vs the one below, seeds 6921–6960)

| look 10 vs look 6 | look 20 vs look 10 | look 40 vs look 20 | look 720 vs look 40 |
|---:|---:|---:|---:|
| 53–23–4 | 67–11–2 | 73–7 | 47–11–22 |

## Guards (identical seeds 7001–7040)

| arm | vs submission | F4 | F4 + counter | racing stand-in | F2 | F1 | Metav4 |
|---|---:|---:|---:|---:|---:|---:|---:|
| submission (look 3) | — | 80–0 | 62–16 | 78–0–2 | 66–14 | 70–10 | 73–7 |
| **look 10** | **58–18–4** | 80–0 | 66–14 | 80–0 | 68–12 | 70–8–2 | 71–9 |
| look 20 | 72–6–2 | 80–0 | 72–8 | 80–0 | 64–16 | 68–12 | 67–13 |
| look 40 | 72–8 | | | | 62–18 | 68–12 | 69–11 |

On seeds 6961–7000, look 6 was equal to the submission on every guard, and +36 wins
(55–19–6) against it.

**Older-family totals (F2 + F1 + Metav4):**
- submission 209;
- **look 10 209;**
- look 20 199;
- look 40 199.

## Reading

- **Look 10** beats the submission 58–18 and 66–12 on two seed sets, with no measured
  cost against any opponent.
- **Look 20** wins F4-family mirrors harder: 72–6 against the submission and 72–8
  against F4 + counter. It costs about 10 of 240 wins against the older families, which
  are about a third of ladder opponents, so it is roughly neutral in expectation and
  riskier.
- Beyond 20 there is no further gain against the submission, and the same cost.

## Candidates

- `agents/ours/h1-counter-f4-racewheat-look10-candidate/main.py` (sha256
  `fa91b31d226b0e87…`);
- `agents/ours/h1-counter-f4-racewheat-look20-candidate/main.py` (sha256
  `17a8132ffa43a95d…`).

Each is one line different from the submission, and a full game through the Kaggle
loader was checked. Evidence: `evaluation/f4_race/v2_*.json`, `v2s_*.json`.
Seeds used: 6921–7040.

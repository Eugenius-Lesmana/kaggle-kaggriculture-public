# Where board-p2's middle game loses to the teacher, against fifth-nflow (2026-10-26)

Tools: `tools/gap_profile.py` (day-by-day money, jobs, farm at dawn) and `tools/market_compete.py`, re-simulated
exactly from the replays. Games: seeds 20001-20024, both seats, against fifth-nflow: `runs/nflow-p2` (board-p2),
`runs/plan-measure-M/reference/nflow/games` (reference: template days 0-5 and 29, teacher days 6-28) and
`runs/nflow-teacher`; and the teacher against Metav4 (`runs/full-teacher`). Outputs:
`<data>/runs/diag-market/profile-*.csv|txt`, `market-*.csv|txt`.

## 1. The teacher plays the same against Metav4 and fifth-nflow

Per game, days 6-29: the same animals and land bought, the same crop and animal tiles, the same jobs (watering,
harvests, feeding, care, fertilizing within a few percent) and the same units sold (wheat 564 / 564, eggs 280 / 281,
strawberries 215 / 222, milk 183 / 193). Only its prices differ, because fifth-nflow sells into the same markets
(Metav4 sells almost no eggs or tomatoes). **The teacher does not switch tactics against a strong opponent**; what
changes for our network is the state it sees (prices, the opponent's stock), not the teacher's behaviour.

## 2. Layout is not where the middle game loses

board-p2 and the reference have the same field, coop and pasture counts through day 23 and the same mean distance
to the shed (crops 4.2-4.7, animals 1.6-1.9 for all three agents). The reference (our opener, teacher from day 6)
reaches share 1.011, so our early layout does not cap the result either.

## 3. Where the money goes: board-p2 against the reference (same opener, same opponent)

Revenue per game by day band:

| Days | board-p2 | Reference | Difference |
|---|---:|---:|---:|
| 6-11 | 25,107 | 26,404 | -1,297 |
| 12-17 | 34,358 | 37,283 | -2,925 |
| 18-23 | 32,963 | 34,269 | -1,306 |
| **24-29** | **28,323** | **35,236** | **-6,913** |

1. **Late-game wind-down (days 24-29, the network runs days 24-28):** fields left empty (26.5 empty tiles a day
   against 15.2), crop tiles 48.7 against 60.4 (wheat 17.5 against 29.0, tomato 4.1 against 9.0), **idle
   unit-turns 120 against 38**, harvests 161 against 198, watering 238 against 300, fertilizing 63 against 84.
2. **Animals lost:** per game over days 6-29, board-p2 loses 3.4 geese and 3.3 cows; the reference 0.5 geese and
   2.0 cows (sheep about the same, 5.6 against 6.7: the teacher also lets sheep go). board-p2 buys more geese (11
   against 9) yet holds fewer (7.4 against 8.8 a day): eggs 212 against 274 sold, milk 172 against 194.
3. **Tomatoes under-planted** in days 18-29 (tomato revenue 5,948 against 8,909); more carrots instead.
4. **Wool sold cheap:** 147 units at 96 against the reference's 127 at 120.
5. **Opponent side:** fifth-nflow earns about 10,000 more against board-p2 than against the reference, mostly milk
   (+4,500), strawberries (+4,300) and wool (+2,500): our lower volume leaves it better prices.

## What this means for training

- More teacher data against fifth-nflow adds the **states** a strong opponent creates (lower prices, contested
  markets), not new tactics. Useful, but the larger gain is likely from correcting **our** states.
- Correction rounds (the teacher taking over from our positions) **against fifth-nflow**, weighted towards days
  22-28 and animal care, aim at the three largest items above.

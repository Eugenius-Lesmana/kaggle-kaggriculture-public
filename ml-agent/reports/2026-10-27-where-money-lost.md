# Where board-p4 loses money against fifth-nflow (2026-10-27)

**Method:** board-p4 plays against live fifth-nflow, and the teacher takes over on the morning of day d and plays to
the end, day 29 included (`run_full.py handover:<d>:net:board-p4:market`, `runs/handover-p4`). Seeds 20001-20008,
both seats: 16 games per day. Each game is compared with board-p4's own game on the same seed and seat
(`runs/nflow-p4`). The two games are identical up to the takeover (checked on the test game). Repeat games reproduced
exactly.

## How much, and when

| Teacher takes over from day | Teacher's gain a game (se over seeds) |
|---|---:|
| 6 | 17,422 (1,762) |
| 12 | 15,858 (1,341) |
| 18 | 10,071 (1,519) |
| 22 | 6,360 (1,405) |
| 25 | 4,985 (696) |
| 28 | 2,850 (359) |

| Days | Lost a game | Share | Per day |
|---|---:|---:|---:|
| 6-11 | 1,564 | 9% | 260 |
| 12-17 | 5,787 | 33% | 965 |
| 18-21 | 3,711 | 21% | 928 |
| 22-24 | 1,375 | 8% | 458 |
| 25-27 | 2,135 | 12% | 712 |
| 28-29 (includes the template's liquidation) | 2,850 | 16% | 1,425 |

For comparison, Codex's benchmark on board-p2 (different seeds) gave: from day 24, 8,197; from day 26, 5,561; from
day 28, 2,708. The last two days did not improve between board-p2 and board-p4; the correction rounds do not reach
day 29.

## How (teacher from day 12 or 22, minus board-p4; per game; `tools/market_compete.py`, `tools/gap_profile.py`)

Money (revenue minus spending) by day band:

| | 12-17 | 18-23 | 24-29 |
|---|---:|---:|---:|
| Teacher from day 12: our net | +2,421 | +2,964 | +3,025 |
| Teacher from day 12: opponent's net | -590 | -2,918 | -3,796 |
| Teacher from day 22: our net | | +863 (days 22-23) | +3,491 |
| Teacher from day 22: opponent's net | | +78 | -2,231 |

About half of the teacher's gain comes from **the opponent earning less**. Over days 18-29, fifth-nflow sells about
the same units but at lower prices: milk -1,475, strawberries -1,960, wool -1,713. Why its prices are lower (the
teacher's sales timing or volume) is not measured yet.

Our side, teacher from day 12 against board-p4:
- **Spends less:** wheat bought as feed -1,377, sheep -656.
- **Different crops:** more tomatoes (+2,667 revenue) and carrots (+2,622); in days 24-29 fewer wheat tiles (30.7
  against 34.5) and more carrots (13.9 against 10.5).
- **Animals:** fewer FEED and CARE jobs with the same number of geese, and fewer cows and sheep kept to the end
  (cows 7.7 against 10.1 on days 24-29).
- **Work:** more harvests (203 against 167 on days 24-29); fewer digging and placing jobs.

Endgame only (teacher from day 22, days 24-29): carrots +1,562 (+41 units: a quick crop at the end), strawberries
+899, wool +531, tomatoes +414, wheat feed -480. Care 51 against 72 and feed 68 against 82: the teacher stops caring
for animals it will not profit from. Fewer digging and placing jobs, more harvests; it also idles more (53 against 34).

**Layout:** the teacher takes over our day-12 farm and still recovers 15,858 of the 17,422. Our farm as it stands on
day 12 costs at most about 1,600 a game. Whether the layout built after day 12 costs money is not separated by this
measurement: the teacher keeps changing the farm after it takes over.

## Conclusion

- **Middle days 12-21: about 9,500 a game.** The causes are crop choice (tomatoes and carrots against wheat), buying
  wheat feed and sheep, and sales that leave fifth-nflow good prices.
- **Endgame, days 22-29: about 6,400 a game,** with the most per day on days 28-29 (liquidation). The teacher's
  endgame is different play: quick crops, less animal care, more harvesting and less spending. This supports a
  separate endgame model that includes day 29.

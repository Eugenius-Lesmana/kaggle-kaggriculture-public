# The top teams' macro plan, days 0–19

Date: 2026-09-24
Status: **extraction only, no agent changes, no partition seeds.**
Inputs: `research/intake/replays/24 Sept/` — 46 player-games of today's top teams
(Team A 11, Team B 15, Team C 10, Team D 10, deduplicated by
episode). 22 Sept replays for the "did it change" check. Metav4 and ours/v0.9.4 on
local seeds 5791–5796 vs More Wheat, as the contrast.
Tools (untracked): `.cache/macro_extract.py` → `.cache/macro.pkl`,
`.cache/macro_report.py <section>`, `.cache/opener_lineage.py`,
`.cache/determinism.py`. Everything is confirmed from the next observed state.

Grid key used below (x = 0..9 left→right, y = 0..9 top→bottom, one row per `|`):
`W` wheat, `C` carrot, `T` tomato, `S` strawberry, `M` melon, `g` goose, `c` cow,
`s` sheep, `.` empty, `#` locked.

---

## 0. The headline: the top four are one lineage, and it is not ours or Metav4's

- **Day 0 is byte-identical across all four teams and all 46 games.** Same market
  orders on the same steps:
  - step 1: buy 1 cow + 5 wheat;
  - step 2: buy 1 cow + 3 sheep, hire;
  - steps 2–7: a 1-unit wheat buy/sell churn every step;
  - steps 7, 9, 12: melon seeds ×2;
  - steps 13–22: wheat seeds.
- **The farm layout matches in 100% of cells** through day 5 for every team.
- **They share one land schedule:** NE at step 150, SW at 220–222, SE at 254–255.
- **None of our 56 registered agents plays this opener.** It is not the Metav4/V46
  family (at most 10% of day-0 orders match) and not ours.

So today's top of the leaderboard shares one ancestor we don't have. It is probably
a recent public notebook, or a shared base. **Finding it is the single most valuable
next step** (§9).

## 1. The opener (days 0–5)

| | top four (all identical) | Metav4 | v0.9.4 |
|---|---|---|---|
| day-0 planting | 9 wheat + 6 melon, then 4 more melon on day 1 (10 melon) | 7 wheat + 12 melon | 7 wheat + 3 melon |
| animals day 0 | 2 cows + 3 sheep, 5 pastures in NW | 2 cows + 2 sheep | 2 cows + 2 sheep |
| workers | 5 on day 0, 7 from day 2 | 6 → 5 | 6 → 7 |
| wheat's job | **a 2-day filler**: harvested at first yield (age 2) and replaced by strawberry | harvested and replanted wheat | wheat |
| strawberry | 4 on day 2, 6 on day 3 → **10 by day 5**, in the old wheat cells | 4 on day 5 | 2 |
| fertilizer | none | none | none |
| cash | ~$0 on days 0–2; ~$800 on day 5 | ~$800 | ~$1,200 |

```
top four, end of day 0        end of day 2          end of day 5
WWW..|WWWMM|WMWMc|.M..s|WMssc  S.WMM|SSWMM|WM.Mc|WMMMs|SMssc  SSSMM|SSSMM|SMSMc|SMMMs|SMssc
```

**What the opener does:**
- It locks in **10 melons** (sold around day 10) and **10 strawberries by day 5**.
- It uses wheat purely as a fast cash and turnover crop in the cells strawberry
  will take.
- It keeps 5 animals on 5 pastures from day 0.
- It spends everything: cash is near zero until day 5.

Answers to your question 1:
- **Always the same plants?** Yes, in every game, every team.
- **Do they buy anything?** Yes: animals and wheat at steps 1–2, then seeds.
- **Fertilizer in the opener?** None, from any team.
- **Is the herd a preset amount?** Yes: exactly 2 cows + 3 sheep on day 0, in every
  game.

## 2. After the opener (days 6–19)

Plantings per game by day (mean over teams; they differ by less than ±2):
- **Day 6** (second quad opens): ~7 strawberry + ~5 wheat.
- **Days 7–8:** 2–4 wheat a day.
- **Day 9** (third quad opens): **~14 wheat** + 2–3 tomato + 2–3 strawberry.
- **Days 10–19:** 5–10 wheat a day, a steady wheat rotation, plus carrot, tomato
  and strawberry that depend on the shop draw (§6).

Replanting (previous crop → next crop, per game, days 6–19):

| transition | Team A | Team B | Team C | Team D | Metav4 | v0.9.4 |
|---|---:|---:|---:|---:|---:|---:|
| wheat → wheat | 52 | 52 | 61 | 41 | 60 | 64 |
| wheat → tomato | 8.5 | 8.8 | 5.8 | 6.0 | 0 | 0 |
| wheat → carrot | 6.8 | 2.9 | 6.7 | 8.3 | 0.8 | 0 |
| wheat → strawberry | 5.0 | 8.5 | 4.2 | 6.6 | 5 | 0 |
| carrot → carrot | 11.4 | 4.7 | 8.8 | 8.3 | 0 | 0 |
| melon → wheat (day 10) | 4.8 | 5.1 | 5.3 | 7.4 | 8 | 3 |
| **idle steps between harvest and replant** | **1** | **1** | **1** | **1** | 1 | **14** |

Answers to your question 2:
- **When do they harvest?** Wheat at first yield, then immediately.
- **What happens after the harvest?** The cell is **replanted the next step**,
  usually wheat again. Our planner leaves the cell empty for a median of 14 steps.
- **Do they plant the same thing?** Mostly; about 1 in 4 replants switches crop
  (wheat → tomato, carrot or strawberry).
- **Is the amount the same across games?** The wheat backbone is. The switches
  depend on the shops (§6).
- Melon cells become wheat after the day-10 melon harvest.

## 3. Land timing

| | NE (2nd) | SW (3rd) | SE (4th) |
|---|---|---|---|
| Team A | step 150, 11/11 | 218–222, 11/11 | **253–255, 11/11** |
| Team B | 150, 15/15 | 220–225, 15/15 | 254–255, 15/15 |
| Team C | 150, 10/10 | 220–222, 10/10 | 254–255, 9/10 |
| Team D | 150, 10/10 | 220–222, 10/10 | 254–255, 5/10 |
| Metav4 | 151 | 266 | rarely |
| v0.9.4 | 146 | 217–218 | never |

Answers to your question 3:
- **Hard-coded, not a cash threshold.** The step is fixed while cash at purchase
  varies from $1.1k to $3.7k (SW) and $3.3k to $6.6k (SE). They fund it by selling
  on or just before that step.
- **Not tied to finishing a layout.** NE opens at the start of day 6, while the NW
  layout is already complete from day 5.

**New since 22 Sept:** the fourth quad (SE) on day 10. On 22 Sept Team A stopped at three
quads, and Team D bought SW on day 8 (step 199). Both have now moved onto one
shared schedule.

## 4. What goes on each new quad (first 72 steps after purchase, per game)

| | NE, day 6 | SW, day 9 | SE, day 10 |
|---|---|---|---|
| Team A | 10 wheat, 9 strawberry, **6 pastures + 3 coops**, 4 cows, 3 geese, 1–2 sheep | 14 wheat, **5 tomato**, 3.5 geese + coops, 2.6 strawberry | 13.5 wheat, 4.5 strawberry, 3 carrot |
| Team B | 12 wheat, 9 strawberry, **8 pastures**, 5 cows, 3 sheep | 15 wheat, 5 strawberry, 3 tomato, 2.6 geese | 12 wheat, 5 strawberry |
| Team C | 12 wheat, 7 strawberry, **9 pastures**, 4.5 cows, 3.4 sheep | 15 wheat, 4 tomato, 4 strawberry, 3 geese | 15 wheat, 3 carrot |
| Team D | 10 wheat, 6 strawberry, 7 pastures, 3.6 cows, 3 sheep, 2 melon | 15 wheat, 4 tomato, 2 geese, 2 carrot | 9 wheat, 4 tomato |
| Metav4 | 15 strawberry, 8 wheat, 7 pastures | 13 strawberry, 13 wheat | — |

Answers to your question 4:
- **Is the animal farm opened first?** On NE, yes: they build pastures and place
  cows and sheep on day 6 itself. NE becomes the animal quad.
- **What goes on the later quads?** SW gets the **geese** (coops) and the first
  tomatoes. SE is almost pure crops.
- **Order within a quad:** structures and animals first, then wheat, then
  strawberry or tomato into the remaining cells.

Consensus grid, end of day 11 (Team A):
```
SSSSSSSSSS | SSSWWSWSSW | SWSWcccSSW | SggWscgSWS | SWssccgggW
WWgcgWWWWW | TWWWgWWW.. | TWWWgWWW.. | TTSSWS.... | TTWSWS....
```

## 5. What happens to the first quad (NW) after new land opens

- **Melons (10) are harvested around day 10 and become wheat**, and later tomato or
  strawberry.
- **They build 2 coops in NW on days 10–11** and add geese: the animal farm spreads
  into NW.
- Strawberry spreads across NW and NE row 0: `SSSSSSSSSS` by day 11.
- The day-0 cows and sheep stay where they are.

Answer to your question 5: **yes, they expand the animal farm into NW, and melon cells
switch to wheat.** The day-0 strawberries keep producing.

## 6. The middle game: they follow the shops

A fixed skeleton (opener, land steps, wheat backbone) plus **product modules switched
on by which shops open**. A new shop unlocks every 3 days from day 3.

| shop open by day 12 | what changes (per game, days 6–19) | the shop buys |
|---|---|---|
| **Pet Café** | carrot plantings **52 vs 3** | carrot ×2 |
| **Pizza Shop** | tomato **24 vs 14** | tomato, milk, wheat |
| Farmers Market | tomato 19 vs 13 | wheat, carrot, tomato, strawberry |
| **Yarn Store** | sheep **11 vs 3.5** | wool ×2 |
| Ice Cream Shop | cows 11 vs 7 | strawberry, milk, wheat |
| Bakery, Farmers Market | geese ~7.6 vs 5.8 | egg (Bakery) |

Answers to your question 6:
- **Do they follow the market?** Yes, the shop draw. Each shop they see switches on
  the crop or animal that shop buys. Whether they also react to *prices* is Codex's
  half of the work.
- **Is there a backup?** Wheat is the default. Every freed cell without a
  shop-driven assignment goes back to wheat, the next step.
- **When do they use fertilizer?** Never before day 6. Per game:

| | days 6–11 | days 12–19 |
|---|---|---|
| top four | wheat 1–9, strawberry 3–4 | **strawberry 28–40, wheat 20–40**, tomato 5–9 |
| Metav4 | 0 | strawberry 32, wheat 4 |
| v0.9.4 | strawberry 1 | strawberry 14, wheat 1 |

## 7. Questions you didn't ask, answered by the replays

**Worker time.** Share of worker-steps spent idle (PASS):

| | days 0–5 | days 6–11 | days 12–19 |
|---|---:|---:|---:|
| top four | 19–34% | **2–4%** | **0–1%** |
| Metav4 | 25% | 10% | 5% |
| **v0.9.4** | **54%** | **27%** | **15%** |

The top four keep their workers busy from day 6 onwards. **Our planner wastes a
quarter of its worker time in the mid-game.** This is the execution gap, and it
matters as much as the plan. Per game, days 0–19, they also do more of everything:

| | watering | fertilizing | planting |
|---|---:|---:|---:|
| top four | ~770 | 70–100 | ~190 |
| v0.9.4 | 624 | 17 | 150 |

**Workers.** 5 on day 0 → 7 on day 2 → 10 on day 8 → 12–13 by day 10, the same for
all four.

**Opponent and seat.** No visible effect on the plan (the land steps and grids don't
change). Team A won 10 of 11 today, in both seats.

**Deaths and digging.** 1–2 plants die per game. They dig 11–15 times per game,
mostly weeds and spent crops.

**Did the plan change in two days?** Yes:
- Team A and Team D added the SE quad and more wheat, carrot and geese.
- Team D moved its SW purchase from step 199 to Team A's step 220.
- The whole top is converging on one plan, which fits a shared source.

## 8. What this means for building it

- **The opener (days 0–5) is fully deterministic.** It could be reproduced exactly
  as a fixed script. There is nothing to "plan" there.
- **The mid-game is rule-shaped, not scripted.** The rules:
  - land on fixed steps;
  - the wheat backbone, replanted the next step;
  - shop-triggered modules (Pet Café → carrot, Pizza/Farmers Market → tomato,
    Yarn → sheep, Ice Cream → cows, Bakery → geese);
  - fertilizer on strawberry and wheat from day 6;
  - near-zero idle workers.

  Our planner has the right *architecture* for that; its settings and its task
  scheduling are what's off.
- **Our biggest single gap is not the plan but the idle 14 steps per replant and the
  27% idle workers.** Transplanting their plan into our planner without fixing that
  would repeat the earlier failures: every plan feature on its own came out neutral.

## 9. Open questions

1. **Where does the shared opener come from?** A public notebook from roughly 21–24
   Sept is the likeliest source. If it is public, it is the substrate to fork: it
   already *is* the top-four plan, and "substrate + our change" is the model we
   agreed for Metav4. (Eugene: see the ask in the handoff.)
2. Do they react to prices within a shop module, or only to shop presence? (Codex, part 1.)
3. Why buy SE at step 254–255 when Team D skips it half the time? Is it
   worth it? (Codex, part 2.)

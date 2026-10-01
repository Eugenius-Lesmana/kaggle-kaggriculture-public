# How the top four actually run their farm: land, layout, care, shops, prices

Date: 2026-09-24
Status: **extraction only.** Extends `docs/TOP3_MACRO_PLAN_2026-09-24.md` (same day)
with the mid-game detail Eugene asked for.
Inputs: 46 player-games of Team A, Team B, Team C and Team D
(`research/intake/replays/24 Sept/`, gzipped on main); Metav4 and ours/v0.9.4 on local
seeds 5791–5796 as the contrast.
Tools (untracked): `.cache/mid_extract.py` → `.cache/mid.pkl`,
`.cache/mid_report.py keyed|land|care|harvest|shopevent|price`,
`.cache/macro_report.py grid <days>`.

Engine facts used (from the engine table embedded in Metav4):

| | crops | | animals |
|---|---|---|---|
| wheat | yield from day 2, max 6 units by day 4 | goose | an egg every day, holds at most 4, needs a coop |
| carrot | day 2–3, max 4 | cow | milk every 2 days, holds 6, pasture |
| tomato | 1 unit a day from day 8, 4 days | sheep | wool every 3 days, holds 6, pasture |
| strawberry | 1 unit every 2 days from day 10, 4 times | shed | the 4 centre cells (4,4)–(5,5) |
| melon | one crop, max 6 units by day 12 | | |

---

## 1. Land timing: same every time, and why these steps

**Same in every game today, for every team:**

| quad | step | time | how it is paid for |
|---|---|---|---|
| NE | **150** | day 6, hour 5 | sells 6–8 wool on the same step |
| SW | **220** (sometimes 222) | day 9, hour 3 | same-step sales |
| SE | **254–255** | day 10, hour 14 | same-step sales |

**History:**
- On 22 Sept, Team D and Team G bought SW at step 198–200 (day 8), and Team A
  bought no fourth quad.
- By 24 Sept all four had moved to 220 and added SE at 254.
- Teams that were testing different timings converged on this one. That is evidence
  it beat day 8 in their own testing, not proof it is optimal.

**Why these steps: the pattern the data shows**

1. **Right after a shop reveal.** New shops unlock every 3 days at hour 0 (steps 72,
   144, 216, 288, …). NE is bought 6 steps after the day-6 reveal and SW 4 steps after
   the day-9 reveal. They buy land **after** seeing which shop just opened, so the new
   quad can be planned around it (§4).
2. **Just in time for a worker.** At every purchase a worker is **one step** from the
   new quad, and the quad is in use 2–4 steps later. The land is never idle, and cash
   isn't locked up before it can be used.
3. **Paid by same-step sales.** Cash before the purchase is often below the price
   (SW: $1.1–3.7k for $2,000; SE: $3.3–6.6k for $4,000). They sell wool and other
   stock on that same step to cover it.
4. **SE on day 10** follows the melon harvest, where 10 melon cells (60 units at ~$210,
   about $13k) fund the $4,000 quad.

**Is there a better timing?** Replays cannot answer it; only a test can. Codex's model
says an earlier purchase pays only if it creates an extra crop cycle without starving
seeds, animals or hires. The cheapest test is a sweep on our planner once it runs their
plan: SW at 200 / 220 / 240, and SE at 254 vs none.

## 2. The farm layout: an animal core around the shed

Consensus farm at the end of day 12 (Team A, 11 games; Team B and Team C are the same shape):

```
      x: 0 1 2 3 4 | 5 6 7 8 9
 y0      S S S S S | S S S S S     strawberry on the outer rim (top row, left column)
 y1      S S S S W | S W S S W
 y2      S W S W c | c c S S W     cows on (4,2),(5,2),(6,2)
 y3      S g g W s | c g S W W     geese on (1,3),(2,3),(6,3); sheep (4,3)
 y4      S W s s c | c g g g W     ← shed access (4,4),(5,4) is here
 ------------------+----------
 y5      W W g c g | W W W W W     ← shed access (4,5),(5,5); geese (2,5),(4,5), cow (3,5)
 y6      T W W W g | W W W W W
 y7      T T W W g | W W W . .
 y8      T T S S S | S W W . .
 y9      T T W S S | S W S . .     tomato block bottom-left (SW), x 0–1
```

- **Animals form one tight cluster around the shed**: about 8 animals within 2 steps of
  (4–5, 4–5). Feeding, care, collecting fertilizer and dropping products at the shed
  are all short trips.
  - Day 0: 2 cows + 3 sheep in NW next to the shed.
  - Day 6: cows and sheep in NE, next to the shed.
  - Day 9: geese and a cow in SW, next to the shed.
  - Days 10–11: two coops of geese in NW.
- **Animals per quad at day 12:**

  | quad | cows | geese | sheep |
  |---|---:|---:|---:|
  | NW | 2 | 2 | 3 |
  | NE | 4.4 | 1.5 | 2.8 |
  | SW | 1.8 | 2.9 | — |
  | SE | none | none | none |

- **Strawberry goes on the rim** (row 0 and column 0, 20+ cells): it is only harvested
  every 2 days, so it tolerates the long walk.
- **Wheat fills the ring between** the animals and the rim, and most of SE: it is
  harvested every 3 days, closer in.
- **The tomato block sits in the SW corner**, columns 0–1, rows 6–9.
- **Metav4 and v0.9.4 spread animals less tightly and keep far fewer geese** (1.6–1.9
  vs 5–8).

## 3. How they look after it (days 8–19)

**Animals.** At end of day, only 78–89% are fed and 79–88% cared for. Metav4 and ours
feed 88–100%. So they accept a missed feed now and then; an animal only dies after 2
unfed days, and that spare worker time goes to crops. Fertilizer is collected almost
every day (0–3% left uncollected; Metav4 leaves 3–14%).

**Harvest rhythm (per game, days 6–19):**

| | top four | Metav4 | v0.9.4 |
|---|---|---|---|
| wheat | **60–78 harvests at age 3**, 4.2 units each | 65 at age 3, 3.1 units | 59 at **age 4**, 4.0 units |
| strawberry | ~50 harvests, every 2 days, 2 units each | 39 | 50, 1.5 units |
| goose eggs | **31–43 harvests**, every ~2 days, 2.6–2.8 each | 10 | 14 |
| cow milk | 24–29, every 2 days, 3.9 each | 31 | 20 |
| wool | 15–22, every 3 days, 4.5 each | 21 | 14 |
| tomato | from age 8, every 1–2 days, 2 units | — | — |

**Wheat at age 3, not 4.** Watering and fertilizer inside the yield window get it to
~4.2 units by day 3, the same as our 4.0 at day 4, **one day sooner**. Over a 20-day
mid-game that is about a third more wheat cycles per cell.

**Watering.** About 61–67% of plants are watered each day, not all of them. A plant
only dies after 2 dry days, and watering only adds yield inside the yield window. So
they water where it pays: melon 100%, the rest on demand. Our planner waters wheat
74%, which is more than they do.

**Fertilizer at end of day:**

| | strawberry | wheat | tomato | carrot |
|---|---:|---:|---:|---:|
| top four | 28–33% | 22–23% (Team C 8%) | 13–17% | ~2% |
| Metav4 | 21% | 4% | 0% | — |
| v0.9.4 | 12% | 0% | — | — |

**Weeds.** 0.1–0.4 standing per day. They are cleared almost at once.

## 4. How they react to new shops

Event study: how often they plant or place the shop's product in the 3 days after a
shop unlocks vs the 3 days before, per unlock (18–31 unlocks each):

| shop unlocks | they add | before → after | first response |
|---|---|---:|---:|
| **Pizza Shop** | tomato | **1.7 → 5.9** | 16 steps |
| **Yarn Store** | sheep | **1.0 → 3.1** | 11 steps |
| **Smoothie Shop** | strawberry | 5.7 → 8.6 | 10 steps |
| Farmers Market | tomato | 1.6 → 2.7 | 42 steps |
| Brunch Spot | geese | 0.1 → 1.4 | 52 steps |
| Pet Café | carrot | 0 → 1.3 (but **52 vs 3** carrot over days 6–19) | ~5 days |
| Ice Cream Shop | cows | 1.1 → 1.3 | slow |
| Bakery | geese | 1.6 → 1.4 | no change |

- **Pizza, Yarn and Smoothie** get an immediate response, within half a day: the next
  free cells or structures go to that product.
- **Pet Café** doesn't get an immediate response. Carrot comes in bulk later, at the
  next wheat turnover.
- **Bakery and Ice Cream** shift little. Eggs and milk are already produced by the
  standing herd.

## 5. How they respond to prices

When a wheat cell is harvested and replanted on days 9–19:

| | carrot/wheat price when carrot chosen | when wheat chosen | tomato/wheat price when tomato chosen | when wheat chosen |
|---|---:|---:|---:|---:|
| Team A | **1.18** | 1.00 | 1.70 | 1.70 |
| Team B | **1.22** | 0.98 | 1.64 | 1.68 |
| Team C | **1.11** | 1.00 | 1.59 | 1.65 |
| Team D | **1.28** | 1.05 | 1.68 | 1.77 |

- **Carrot is price-driven.** They pick carrot over wheat when carrot is selling at
  about 1.1–1.3× wheat, and stay on wheat when it isn't.
- **Tomato is shop-driven, not price-driven.** The tomato-to-wheat price ratio is the
  same whether they plant tomato or wheat. Tomato follows the Pizza Shop and Farmers
  Market (§4).
- How they time **sales** against prices is Codex's part and is in progress
  (`docs/TOP3_MARKET_BEHAVIOUR_2026-09-24.md` when it lands).

## 6. Flexible, or an optimised path?

**Both, in layers:**

| layer | how fixed | evidence |
|---|---|---|
| Opener, days 0–5 | **fully scripted** | 100% identical moves and layout in 46 games |
| Land steps, hiring (5 → 7 → 10 → 12–13 workers), day-0 herd | **fixed schedule** | identical steps and days in every game |
| Layout skeleton (animal core, strawberry rim, SW tomato corner) | **fixed template** | 75–93% cell agreement through day 16 |
| What to replant, which animals to add, fertilizer and harvest targets | **adaptive rules** | only ~50% identical moves on days 6–11 and ~25% after, **even between games with the same shops**, so it is not a pre-recorded route per shop draw; reacts to shops within 10–16 steps; carrot follows prices |

**Summary:** a hand-optimised skeleton (timings and layout tuned offline, probably by
testing many variants) run by an adaptive planner for the day-to-day work. That is our
v0.9.4's architecture. The gap is in the skeleton's numbers and in how tightly the
workers are used, not in the kind of agent.

## 7. What we copy, in order (feeds the build)

1. **Execution.** Idle workers under 5% from day 6; replant in 1 step, not 14.
2. **Opener.** Days 0–5 transcribed exactly (§1 of the macro-plan doc).
3. **Skeleton:**
   - land at 150 / 220 / 254, bought just in time with same-step sales;
   - the animal core around the shed;
   - strawberry rim;
   - SW tomato corner;
   - hires at 5 → 7 → 10 → 12–13.
4. **Mid-game rules:**
   - wheat harvested at age 3, with watering and fertilizer in the yield window;
   - geese kept at ~5–8 and harvested every 2 days;
   - shop triggers: Pizza → tomato, Yarn → sheep, Smoothie → strawberry,
     Pet Café → carrot at the next turnover;
   - carrot replaces wheat when its price is ≥ ~1.15× wheat;
   - feed and care at ~85%, not 100%, when a worker has something better to do.
5. **Then tune** what the replays can't settle: SW/SE timing, the tomato block size,
   herd size.

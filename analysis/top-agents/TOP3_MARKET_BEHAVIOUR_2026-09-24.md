# Top-four market behaviour, days 0–19: buying, selling, fertilizer, cash

Date: 2026-09-24
Status: **analysis only.** Part 1 of Codex's market brief.
- **Extraction by Codex:** `.cache/extract_market_behaviour.py`,
  `.cache/summarize_market_behaviour.py` and `.cache/detail_market.py` in the Codex
  worktree `.tmp-codex-market-20260924` (untracked). Its money, seed, land and market
  reconciliation passed on **every one of 31,680 player-steps**.
- **Written up by Claude** after Codex ran out of usage, from Codex's
  `summary24.json` and `detail_market.py` output.

Inputs: 33 unique episodes (39 files, 6 exact duplicates), 46 player-games (Team B 15,
Team A 11, Team C 10, Team D 10). Physical plan:
`docs/TOP3_MACRO_PLAN_2026-09-24.md` and `docs/TOP4_MIDGAME_RESEARCH_2026-09-24.md`.

---

## 1. What they buy (per game, days 0–19)

| | cows | sheep | geese | wheat (product) | strawberry seeds | tomato seeds | carrot seeds | fertilizer |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| Team A | 7.9 | 5.0 | 8.5 | 133 | 34 | 21 | 27 (9/11 games) | 0 |
| Team B | 9.8 | 6.3 | 5.8 | 131 | 40 | 17 | 13 (12/15) | 0.8 (3/15) |
| Team C | 8.5 | 7.3 | 6.6 | 148 | 30 | 15 | 22 (6/10) | 0 |
| Team D | 7.5 | 7.3 | 5.9 | 140 | 27 | 16 | 25 (6/10) | 0 |

- **Cows and sheep from day 0; geese only from day 6–11**, which is when the coops go
  in.
- **Wheat is bought as a product, ~130–150 units a game**: animal feed, plus the
  1-unit buy/sell churn on day 0.
- **Fertilizer is essentially never bought.** All of it comes from the animals.

## 2. Fertilizer flow (per game)

| | collected | applied: wheat | strawberry | tomato | carrot | sold | sale price |
|---|---:|---:|---:|---:|---:|---:|---:|
| Team A | 274 | 48 | 46 | 9 | 2 | 162 | $67 |
| Team B | 276 | 49 | 47 | 6 | 1 | 164 | $66 |
| Team C | 279 | 23 | 41 | 8 | 0 | 194 | $62 |
| Team D | 265 | 43 | 33 | 9 | 2 | 169 | $66 |

- **About 100 of ~275 collected units go into crops**, mostly wheat and strawberry;
  the rest is sold.
- **The sales start on day 1 and are spread across the day**: 51–57 small batches a
  game, the most common hour being 0 (just after midnight).
- Team C fertilizes wheat half as much and scores lowest of the four.

## 3. When they sell

**Sales are mostly a fixed schedule.** Knowing only the step and the product predicts
whether they sell **91–93%** of the time. Two games of the same team share 35–40% of
their exact sale (step, product) pairs, and 44–52% of their purchases.

Timing by product (all four teams agree):

| product | first sold | main hours | avg price |
|---|---|---|---:|
| wheat | day 0 | hours 22, 0–2 | $37–38 |
| fertilizer | day 1 | hour 0, then spread | $62–67 |
| wool | day 6 | hours 1–5 | $144–168 |
| milk | day 8 | hours 17–21 and 1 | $129–158 |
| melon | **day 10 only** | hours 9–12 | $203–221 |
| egg | day 11–14 | **hour 22 (40–44%)** | $47–50 |
| strawberry | day 13 | hours 0–1, 5, 9 | $161–199 |
| carrot | day 11–19 | **hours 22–23 (70–80%)** | $42–47 |
| tomato | day 18 | **hours 22–23 (75–97%)** | $64–72 |

**Hours 22–23** fall just before the day's town-centre demand refresh. Eggs, carrot and
tomato are all sold into it.

**Selling does respond to price, but only for the expensive animal products and
strawberry.** In steps where two games had the same stock and one sold while the other
held, the one that sold saw a higher price:

| sale price when they sold vs held | wool | milk | strawberry | wheat, egg, fertilizer |
|---|---:|---:|---:|---:|
| difference | **+$49 to +$93** | +$5 to +$45 | +$9 to +$45 | about $0 |

So:
- **Wool, milk and strawberry** are sold on schedule, **but held back when the price is
  low.**
- **Wheat, eggs and fertilizer** follow the schedule regardless of price.

**Other associations (correlation, not proven cause):**
- They are **2× more likely to sell within 4 turns after the rival sold** (29–36% vs
  13–16% of opportunities).
- They are **1.5× more likely near a shop unlock** (27–35% vs 17–20%).
- Both fit a schedule that sells into the same demand refreshes the rival also targets.
- Across *all* steps they sell less often when the price is in its top quartile. That
  is a scheduling artefact: prices are high when nobody has sold recently, which is
  off-schedule.

## 4. Cash policy

**They run cash to $0 in every game** (absolute minimum $0 for all four; median game
minimum $0–1). There is no reserve.

**Land is paid for by selling on the purchase step** (see the mid-game doc, §1):
- NE: 6–8 wool is sold on step 150 itself.
- SE: follows the day-10 melon sale (~60–74 melons at ~$210).

## 5. What varies with the shop draw

- Carrot seeds are bought in only 6–12 of 10–15 games: the Pet Café and Farmers Market
  games (mid-game doc, §4).
- Tomato seeds vary between 15 and 21 per game, with the Pizza Shop.
- Geese go from 5.8 to 8.5 per team.

Everything else in §1–§4 is the same in every game.

## 6. What to copy (market side)

1. **No fertilizer purchases.** Collect all of it; apply ~100 (wheat ≈ strawberry,
   plus tomato); sell the rest in small batches from day 1.
2. **Buy wheat as feed**, not grow it for feed. Cows and sheep from day 0, geese from
   day 6.
3. **A sale schedule by product and hour.**
   - Eggs, carrot and tomato at hours 22–23.
   - Melon all on day 10.
   - Wool, milk and strawberry on schedule, but held back when the price is low
     (their held-vs-sold gap: $49–93 on wool).
4. **Spend to zero.** Fund land with same-step sales.

## 7. Not done: Codex part 2

Valuing their full schedule with `research/models/plan_value.py` and ranking
improvements was not started. It is not needed for the build (execution fixes, opener
and skeleton come first). It can run when Codex's usage resets.

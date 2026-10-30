# Work model: the full feature list (draft for review, 2026-10-18)

The model makes one decision per worker per turn: which job to head for next. It sees a list of **candidate jobs**
and, for each, the information below (the **features**). It can only react to what is in this list: anything
missing is invisible to it. Codex's W1 measurements of how top workers spend a day will add and correct items.

A decision's candidates share the context features (group H); each candidate has its own A-G.

## A. The job itself

| # | Feature | Meaning |
|---|---|---|
| A1 | Job type | Water, feed, care, harvest, collect fertilizer, fertilize, plant (which crop), dig, pick up at the shed (wheat, fertilizer, an animal), drop or place goods at the shed, place an animal on its pen, wait (stay or move to a useful spot) |
| A2 | Steps to the job | Shortest-path steps from the worker to the job's tile on our farm (0 if standing on it) |
| A3 | Steps including a detour | Steps if the job needs something fetched first, for example a shed trip for wheat before feeding |
| A4 | Turns to finish | Steps plus the action turns the job takes (for example feed then care is two) |
| A5 | Fits in today | Whether it can be finished before the day ends, and how many turns would be left after |
| A6 | Tile to shed | Steps from the job's tile to the nearest shed tile (matters for carrying the harvest back) |

## B. What is on the tile: crops

| # | Feature | Meaning |
|---|---|---|
| B1 | Crop and age | Which crop, days since planted, and its stage (growing, producing, finished) |
| B2 | Water | Watered today; days in a row without water (a plant dies after two dry days) |
| B3 | Units held | Fruit or yield currently on the plant, and how close to its maximum |
| B4 | Fertilizer | Whether fertilizer is active today and for how many more days |
| B5 | Next production | Nights until the plant next produces (strawberry, tomato) or how far into its yield window it is (wheat, carrot, melon) |
| B6 | Rot clock | Turns until fruit left on the plant starts to rot or is lost |
| B7 | Plan for the tile | What our plan wants on this tile (a crop, an animal, empty) and whether the tile matches it |

## C. What is on the tile: animals

| # | Feature | Meaning |
|---|---|---|
| C1 | Animal and age | Goose, cow or sheep; days since placed |
| C2 | Next production | Nights until it next produces (geese every night, cows every two, sheep every three) |
| C3 | Fed and cared | Fed today, cared for today, days in a row without food (it escapes after two) |
| C4 | Bonus and units | Care bonus built up so far, product units it is holding, and its holding limit |
| C5 | Fertilizer | Whether it has fertilizer ready to collect |

## D. Money

| # | Feature | Meaning |
|---|---|---|
| D1 | Product price | The product's price now, at dawn, and relative to its base price |
| D2 | Price trend | Today's highest and lowest price so far, and the change over the last few hours |
| D3 | Shop demand | How many open shops buy this product, how much they consume, and turns until the next consumption |
| D4 | Our stock | Units of this product we already hold in the shed and bags |
| D5 | Opponent's supply | Units of this product visible on the opponent's farm (on plants and animals), and how fast they have been selling it (from the market) |
| D6 | Immediate value | What the job is worth by the game's rules right now, for example units harvested times price, or the bonus unit care adds times the price |
| D7 | Future value | What the job adds to the tile's value over the rest of the game (from the future-value model; added later) |
| D8 | Input cost | What the job uses up: a wheat for feeding, a seed for planting, a fertilizer |

## E. Urgency

| # | Feature | Meaning |
|---|---|---|
| E1 | Turns until loss | Turns until something is lost if nobody does this job: a plant dies at midnight, an animal escapes, fruit rots, an animal produces tonight unfed |
| E2 | Deadline flag | Whether our guards already mark this cell as must-do today |

## F. The worker

| # | Feature | Meaning |
|---|---|---|
| F1 | Carrying | Wheat, fertilizer, products and animals in its bag, and how full the bag is |
| F2 | Who it is | Farmer or hand, and whether it was hired today (new hands appear at the shed) |
| F3 | Last job | Its previous job type and how many turns ago (continuity: finishing a run of animals, a row of crops) |

## G. Coordination and surroundings

| # | Feature | Meaning |
|---|---|---|
| G1 | Closer workers | How many other workers are closer to this job, and the nearest one's distance |
| G2 | Already taken | Whether an earlier worker already chose this job this turn |
| G3 | Cluster | How many other jobs lie within two steps of this one, and their combined value (a group worth visiting together) |
| G4 | On the way | Extra steps this job adds to the worker's trip toward the shed or toward the next valuable cluster |

## H. The game (shared by all candidates in a decision)

| # | Feature | Meaning |
|---|---|---|
| H1 | Time | Day, hour, turns left today, days left in the game |
| H2 | Our farm | Cash, hands, hires today, land owned, animals by kind, crops by kind, empty plantable cells |
| H3 | Our shed | Stock of wheat, fertilizer and each product; how full the shed is (risk of midnight overflow) |
| H4 | Shops | Which shops are open (how many of each), and the early-strawberry-buyer scenario |
| H5 | Opponent | Cash, animals and crops by kind (visible), recent selling pace by product |
| H6 | Market depth | Market stock of each product (how much selling would move the price) |
| H7 | Our seeds | Seeds in stock, by crop (added after the comparison above) |

## Not features

The label (which job the teacher actually chose), the decision's identity, the game, the teacher team, and the
final result are never given to the model as inputs: they would let it cheat.

## Compared with what the top teams describe (write-ups only, not their code; 2026-10-18)

Sources: the inputs described in the write-ups of the 4th, 5th, 7th, 28th, 31st and 48th places.

**They had, and we lacked (added below):**

| Added | Seen in | Status |
|---|---|---|
| H7 Our seeds in stock, by crop | 5th, 28th | core (planting depends on it) |
| D9 Demand from the shops already open: how many units of each product they will consume over the next 1, 3 and 6 days and the rest of the season (no guessing about shops not yet open) | 48th | **core** (Eugene, 2026-10-18) |
| D10 Units coming soon: what our plants and animals will produce in the next 1 and 3 days, by product | 48th | **core** |
| D11 Where our stock is: shed, bags and still on tiles, kept apart rather than summed | 48th | **core** |
| D12 What our stock would fetch if sold now, given market depth | 48th | **core** |
| H8 Cash gap to the opponent | 5th | **core** |
| D13 Recent sales of each product, ours and the opponent's: summary only (see below) | 28th, 31st | **core, summary** (Eugene, 2026-10-18) |
| D14 Expected demand from shops not yet open (a new shop every 3 days, chosen at random) | ours | optional |
| B8 Tile's land (quadrant) and coordinates | 28th, 48th | optional; risks learning one layout, so tested last |

**They had, and we keep as summaries:** the opponent's whole farm. They fed every opponent tile to the network;
the 7th-place team found the network barely used it beyond what shows in the market, so totals (H5, D5) suffice.

**We have, and they left to the network to discover:** the candidate list itself, distances relative to the
worker (A2-A6), coordination (G1-G4), the deadline flag (E2) and the rule values (D6, D7). A gradient-boosted
ranker cannot work these out from a raw grid the way their large networks could, so we give them explicitly.

**D13 in detail.** The market shows only prices and stock, but the opponent's sales can be worked out each turn:
the change in market stock, minus our own sales, minus what the shops consumed. From that we can describe, for each
product: how many units the opponent sold in the last 4 and 24 hours, at which hours it usually sells, and how the
price moved after. What it would let a worker do: time harvests around the opponent's selling, for example leave
strawberries on the plant while the opponent is flooding the market and pick them before its next wave. Its main
use is selling (market orders), which stays with the template for now; for job choice its value is less certain.
Cost: the full history is 24 numbers per product (216 in all); a summary is 3-4 per product. Suggestion: the summary
now, the full history only if selling is learned later. The 31st-place team found the opponent's sale timing worth
about $8k a game, but used it in its seller, not its workers.

**Optional features are tested by removal:** train with and without each; keep it only if the bench improves.

## Do the top teams use rules like our D7 (future value) and E2 (deadlines)?

Yes, in both cases.

- **Deadlines and guards:** the 48th place fed "remaining time before neglect causes loss" to its network; the 4th
  and 7th places kept rules for feeding unfed animals, selling what would overflow at midnight, the last-day
  drop-off and selling everything at the end; the 28th-place planner separated mandatory survival work from
  optional work and kept a cash floor for feed; the 1st place masked fertilizing that cannot pay.
- **Future value:** the 28th-place planner valued each tile's whole future schedule against market values and
  labour costs; the 31st valued stock kept overnight at 95% of the next morning's expected price; the 48th
  trained a value estimate of the final result.

Risk: a feature taken from our own rules can teach the model our rules' mistakes. Check: train once without D7 and
E2; if the model plays as well without them, drop them.

## Questions for review

1. Is there anything a top worker clearly reacts to that is missing?
2. Is anything here that a player could not know at that moment? (Everything listed is visible in the observation
   or derived from earlier observations; the opponent's shed and bags are hidden and not used.)
3. Groups D7 and E2 come from our own models and rules. Keep them, or let the model learn without our guidance?

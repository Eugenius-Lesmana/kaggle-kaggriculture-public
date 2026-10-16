# Template agent: progress on 2026-10-16

Supersedes [`TEMPLATE_PROGRESS_2026-10-11`](TEMPLATE_PROGRESS_2026-10-11.md), which stays unchanged as the
earlier record. Every figure below was measured; estimates are marked.

## Where it stands

| | Share of Metav4's final bank |
|---|---:|
| Before (10 October) | 0.892 |
| **Now: end-of-day fix (15 October)** | **0.913** on 24 paired seeds |
| Same version, seats swapped / against F1 / against F4 / fresh seeds | 0.916 / 0.919 / 0.918 / 0.896 |

The target was at least 0.9 of Metav4's bank. It is met in four of the five setups; fresh seeds sit just under.
The agent still does not beat Metav4: it wins 2 of 24 standard games.

## What changed: goods the engine was destroying

Three medal teams' write-ups each added rules for goods the engine destroys. Measured on our agent first:

- **Midnight overflow.** About 26 units a game were destroyed when workers' bags were emptied into a full shed.
  About 20 of them were lost because the bags alone held more than the shed's 100, so selling from the shed (which
  we already did at hour 23) could not help.
- **The last day.** About 56 units a game were still in bags when the game ended: workers harvested on the way
  home and reached the shed one move too late.

The fix: on the last day, a worker holding goods walks home before any other job once time is short; from hour 20,
when the crew's loads would overflow the shed, the most loaded workers near the shed bring theirs in.

| Setup | Our bank per game (SE) | Opponent's bank |
|---|---:|---:|
| Standard | +$2,113 (323), up in 23 of 24 | -$56 |
| Seats swapped | +$2,052 (272) | -$268 |
| Against F1 | +$2,201 (338) | -$198 |
| Against F4 | +$1,778 (343) | -$86 |
| Fresh seeds | +$1,107 (430) | -$163 |
| **Pooled** | **+$1,784 (185)** | -$179 |

Our own bank rose in every setup, by goods recovered rather than by the opponent earning less. Side costs: about
one more unfed goose a game and up to one more dry crop.

## A dollar ledger of what is still missing

Every remaining loss, in dollars per game at quoted prices, ranked the same way in all five setups and all
scenarios: animals left unfed on ordinary days ($7-8.5k, because an unfed day wipes the animal's bonus build-up),
unplanted owned land ($4.2-5.6k), uncollected fertilizer (about $2.4k), animals unfed on their payout night
($1.3-2k), crop deaths and rot ($1.1-1.6k), selling at worse prices than Metav4 ($0.6-2.5k), what is left of shed
losses (under $0.7k). These are gross values: no feed, labour or price response is subtracted, and in some
scenarios they add up to more than three times the real gap.

## What did not work since

| Attempt | Result (24 paired seeds unless marked) |
|---|---|
| Feed and care an animal in the same visit that empties it | Our bank +$85 (SE 452): level |
| Count feed only near hungry animals; fetch wheat when standing on a hungry animal | -$1,656 on 6 seeds; stopped |
| For a day after new land is bought, the nearest three workers plant it first | +$34 (SE 396): level, although the land filled 2-5 cells a day faster |

The pattern: every fix that needs worker time takes it from other work, and the ledger's biggest numbers do not
turn into money. The fixes that worked recovered waste at almost no cost in worker time. The part that hands out
worker time, a step-by-step scoring of jobs with hand-set weights, appears to be at its limit.

## What the top teams' write-ups taught us

The top agents were trained networks (behaviour cloning on replays, some with self-play), with a few rules on top;
see [`LEARNED_POLICIES_2026-10-15`](../../analysis/top-agents/LEARNED_POLICIES_2026-10-15.md). Their evaluation
methods match ours: paired seeds, both seats, our money and the opponent's reported separately.

## Next: a hybrid agent (in progress)

We are building a version that keeps the rules for the plan (what to grow and buy, land, herd, deadlines and the
end-of-day rules) and replaces the job scoring with a model learned from one top team's replays: for each worker,
the rules list the legal next jobs and the model chooses. It starts as a gradient-boosted ranker on a laptop.
Target: beat Metav4 in all five setups. Nothing has been measured yet; results will be published here.

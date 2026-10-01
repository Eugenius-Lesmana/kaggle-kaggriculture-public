# Kaggriculture: a counter-focused agent, and what the leaderboard taught us

Our work on the Kaggle **Kaggriculture** simulation competition: the agent we submitted, our analysis of the
leaderboard and the top teams, and an unfinished second agent.

| Part | Status | Where |
|---|---|---|
| Final agent: F4 + counter + race + wheat round-trip + look-ahead 10 + snipe | **Finished, submitted** | [`agent/`](agent/) |
| Leaderboard and top-agent analysis | **Finished** | [`analysis/`](analysis/) |
| A new agent: our own planner, built from what the top teams do | **Unfinished.** We ran out of time. Work continues. | [`next-agent/`](next-agent/) |

Everything here is a dated lab record. Numbers come from local games against a fixed opponent panel, or from
replays of public ladder games. Where a result did not hold up on the live ladder, we say so below.

## The game

Two players farm for a 30-day season (720 steps, 24 per day) and sell into **shared markets**. Whoever holds more
money at the end wins. Selling fewer units of a product raises the opponent's price for it, so every decision
also changes the opponent's income. Engine: `kaggle-environments` 1.32.7.

## What the ladder looked like

We measured it from 139 mid-ladder replays (ranks ~50–500, 137 teams): about **80% of teams play one tape
family** (Metav4 and its successors). A "tape" is a fixed table of actions per step, optimised offline for the
whole season. Nobody runs a public file unchanged; most are forks that change a few steps. Details in
[`analysis/leaderboard/`](analysis/leaderboard/).

Against that field, a strong tape agent mostly loses or draws to near-copies of itself, and the games are
decided by tiny edits: who sells first at a lifted price.

## Our final agent

[`agent/main.py`](agent/main.py) is the public **F4** notebook agent plus five small layers. Most of the 1.2 MB is
inherited and machine-generated. Our changes are a few hundred lines. They are shown as diffs in
[`agent/lineage/`](agent/lineage/).

| # | Layer | Size | Credit |
|---|---|---|---|
| 1 | **Counter**: reorders our SELL orders against a detected mirror opponent | ~90 lines | ours |
| 2 | **Race**: lets the tape's early-sale rule fire at any price and on the next sale | 2 lines | ours |
| 3 | **Wheat round-trip**: sells bought wheat in the same turn at the lifted price | ~100 lines | ours, written with Codex |
| 4 | **Look-ahead 10**: advances sales that the tape would make in the next 10 turns, not 3 | 1 constant | ours |
| 5 | **Snipe**: two empty-order guards, a carrot margin, and a sale-snipe switch | 4 lines | **from a public notebook** (`a-song-of-ice-and-fire-fixed-flexible`, by AlekseiProvorov), not ours |

The base F4 agent, and everything it builds on, belongs to its public authors. See [`NOTICE`](NOTICE) and
[`agent/NOTICE.txt`](agent/NOTICE.txt).

### Local results

Paired seeds, both seats, 80 games per cell, fresh seeds for each confirmation. Wins–losses(–ties) for the
newer agent in each row.

| Step | Compared with | Result | Evidence |
|---|---|---|---|
| Counter on F4 | F4 mirror | 70–4–6 | [`evidence/f4_screen`](evidence/f4_screen/) |
| + race + wheat | F4 + counter | 66–14 | [`evidence/f4_race`](evidence/f4_race/) |
| + look-ahead 10 | race + wheat | 58–18–4, then 66–12 on a second seed set | [`evidence/f4_race`](evidence/f4_race/) |
| + snipe (**final**) | look-ahead 10 | 60–18–2 | [`evidence/final_snipe`](evidence/final_snipe/) |
| Final | the public snipe notebook | 77–3 | [`evidence/final_snipe`](evidence/final_snipe/) |
| Final, guards | F4 + counter / F1 / F2 / Metav4 | 62–18 / 70–10 / 66–14 / 67–13 | [`evidence/final_snipe`](evidence/final_snipe/) |

One result went the other way: the public snipe notebook **beat look-ahead 10, 46–34** (seeds 8201–8240).
That is why the snipe lines are in the final agent.

### What happened on the live ladder

- **F1 + counter** (96 games): 51–44–1, rating about 2,186, peak about 2,350.
- **F4 + counter** (153 games): 93–58–2, rating about 2,200. It went **5–18 against opponents rated 2,300+**.
  Most of those losses were to *close F4 forks*: they play F4 exactly, then sell a little earlier at one or two
  steps. Its rating stood at 2,093 when we deactivated it.
- **Race + wheat** (231 games): rating about **1,898**, below F4 + counter, even though it beat F4 + counter
  66–14 locally. Our local panel did not predict the ladder. We have no verified explanation.
- **Look-ahead 10**, submitted on the final day, is rated **1,872.3**. **Look-ahead 10 + snipe** (the final agent,
  submitted last) is rated **1,776.9**. Neither rating has settled yet, but the snipe version is the lower of the
  two even though it beat look-ahead 10 locally 60–18–2.
- The public notebook whose four lines we added was around 2,300 when we looked. Locally our final agent beats
  it 77–3.

Take-away: none of our three late agents rates above F4 + counter, even though each beat its predecessor locally.
Tuning a late layer on a fixed local panel did not transfer to a ladder of forks that each change something
different. We have not established why.

## What the top teams do

Full write-up: [`analysis/`](analysis/). The short version:

- **Their edge is units, not prices.** The top three produce about 52% more units per game than our planner
  (54% from more cells and animals, 46% from higher yield per cell). They sell those units at about the same
  prices.
- **Fertilizer is timed to the yield window.** Wheat at age 2, strawberries at ages 9 and 13. On days 12–27,
  78% of wheat bonus-window plant-days and 94% of strawberry production-window plant-days are watered *and*
  fertilized. Over 80% of their fertilizer applications use fertilizer the same worker just collected from an
  animal.
- **The plan is layered.** A scripted opener and land/hire schedule, a fixed layout template, and adaptive
  rules on top: shops tilt which crop or animal gets the next free cell, and carrot follows its price.
- **There are no discrete "shop modes".** Farms cluster by season phase. Conversion mostly happens at harvest
  (60–63% of plantings follow a harvest).
- **Routes repeat across games, not across days.** The same worker on the same day follows a recognisable
  route in different games. That is what an offline-optimised tape looks like.
- **A fourth top team plays differently**: heavy product trading, about 3,470 wheat units sold per game, for
  a similar final bank.

## The next agent

Our own planner reaches about **0.70 of Metav4's bank** in paired games. We ran about 22 single changes meant
to close the gap. One was a small gain still waiting for confirmation; the rest were neutral or negative.
Copying the top teams' routes, plan or job priorities onto our executor did not work either. The gap is
structural: the top agents' whole season is optimised as one piece, offline.

The plan is to do the same for our own farm: search for a whole-season plan automatically, with real games as
the judge, and keep the planner as the fallback when a game drifts from the plan. That is unfinished.
See [`next-agent/`](next-agent/).

## Repository map

```
agent/        final submission, licence, notices, diffs of every layer we added
analysis/     leaderboard census, ladder diagnosis, top-agent studies (dated lab notes)
evidence/     result files behind the analysis (per-game rows, summary tables, scripts)
tools/        game screen, replay fetcher, opponent classifier
next-agent/   unfinished planner, its experiment log and roadmap
```

## Reproducing

```bash
pip install kaggle-environments==1.32.7 requests
python tools/screen.py --candidate agent/main.py --opponent agent/main.py --seeds 8201-8202 --seats 2 --workers 2
```

Full instructions: [`tools/README.md`](tools/README.md). Games take about 10–30 seconds each. Use at most
2 workers on a laptop.

## What is not here

- **Raw replays.** They belong to Kaggle and its competitors. We publish derived tables, and the scripts to
  rebuild them from replays you fetch yourself.
- A few large derived tables (over 1 MB). They are listed in
  [`evidence/README.md`](evidence/README.md#files-not-included).
- Our earlier agents (v0.1–v0.10) and the replay inspector. They stay in our working repository.

## Credits and licence

- Licence: **Apache-2.0** ([`LICENSE`](LICENSE)).
- The agent in [`agent/`](agent/) derives from public Kaggle notebooks. Their authors are credited in
  [`NOTICE`](NOTICE) and [`agent/NOTICE.txt`](agent/NOTICE.txt), and every upstream notice stays inside
  `agent/main.py`.
- Kaggle and the `kaggle-environments` contributors wrote the engine.
- Much of the analysis and code was written with AI assistants (Claude and Codex), under the authors' direction.
- Top-ranked leaderboard teams are anonymised as **Team A–G**; the same letter is the same team in every note.
  Other ladder opponents are replaced by hashes in `evidence/census/`. Kaggle episode and submission IDs are kept
  as evidence references.
- The snipe changes come from the public notebook `a-song-of-ice-and-fire-fixed-flexible` by AlekseiProvorov.

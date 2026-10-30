# The work model: learning who does which job next (plan, 2026-10-18)

Status: **plan, not started.** Part of Stage 3 in `PLAN.md`, brought forward because two measurements show daily
work is our biggest gap. Open for Eugene's challenges before any code.

## 1. Why this, now

From the same morning (same farm, animals, market), measured with `tools/compare_day.py`:

| Test | Result |
|---|---|
| Our template agent takes over the reference team's seat (60 games; 30 for three days) | The team's real play is worth about **$1.7-2k a day** more from day 12 on |
| The 4th-place agent takes over our seat in our own games (24 games) | It earns about **$1-1.4k a day** more on our own farm |

On our farm the top agent fertilizes far more, collects more fertilizer, waters more, feeds and cares more, and
harvests less often (more goods left on plants and animals, collected in batches). Our step-by-step job scoring
cannot be fixed by more rules: every rule fix took worker time from somewhere else. The model below learns the
whole trade-off at once from players who already make it well.

## 2. What the model decides, and what it does not

**Decides:** for every worker, every turn, which job to head for next: water, feed, care, harvest, collect
fertilizer, fertilize, plant, dig, a shed trip (pick up wheat, fertilizer or an animal; drop goods), place an
animal, or wait somewhere useful. It outputs one action per worker per turn, recomputed from the new state each
turn, so it reacts like the top agents and is never idle when a useful move exists.

**Does not decide (yet):** what to grow and where, how many animals, land, hires, and market orders. These stay
with the template agent's plan and market code for now, so a test of the work model measures only the work model.
The plan and opener are learned later (Stage 2/C); guards stay as rules (an animal on its second unfed day, a
dying plant, goods left at the end).

Movement is not learned: once a job is chosen, the worker takes a shortest path to it (the 4th-place team found
every top step it measured was a shortest-path move).

## 3. How learning from their games works on our farm (the central question)

The worry: the top teams play on their own layouts and particular shop sequences, so what they did might only fit
those conditions. Four things make it transfer.

**3.1 Their conditions are not one condition.** Measured on the D1 tables:

- All **6,694** games have a **different shop sequence**; all 64 possible pairs of first two shops occur.
- The reference team's own farm on day 12 varies widely across its 1,703 games: strawberries 10-46 cells (median
  25), wheat 11-51 (36), tomatoes 0-33 (8), animals 17-28 (22); **1,203 different farm compositions**.
- Opponents, prices, cash and days left differ in every game, and both seats are recorded.

So the model sees thousands of situations, not one. What it can learn is how good players **respond** to a
situation, not a single fixed layout.

**3.2 The model never sees "cell 47"; it sees relationships.** Each candidate job is described relative to the
worker and the moment: how many steps away, what is on the tile and in what state, what it is worth now and later,
how soon it will be lost, what the worker is carrying, how many other workers are closer, how many similar jobs
are clustered nearby, how far the shed is. A rule like "a worker carrying wheat, three steps from a sheep that
produces tomorrow, with wool expensive and six hours left, goes and feeds it" means the same on any layout. That is
why a farm arranged differently from theirs can still use what they learned.

**3.3 The scenario is an input, not a fixed background.** Prices, open shops (and what they buy), the opponent's
visible herd and crops, cash, day and hour go in with every decision. So the model can learn that a job's value
changes with the scenario (your point that their job values "fluctuate"), instead of one rule for all games.

**3.4 Their choices carry future value.** A top player waters a strawberry that is not due today, or skips a
harvest, because of what it will earn later. Imitating those choices teaches that future value without our
writing it down. Alongside, a separate **future-value model** learns from the 6,694 games what a farm (and later a
tile) is worth in final money from its current state; its estimates become inputs to the work model and the score
for the Judge.

**3.5 Labels from our own farm, and the correction loop (approved 2026-10-18).** Replays show top players on
their farms. Their habits fit their layout and paths; on our layout the best choice can differ. So we also record
what a top player does **on our farm**: the 4th-place agent (runnable on CPU, and shown to play sensibly when it
joins mid-game) takes over our seat from our saved mornings, and at every turn we record which job each of its
workers heads for. These labels carry a top player's judgement applied to our layout and distances. Then a loop:

1. Train on replays plus these labels.
2. Our model plays from saved mornings on the bench.
3. Collect the states where it went wrong (it lost value against the top agent from the same morning).
4. Ask the top agent what it would do in exactly those states; add those as labels.
5. Retrain, and repeat while the bench keeps improving.

This is the standard cure for imitation breaking on situations the teacher never saw (known as DAgger). It is
learning from the agent's behaviour, as with replays; its code is never copied into ours, and the agent remains a
held-out opponent only in the final tests that do not use its labels (the 5th-place agents stay fully held out).

**What does not transfer, and how we handle it**

| Risk | Handling |
|---|---|
| Our farm reaches states the teacher never saw (a smaller herd, a different layout, our plan's mistakes), and imitation errors snowball | Relative features (3.2); train on several top teams first, then specialise on the teacher; **labels from our own states** (3.5): a runnable top agent shows what it would do on our farm, and the correction loop keeps adding the states where our model goes wrong (approved by Eugene 2026-10-18) |
| Habits that only make sense with their plan (for example their strawberry block's morning run) | The plan stays ours for now; the bench shows whether a learned habit helps on our farm |
| Two teams with different styles averaged into nonsense | Learn from one consistent teacher in the final stage (27th- and 7th-place lesson); Eugene's teacher study picks it |

## 4. Data: from replays to training rows

Source: the D1 tables and exact replay (`src/kagml/replay_tables.py`). Each game is re-simulated step by step,
because features need the full state at the moment of each decision (the tables store farms only at dawn).

- **A decision** = a worker at a turn where it starts heading for a new job (the turn after its previous job, or
  at dawn). Turns spent walking to an already chosen job are not new decisions.
- **The label** = the first real job that worker then carried out (a non-move action that took effect, from
  `unit_actions.took_effect`) and its cell. Failed or trimmed actions never become labels.
- **The candidates** = every legal job for that worker that could still be reached and done today: all tiles with
  something to do, shed trips, placing an animal, waiting. Not filtered by our rules, so the model is not limited
  by our blind spots. We measure **coverage**: how often the teacher's choice is in the list (target over 95%).
- **Labels from our own farm:** the same extraction run on games where the 4th-place agent plays our seat from
  our saved mornings (3.5).
- **Sequential workers:** workers decide in order; a job already chosen by an earlier worker this turn is marked
  on later workers' candidates, so two workers do not run to the same melon.

Size: roughly 25 decisions per worker per day, 12 workers, 30 days, about 9,000 decisions per seat per game, each
with about 40 candidates. The reference team's 1,703 games would give about 15 million decisions; the first
dataset uses a sample (about 100 games) and grows only if the model needs it.

## 5. The model

**First version: a gradient-boosted ranker** (LightGBM, ranking objective, trained on the laptop). One decision is
one group; its candidates are the items; the label is the teacher's choice. Fast, handles mixed features well,
easy to inspect (which features drive each choice).

**Second version, only if needed: a small neural ranker** on Kaggle's GPUs (about 30 hours a week), able to look
at the whole farm at once rather than at candidate features alone.

**Features of a candidate** (first list; Codex's W1 measurements will add and correct):

- Job type; steps to reach it; total steps including any shed detour it needs.
- Tile state: crop or animal, age, watered or fed or cared today, days without water or food, units held and how
  close to the cap, fertilizer active, days to the next production, care bonus held, hours until fruit rots.
- Money: the product's price now and at dawn, relative to its base; shop demand for it; the opponent's visible
  supply of it; later the future-value model's estimate of what doing the job adds.
- Urgency: hours until something is lost if the job is not done.
- The worker: what it carries (wheat, fertilizer, products), how full its bag is.
- Context: hour, day, cash, hands, land, herd and crop counts, how many other workers are closer, how many similar
  jobs lie within two steps, whether an earlier worker already took this job.

## 6. How it is measured

1. **Offline:** coverage; top-1 and top-3 agreement with the teacher by job type and day band, on held-out games.
   Only a filter: two teams found offline accuracy does not predict playing strength.
2. **The saved-mornings bench** (minutes): the work model plays our seat from the same mornings as the template
   agent and the 4th-place agent, one and three days, on our own games. Target: close most of the $1-1.4k a day.
3. **Full games** against Metav4 (24 standard seeds), then the held-out group (F4, counter versions, the three
   top agents, fresh seeds), by scenario.

## 7. Steps and stop points

| Step | What | Stop if |
|---|---|---|
| 1 | Candidate and label extractor on a few games; coverage check | coverage under 90%: fix candidates first |
| 2 | Dataset on ~100 games from several top teams, plus top-agent labels on our saved mornings; first ranker; offline report | top-1 agreement no better than our template's own choices against the teacher |
| 3 | Plug into our agent behind a switch; bench against template and 4th place | no gain on the bench after fixing obvious failures |
| 4 | Full games against Metav4, then held-out opponents | no gain in full games |
| 5 | The correction loop (3.5): top-agent labels on our states, then on the states where our model went wrong; retrain | bench stops improving |
| 6 | More data, the future-value model, neural ranker | as needed |

## 8. Decisions (Eugene, 2026-10-18)

1. Teacher: several top teams first if they play alike (measured by the teacher study and W1), then compare with
   a reference-team-only model and keep whichever plays better on the bench.
2. Labels from our own states using the 4th-place agent, and the correction loop: approved.
3. Feature list: full list in `WORK_MODEL_FEATURES.md`, for Eugene's review before any code.

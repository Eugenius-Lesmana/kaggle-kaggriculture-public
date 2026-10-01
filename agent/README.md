# The submitted agent

`main.py` is the agent we submitted at the end of the competition: public **F4** plus five layers.

- SHA-256: `08486634bdc408de90d1bd53b1cd3ff54ed6c4fac3eefe0a0065395598d38211`. The file we submitted
  (`f9effa30093a8179…`) differs only in two inherited comment lines that named ladder teams. They are redacted here.
  Behaviour is identical.
- 10,321 lines, 1.2 MB. Almost all of it is inherited. The base is a stack of about 48 wrapper layers over a
  table of 41 whole-season action routes ("tapes"). Do not expect to read it top to bottom.
- Kaggle loads the **last callable defined in the file**. `main.py` ends with `agent = globals().pop('agent')`
  so that the entry point is the outermost layer.
- Licence: Apache-2.0 ([`LICENSE.txt`](LICENSE.txt)). Upstream credits: [`NOTICE.txt`](NOTICE.txt) and the
  header of `main.py`. Our changes are marked in [`lineage/`](lineage/).

## How the base works (short)

F4 is the end of a lineage of public notebooks: Metav4 → F1 → F4. Each step added sale-timing rules to the
last (F4 also adds an opening controller).

1. **A router** picks one of 41 precomputed routes at step 144, from the first two shops that open. Days 0–5
   share one opener.
2. **The route is a tape**: for every step it lists every worker's move and every market order.
3. **Layers on top** adjust the tape's market orders: sell a little earlier when the model expects a price
   fall (`MODELPX`), reorder sales within a turn (`V44Y`, `ORDERPRI2`), advance the tape's sales (`Step809`),
   and detect a mirror opponent (`RACE`).

Because the tape is built for the whole season, changing one early action usually breaks later ones. That is
why our changes touch only **market orders and sale timing** and never worker moves or crop choice.

## Our layers

Diffs are in [`lineage/`](lineage/). Line numbers refer to `main.py`.

| # | Layer | Where | Idea | Diff |
|---|---|---|---|---|
| 1 | **Counter** | `_counter_reorder`, line ~10151 | Against a detected exact copy of F4, F4's sale reorder (`V44Y`) assumes the copy plays its *input* order. The copy plays its *final* order. We take the finished action as the opponent hypothesis and best-respond once more, permuting only SELL orders in blocks of 2–6. | [`01`](lineage/01-counter-on-f4.diff) |
| 2 | **Race** | `_s809_apply`, line ~8193 | `Step809` already advances the tape's near-future sales. It only did so at quotes ≥ 50 and never for the next turn's first sale. We removed both limits (2 lines). This beats forks that sell a step before the tape does. | [`02`](lineage/02-race.diff) |
| 3 | **Wheat round-trip** | `_wheat_lead`, line ~10235 | The tape buys wheat on one step and sells it on the next. A later `SELL` in the same turn quotes at the lifted price, so selling in the same turn wins the race. The layer abstains if its own modelled revenue falls. Written with Codex. | [`03`](lineage/03-wheat-roundtrip.diff) |
| 4 | **Look-ahead 10** | `_S809_LOOK`, line 8187 | `Step809` advances sales the tape makes in the next 3 turns. We use 10. | [`04`](lineage/04-look-ahead-10.diff) |
| 5 | **Snipe** | lines ~1833, 1837, 4475, 4731 | Four changes taken from AlekseiProvorov's public notebook: two empty-order guards in the SELL-block scan, `_CA_MARGIN` −15 → −22 (carrot instead of wheat more readily), `_OR2_SN_K` 0 → 1 (sale snipe on milk, strawberry, wool, melon, egg when the rival holds stock). **Not our work.** | [`05`](lineage/05-snipe.diff) |

Design notes: [`analysis/our-agent/`](../analysis/our-agent/) (counter, wheat round-trip) and
[`analysis/leaderboard/`](../analysis/leaderboard/) (race, look-ahead).

## Why these layers

On the live ladder, F4 + counter lost mostly to **close F4 forks**. A fork plays F4 exactly, then sells earlier
or larger at one or two steps. The first difference is almost always a sale. We reproduced that locally with
stand-ins (F4 with the same two lines as layer 2) and then beat them.

Copying the forks' own edits did not work. F4's tape depends on the route chosen for the map, so an edit keyed
to a step number rarely fires on other maps: 13 harvested edits together scored 9–33–38 against our
submission. Making our own sale rule moderately more aggressive did work. Maximum aggression did not: it
lost 3–39 of 80 games against non-racing families ([`LADDER_F1`](../analysis/leaderboard/LADDER_F1_2026-09-27.md)).

## Results

All local, paired seeds, both seats, 80 games per cell. W–L(–T) for the newer agent.

| Step | Opponent | Result |
|---|---|---|
| Counter | F4 mirror | 70–4–6 |
| + race + wheat | F4 + counter | 66–14 |
| + race + wheat | F4 | 77–3 |
| + race + wheat | racing stand-in | 75–3–2 |
| + look-ahead 10 | race + wheat | 58–18–4, 66–12 (second seed set) |
| + snipe (final) | look-ahead 10 | 60–18–2 |
| Final | the public snipe notebook | 77–3 |
| Final | F4 + counter / F1 / F2 / Metav4 | 62–18 / 70–10 / 66–14 / 67–13 |

The look-ahead dose is non-monotonic against older families: look-ahead 20 gains more against F4 mirrors but
costs about 10 of 240 wins against F2/F1/Metav4. Look-ahead 10 has no measured cost
([`F4_RACE_LOOKAHEAD`](../analysis/leaderboard/F4_RACE_LOOKAHEAD_2026-09-29.md)).

Evidence: [`evidence/f4_race`](../evidence/f4_race/), [`evidence/final_snipe`](../evidence/final_snipe/),
[`evidence/f4_wheat`](../evidence/f4_wheat/), [`evidence/h1_counter`](../evidence/h1_counter/).

## Limits

- **The ladder disagreed with our local tests.** Race + wheat beat F4 + counter 66–14 locally and rated about
  1,898 on the ladder against about 2,100–2,200 for F4 + counter. Look-ahead 10 is rated 1,872.3 and the final agent
  (look-ahead 10 + snipe) 1,776.9, not yet settled. Locally the final agent beats the public snipe notebook 77–3, yet that notebook was
  around 2,300 when we looked. We do not know why.
- The 2,300+ opponents that are *not* F4 forks (different openers, wins of $3k–30k) are untouched. A sale-timing
  layer cannot fix a plan that produces fewer units.
- Results hold for our opponent panel and the standard engine configuration. The panel is public agents plus
  stand-ins, not the live ladder.
- Layer 5 is not ours (it is from AlekseiProvorov's public notebook). We kept it because that notebook beat layer 4
  locally (46–34), and the combination beat both.

## Run it

```bash
pip install kaggle-environments==1.32.7
python tools/screen.py --candidate agent/main.py --opponent agent/main.py --seeds 8201-8202 --seats 2 --workers 2
```

See [`tools/README.md`](../tools/README.md).

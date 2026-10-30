# Eugene's replay observations, tested on all 552 mornings (2026-10-23)

Eugene watched the biggest-gap mornings (games 10321 d20, 10312 d20, 10303 d24; template vs the 4th-place agent
from the same morning). Each observation was turned into a measure and checked on all 552 L1 mornings (24 games,
days 6-28, seat 0). Tool: `tools/behaviour_check.py`; per-job data `<data>/runs/behaviour/`.

| Observation | Measure (per day, all 552 mornings) | 4th place | Template | Verdict |
|---|---|---:|---:|---|
| We keep collecting milk when its price has collapsed; it ignores it | Milk collections at price <= 30 (total) | 23 | 517 | **Confirmed, strongly** |
| | Mean price when milk / wool is collected | 144 / 195 | 89 / 148 | It collects animal products when the price is high and leaves them waiting otherwise (12.3 vs 8.8 units waiting at night) |
| | Cow / sheep collections per day | 1.3 / 0.9 | 2.7 / 1.7 | |
| | Goose (egg) collections per day | 3.2 | 2.7 | It collects eggs more |
| It waters strawberries and tomatoes more, wheat and carrot less | Share of tiles watered by night: strawberry / tomato | 61% / 66% | 54% / 59% | **Confirmed for valuable crops** |
| | wheat / carrot | 62% / 70% | 63% / 63% | Not neglected across all days (it waters more overall) |
| It uses fertilizer better | Fertilizer applied: strawberry / tomato / wheat | 3.6 / 1.7 / 6.5 | 1.6 / 0.9 / 3.0 | **Confirmed**: about twice as much, on every crop |
| It harvests strawberries less, maybe only at certain times or on the way | Strawberry / tomato harvests | 3.9 / 2.5 | 4.8 / 2.9 | **Fewer harvests confirmed** |
| | Units waiting when a strawberry is harvested | 1.53 | 1.52 | Not by waiting for a fuller plant; the timing idea is not supported by this measure |
| Workers keep to their own area | Distinct tiles each worker stands on | 8.8 | 9.9 | **Mildly confirmed** (-11%) |
| Herd finished by about 17:00 | Hour of the last feed/care job | 19.6 | 20.9 | **Confirmed, smaller**: about an hour earlier on average |
| It buys less wheat and no carrot seed | Wheat / carrot seeds bought | 3.5 / 2.5 | 10.3 / 1.6 | **Wheat confirmed** (a third of ours); carrot not (it buys more) |
| It ignores weeds | Digs per day (earlier profile) | 2.2 | 2.2 | Not supported across all days |

## What it means for the work model

- **Collecting animal products only when the price is high** is the clearest new habit. It is a worker choice
  that depends on the market, so it belongs in the ranker: the product's price against its recent level should
  be an explicit feature (check whether the current features capture it; add it for the next ranker if not).
- **Fertilizer twice as often** and **more water on valuable crops** match the earlier day profile (fertilize
  12 vs 6) and are what the ranker should learn from L1; check the bench model's fertilizer and watering by crop.
- **Wheat seed buying** is a plan (market) decision; the swap test found buying worth nothing over one day, so it
  waits for the plan stage, but it is recorded here.

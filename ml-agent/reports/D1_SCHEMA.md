# D1 replay tables (schema version 1)

Source: `manifests/replays.csv`, frozen for each build as `<data>/datasets/d1/manifest.csv`.
Raw replays and all generated tables remain on the configured data drive. No real player/team names are copied.

Rebuild (Python 3.12, installed `kaggle-environments==1.32.7`, `pyarrow`; `duckdb` for queries):

```powershell
python tools/build_tables.py --workers 2
```

The command hashes raw compressed inputs, collapses duplicate episode IDs only when the decompressed replay bytes
match, feeds recorded actions into the installed native interpreter, and compares both seats' farms, market, town,
private inventories/seeds/shed, day/hour/player, status and reward on every frame including initialization.
Cash is also bridged independently every turn from successful market commitments and unit-operation cash changes.
Only complete, entirely reconciled games publish Parquet shards. Failure receipts live under `audit/`; `summary.json`
contains unique-episode retention by submission (a game counts once for each distinct participating submission).
Input SHA256 and extractor-source SHA256 govern resume. A changed extractor rebuilds shards. Use a new output folder
for a different corpus; existing unrelated shards are not deleted. No agent entry point or game runner is called.

Layout: `datasets/d1/<table>/<episode>.parquet`, Zstandard compression, fixed Arrow schemas. Per-episode shards avoid
holding the corpus in memory and make interruption resumable. `*.tmp` files are unpublished and ignored by queries.
The coordinator uses two game workers at most. Native RNG is tried first. A separately labelled `split-weeds` mode
supports the earlier local runner's weed RNG convention only if every full state still matches; no state is patched
to the recorded replay. A failed game has no table shards. Receipts distinguish mismatch field, frame and seat.

| Table | Grain / key | Fields and meaning |
|---|---|---|
| `games` | episode | `date` (listing createTime as supplied, no inferred timezone), `submission_0/1`, `team_0/1` (IDs), `rating_0/1` (initial listing rating), `bank_0/1`, `winner` (0/1, -1 tie), ordered `shops` list (duplicates retained), `rng_mode`, `frames` |
| `market_steps` | episode, step | All recorded pre-decision frames, including terminal frame. `day`, `hour`, `price_<product>`, `inventory_<product>` for nine products; `cash_0/1`. Prices are visible quotes, not necessarily execution prices. |
| `farm_daily` | episode, seat, day, x, y | Every tile at hour 0 including EMPTY and LOCKED. `step`, `kind`, `crop`, `age` (from planted_day or placed_day), `animal`, `yield_units`, `watered`, `fed`, `cared`, `fertilized_until_day`, `fertilizer_available`, `care_bonus`, `hands`, `land`. Non-applicable fields are NULL; hands/land are JSON strings repeated on tile rows. |
| `unit_actions` | episode, seat, step, unit | `unit=0` farmer; hands indexed from 1, reset daily. `x/y` before acting; NULL if nonexistent. `command` issued JSON, `effective_command` passed to native unit handler (e.g. atomic planting rejection becomes PASS), `took_effect`, `exists`, `cash_delta`. Omitted existing-hand commands are explicit PASS rows. Extra commands for nonexistent hands are retained with exists=false. |
| `sales` | episode, seat, step, order_index, product, price | Successful unit sales grouped by actual execution price within order. `units`, `price`, `revenue`. One order can create multiple rows as its marginal price changes. Includes $1 sales, which need not increase market inventory. |
| `market_orders` | episode, seat, step, order_index | Audit companion: issued `command` JSON, `attempted` (parser reached it), `took_effect`, `units` committed (one for successful HIRE/BUY_LAND), signed `cash_delta`. Includes invalid and capped-away orders with zero effect. This also records effective purchases and hires. |

`step=s` on actions/sales means the decision at market frame `s`, producing recorded frame `s+1`. The final market
frame has no following action. `took_effect` means the individual native operation changed tracked state; idempotent
commands and PASS have false. Worker-local changes are captured before other workers, market processing, decay or
midnight. A successful operation is not inferred from a whole-turn net difference. Position and inventory validity
come from the running engine, not guessed from the next replay frame.

`fertilizer_available`, watered/fed/cared, attempted/effect/exists are Boolean. IDs, coordinates, steps, counts,
prices and revenues are int64; cash, ratings and cash deltas float64; names/commands are strings. See
`src/kagml/replay_tables.py:SCHEMAS` for the exact machine-readable schemas.

## Query with DuckDB

```python
import sys
sys.path.insert(0, 'src')
from kagml.replay_tables import connect
con = connect()
print(con.sql('SELECT count(*) AS games FROM games').fetchall())
print(con.sql('SELECT product, sum(units) units, sum(revenue) revenue FROM sales GROUP BY product').fetchall())
```

Or direct SQL:

```sql
CREATE VIEW sales AS SELECT * FROM read_parquet('<data>/datasets/d1/sales/*.parquet');
CREATE VIEW market_steps AS SELECT * FROM read_parquet('<data>/datasets/d1/market_steps/*.parquet');
SELECT s.episode, s.seat, s.step, m.day, m.hour, s.product,
       sum(s.units) AS units, sum(s.revenue) AS revenue,
       m.cash_0, m.cash_1
FROM sales s JOIN market_steps m USING (episode, step)
GROUP BY ALL;
```

For stand-in training, form the episode × seat × decision-step × product grid first, then left join aggregate sales
and fill absent units with zero. Never train only on nonzero-sale rows. Join market_steps on the SAME step for
pre-decision features; never on step+1. Final banks, winner, final shops and future daily snapshots are outcomes,
not features. Split by entire episode (both seats together) and hold out teacher submissions as required by PLAN.
Current-hour shops can be recovered from previous dawn snapshots only if retained separately; final `games.shops`
is not a safe current-hour feature. Unit action and sales labels are privileged outcomes, not observations.

Verification: `python tools/check_tables.py` checks accepted receipts against shard row counts, primary keys,
sales/order revenue reconciliation, one-frame-ahead bank bridges, daily coverage, and rejected-shard absence.

To rebuild the identical frozen corpus, pass --manifest <data>/datasets/d1/manifest.csv (use a separate --output directory for a clean rebuild). The verifier also proves a deliberately altered recorded market quote is rejected; it never changes a raw replay file.

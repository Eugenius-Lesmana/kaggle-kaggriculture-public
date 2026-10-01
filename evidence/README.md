# Evidence

Result files behind the notes in [`analysis/`](../analysis/) and the agent's results in
[`agent/README.md`](../agent/README.md). Each directory is named in the notes that use it.

## Game screens (our agents against local opponents)

One JSON per match-up: seeds and seats, per-game banks (`cand`, `opp`), products sold and revenue. Named
`<candidate>_vs_<opponent>[_<seeds>].json`. Seeds in a file name are the seed range used.

| Directory | Contents |
|---|---|
| `final_snipe/` | The final agent (`L10S`) against look-ahead 10, the public snipe notebook (`SN`), F1, F2, F4 + counter, Metav4. |
| `f4_race/` | Race, look-ahead dose (`v2s_L6`…`L40`), the 13 fork edits (`E*`), and the day-6 variant (`d6_*`). `cF4` = F4 + counter. `m_*` and `c_*`: the submission (`cF4`) and the race candidate (`cF4s809`) against the opponent panel. |
| `f4_wheat/` | The wheat round-trip against its parent and the guards, plus the mechanism trace for seed 6827. |
| `f4_screen/`, `f4_guard/` | F4 + counter against F1, F4 and the older panel. |
| `h1_counter/`, `h1_counter_f1/`, `h1_counter_f1_confirm/` | The counter on Metav4 and on F1, with `verify.py`. |
| `mpx_race/`, `mpx_guard/` | Stand-ins for racing forks, and the cost of maximum selling against older families. |

## Replay-derived tables (top teams, ladder)

| Directory | Contents | Note |
|---|---|---|
| `census/` | Per-player classification of ladder games by which known agent they match. | Team names other than ours are **replaced by a short hash**. |
| `modes/` | Farm snapshots at shop openings, conversion timing, skeleton (hires, land). | [`MODES_STUDY`](../analysis/top-agents/MODES_STUDY_2026-09-29.md) |
| `backbones/` | Route stability, action-accuracy tables. | [`ROUTE_BACKBONES`](../analysis/top-agents/ROUTE_BACKBONES_2026-09-29.md) |
| `production_gap/` | Capacity × yield decomposition, rollover harvest. | [`PRODUCTION_GAP`](../analysis/top-agents/PRODUCTION_GAP_2026-09-30.md) |
| `market_edge/` | Product mix, selling behaviour, revenue decomposition. | [`MARKET_EDGE`](../analysis/top-agents/MARKET_EDGE_2026-09-30.md) |
| `yield_drivers/` | Per-crop yield summaries, fertilizer timing, regressions. | [`YIELD_DRIVERS`](../analysis/top-agents/YIELD_DRIVERS_2026-09-30.md) |

The analysis scripts (`analyze.py`, `summarize.py`, `study.py`) are included. Their default input paths pointed
at our local replay folders (shown as `<repo>/…`). Point `--intake`, or the environment variable the script
names, at replays you fetched with [`tools/fetch_episodes.py`](../tools/fetch_episodes.py).
Some scripts also read control results with `git show <branch>:…` from our working repository. For those, use the
matching files in [`next-agent/evidence/routeopt/`](../next-agent/evidence/routeopt/) instead.

Top-ranked teams appear as Team A–G, including in the compressed tables and in the scripts that select a team by
name. Those scripts read replay folders and team fields by the *real* name, so map `Team A`–`G` back to the
leaderboard names yourself before re-running them.

## Files not included

Over 1 MB each, or tied too closely to one replay. Re-create them with the scripts in the same directory.

| File | Size | Rebuild |
|---|---:|---|
| `backbones/routes.csv.gz` | 6.6 MB | `python evidence/backbones/analyze.py` |
| `backbones/medoids.csv` | 3.9 MB | same |
| `production_gap/game_product_phase.csv` | 2.6 MB | `python evidence/production_gap/analyze.py` |
| `yield_drivers/plant_lifecycles.csv` | 9.2 MB | `python evidence/yield_drivers/analyze.py --intake <replays>` |
| `yield_drivers/fertilizer_actions.csv` | 5.5 MB | same |
| `next-agent/evidence/executor/team_a_tape_112920694.json`, `team_a_backbone.json` | 58 KB, 40 KB | `extract_backbone.py`. A literal action tape of another team's game; we do not republish it. |

## Reading a screen file

```python
import json
rows = json.load(open("evidence/final_snipe/L10S_vs_SN_8201-8240.json"))["rows"]
wins = sum(r["cand"] > r["opp"] for r in rows)
```

Win means the candidate's final bank is higher. Ties are equal banks. The bank ratio `cand / opp` is our
secondary measure. For plan experiments we report our bank and the opponent's bank separately, because a
change can win by lowering the opponent's income ([`PLAN_VS_MARKET`](../next-agent/docs/PLAN_VS_MARKET_2026-09-30.md)).

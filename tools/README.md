# Tools

Four stand-alone scripts. Install once:

```bash
pip install kaggle-environments==1.32.7 requests
```

Run from the repository root. Scripts print and write JSON; they do not modify anything else.

## `screen.py`: paired game screen

Plays a candidate against an opponent on a list of seeds, in both seats, through the real engine and the real
Kaggle agent loader (the last callable in the file). Reports wins, the bank ratio, and, per product, units
sold, revenue per unit and the end-of-game prices. Every step of every sale is checked against the observed
money change, and steps that disagree are dropped and counted.

```bash
python tools/screen.py --candidate agent/main.py --opponent next-agent/planner/main.py \
    --seeds 9001-9040 --seats 2 --workers 2 --json out.json
```

- `--seeds 9001-9040` or `9001,9005`. 40 seeds × 2 seats = 80 games, our standard cell.
- `--seats 1` plays the candidate as player 1 only.
- **Use at most 2 workers on a laptop.** Twelve crashed ours.
- The JSON has one row per game: `cand` and `opp` banks, `own_sold`, `own_revenue`, `opp_sold`,
  `opp_revenue`, harvest, plant and fertilizer counts, and failures. Check a result file for zero banks before
  trusting it.
- Games take about 10–30 seconds each.

Compare two result files on identical seeds and seats with
[`next-agent/evidence/routeopt/paired.py`](../next-agent/evidence/routeopt/paired.py).

## `fetch_episodes.py`: download a submission's public games

```bash
python tools/fetch_episodes.py <submissionId> replays/<name> --workers 4
```

Uses Kaggle's public episode service. No login. It saves `<episodeId>.json.gz` per game and an
`episodes.json` listing with both players' rewards and ratings. Replays are not included in this repository.
Read the competition rules before you redistribute any.

## `reproduce.py`: which agent is this ladder player running?

Replays one player's observations step by step through a fresh copy of each candidate agent and compares its
actions with what the player did. An exact copy of a deterministic agent matches every step. Used for the
census and the ladder diagnosis in [`analysis/leaderboard/`](../analysis/leaderboard/).

```bash
python tools/reproduce.py "replays/<name>/*.json.gz" --candidates metav4 --workers 2 \
    --extra F4=agent/main.py --out census.json --skip-team "<your team name>"
```

The built-in `CANDIDATES` table names public-notebook agent files that are **not in this repository**. Give
your own with `--extra name=path` and pick them with `--candidates`.

## `fingerprint.py`: does a replay run the Metav4 tape family?

```bash
python tools/fingerprint.py "replays/<name>/*.json.gz"
```

Before step 144 the family's router always plays route 0, so the opening is a clean fingerprint. After that it
reports the best-matching of the 41 routes. It reads the tape out of a Metav4 file; see the script header.

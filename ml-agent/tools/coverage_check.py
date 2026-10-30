"""Step 1 check: how often is the teacher's actual next job in our candidate list?

python tools/coverage_check.py [n_games] [submission]     (defaults: 5 games of the reference team 56711476)
"""
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import raw_replays  # noqa: E402
from kagml.replay_tables import connect  # noqa: E402
from kagml.work_data import decisions, load_replay  # noqa: E402

n_games = int(sys.argv[1]) if len(sys.argv) > 1 else 5
sub = int(sys.argv[2]) if len(sys.argv) > 2 else 56711476
con = connect()
games = con.sql(f"select episode, case when submission_0={sub} then 0 else 1 end from games "
                f"where submission_0={sub} or submission_1={sub} order by episode limit {n_games}").fetchall()
hit, total, miss_kinds, sizes = Counter(), Counter(), Counter(), []
for episode, seat in games:
    path = next(p for p in raw_replays(sub).parent.glob(f"*/{episode}.json.gz"))
    replay = load_replay(path)
    rows = con.sql(f"select step, unit, x, y, command, took_effect from unit_actions "
                   f"where episode={episode} and seat={seat}").fetchall()
    for step, unit, label, cands in decisions(replay, seat, rows):
        kind = label[0].split(":")[0]
        total[kind] += 1
        sizes.append(len(cands))
        if label in cands:
            hit[kind] += 1
        else:
            miss_kinds[label[0]] += 1
all_hit, all_total = sum(hit.values()), sum(total.values())
print(f"{len(games)} games, {all_total} decisions, coverage {all_hit / all_total:.1%}, "
      f"median candidates {sorted(sizes)[len(sizes) // 2]}")
for kind, n in total.most_common():
    print(f"  {kind:20s} {n:6d} decisions  coverage {hit[kind] / n:.1%}")
print("most common misses:", miss_kinds.most_common(8))

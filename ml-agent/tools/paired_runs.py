"""Paired comparison of run_full folders: share, wins and margin difference (se over seed means).

python tools/paired_runs.py BASE_RUN RUN [RUN ...]
"""
import json
import statistics
import sys
from collections import defaultdict

from kagml.paths import runs


def load(run):
    out = {}
    for p in (runs() / run).glob('*.metrics.json'):
        m = json.loads(p.read_text())
        ours, theirs = m['banks']  # already [ours, opponent's]
        out[(m['seed'], m['seat'])] = (ours, theirs)
    return out


def main():
    base, *others = sys.argv[1:]
    b = load(base)
    for run in [base, *others]:
        r = load(run)
        keys = sorted(set(r) & set(b))
        share = sum(r[k][0] for k in keys) / sum(r[k][1] for k in keys)
        wins = sum(r[k][0] > r[k][1] for k in keys)
        base_share = sum(b[k][0] for k in keys) / sum(b[k][1] for k in keys)
        by_seed = defaultdict(list)
        for k in keys:
            by_seed[k[0]].append((r[k][0] - r[k][1]) - (b[k][0] - b[k][1]))
        diffs = [statistics.mean(v) for v in by_seed.values()]
        se = statistics.stdev(diffs) / len(diffs) ** 0.5 if len(diffs) > 1 else 0
        print(f'{run:16s} games {len(keys):3d} share {share:.3f} wins {wins:2d} '
              f'({base} {base_share:.3f} on these games) margin vs {base} {statistics.mean(diffs):+8.0f} (se {se:5.0f}) seeds better {sum(d > 0 for d in diffs)}/{len(diffs)}')


if __name__ == '__main__':
    main()

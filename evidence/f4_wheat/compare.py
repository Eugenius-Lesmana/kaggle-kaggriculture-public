"""Compare two screen.py outputs on identical seed/seat keys."""

import json
import sys


def rows(path):
    data = json.load(open(path, encoding='utf-8'))
    return {(r['seed'], r['side']): r for r in data['rows']}


candidate, parent = map(rows, sys.argv[1:3])
assert candidate.keys() == parent.keys()
assert len(candidate) >= 80


def record(table):
    diffs = [r['cand'] - r['opp'] for r in table.values()]
    return (sum(d > 0 for d in diffs), sum(d < 0 for d in diffs),
            sum(d == 0 for d in diffs), round(sum(diffs) / len(diffs), 2))


paired = [(candidate[k]['cand'] - candidate[k]['opp']) -
          (parent[k]['cand'] - parent[k]['opp']) for k in candidate]
lost_wins = sum(parent[k]['cand'] > parent[k]['opp'] and
                candidate[k]['cand'] <= candidate[k]['opp'] for k in candidate)
gained_wins = sum(parent[k]['cand'] <= parent[k]['opp'] and
                  candidate[k]['cand'] > candidate[k]['opp'] for k in candidate)
print('games', len(candidate), 'candidate W/L/T/mean margin', record(candidate),
      'parent', record(parent), 'paired mean margin gain', round(sum(paired) / len(paired), 2),
      'gained/lost wins', (gained_wins, lost_wins),
      'paired improvements/declines/ties',
      (sum(d > 0 for d in paired), sum(d < 0 for d in paired), sum(d == 0 for d in paired)))

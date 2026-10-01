"""Fit compact priority trees from replay actions, split by whole episode.

Run from repository root. The local 29 Sept archive is read by absolute path and
never copied into the worktree. One replay is held in memory at a time.
"""
import gzip
import json
import random
import sys
import zlib
from collections import Counter, defaultdict
from pathlib import Path

from sklearn.tree import DecisionTreeClassifier

sys.path.insert(0, str(Path(__file__).resolve().parent))
from value import OPS, due, features

ROOT = Path(__file__).resolve().parents[2]
NEW = Path(r'<repo>/research\intake\replays\29 Sept top')
CORE = set(OPS) - {'DIG', 'PLANT'}
MOVE = {'NORTH', 'SOUTH', 'EAST', 'WEST'}
SEED = 20260930


def sources():
    for folder in sorted((ROOT / 'research/intake/replays/24 Sept').iterdir()):
        if folder.is_dir():
            for path in sorted(folder.glob('*.json.gz')):
                yield '24', folder.name.split(' - Top')[0], path, None
    for folder in sorted(NEW.iterdir()):
        manifest_path = folder / 'episodes.json'
        if not folder.is_dir() or not manifest_path.exists():
            continue
        submission = int(folder.name)
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        seats = {str(e['id']): next((j for j, a in enumerate(e['agents'])
                                    if a.get('submissionId') == submission), None)
                 for e in manifest['episodes']}
        for path in sorted(folder.glob('*.json.gz')):
            seat = seats.get(path.name.split('.')[0])
            if seat is not None:
                yield '29', folder.name, path, seat


def chosen_seat(replay, team, seat):
    if seat is not None:
        return seat
    norm = lambda name: ''.join(c for c in name.casefold() if c.isalnum())
    return next((j for j, name in enumerate(replay.get('info', {}).get('TeamNames', []))
                 if norm(name) == norm(team)), None)


def records(replay, seat):
    hands = defaultdict(list)
    steps = replay['steps']
    for i in range(1, len(steps)):
        obs = steps[i - 1][seat]['observation']
        action = steps[i][seat].get('action') or {}
        if not isinstance(action, dict):
            continue
        farm = obs['farms'][seat]
        positions = [farm['farmer']] + list(farm.get('hands') or [])
        commands = [action.get('farmer')] + list(action.get('hands') or [])
        for hand, pos in enumerate(positions):
            cmd = commands[hand] if hand < len(commands) else None
            if not isinstance(cmd, list) or not cmd:
                cmd = ['PASS']
            inventory = obs['private']['inventories']
            hands[hand].append((i, obs, tuple(pos), inventory[hand] if hand < len(inventory) else {}, cmd))
    return hands


def candidates(obs, inventory, position):
    tiles = obs['farms'][obs['player']]['tiles']
    for y, line in enumerate(tiles):
        for x, tile in enumerate(line):
            for op in due(tile, inventory, obs['day']):
                if op in CORE:
                    yield op, (x, y), features(obs, op, (x, y), inventory, position)


def tree_json(tree):
    t = tree.tree_
    return {'feature': t.feature.tolist(), 'threshold': [round(float(v), 4) for v in t.threshold],
            'left': t.children_left.tolist(), 'right': t.children_right.tolist(),
            'value': [round(float(v[0, 1] / sum(v[0])), 6) if len(v[0]) == 2 else 0.0
                      for v in t.value]}


def evaluate(groups, tree, baseline):
    counts = Counter()
    by_op = defaultdict(Counter)
    for rows, answer, base in groups:
        scores = tree.predict_proba([row for _, _, row in rows])[:, 1]
        ranked = sorted(range(len(rows)), key=lambda j: (-scores[j], j))
        selected = rows[ranked[0]][:2]
        op = answer[0]
        counts['n'] += 1
        counts['top1'] += selected == answer
        counts['top3'] += answer in [rows[j][:2] for j in ranked[:3]]
        counts['baseline'] += base == answer
        by_op[op]['n'] += 1
        by_op[op]['top1'] += selected == answer
        by_op[op]['baseline'] += base == answer
        by_op[selected[0]]['predicted'] += 1
        by_op[base[0]]['baseline_predicted'] += 1
    return {'n': counts['n'], 'top1': round(counts['top1'] / counts['n'], 4) if counts['n'] else None,
            'top3': round(counts['top3'] / counts['n'], 4) if counts['n'] else None,
            baseline: round(counts['baseline'] / counts['n'], 4) if counts['n'] else None,
            'by_command': {op: {'n': c['n'], 'recall': round(c['top1']/c['n'], 4),
                                 'precision': round(c['top1']/c['predicted'], 4) if c['predicted'] else None,
                                 'f1': round(2*c['top1']/(c['n']+c['predicted']), 4),
                                 'baseline_recall': round(c['baseline']/c['n'], 4),
                                 'baseline_precision': round(c['baseline']/c['baseline_predicted'], 4)
                                 if c['baseline_predicted'] else None,
                                 'baseline_f1': round(2*c['baseline']/(c['n']+c['baseline_predicted']), 4)}
                           for op, c in sorted(by_op.items()) if c['n']}}


def main():
    random.seed(SEED)
    samples = {'within': {'train': [], 'test': []}, 'next': {'train': [], 'test': []}}
    games = Counter()
    coverage = Counter()
    for cohort, team, path, seat in sources():
        try:
            with gzip.open(path, 'rt', encoding='utf-8') as f:
                replay = json.load(f)
        except (OSError, json.JSONDecodeError):
            coverage['bad_replay'] += 1
            continue
        seat = chosen_seat(replay, team, seat)
        if seat is None:
            coverage['unknown_seat'] += 1
            continue
        episode = path.name.split('.')[0]
        # The same episode may occur in multiple team folders: keep every seat
        # and duplicate download of that game on one side of the split.
        split = 'test' if zlib.crc32(f'{cohort}:{episode}'.encode()) % 5 == 0 else 'train'
        games[cohort, split] += 1
        for hand, turns in records(replay, seat).items():
            next_work = [None] * len(turns)
            upcoming = None
            for j in range(len(turns)-1, -1, -1):
                next_work[j] = upcoming
                if turns[j][4][0] in CORE:
                    upcoming = j
            for j, (step, obs, pos, inv, cmd) in enumerate(turns):
                op = cmd[0]
                sampled = zlib.crc32(f'{episode}:{hand}:{step}'.encode())
                if op in CORE and sampled % 12 == 0:
                    jobs = due(obs['farms'][seat]['tiles'][pos[1]][pos[0]], inv, obs['day'])
                    if len(jobs) >= 2:
                        coverage['within_multi'] += 1
                        if op in jobs:
                            rows = [(candidate, pos, features(obs, candidate, pos, inv, pos))
                                    for candidate in jobs]
                            samples['within'][split].append((rows, (op, pos), (jobs[0], pos)))
                        else:
                            coverage['within_uncovered'] += 1
                if op not in MOVE or sampled % 32 or not (j == 0 or turns[j-1][4][0] in CORE or obs['hour'] == 0):
                    continue
                k = next_work[j]
                if k is None or k - j > 12 or turns[k][1]['day'] != obs['day']:
                    continue
                target_op = turns[k][4][0]
                target = turns[k][2]
                if target_op not in CORE:
                    continue
                rows = list(candidates(obs, inv, pos))
                coverage['next_attempt'] += 1
                if len(rows) < 2 or (target_op, target) not in [(a, b) for a, b, _ in rows]:
                    coverage['next_uncovered'] += 1
                    continue
                nearest = min(rows, key=lambda r: (r[2][18], r[1][1], r[1][0], r[0]))[:2]
                samples['next'][split].append((rows, (target_op, target), nearest))
        if sum(games.values()) % 50 == 0:
            print('games', sum(games.values()), 'within', len(samples['within']['train']),
                  'next', len(samples['next']['train']), flush=True)
        del replay

    result = {'seed': SEED, 'games': {f'{c}_{s}': n for (c, s), n in games.items()},
              'coverage': dict(coverage), 'models': {}}
    export = {}
    for kind, max_leaves in [('within', 64), ('next', 96)]:
        train = samples[kind]['train']
        X, y = [], []
        for rows, answer, _ in train:
            X.extend(row for _, _, row in rows)
            y.extend((op, pos) == answer for op, pos, _ in rows)
        model = DecisionTreeClassifier(max_leaf_nodes=max_leaves, min_samples_leaf=80,
                                       random_state=SEED)
        model.fit(X, y)
        export[kind] = tree_json(model)
        result['models'][kind] = {'train_choices': len(train), 'train_rows': len(X),
                                  'test': evaluate(samples[kind]['test'], model,
                                                   'cell_rule' if kind == 'within' else 'nearest_due_job')}
        print(kind, result['models'][kind], flush=True)
    export['scale'] = 1000
    out = Path(__file__).resolve().parent
    (out/'model.json').write_text(json.dumps(export, separators=(',', ':')), encoding='utf-8')
    (out/'results.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print('coverage', result['coverage'], 'games', result['games'])


if __name__ == '__main__':
    main()

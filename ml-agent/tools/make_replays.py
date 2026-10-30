"""Turn recorded full games (run_full output) into replay pages for the game's own viewer.

python tools/make_replays.py OUT_DIR RUN[:PLAYER] [RUN[:PLAYER] ...]

RUN is a folder under the data drive's runs/ (or any folder) holding <stem>.json.gz + <stem>.metrics.json. From
each run, the game whose margin is closest to the run's mean margin is picked (a typical game, not the best one);
pass a .json.gz file instead of a folder to render that exact game. Writes OUT_DIR/<run>-<seed>-seat<k>.html and
prints the banks.
"""
import gzip
import json
import statistics
import sys
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.core import get_player
from kagml.paths import runs


def typical(folder, player=None):
    rows = [json.loads(p.read_text()) for p in sorted(folder.glob('*.metrics.json'))]
    rows = [r for r in rows if player is None or r['name'] == player]
    mean = statistics.mean(r['margin'] for r in rows)
    best = min(rows, key=lambda r: (abs(r['margin'] - mean), r['seat'], r['seed']))
    stem = next(p for p in folder.glob(f"*-{best['seed']}-seat{best['seat']}.metrics.json")
                if json.loads(p.read_text())['name'] == best['name']).name[:-len('.metrics.json')]
    return folder / f'{stem}.json.gz', best, mean


def render(replay):
    env = make('kaggriculture', configuration=replay['configuration'], debug=False)
    window = {'debug': False, 'playing': False, 'step': 0, 'controls': True, 'environment': replay, 'logs': []}
    return get_player(window, env.html_renderer(env, 'html'))


def main():
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    for spec in sys.argv[2:]:
        run, _, player = spec.partition(':') if not spec.endswith('.json.gz') else (spec, '', '')
        path = Path(run) if Path(run).exists() else runs() / run
        if path.is_dir():
            path, m, mean = typical(path, player or None)
            note = f'typical of {path.parent.name}: mean margin {mean:,.0f}'
        else:
            m, note = json.loads(Path(str(path)[:-len('.json.gz')] + '.metrics.json').read_text()), 'chosen game'
        with gzip.open(path, 'rt', encoding='utf8') as f:
            replay = json.load(f)
        target = out / f"{path.parent.name}-{m['seed']}-seat{m['seat']}.html"
        target.write_text(render(replay), encoding='utf8')
        opponent = Path(m['opponent']).parent.name if m['opponent'].endswith('.py') else m['opponent']
        print(f"{target.name}: {m['name']} (seat {m['seat']}) {m['banks'][0]:,.0f} vs {opponent} "
              f"{m['banks'][1]:,.0f}, margin {m['margin']:,.0f} ({note}); {target.stat().st_size/1e6:.1f} MB")


if __name__ == '__main__':
    main()

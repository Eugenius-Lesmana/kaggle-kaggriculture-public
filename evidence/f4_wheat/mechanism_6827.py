"""Reproduce the selected wheat race through the real Kaggle engine."""

import json
from pathlib import Path

from kaggle_environments import make


candidate = 'agents/ours/h1-counter-f4-wheat-candidate/main.py'
parent = 'agents/ours/h1-counter-f4-candidate/main.py'
env = make('kaggriculture', configuration={'seed': 6827}, debug=True)
env.run([candidate, parent])
steps = env.toJSON()['steps']
rows = []
for step in (327, 328, 329):
    observation = steps[step][0]['observation']
    farms = observation['farms']
    rows.append({
        'step': step,
        'price': observation['market']['prices']['WHEAT'],
        'market_inventory': observation['market']['inventory']['WHEAT'],
        'bank': [farm['money'] for farm in farms],
        'shed_wheat': [steps[step][p]['observation']['private']['shed'].get('WHEAT', 0)
                       for p in (0, 1)],
        'issued_market': [steps[step + 1][p]['action'].get('market', []) for p in (0, 1)],
    })
assert any(o[:2] == ['BUY_PRODUCT', 'WHEAT'] for o in rows[0]['issued_market'][0])
assert any(o[:2] == ['SELL', 'WHEAT'] for o in rows[0]['issued_market'][0])
Path('evaluation/f4_wheat/mechanism_6827.json').write_text(
    json.dumps(rows, indent=2), encoding='utf-8')
print(rows)

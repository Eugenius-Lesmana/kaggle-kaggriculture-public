"""Controlled state-injection check, not a played F4 replay.

Feeds the recorded observations from episode 113883512 through the actual
Kaggle loader, then imposes the clone hypothesis at step 327. This isolates
the wheat market rule without claiming those are F4's own preceding actions.
"""

import gzip
import hashlib
import json
from pathlib import Path

from kaggle_environments.agent import get_last_callable


base = Path('agents/ours/h1-counter-f4-candidate/main.py').read_bytes()
path = Path('agents/ours/h1-counter-f4-wheat-candidate/main.py')
assert path.read_bytes().startswith(base)
assert hashlib.sha256(base).hexdigest() == 'd29a6e1f37967f4662dc08225b56a1f4ced3975316493bfd8e5d5dc6fcd806c3'
agent = get_last_callable(path.read_text(encoding='utf-8'), path=str(path))
assert agent.__name__ == 'agent'

replay = json.load(gzip.open('research/intake/replays/27 Sept ours/113883512.json.gz', 'rt'))
for step in range(328):
    observation = dict(replay['steps'][step][0]['observation'])
    observation.setdefault('step', step)
    if step == 327:
        agent.__globals__['_COUNTER_MIRRORS'][0] = True
    action = agent(observation, replay['configuration'])

assert action['market'] == [['BUY_PRODUCT', 'WHEAT', 63], ['SELL', 'WHEAT', 63]]
assert agent.telemetry['wheat_leads'] == 1
assert agent.telemetry['predicted_margin'] > 0
print('loader, prefix, buy 63 + same-turn sell 63: verified')

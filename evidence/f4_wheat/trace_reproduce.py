import json
import sys
from collections import defaultdict
from pathlib import Path

from kaggle_environments import make
from kaggle_environments.agent import get_last_callable


path = 'agents/ours/h1-counter-f4-candidate/main.py'
other = 'agents/ours/h1-substrate-f4/main.py'
env = make('kaggriculture', configuration={'seed': 6827}, debug=True)
env.run([path, other])
replay = env.toJSON()
policy = get_last_callable(Path(path).read_text(encoding='utf-8'), path=path)
events = defaultdict(list)
step_meta = {}
matched = 0

for step in range(len(replay['steps']) - 1):
    obs = dict(replay['steps'][step][0]['observation'])
    obs.setdefault('step', step)
    want = replay['steps'][step + 1][0]['action']

    def profile(frame, event, arg):
        if event != 'return' or not isinstance(arg, dict) or 'market' not in arg:
            return
        if frame.f_locals.get('observation') is not obs:
            return
        wheat = [(i, list(o)) for i, o in enumerate(arg['market'])
                 if o and len(o) >= 3 and o[1] == 'WHEAT' and o[0] in ('BUY_PRODUCT', 'SELL')]
        events[step].append((frame.f_code.co_name, frame.f_code.co_firstlineno, wheat))

    if step in (250, 252, 254, 256, 257, 259, 266, 268, 270, 272, 274, 276, 277, 282,
                326, 327, 328, 329):
        sys.setprofile(profile)
    try:
        got = policy(obs, replay['configuration'])
    finally:
        sys.setprofile(None)
    if got != want:
        raise AssertionError((step, got, want))
    native = policy.__globals__['_IMPL'].chassis.players[0]
    tape = policy.__globals__['_IMPL'].chassis.routes[2 if step >= 648 else native['route']][step]
    step_meta[step] = {'route': native['route'], 'tape_market': tape.get('market')}
    matched += 1

out = []
for step, stages in events.items():
    changes = []
    last = None
    for name, line, wheat in stages:
        if wheat != last:
            changes.append({'layer': name, 'line': line, 'wheat': wheat})
            last = wheat
    if len(changes) > 1 or (changes and changes[0]['wheat']):
        market = replay['steps'][step][0]['observation']['market']
        obs = replay['steps'][step][0]['observation']
        out.append({'step': step, 'quote': market['prices']['WHEAT'],
                    'inventory': market['inventory']['WHEAT'],
                    'shed_wheat': obs['private']['shed'].get('WHEAT', 0),
                    'bank': obs['farms'][0]['money'],
                    'route': step_meta[step]['route'],
                    'tape_market': step_meta[step]['tape_market'],
                    'issued_market': replay['steps'][step + 1][0]['action'].get('market'),
                    'rival_market': replay['steps'][step + 1][1]['action'].get('market'),
                    'changes': changes})

print('matched', matched, 'steps', 'wheat events', len(out))
for item in out[:12]:
    print(item)
Path('evaluation/f4_wheat/trace_6827.json').write_text(json.dumps(out, indent=2), encoding='utf-8')

"""Check the preview harness on one of our own recorded games: the template agent, warmed up and dropped into a
snapshot, should reproduce the real game exactly (the recording was played by the same template agent).

python tools/preview_check.py <our_game.json> [step] [turns]
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.preview import TemplatePlayer, pin_weeds, play, snapshot_from_replay, summary  # noqa: E402

path, step = sys.argv[1], int(sys.argv[2]) if len(sys.argv) > 2 else 240
turns = int(sys.argv[3]) if len(sys.argv) > 3 else 24
replay = json.load(open(path))
pin_weeds(True)                      # our runner pinned the weed draw
snap = snapshot_from_replay(replay, step)

t = time.perf_counter()
ours = TemplatePlayer()
ours.warm(replay, seat=0, upto=step)
print(f"warm-up to step {step}: {time.perf_counter() - t:.1f}s")

t = time.perf_counter()
end = play(snap, [ours, "recorded"], steps=turns, replay=replay)
print(f"template plays {turns} turns from the snapshot: {time.perf_counter() - t:.2f}s")
rec = replay["steps"][step + turns][0]["observation"]["farms"]
s = summary(end)
for p in (0, 1):
    print(f"seat {p}: preview cash {s[p]['cash']:.0f} vs recorded {rec[p]['money']:.0f} | goods {s[p]['goods']:.0f} "
          f"crops {s[p]['crops']} animals {s[p]['animals']} hands {s[p]['hands']} land {s[p]['land']}")

"""Pin source hashes and live globals; evaluate only the initial observation."""
import argparse
import hashlib
import json
from pathlib import Path

from measure import load, ROOT, OUT


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--f4-source", type=Path, required=True)
    args = parser.parse_args()
    from kaggle_environments import make

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 8301})
    rows = []
    for label, path in (("metav4", ROOT / "agents/ours/h1-substrate-metav4/main.py"), ("f4", args.f4_source)):
        namespace = load(path)
        action = namespace["agent"](env.state[0].observation, env.configuration)
        rows.append(dict(source=label, path=f"agents/ours/h1-substrate-{label}/main.py", sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                         opening_market=action["market"],
                         modelpx_hours=list(namespace.get("_S758_HOURS", [])),
                         modelpx_apply=getattr(namespace.get("_s758_apply"), "__name__", None)))
    (OUT / "source_audit.json").write_text(json.dumps(rows, indent=2))
    print(json.dumps(rows))

"""Write manifests/replays.csv: one row per game on the data drive, so the raw replays can be rebuilt without it.

python tools/build_manifest.py
Columns: episode, folder (submission the file was fetched under), created, sub_0, sub_1, team_0, team_1, reward_0,
reward_1, rating_0, rating_1, bytes, sha256. Seats come from the listing's agent order (index 0, 1).
"""
import csv
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from kagml.paths import REPO, data_root  # noqa: E402

raw = data_root() / "raw" / "replays"
listing = {}
for f in raw.glob("*/episodes.json"):
    for e in json.loads(f.read_text(encoding="utf-8")).get("episodes", []):
        agents = sorted(e.get("agents", []), key=lambda a: a.get("index", 0))
        if len(agents) == 2:
            listing[str(e["id"])] = (e.get("createTime", "")[:19], agents)

rows, missing = [], 0
for path in sorted(raw.glob("*/*.json.gz")):
    eid = path.name.split(".")[0]
    if eid not in listing:
        missing += 1
        continue
    created, (a, b) = listing[eid]
    rows.append({"episode": eid, "folder": path.parent.name, "created": created,
                 "sub_0": a["submissionId"], "sub_1": b["submissionId"], "team_0": a.get("teamId"), "team_1": b.get("teamId"),
                 "reward_0": a.get("reward"), "reward_1": b.get("reward"),
                 "rating_0": round(a.get("initialScore") or 0, 1), "rating_1": round(b.get("initialScore") or 0, 1),
                 "bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})

out = REPO / "manifests" / "replays.csv"
with out.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"{len(rows)} games written to {out}; {missing} files without a listing entry")

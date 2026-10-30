"""Download a submission's ladder episodes from Kaggle's public episode service (no login).
Copied from the competition repository's research/tools/fetch_episodes.py; --skip-under added here.

Usage: python research/tools/fetch_episodes.py <submissionId> <out_dir> [--workers 4]
Saves <episodeId>.json.gz per completed public episode (skips existing files) and
episodes.json (the listing, with both agents' rewards and ratings).
"""
import argparse, gzip, json, os, time
from concurrent.futures import ThreadPoolExecutor
import requests

LIST_URL = "https://www.kaggle.com/api/i/competitions.EpisodeService/ListEpisodes"
REPLAY_URL = "https://www.kaggleusercontent.com/episodes/{id}.json"


def fetch(eid, out):
    path = os.path.join(out, f"{eid}.json.gz")
    if os.path.exists(path):
        return eid, "exists"
    for attempt in range(4):
        try:
            r = requests.get(REPLAY_URL.format(id=eid), timeout=120)
            if r.ok:
                with gzip.open(path, "wb", compresslevel=9) as f:
                    f.write(r.content)
                return eid, "ok"
        except requests.RequestException:
            pass
        time.sleep(3 * (attempt + 1))
    return eid, "failed"


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("submission", type=int)
    ap.add_argument("out")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--skip-under", help="skip episodes already saved anywhere under this folder")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    listing = requests.post(LIST_URL, json={"submissionId": a.submission}, timeout=60).json()
    json.dump(listing, open(os.path.join(a.out, "episodes.json"), "w"), indent=1)
    ids = [e["id"] for e in listing.get("episodes", [])
           if e.get("state") == "COMPLETED" and e.get("type") == "EPISODE_TYPE_PUBLIC"]
    if a.skip_under:
        have = {f.split(".")[0] for _, _, fs in os.walk(a.skip_under) for f in fs if f.endswith(".json.gz")}
        held = [i for i in ids if str(i) in have and not os.path.exists(os.path.join(a.out, f"{i}.json.gz"))]
        ids = [i for i in ids if i not in set(held)]
        print(len(held), "already saved under another submission, skipped")
    with ThreadPoolExecutor(a.workers) as pool:
        results = list(pool.map(lambda i: fetch(i, a.out), ids))
    from collections import Counter
    print(len(ids), "episodes:", dict(Counter(s for _, s in results)))

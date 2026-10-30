"""Rebuild D1: python tools/build_tables.py --workers 2. Resumes verified shards by code+input hashes."""
import argparse
import csv
import hashlib
import gzip
import json
import sys
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from kagml.paths import REPO, datasets, data_root
from kagml.replay_tables import TABLES, build_one


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--workers', type=int, choices=(1, 2), default=2)
    parser.add_argument('--limit', type=int)
    parser.add_argument('--manifest', type=Path, default=REPO/'manifests/replays.csv')
    parser.add_argument('--output', type=Path, default=datasets()/'d1')
    args = parser.parse_args()
    manifest = args.manifest.read_bytes()
    records = list(csv.DictReader(manifest.decode('utf-8').splitlines()))
    if args.limit:
        records = records[:args.limit]
    unique = {}
    for row in records:
        previous = unique.setdefault(row['episode'], row)
        if previous['sha256'] != row['sha256']:
            paths = [data_root()/'raw'/'replays'/r['folder']/(r['episode']+'.json.gz') for r in (previous,row)]
            if gzip.decompress(paths[0].read_bytes()) != gzip.decompress(paths[1].read_bytes()):
                raise ValueError('conflicting duplicate episode '+row['episode'])
    records = list(unique.values())[:args.limit]
    root = args.output
    root.mkdir(parents=True, exist_ok=True)
    (root/'manifest.csv').write_bytes(manifest)
    for table in (*TABLES, 'audit'):
        (root/table).mkdir(parents=True, exist_ok=True)
    signature = hashlib.sha256((REPO/'src/kagml/replay_tables.py').read_bytes()).hexdigest()
    tasks = [(r, str(root), signature) for r in records]
    counts = Counter()
    submissions = {}
    totals = Counter()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        for n, audit in enumerate(pool.map(build_one, tasks, chunksize=1), 1):
            counts[audit['reason']] += 1
            totals.update(audit.get('rows', {}))
            for submission in {audit['sub_0'], audit['sub_1']}:
                tally = submissions.setdefault(submission, Counter())
                tally['total'] += 1
                tally[audit['reason']] += 1
            if n % 25 == 0 or n == len(tasks):
                progress = {'completed':n,'total':len(tasks),'outcomes':dict(counts),'rows':dict(totals),'submissions':submissions,'signature':signature}
                (root/'summary.json').write_text(json.dumps(progress,indent=2),encoding='utf-8')
                print(json.dumps({k:v for k,v in progress.items() if k not in ('submissions','signature')}),flush=True)
    (root/'README.md').write_text('D1 recorded-action replay tables. Rebuild from kaggriculture-ml: python tools/build_tables.py --workers 2\nSee reports/D1_SCHEMA.md for grains, timing, schemas and DuckDB queries.\nOnly fully reconciled complete games have Parquet shards. audit/ contains exclusions; summary.json has totals.\n',encoding='utf-8')


if __name__ == '__main__':
    main()

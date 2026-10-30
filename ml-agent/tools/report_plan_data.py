"""Final package P corpus report; requires complete generation, verification and audit receipts."""
from collections import Counter,defaultdict
import csv
import datetime as dt
import hashlib
import importlib.metadata
import json
from pathlib import Path
import statistics
import subprocess
import time
import plan_dataset as D
import plan_games as G


def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])


def main():
    check=json.loads((G.RUN/'checks.json').read_text());verify=json.loads((G.RUN/'verification.json').read_text());assert check['passed'] and verify['passed']
    assert subprocess.run(['git','diff','--exit-code','eb22c63','--','src','vendor','agents'],capture_output=True).returncode==0
    seeds=G.seed_rows();seed_map={int(r['seed']):r for r in seeds};turns=D.read_csv(G.REPO/'manifests/turns.csv');markets=D.read_csv(G.REPO/'manifests/turn-markets.csv')
    original=json.loads((G.RUN/'markets-original.json').read_text());new=[r for r in turns if r['source'] in ('l1bal','tfull')]
    groups=defaultdict(list)
    for r in new:groups[r['source'],r['split'],seed_map[int(r['game'])]['B'],D.teacher_seat(r)].append(r)
    counts=[]
    for (source,split,b,seat),rows in sorted(groups.items()):
        counts.append(dict(source=source,split=split,B=b,seat=seat,seeds=len({r['game'] for r in rows}),segments=len(rows),turns=sum(int(r['turns']) for r in rows),worker_decisions=sum(int(r['worker_decisions']) for r in rows)))
    D.write_csv(G.REPO/'reports/PLAN_DATA_COUNTS.csv',counts)
    seed_counts=[]
    for b in range(3):
        for split in ('train','analysis2','all'):
            rows=[r for r in seeds if int(r['B'])==b and (split=='all' or r['split']==split)]
            seed_counts.append(dict(B=b,split=split,seeds=len(rows),ordered_pairs=len({r['pair'] for r in rows}),previously_unseen_pairs=len({r['pair'] for r in rows if int(r['prior_fit_pair_count'])==0}),seed_list=' '.join(r['seed'] for r in rows)))
    D.write_csv(G.REPO/'reports/PLAN_SEED_COVERAGE.csv',seed_counts)
    D.write_csv(G.REPO/'reports/PLAN_MARKET_VOCAB.csv',[dict(token=i,op=k[0],item=k[1] if len(k)>1 else '',supported=k[0]!='BUY_PRODUCT' or k[1] in ('WHEAT','FERTILIZER')) for i,k in enumerate(D.VOCAB)])
    families=[json.loads((G.RUN/'seeds'/f"{r['seed']}.json").read_text()) for r in seeds]
    timing=[]
    for f in families:
        timing.append(dict(seed=f['seed'],B=f['B'],split=f['split'],family_seconds=f['seconds'],template_game_seconds=f['template']['seconds'],teacher_day_generation_seconds=sum(r['generation_seconds'] for r in f['days']),teacher_full_seconds=sum(m['seconds'] for m in f['full_games']),teacher_calls_days=sum(r['teacher_calls'] for r in f['days']),teacher_calls_full=sum(m['timing']['turns'] for m in f['full_games'])))
    D.write_csv(G.REPO/'reports/PLAN_DATA_TIMING.csv',timing)
    summary=[]
    for source in ('l1bal','tfull'):
        for split in ('train','analysis2'):
            rows=[r for r in new if r['source']==source and r['split']==split]
            summary.append([source,split,len({r['game'] for r in rows}),len(rows),f"{sum(int(r['turns']) for r in rows):,}",f"{sum(int(r['worker_decisions']) for r in rows):,}"])
    new_orders=sum(int(r['orders']) for r in markets if r['source'] in ('l1bal','tfull'))
    rule=json.loads((G.RUN/'seed-rule.json').read_text())['rule'];analysis2=[r['seed'] for r in seeds if r['split']=='analysis2']
    elapsed=time.time()-(G.RUN/'seed-rule.json').stat().st_mtime
    versions={p:importlib.metadata.version(p) for p in ('kaggle-environments','numpy','torch','pyarrow')}
    tools=[G.REPO/'tools'/p for p in ('plan_games.py','plan_dataset.py','plan_pipeline.py','check_plan_data.py','verify_plan_data.py','report_plan_data.py')]
    provenance=dict(base_commit='eb22c63',branch='dev/eugene-codex-plandata',versions=versions,tools_sha256={p.name:G.sha(p) for p in tools},inputs=json.loads((G.RUN/'inputs.json').read_text()),generated_sources=['l1bal','tfull'],test_game_contents_read=0,workers=2,hashseed=0,elapsed_seconds=elapsed)
    G.save(G.RUN/'provenance.json',provenance)
    text=f'''# Codex to Claude: package P, plan and market training data

Complete on branch `dev/eugene-codex-plandata`, cut from master `eb22c63`, in the separate `kaggriculture-ml-plandata` worktree. No agent/model changes, pushes or submissions. At most two worker processes; `PYTHONHASHSEED=0` throughout.

**Market labels cover all {original['segments']:,} existing non-test teacher segments: {original['turns']:,} turns and {original['orders']:,} issued orders across seven sources. Every original non-test worker NPZ hash is unchanged.** Existing test identities 10320-10324 were excluded before data files were opened, including hash reads; their original manifest rows remain unchanged. Labels are sibling files in `datasets/turn-markets/`, never additions to the worker files.

**All 60 balanced seeds are complete:** 20 per B, split into 15 train + 5 `analysis2` per B. Generated 60 template games, 1,800 teacher day segments (days 0-29), and 120 teacher full games (both physical seats), all against Metav4 with weeds pinned. The new sources contain **5,400 day shards and 129,420 teacher turns**, with **{new_orders:,}** issued market orders. No model was trained; every source and physical seat retains its seed's fixed train/analysis2 split.

{table(['Source','Split','Seeds','Day shards','Teacher turns','Worker decisions'],summary)}

Native reconciliation passes for every newly encoded day, including actual market orders and sales tables. Fresh encoder/market parity covers {sum(r['segments'] for r in verify['new_source_parity'])} new shards spanning all three scenarios, both splits and both full-game seats; all seven existing sources also pass sample native/encoder parity. Fresh-process repeats match for one template game, two teacher full games, and teacher days 0,16,29. Three full replays also reconcile from reset through the native engine. The complete audit verifies {check['worker_files_checked']:,} non-test worker shards and {check['market_files_checked']:,} market sidecars, all recorded splits, hashes, masks and sale fills.

**Timing:** {elapsed/3600:.2f} hours wall time from fixed seed selection through this report, including development/checks; sum of measured per-family worker times {sum(r['family_seconds'] for r in timing)/3600:.2f} hours (overlapping lanes, not wall time). Family median {statistics.median(r['family_seconds'] for r in timing):.1f}s; min/max {min(r['family_seconds'] for r in timing):.1f}/{max(r['family_seconds'] for r in timing):.1f}s. `PLAN_DATA_TIMING.csv` separates template game time, teacher day generation and teacher full-game time; family time also includes verification, Parquet extraction and I/O. Repeat/parity audit took {verify['seconds']:.1f}s. Resume reuses verified completed outputs; no duplicate repeat games enter training.

Held-out opponent evaluation is deferred at Eugene's request until P is finished and he confirms resources are available. No held-out games were run for this package.

## Market label contract

`reports/BOARD_FEATURES.md` documents every new array and the fixed 28-token vocabulary. `PLAN_MARKET_VOCAB.csv` is the machine-readable vocabulary. Arrays are indexed by physical step and explicit teacher seat. The manifest `manifests/turn-markets.csv` joins each sidecar to its exact worker file/hash and raw replay hash.

The vocabulary is SELL x9 products, BUY_SEED x5 crops, BUY_ANIMAL x3 animals, BUY_PRODUCT x9 products, BUY_LAND and HIRE. The engine supports BUY_PRODUCT only for wheat and fertilizer; the other fixed tokens have `order_valid=False`. `units_issued` and `units_executed` are distinct. Land has separate binary requested/executed flags; ordered records and quantity totals preserve repeated land orders, just as HIRE retains its count.

The ordered arrays preserve every issued order in its original position, raw JSON, token, parsed request, attempted/effective flags, executed units and actual cash delta. Orders beyond the processing cap remain present and unattempted. Failed and partial fills remain explicit. Per-price native sale-fill arrays preserve price changes within a single SELL order; quantities and revenue reconcile to the corresponding native order. Padding is masked; unknown or malformed orders retain raw JSON and token -1. All arrays load with `allow_pickle=False`.

Existing labels come from the already reconciled market_orders/sales tables, with fresh native replay samples for each source. New-source encodes use the unchanged worker encoder and compare all six native tables. All sidecars are independently checked for quantities, order masks, sale units/prices/revenue and original worker-file hashes. `PLAN_MARKET_COVERAGE.csv` reports requested/executed units and issued/attempted/effective orders by source, split, physical seat and token, including zero channels.

## Seed choice and analysis2

Selection was fixed before any new game: **{rule}**

{table(['B','Split','Seeds','Ordered pairs','Pairs absent from prior fitting data'],[[r['B'],r['split'],r['seeds'],r['ordered_pairs'],r['previously_unseen_pairs']] for r in seed_counts])}

The 60 seeds cover 52 different ordered pairs (16 / 20 / 16 by B), prioritizing pairs absent from the prior 62 fitting games. Both shop identity and order are retained. The seed schedule is local pinned-weed mode, as documented by package U; every new seed family's recorded first-two shops and B match the chosen manifest.

Reserved analysis2 seed identities (never train):

```text
{' '.join(analysis2)}
```

`manifests/plan-seeds.csv` is authoritative for seed identity, B, ordered shops and split. All three corpus manifests (`template-balanced.csv`, `ownfarm-balanced.csv`, `teacher-full.csv`) preserve that split. `PLAN_SEED_COVERAGE.csv` keeps exact seed lists and pair denominators. There is no cross-seat or cross-source split leakage. **Future training consumers must honor `split`, not the older numeric shortcut `game >=10401`**; existing training scripts were not modified.

## New-source encoding and lifecycle

`l1bal`: one teacher day from every template morning, days 0-29, seed-reset teacher each morning, same recorded Metav4 continuation. Teacher calls cover every available turn: 24 for days 0-28, 23 for terminal day 29. The existing narrow, provenance-recorded overflow compatibility helper is reused for day segments; unrelated exceptions still fail. No teacher source or weights were edited/copied into this repository.

`tfull`: teacher's own plan from day 0, against Metav4 in each physical seat; full games each have 720 frames and 719 calls per player, DONE/DONE statuses, no policy errors/fallbacks, and audited bank/command/shop/gameplay hashes as in G. Full games are split into day shards for the unchanged day-bounded worker targets. Native reconstruction covers every day transition; separate full replay checks include reset. Policy state is fresh/reset for every independent full game; each seed family runs in a fresh process, and selected full repeats run in separate fresh processes to check isolation.

The original `board_features.py`, `build_turn_dataset.py`, worker arrays and all protected agent/training/vendor files are unchanged. The new wrapper uses the same encode/mask/label implementation, with the correct parent history (template for l1bal, teacher full game for tfull) and actual physical teacher seat. `manifests/turns.csv` retains all original row values, appends the new sources with the original columns unchanged; full-game paths include seat0/seat1 to prevent collisions. The market and teacher-full manifests carry explicit seat; the helper validates the filename seat against the native episode id. When integrating with concurrent Claude work, retain any later master-only source rows rather than replacing the merged manifest with this branch snapshot.

Large data, weights, raw replays, native tables, tensors, per-seed receipts, immutable original manifests, timing and audit details stay under `<data>/`. Generated paths are recorded in the manifests. Key evidence: `runs/plan-data-v1/checks.json`, `verification.json`, `inputs.json`, `provenance.json`, per-seed generation/encoding receipts and market receipts. Only manifests, small coverage/check tables, documentation and new tools belong in git.

## Reproduce / resume

Use at most two worker processes total. The two lane commands below run concurrently with one worker each; other validation/encoding commands run after a worker is free.

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
python tools/plan_games.py seeds
python tools/plan_dataset.py markets --workers 1
python tools/plan_games.py generate --lane 0 --lanes 2 --workers 1
python tools/plan_pipeline.py run --lane 1 --lanes 2
python tools/plan_pipeline.py encode --lane 0 --lanes 2
python tools/plan_pipeline.py publish
python tools/check_plan_data.py
python tools/verify_plan_data.py --workers 2
python tools/check_plan_data.py --audit
python tools/report_plan_data.py
```

Run native/encoder smoke checks before a fresh full run; their successful receipts are retained. Seed selection is deterministic; preserve the original split reservation and input snapshot on resume. Market sidecars are idempotent and verified against the associated worker hash. Skipped test files were neither hashed nor parsed. No new model fits, game policies, teacher code/weights, net_player.py, board_net.py, train_board_net.py, Claude tools or vendor files were modified.
'''
    (G.REPO/'handoff/2026-10-2X-codex-to-claude-plan-data.md').write_text(text,encoding='utf-8')
    G.save(G.REPO/'reports/PLAN_DATA_VERIFICATION.json',verify)
    print(json.dumps(dict(report='handoff/2026-10-2X-codex-to-claude-plan-data.md',new_segments=len(new),new_turns=sum(int(r['turns']) for r in new),old_segments=original['segments'],market_sidecars=len(markets),elapsed_hours=elapsed/3600)),flush=True)

if __name__=='__main__':main()

"""Write the small D2 handoff after the evidence audit and summaries succeed."""
import csv
import json
from pathlib import Path
import statistics
import sys

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/'src'))
from kagml.paths import runs
root=runs()/'d2-opponents-2026-10-17'
verified=json.loads((root/'verification.json').read_bytes())
assert verified['accepted']==144 and verified['rejected']==0
strength=list(csv.DictReader((REPO/'reports/D2_STRENGTH.csv').open()))
speed=json.loads((REPO/'reports/D2_TIMING.json').read_bytes())
joins=json.loads((root/'join.json').read_bytes())
assert len(joins)==18
summary=[]
for r in joins:
    assert r['timing']['turns']==24 and not r['diagnostics']['fallbacks'] and not r['diagnostics']['search_errors']
    assert not [e for e in r['exceptions'] if e['type'] not in ('GeneratorExit','StopIteration','StopAsyncIteration')]
    effective=sum(v for k,v in r['effects'].items() if k.startswith('effective_'))
    assert effective>0
    summary.append({'name':r['name'],'step':r['step'],'seat':r['seat'],'turns':24,
       'cash_change':r['after']['cash']-r['before']['cash'],'goods_change':r['after']['goods']-r['before']['goods'],
       'attempted':sum(v for k,v in r['effects'].items() if k.startswith('attempted_')),'effective':effective,
       'median_ms':r['timing']['median_ms'],'max_ms':r['timing']['max_ms']})
with (REPO/'reports/D2_JOINS.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(summary[0]));w.writeheader();w.writerows(summary)
def md(rows,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+['| '+' | '.join(str(r[k]) for k in columns)+' |' for r in rows])
main=[]
for r in strength:
    if r['buyers']!='all' or r['seat']!='all':continue
    main.append({'agent':r['name'],'control':r['control'],'bank':f"{float(r['bank']):,.0f}",'control_bank':f"{float(r['control_bank']):,.0f}",
      'margin':f"{float(r['margin']):+,.0f}",'wins':r['wins']+'/24','paired_seed_wins':r['paired_seed_wins']+'/12','bank_share':f"{float(r['bank_share']):.4f}"})
timing=[{'agent':r['name'],'median_ms':round(r['median_ms'],2),'max_ms':round(r['max_ms'],2),'cold_load_seconds':round(r['cold_load_seconds'],2),'turns_above_1s':r['over_1s_turns']} for r in speed]
text=f'''# Codex to Claude: D2 complete (2026-10-23)

**All 144 existing games verified; none needed rerunning. All three policies win all 24 games against each baseline, and all 18 cold joins complete with effective actions and zero policy errors/fallbacks.** This supersedes the missing-drive status in `2026-10-22-codex-to-claude-opponents.md`.

Banks and margins below are means; share is summed published-agent bank / summed baseline bank. Both seats are paired within seed; a seed win means positive mean margin across the two seats. `fourth` rows are the specifically requested historical calibration, **not held-out opponent evidence**: it is now our teacher and yardstick per PLAN.md. The fifth-place policies remain held out.

{md(main,['agent','control','bank','control_bank','margin','wins','paired_seed_wins','bank_share'])}

## Speed

{md(timing,['agent','median_ms','max_ms','cold_load_seconds','turns_above_1s'])}

**Runtime caveat:** fifth-n1 exceeds one second on 22,340/33,793 untraced turns (66.1%); its median is above one second. All three have maximum turns above one second and multi-second cold loads. These are local generous-time comparisons, not proof they fit competition timing.

Per-turn clocks pool the 47 untraced games per policy (33,793 turns each); exception-traced turns are excluded from timing comparisons. Cold-load clocks are the existing isolated `cold-*.json` measurements, not newly measured post-restart loads. Generous evaluation limits were 30 seconds/turn and 7200 seconds/game; strength here does not establish submission-time compatibility. These 12 seeds do not establish broad generalisation.

## Verification and joins

The audit checks every expected agent/control/seed/seat, replay seed, all 720 frames with both final statuses DONE, all 719 issued actions against daily counts (including each operation), timing coverage, final banks/margins/wins/ties, and early-shop scenario. All 4,320 policy-days contain both non-PASS commands and market orders. Across every game: zero loader fallbacks/search errors. In the three designated traced proof games, only GeneratorExit control-flow events occur; no non-control-flow policy exceptions. Remaining games have diagnostic counters rather than full internal tracing.

Join source: local el3/10301, independent resets at steps 240,384,600 (mornings 10,16,25), both seats, 24 turns each. All 18 windows pass, each with 247-336 effective native unit operations. Details: `reports/D2_JOINS.csv`. Effect hooks now exist only during actual `env.step`, never while an agent's private simulator plans; selected native interpreter code/seat must match. This fixes the checker without modifying any policy. Day 16 replaces the previous non-morning step 400. Cash changes can be negative when buying land/animals and are not alone a sensibility test. We verify native work, not an optimality claim. L1's prior 552 accepted fourth-place joins remains additional evidence.

Both fifth-place wrappers keep per-seat policy state, a last-step clock, and supported v8 short-history/long-gap trackers; cold/discontinuous calls initialise these. The fourth-place agent keeps a FlowTracker, previous observation/action, market gate accumulators and land accumulators, plus seeded sampling RNG. It reconstructs recent market/production flow from observations and its previous action; empty history does not prevent these tested joins. Its action-dependent flow accounting matters for shadow labels and is investigated in L2. No upstream policy or weight file was edited.

## Evidence and reproduction

- Branch `dev/eugene-codex-d2-finish`, from master `105a3dd` (contains L1's `2b169c3`). Maximum two active validation/game processes; no pushes or submissions.
- `reports/D2_STRENGTH.csv`: all/scenario 0/1/2 x all/seat 0/seat 1, both banks, margin, wins/ties, share, paired seed wins and seed-level standard error. No unpaired significance claim.
- `reports/D2_PAIRED.csv`: 72 seed pairs, each with both seats' banks/margins/wins and paired share/margin.
- `reports/D2_TIMING.json`, `D2_VERIFICATION.json`, `D2_JOINS.csv`: small result tables. All replays, detailed daily counts, exceptions and logs remain under `<data>/runs/`.
- `tools/audit_opponents.py`, `summarize_opponents.py`, `report_opponents.py`: verification before summarisation/reporting. Regression checks in `test_d2_checks.py`: 2/2 passed, including corruption rejection and simulator isolation.

```powershell
python tools/audit_opponents.py
python tools/check_opponents.py join --replay ../Kaggle-Kaggriculture/.scratch/template-bench/runs/el3/10301.json
python tools/summarize_opponents.py
python tools/report_opponents.py
```

No new strength games, training, vendor edits, policy copies, or configuration changes. Work can proceed to L2.
'''
(REPO/'handoff/2026-10-23-codex-to-claude-opponents.md').write_text(text,encoding='utf8')
print(md(main,['agent','control','margin','wins','bank_share']))
print(md(timing,['agent','median_ms','max_ms','cold_load_seconds','turns_above_1s']))

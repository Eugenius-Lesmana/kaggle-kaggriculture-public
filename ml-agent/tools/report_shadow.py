"""Summarise the completed, independently checked L2 build. No policy calls."""
from collections import Counter
import csv
import json
from pathlib import Path
import statistics
import shutil

from shadow_labels import ROOT,REPO,folders,slug,save_json

name='template';raw,out,log=folders(name)
build=json.loads((log/'full.json').read_bytes());checked=json.loads((log/'validation.json').read_bytes())
assert build['outcomes']=={'kept':552} and checked['segments']==552 and checked['teacher_calls']==13248
assert checked['benchmark_pairs']==checked['benchmark_exact_both']==120
memory=json.loads((log/'memory-analysis.json').read_bytes())
repair=json.loads((log/'repair.json').read_bytes())
assert checked['compatibility_calls']==1 and repair['unchanged_other_segments']==551
smokes=[]
for player in ('fourth','template','model:ranker-v1'):
    folder=folders(player)[2]
    s=json.loads((folder/'smoke.json').read_bytes());v=json.loads((folder/'smoke-validation.json').read_bytes())
    assert s['outcomes']=={'kept':3} and v['segments']==3
    smokes.append({'player':player,'build_seconds':s['seconds'],'validation_seconds':v['seconds'],
        'teacher_calls':v['teacher_calls'],'job_rows':v['label_counts']['job_rows'],
        'legal_job_rows':v['label_counts']['legal_job_rows'],'action_differences':v['action_differences']})
rows=list(csv.DictReader((REPO/'manifests/shadow-template.csv').open()))
receipts=[json.loads((out/'audit'/f"{r['episode']}.json").read_bytes()) for r in rows]
timings=[dict(game=r['game'],day=r['day'],seconds=r['seconds'],generation_seconds=r['generation_seconds'],
              extraction_seconds=r['extraction_seconds'],teacher_load_seconds=r['teacher_load_seconds']) for r in receipts]
bytes_by_type=Counter()
for r in receipts:
    for p in r['output_hashes']:
        bytes_by_type['replays' if p.endswith('.json.gz') else 'parquet']+=(ROOT/p).stat().st_size
result={'date':'2026-10-23','branch':'dev/eugene-codex-shadow','base':'105a3dd','workers':2,
    'full_build_seconds':build['seconds'],'validation_seconds':checked['seconds'],'smokes':smokes,
    'segments':552,'teacher_calls':13248,'resumed_smoke_segments':build['resumed'],
    'rows':checked['rows'],'label_counts':checked['label_counts'],'teacher_median_ms':checked['teacher_median_ms'],
    'teacher_max_ms':checked['teacher_max_ms'],'benchmark_exact_both':checked['benchmark_exact_both'],
    'checks':checked['checks'],'signature':build['signature'],'bytes':dict(bytes_by_type),
    'compatibility_calls':checked['compatibility_calls'],'compatibility':repair,'unmodified_teacher_segments':551,'adapted_teacher_segments':1,
    'teacher_memory':memory,'self_shadow_resume':json.loads((folders('fourth')[2]/'resume-check.json').read_bytes())}
save_json(REPO/'reports/SHADOW_RESULTS.json',result)
with (REPO/'reports/SHADOW_TIMING.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(timings[0]));w.writeheader();w.writerows(timings)
with (REPO/'reports/SHADOW_BENCHMARK.csv').open('w',newline='') as f:
    comparisons=json.loads((log/'benchmark.json').read_bytes())
    w=csv.DictWriter(f,fieldnames=list(comparisons[0]));w.writeheader();w.writerows(comparisons)
with (REPO/'reports/SHADOW_LEGALITY.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=('kind','status','rows'));w.writeheader();w.writerows(checked['legality_by_kind'])

def table(records,columns):
    return '\n'.join(['| '+' | '.join(columns)+' |','| '+' | '.join(['---']*len(columns))+' |']+
        ['| '+' | '.join(f'{r[k]:.2f}' if isinstance(r[k],float) else str(r[k]) for k in columns)+' |' for r in records])
counts=checked['label_counts'];pct=100*counts['legal_job_rows']/counts['job_rows']
text=f'''# Codex to Claude: L2 shadow labels complete (2026-10-23)

**552/552 template segments accepted and independently reconciled. The self-shadow test matches all 72 full actions exactly.** Every template turn has a teacher answer: **13,248/13,248**, with zero generic inference/PASS fallbacks or search errors. One explicitly approved optional-helper bypass is recorded at episode 1031925, step 623; this is not a fully unmodified teacher corpus. Mapped teacher jobs are legal under `work_data.candidates` on **{counts['legal_job_rows']:,}/{counts['job_rows']:,} ({pct:.4f}%)** rows. Both seats' cash matches the existing template benchmark exactly on all **120** overlapping mornings.

**Memory caveat:** these are raw stateful shadow labels. On {memory['flow_estimate_disagreements']:,}/{memory['within_segment_transitions']:,} within-segment transitions ({100*memory['flow_estimate_disagreement_fraction']:.2f}%), the teacher's own-flow estimate differs when its previous unexecuted answer is replaced, for audit purposes only, with the action the player actually executed. Actual labels, teacher memory and policy files were not changed. Current job legality is high, but it does not establish accurate hidden flow features or optimal choices.

## Smoke, timing and scope

All smoke builds and independent checks passed before the full run. Each uses game 10301, mornings 6,16,28, two workers:

{table(smokes,['player','build_seconds','validation_seconds','teacher_calls','job_rows','legal_job_rows','action_differences'])}

The initial full template attempt took **{build['seconds']:.2f}s ({build['seconds']/60:.2f} minutes)**, reusing {build['resumed']} hash-verified smoke segments. It accepted 551 and rejected one day. The approved one-day compatibility retry took {repair['seconds']:.2f}s (excluding its initial imports, actor load and preflight hash scan); the other 551 segments were reused unchanged. Independent full validation took **{checked['seconds']:.2f}s**. Teacher-call median **{checked['teacher_median_ms']:.2f}ms**, maximum **{checked['teacher_max_ms']:.2f}ms**. Build clocks include pool start/stop, imports, player warm-up, generation, reconciliation and writes; coordinator imports/dependency hashing are outside the build timer. Checker clocks include its worker pool and checks, excluding coordinator imports/dependency hashing. Existing per-worker loaded weights stay cached, with actor memory/RNG reset for every segment. Detailed per-segment clocks are in `reports/SHADOW_TIMING.csv`.

## What was played and stored

- All 24 el3 games 10301-10324 x mornings 6-28 inclusive, seat 0; `pin_weeds(True)`, original `info.seed`, opponent's exact recorded commands.
- `<data>/raw/shadow/template/<game>-d<day>.json.gz`: 552 actual-player segments, 25 frames each. Preview padding removed, absolute step numbers retained; ACTIVE endpoint banks are intermediate outcomes.
- `<data>/datasets/shadow/template/<table>/<episode>.parquet`: six unchanged D1 tables for BOTH executed seats, plus teacher_actions, teacher_turns and teacher_market_orders for teacher seat 0. 4,969 Parquet files (nine tables per segment plus one compatibility-event shard); compressed replays {bytes_by_type['replays']:,} bytes, Parquet {bytes_by_type['parquet']:,} bytes.
- `manifests/shadow-template.csv`: 552 original-game/day/seat/file/hash/bank/episode/seed/start/end mappings. Three-row self and model smoke manifests are also tracked. `model:ranker-v1` uses directory/manifest slug `model-ranker-v1`.
- Receipts, diagnostics, memory audit, benchmark and detailed logs stay under `<data>/runs/shadow/` and `datasets/shadow/<player>/audit/`. Small tracked results: `SHADOW_RESULTS.json`, `SHADOW_BENCHMARK.csv`, `SHADOW_LEGALITY.csv`, `SHADOW_TIMING.csv`; definitions and commands: `reports/SHADOW_SCHEMA.md`.

{table([{'table':t,'rows':n} for t,n in checked['rows'].items()],['table','rows'])}

## Plumbing and checks

`tools/shadow_labels.py` reuses `compare_day.make_player`, preview snapshots, L1 hashing/output helpers and native D1 segment extraction. Template/model memory is warmed on the recording before takeover, including model price history; worker targets reset as in compare_day. The teacher receives an independent deep copy of the exact same pre-decision observation as the actual player. Only the player's action reaches env.step. Full teacher actions and all market orders are preserved; unit positions and job legality use the actual pre-state. Omitted existing-hand commands become explicit PASS; moves/PASS have nullable job/legality and are excluded from mapped-job denominators. Candidate membership allows a future shed trip and is not a native effect or shared-resource/quantity validation.

The self-shadow player is an independent Opponent instance; using load('fourth') twice would share memory. Independent actors with identical reset seeds produce identical full actions on all 72 tested turns. {result['self_shadow_resume']['resumed']} self-smoke receipts resumed without regeneration. All outputs are hash-verified on resume; changed code/model/weights/source invalidate it. Full build requires passing self and selected-player smoke on matching dependencies and sources.

`tools/check_shadow.py` checks all source/output/dependency hashes, snapshots, seeds, exact opponent commands, 25-frame/24-answer coverage, all primary keys, teacher positions/jobs/legal membership and every D1 table against fresh native re-extraction. This also rechecks native per-turn cash bridges and sales. Corrupted teacher labels and replay quotes are rejected. Full self-shadow actions and benchmark cash are exact. This checker does not call an agent. The model smoke passed with 72 answers; no full ranker run or training was requested/performed.

"## Approved compatibility: distinguish teacher from our guard

The unmodified teacher crashes at game 10319/day25/step623 (last turn of the day): policy.py night_room_value indexes minv['SHEEP'], although animals are not market-price products. Its model/decoder action already exists; the optional helper fails while valuing predicted overnight inventory overflow. The failure was reproduced in a fresh process and its exact observation/configuration/error/upstream hashes retained at runs/shadow/template/failure-10319-d25.json.gz. The original failed full receipt is archived as runs/shadow/template/unmodified-full.json.

Eugene explicitly approved a narrowly documented compatibility repair and a retry of only that day. tools/shadow_compat.py wraps only night_room_value in the retry process. It catches ONLY a KeyError originating in that helper's own frame where item is an animal missing from minv. Other errors propagate. It restores the pre-helper teacher action and returns zero extra overflow sales. It invents no animal price, inserts no PASS, changes no worker command and adds no order. It then lets the teacher finish its ordinary bookkeeping. Source/weight files and the shared loader are untouched. Four focused tests prove normal helper behaviour is unchanged, the animal case is marked, and unrelated/nested KeyErrors propagate.

Result: exactly one bypass at step 623. All 5,510 replay/Parquet outputs for the other 551 segments have identical SHA256 before/after. The repaired segment has its own effective signature derived from the original dependency signature plus the two adapter-tool hashes; the final checker validates that provenance separately. The mixed-provenance corpus is deliberate and explicit, not silently labelled as raw teacher output.

For later decision logic, LEFT JOIN datasets/shadow/template/teacher_compatibility/1031925.parquet on (episode,step). It stores the original error/helper, teacher_pre_helper_action, returned_action, and our_action. A missing row means no adapter intervention. On the marked row, pre-helper and returned full actions are exactly equal; the unmodified teacher's final answer does not exist because it crashed. The replay's shadow.compatibility marker and the audit's compatibility.events mirror this. SHADOW_RESULTS.json carries the complete event and source/hash provenance. Exclude the marked turn (or its segment) if a later analysis requires strictly unmodified teacher answers. No attempt is made to claim the skipped overflow sales adjustment would have been beneficial or harmful.

To resume this specific approved repair, run python tools/retry_shadow_compat.py after a raw full attempt. The ordinary raw generator intentionally does not pretend that this adapted segment has its unmodified signature. Final validation accepts exactly the declared per-segment signature and helper event, and rejects undocumented interventions.

## Teacher memory: observed limitation"

The unmodified fourth-place play.py retains `_FLOW`: FlowTracker, previous observation/action, step, market gate-rate accumulators (`acc`) and land accumulators (`land_acc`). Every segment resets all of them and the private RNG. On successive turns it calls FlowTracker.observe(previous_actual_observation,current_actual_observation,previous_teacher_answer). Upstream own_flows reads that answer's HARVEST/COLLECT_FERTILIZER/FEED and BUY_PRODUCT commands to estimate production, consumption and purchases. During shadow play those commands may not have executed, so flow totals and estimated opponent pressure can be wrong. Loaded accumulator flags: gate_rate={memory['decoder_memory_settings']['gate_rate']}, land_rate={memory['decoder_memory_settings']['land_rate']}. These optional pathways must not be assumed active merely because their empty fields exist. The policy's previous-action input columns are documented upstream as unused; the flow/accumulator pathway still exists.

`tools/check_shadow_memory.py` imports the upstream function read-only and evaluates both prior-action alternatives on the SAME actual observation pairs. It excludes the first answer, where no prior pair exists. It measures accounting disagreement, not exact native sales, and never executes another teacher action or edits upstream code. Fourth self-shadow has zero such disagreement; full template has the rate above. Examples and per-product absolute estimate differences are saved on D: and in SHADOW_RESULTS. This percentage measures sensitivity of flow accounting to the previous-action assumption; it is not an action-accuracy score. Action quality was not measured. This is the concrete oddness observed, with no claim that it is harmless.

## Branch and reproduction

`dev/eugene-codex-shadow`, from master `105a3dd`. No edits to preview.py, opponents.py, compare_day.py, model_player.py, dataset builders, vendor, teacher sources or weights. No model training, pushes or submissions by this package. Maximum two workers throughout. During generation, concurrent commits 5773a3c, d9f5ba4 and f1a32cf appeared on this branch. They are left intact; our commit stages only the L2 paths listed here and does not rewrite that history. Fourth-place model code remains on D: under CC BY 4.0; preserve credit in downstream write-ups.

Commands are in `reports/SHADOW_SCHEMA.md`. After generation and independent checks:

```powershell
python tools/check_shadow_memory.py
python tools/check_shadow_resume.py
python tools/report_shadow.py
```

Split downstream training by original game, never by synthetic segment episode; use absolute pre-state steps and teacher seat 0 only. Teacher market orders are proposed labels, not actual sales. The raw stateful-memory caveat must travel with this dataset.
'''
(REPO/'handoff/2026-10-23-codex-to-claude-shadow-labels.md').write_text(text,encoding='utf8')
print(json.dumps({k:result[k] for k in ('segments','teacher_calls','full_build_seconds','validation_seconds','label_counts','benchmark_exact_both')}))

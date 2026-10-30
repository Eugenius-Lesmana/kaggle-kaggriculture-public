"""Render the requested report from completed training and gated evaluation proofs."""
import csv,json,sys
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def main():
    a=load(ROOT/'reports/MARKET_TRAIN_ANALYSIS_CHECKS.json');live=load(ROOT/'reports/MARKET_TRAIN_LIVE_CHECKS.json')
    assert a['passed'] and a['complete'] and live['passed']
    data=Path(__import__('os').environ['KAGML_DATA']);training=load(data/'models/market-gru-v1/report.json')
    rows=list(csv.DictReader((ROOT/'manifests/market-history.csv').open()));splits=Counter(r['split'] for r in rows)
    turns=Counter()
    for r in rows:turns[r['split']]+=int(r['turns'])
    if not a['live_gate']['passed']:answer='Do not replace P5’s market head. The trained market model shows a clear analysis regression; live games were skipped as required.'
    elif live.get('keep'):answer='Keep market-gru-v1 on P5: the pooled margin passes the fixed 2-SE rule and the fresh-seed margin is positive.'
    elif live['status']=='rejected-first-margin':answer='Do not keep market-gru-v1 on P5. Its first 48 live games have a nonpositive paired margin; the fresh stage was skipped.'
    else:answer='Do not keep market-gru-v1 on P5: the complete live confirmation misses the fixed keep rule.'
    lines=['# Market model — 2026-10-30','',f'**{answer}**','',
        'The current P5 baseline remains §net:board-p5:market:overflow:endmask:endwork§ until Claude separately integrates any kept option. No board-p6 combination was tested.','',
        '## Build and training','',
        'Full causal history build §market-v1§ completed; all selected TRAIN/analysis/analysis2 rows are represented. Test and endval rows were excluded before opening arrays. Existing worker/market arrays were hash-checked and not rewritten. No true opponent sales, opponent private stock, step-t action or future observations are model inputs.','',
        '| Split | Segments | Turns | Parent seed families |','| --- | ---: | ---: | ---: |']
    for s in ('train','analysis','analysis2'):lines.append(f"| {s} | {splits[s]:,} | {turns[s]:,} | {len(training['families'][s]):,} |")
    lines+=['','The 90,932-parameter GRU/MLP uses 24×65 causal history and 148 current features. Four CUDA epochs, AdamW lr2e-4, batch option128, non-zero weight1. Batches stay within each segment, so most are smaller than128. Scaling/fitting use TRAIN only; lowest analysis cross-entropy chooses the checkpoint; count calibration uses analysis2 only and is bound to the checkpoint SHA. Seed families are disjoint across these splits.','',
        '| Epoch | Analysis CE | Raw event precision | Raw event recall |','| --- | ---: | ---: | ---: |']
    for e in training['log']:
        v=e['analysis'];lines.append(f"| {e['epoch']} | {v['loss']:.6f} | {v['precision']:.2%} | {v['recall']:.2%} |")
    lines+=['','The GPU was checked with §nvidia-smi§ and the trainer process list before training; Claude’s §train_board_net.py§ blocks startup. Exact-input epoch recovery preserves completed epochs and refuses changed manifests/code/options. Logs: §.cache/market-train/training.stdout.log§ and §gpu-before-training.log§.','',
        '## Teacher-state analysis comparison','',
        f"All {a['segments']:,} analysis segments / {a['turns']:,} turns were scored. Main comparison below restricts decisions to NN days6–28. Complete-analysis figures and all28 token totals are in the [checks](MARKET_TRAIN_ANALYSIS_CHECKS.json) and [token CSV](market-train-analysis-tokens.csv). P5 is its original market head, without mcal. GRU raw and analysis2-calibrated outputs are both shown.",'',
        '| Model | Exact precision | Exact recall | ±2 precision | ±2 recall | Total normalized absolute token-unit error |','| --- | ---: | ---: | ---: | ---: | ---: |']
    models=a['scopes']['live6-28']
    for n,d in models.items():
        s=d['overall'];lines.append(f"| {n} | {s['exact_precision']:.2%} | {s['exact_recall']:.2%} | {s['within2_precision']:.2%} | {s['within2_recall']:.2%} | {s['unit_absolute_error_ratio']:.3f} |")
    token_names=[r['token'] for r in csv.DictReader((ROOT/'reports/market-train-analysis-tokens.csv').open()) if r['scope']=='live6-28' and r['model']=='board-p5']
    lines+=['','Exact means the same token is positive on the same turn; it does not require the same quantity class. The ±2 score locks exact matches, then matches remaining predicted/teacher events one-to-one within two turns of the same contiguous segment; it never reuses a teacher event. Forks/boundaries are not joined. Quantity-class hits are reported separately in the CSV.','',
        'Unit totals use the shared QTY_PLAY representatives before availability, hire cap, ten-order truncation and overflow/endmask. They measure head over-ordering potential, not executed sales or profit. BUY_LAND’s runtime decoder emits one order for any positive class.','',
        '| Token, days6–28 | Teacher units | P5 head units | Calibrated GRU units | P5 / teacher | GRU / teacher |','| --- | ---: | ---: | ---: | ---: | ---: |']
    for token in a['live_gate']['criteria']['focus_tokens']:
        k=token_names.index(token);b=models['board-p5']['tokens'][k];g=models['market-gru-v1']['tokens'][k]
        f=lambda v:'NA' if v is None else f'{v:.3f}'
        lines.append(f"| {token} | {g['teacher_units']:,} | {b['predicted_units']:,} | {g['predicted_units']:,} | {f(b['unit_ratio'])} | {f(g['unit_ratio'])} |")
    lines+=['','## Predeclared analysis gate','',
        '[Criteria](MARKET_TRAIN_ANALYSIS_GATE.json) were fixed before training/results: reject a decline greater than2percentage points in exact or ±2 F1, an increase greater than0.10 in total normalized absolute token-unit error, or more than0.25 additional absolute unit-ratio error in any of the six focus tokens with at least20 teacher units. No parameters or calibration were tuned on evaluation seeds.','',
        'Gate: **'+('passed' if a['live_gate']['passed'] else 'failed')+'**.']
    lines+=['- '+r for r in a['live_gate']['reasons']]
    lines+=['','This is analysis-based checkpoint selection and a repeated validation comparison, not an untouched generalization test. Label matching on recorded teacher farms does not establish live bank gain; production, availability and opponent reactions can change.','',
        '## Conditional live evaluation','']
    if not live['comparisons']:lines+=['No policy games were started. Task2 was skipped because the analysis gate failed. There is no live or pooled keep claim.']
    else:
        lines+=['The fresh default P5 replay matched §'+live['default_gate']['gameplay_sha256']+'§. Original baseline receipts and candidate replays were audited with their original stored signatures; separate market weights/calibration are included in candidate signatures. At most3 owned game workers were active.','',
        '| Seed set | Games per agent | Margin Δ ± SE | Our bank Δ ± SE | NF bank Δ ± SE | P5 share / wins | GRU share / wins |','| --- | ---: | ---: | ---: | ---: | --- | --- |']
        for label,c in live['comparisons'].items():
            f=lambda name:f"{c[name]['mean']:+,.1f} ± {c[name]['se']:,.1f}"
            lines.append(f"| {label} | {c['games']} | {f('margin')} | {f('our_bank')} | {f('opponent_bank')} | {c['baseline']['share']:.3f} / {c['baseline']['wins']} | {c['candidate']['share']:.3f} / {c['candidate']['wins']} |")
        lines+=['','Share = total our bank / total opponent bank. Deltas are candidate minus P5; margin Δ equals our-bank Δ minus NF-bank Δ. SE uses sample SD of seed means divided by sqrt(seed count), with both seats averaged within each seed. Wins count games, not seeds.','',
            'Fixed rule: first-seed margin must be positive before a fresh run; keep only if all48 pooled seed pairs are complete, pooled margin≥2SE and fresh-seed margin>0. '+live['coverage']+'.']
    lines+=['','## Reproducibility and boundaries','', 'Exact commands:','',
        '§§§powershell',"$env:PYTHONHASHSEED='0'","$env:KAGML_DATA='<data>'","$env:OMP_NUM_THREADS='1'","$env:MKL_NUM_THREADS='1'",
        'python tools/build_market_history.py --full --splits train,analysis,analysis2 --tag market-v1 --manifest manifests/market-history.csv',
        'python tools/train_market_net.py market-gru-v1 --manifest manifests/market-history.csv --epochs 4 --lr 2e-4 --batch 128 --require-cuda --resume',
        'python tools/compare_market_model.py','python tools/market_train_live.py','§§§','',
        'The live runner refuses to start games after a failed analysis gate and implements the fixed fresh-stage/pooled conditions. Supporting [live checks](MARKET_TRAIN_LIVE_CHECKS.json), [history manifest](../manifests/market-history.csv), [comparison code](../tools/compare_market_model.py). Weights/calibration remain on D: in §models/market-gru-v1§; no model arrays/raw games/caches are committed.','',
        'New branch §dev/eugene-codex-market-train-20261030§ from master §1f85c4007a512c403bc25a6a5c880e1159dc8a2c§. Main working copy, master source and other worktrees were not edited. Seeds20001–20048 evaluation-only; no training/tuning on them; no test10320–10324 contents, pushes, submissions or attribution lines.']
    text='\n'.join(lines).replace('§',chr(96))+'\n';(ROOT/'reports/2026-10-30-market-model.md').write_text(text,encoding='utf8')
    note='# Market training handoff — 2026-10-30\n\n**'+answer+'**\n\nFour CUDA epochs of market-gru-v1 completed, TRAIN fit/scaling, analysis checkpoint, analysis2 calibration; all selected history sidecars built. Analysis and any conditional live coverage are documented in the [report](../reports/2026-10-30-market-model.md), [analysis checks](../reports/MARKET_TRAIN_ANALYSIS_CHECKS.json) and [live checks](../reports/MARKET_TRAIN_LIVE_CHECKS.json).\n\n'
    note+='Default P5 is unchanged. No board-p6 combination, evaluation tuning/training, test contents, pushes or submissions. All work is on dev/eugene-codex-market-train-20261030 in kaggriculture-ml-market-train-20261030; main and other worktrees untouched. Weights and calibration are <data>/models/market-gru-v1/model.pt and calibration.json. Claude can integrate a kept option separately.\n'
    (ROOT/'handoff/2026-10-30-codex-to-claude-market-train.md').write_text(note,encoding='utf8')
    print(json.dumps(dict(passed=True,answer=answer,segments=len(rows),split_segments=splits,split_turns=turns,live_status=live['status'])))
if __name__=='__main__':main()

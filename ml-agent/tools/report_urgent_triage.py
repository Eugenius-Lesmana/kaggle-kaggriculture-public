"""Package U tables and handoff, from the retained analysis evidence only."""
import gzip
import hashlib
import json
import math
from pathlib import Path
import sys
import numpy as np
import pandas as pd
import joblib
import urgent_triage as U


def md_table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,row))+' |' for row in rows])


def number(x):return 'unavailable' if pd.isna(x) else f'{x:,.0f}'


def report():
    baseline=json.loads((U.OUT/'model-input-hours-hashes.json').read_text())
    assert all(hashlib.sha256(gzip.decompress((U.OUT/p).read_bytes())).hexdigest()==digest for p,digest in baseline.items()),'Hourly model inputs changed; refit required'
    e=pd.concat([pd.read_csv(U.OUT/f'{s}-items.csv.gz') for s in U.SOURCES],ignore_index=True)
    e['service_other_open']=np.where(e.served==1,e.service_open-1,-1)
    e.to_csv(U.OUT/'items.csv.gz',index=False)
    valid=e[e.terminal_censored==0].copy()
    resolutions=valid.groupby(['source','item','resolution']).agg(items=('served','size'),mean_stake=('stake','mean'),mean_skip_loss=('actual_skip_loss','mean')).reset_index()
    U.write_csv(U.REPORT/'URGENT_RESOLUTIONS.csv',resolutions)
    counts=[]
    for (item,survival,production),g in valid.groupby(['item','survival','production']):
        served=g[g.served==1]
        counts.append(dict(item=item,survival=survival,production=production,**U.se_stats(g.served,g.game),
            median_hour=served.service_hour.median(),q90_hour=served.service_hour.quantile(.9),
            mean_stake=g.stake.mean(),mean_actual_skip_loss=g.actual_skip_loss.mean(),
            harvest_without_service=int((g.resolution=='HARVEST').sum()),dry_deaths=int((g.resolution=='dry_death').sum()),escapes=int((g.resolution=='escape').sum())))
    U.write_csv(U.REPORT/'URGENT_RISK_TYPES.csv',counts)
    curve=[]
    for (source,h,item),g in valid.groupby(['source','H','item']):
        for hour in range(24):
            curve.append(dict(source=source,H=h,item=item,hour=hour,items=len(g),served_by_hour=((g.served==1)&(g.service_hour<=hour)).mean()))
    U.write_csv(U.REPORT/'URGENT_COMPLETION_CURVES.csv',curve)
    competition=[]
    valid['queue_band']=pd.cut(valid.onset_open,[0,4,9,19,39,100],labels=['1-4','5-9','10-19','20-39','40+'])
    for (item,q),g in valid.groupby(['item','queue_band'],observed=True):
        competition.append(dict(item=item,queue_band=str(q),**U.se_stats(g.served,g.game)))
    U.write_csv(U.REPORT/'URGENT_ONSET_COMPETITION.csv',competition)
    # Scenario crop frequencies and paired per-morning differences, including explicit zero crops.
    mix=pd.read_csv(U.REPORT/'SCENARIO_PLANT_MIX.csv');agreement=pd.read_csv(U.REPORT/'SCENARIO_PLANT_MORNINGS.csv')
    assert len(agreement)==105
    crop=[]
    for (b,p,c),g in mix.groupby(['B','player','crop']):
        crop.append(dict(B=b,player=p,crop=c,plants=int(g['count'].sum()),all_plants=int(g.total.sum()),share=g['count'].sum()/g.total.sum(),**U.se_stats(g['count'],g.game)))
    U.write_csv(U.REPORT/'SCENARIO_PLANT_SUMMARY.csv',crop)
    crop_delta=[]
    for (b,c),g in mix.groupby(['B','crop']):
        w=g.pivot(index=['game','day'],columns='player',values='count')
        diff=w['board-v4+guard']-w['teacher']
        crop_delta.append(dict(B=b,crop=c,comparison='board_minus_teacher_plants_per_day',**U.se_stats(diff,w.index.get_level_values('game'))))
    U.write_csv(U.REPORT/'SCENARIO_PLANT_DIFFERENCES.csv',crop_delta)
    ag=[]
    for b,g in agreement.groupby('B'):
        ag.append(dict(B=b,mornings=len(g),games=g.game.nunique(),board_plants=int(g.board_plants.sum()),teacher_plants=int(g.teacher_plants.sum()),
            mix_overlap=int(g.mix_overlap.sum()),mix_overlap_board_share=g.mix_overlap.sum()/g.board_plants.sum(),
            common_cell_pairs=int(g.common_cell_pairs.sum()),same_crop_cell_pairs=int(g.same_crop_cell_pairs.sum()),
            same_crop_common_cell_share=g.same_crop_cell_pairs.sum()/g.common_cell_pairs.sum(),
            common_time_cell_pairs=int(g.common_time_cell_pairs.sum()),same_crop_time_cell_pairs=int(g.same_crop_time_cell_pairs.sum()),
            same_crop_common_time_cell_share=g.same_crop_time_cell_pairs.sum()/g.common_time_cell_pairs.sum()))
    U.write_csv(U.REPORT/'SCENARIO_PLANT_AGREEMENT.csv',ag)
    # Readable rule paths with actual analysis-game leaf rates.
    model=joblib.load(U.MODEL/'shallow.joblib');arr=[]
    for source in U.SOURCES:
        h=pd.read_csv(U.OUT/f'{source}-hours.csv.gz');h=h[(h.split=='analysis')&(h.terminal_censored==0)]
        if h.empty:continue
        for item in U.ITEMS:h[f'item_{item.lower()}']=(h.item==item).astype('int8')
        h['leaf']=model.apply(h[U.FEATURES].astype('float32'));arr.append(h[['leaf','served','game']])
    held=pd.concat(arr,ignore_index=True);t=model.tree_;leaves=[]
    def visit(node,terms):
        if t.children_left[node]==t.children_right[node]:
            h=held[held.leaf==node]
            leaves.append(dict(leaf=node,condition=' AND '.join(terms),training_rows=int(t.n_node_samples[node]),
                predicted_service_probability=float(t.value[node,0,1]),analysis_rows=len(h),analysis_games=h.game.nunique(),analysis_served_share=h.served.mean()))
            return
        name=U.FEATURES[t.feature[node]];cut=t.threshold[node]
        visit(t.children_left[node],terms+[f'{name} <= {cut:.2f}']);visit(t.children_right[node],terms+[f'{name} > {cut:.2f}'])
    visit(0,[]);U.write_csv(U.REPORT/'URGENT_RULES.csv',leaves)
    score=pd.read_csv(U.REPORT/'URGENT_MODEL_SCORES.csv');macro=[]
    for name,g in score[score.cohort.str.startswith('game:')].groupby('model'):
        for metric in ('accuracy','balanced_accuracy','roc_auc','brier'):
            macro.append(dict(model=name,metric=metric,games=5,mean=g[metric].mean(),se_game=g[metric].std(ddof=1)/math.sqrt(5)))
    U.write_csv(U.REPORT/'URGENT_MODEL_GAME_SE.csv',macro)
    gap=pd.read_csv(U.REPORT/'SCENARIO_GAPS.csv');gap=gap[(gap.dimension=='B')&(gap.metric=='value_plus_assets')]
    gaps=[]
    for player in ('board-v4+guard','v3-fw','template','teacher-workers+our-plan'):
        values=[]
        for b in range(3):
            r=gap[(gap.scenario.astype(str)==str(b))&(gap.player==player)].iloc[0]
            values.append(f"{r['mean']:,.0f} ({number(r.se_game)})"+(' [morning SE '+number(r.se_morning)+']' if r.games==1 else ''))
        gaps.append([player,*values])
    service=[]
    for item,g in valid.groupby('item'):
        a=g[g.served==1]
        service.append([item,f'{len(g):,}',f'{g.served.mean():.1%}',number(a.service_hour.median()),number(a.service_hour.quantile(.9)),int((g.resolution=='HARVEST').sum()),int((g.resolution=='dry_death').sum()),int((g.resolution=='escape').sum())])
    mixrows=[]
    for b in range(3):
        values=[b]
        for p in ('board-v4+guard','teacher'):
            g=pd.DataFrame(crop);g=g[(g.B==b)&(g.player==p)]
            values.append(' / '.join(f"{g[g.crop==c].iloc[0]['share']:.1%}" for c in ('STRAWBERRY','WHEAT','TOMATO','CARROT')))
        mixrows.append(values)
    seeds=pd.read_csv(U.REPORT/'SCENARIO_SEEDS_10501_11500.csv')
    same=[(int(r['B']),f"{r['same_crop_common_cell_share']:.1%}",r['common_cell_pairs'],f"{r['same_crop_common_time_cell_share']:.1%}",r['common_time_cell_pairs'],f"{r['mix_overlap_board_share']:.1%}") for r in ag]
    outcomes=valid.resolution.value_counts().to_dict();rules_text=(U.MODEL/'shallow_rules.txt').read_text()
    meta=json.loads((U.MODEL/'features.json').read_text());coverage=json.loads((U.OUT/'ledger.json').read_text())
    text=f'''# Codex to Claude: package U, urgent-job triage and scenario census

Completed 2026-10-25 (client date; incoming request is dated 2026-10-26). Branch `dev/eugene-codex-urgent`, cut from master `e6afad0`, separate worktree `kaggriculture-ml-urgent`. Analysis only.

The teacher serves animals earlier than dry crops: animal service medians are hours 7-10, versus hour 17 for wheat, carrot, tomato and strawberry. Survival-risk wheat and carrot are almost always watered. Older, lower-price items remain open more often; the shallow model predicts non-service after hour 12 for age >9.5 and price <=86.5 when unfertilized, and for age >15.5 with price >86.5 but total stake <=500.5. These are observational classification rules, not measured benefits of skipping a job.

The 62 fitting games have scenario counts **17 / 29 / 16** for B=0/1/2. The full original 24 seed identities are **11 / 8 / 5**; the 48 N2 games are **10 / 24 / 14**. Five original analysis games and five test identities are not fitting games. All 72 source seed identities total **21 / 32 / 19**. The analysis sample has only **2 / 2 / 1 games** per B, so scenario 2 has no estimable between-game standard error.

Board-v4 + guard remains **$235 / $359 / $433 per day below the teacher** in value including asset changes for B=0/1/2, on the requested same-morning days 6-26. Below, signed differences are player minus teacher; parentheses are paired game-level SE. Morning SE is also retained in the CSV and shown when only one game exists.

{md_table(['Player','B=0: 42 mornings / 2 games','B=1: 42 / 2','B=2: 21 / 1'],gaps)}

`value_plus_assets` uses the existing closing-price convention: cash change plus change in goods held and waiting produce at closing prices, plus assets at cost. It is neither final bank nor a causal estimate of changing the guard. All four metrics (cash, goods/produce value, assets, their total), ordered first-two shops, and early demand for wheat/carrot/tomato/egg/milk/wool are in `SCENARIO_GAPS.csv`. Exact-shop strata have one game each; no between-game SE is reported for them. Rows are paired by game and morning; game means are the independent units for the primary SE.

## Engine corrections that matter

1. The installed pinned engine, `kaggle-environments==1.32.7`, gives ongoing crops **one base unit even when unwatered**, if they survive. Watering enables only the fertilizer increment. An unfed animal can also produce **one base unit**, if it survives; feeding enables its banked care bonus. Production is capped by available room. Thus the handoff's statement that all base production is lost without water/feed, and the production-only `n_loss_if_dry` / `n_loss_if_unfed` proxies, overstate the native incremental loss. Existing protected code is unchanged.
2. `stake = seed/animal cost + current-price waiting units + tonight's capped potential production`. `actual_skip_loss` instead values survival loss, or only the native fertilizer/care increment for production-only cases. Both are retained; neither includes speculative future lifetime output. The animal counterfactual holds current care bonus fixed and does not assume a future CARE action. One-time watering yield bonuses and future care accrual are outside this requested urgent-production definition.
3. Shop schedules are **seed-determined in our pinned-weed mode**, not stored at reset: town starts empty, and each shop is drawn at its unlock. `_end_of_day` creates `random.Random((seed * 1_000_003) ^ day)`, then `pin_weeds(True)` consumes exactly two parent `random()` draws, one per farm, before `choice(sorted(SHOPS))`. In the unmodified engine the weed loop consumes a farm-state-dependent number of draws, so seed alone does not specify those native schedules. All **536** non-test recorded shop dawns match the local seed formula; independent direct native end-of-day checks also pass. The 1,000-row seed list is labelled for this local mode.

## Ledger and teacher order

All seven sources are covered: L1, L3 ranker round 1, L3 ranker round 2, L3 network round, L1-edge, L3-edge, N2 l1more. **{sum(r['segments'] for r in coverage):,} segments, {len(e):,} item records, {sum(r['hours'] for r in coverage):,} hourly open-item rows**. L3 prefix actions never label the teacher; an unresolved dawn item first observed at takeover is marked `takeover_risk`, rather than falsely attributed a dawn-to-service teacher history. Newly planted/placed items enter as their actual state becomes at risk. Within each turn, service order follows native unit order; simultaneous commands do not imply a known policy planning order.

Day 29 has no midnight refresh in these terminal segments. Its **{int(e.terminal_censored.sum()):,}** item records remain in the raw ledger but are censored from rates and model fitting/scoring. The following rates include all other observed branches; repeated takeover branches and sources are pooled, not independent games. `URGENT_RISK_TYPES.csv` separates survival, production-only and combined risks with game-level SE.

{md_table(['Item','At-risk records','Watered/fed','Median service hour','90th percentile hour','Harvested unserved','Dry deaths','Escapes'],service)}

Service means successful WATER or FEED. HARVEST and DIG resolutions are explicitly separate; an item harvested before midnight is not a failed survival intervention. Production-only items can remain present without service. All outcomes: `{json.dumps(outcomes,sort_keys=True)}`. Service-time quantiles condition on service; unconditional completion curves are in `URGENT_COMPLETION_CURVES.csv` by source/takeover hour/type. A season/day/coordinate/species/birth-day identity prevents replacement crops inheriting their predecessor's label.

The complete item ledger is `<data>/runs/urgent-triage-v1/items.csv.gz`; source-level item/hour/job ledgers are alongside it. Each item records species, crop/animal, onset day/hour, age, days left, waiting units, price, fertilizer, survival/production flags, cost and both values, actual resolution, service hour/unit/order, queue size, and distance. Service happens on the tile (distance zero); `service_dist_at_onset` measures that same worker's distance when the item first entered the ledger, -1 if hired later. `service_dist_previous` gives its preceding observed turn's distance, -1 at takeover; it is not a path-length estimate. `service_open` includes the target; `service_other_open` subtracts it. Queue counts remove same-turn successful service and removals in native unit order.

Tables: `URGENT_SERVICE.csv` by type/value/days-left/onset-hour/source/split; `URGENT_ONSET_COMPETITION.csv` by opening queue; `URGENT_OPEN_HOURS.csv` by type/hour/current queue; `URGENT_ALTERNATIVE_JOBS.csv` lists every worker job kind during hours containing an eventually unserved item, and at hour 23. A segment/hour is counted once even with several misses; all workers are counted, not just the nearest. For L1 hour-23 crews with an open eventual miss, issued commands are 38.2% WATER, 27.7% PASS, 16.9% HARVEST and 8.6% FERTILIZE (3,555 worker commands). Full hourly worker-kind counts remain on D:. `URGENT_RESOLUTIONS.csv` retains harvested, dug, decayed, dead, escaped, remaining and served outcomes.

## Triage models

Models and exact ordered features: `<data>/models/triage-v1/`. Files: `gbt.joblib`, portable LightGBM `gbt.txt`, `shallow.joblib`, `shallow_rules.txt`, `features.json`, and analysis prediction files. **{meta['train_rows']:,} training rows from 62 whole games; {meta['analysis_rows']:,} scoring rows from games 10315-10319 only**. No game, source, future action, final outcome or teacher command is an input. All hourly open-item rows have equal fitting weight; longer-open items and more numerous takeover branches therefore contribute more rows. No hyperparameter search or analysis-driven retraining was done.

{md_table(['Model / scoring rows','Accuracy','Balanced accuracy','ROC AUC','Majority accuracy'],[[r.model+' / '+r.cohort,f'{r.accuracy:.2%}',f'{r.balanced_accuracy:.2%}',f'{r.roc_auc:.4f}',f'{r.majority_accuracy:.2%}'] for _,r in score[score.cohort.isin(['overall','onset_only'])].iterrows()])}

`onset_only` scores one row per item when it first becomes at risk in the teacher portion ({int(score[score.cohort=='onset_only'].iloc[0].n):,} records). Models still fit hourly examples. `URGENT_MODEL_SCORES.csv` includes precision, recall, Brier score and per-game results; `URGENT_MODEL_GAME_SE.csv` gives unweighted game-mean metrics and their SE across the five analysis games. `URGENT_RULES.csv` gives every exact depth-four rule path with training support, predicted probability, analysis support and observed service rate. Sparse leaves and the one-game scenario-2 stratum limit conclusions. A probability of teacher service is not a job priority, safety guarantee or value of intervention; no guard integration was attempted.

Readable shallow tree (class 1 = the teacher eventually waters/feeds):

```text
{rules_text.rstrip()}
```

## Planting by scenario

Successful plantings were replayed through the native engine from the same mornings. All **5,040** turn-by-turn tile snapshots match the original diagnostic signatures; **3,052** successful plantings are counted. Crop shares below are strawberry / wheat / tomato / carrot, respectively; melon is retained separately in the CSVs and included in every denominator, so the four displayed shares need not sum to 100%.

{md_table(['B','Board-v4 + guard','Teacher'],mixrows)}

There is no natural one-to-one planting action match after two policies diverge. The report therefore distinguishes common-cell crop agreement, stricter same-hour/common-cell agreement, and the number of crop counts shared by both daily mixes (`sum(min(board_count,teacher_count)) / board_plantings`). Common-cell counts are planting-event pairs; repeated planting on one cell would create multiple pairs, not a fabricated matching assignment.

{md_table(['B','Same crop at common cell','Common-cell pairs','Same crop at same hour/cell','Same-hour/cell pairs','Daily mix overlap / board plants'],same)}

`SCENARIO_PLANT_DIFFERENCES.csv` reports paired crop-count differences per morning and both morning/game SE. `SCENARIO_PLANT_MORNINGS.csv`, `SCENARIO_PLANT_MIX.csv`, `SCENARIO_PLANT_SUMMARY.csv` and `SCENARIO_PLANT_AGREEMENT.csv` retain all denominators and zero crops. These comparisons describe policies under the same starting morning; they do not assert identical later decision states.

## Seed selection and balance

`SCENARIO_SEEDS_10501_11500.csv` contains every requested seed, ordered first two shops, B, full eight-shop schedule, and per-product early shop demand. For these 1,000 seeds the B counts are `{json.dumps(seeds.B.value_counts().sort_index().to_dict())}`. Choose equal numbers from B=0/1/2 when balanced evaluation is required, then retain or stratify exact ordered pairs and early product demand. This is a listing, not a new experiment or proposed tuning split.

The 72 source identities span {pd.read_csv(U.REPORT/'SCENARIO_CENSUS.csv').pair.nunique()} of the 64 possible ordered shop pairs; fitting identities span {pd.read_csv(U.REPORT/'SCENARIO_CENSUS.csv').query('split == "train"').pair.nunique()}. `SCENARIO_CENSUS.csv` marks the five excluded test identities as `test_metadata_only`: their shops were calculated from seeds, never read from replay contents. `SCENARIO_BALANCE.csv` separates all-source, actual fitting, analysis, original and N2 cohorts. Other early-demand features and exact pairs are descriptive strata, not independent evidence that one shop caused a gap.

## Reproduce and checks

```powershell
$env:PYTHONHASHSEED='0'
$env:KAGML_DATA='<data>'
python tools/test_urgent_triage.py
python tools/urgent_triage.py ledger --workers 2
python tools/urgent_triage.py scenarios --workers 1
python tools/urgent_triage.py fit
python tools/urgent_triage.py summary
python tools/report_urgent_triage.py
python tools/urgent_triage.py check
```

At most two worker processes; numeric-library and model threads bounded. No new games, policy/teacher calls, protected-code edits, pushes or submissions. Games 10320-10324 were excluded before raw game files were opened; manifests were read only to select/exclude identities. Six independent tests cover native production/survival/caps, pinned schedules, the test-file access gate, and full native reconciliation of one segment from each source. Completed model reload predictions match. Hourly input content hashes are unchanged by the separate resolution/queue-detail refinement, so the saved fit uses exactly the final hourly dataset. Receipts, source read lists, model input hashes and final checks remain under `runs/urgent-triage-v1/` on D:. No current-plan file exists in this repository; this new handoff is the status record.
'''
    path=U.REPO/'handoff/2026-10-2X-codex-to-claude-urgent-triage.md';path.write_text(text,encoding='utf-8')
    U.save(U.OUT/'report-checks.json',dict(hourly_model_inputs_unchanged=True,items=len(e),uncensored=len(valid),censored=int(e.terminal_censored.sum()),
        sources=U.SOURCES,outcomes=outcomes,plant_mornings=len(agreement),model_features=len(U.FEATURES),report=str(path)))
    print(path);print(json.dumps(outcomes,sort_keys=True))

if __name__=='__main__':report()

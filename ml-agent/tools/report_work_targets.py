"""Generate the W1 Markdown handoff from validated D: summaries."""
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kagml.paths import data_root
import pandas as pd

ROOT=data_root()/"runs/work-targets-2026-10-18"
REPO=Path(__file__).resolve().parents[1]
ORDER=("reference","second","template","fourth")
LABEL=dict(zip(ORDER,("Reference","Second","Template","Fourth")))
V=json.loads((ROOT/"validation.json").read_text())
CHECKS=json.loads((ROOT/"analysis_checks.json").read_text())
RULES=json.loads((ROOT/"rules.json").read_text())["rules"]
DATA={p.stem:pd.read_csv(p) for p in ROOT.glob("*.csv")}
assert len(RULES)==24 and not any(CHECKS.values())
for name in ("day_shape","harvest","fertilizer","watering","animal_rounds","animal_service"):
    assert len(DATA[name])==48 and set(DATA[name].cohort)==set(ORDER),name


def row(name,c,b=1,band=12):
    d=DATA[name]
    result=d[(d.cohort==c)&(d.buyers==b)&(d.band==band)]
    assert len(result)==1,(name,c,b,band)
    return result.iloc[0]


def num(x,n=1):
    return "NA" if pd.isna(x) else f"{x:.{n}f}"


def values(name,key,n=1):
    return "/".join(num(row(name,c)[key],n) for c in ORDER)


def table(head,rows):
    return "\n".join(["| "+" | ".join(head)+" |","| "+" | ".join("---" for _ in head)+" |"]+
                     ["| "+" | ".join(str(x) for x in r)+" |" for r in rows])+"\n"


def matrix(title,legend,render):
    rows=[]
    for b in range(3):
        for band in (6,12,18,24):
            rows.append([b,f"{band}–{band+5}"]+[render(c,b,band) for c in ORDER])
    return "\n## "+title+"\n\n"+legend+"\n\n"+table(["B","Days"]+[LABEL[c] for c in ORDER],rows)


def jobs(c,b,band):
    d=DATA["jobs"];d=d[(d.cohort==c)&(d.buyers==b)&(d.band==band)]
    by=dict(zip(d.op,d.per_worker_day))
    return "/".join(num(by.get(k,0),2) for k in ("WATER","HARVEST","FERTILIZE","COLLECT_FERTILIZER","FEED","CARE"))


def farmdays(c,b,band):
    return V["teacher_by_B"][f"{c}-B{b}"]*6 if c in ("reference","second") else V["local_games_by_B"][f"{c}-B{b}"]*(2 if band==12 else 1)


def flow(c,b,band):
    r=row("fertilizer",c,b,band);n=farmdays(c,b,band)
    return "/".join(num(0 if pd.isna(r[k]) else r[k]/n) for k in ("collections","uses","sold"))+f"; {num(r.wait_median)}h"


def harvest(c,b,band):
    r=row("harvest",c,b,band)
    return f"{num(r.mean_units,2)}/{num(r.cap_full_pct)}%; {num(r.oldest_wait_median)}h; {num(100*r.price_to_day_best)}%; {num(r.nearby_route_pct)}%"


def fertilize(c,b,band):
    r=row("fertilizer",c,b,band)
    censored=0 if pd.isna(r.censored) else int(r.censored)
    uses=0 if pd.isna(r.uses) else int(r.uses)
    return f"{num(r.already_watered_pct)}%; {num(r.marginal_harvest_72,2)}+{num(r.marginal_held_72,2)}; {censored}/{uses}"


def animals(c,b,band):
    r=row("animal_rounds",c,b,band);a=row("animal_service",c,b,band);n=row("animal_nearest",c,b,band)
    return f"{num(r.animals_per_round,2)}/{num(r.feeding_wheat_at_start,2)}; {num(a.same_visit_pct)}%; {num(n.nearest_unfed_pct)}%; {num(r.start_hour)}h"


def rule(c,habit):
    return next(r for r in RULES if r["cohort"]==c and r["habit"]==habit)


def weighted_age(d,q):
    d=d.groupby("age").applications.sum().sort_index()
    return int(d.index[d.cumsum()>=q*d.sum()][0])


anchor="Slash-separated operational figures below are Reference / Second / Template / Fourth, for B=1 and days 12–17. Rule-validation scores pool all held-out B/day strata. The teacher band covers six actual days; the paired local band samples days 12 and 16. Teacher farms differ from our farms. Only Template versus Fourth is a same-morning comparison."
text=f"""# W1: measured worker habits, 2026-10-18

The two teacher cohorts agree closely on daily work and fertilizer timing. On our own mornings, Fourth spends less time travelling, collects fertilizer sooner, applies it before watering, and waters more production-due plants. A universal full-tile harvest rule does not describe the teachers.

{anchor}

1. **Shape the day around an early animal round, then crop work.** The best hour/day classifier switches from animals to crops at hour 12 for both teachers and Fourth; Template switches at hour 11. Held-out balanced accuracy is 71.9% / 72.6% / 65.7% / 75.1%. Walking occupies {values("day_shape","walk_workerday_pct")}% of a worker-day; working {values("day_shape","work_workerday_pct")}%; idle {values("day_shape","idle_workerday_pct",2)}%. Workers serve {values("day_shape","cells_per_worker_day",2)} distinct cells and make {values("day_shape","shed_returns",2)} extra shed returns. Only about 8–9% of teacher worker-days fit inside a 3×3 service footprint; most worker visits span wider areas.

2. **Batch by product and nearby work.** The teachers' harvest trees split first near 0.71 of tile capacity, but ongoing fruit is collected below that threshold and one-time crops depend on watering and age. In this band, teacher strawberries average about 2/4 units, eggs 3.5/4, and melons almost 6/6. Median age of the oldest held unit is {values("harvest","oldest_wait_median")} hours; {values("harvest","nearby_route_pct")}% of harvests share a shed trip with another serviced cell within Manhattan distance 2. Harvest quotes average {"/".join(num(100*row("harvest",c).price_to_day_best) for c in ORDER)}% of that day's best quote. No price feature survives either teacher's depth-3 harvest tree. That is descriptive evidence, not proof that price never matters. Fourth does not harvest less in every stratum: here it makes 1.61 successful harvests/worker-day versus Template's 1.55.

3. **Collect fertilizer as part of animal service, keeping small field stocks.** The teacher collection rule mainly separates cared-for animals after hour 3 from animals still needing feed/care while the worker carries wheat; low-wheat workers also collect without finishing care first. Held-out balanced accuracy is 79.2% / 79.7% / 88.1% / 80.6%. Collections cover {values("fertilizer","collected_day_pct")}% of exposed animal-days; median delay from first availability is {values("fertilizer","wait_median")} hours. Median fertilizer carried before collection is {values("fertilizer","carried_before",0)} units; the teacher 90th percentile is 2. Excess fertilizer is sold; the flow table gives collected, used and sold units separately, without attributing a band's sales to that same band's collections.

4. **Apply fertilizer while expired, production-due, and not yet watered.** This exact simplified condition describes both teachers' fitted trees (92.9% balanced accuracy; precision about 76%, recall about 90%). Fourth's tree largely agrees, with an additional mature-crop branch; Template's tree omits the before-watering condition and excludes due melons. Already-watered applications are {values("fertilizer","already_watered_pct")}%; same-day watering follows or precedes {values("fertilizer","watered_same_day_pct")}%. Per completed dose, extra harvested plus still-held units are {"/".join(num(row("fertilizer",c).marginal_harvest_72,2)+"+"+num(row("fertilizer",c).marginal_held_72,2) for c in ORDER)}. Successful applications per worker-day are {values("day_shape","fertilizes",2)}. More applications and better timing are distinct measurements; this is not a bank-gain estimate.

5. **Use short animal rounds and combine feed with care.** The best tested eligible-job priority is FEED → HARVEST at ≥2/3 cap → CARE → COLLECT_FERTILIZER for both teachers and Fourth. Template's is FEED → CARE → HARVEST at ≥1/6 cap → COLLECT_FERTILIZER. These rules reach only 66.7–69.8% held-out macro recall, so they do not fully recover routing. Inferred rounds serve {values("animal_rounds","animals_per_round",2)} animals. Rounds that actually feed begin with {values("animal_rounds","feeding_wheat_at_start",2)} wheat carried, with {values("animal_rounds","feeding_wheat_picked_before",2)} picked up since the preceding round. When both feed and care succeed, {values("animal_service","same_visit_pct")}% occur during one worker's uninterrupted visit. Teachers feed before care about 99% of the time. Subsequent feeds choose a nearest currently-unfed animal from the preceding feed location {values("animal_nearest","nearest_unfed_pct")}% of the time.

6. **Water for production or survival, with late-crop exceptions.** Both teachers and Fourth are best described by production due or a previous unwatered day; the teachers' trees also stop rescuing some older crops. Template's fitted tree largely falls back to previous-day dryness after day 10, missing some production-led work. Held-out watering-rule precision is 97.0% / 97.1% / 99.9% / 94.3%, with recall 89.4% / 88.7% / 73.0% / 89.2%. Among complete continuing plant-days, due plants are watered {values("watering","due_watered_pct")}%, non-due plants {values("watering","not_due_watered_pct")}%; median watering hour is {values("watering","median_water_hour")}. Non-due watering is often survival work, not necessarily waste.

## Coverage and verification

Reference is submission 56711476; Second is submission 56722220. B counts strawberry-demanding shops among the first two unlocks (ICE_CREAM_SHOP, BRUNCH_SPOT, SMOOTHIE_SHOP, FARMERS_MARKET). It is a count of shop instances, including duplicates.

"""
coverage=[]
for c in ORDER:
    counts=V["teacher_by_B"] if c in ("reference","second") else V["local_games_by_B"]
    coverage.append([LABEL[c]]+[counts[f"{c}-B{b}"] for b in range(3)]+["all days 6–29" if c in ("reference","second") else "8, 12, 16, 20, 24"])
text+=table(["Cohort","B=0 seats/games","B=1","B=2","Measured days"],coverage)
text+=f"""
The 2,026 selected teacher seats occupy 1,394 unique accepted D1 games. Every teacher game matched its recorded full farm/private/market/town state at each dawn and the final frame: 41,820 checked frames. All 13,729,764 enriched teacher worker-turns matched D1's positions, existence, effective commands and effects; fertilizer sales matched D1. The original single timeout rejected by D1 remains excluded.

All 240 rev24 rows (24 games × five mornings × two players) reproduce cash and all eleven issued job counts exactly. Recorded warm-up states also match at every dawn. First-day measurements comprise 68,324 local worker-turns. Follow-up continues only to resolve that morning's doses, for at most 96 total turns. Template memories are restored from recorded history; Fourth's flow and RNG are restored after the first day so extra follow-up cannot alter the next rev24 morning.

Native engine: kaggle-environments 1.32.7. Eight native regression fixtures pass. All seven final aggregate checks are zero: activity partition, duplicate worker-turns, fertilizer gain above three, ended-crop held goods, negative fertilizer marginal, water-hour consistency and harvest-cap violations.

A final conservation check found 1,275 local dose rows with pre-turn goods incorrectly counted after a crop ended. The observer and regression test are fixed. The correction changed only that held-yield column in 187 local shards; every other column and all teacher shards are unchanged. Original shards, hashes and the correction ledger remain on D:. All tables below use the corrected data.

## Definitions and limits

- A worker-day includes each worker who exists for at least one decision that day. Shares average each worker-day's own walking/working/idle fractions; jobs are successful native actions per actual worker-day. The CSVs also contain turn-weighted shares, available turns, and jobs per 24 available turns. Omitted existing hands count as PASS; nonexistent hands do not count. There are 719 decisions in 720 replay states; day 29 has 23 decisions.
- Working includes successful inventory transfers and construction. Served cells count successful crop/animal/terrain jobs; shed transfers are separate. Shed visits count starting at the four central shed-adjacent cells plus re-entry from outside them. Automatic end-of-day deposits are recorded separately and never counted as visits.
- Availability clocks start when goods become harvestable, including maturity and native dawn/watering increases. Oldest wait is a per-harvest median; mean unit wait in the CSV weights by units. Decay-ambiguous FIFO clocks are excluded from latency means and flagged. A nearby route means another serviced cell within distance 2 on the same worker/day excursion from the shed; it does not establish why the route was chosen.
- Harvest price is the pre-action quote divided by the maximum actionable pre-action quote that day, within the same run/product. This retrospective comparison is not a realized sale price or a future-price predictor. Rules can use only the price maximum already observed.
- An animal round is consecutive animal jobs by one worker/day, split by crop/shed work or a gap exceeding Manhattan distance plus three turns. Feed/care share a visit only when worker and uninterrupted position-visit match. Nearest-unfed is evaluated at feed time from the previous fed cell, so concurrent workers can change the eligible set. Round sizes depend on this explicit inferred definition.
- Each fertilizer dose is omitted in its own native crop shadow while subsequent actual work, other doses, refreshes, harvests and decay are retained. Outcomes are extra harvested and extra still held after 72 hours or the original crop spell ending. Missing season/window follow-up is censored, never called zero. Marginals are conditional on fixed work, interact across doses and must not be summed as a whole-policy bank benefit. Units sold/used in a band can come from earlier stock.
- Production due means a one-time crop's watering bonus window, or an ongoing crop's scheduled next-dawn production. Survival risk means at least one previous unwatered end-of-day refresh. Watering CSVs contain every observed crop-spell/day and, separately, those present through midnight with a completed day. The displayed due/non-due rates use the latter; they exclude crops harvested/destroyed before midnight. Detailed crop/age/risk rows retain both denominators. Animal service percentages use all exposed animal-spell/days, including new animals.
- Rules use whole-game holdout: SHA256(game) modulo 5 equals zero. A depth-3 class-balanced tree uses current local state, known crop schedules, and day/hour, without coordinates, identity or future quotes. Minimum leaf is 0.2% of training rows, clipped to 10–500. Animal priority selects among all 24 orders and seven cap thresholds on training games. These are local opportunity/day rules, not recovered hidden policies or a proposed agent. Local validation has only six held-out games; per-stratum counts/scores and full trees are in rules.json. B=2 has only five local source games.

All following matrices keep B and band separate. NA means no eligible measurement. Reference/Second bands span six days; Template/Fourth use the sampled morning(s) inside that band.

"""
text+=matrix("Day shape","Each cell: walking/working/idle %; distinct served cells; extra shed returns per worker-day.",
    lambda c,b,k:"/".join(num(row("day_shape",c,b,k)[x]) for x in ("walk_workerday_pct","work_workerday_pct","idle_workerday_pct"))+"; "+num(row("day_shape",c,b,k).cells_per_worker_day,2)+"; "+num(row("day_shape",c,b,k).shed_returns,2))
text+=matrix("Jobs per worker-day","Each cell: WATER / HARVEST / FERTILIZE / COLLECT_FERTILIZER / FEED / CARE. Full jobs.csv includes planting, digging, building, pickup and deposits.",jobs)
text+=matrix("Harvest batching, wait, price and route","Each cell: mean units / full-cap %; median oldest-unit wait; mean quote/day-best %; nearby-route %. Product caps differ.",harvest)
text+=matrix("Fertilizer collection and stock flow","Each cell: collected / used / sold units per measured farm-day; median collection lag. A terminal partial day still counts as one observed farm-day; band stocks need not balance.",flow)
text+=matrix("Fertilizer timing and later yield","Each cell: already-watered applications %; extra harvested + held units per completed dose; censored doses / all doses. Complete doses are the complement of the final pair.",fertilize)
text+=matrix("Animal rounds","Each cell: animals per inferred round / wheat at start of feeding rounds; same-visit feed+care % given both; nearest-unfed subsequent feed %; median round start hour.",animals)
text+=matrix("Watering","Each cell: continuing due plants watered % / non-due plants watered %; median watering hour (all successful water events).",
    lambda c,b,k:f"{num(row('watering',c,b,k).due_watered_pct)}/{num(row('watering',c,b,k).not_due_watered_pct)}; {num(row('watering',c,b,k).median_water_hour)}h")

text+="\n## Product-specific harvests in the comparison band\n\nEach cell: mean units / native cap; full-cap %; median oldest-unit wait. B=1, days 12–17; this is not a pooled all-season target.\n\n"
caps={"WHEAT":6,"CARROT":4,"TOMATO":4,"STRAWBERRY":4,"MELON":6,"EGG":4,"MILK":6,"WOOL":6}
products=[]
for item,cap in caps.items():
    cells=[]
    for c in ORDER:
        d=DATA["harvest_product"]
        d=d[(d.cohort==c)&(d.buyers==1)&(d.band==12)&(d.item==item)]
        cells.append("NA" if d.empty else f"{num(d.iloc[0].mean_units,2)}/{cap}; {num(d.iloc[0].cap_full_pct)}%; {num(d.iloc[0].oldest_wait_median)}h")
    products.append([item]+cells)
text+=table(["Product"]+[LABEL[c] for c in ORDER],products)

text+="\n## Fertilizer crop and age in the comparison band\n\nEach cell: applications; age median [10th–90th percentile], in days. Weighted by applications; all crop/age/B/band outcomes remain in fertilizer_crop_age.csv.\n\n"
ages=[]
for crop in ("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON"):
    cells=[]
    for c in ORDER:
        d=DATA["fertilizer_crop_age"];d=d[(d.cohort==c)&(d.buyers==1)&(d.band==12)&(d.crop==crop)]
        cells.append("NA" if d.empty else f"{int(d.applications.sum())}; {weighted_age(d,.5)} [{weighted_age(d,.1)}–{weighted_age(d,.9)}]")
    ages.append([crop]+cells)
text+=table(["Crop"]+[LABEL[c] for c in ORDER],ages)

text+="\n## Watering at selected crop ages in the comparison band\n\nEach cell: complete continuing plant-days watered % (eligible plant-days). These exact-age rates combine the risk groups by their denominators. Every age, including newborn and harvested crop-spell/days, is retained in watering_crop_age.csv.\n\n"
water=[]
for crop,age in (("WHEAT",1),("WHEAT",2),("CARROT",2),("TOMATO",7),("TOMATO",8),("STRAWBERRY",9),("STRAWBERRY",10),("STRAWBERRY",11),("MELON",6),("MELON",10)):
    cells=[]
    for c in ORDER:
        d=DATA["watering_crop_age"];d=d[(d.cohort==c)&(d.buyers==1)&(d.band==12)&(d.crop==crop)&(d.age==age)]
        n=d.continuing_complete.sum()
        cells.append("NA" if not n else f"{num((d.continuing_complete*d.continuing_watered_pct.fillna(0)).sum()/n)}% ({int(n)})")
    water.append([crop,age]+cells)
text+=table(["Crop","Age"]+[LABEL[c] for c in ORDER],water)

text+="\n## Shed goods in the comparison band\n\nNative item units per worker-day. Most input pickups are wheat or fertilizer; livestock pickups are also listed. Animal inventory placement is excluded from shed deposits. AUTO_DROP is compulsory end-of-day transfer from anywhere on the farm.\n\n"
shed=[]
for c in ORDER:
    d=DATA["shed_goods"];d=d[(d.cohort==c)&(d.buyers==1)&(d.band==12)]
    wd=row("day_shape",c).worker_days
    pickup=d[d.op=="PICKUP"].groupby("item").bag_delta.sum().sort_values(ascending=False)
    drop=d[d.op.isin(["DROP","PLACE"])].groupby("item").shed_delta.sum().sort_values(ascending=False)
    auto=d[d.op=="AUTO_DROP"].groupby("item").shed_delta.sum().sort_values(ascending=False)
    def goods(s):return ", ".join(f"{k} {num(v/wd,2)}" for k,v in s.items() if v>0) or "none"
    shed.append([LABEL[c],goods(pickup),goods(drop),goods(auto)])
text+=table(["Cohort","Picked up","Deposited by worker","Automatic deposit"],shed)

text+="\n## Held-out rule checks\n\nBA is balanced accuracy (mean sensitivity/specificity); animal priority reports macro recall over observed job classes, with precision/recall left NA. H is positive jobs/days in the test set; tests are grouped by complete game. Precision matters because most local opportunities do not issue the target job.\n\n"
scores=[]
for c in ORDER:
    for habit in ("day_phase","harvest","fertilizer_collection","fertilizer_use","animal_priority","watering"):
        r=rule(c,habit);s=r.get("scores")
        scores.append([LABEL[c],habit,r["test_games"],s["n"] if s else r["test_rows"],
            s["positive"] if s else "NA",num(100*s["balanced_accuracy"] if s else 100*r["balanced_accuracy"]),
            num(100*s["precision"]) if s else "NA",num(100*s["recall"]) if s else "NA"])
text+=table(["Cohort","Habit","Test games","Test rows","H","BA %","Precision %","Recall %"],scores)

text+="\n## Detailed evidence and rerun\n\nAll generated evidence remains under "+str(ROOT)+". These CSVs retain cohort, B and band rather than pooling them:\n\n"
descriptions=[
("day_shape.csv","worker-day shares, time available, cells, shed entries, first/last job timing"),
("jobs.csv","successful jobs per worker-day and per 24 available turns, hour quantiles"),
("hourly.csv","walking, working, idle, animal and crop jobs by hour"),
("harvest.csv","batch size, full cap, unit-weighted FIFO wait, quote comparison, nearby route"),
("harvest_product.csv","the same harvest measures by product"),
("fertilizer.csv","collection lag/carry, applications, follow-up completeness, extra yield, sales and loss"),
("fertilizer_carry.csv","carried fertilizer distributions at collection and use"),
("fertilizer_crop_age.csv","crop/age application counts, water order, later yield and censoring"),
("animal_rounds.csv","round size/time, wheat carried and picked up, feeding-round quantities"),
("animal_service.csv","feed/care coverage, worker/visit pairing and order"),
("animal_nearest.csv","feed transitions and nearest-unfed agreement"),
("animal_route_order.csv","adjacency, row/column direction and distances"),
("animal_visit_order.csv","exact successful job patterns per stationary worker visit"),
("watering.csv","all-exposed and continuing/due/non-due coverage, hour quantiles"),
("watering_crop_age.csv","coverage by crop, age, due status and survival risk"),
("shed_goods.csv","item-level pickups, deposits and automatic transfers"),
("rules.json","full descriptive trees, priorities and held-out B/band scores"),
("validation.json","cohorts, replay checks, row counts, engine version/hash and correction"),
("analysis_checks.json","seven independent aggregate checks"),
("source_versions.json","measurement sources and protected template/loader hashes"),
("held-correction.json","all corrected shards, before/after hashes and unchanged-column verification")]
text+=table(["Evidence","Contents"],[(f"[{p}]({(ROOT/p).as_posix()})",d) for p,d in descriptions])
text+="""
Raw shards are in events/, doses/, plant_days/, animal_days/, flows/ and markets/; per-run receipts are in audit/. The original pre-correction observer and extraction source, and original corrected dose shards, are retained on D:. The correction affected no event labels or rule-fitting inputs.

Run sequentially from this repository (the first command uses two replay workers; the following commands use at most one game process):

~~~text
python tools/work_targets.py teachers --workers 2
python tools/work_targets.py previews
python tools/check_work_targets.py
python tools/summarize_work_targets.py --threads 2
python tools/fit_work_targets.py --threads 2
python tools/report_work_targets.py
~~~

The source-signature cache safely recomputes shards after source changes. The old extraction's signatures are backed by its archived sources; teacher extraction functions were also AST-checked as unchanged after the preview-validation patch. For pre-fix archived outputs only, tools/repair_work_target_held.py applies the exact ended-crop correction, preserving originals and hashes; new extractions already produce zero held goods for ended crops.

Measurement only: no agent or vendor edits, no opponent code or weights copied, no D: data files staged, no pushes/submissions. The tools, this report, and its generator are the repository deliverables.
"""
target=REPO/"handoff/2026-10-1X-codex-to-claude-work-targets.md"
target.write_text(text,encoding="utf-8")
print(json.dumps({"report":str(target),"characters":len(text),"checks":CHECKS}))

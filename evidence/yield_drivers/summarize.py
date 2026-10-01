"""Summarize lifecycle factors, fixed-action fertilizer gain, and timing."""
import csv
import itertools
import json
import statistics
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np

OUT=Path(__file__).resolve().parent
CROPS=("WHEAT","CARROT","TOMATO","STRAWBERRY","MELON")


def write(name,rows):
    with (OUT/name).open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=list(rows[0]))
        writer.writeheader();writer.writerows(rows)


def fit(rows):
    """Shapley allocation of within-top incremental R² beyond lifecycle controls."""
    if len(rows)<20:
        return None
    y=np.array([float(r["harvested_units"])*24/float(r["active_hours"]) for r in rows])
    life=np.array([float(r["active_hours"])/24 for r in rows])
    base=np.column_stack((np.ones(len(rows)),life,
        [float(r["planted_day"]) for r in rows],
        [float(r["window_days"])/(h/24) for r,h in zip(rows,[float(r["active_hours"]) for r in rows])],
        [float(r["submission"]=="56664798") for r in rows],
        [float(r["submission"]=="56666211") for r in rows]))
    factors=np.column_stack((
        [float(r["window_watered_days"])*24/float(r["active_hours"]) for r in rows],
        [float(r["window_water_fert_days"])*24/float(r["active_hours"]) for r in rows],
        [float(r["delay_hours"])/24/max(1,float(r["harvest_events"])) for r in rows]))
    def error(which):
        x=np.column_stack((base,factors[:,list(which)])) if which else base
        coefficients=np.linalg.lstsq(x,y,rcond=None)[0]
        return float(np.square(y-x@coefficients).sum()),coefficients
    errors={s:error(s)[0] for n in range(4) for s in itertools.combinations(range(3),n)}
    alloc=[0.0]*3
    for order in itertools.permutations(range(3)):
        chosen=()
        for j in order:
            more=tuple(sorted((*chosen,j)))
            alloc[j]+=(errors[chosen]-errors[more])/6
            chosen=more
    full=errors[(0,1,2)]
    _,beta=error((0,1,2))
    total=float(np.square(y-y.mean()).sum())
    gain=errors[()]-full
    return dict(n=len(rows),mean_rate=float(y.mean()),base_r2=1-errors[()]/total,
        full_r2=1-full/total,incremental_r2=gain/total,
        water_r2=alloc[0]/total,fert_overlap_r2=alloc[1]/total,
        delay_r2=alloc[2]/total,
        water_coef=beta[-3],fert_overlap_coef=beta[-2],delay_coef=beta[-1])


def main():
    games=set()
    sums=defaultdict(Counter)
    by_agent=defaultdict(Counter)
    regress=defaultdict(list)
    gaps=defaultdict(list)
    lifecycle=defaultdict(Counter)
    with (OUT/"plant_lifecycles.csv").open(newline="",encoding="utf-8") as file:
        for r in csv.DictReader(file):
            crop=r["crop"]
            assert int(r["no_fert_harvested_units"])<=int(r["harvested_units"]),(crop,r["game"])
            games.add((r["submission"],r["game"]))
            s=sums[crop]
            a=by_agent[(r["submission"],crop)]
            s["plants"]+=1
            a["plants"]+=1
            s["late_hours"]+=int(r["late_hours"])
            a["late_hours"]+=int(r["late_hours"])
            s["late_units"]+=int(r["late_harvested_units"])
            a["late_units"]+=int(r["late_harvested_units"])
            s["late_nofert"]+=int(r["late_no_fert_units"])
            a["late_nofert"]+=int(r["late_no_fert_units"])
            s["late_window"]+=int(r["late_window_days"])
            a["late_window"]+=int(r["late_window_days"])
            s["late_water"]+=int(r["late_window_watered_days"])
            a["late_water"]+=int(r["late_window_watered_days"])
            s["late_fert"]+=int(r["late_window_fertilized_days"])
            a["late_fert"]+=int(r["late_window_fertilized_days"])
            s["late_overlap"]+=int(r["late_window_water_fert_days"])
            a["late_overlap"]+=int(r["late_window_water_fert_days"])
            a["delay_hours"]+=int(r["delay_hours"])
            a["harvest_events"]+=int(r["harvest_events"])
            if r["replant_gap_hours"]!="" and 12<=int(r["ended_day"])<=27:
                gaps[crop].append(int(r["replant_gap_hours"])/24)
            if int(r["late_harvested_units"])>0:
                z=lifecycle[crop]
                z["plants"]+=1
                for field in ("active_hours","watered_days","window_days","window_watered_days",
                    "fertilized_days","window_fertilized_days","window_water_fert_days",
                    "harvest_events","harvested_units","late_harvested_units","delay_hours"):
                    z[field]+=int(r[field])
            if r["censored"]=="0" and r["ended_day"]!="" and 12<=int(r["ended_day"])<=27 and int(r["harvested_units"])>0 and int(r["active_hours"])>0:
                regress[crop].append(r)
    old=csv.DictReader((OUT/"production_reference.csv").open(newline="",encoding="utf-8"))
    matched=defaultdict(Counter)
    for r in old:
        if r["phase"] not in ("d12_19","d20_27") or r["product"] not in CROPS or r["group"] not in ("top_three","planner_v010"):
            continue
        d=matched[(r["group"],r["product"])]
        d["harvest"]+=float(r["harvested_units"])
        d["capacity"]+=float(r["capacity_days"])
    crop_rows=[];model_rows=[]
    n_games=len(games)
    for crop in CROPS:
        s=sums[crop]
        top=matched[("top_three",crop)]
        planner=matched[("planner_v010",crop)]
        top_rate=top["harvest"]/top["capacity"] if top["capacity"] else 0
        planner_rate=planner["harvest"]/planner["capacity"] if planner["capacity"] else 0
        fert_gain=s["late_units"]-s["late_nofert"]
        expected=top["harvest"]*n_games
        assert abs(s["late_units"]-expected)<1e-5,(crop,s["late_units"],expected)
        assert fert_gain>=0,(crop,fert_gain)
        g=gaps[crop]
        crop_rows.append(dict(crop=crop,games=n_games,late_plants=s["plants"],
            late_units_per_game=s["late_units"]/n_games,
            hourly_cell_days_per_game=s["late_hours"]/24/n_games,
            hourly_units_per_cell_day=s["late_units"]*24/s["late_hours"] if s["late_hours"] else 0,
            late_window_water_share=s["late_water"]/s["late_window"] if s["late_window"] else 0,
            late_window_fert_share=s["late_fert"]/s["late_window"] if s["late_window"] else 0,
            late_window_water_fert_share=s["late_overlap"]/s["late_window"] if s["late_window"] else 0,
            fixed_action_fert_gain_per_game=fert_gain/n_games,
            fixed_action_fert_gain_per_top_dayend_cell_day=fert_gain/n_games/top["capacity"] if top["capacity"] else 0,
            top_dayend_rate=top_rate,planner_dayend_rate=planner_rate,
            top_nofert_dayend_rate=(top["harvest"]-fert_gain/n_games)/top["capacity"] if top["capacity"] else 0,
            observed_rate_gap=top_rate-planner_rate,
            maximum_gap_fraction_from_top_fert=(fert_gain/n_games/top["capacity"])/(top_rate-planner_rate) if top_rate>planner_rate else "",
            observed_replant_gaps=len(g),median_replant_gap_days=statistics.median(g) if g else "",
            mean_replant_gap_days=statistics.mean(g) if g else ""))
        model=fit(regress[crop])
        if model:model_rows.append(dict(crop=crop,**model))
    write("crop_summary.csv",crop_rows)
    write("factor_regression.csv",model_rows)
    write("lifecycle_summary.csv",[dict(crop=c,late_harvested_plants=z["plants"],
        mean_active_days=z["active_hours"]/24/z["plants"],
        mean_watered_days=z["watered_days"]/z["plants"],
        mean_yield_window_days=z["window_days"]/z["plants"],
        mean_window_watered_days=z["window_watered_days"]/z["plants"],
        mean_fertilized_days=z["fertilized_days"]/z["plants"],
        mean_window_fertilized_days=z["window_fertilized_days"]/z["plants"],
        mean_window_water_fert_days=z["window_water_fert_days"]/z["plants"],
        mean_harvested_units=z["harvested_units"]/z["plants"],
        mean_late_harvested_units=z["late_harvested_units"]/z["plants"],
        mean_delay_days_per_harvest=z["delay_hours"]/24/z["harvest_events"] if z["harvest_events"] else "",
        observed_replant_gaps=len(gaps[c]),median_replant_gap_days=statistics.median(gaps[c]) if gaps[c] else "")
        for c,z in sorted(lifecycle.items())])
    agent_games=Counter(g for g,_ in games)
    write("submission_crop_summary.csv",[dict(submission=g,crop=c,games=agent_games[g],plants=s["plants"],
        late_units_per_game=s["late_units"]/agent_games[g],
        hourly_units_per_cell_day=s["late_units"]*24/s["late_hours"] if s["late_hours"] else 0,
        late_window_water_share=s["late_water"]/s["late_window"] if s["late_window"] else 0,
        late_window_fert_share=s["late_fert"]/s["late_window"] if s["late_window"] else 0,
        late_window_water_fert_share=s["late_overlap"]/s["late_window"] if s["late_window"] else 0,
        fixed_action_fert_gain_per_game=(s["late_units"]-s["late_nofert"])/agent_games[g],
        mean_delay_days=s["delay_hours"]/24/s["harvest_events"] if s["harvest_events"] else "")
        for (g,c),s in sorted(by_agent.items())])
    timing=Counter();ages=Counter();sources=Counter()
    with (OUT/"fertilizer_actions.csv").open(newline="",encoding="utf-8") as file:
        for r in csv.DictReader(file):
            if not 12<=int(r["day"])<=27:
                continue
            timing[(r["crop"],int(r["day"]),int(r["hour"]))]+=1
            ages[(r["crop"],int(r["crop_age"]),r["source"])]+=1
            sources[(r["crop"],r["source"])]+=1
    write("fertilizer_day_hour.csv",[dict(crop=c,day=d,hour=h,applications=n,per_game=n/n_games) for (c,d,h),n in sorted(timing.items())])
    write("fertilizer_age_source.csv",[dict(crop=c,crop_age=a,source=s,applications=n,per_game=n/n_games) for (c,a,s),n in sorted(ages.items())])
    write("fertilizer_source.csv",[dict(crop=c,source=s,applications=n,share_of_crop=n/sum(v for (x,_),v in sources.items() if x==c)) for (c,s),n in sorted(sources.items())])
    print(json.dumps({"games":n_games,"plants":sum(v["plants"] for v in sums.values()),"fertilizations":sum(sources.values()),"crops":crop_rows},indent=2))


if __name__=="__main__":main()

"""W1 extraction: recorded D1 cohorts, then paired rev24 worker traces.
python tools/work_targets.py teachers [--workers 2] [--limit N]
python tools/work_targets.py previews [--limit N]
All generated data and receipts stay under <data>/runs/work-targets-2026-10-18.
"""
import argparse
import contextlib
import copy
import csv
from collections import Counter
import gzip
import hashlib
import io
import json
import os
from pathlib import Path
import sys
import time
from types import SimpleNamespace

REPO=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(REPO/"src"))
from kagml.paths import data_root
from kagml.work_targets import Observer,TABLES,SB,K
import pyarrow.parquet as pq

OUT=data_root()/"runs/work-targets-2026-10-18"
D1=data_root()/"datasets/d1"
TEMPLATE_SOURCE=REPO.parent/"Kaggle-Kaggriculture/.scratch/template-bench/runs/el3"


def signature():
    paths=[REPO/"src/kagml/work_targets.py",Path(__file__),Path(K.__file__)]
    return hashlib.sha256(b"".join(p.read_bytes() for p in paths)).hexdigest()


def initialize(rep):
    states=[SimpleNamespace(observation=SimpleNamespace(step=0,player=p),action={},status="ACTIVE",reward=0) for p in (0,1)]
    env=SimpleNamespace(configuration=SimpleNamespace(**rep["configuration"]),
                        info={"seed":rep["info"]["seed"]},done=False)
    K._initialize(states,env)
    return states,env


def step_recorded(rep,states,env,observer,s):
    for p in (0,1):
        states[p].action=rep["steps"][s+1][p]["action"]
        states[p].observation.step=s
    observer.begin(s,states)
    K.interpreter(states,env)
    observer.end(states)


def assert_frame(states,rep,frame):
    for p in (0,1):
        actual=vars(states[p].observation);expected=rep["steps"][frame][p]["observation"]
        for field in ("farms","private","market","town","day","hour","player"):
            assert actual[field]==expected[field],(frame,p,field)


def inputs():
    accepted=[]
    for r in csv.DictReader((D1/"manifest.csv").open()):
        cohorts={p:("reference" if r[f"sub_{p}"]=="56711476" else "second")
                 for p in (0,1) if r[f"sub_{p}"] in ("56711476","56722220")}
        if cohorts and (D1/"games"/(r["episode"]+".parquet")).exists():
            shops=pq.read_table(D1/"games"/(r["episode"]+".parquet"),columns=["shops"]).to_pylist()[0]["shops"]
            accepted.append({**r,"cohorts":cohorts,"buyers":sum(s in SB for s in shops[:2])})
    return sorted(accepted,key=lambda r:int(r["episode"]))


def one(task):
    meta,sig=task;eid=meta["episode"];run="t-"+eid
    receipt=OUT/"audit"/(run+".json")
    if receipt.exists():
        old=json.loads(receipt.read_text())
        if old.get("signature")==sig and old.get("sha256")==meta["sha256"] and all(
            n==0 or (OUT/t/(run+".parquet")).exists() for t,n in old["rows"].items()):
            return dict(run=run,status="cached")
    start=time.perf_counter()
    path=data_root()/"raw/replays"/meta["folder"]/(eid+".json.gz")
    raw=path.read_bytes();assert hashlib.sha256(raw).hexdigest()==meta["sha256"]
    rep=json.loads(gzip.decompress(raw))
    cohorts={int(p):c for p,c in meta["cohorts"].items()}
    o=Observer(run,eid,cohorts,meta["buyers"])
    states,env=initialize(rep)
    with o:
        for s in range(len(rep["steps"])-1):
            step_recorded(rep,states,env,o,s)
            if (s+1)%24==0 or s==len(rep["steps"])-2:
                assert_frame(states,rep,s+1);o.checks["exact_frames"]+=1
    o.finish(states,len(rep["steps"])-2,"season_end")
    # D1 remains the authority for existence, effective operations and positions.
    cols=["step","seat","unit","x","y","effective_command","took_effect","exists"]
    expected={}
    for row in pq.read_table(D1/"unit_actions"/(eid+".parquet"),columns=cols).to_pylist():
        if row["exists"] and row["seat"] in cohorts and row["step"]//24>=6:
            expected[(row["seat"],row["step"],row["unit"])]=row
    assert len(expected)==len(o.rows["events"]),(eid,len(expected),len(o.rows["events"]))
    for row in o.rows["events"]:
        e=expected.pop((row["seat"],row["step"],row["unit"]))
        command=json.loads(e["effective_command"])
        op=command[0] if isinstance(command,list) and command else "PASS"
        assert (row["x"],row["y"],row["op"],row["effective"])==(e["x"],e["y"],op,e["took_effect"]),(eid,row,e)
    assert not expected
    o.checks["D1_unit_rows"]=len(o.rows["events"])
    expected_fert=sum(r["units"] for r in pq.read_table(D1/"sales"/(eid+".parquet"),
        columns=["step","seat","product","units"]).to_pylist()
        if r["step"]//24>=6 and r["seat"] in cohorts and r["product"]=="FERTILIZER")
    actual_fert=sum(r["units"] for r in o.rows["flows"] if r["op"]=="SELL" and r["item"]=="FERTILIZER")
    assert actual_fert==expected_fert,(eid,actual_fert,expected_fert)
    o.checks["fertilizer_sales_units"]=actual_fert
    o.save(OUT,dict(run=run,status="kept",sha256=meta["sha256"],signature=sig,
                   source=str(path),seconds=round(time.perf_counter()-start,3),cohorts=cohorts,
                   buyers=meta["buyers"]))
    return dict(run=run,status="kept",seconds=round(time.perf_counter()-start,2),
                events=len(o.rows["events"]),doses=len(o.rows["doses"]))


def preview_inputs():
    rows=list(csv.DictReader((data_root()/"runs/compare/rev24.csv").open()))
    return rows,sorted({r["game"] for r in rows},key=int),sorted({int(r["day"]) for r in rows})


def previews(limit):
    from kagml.preview import TemplatePlayer,env_from_snapshot,snapshot_from_replay,pin_weeds
    from kagml.opponents import load
    rows,games,days=preview_inputs()
    if limit:games=games[:limit]
    expected={(r["game"],int(r["day"]),r["player"]):r for r in rows}
    pin_weeds(True)
    fourth=load("fourth")
    results=[]
    for game in games:
        path=TEMPLATE_SOURCE/(game+".json");rep=json.loads(path.read_text())
        buyers=sum(s in SB for s in rep["steps"][144][0]["observation"]["town"]["unlocked_shops"][:2])
        template=TemplatePlayer()
        memories={};done=0
        for day in days:
            for s in range(done,day*24):
                template(rep["steps"][s][0]["observation"],rep["configuration"])
            done=day*24;memories[day]=template.memory()
        # Recorded-action warm-up provides exact availability clocks at every saved morning.
        pin_weeds(True)
        states,env=initialize(rep)
        warm=Observer("warm",game,{0:"template"},buyers,record_days=())
        from kagml.preview import _ORIG_WEEDS
        import random
        original=K._spawn_weeds
        K._spawn_weeds=lambda farm,n,chance,rng:_ORIG_WEEDS(farm,n,chance,random.Random(rng.random()))
        snapshots={}
        try:
            with warm:
                for s in range(max(days)*24):
                    if s in {d*24 for d in days}:snapshots[s//24]=copy.deepcopy(warm)
                    step_recorded(rep,states,env,warm,s)
                    if (s+1)%24==0:assert_frame(states,rep,s+1)
                snapshots[max(days)]=copy.deepcopy(warm)
        finally:K._spawn_weeds=original
        for day in days:
            snap=snapshot_from_replay(rep,day*24)
            for name,player in (("template",template),("fourth",fourth)):
                if name=="template":template.restore(memories[day])
                run=f"rev-{game}-{day}-{name}"
                o=snapshots[day];o=copy.deepcopy(o)
                o.run=run;o.cohorts={0:name};o.record_days={day}
                o.rows.clear();o.plant_days.clear();o.animal_days.clear()
                o.active=False
                e=env_from_snapshot(snap)
                # The first day matches rev24. Extra 72 turns only follow that day's doses.
                end24=None;retained=None;issued=Counter()
                with o:
                    for n in range(96):
                        s=day*24+n
                        if s>=719:break
                        ours=player(e.state[0].observation,e.configuration)
                        if n<24 and isinstance(ours,dict):
                            for cmd in [ours.get("farmer")]+list(ours.get("hands") or []):
                                if isinstance(cmd,list) and cmd:issued[cmd[0]]+=1
                        theirs=rep["steps"][s+1][1]["action"]
                        o.begin(s,e.state);e.step([ours,theirs]);o.end(e.state)
                        if n==23:
                            from kagml.preview import summary
                            end24={"cash":e.state[0].observation.farms[0].money}
                            retained=(copy.deepcopy(fourth.play._FLOW),fourth.rng.clone(),
                                      dict(fourth.last_steps)) if name=="fourth" else None
                        if n>=23 and not any(o.shadows.values()):break
                o.finish(e.state,day*24+n,"window_end")
                if retained:
                    fourth.play._FLOW.clear();fourth.play._FLOW.update(retained[0])
                    fourth.rng=retained[1];fourth.last_steps=retained[2]
                exp=expected[(game,day,name)]
                cash0=snap["obs"][0]["farms"][0]["money"]
                assert end24["cash"]-cash0==float(exp["cash_change"]),(game,day,name,end24,exp["cash_change"])
                for op in ("PLANT","WATER","HARVEST","FEED","CARE","FERTILIZE","COLLECT_FERTILIZER","DIG","PICKUP","DROP","PLACE"):
                    assert issued[op]==int(exp["n_"+op.lower()]),(game,day,name,op,issued[op],exp["n_"+op.lower()])
                o.checks["rev24_exact_issued_counts"]=11
                o.checks["rev24_exact_cash"]=1
                o.save(OUT,dict(run=run,status="kept",source=str(path),signature=signature(),
                    sha256=hashlib.sha256(path.read_bytes()).hexdigest(),buyers=buyers,
                    measured_day=day,followup_turns=n+1,rev24_exact_cash=True,rev24_exact_issued_counts=True))
                results.append(dict(game=game,day=day,cohort=name,events=len(o.rows["events"]),
                                    doses=len(o.rows["doses"]),rev24_exact_cash=True,rev24_exact_issued_counts=True))
                print(json.dumps(results[-1]),flush=True)
    (OUT/"preview_validation.json").write_text(json.dumps(results,indent=2))


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",choices=("teachers","previews"))
    ap.add_argument("--workers",type=int,choices=(1,2),default=2)
    ap.add_argument("--limit",type=int)
    a=ap.parse_args();OUT.mkdir(parents=True,exist_ok=True)
    if a.mode=="previews":
        previews(a.limit);return
    tasks=inputs()
    (OUT/"inputs.json").write_text(json.dumps(tasks,indent=2))
    if a.limit:tasks=tasks[:a.limit]
    sig=signature()
    from multiprocessing import Pool
    with Pool(a.workers) as pool:
        for i,row in enumerate(pool.imap_unordered(one,[(r,sig) for r in tasks]),1):
            print(f"{i}/{len(tasks)} "+json.dumps(row),flush=True)


if __name__=="__main__":main()

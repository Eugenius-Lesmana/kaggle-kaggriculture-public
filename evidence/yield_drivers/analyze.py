"""Stream top-three replays into crop lifecycles and successful fertilizer actions."""
import argparse
import contextlib
import csv
import gzip
import io
import json
from collections import Counter
from pathlib import Path

with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
    import kaggle_environments.envs.kaggriculture.kaggriculture as game

OUT = Path(__file__).resolve().parent
TOP = {"56654377", "56664798", "56666211"}
PLANT = "submission game x y crop planted_day planted_step ended_day ended_step end_reason censored active_hours late_hours watered_days window_days window_watered_days fertilized_days window_fertilized_days window_water_fert_days late_window_days late_window_watered_days late_window_fertilized_days late_window_water_fert_days harvest_events harvested_units late_harvested_units no_fert_harvested_units late_no_fert_units last_harvest_units delay_hours last_yield_units replant_gap_hours".split()
FERT = "submission game day hour step worker x y crop crop_age source held_before direct_before shed_before unknown_before".split()


def paths(intake):
    for folder in sorted(intake.iterdir()):
        if folder.name not in TOP:
            continue
        index = {int(e["id"]): e for e in json.loads((folder / "episodes.json").read_text(encoding="utf-8"))["episodes"]}
        for path in sorted(folder.glob("*.json.gz")):
            episode = index.get(int(path.name.split(".")[0]))
            if episode:
                seats = [i for i, a in enumerate(episode["agents"]) if str(a["submissionId"]) == folder.name]
                if len(seats) == 1:
                    yield folder.name, path, seats[0]


def key(x, y, tile):
    return x, y, tile["crop"], tile["planted_day"]


def in_window(crop, age):
    cd = game.CROPS[crop]
    if not cd["ongoing"]:
        return (cd["max_yield_day"] + 1)//2 <= age <= cd["max_yield_day"]
    n = age + 1 - cd["first_yield_day"]
    return n >= 0 and n % cd["interval"] == 0 and n//cd["interval"] < cd["max_yield"]


def make(group, path, x, y, tile, step):
    r = {f: 0 for f in PLANT}
    r.update(submission=group, game=path.name, x=x, y=y, crop=tile["crop"],
        planted_day=tile["planted_day"], planted_step=step, ended_day="", ended_step="",
        end_reason="", replant_gap_hours="", _last_day=-1, _ripe=None,
        _no_fert=0 if game.CROPS[tile["crop"]]["ongoing"] else 1)
    return r


def day_count(r, tile, day):
    if r["_last_day"] == day:
        return
    r["_last_day"] = day
    water = bool(tile["watered_today"])
    fert = tile.get("fertilized_until_day", -1) >= day
    due = in_window(r["crop"], day-r["planted_day"])
    for name, value in (("watered_days",water),("fertilized_days",fert),
        ("window_days",due),("window_watered_days",due and water),
        ("window_fertilized_days",due and fert),("window_water_fert_days",due and water and fert)):
        r[name] += value
    if 12 <= day <= 27:
        for name,value in (("late_window_days",due),("late_window_watered_days",due and water),
            ("late_window_fertilized_days",due and fert),
            ("late_window_water_fert_days",due and water and fert)):
            r[name] += value


def end(r, tile, step, reason, pending, finished):
    if r["ended_step"] != "":
        return
    r.update(ended_step=step, ended_day=step//24, end_reason=reason,
             last_yield_units=tile.get("yield_units", 0))
    pending[(r["x"],r["y"])] = r, step
    finished.append(r)


def one(group, path, seat, pw, fw):
    with gzip.open(path, "rt", encoding="utf-8") as file:
        replay = json.load(file)
    steps, live, finished, pending = replay["steps"], {}, [], {}
    sources, stats = [], Counter()
    for step in range(1, len(steps)):
        before = steps[step-1][seat]["observation"]
        after = steps[step][seat]["observation"]
        day, hour = before["day"], before["hour"]
        farm0, private0 = before["farms"][seat], before["private"]
        action = steps[step][seat].get("action") or {}
        commands = [action.get("farmer",["PASS"])] + list(action.get("hands") or [])
        if hour == 0:
            sources = [Counter(unknown=inv.get("FERTILIZER",0)) for inv in private0["inventories"]]
        while len(sources) < len(private0["inventories"]):
            sources.append(Counter())
        for y, row in enumerate(farm0["tiles"]):
            for x, tile in enumerate(row):
                if not isinstance(tile,dict) or tile.get("kind") != "PLANT":
                    continue
                k = key(x,y,tile)
                if k not in live:
                    live[k] = make(group,path,x,y,tile,step-1)
                r = live[k]
                r["active_hours"] += 1
                r["late_hours"] += 12 <= day <= 27
                if tile["yield_units"] > 0 and day-tile["planted_day"] >= game.CROPS[tile["crop"]]["first_yield_day"]:
                    if r["_ripe"] is None:
                        r["_ripe"] = step-1
                elif tile["yield_units"] == 0:
                    r["_ripe"] = None
        tiles = [row.copy() for row in farm0["tiles"]]
        for x,y in [farm0["farmer"]] + farm0["hands"]:
            if isinstance(tiles[y][x],dict):
                tiles[y][x] = tiles[y][x].copy()
        farm = {**farm0,"tiles":tiles,"farmer":farm0["farmer"].copy(),
                "hands":[p.copy() for p in farm0["hands"]]}
        private = {**private0,"shed":private0["shed"].copy(),"seeds":private0["seeds"].copy(),
                   "inventories":[v.copy() for v in private0["inventories"]]}
        demand = Counter(a[1] for a in commands if isinstance(a,list) and len(a)>=2 and a[0]=="PLANT")
        blocked = {crop for crop,n in demand.items() if n>private0["seeds"].get(crop,0)}
        for worker,op in enumerate(commands):
            if not isinstance(op,list) or not op:
                continue
            if len(op)>=2 and op[0]=="PLANT" and op[1] in blocked:
                op=["PASS"]
            pos=game._farmer_position(farm,worker)
            if pos is None:
                continue
            x,y=pos
            tile=farm["tiles"][y][x]
            k=key(x,y,tile) if isinstance(tile,dict) and tile.get("kind")=="PLANT" else None
            r=live.get(k)
            inv=game._farmer_inventory(private,worker)
            held=inv.get("FERTILIZER",0)
            prior=sources[worker].copy()
            units=tile.get("yield_units",0) if isinstance(tile,dict) else 0
            was_watered=tile.get("watered_today",False) if isinstance(tile,dict) else False
            game._apply_unit_action(farm,private,worker,op,len(tiles),day,24,
                                    replay["configuration"].get("shedCapacity",100))
            now=game._farmer_inventory(private,worker).get("FERTILIZER",0)
            name=op[0]
            if name=="WATER" and r and not was_watered and farm["tiles"][y][x]["watered_today"] and not game.CROPS[r["crop"]]["ongoing"] and in_window(r["crop"],day-r["planted_day"]):
                r["_no_fert"]=min(game.CROPS[r["crop"]]["max_yield"],r["_no_fert"]+1)
            if now>held:
                src="direct" if name=="COLLECT_FERTILIZER" else "shed" if name=="PICKUP" else "unknown"
                sources[worker][src]+=now-held
            elif now<held:
                pool=sources[worker]
                if sum(pool.values())!=held:
                    pool.clear();pool["unknown"]=held
                kinds=[s for s,n in pool.items() if n]
                src=kinds[0] if len(kinds)==1 else "mixed" if kinds else "unknown"
                if name=="FERTILIZE" and r:
                    fw.writerow(dict(submission=group,game=path.name,day=day,hour=hour,
                        step=step-1,worker=worker,x=x,y=y,crop=r["crop"],
                        crop_age=day-r["planted_day"],source=src,held_before=held,
                        direct_before=prior["direct"],shed_before=prior["shed"],
                        unknown_before=prior["unknown"]))
                    stats[("fert",src)]+=1
                if len(kinds)==1:
                    pool[kinds[0]]-=held-now
                else:
                    pool.clear();pool["unknown"]=now
            if name=="HARVEST" and r and units>0 and day-r["planted_day"]>=game.CROPS[r["crop"]]["first_yield_day"]:
                cf=r["_no_fert"]
                r["harvest_events"]+=1
                r["harvested_units"]+=units
                r["no_fert_harvested_units"]+=cf
                r["last_harvest_units"]=units
                r["late_harvested_units"]+=units if 12<=day<=27 else 0
                r["late_no_fert_units"]+=cf if 12<=day<=27 else 0
                r["_no_fert"]=0
                r["delay_hours"]+=max(0,step-1-(r["_ripe"] if r["_ripe"] is not None else step-1))
                r["_ripe"]=None
                if not game.CROPS[r["crop"]]["ongoing"]:
                    day_count(r,tile,day)
                    end(r,tile,step-1,"harvest",pending,finished)
                    del live[k]
            elif name=="DIG" and r and farm["tiles"][y][x] is None:
                day_count(r,tile,day)
                end(r,tile,step-1,"dig",pending,finished)
                del live[k]
            elif name=="PLANT":
                planted=farm["tiles"][y][x]
                if tile is None and isinstance(planted,dict) and planted.get("kind")=="PLANT":
                    live[key(x,y,planted)]=make(group,path,x,y,planted,step-1)
                    if (x,y) in pending:
                        old,ended=pending.pop((x,y))
                        old["replant_gap_hours"]=step-1-ended
        if hour==23:
            for k,r in live.items():
                x,y=r["x"],r["y"]
                tile=farm["tiles"][y][x]
                if isinstance(tile,dict) and tile.get("kind")=="PLANT" and key(x,y,tile)==k:
                    day_count(r,tile,day)
        for k,r in live.items():
            x,y=r["x"],r["y"]
            tile=farm["tiles"][y][x]
            if not isinstance(tile,dict) or tile.get("kind")!="PLANT" or key(x,y,tile)!=k:
                continue
            mls=tile["max_lifespan_step"]
            if mls>=0 and step-1>=mls and (step-1-mls)%2==0:
                r["_no_fert"]=max(0,r["_no_fert"]-1)
            next_tile=after["farms"][seat]["tiles"][y][x]
            if hour==23 and game.CROPS[r["crop"]]["ongoing"] and in_window(r["crop"],day-r["planted_day"]) and isinstance(next_tile,dict) and next_tile.get("kind")=="PLANT" and key(x,y,next_tile)==k:
                r["_no_fert"]=min(game.CROPS[r["crop"]]["max_yield"],r["_no_fert"]+1)
        new_tiles=after["farms"][seat]["tiles"]
        for k,r in list(live.items()):
            x,y=r["x"],r["y"]
            tile=new_tiles[y][x]
            if not isinstance(tile,dict) or tile.get("kind")!="PLANT" or key(x,y,tile)!=k:
                current=farm["tiles"][y][x]
                if isinstance(current,dict) and current.get("kind")=="PLANT" and key(x,y,current)==k:
                    day_count(r,current,day)
                    reason="weed" if isinstance(tile,dict) and tile.get("kind")=="WEED" else "vanished"
                    end(r,current,step,reason,pending,finished)
                else:
                    end(r,{},step,"vanished",pending,finished)
                del live[k]
        stats["steps"]+=1
    for r in live.values():
        r["censored"]=1
        r["end_reason"]="replay_end"
        finished.append(r)
    for r in finished:
        if r["late_hours"] or 12<=r["planted_day"]<=27:
            pw.writerow({f:r[f] for f in PLANT})
            stats["late_plants"]+=1
    return stats


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--intake",type=Path,required=True)
    p.add_argument("--limit",type=int)
    args=p.parse_args()
    totals=Counter()
    with (OUT/"plant_lifecycles.csv").open("w",newline="",encoding="utf-8") as a, (OUT/"fertilizer_actions.csv").open("w",newline="",encoding="utf-8") as b:
        pw=csv.DictWriter(a,PLANT);pw.writeheader()
        fw=csv.DictWriter(b,FERT);fw.writeheader()
        for i,(group,path,seat) in enumerate(paths(args.intake),1):
            totals.update(one(group,path,seat,pw,fw))
            totals["games"]+=1
            if i%25==0:print(i,flush=True)
            if args.limit and i>=args.limit:break
    print(dict(totals))


if __name__=="__main__":
    main()

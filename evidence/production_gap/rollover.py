"""Count top-agent hour-23 production omitted by the planner diagnostic."""
import csv
import gzip
import json
from collections import Counter, defaultdict
from pathlib import Path

from analyze import ANIMALS, OUT, engine, phase, replay_paths

def rollover_units(data, seat):
    steps = data["steps"]
    cfg = data["configuration"]
    result = Counter()
    for day in range(28):
        i = (day+1)*24
        if i >= len(steps):
            continue
        before = steps[i-1][seat]["observation"]
        action = steps[i][seat].get("action") or {}
        original = before["farms"][seat]
        tiles = [row.copy() for row in original["tiles"]]
        for pos in [original["farmer"]] + list(original["hands"]):
            x,y = pos
            if isinstance(tiles[y][x],dict):
                tiles[y][x] = tiles[y][x].copy()
        farm = {**original,"farmer":original["farmer"].copy(),
                "hands":[p.copy() for p in original["hands"]],
                "tiles":tiles}
        q = before["private"]
        private = {**q,"shed":q["shed"].copy(),"seeds":q["seeds"].copy(),
                   "inventories":[v.copy() for v in q["inventories"]]}
        commands = [action.get("farmer",["PASS"])] + list(action.get("hands") or [])
        for worker, command in enumerate(commands):
            if not isinstance(command,list) or not command:
                continue
            pos = engine._farmer_position(farm,worker)
            if pos is None:
                continue
            x,y=pos
            tile=farm["tiles"][y][x]
            tile=tile if isinstance(tile,dict) else {}
            product=tile.get("crop") or ANIMALS.get(tile.get("animal"))
            inventory=engine._farmer_inventory(private,worker)
            before_count=inventory.get("FERTILIZER",0) if command[0]=="COLLECT_FERTILIZER" else inventory.get(product,0) if product else 0
            engine._apply_unit_action(farm,private,worker,command,
                cfg.get("boardSize",10),day,cfg.get("turnsPerDay",24),cfg.get("shedCapacity",100))
            inventory=engine._farmer_inventory(private,worker)
            if command[0]=="HARVEST" and product:
                result[(phase(day),product)]+=max(0,inventory.get(product,0)-before_count)
            elif command[0]=="COLLECT_FERTILIZER":
                result[(phase(day),"FERTILIZER")]+=max(0,inventory.get("FERTILIZER",0)-before_count)
    return result

def main():
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument("--intake",type=Path,required=True)
    args=parser.parse_args()
    rows=[]
    for index,(group,path,seat) in enumerate(replay_paths(args.intake)):
        with gzip.open(path,"rt",encoding="utf-8") as file:
            data=json.load(file)
        counts=rollover_units(data,seat)
        for (phase_name,product),units in counts.items():
            rows.append(dict(group=group,game=path.name,phase=phase_name,product=product,units=units))
        if (index+1)%100==0:print(index+1,flush=True)
    with (OUT/"rollover_harvest.csv").open("w",newline="",encoding="utf-8") as file:
        writer=csv.DictWriter(file,fieldnames=("group","game","phase","product","units"))
        writer.writeheader();writer.writerows(rows)
    grouped=defaultdict(int)
    for row in rows:
        grouped[(row["group"],row["phase"],row["product"])]+=row["units"]
    print("rows",len(rows),"units",sum(row["units"] for row in rows))

if __name__=="__main__":
    main()

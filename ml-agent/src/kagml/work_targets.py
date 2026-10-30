"""W1 measurement hooks. Only recorded/native operations are observed; no policy logic."""
import copy
import hashlib
import json
from collections import defaultdict, deque
from pathlib import Path
import sys

import pyarrow as pa
import pyarrow.parquet as pq
from kagml.replay_tables import K, snapshot

MOVES = set(K.FARMER_MOVES)
ANIMAL_JOBS = {"FEED", "CARE", "COLLECT_FERTILIZER", "HARVEST"}
SERVICE = {"PLANT", "WATER", "HARVEST", "FERTILIZE", "FEED", "CARE",
           "COLLECT_FERTILIZER", "DIG", "BUILD_COOP", "BUILD_PASTURE", "PLACE"}
SB = {"ICE_CREAM_SHOP", "BRUNCH_SPOT", "SMOOTHIE_SHOP", "FARMERS_MARKET"}
NATIVE = {n:getattr(K,n) for n in ("_apply_unit_action", "_process_market", "_commit_unit",
          "_daily_refresh_plants", "_daily_refresh_animals", "_decay_plants", "_drop_inventories_to_shed")}
STRINGS = {"run","game","cohort","op","kind","crop","animal","item","command","reason"}
BOOLS = {"effective","on_shed","watered","fed","cared","fert_available","due","bonus_window",
         "risk","queue_clean","at_midnight","complete_day","collected","complete","censored",
         "watered_before","watered_apply_day","ongoing","selected"}
FLOATS = {"ratio","wait_mean","price_ratio","first_ready_wait","first_fert_wait"}
TABLES = ("events","doses","plant_days","animal_days","flows","markets")


def ready(tile, day):
    if not isinstance(tile,dict):
        return 0
    if tile.get("kind")=="PLANT" and day-tile["planted_day"] < K.CROPS[tile["crop"]]["first_yield_day"]:
        return 0
    return int(tile.get("yield_units",0))


def due(tile, day):
    if not isinstance(tile,dict) or tile.get("kind")!="PLANT":
        return False
    c=K.CROPS[tile["crop"]];age=day-tile["planted_day"]
    if not c["ongoing"]:
        return (c["max_yield_day"]+1)//2 <= age <= c["max_yield_day"]
    n=day+1-tile["planted_day"]-c["first_yield_day"]
    return n>=0 and n%c["interval"]==0 and n//c["interval"]<c["max_yield"]


def write_table(path, rows):
    if not rows:
        return
    keys=list(rows[0])
    assert all(set(r)==set(keys) for r in rows), path
    fields=[(k,pa.string() if k in STRINGS else pa.bool_() if k in BOOLS else
             pa.float64() if k in FLOATS else pa.int64()) for k in keys]
    table=pa.Table.from_pylist(rows,schema=pa.schema(fields))
    tmp=path.with_suffix(".tmp")
    pq.write_table(table,tmp,compression="zstd")
    tmp.replace(path)


class Shadow:
    """One-dose omission, following the actual crop's later work through native rules."""
    def __init__(self,tile):
        self.farm={"tiles":[[copy.deepcopy(tile)]],"farmer":[0,0],"hands":[]}
        self.harvested=0

    def act(self, op, day):
        private={"inventories":[{"FERTILIZER":1}],"seeds":{},"shed":{}}
        NATIVE["_apply_unit_action"](self.farm,private,0,[op],10,day,24,100)
        if op=="HARVEST":
            self.harvested+=sum(v for k,v in private["inventories"][0].items() if k!="FERTILIZER")

    def refresh(self,day):
        NATIVE["_daily_refresh_plants"](self.farm,day,24)

    def decay(self,step):
        NATIVE["_decay_plants"](self.farm,step)

    def held(self):
        t=self.farm["tiles"][0][0]
        return t.get("yield_units",0) if isinstance(t,dict) and t.get("kind")=="PLANT" else 0


class Observer:
    def __init__(self,run,game,cohorts,buyers,record_days=range(6,30)):
        self.run,self.game=str(run),str(game)
        self.cohorts=dict(cohorts);self.buyers=int(buyers);self.record_days=set(record_days)
        self.rows=defaultdict(list);self.cells={};self.serial=defaultdict(int)
        self.plant_days={};self.animal_days={};self.history={};self.shadows=defaultdict(list)
        self.active=False;self.step=0;self.farm_seats={};self.private_seats={}
        self.seen=set();self.sales=defaultdict(lambda:[0,0]);self.best=defaultdict(int)
        self.dose_count=0;self.checks=defaultdict(int)

    def base(self,seat,**fields):
        return dict(run=self.run,game=self.game,cohort=self.cohorts[seat],seat=seat,
                    buyers=self.buyers,**fields)

    def recording(self,day=None):
        return (self.step//24 if day is None else day) in self.record_days

    def begin(self,step,states):
        self.step=step;self.seen=set();self.sales=defaultdict(lambda:[0,0])
        self.farms=states[0].observation.farms
        self.farm_seats={id(f):p for p,f in enumerate(self.farms)}
        self.private_seats={id(s.observation.private):p for p,s in enumerate(states)}
        self.prices=dict(states[0].observation.market["prices"])
        day=step//24
        for product,price in self.prices.items():
            self.best[(day,product)]=max(self.best[(day,product)],price)
            if self.recording():
                self.rows["markets"].append(dict(run=self.run,game=self.game,step=step,day=day,
                                                 hour=step%24,item=product,price=price))
        self.sync(states,step)
        self.active=True

    def end(self,states):
        self.active=False
        self.sync(states,self.step+1)
        for (seat,op,item,price),(units,cash) in self.sales.items():
            if self.recording():
                self.rows["flows"].append(self.base(seat,step=self.step,day=self.step//24,
                    hour=self.step%24,unit=-1,x=None,y=None,op=op,item=item,
                    bag_delta=0,shed_delta=-units if op=="SELL" else units,
                    bag_before=0,bag_after=0,on_shed=False,units=units,revenue=cash))
        self.checks["turns"]+=1

    def cell(self,seat,x,y,tile,step,harvest=False):
        key=(seat,x,y);day=step//24
        if not isinstance(tile,dict) or (tile.get("kind")!="PLANT" and not tile.get("animal")):
            if key in self.cells:
                self.close_cell(key,step,"removed",tile)
            return None
        ident=(tile.get("crop") or tile.get("animal"),tile.get("planted_day",tile.get("placed_day")))
        c=self.cells.get(key)
        if c is None or c["ident"]!=ident:
            if c is not None:self.close_cell(key,step,"replaced",tile)
            self.serial[key]+=1
            c=self.cells[key]={"ident":ident,"id":self.serial[key],"queue":deque(),
                "known":0,"clean":True,"fert_since":None,"fert_known":False}
        available=ready(tile,day);delta=available-c["known"]
        if harvest:
            c["queue"].clear();c["clean"]=True
        elif delta<0:
            left=-delta;c["clean"]=False
            while left and c["queue"]:
                batch=c["queue"][0];take=min(left,batch[1]);left-=take;batch[1]-=take
                if not batch[1]:c["queue"].popleft()
        if delta>0:
            c["queue"].append([step,delta])
        c["known"]=available
        flag=bool(tile.get("fertilizer_available"))
        if flag and not c["fert_known"]:c["fert_since"]=step
        if not flag:c["fert_since"]=None
        c["fert_known"]=flag
        if self.recording(day):
            dkey=(*key,c["id"],day)
            if tile.get("kind")=="PLANT":
                if dkey not in self.plant_days:
                    self.plant_days[dkey]=self.base(seat,day=day,x=x,y=y,spell=c["id"],
                        crop=tile["crop"],age=day-tile["planted_day"],due=due(tile,day),
                        risk=tile.get("consecutive_unwatered",0)>=1,first_hour=step%24,
                        watered=bool(tile.get("watered_today")),water_hour=None,fert_uses=0,
                        at_midnight=False,complete_day=False)
            elif dkey not in self.animal_days:
                self.animal_days[dkey]=self.base(seat,day=day,x=x,y=y,spell=c["id"],
                    animal=tile["animal"],age=day-tile["placed_day"],first_hour=step%24,
                    fed=bool(tile.get("fed_today")),cared=bool(tile.get("cared_today")),
                    collected=False,feed_hour=None,care_hour=None,collect_hour=None,
                    feed_unit=None,care_unit=None,feed_visit=None,care_visit=None,
                    at_midnight=False,complete_day=False,first_fert_wait=None)
        return c

    def sync(self,states,step):
        self.farms=states[0].observation.farms
        for seat in self.cohorts:
            for y,row in enumerate(self.farms[seat]["tiles"]):
                for x,tile in enumerate(row):
                    self.cell(seat,x,y,tile,step)
        for key,doses in list(self.shadows.items()):
            for dose in list(doses):
                if self.step>=dose["end"]:
                    self.finish_dose(key,dose,self.step,"72h")

    def close_cell(self,key,step,reason,tile):
        for dose in list(self.shadows.get(key,[])):
            self.finish_dose(key,dose,step,reason,tile)
        self.cells.pop(key,None)

    def finish_dose(self,key,dose,step,reason,tile=None):
        if tile is None:
            s,x,y=key;tile=self.farms[s]["tiles"][y][x]
        held=tile.get("yield_units",0) if reason not in ("harvested","dug","removed","replaced") and isinstance(tile,dict) and tile.get("kind")=="PLANT" else 0
        row=dose["row"]
        row.update(marginal_harvest=dose["actual"]-dose["shadow"].harvested,
                   marginal_held=max(0,held-dose["shadow"].held()),followup_hours=max(0,step-row["step"]),
                   complete=reason in ("72h","harvested","dug","removed","replaced"),
                   censored=reason not in ("72h","harvested","dug","removed","replaced"),reason=reason)
        assert row["marginal_harvest"]>=0,(key,row)
        self.shadows[key].remove(dose)

    def dose(self,seat,x,y,tile):
        key=(seat,x,y);day=self.step//24;self.dose_count+=1
        row=self.base(seat,step=self.step,day=day,hour=self.step%24,x=x,y=y,
            dose=self.dose_count,crop=tile["crop"],age=day-tile["planted_day"],
            ongoing=bool(K.CROPS[tile["crop"]]["ongoing"]),due=due(tile,day),
            watered_before=bool(tile["watered_today"]),watered_apply_day=bool(tile["watered_today"]),
            fert_until_before=tile["fertilized_until_day"],held_at_apply=tile["yield_units"],
            marginal_harvest=0,marginal_held=0,followup_hours=0,complete=False,censored=True,
            reason="pending",water_events=0)
        self.rows["doses"].append(row)
        self.shadows[key].append({"shadow":Shadow(tile),"actual":0,"end":self.step+72,"row":row})

    def history_for(self,seat,unit,pos):
        key=(seat,self.step//24,unit);h=self.history.get(key)
        if h is None:
            h=self.history[key]={"pos":pos,"visit":1,"trip":0,"feed_pos":None}
        elif h["pos"]!=pos:
            if h["pos"] in {(4,4),(4,5),(5,4),(5,5)} and pos not in {(4,4),(4,5),(5,4),(5,5)}:
                h["trip"]+=1
            h["visit"]+=1;h["pos"]=pos
        return h

    def observe(self,seat,farm,private,unit,action,args,execute=True):
        before=snapshot(farm,private,unit)
        if before is None:
            if execute:return NATIVE["_apply_unit_action"](farm,private,unit,action,*args)
            return
        x,y=before[0];tile=farm["tiles"][y][x]
        t=tile.copy() if isinstance(tile,dict) else {}
        c=self.cell(seat,x,y,tile,self.step)
        inv=private["inventories"][unit].copy();shed=private["shed"].copy()
        money=farm["money"];op=action[0] if isinstance(action,list) and action else "PASS"
        h=self.history_for(seat,unit,(x,y));day=self.step//24
        self.seen.add((seat,unit))
        queue=list(c["queue"]) if c else []
        wait_mean=(sum((self.step-b[0])*b[1] for b in queue)/sum(b[1] for b in queue)) if queue else None
        fert_wait=self.step-c["fert_since"] if c and c["fert_since"] is not None else None
        feed_distance=feed_best=None
        if t.get("animal") and h["feed_pos"] is not None:
            px,py=h["feed_pos"];feed_distance=abs(px-x)+abs(py-y)
            feed_best=min((abs(px-a)+abs(py-b) for b,row in enumerate(farm["tiles"])
                for a,q in enumerate(row) if isinstance(q,dict) and q.get("animal") and not q.get("fed_today")),default=None)
        nready=0
        if c and c["known"]>0:
            for dy in range(-2,3):
                for dx in range(-2,3):
                    if 0<abs(dx)+abs(dy)<=2 and 0<=x+dx<10 and 0<=y+dy<10:
                        nready+=ready(farm["tiles"][y+dy][x+dx],day)>0
        result=NATIVE["_apply_unit_action"](farm,private,unit,action,*args) if execute else None
        after=snapshot(farm,private,unit)
        effect=before!=after or money!=farm["money"]
        post=farm["tiles"][y][x];key=(seat,x,y)
        if effect and op in ("WATER","FERTILIZE","HARVEST") and t.get("kind")=="PLANT":
            for dose in list(self.shadows.get(key,[])):
                if self.step<=dose["end"]:
                    dose["shadow"].act(op,day)
                    if op=="HARVEST":dose["actual"]+=t["yield_units"]
                    if op=="WATER":
                        dose["row"]["water_events"]+=1
                        if day==dose["row"]["day"]:dose["row"]["watered_apply_day"]=True
            if op=="FERTILIZE" and self.recording():self.dose(seat,x,y,t)
            if op=="HARVEST" and not K.CROPS[t["crop"]]["ongoing"]:
                for dose in list(self.shadows.get(key,[])):self.finish_dose(key,dose,self.step,"harvested",post)
        if effect and op=="DIG" and t.get("kind")=="PLANT":
            for dose in list(self.shadows.get(key,[])):self.finish_dose(key,dose,self.step,"dug",post)
        if self.recording():
            cap=K.CROPS[t["crop"]]["max_yield"] if t.get("crop") else K.ANIMALS[t["animal"]]["max_held"] if t.get("animal") else None
            item=t.get("crop") or (K.ANIMALS[t["animal"]]["product"] if t.get("animal") else None)
            r=self.base(seat,step=self.step,day=day,hour=self.step%24,unit=unit,x=x,y=y,
                op=op,effective=effect,kind=t.get("kind","EMPTY"),crop=t.get("crop"),animal=t.get("animal"),
                age=day-t.get("planted_day",t.get("placed_day",day)),yield_before=t.get("yield_units",0),
                cap=cap,ratio=t.get("yield_units",0)/cap if cap else None,
                bag_total=sum(inv.values()),wheat=inv.get("WHEAT",0),fert=inv.get("FERTILIZER",0),
                watered=bool(t.get("watered_today")),fed=bool(t.get("fed_today")),cared=bool(t.get("cared_today")),
                fert_available=bool(t.get("fertilizer_available")),fert_until=t.get("fertilized_until_day",-1),
                due=due(t,day),bonus_window=bool(t.get("crop") and not K.CROPS[t["crop"]]["ongoing"] and due(t,day)),
                risk=t.get("consecutive_unwatered",t.get("consecutive_unfed",0))>=1,
                on_shed=(x,y) in {(4,4),(4,5),(5,4),(5,5)},visit=h["visit"],trip=h["trip"],
                near_ready=nready,wait_mean=wait_mean,first_ready_wait=float(self.step-queue[0][0]) if queue else None,
                queue_clean=bool(c is None or c["clean"]),first_fert_wait=float(fert_wait) if fert_wait is not None else None,
                item=item,price=self.prices.get(item),best_so_far=self.best.get((day,item)),
                feed_distance=feed_distance,feed_best=feed_best,
                after_x=after[0][0],after_y=after[0][1])
            self.rows["events"].append(r)
            if effect:
                for item in set(inv)|set(private["inventories"][unit])|set(shed)|set(private["shed"]):
                    bd=private["inventories"][unit].get(item,0)-inv.get(item,0)
                    sd=private["shed"].get(item,0)-shed.get(item,0)
                    if bd or sd:self.rows["flows"].append(self.base(seat,step=self.step,day=day,hour=self.step%24,
                        unit=unit,x=x,y=y,op=op,item=item,bag_delta=bd,shed_delta=sd,bag_before=inv.get(item,0),
                        bag_after=private["inventories"][unit].get(item,0),on_shed=r["on_shed"],units=abs(bd),revenue=0))
                if c:
                    dk=(seat,x,y,c["id"],day)
                    if t.get("kind")=="PLANT":
                        row=self.plant_days.get(dk)
                        if row and op=="WATER":row.update(watered=True,water_hour=self.step%24)
                        if row and op=="FERTILIZE":row["fert_uses"]+=1
                    elif t.get("animal"):
                        row=self.animal_days.get(dk)
                        if row and op in ("FEED","CARE","COLLECT_FERTILIZER"):
                            if op=="FEED":row.update(fed=True,feed_hour=self.step%24,feed_unit=unit,feed_visit=h["visit"])
                            if op=="CARE":row.update(cared=True,care_hour=self.step%24,care_unit=unit,care_visit=h["visit"])
                            if op=="COLLECT_FERTILIZER":row.update(collected=True,collect_hour=self.step%24,first_fert_wait=float(fert_wait) if fert_wait is not None else None)
        if effect and op=="FEED":h["feed_pos"]=(x,y)
        self.cell(seat,x,y,post,self.step,harvest=bool(effect and op=="HARVEST"))
        return result

    def __enter__(self):
        def apply(farm,private,unit,action,*args):
            if not self.active:return NATIVE["_apply_unit_action"](farm,private,unit,action,*args)
            seat=sys._getframe(1).f_locals["i"]
            if seat not in self.cohorts:return NATIVE["_apply_unit_action"](farm,private,unit,action,*args)
            return self.observe(seat,farm,private,unit,action,args)

        def market(states,env):
            if not self.active:return NATIVE["_process_market"](states,env)
            self.farms=states[0].observation.farms
            self.farm_seats={id(f):p for p,f in enumerate(self.farms)}
            self.private_seats={id(s.observation.private):p for p,s in enumerate(states)}
            for seat in self.cohorts:
                farm=states[0].observation.farms[seat];private=states[seat].observation.private
                for unit in range(1+len(farm["hands"])):
                    if (seat,unit) not in self.seen:
                        self.observe(seat,farm,private,unit,["PASS"],(10,self.step//24,24,100),execute=False)
            return NATIVE["_process_market"](states,env)

        def commit(op,item,price,farm,private,market,*args):
            result=NATIVE["_commit_unit"](op,item,price,farm,private,market,*args)
            seat=self.farm_seats.get(id(farm))
            if self.active and result and seat in self.cohorts and item=="FERTILIZER":
                row=self.sales[(seat,op,item,price)];row[0]+=1;row[1]+=price
            return result

        def refresh(farm,day,tpd):
            seat=self.farm_seats.get(id(farm))
            if self.active and seat in self.cohorts:
                for (s,x,y,spell,d),row in self.plant_days.items():
                    if s==seat and d==day:
                        tile=farm["tiles"][y][x];c=self.cells.get((s,x,y))
                        if isinstance(tile,dict) and tile.get("kind")=="PLANT" and c and c["id"]==spell:
                            row.update(at_midnight=True,complete_day=True)
            result=NATIVE["_daily_refresh_plants"](farm,day,tpd)
            if self.active and seat in self.cohorts:
                for (s,x,y),doses in list(self.shadows.items()):
                    if s==seat:
                        for dose in doses:dose["shadow"].refresh(day)
            return result

        def animals(farm,day):
            seat=self.farm_seats.get(id(farm))
            if self.active and seat in self.cohorts:
                for (s,x,y,spell,d),row in self.animal_days.items():
                    if s==seat and d==day:
                        tile=farm["tiles"][y][x];c=self.cells.get((s,x,y))
                        if isinstance(tile,dict) and tile.get("animal") and c and c["id"]==spell:
                            row.update(at_midnight=True,complete_day=True)
            return NATIVE["_daily_refresh_animals"](farm,day)

        def decay(farm,step):
            result=NATIVE["_decay_plants"](farm,step)
            seat=self.farm_seats.get(id(farm))
            if self.active and seat in self.cohorts:
                for (s,x,y),doses in list(self.shadows.items()):
                    if s==seat:
                        for dose in doses:dose["shadow"].decay(step)
            return result

        def drop(private,capacity):
            seat=self.private_seats.get(id(private))
            if not self.active or seat not in self.cohorts:return NATIVE["_drop_inventories_to_shed"](private,capacity)
            before=defaultdict(int)
            for bag in private["inventories"]:
                for item,n in bag.items():before[item]+=n
            shed=private["shed"].copy();result=NATIVE["_drop_inventories_to_shed"](private,capacity)
            if self.recording():
                for item,n in before.items():
                    if n:self.rows["flows"].append(self.base(seat,step=self.step,day=self.step//24,hour=self.step%24,
                        unit=-1,x=None,y=None,op="AUTO_DROP",item=item,bag_delta=-n,
                        shed_delta=private["shed"].get(item,0)-shed.get(item,0),bag_before=n,bag_after=0,
                        on_shed=False,units=n,revenue=0))
            return result

        for name,fn in (("_apply_unit_action",apply),("_process_market",market),("_commit_unit",commit),
                        ("_daily_refresh_plants",refresh),("_daily_refresh_animals",animals),
                        ("_decay_plants",decay),("_drop_inventories_to_shed",drop)):setattr(K,name,fn)
        return self

    def __exit__(self,*args):
        self.active=False
        for name,fn in NATIVE.items():setattr(K,name,fn)

    def finish(self,states,step,reason):
        self.farms=states[0].observation.farms
        for key,doses in list(self.shadows.items()):
            for dose in list(doses):self.finish_dose(key,dose,step,reason)
        self.rows["plant_days"]=list(self.plant_days.values())
        self.rows["animal_days"]=list(self.animal_days.values())

    def save(self,out,receipt):
        out=Path(out)
        for table in TABLES:
            (out/table).mkdir(parents=True,exist_ok=True)
            write_table(out/table/(self.run+".parquet"),self.rows[table])
        receipt.update(rows={t:len(self.rows[t]) for t in TABLES},checks=dict(self.checks))
        (out/"audit").mkdir(exist_ok=True)
        tmp=out/"audit"/(self.run+".tmp");tmp.write_text(json.dumps(receipt,separators=(",",":")))
        tmp.replace(out/"audit"/(self.run+".json"))

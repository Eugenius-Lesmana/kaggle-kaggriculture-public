"""Summarize D2 results, preserving seed pairing and early-shop strata."""
import collections
import csv
import json
from pathlib import Path
import statistics
import sys

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
from kagml.paths import runs
from kagml.opponents import NAMES

root = runs() / (sys.argv[1] if len(sys.argv)>1 else "d2-opponents-2026-10-17")
from audit_opponents import audit
verified = audit(root)
assert verified['accepted'] == 144 and not verified['rejected'], verified['failures']
rows = [json.loads(p.read_text()) for p in root.glob("*.metrics.json")]
keys = {(r["name"], r["control"], r["seed"], r["seat"]) for r in rows}
expected = {(n,c,s,p) for n in NAMES for c in ("metav4","template") for s in range(10301,10313) for p in (0,1)}
assert keys == expected, f"missing={sorted(expected-keys)}, unexpected={sorted(keys-expected)}"
assert len(rows)==144
assert all(r["steps"]==720 and r["statuses"]==["DONE","DONE"] and r["timing"]["turns"]==719 for r in rows)
assert all(not r["diagnostics"]["fallbacks"] for r in rows)
by_seed = collections.defaultdict(set)
for r in rows:
    by_seed[r["seed"]].add(r["buyers"])
assert all(len(v)==1 for v in by_seed.values()), "shops differ between paired games"
out = []
for n in NAMES:
    for control in ("metav4","template"):
        for buyers, seat in ((b,p) for b in ("all",0,1,2) for p in ("all",0,1)):
            group=[r for r in rows if r["name"]==n and r["control"]==control and (buyers=="all" or r["buyers"]==buyers) and (seat=="all" or r["seat"]==seat)]
            if not group:
                continue
            seeds=collections.defaultdict(list)
            for r in group:
                seeds[r["seed"]].append(r["margin"])
            assert all(len(v)==(2 if seat=="all" else 1) for v in seeds.values())
            paired=[statistics.mean(v) for v in seeds.values()]
            out.append({"name":n,"control":control,"buyers":buyers,"seat":seat,"seeds":len(seeds),"games":len(group),
                        "bank":statistics.mean(r["banks"][0] for r in group),
                        "control_bank":statistics.mean(r["banks"][1] for r in group),
                        "margin":statistics.mean(paired),
                        "bank_share":sum(r['banks'][0] for r in group)/sum(r['banks'][1] for r in group),
                        "mean_game_bank_share":statistics.mean(r['banks'][0]/r['banks'][1] for r in group),
                        "margin_seed_se":statistics.stdev(paired)/len(paired)**0.5 if len(paired)>1 else None,
                        "wins":sum(r["win"] for r in group),"ties":sum(r["tie"] for r in group),
                        "paired_seed_wins":sum(m>0 for m in paired)})
with (root/"summary.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(out[0]));writer.writeheader();writer.writerows(out)
(root/"summary.json").write_text(json.dumps(out,indent=2))
daily=[]
for r in rows:
    for day, counts in r["timing"]["daily"].items():
        daily.append({"name":r["name"],"control":r["control"],"seed":r["seed"],"seat":r["seat"],"day":int(day),
                      "turns":counts["turns"],"non_pass":counts.get("non_pass",0),"market_orders":counts.get("market_orders",0)})
with (root/"daily.csv").open("w",newline="") as f:
    writer=csv.DictWriter(f,fieldnames=list(daily[0]));writer.writeheader();writer.writerows(daily)
speed=[]
for n in NAMES:
    group=[r for r in rows if r["name"]==n]
    ms=[t for r in group if not r["exception_tracing"] for t in r["timing"]["turn_ms"]]
    speed.append({"name":n,"turns":len(ms),"median_ms":statistics.median(ms),"max_ms":max(ms),"over_1s_turns":sum(t>1000 for t in ms),
                  "min_game_seconds":min(r["seconds"] for r in group),"max_game_seconds":max(r["seconds"] for r in group),
                  "exception_events":sum(e["events"] for r in group for e in r["exceptions"]),
                  "handled_policy_exceptions":sum(e["events"] for r in group for e in r["exceptions"] if e.get("kind")=="handled" and e["type"] not in ("GeneratorExit","StopIteration","StopAsyncIteration")),
                  "handled_control_flow":sum(e["events"] for r in group for e in r["exceptions"] if e.get("kind")=="handled" and e["type"] in ("GeneratorExit","StopIteration","StopAsyncIteration")),
                  "fallbacks":sum(r["diagnostics"]["fallbacks"] for r in group),
                  "cold_load_seconds":json.loads((root/f"cold-{n}.json").read_text())["load_seconds"]})
(root/"speed.json").write_text(json.dumps(speed,indent=2))
print(json.dumps({"groups":out,"speed":speed},indent=2))

import shutil
for source, target in (("summary.csv","D2_STRENGTH.csv"),("speed.json","D2_TIMING.json"),("verification.json","D2_VERIFICATION.json")):
    if source == 'verification.json':
        (REPO/'reports'/target).write_text(json.dumps({k:v for k,v in verified.items() if k not in ('games','failures')},indent=2))
    else: shutil.copyfile(root/source, REPO/'reports'/target)

paired_rows=[]
for n in NAMES:
    for control in ('metav4','template'):
        for seed in range(10301,10313):
            pair=sorted((r for r in rows if (r['name'],r['control'],r['seed'])==(n,control,seed)),key=lambda r:r['seat'])
            assert [r['seat'] for r in pair]==[0,1]
            paired_rows.append({'name':n,'control':control,'seed':seed,'buyers':pair[0]['buyers'],
                **{f'{key}_seat{r["seat"]}':value for r in pair for key,value in
                   (('bank',r['banks'][0]),('control_bank',r['banks'][1]),('margin',r['margin']),('win',r['win']))},
                'paired_margin':statistics.mean(r['margin'] for r in pair),
                'paired_bank_share':sum(r['banks'][0] for r in pair)/sum(r['banks'][1] for r in pair)})
with (REPO/'reports/D2_PAIRED.csv').open('w',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(paired_rows[0]));writer.writeheader();writer.writerows(paired_rows)

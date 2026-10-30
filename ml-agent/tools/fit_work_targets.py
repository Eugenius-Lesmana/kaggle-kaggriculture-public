"""W1 held-out descriptive rules, fitted without coordinates, identity or future prices."""
import argparse
import hashlib
import os
import itertools
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kagml.paths import data_root
os.environ["OMP_NUM_THREADS"]="1"
os.environ["MKL_NUM_THREADS"]="1"
os.environ["OPENBLAS_NUM_THREADS"]="1"
import duckdb
import numpy as np
import pandas as pd
from sklearn.tree import DecisionTreeClassifier,export_text
from sklearn.metrics import balanced_accuracy_score,precision_score,recall_score,f1_score

ROOT=data_root()/"runs/work-targets-2026-10-18"
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument("--cohorts",nargs="+",choices=("reference","second","template","fourth"),default=["reference","second","template","fourth"])
ap.add_argument("--tag",default="rules")
ap.add_argument("--threads",type=int,choices=(1,2),default=2)
ARGS=ap.parse_args()
db=duckdb.connect(config={"threads":ARGS.threads,"memory_limit":"4GB"})
path=str(ROOT/"events/*.parquet").replace("'","''")
db.execute(f"CREATE VIEW e AS SELECT *,6*(day//6) band FROM read_parquet('{path}',union_by_name=true)")
path=str(ROOT/"plant_days/*.parquet").replace("'","''")
db.execute(f"CREATE VIEW p AS SELECT *,6*(day//6) band FROM read_parquet('{path}',union_by_name=true)")


def test_game(game):
    return int.from_bytes(hashlib.sha256(str(game).encode()).digest()[:8],"big")%5==0


def scores(y,pred):
    if not len(y):return None
    y=np.asarray(y);pred=np.asarray(pred)
    return dict(n=int(len(y)),positive=int(y.sum()),base_rate=float(y.mean()),
        balanced_accuracy=float(balanced_accuracy_score(y,pred)),
        precision=float(precision_score(y,pred,zero_division=0)),
        recall=float(recall_score(y,pred,zero_division=0)),f1=float(f1_score(y,pred,zero_division=0)))


def split(df):
    return df["game"].astype(str).map(test_game).to_numpy()


def tree(name,cohort,query,features):
    df=db.execute(query,[cohort]).fetchdf()
    if df.empty:return None
    df["test"]=split(df)
    numeric=df[features].copy()
    for col in ("crop","animal"):
        if col in features:numeric[col]=numeric[col].fillna("NONE")
    X=pd.get_dummies(numeric,columns=[c for c in ("crop","animal") if c in features],dtype=np.float32)
    X=X.fillna(-1).astype(np.float32)
    y=df["target"].astype(int).to_numpy();test=df["test"].to_numpy()
    if not test.any() or test.all():return dict(habit=name,cohort=cohort,reason="no whole-game test split")
    min_leaf=max(10,min(500,int((~test).sum()*.002)))
    model=DecisionTreeClassifier(max_depth=3,min_samples_leaf=min_leaf,class_weight="balanced",random_state=10301)
    model.fit(X.loc[~test],y[~test]);pred=model.predict(X.loc[test])
    result=dict(habit=name,cohort=cohort,train_rows=int((~test).sum()),
        test_games=int(df.loc[test,"game"].nunique()),scores=scores(y[test],pred),
        tree=export_text(model,feature_names=list(X.columns),decimals=2),
        important_features=sorted([(c,float(v)) for c,v in zip(X.columns,model.feature_importances_) if v],
                                  key=lambda p:-p[1]))
    df.loc[test,"prediction"]=pred
    result["by_stratum"]=[]
    for (buyers,band),g in df.loc[test].groupby(["buyers","band"]):
        result["by_stratum"].append(dict(buyers=int(buyers),band=int(band),
            games=int(g["game"].nunique()),**scores(g["target"].astype(int),g["prediction"].astype(int))))
    return result


def priority(cohort):
    df=db.execute("""SELECT game,buyers,band,fed,cared,fert_available,wheat,ratio,
       CASE WHEN effective AND op='FEED' THEN 0 WHEN effective AND op='CARE' THEN 1
            WHEN effective AND op='COLLECT_FERTILIZER' THEN 2
            WHEN effective AND op='HARVEST' THEN 3 ELSE 4 END AS "target"
       FROM e WHERE cohort=? AND animal IS NOT NULL""",[cohort]).fetchdf()
    if df.empty:return None
    test=split(df);y=df.target.to_numpy(dtype=int)
    def metric(actual,pred):
        cm=np.bincount(actual*5+pred,minlength=25).reshape(5,5)
        n=cm.sum(axis=1);valid=n>0
        return float(np.mean(np.diag(cm)[valid]/n[valid])),float(np.trace(cm)/cm.sum())
    best=None
    for threshold in (1/6,.25,1/3,.5,2/3,.75,1.0):
        eligible=np.column_stack((~df.fed & (df.wheat>0),~df.cared,df.fert_available,df.ratio>=threshold))
        for order in itertools.permutations(range(4)):
            pred=np.full(len(df),4,dtype=int)
            for op in reversed(order):pred[np.asarray(eligible[:,op],dtype=bool)]=op
            train=metric(y[~test],pred[~test])[0]
            if best is None or train>best[0]:best=(train,order,threshold,pred)
    _,order,threshold,pred=best
    macro,accuracy=metric(y[test],pred[test])
    names=("FEED","CARE","COLLECT_FERTILIZER","HARVEST")
    result=dict(habit="animal_priority",cohort=cohort,priority=[names[i] for i in order],
        harvest_cap_threshold=threshold,test_rows=int(test.sum()),test_games=int(df.loc[test,"game"].nunique()),
        balanced_accuracy=macro,accuracy=accuracy,
        majority_accuracy=float(np.max(np.bincount(y[test],minlength=5))/test.sum()),by_stratum=[])
    for (buyers,band),g in df.loc[test].groupby(["buyers","band"]):
        index=g.index.to_numpy();macro,accuracy=metric(y[index],pred[index])
        result["by_stratum"].append(dict(buyers=int(buyers),band=int(band),n=len(index),
                                        balanced_accuracy=macro,accuracy=accuracy))
    return result


def main():
    results=[]
    base=["hour","age","ratio","bag_total","wheat","fert","watered","fed","cared",
          "fert_available","fert_left","due","risk","near_ready","wait_mean","first_fert_wait","production_in_3days","crop","animal"]
    common="""SELECT game,buyers,band,day,hour,age,ratio,bag_total,wheat,fert,watered,fed,cared,
       fert_available,fert_until-day AS fert_left,
       CASE WHEN animal='GOOSE' THEN age+1>=4
            WHEN animal='COW' THEN age+1>=8 AND (age+1-8)%2=0
            WHEN animal='SHEEP' THEN age+1>=6 AND (age+1-6)%3=0 ELSE due END AS due,
       risk,near_ready,wait_mean,first_fert_wait,
       crop,animal,
       CASE crop WHEN 'WHEAT' THEN age BETWEEN 0 AND 4 WHEN 'CARROT' THEN age BETWEEN 0 AND 3
          WHEN 'MELON' THEN age BETWEEN 4 AND 12 WHEN 'TOMATO' THEN age BETWEEN 5 AND 10
          WHEN 'STRAWBERRY' THEN age BETWEEN 7 AND 15 ELSE FALSE END AS production_in_3days,
       price::DOUBLE/nullif(best_so_far,0) price_prefix_ratio,
       (effective AND op='{op}')::INTEGER AS "target" FROM e WHERE cohort=? AND {eligible}"""
    cases=[
      ("harvest","HARVEST","yield_before>0 AND (animal IS NOT NULL OR age>=CASE crop WHEN 'WHEAT' THEN 2 WHEN 'CARROT' THEN 2 WHEN 'MELON' THEN 10 WHEN 'TOMATO' THEN 8 WHEN 'STRAWBERRY' THEN 10 ELSE 999 END)",base+["price_prefix_ratio"]),
      ("fertilizer_collection","COLLECT_FERTILIZER","animal IS NOT NULL AND fert_available",base),
      ("fertilizer_use","FERTILIZE","crop IS NOT NULL AND fert>0",base)]
    for cohort in ARGS.cohorts:
        for name,op,eligible,features in cases:
            r=tree(name,cohort,common.format(op=op,eligible=eligible),features)
            if r:results.append(r)
        r=tree("day_phase",cohort,"""SELECT game,buyers,band,day,hour,
           (animal IS NOT NULL)::INTEGER AS "target" FROM e WHERE cohort=? AND effective AND
           op IN ('WATER','FERTILIZE','PLANT','HARVEST','FEED','CARE','COLLECT_FERTILIZER')""",["hour","day"])
        if r:results.append(r)
        r=tree("watering",cohort,"""SELECT game,buyers,band,day,crop,age,due,risk,first_hour,
           watered::INTEGER AS "target" FROM p WHERE cohort=? AND at_midnight AND complete_day""",
           ["day","crop","age","due","risk","first_hour"])
        if r:results.append(r)
        r=priority(cohort)
        if r:results.append(r)
    (ROOT/(ARGS.tag+".json")).write_text(json.dumps({"split":"SHA256(game) modulo 5; whole games held out",
        "scope":"descriptive local-opportunity/day rules, not an inferred hidden policy or recommended agent",
        "rules":results},indent=2))
    print(json.dumps([{k:v for k,v in r.items() if k not in ("tree","by_stratum")} for r in results],indent=2))


if __name__=="__main__":main()

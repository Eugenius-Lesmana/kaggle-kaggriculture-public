"""Aggregate W1 measurements; all generated tables remain on D:."""
import argparse
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from kagml.paths import data_root
import duckdb

ROOT=data_root()/"runs/work-targets-2026-10-18"
ap=argparse.ArgumentParser(description=__doc__)
ap.add_argument("--cohorts",nargs="+",choices=("reference","second","template","fourth"),default=["reference","second","template","fourth"])
ap.add_argument("--limit-shards",type=int)
ap.add_argument("--threads",type=int,choices=(1,2),default=2)
ARGS=ap.parse_args()
DEST=ROOT/("smoke" if ARGS.limit_shards else "")
DEST.mkdir(exist_ok=True)
db=duckdb.connect(config={"threads":ARGS.threads,"memory_limit":"5GB","temp_directory":str(ROOT/"tmp")})


def table(name,query):
    frame=db.sql(query).df()
    frame.to_csv(DEST/(name+".csv"),index=False)
    return frame


def main():
    chosen={p.stem for p in sorted((ROOT/"events").glob("*.parquet"))[:ARGS.limit_shards]} if ARGS.limit_shards else None
    for name,alias in (("events","e"),("doses","doses"),("plant_days","pd"),
                       ("animal_days","ad"),("flows","f"),("markets","m")):
        path=str(ROOT/name/"*.parquet").replace("'","''")
        source="'"+path+"'" if chosen is None else "["+",".join("'"+str(p).replace("'","''")+"'" for p in sorted((ROOT/name).glob("*.parquet")) if p.stem in chosen)+"]"
        selected=",".join("'"+c+"'" for c in ARGS.cohorts)
        where="" if name=="markets" else f" WHERE cohort IN ({selected})"
        db.execute(f"CREATE VIEW {alias} AS SELECT * FROM read_parquet({source},union_by_name=true){where}")
    db.execute("CREATE TABLE deposits AS SELECT DISTINCT run,seat,step,unit FROM f WHERE op='PLACE' AND shed_delta>0")
    db.execute("""CREATE VIEW events AS SELECT e.*,d.unit IS NOT NULL AS place_deposit,6*(day//6) AS band,
       CASE WHEN effective AND op IN ('NORTH','SOUTH','EAST','WEST') THEN 'walk'
            WHEN effective AND op!='PASS' THEN 'work' ELSE 'idle' END AS activity,
       effective AND op IN ('PLANT','WATER','HARVEST','FERTILIZE','FEED','CARE','COLLECT_FERTILIZER',
                           'DIG','BUILD_COOP','BUILD_PASTURE') AS service,
       effective AND animal IS NOT NULL AND op IN ('FEED','CARE','COLLECT_FERTILIZER','HARVEST') AS animal_job,
       effective AND ((on_shed AND op IN ('PICKUP','DROP','PLACE')) OR
          op IN ('PLANT','WATER','FERTILIZE','DIG','BUILD_COOP','BUILD_PASTURE') OR
          (op='HARVEST' AND crop IS NOT NULL)) AS round_break
       FROM e LEFT JOIN deposits d USING(run,seat,step,unit)""")
    db.execute("""CREATE TABLE worker_days AS SELECT run,game,cohort,buyers,band,day,seat,unit,
       count(*) turns,count_if(activity='walk') walking,count_if(activity='work') working,
       count_if(activity='idle') idle,
       count(DISTINCT (x,y)) FILTER(WHERE service) cells,
       max(x) FILTER(WHERE service)-min(x) FILTER(WHERE service)+1 span_x,
       max(y) FILTER(WHERE service)-min(y) FILTER(WHERE service)+1 span_y,
       count_if(NOT on_shed AND (after_x,after_y) IN ((4,4),(4,5),(5,4),(5,5))) shed_returns,
       count_if(effective AND op='PICKUP') pickups,
       count_if(effective AND (op='DROP' OR (op='PLACE' AND place_deposit)) AND on_shed) shed_deposits,
       first(on_shed ORDER BY step)::INTEGER initial_shed,
       min(hour) FILTER(WHERE animal_job) first_animal,max(hour) FILTER(WHERE animal_job) last_animal,
       min(hour) FILTER(WHERE service AND NOT animal_job) first_crop,
       min(hour) FILTER(WHERE effective AND op='WATER') first_water,
       count_if(effective AND op='HARVEST') harvests,
       count_if(effective AND op='FERTILIZE') fertilizes,
       count_if(effective AND op='COLLECT_FERTILIZER') collects
       FROM events GROUP BY ALL""")
    table("day_shape","""SELECT cohort,buyers,band,count(DISTINCT game) games,count(*) worker_days,
       sum(turns) worker_turns,avg(turns) mean_available_turns,
       100.0*avg(walking::DOUBLE/turns) walk_workerday_pct,
       100.0*avg(working::DOUBLE/turns) work_workerday_pct,
       100.0*avg(idle::DOUBLE/turns) idle_workerday_pct,
       100.0*sum(walking)/sum(turns) walk_pct,
       100.0*sum(working)/sum(turns) work_pct,100.0*sum(idle)/sum(turns) idle_pct,
       avg(cells) cells_per_worker_day,median(cells) cells_median,
       avg(shed_returns) shed_returns,avg(shed_returns+initial_shed) shed_visits,avg(pickups) pickups,avg(shed_deposits) deposits,
       avg(harvests) harvests,avg(fertilizes) fertilizes,avg(collects) collects,
       100.0*avg((first_animal<first_crop)::INTEGER) FILTER(WHERE first_animal IS NOT NULL AND first_crop IS NOT NULL) animal_first_pct,
       100.0*avg((last_animal<first_water)::INTEGER) FILTER(WHERE last_animal IS NOT NULL AND first_water IS NOT NULL) animal_before_water_pct,
       100.0*avg((span_x<=3 AND span_y<=3)::INTEGER) FILTER(WHERE cells>0) footprint_3x3_pct
       FROM worker_days GROUP BY ALL ORDER BY cohort,buyers,band""")
    table("jobs","""WITH n AS(SELECT cohort,buyers,band,count(*) wd,sum(turns) worker_turns FROM worker_days GROUP BY ALL)
       SELECT e.cohort,e.buyers,e.band,e.op,count(*) jobs,count(*)::DOUBLE/n.wd per_worker_day,count(*)::DOUBLE/n.worker_turns*24 per_24_worker_turns,
       median(e.hour) median_hour,quantile_cont(e.hour,.1) p10_hour,quantile_cont(e.hour,.9) p90_hour
       FROM events e JOIN n USING(cohort,buyers,band) WHERE e.effective AND e.op NOT IN ('NORTH','SOUTH','EAST','WEST','PASS')
       GROUP BY e.cohort,e.buyers,e.band,e.op,n.wd,n.worker_turns ORDER BY e.cohort,e.buyers,e.band,e.op""")
    table("hourly","""SELECT cohort,buyers,band,hour,count(*) turns,
       count_if(activity='walk') walking,count_if(activity='work') working,count_if(activity='idle') idle,
       count_if(animal_job) animal_jobs,count_if(service AND NOT animal_job) crop_jobs
       FROM events GROUP BY ALL ORDER BY cohort,buyers,band,hour""")
    db.execute("""CREATE TABLE route_cells AS SELECT DISTINCT run,seat,day,unit,trip,x,y FROM events WHERE service""")
    db.execute("""CREATE TABLE harvests AS SELECT e.*,b.day_best,
       e.price::DOUBLE/b.day_best harvest_price_ratio,
       count(r.x) FILTER(WHERE abs(r.x-e.x)+abs(r.y-e.y) BETWEEN 1 AND 2) nearby_services
       FROM events e JOIN(SELECT run,day,item,max(price) day_best FROM m GROUP BY ALL)b USING(run,day,item)
       LEFT JOIN route_cells r ON e.run=r.run AND e.seat=r.seat AND e.day=r.day AND e.unit=r.unit AND e.trip=r.trip
       WHERE e.op='HARVEST' AND e.effective GROUP BY ALL""")
    for product,name in (("", "harvest"),(",item","harvest_product")):
        table(name,f"""SELECT cohort,buyers,band{product},count(*) harvests,
           avg(yield_before) mean_units,median(yield_before) median_units,
           100.0*avg((yield_before>=cap)::INTEGER) cap_full_pct,avg(ratio) cap_fraction,
           median(first_ready_wait) FILTER(WHERE queue_clean) oldest_wait_median,
           sum(wait_mean*yield_before) FILTER(WHERE queue_clean)/nullif(sum(yield_before) FILTER(WHERE queue_clean),0) unit_wait_mean,
           100.0*avg(queue_clean::INTEGER) clean_wait_pct,
           avg(harvest_price_ratio) price_to_day_best,
           100.0*avg((harvest_price_ratio>=.95)::INTEGER) within_5pct_best,
           100.0*avg((nearby_services>0)::INTEGER) nearby_route_pct,
           median(hour) median_hour
           FROM harvests GROUP BY ALL ORDER BY cohort,buyers,band{product}""")
    table("fertilizer","""WITH doses_by AS(SELECT cohort,buyers,6*(day//6) band,
       count(*) uses,count_if(complete) complete_72_or_ended,count_if(censored) censored,
       100.0*avg(watered_before::INTEGER) already_watered_pct,
       100.0*avg(watered_apply_day::INTEGER) watered_same_day_pct,
       avg(marginal_harvest) FILTER(WHERE complete) marginal_harvest_72,
       avg(marginal_held) FILTER(WHERE complete) marginal_held_72,
       100.0*avg((marginal_harvest=0 AND marginal_held=0)::INTEGER) FILTER(WHERE complete) zero_marginal_pct
       FROM doses GROUP BY ALL),
       collected AS(SELECT cohort,buyers,band,count(*) collections,median(first_fert_wait) wait_median,
          avg(first_fert_wait) wait_mean,median(fert) carried_before,quantile_cont(fert,.9) carried_p90
          FROM events WHERE op='COLLECT_FERTILIZER' AND effective GROUP BY ALL),
       stock AS(SELECT cohort,buyers,6*(day//6) band,
          sum(units) FILTER(WHERE op='SELL') sold,sum(units) FILTER(WHERE op='BUY_PRODUCT') bought,
          sum(-bag_delta-shed_delta) FILTER(WHERE op='AUTO_DROP') lost_auto,
          sum(shed_delta) FILTER(WHERE op='AUTO_DROP') auto_deposited
          FROM f WHERE item='FERTILIZER' GROUP BY ALL),
       served AS(SELECT cohort,buyers,6*(day//6) band,count(*) animal_days,
          100.0*avg(collected::INTEGER) collected_day_pct FROM ad GROUP BY ALL)
       SELECT * FROM doses_by FULL JOIN collected USING(cohort,buyers,band)
       FULL JOIN stock USING(cohort,buyers,band) FULL JOIN served USING(cohort,buyers,band)
       ORDER BY cohort,buyers,band""")
    table("fertilizer_carry","""SELECT cohort,buyers,band,op,count(*) jobs,
       avg(fert) carried_before_mean,median(fert) carried_before_median,
       quantile_cont(fert,.9) carried_before_p90,max(fert) carried_before_max,
       median(hour) median_hour FROM events WHERE effective AND op IN ('FERTILIZE','COLLECT_FERTILIZER')
       GROUP BY ALL ORDER BY cohort,buyers,band,op""")
    table("fertilizer_crop_age","""SELECT cohort,buyers,6*(day//6) band,crop,age,count(*) applications,
       100.0*avg(watered_before::INTEGER) already_watered_pct,
       100.0*avg(watered_apply_day::INTEGER) watered_apply_day_pct,
       count_if(complete) complete,count_if(censored) censored,
       avg(marginal_harvest) FILTER(WHERE complete) marginal_harvest_72,
       avg(marginal_held) FILTER(WHERE complete) marginal_held_72,
       100.0*avg((marginal_harvest=0 AND marginal_held=0)::INTEGER) FILTER(WHERE complete) zero_marginal_pct
       FROM doses GROUP BY ALL ORDER BY cohort,buyers,band,crop,age""")
    table("watering","""SELECT cohort,buyers,6*(day//6) band,count(*) plant_days,
       100.0*avg(watered::INTEGER) all_exposed_watered_pct,
       count_if(at_midnight AND complete_day) continuing_complete,
       100.0*avg(watered::INTEGER) FILTER(WHERE at_midnight AND complete_day) continuing_watered_pct,
       100.0*avg(watered::INTEGER) FILTER(WHERE at_midnight AND complete_day AND due) due_watered_pct,
       100.0*avg(watered::INTEGER) FILTER(WHERE at_midnight AND complete_day AND NOT due) not_due_watered_pct,
       median(water_hour) median_water_hour,quantile_cont(water_hour,.1) p10_water_hour,
       quantile_cont(water_hour,.9) p90_water_hour
       FROM pd GROUP BY ALL ORDER BY cohort,buyers,band""")
    table("watering_crop_age","""SELECT cohort,buyers,6*(day//6) band,crop,age,due,risk,
       count(*) plant_days,100.0*avg(watered::INTEGER) all_exposed_watered_pct,
       count_if(at_midnight AND complete_day) continuing_complete,
       100.0*avg(watered::INTEGER) FILTER(WHERE at_midnight AND complete_day) continuing_watered_pct,
       median(water_hour) median_water_hour FROM pd GROUP BY ALL ORDER BY cohort,buyers,band,crop,age""")
    table("animal_service","""SELECT cohort,buyers,6*(day//6) band,count(*) animal_days,
       100.0*avg(fed::INTEGER) fed_pct,100.0*avg(cared::INTEGER) cared_pct,
       100.0*avg((fed AND cared)::INTEGER) both_pct,
       100.0*avg((feed_unit=care_unit AND feed_visit=care_visit)::INTEGER) FILTER(WHERE fed AND cared) same_visit_pct,
       100.0*avg((feed_unit!=care_unit)::INTEGER) FILTER(WHERE fed AND cared) different_worker_pct,
       100.0*avg((feed_hour<care_hour OR (feed_hour=care_hour AND feed_unit<care_unit))::INTEGER)
          FILTER(WHERE fed AND cared) feed_before_care_pct,
       median(feed_hour) feed_hour,median(care_hour) care_hour,median(collect_hour) collect_hour
       FROM ad GROUP BY ALL ORDER BY cohort,buyers,band""")
    # A round is consecutive animal work, separated by crop/shed work or unexplained gaps.
    db.execute("""CREATE TABLE sequence AS WITH prev AS(
       SELECT run,game,cohort,buyers,band,seat,day,unit,step,hour,x,y,wheat,op,effective,
       animal_job,round_break,feed_distance,feed_best,
       max(step) FILTER(WHERE animal_job) OVER w prev_animal,
       last_value(CASE WHEN animal_job THEN x END IGNORE NULLS) OVER w prev_x,
       last_value(CASE WHEN animal_job THEN y END IGNORE NULLS) OVER w prev_y,
       max(step) FILTER(WHERE round_break) OVER w last_break
       FROM events WHERE animal_job OR round_break WINDOW w AS(PARTITION BY run,seat,day,unit ORDER BY step ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING)),
       starts AS(SELECT *,CASE WHEN animal_job AND(prev_animal IS NULL OR last_break>prev_animal OR
           step-prev_animal>abs(x-prev_x)+abs(y-prev_y)+3) THEN 1 ELSE 0 END new_round FROM prev)
       SELECT *,sum(new_round) OVER(PARTITION BY run,seat,day,unit ORDER BY step) round_id FROM starts""")
    db.execute("""CREATE TABLE rounds AS SELECT run,game,cohort,buyers,band,seat,day,unit,round_id,
       min(step) start_step,max(step) end_step,min(hour) start_hour,
       count(DISTINCT (x,y)) animals,count(*) jobs,first(wheat ORDER BY step) wheat_at_start,
       count_if(op='FEED') feeds,count_if(op='CARE') cares,count_if(op='COLLECT_FERTILIZER') collections
       FROM sequence WHERE animal_job GROUP BY ALL""")
    table("animal_rounds","""WITH prior AS(SELECT *,lag(end_step,1,-1) OVER(PARTITION BY run,seat,day,unit ORDER BY start_step) prior_end FROM rounds),
       pickup AS(SELECT r.run,r.seat,r.day,r.unit,r.round_id,coalesce(sum(f.bag_delta),0) wheat_pickup
         FROM prior r LEFT JOIN f ON f.run=r.run AND f.seat=r.seat AND f.day=r.day AND f.unit=r.unit AND
         f.op='PICKUP' AND f.item='WHEAT' AND f.step<r.start_step AND f.step>r.prior_end GROUP BY ALL)
       SELECT r.cohort,r.buyers,r.band,count(*) rounds,avg(r.animals) animals_per_round,
       median(r.animals) animals_median,quantile_cont(r.animals,.9) animals_p90,
       avg(r.wheat_at_start) wheat_at_start,avg(p.wheat_pickup) wheat_picked_before,
       100.0*avg((p.wheat_pickup>0)::INTEGER) fresh_pickup_pct,
       avg(r.wheat_at_start) FILTER(WHERE r.feeds>0) feeding_wheat_at_start,
       avg(p.wheat_pickup) FILTER(WHERE r.feeds>0) feeding_wheat_picked_before,
       100.0*avg((p.wheat_pickup>0)::INTEGER) FILTER(WHERE r.feeds>0) feeding_fresh_pickup_pct,
       median(start_hour) start_hour,
       avg(r.jobs) jobs_per_round FROM rounds r JOIN pickup p USING(run,seat,day,unit,round_id)
       GROUP BY ALL ORDER BY cohort,buyers,band""")
    table("animal_nearest","""WITH feeds AS(SELECT *,row_number() OVER(PARTITION BY run,seat,day,unit,round_id ORDER BY step) n
       FROM sequence WHERE effective AND op='FEED')
       SELECT cohort,buyers,band,count(*) transitions,
       100.0*avg((feed_distance=feed_best)::INTEGER) nearest_unfed_pct,
       avg(feed_distance) distance FROM feeds WHERE n>1 AND feed_best IS NOT NULL
       GROUP BY ALL ORDER BY cohort,buyers,band""")
    table("animal_route_order","""SELECT cohort,buyers,band,count(*) cell_transitions,
       100.0*avg((x=prev_x)::INTEGER) same_column_pct,
       100.0*avg((y=prev_y)::INTEGER) same_row_pct,
       100.0*avg((abs(x-prev_x)+abs(y-prev_y)=1)::INTEGER) adjacent_pct,
       100.0*avg((x>prev_x)::INTEGER) east_pct,100.0*avg((y>prev_y)::INTEGER) south_pct,
       avg(abs(x-prev_x)+abs(y-prev_y)) distance
       FROM sequence WHERE animal_job AND new_round=0 AND (x!=prev_x OR y!=prev_y)
       GROUP BY ALL ORDER BY cohort,buyers,band""")
    table("animal_visit_order","""WITH visits AS(SELECT cohort,buyers,band,run,seat,day,unit,visit,
       string_agg(op,'>' ORDER BY step) pattern FROM events WHERE animal_job GROUP BY ALL)
       SELECT cohort,buyers,band,pattern,count(*) visits FROM visits GROUP BY ALL
       ORDER BY cohort,buyers,band,visits DESC""")
    table("shed_goods","""SELECT cohort,buyers,6*(day//6) band,op,item,count(*) operations,
       sum(bag_delta) bag_delta,sum(shed_delta) shed_delta,
       sum(units) units FROM f WHERE op='AUTO_DROP' OR (on_shed AND op IN ('PICKUP','DROP','PLACE') AND (shed_delta!=0 OR op='DROP'))
       GROUP BY ALL ORDER BY cohort,buyers,band,op,item""")
    # Compact independent QA at each analysis grain.
    audit={"activity_partition":db.sql("SELECT count(*) FROM worker_days WHERE walking+working+idle!=turns").fetchone()[0],
           "duplicate_worker_turns":db.sql("SELECT count(*) FROM(SELECT run,seat,step,unit,count(*) n FROM events GROUP BY ALL HAVING n!=1)").fetchone()[0],
           "fertilizer_gain_above_three":db.sql("SELECT count(*) FROM doses WHERE marginal_harvest+marginal_held>3").fetchone()[0],
           "ended_crop_still_held":db.sql("SELECT count(*) FROM doses WHERE reason IN ('harvested','dug','removed','replaced') AND marginal_held!=0").fetchone()[0],
           "negative_fertilizer_marginal":db.sql("SELECT count(*) FROM doses WHERE marginal_harvest<0 OR marginal_held<0").fetchone()[0],
           "water_hour_without_water":db.sql("SELECT count(*) FROM pd WHERE water_hour IS NOT NULL AND NOT watered").fetchone()[0],
           "harvest_cap_violations":db.sql("SELECT count(*) FROM harvests WHERE yield_before>cap OR yield_before<=0").fetchone()[0]}
    (DEST/"analysis_checks.json").write_text(json.dumps(audit,indent=2))
    assert not any(audit.values()),audit
    print(json.dumps({"tables_written":True,"checks":audit},indent=2))


if __name__=="__main__":main()

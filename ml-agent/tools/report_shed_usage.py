"""S summaries and descriptive decision tables. Large per-decision CSVs stay on D:."""
from collections import Counter,defaultdict
import csv
import gzip
import json
from pathlib import Path
import statistics
import duckdb
import pyarrow as pa
from shed_usage import OUT,REPO,DATA,TOOLS,cases,key,signature,sha,digest,context

SOURCES=('ALL','L1','L3','L3h4','L3h8','L3h12','L3h16')


def select(rows,source):
    return [r for r in rows if source=='ALL' or (r['source']=='L3' and source.startswith('L3h') and r['H']==int(source[3:])) or r['source']==source]


def mean(xs):return statistics.mean(xs) if xs else None

def median(xs):return statistics.median(xs) if xs else None


def p90(xs):return statistics.quantiles(xs,n=10,method='inclusive')[-1] if len(xs)>1 else xs[0] if xs else None


def table(path,rows):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def large_table(path,rows):
    fields=['source','game','day','H','episode','step','hour','unit','event_id']
    fields+=sorted(set().union(*(r.keys() for r in rows))-set(fields))
    with gzip.open(path,'wt',newline='',encoding='utf8',compresslevel=1) as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for row in rows:w.writerow({k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in row.items()})


def need_bin(r):
    if r['amount']==0:return 'zero actual pickup'
    n=r['uncovered_jobs']
    return '0 uncovered' if n==0 else '1-3 uncovered' if n<=3 else '4-7 uncovered' if n<=7 else '8+ uncovered'


def main():
    expected=cases();assert len(expected)==2185 and len({key(m) for m in expected})==2185
    assert {(m['source'],m['game'],m['day'],m['H']) for m in expected}=={(s,g,d,h) for s,hs in [('L1',(0,)),('L3',(4,8,12,16))] for g in range(10301,10320) for d in range(6,29) for h in hs}
    receipts=[];events=[];keeps=[];sig=signature()
    assert {p.name.removesuffix('.metrics.json') for p in (OUT/'cases').glob('*.metrics.json')}=={key(m) for m in expected}
    for m in expected:
        path=OUT/'cases'/key(m);r=json.loads(Path(str(path)+'.metrics.json').read_text());packed=Path(str(path)+'.json.gz')
        assert r['signature']==sig and r['raw_sha256']==m['raw_sha256'] and r['native_check']['reason']=='kept'
        assert r['teacher_start']==m['cutoff'] and r['teacher_end']==m['end'] and sha(packed)==r['output_sha256']
        with gzip.open(packed,'rt',encoding='utf8') as f:data=json.load(f)
        assert digest(data)==r['payload_sha256']
        assert len(data['events'])==r['item_rows'] and len(data['keeps'])==r['keep_rows']
        assert len({x['event_id'] for x in data['events']})==r['shed_commands']
        assert all(m['cutoff']<=x['step']<m['end'] for x in data['events']+data['keeps'])
        # Preserve both the decision-time view and actual sequential execution context.
        raw=DATA/m['file'];assert sha(raw)==m['raw_sha256']
        with gzip.open(raw,'rt',encoding='utf8') as f:rep=json.load(f)
        start=m['day']*24;contexts={}
        for item_row in data['events']+data['keeps']:
            pair=(item_row['step'],item_row['unit'])
            obs=rep['steps'][item_row['step']-start][0]['observation'];item=item_row['item']
            if pair not in contexts:contexts[pair]=context(obs['farms'][0],obs['private'],item_row['unit'],obs['day'])
            pre=contexts[pair];needed=pre['needs'].get(item,0);other=pre['other_qty'].get(item,0)
            item_row.update(pre_turn_open_jobs=needed,pre_turn_legal_jobs=pre['fert_legal'] if item=='FERTILIZER' else needed,
                pre_turn_other_carried=other,pre_turn_other_workers_carrying=pre['other_workers'].get(item,0),
                pre_turn_uncovered_jobs=max(0,needed-other),pre_turn_shed_available=obs['private']['shed'].get(item,0))
        receipts.append(r);events.extend(data['events']);keeps.extend(data['keeps'])
    assert sum(r['teacher_turns'] for r in receipts)==34960
    large_table(OUT/'shed_events.csv.gz',events);large_table(OUT/'tool_keep_decisions.csv.gz',keeps)
    counts=[];summary=[];rules=[];following=[];keep_rules=[];quantities=[]
    for source in SOURCES:
        rs=select(receipts,source);es=select(events,source);ks=select(keeps,source)
        commands=defaultdict(list)
        for e in es:commands[e['event_id']].append(e)
        op_count=Counter(rows[0]['op'] for rows in commands.values())
        counts.append(dict(source=source,cases=len(rs),teacher_turns=sum(r['teacher_turns'] for r in rs),unit_rows=sum(r['unit_rows'] for r in rs),
            shed_commands=len(commands),item_rows=len(es),keep_rows=len(ks),pickups=op_count['PICKUP'],drops=op_count['DROP'],shed_places=op_count['PLACE'],
            zero_unit_commands=sum(sum(e['amount'] for e in rows)==0 for rows in commands.values()),discarded_units=sum(e['discarded'] for e in es),
            implicit_passes=sum(r['implicit_passes'] for r in rs)))
        groups=defaultdict(list)
        for e in es:groups[e['op'],e['item']].append(e)
        for (op,item),rows in groups.items():
            summary.append(dict(source=source,op=op,item=item,commands=len(rows),actual_units=sum(r['amount'] for r in rows),
                mean_amount=mean([r['amount'] for r in rows]),median_amount=median([r['amount'] for r in rows]),
                mean_carried_before=mean([r['carried_before'] for r in rows]),mean_open_jobs=mean([r['open_jobs'] for r in rows]),
                mean_legal_jobs=mean([r['legal_jobs'] for r in rows]),mean_other_workers_carrying=mean([r['other_workers_carrying'] for r in rows]),
                mean_other_carried=mean([r['other_carried'] for r in rows]),mean_hour=mean([r['hour'] for r in rows])))
        picks=[e for e in es if e['op']=='PICKUP'];byitem=defaultdict(list)
        for r in picks:byitem[r['item']].append(r)
        for item,items in byitem.items():
            for amount in sorted({r['amount'] for r in items}):
                rs=[r for r in items if r['amount']==amount]
                quantities.append(dict(source=source,item=item,amount=amount,commands=len(rs),share_item_pickups=len(rs)/len(items),
                    mean_requested=mean([r['requested'] for r in rs]),stock_clipped=sum(r['amount']<r['requested'] for r in rs),
                    median_uncovered_jobs=median([r['uncovered_jobs'] for r in rs]),median_hour=median([r['hour'] for r in rs])))
            bins=defaultdict(list)
            for r in items:bins[need_bin(r)].append(r)
            for condition,rows in bins.items():
                q=Counter(r['amount'] for r in rows);top=max(q.values());modes='|'.join(map(str,sorted(k for k,v in q.items() if v==top)))
                rules.append(dict(source=source,item=item,condition=condition,commands=len(rows),episodes=len({r['episode'] for r in rows}),
                    share_item_pickups=len(rows)/len(items),share_all_pickups=len(rows)/len(picks),mean_amount=mean([r['amount'] for r in rows]),
                    median_amount=median([r['amount'] for r in rows]),amount_modes=modes,mode_share=top/len(rows),
                    median_open_jobs=median([r['open_jobs'] for r in rows]),median_uncovered_jobs=median([r['uncovered_jobs'] for r in rows]),
                    median_other_carried=median([r['other_carried'] for r in rows]),median_legal_jobs=median([r['legal_jobs'] for r in rows])))
            for band,lo,hi in [('ALL',0,24),('0-7',0,8),('8-15',8,16),('16-23',16,24)]:
                rows=[r for r in items if r['amount']>0 and lo<=r['hour']<hi]
                if not rows:continue
                observed=[r for r in rows if r['first_use_lag'] is not None]
                drops=[r for r in rows if r['next_drop_lag'] is not None]
                clean=[r for r in drops if r['clean_cohort']]
                following.append(dict(source=source,item=item,hour_band=band,pickups=len(rows),first_use_observed=len(observed),
                    no_use_before_return=sum(r['use_censor'] in ('returned','overnight_return') for r in rows),
                    no_use_before_overnight_return=sum(r['use_censor']=='overnight_return' for r in rows),use_window_censored=sum(r['use_censor']=='window' for r in rows),
                    median_use_lag=median([r['first_use_lag'] for r in observed]),p90_use_lag=p90([r['first_use_lag'] for r in observed]),
                    next_drop_observed=len(drops),explicit_next_drop=sum(r['next_drop_kind']=='command' for r in drops),overnight_next_drop=sum(r['next_drop_kind']=='overnight' for r in drops),next_drop_censored=len(rows)-len(drops),median_next_drop_lag=median([r['next_drop_lag'] for r in drops]),
                    mean_left_at_next_drop=mean([r['left_before_next_drop'] for r in drops]),mean_removed_at_next_drop=mean([r['removed_at_next_drop'] for r in drops]),
                    clean_resolved=len(clean),clean_mean_pickup=mean([r['amount'] for r in clean]),clean_mean_left=mean([r['left_before_next_drop'] for r in clean]),
                    clean_mean_unused_removed=mean([r['removed_at_next_drop'] for r in clean]),
                    clean_unused_removed_fraction=sum(r['removed_at_next_drop'] for r in clean)/sum(r['amount'] for r in clean) if clean else None,
                    tool_kept_at_first_drop=sum(r['kept_after_next_drop']>0 for r in drops)))
        partial_ids={e['event_id'] for e in es if e['op']=='PLACE'}
        for item in TOOLS:
            items=[r for r in ks if r['item']==item]
            for band,lo,hi in [('ALL',0,24),('0-7',0,8),('8-15',8,16),('16-23',16,24)]:
                bins=defaultdict(list)
                for r in items:
                    if lo<=r['hour']<hi:bins[r['uncovered_jobs']>0,r['goods_before']>0].append(r)
                for (uncovered,goods),rows in bins.items():
                    decisions=Counter(r['decision'] for r in rows);choice=decisions['return']+decisions['keep']
                    keep_rules.append(dict(source=source,item=item,hour_band=band,uncovered_jobs=uncovered,sale_goods_carried=goods,
                        opportunities=len(rows),share_item_opportunities=len(rows)/len(items),return_commands=decisions['return'],keep_commands=decisions['keep'],
                        use_commands=decisions['use'],pickup_more_commands=decisions['pickup_more'],
                        return_share_of_return_or_keep=decisions['return']/choice if choice else None,
                        median_held=median([r['held'] for r in rows]),median_open_jobs=median([r['open_jobs'] for r in rows]),
                        partial_deposits_keeping_tool=sum(r['decision']=='keep' and r['event_id'] in partial_ids for r in rows)))
    # Independent SQL verifies every pickup decision-table count, mean and median.
    c=duckdb.connect();flat=[{k:r[k] for k in ('source','H','item','amount','uncovered_jobs')} for r in events if r['op']=='PICKUP']
    c.register('p',pa.Table.from_pylist(flat));sql_checks=0
    for row in rules:
        source=row['source'];where='item=?';params=[row['item']]
        if source!='ALL':
            where+=' AND source=?';params.append('L3' if source.startswith('L3h') else source)
            if source.startswith('L3h'):where+=' AND H=?';params.append(int(source[3:]))
        result=c.execute(f'''WITH b AS (SELECT *,CASE WHEN amount=0 THEN 'zero actual pickup' WHEN uncovered_jobs=0 THEN '0 uncovered'
            WHEN uncovered_jobs<=3 THEN '1-3 uncovered' WHEN uncovered_jobs<=7 THEN '4-7 uncovered' ELSE '8+ uncovered' END bucket FROM p)
            SELECT count(*),avg(amount),median(amount) FROM b WHERE {where} AND bucket=?''',params+[row['condition']]).fetchone()
        for field,value in zip(('commands','mean_amount','median_amount'),result):assert abs(row[field]-value)<1e-9;sql_checks+=1
    pickups=[r for r in events if r['op']=='PICKUP']
    assert all(r['amount']==min(r['requested'],r['shed_available']) for r in pickups)
    assert all(r['next_drop_lag'] is not None and r['next_drop_lag']>=1 for r in pickups)
    assert all(r['first_use_lag'] is not None or r['use_censor'] in ('returned','overnight_return') for r in pickups)
    assert all(r['left_before_next_drop']==r['removed_at_next_drop']+r['kept_after_next_drop'] for r in pickups)
    cols=('source','H','item','amount','hour','first_use_lag','next_drop_lag','left_before_next_drop','removed_at_next_drop','clean_cohort')
    c.register('follow',pa.Table.from_pylist([{k:r[k] for k in cols} for r in pickups]))
    for row in following:
        source=row['source'];where='item=?';params=[row['item']]
        if source!='ALL':
            where+=' AND source=?';params.append('L3' if source.startswith('L3h') else source)
            if source.startswith('L3h'):where+=' AND H=?';params.append(int(source[3:]))
        if row['hour_band']!='ALL':
            lo,hi=map(int,row['hour_band'].split('-'));where+=' AND hour BETWEEN ? AND ?';params.extend([lo,hi])
        result=c.execute(f'''SELECT count(*),count(first_use_lag),median(first_use_lag),count(next_drop_lag),
            avg(left_before_next_drop),avg(removed_at_next_drop),count(*) FILTER(WHERE clean_cohort),
            avg(amount) FILTER(WHERE clean_cohort),avg(removed_at_next_drop) FILTER(WHERE clean_cohort),
            sum(removed_at_next_drop) FILTER(WHERE clean_cohort)/sum(amount) FILTER(WHERE clean_cohort)
            FROM follow WHERE {where}''',params).fetchone()
        for field,value in zip(('pickups','first_use_observed','median_use_lag','next_drop_observed','mean_left_at_next_drop',
                'mean_removed_at_next_drop','clean_resolved','clean_mean_pickup','clean_mean_unused_removed','clean_unused_removed_fraction'),result):
            assert row[field] is None if value is None else row[field] is not None and abs(row[field]-value)<1e-9,(field,row[field],value)
            sql_checks+=1
    for source in SOURCES:
        assert abs(sum(r['share_all_pickups'] for r in rules if r['source']==source)-1)<1e-9
    check=dict(cases=len(receipts),L1_cases=sum(r['source']=='L1' for r in receipts),L3_cases=sum(r['source']=='L3' for r in receipts),
        teacher_turns=sum(r['teacher_turns'] for r in receipts),native_frames=sum(r['native_check']['frames'] for r in receipts),
        teacher_unit_rows_matched=sum(r['unit_rows'] for r in receipts),automatic_return_records=sum(r['automatic_return_records'] for r in receipts),shed_commands=counts[0]['shed_commands'],item_rows=len(events),keep_rows=len(keeps),
        test_games_opened=0,policy_inference_calls=0,independent_sql_checks=sql_checks,pickup_next_deposit_resolved=len(pickups),
        stock_clipped_pickups=sum(r['amount']<r['requested'] for r in pickups),signature=sig,
        event_table_sha256=sha(OUT/'shed_events.csv.gz'),keep_table_sha256=sha(OUT/'tool_keep_decisions.csv.gz'))
    for name,rows in [('COUNTS',counts),('SUMMARY',summary),('PICKUP_RULES',rules),('FOLLOWUP',following),('KEEP_RULES',keep_rules),('QUANTITIES',quantities)]:table(REPO/'reports'/f'SHED_{name}.csv',rows)
    (REPO/'reports/SHED_CHECKS.json').write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps(dict(checks=check,counts=counts[:3],pickups=[r for r in summary if r['source'] in ('ALL','L1','L3') and r['op']=='PICKUP'],
        rules=[r for r in rules if r['source']=='ALL' and r['item'] in TOOLS],
        followup=[r for r in following if r['source']=='ALL' and r['item'] in TOOLS and r['hour_band']=='ALL'],
        keep=[r for r in keep_rules if r['source']=='ALL' and r['hour_band']=='ALL']),indent=2))


if __name__=='__main__':main()

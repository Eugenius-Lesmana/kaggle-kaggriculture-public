"""Package M tables. Native SQL cross-checks and paired seed/seat accounting; no policy calls."""
from collections import Counter,defaultdict
import csv
import gzip
import json
from pathlib import Path
import time

import duckdb
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from market_pressure import ROOT,REPO,OUT,PRODUCTS,sha,save,signature,digest

GROUPS=('teacher','v3fw','template');PAIRS=[(s,p) for s in range(20001,20025) for p in (0,1)]
BANDS=(*range(5),-1)


def bandname(b):return 'all' if b==-1 else f'{b*6}-{b*6+5}'
def stat(values):
    a=np.array(values,dtype=float);cluster=a.reshape(-1,2).mean(axis=1)
    return float(a.mean()),float(cluster.std(ddof=1)/len(cluster)**.5),float(a.std(ddof=1)/len(a)**.5)
def fields(name,values):return dict(zip((name+'_mean',name+'_se_seed24',name+'_se_pair48'),stat(values)))
def ratio(n,d):
    n=np.array(n,dtype=float).reshape(-1,2).sum(axis=1);d=np.array(d,dtype=float).reshape(-1,2).sum(axis=1)
    if not d.sum():return None,None
    estimate=n.sum()/d.sum();den=d.sum()-d
    if np.any(den==0):return float(estimate),None
    jack=(n.sum()-n)/den
    return float(estimate),float(np.sqrt((len(jack)-1)/len(jack)*np.sum((jack-jack.mean())**2)))
def ratio_fields(name,n,d):return dict(zip((name,name+'_se_seed24'),ratio(n,d)))
def ratio_delta(name,nt,dt,nb,db):
    arrays=[np.array(x,dtype=float).reshape(-1,2).sum(axis=1) for x in (nt,dt,nb,db)]
    nt,dt,nb,db=arrays
    if not dt.sum() or not db.sum():return {name:None,name+'_se_seed24':None}
    estimate=nt.sum()/dt.sum()-nb.sum()/db.sum()
    if np.any(dt.sum()-dt==0) or np.any(db.sum()-db==0):return {name:float(estimate),name+'_se_seed24':None}
    jack=(nt.sum()-nt)/(dt.sum()-dt)-(nb.sum()-nb)/(db.sum()-db)
    return {name:float(estimate),name+'_se_seed24':float(np.sqrt((len(jack)-1)/len(jack)*np.sum((jack-jack.mean())**2)))}
def components(qt,rt,qb,rb):
    pt=rt/qt if qt else (rb/qb if qb else 0);pb=rb/qb if qb else pt
    return (qt-qb)*(pt+pb)/2,(pt-pb)*(qt+qb)/2

def write(name,rows):
    path=REPO/'reports'/('MARKET_PRESSURE_'+name+'.csv')
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    return dict(file=str(path.relative_to(REPO)),rows=len(rows),sha256=sha(path))


def load():
    run=json.loads((OUT/'full.json').read_bytes());assert run['cases']==144 and run['signature']==signature()
    data={g:{} for g in GROUPS};sql_checks=0;ties=0;inventory_checks=0;town_by_seed={};config_by_seed={}
    db=duckdb.connect();db.execute('SET threads=1')
    for source in run['sources']:
        key=f"{source['group']}-{source['seed']}-seat{source['seat']}"
        m=json.loads(gzip.decompress((OUT/'cases'/f'{key}.json.gz').read_bytes()))
        assert m['signature']==signature() and m['source']==source
        ties+=m['same_position_unit_quote_pairs']
        seat=source['seat'];role=lambda p:'ours' if p==seat else 'metav4'
        d={'sales':defaultdict(Counter),'orders':defaultdict(Counter),'cash':Counter(),'farm':defaultdict(Counter),
           'path':{},'stock':{},'windows':defaultdict(Counter),'timing':defaultdict(Counter),'banks':dict(zip(('ours','metav4'),m['banks']))}
        rep=json.loads(gzip.decompress(Path(source['raw']).read_bytes()))
        stocks=np.array([[f[0]['observation']['market']['inventory'][item] for item in PRODUCTS] for f in rep['steps']],dtype=np.int64)
        inflow=np.zeros((719,len(PRODUCTS)),dtype=np.int64);sold=np.zeros((2,719,len(PRODUCTS)),dtype=np.int64);bought=np.zeros_like(sold)
        for r in m['native_sales']:
            if r['price']>1:sold[r['seat'],r['step'],PRODUCTS.index(r['product'])]+=r['units']
        for r in m['native_orders']:
            command=json.loads(r['command'])
            if command and command[0]=='BUY_PRODUCT':bought[r['seat'],r['step'],PRODUCTS.index(command[1])]+=r['units']
        inflow=sold.sum(axis=0)-bought.sum(axis=0)
        town=inflow-np.diff(stocks,axis=0);assert np.all(town>=0)
        cfg={k:v for k,v in rep['configuration'].items() if k not in ('actTimeout','runTimeout','seed')}
        schedule=[f[0]['observation']['town'] for f in rep['steps']]
        fingerprint=(town.tobytes(),json.dumps(schedule,sort_keys=True),stocks[0].tobytes())
        if source['seed'] in town_by_seed:
            assert fingerprint==town_by_seed[source['seed']],'town demand or initial stocks differ across matched games'
            assert cfg==config_by_seed[source['seed']],'game rules differ'
        else:town_by_seed[source['seed']]=fingerprint;config_by_seed[source['seed']]=cfg
        assert np.array_equal(stocks[1:],stocks[0]+np.cumsum(inflow-town,axis=0));inventory_checks+=town.size
        for b,stop in enumerate((144,288,432,576,719)):
            for i,item in enumerate(PRODUCTS):
                d['stock'][b,item]=dict(stock=int(stocks[stop,i]),price=rep['steps'][stop][0]['observation']['market']['prices'][item],
                    ours_above_floor_sales=int(sold[seat,:stop,i].sum()),metav4_above_floor_sales=int(sold[1-seat,:stop,i].sum()),
                    ours_buys=int(bought[seat,:stop,i].sum()),metav4_buys=int(bought[1-seat,:stop,i].sum()),town_removed=int(town[:stop,i].sum()))
        for r in m['sales']:
            for b in (r['band'],-1):d['sales'][role(r['seat']),b,r['product']].update({k:r.get(k,0) for k in ('units','revenue','floor_units','unit_hours')})
        for r in m['native_sales']:
            for b in (r['step']//144,-1):d['windows'][role(r['seat']),b,r['step']%24//6,r['product']].update(units=r['units'],revenue=r['revenue'])
        for r in m['harvest']:
            for b in (r['band'],-1):d['sales'][role(r['seat']),b,r['product']]['harvest_units']+=r['units']
        for r in m['orders']:
            for b in (r['band'],-1):
                key=(role(r['seat']),b,r['op']+':'+r['item']);d['cash'][key]+=r['cash']
                d['orders'][key].update({k:r[k] for k in ('units','cash','orders','effect_orders')})
        for r in m['unitcash']:
            for b in (r['band'],-1):d['cash'][role(r['seat']),b,'UNIT:'+r['op']]+=r['cash']
        for r in m['farm']:
            for b in (r['band'],-1):d['farm'][role(r['seat']),b].update({k:v for k,v in r.items() if k not in ('seat','band')})
        for r in m['planted']:
            for b in (r['band'],-1):d['farm'][role(r['seat']),b]['planted_'+r['product']]+=r['units']
        for r in m['path']:d['path'][r['band'],r['hour'],r['product']]={k:r[k] for k in ('price','stock')}
        for r in m['timing']:
            for b in (r['band'],-1):d['timing'][b,r['product']].update({k:r.get(k,0) for k in ('both_sell_turns','ours_first','metav4_first','same_position')})
        db.register('native_sales',pa.Table.from_pylist(m['native_sales']))
        native=db.sql('SELECT seat, CAST(floor(step/144) AS INTEGER),product,sum(units),sum(revenue) FROM native_sales GROUP BY ALL').fetchall()
        for p,b,item,q,cash in native:
            v=d['sales'][role(p),b,item];assert (q,cash)==(v['units'],v['revenue']);sql_checks+=2
        db.register('native_orders',pa.Table.from_pylist(m['native_orders']))
        for p,cash in db.sql('SELECT seat,sum(cash_delta) FROM native_orders GROUP BY seat').fetchall():
            cost=sum(r['cash'] for r in m['unitcash'] if r['seat']==p)
            assert 3000+cash+cost==d['banks'][role(p)];sql_checks+=1
        for who in ('ours','metav4'):
            assert 3000+sum(v for (w,b,_),v in d['cash'].items() if w==who and b==-1)==d['banks'][who]
        data[source['group']][source['seed'],seat]=d
    assert all(set(data[g])==set(PAIRS) for g in GROUPS)
    return data,run,dict(native_sql_numeric_checks=sql_checks,equal_same_position_unit_quotes=ties,inventory_balance_cells=inventory_checks,matched_town_schedules_and_demands=len(town_by_seed))


def cash_totals(data):
    headline=[];bands=[];own=[];bankpaired=[];totals=[]
    for group in GROUPS:
        for who in ('ours','metav4'):
            for band in BANDS:
                revenue=[sum(data[group][p]['sales'].get((who,band,item),{}).get('revenue',0) for item in PRODUCTS) for p in PAIRS]
                cash=[sum(v for (w,b,_),v in data[group][p]['cash'].items() if w==who and b==band) for p in PAIRS]
                totals.append(dict(group=group,role=who,band=bandname(band),**fields('revenue',revenue),**fields('net_cash',cash)))
    for base in ('v3fw','template'):
        for who in ('ours','metav4','margin'):
            def bank(g,p):
                b=data[g][p]['banks'];return b['ours']-b['metav4'] if who=='margin' else b[who]
            bankpaired.append(dict(baseline=base,role=who,contrast='teacher_minus_baseline',**fields('bank_delta',[bank('teacher',p)-bank(base,p) for p in PAIRS])))
        for band in BANDS:
            revloss=[];bankloss=[];ourrev=[];ourcash=[]
            for p in PAIRS:
                def revenue(g,role):return sum(data[g][p]['sales'].get((role,band,item),{}).get('revenue',0) for item in PRODUCTS)
                def cash(g,role):return sum(v for (w,b,_),v in data[g][p]['cash'].items() if w==role and b==band)
                revloss.append(revenue(base,'metav4')-revenue('teacher','metav4'))
                bankloss.append(cash(base,'metav4')-cash('teacher','metav4'))
                ourrev.append(revenue('teacher','ours')-revenue(base,'ours'));ourcash.append(cash('teacher','ours')-cash(base,'ours'))
            bands.append(dict(baseline=base,band=bandname(band),**fields('revenue_loss',revloss),**fields('spending_contribution',np.array(bankloss)-revloss),**fields('bank_loss',bankloss)))
            own.append(dict(baseline=base,band=bandname(band),**fields('own_revenue_delta',ourrev),**fields('own_cash_delta',ourcash)))
            if band==-1:
                for item in PRODUCTS:
                    a=[data[base][p]['sales'].get(('metav4',-1,item),{}).get('revenue',0)-data['teacher'][p]['sales'].get(('metav4',-1,item),{}).get('revenue',0) for p in PAIRS]
                    headline.append(dict(baseline=base,component=item,**fields('bank_loss_contribution',a)))
                headline.append(dict(baseline=base,component='NET_SPENDING',**fields('bank_loss_contribution',np.array(bankloss)-revloss)))
                headline.append(dict(baseline=base,component='TOTAL',**fields('bank_loss_contribution',bankloss)))
    return [write('HEADLINE',headline),write('BANDS',bands),write('OUR_BANDS',own),write('BANKS_PAIRED',bankpaired),write('TOTALS',totals)]


def main():
    begun=time.perf_counter();data,run,checks=load();outputs=[write('SOURCES',[{**c,'raw':Path(c['raw']).relative_to(ROOT).as_posix(),'metrics':Path(c['metrics']).relative_to(ROOT).as_posix()} for c in run['sources']])]
    get=lambda g,p,table,key,field: data[g][p][table].get(key,{}).get(field,0)
    values=lambda g,t,key,field:[get(g,p,t,key,field) for p in PAIRS]
    bankrows=[]
    for g in GROUPS:
        for who in ('ours','metav4'):bankrows.append(dict(group=g,role=who,n_games=48,n_seeds=24,**fields('bank',[data[g][p]['banks'][who] for p in PAIRS])))
    outputs.append(write('BANKS',bankrows))
    salesrows=[];paired=[];paired_raw=[]
    for who in ('ours','metav4'):
        for band in BANDS:
            for item in PRODUCTS:
                key=(who,band,item)
                for g in GROUPS:
                    q=values(g,'sales',key,'units');r=values(g,'sales',key,'revenue');f=values(g,'sales',key,'floor_units');h=values(g,'sales',key,'unit_hours')
                    row=dict(group=g,role=who,band=bandname(band),product=item,n_games=48,n_seeds=24,
                        zero_sales_games=sum(x==0 for x in q),**fields('units',q),**fields('revenue',r),**fields('harvest_units',values(g,'sales',key,'harvest_units')),
                        **ratio_fields('unit_price',r,q),**ratio_fields('floor_share',f,q),**ratio_fields('sell_hour',h,q))
                    salesrows.append(row)
                for base in ('v3fw','template'):
                    qt=values('teacher','sales',key,'units');rt=values('teacher','sales',key,'revenue');qb=values(base,'sales',key,'units');rb=values(base,'sales',key,'revenue')
                    qs=[];ps=[]
                    for index,p in enumerate(PAIRS):
                        bands=range(5) if band==-1 else (band,)
                        effect=[components(get('teacher',p,'sales',(who,b,item),'units'),get('teacher',p,'sales',(who,b,item),'revenue'),get(base,p,'sales',(who,b,item),'units'),get(base,p,'sales',(who,b,item),'revenue')) for b in bands]
                        qe=sum(x[0] for x in effect);pe=sum(x[1] for x in effect);assert abs(qe+pe-(rt[index]-rb[index]))<1e-8
                        qs.append(qe);ps.append(pe)
                        paired_raw.append(dict(baseline=base,role=who,band=bandname(band),product=item,seed=p[0],seat=p[1],revenue_delta=rt[index]-rb[index],quantity_component=qe,price_component=pe))
                    paired.append(dict(baseline=base,contrast='teacher_minus_baseline',role=who,band=bandname(band),product=item,n_pairs=48,n_seeds=24,
                        baseline_positive_teacher_zero_games=sum(t==0 and b>0 for t,b in zip(qt,qb)),teacher_positive_baseline_zero_games=sum(t>0 and b==0 for t,b in zip(qt,qb)),same_units_games=sum(t==b for t,b in zip(qt,qb)),**ratio_delta('unit_price_delta',rt,qt,rb,qb),**fields('units_delta',np.array(qt)-qb),**fields('revenue_delta',np.array(rt)-rb),**fields('quantity_component',qs),**fields('price_component',ps)))
    outputs.extend((write('SALES',salesrows),write('SALES_PAIRED',paired)))
    categories=sorted({k[2] for g in GROUPS for d in data[g].values() for k in d['cash'] if any(c for (w,b,cat),c in d['cash'].items() if cat==k[2])})
    lossrows=[];cashrows=[];purchases=[];purchasepaired=[]
    for who in ('ours','metav4'):
        for band in BANDS:
            for cat in categories:
                arrays={g:[data[g][p]['cash'][who,band,cat] for p in PAIRS] for g in GROUPS}
                for g in GROUPS:
                    cashrows.append(dict(group=g,role=who,band=bandname(band),category=cat,**fields('cash',arrays[g])))
                    if cat.startswith(('BUY_','HIRE:')):
                        units=values(g,'orders',(who,band,cat),'units');purchases.append(dict(group=g,role=who,band=bandname(band),category=cat,
                            **fields('units',units),**fields('spend',-np.array(arrays[g])),**ratio_fields('unit_cost',-np.array(arrays[g]),units)))
                if cat.startswith(('BUY_','HIRE:')):
                    for base in ('v3fw','template'):
                        ut=values('teacher','orders',(who,band,cat),'units');ub=values(base,'orders',(who,band,cat),'units')
                        purchasepaired.append(dict(baseline=base,role=who,band=bandname(band),category=cat,contrast='teacher_minus_baseline',same_units_games=sum(a==b for a,b in zip(ut,ub)),**fields('units_delta',np.array(ut)-ub),**fields('spend_delta',np.array(arrays[base])-arrays['teacher'])))
                for base in ('v3fw','template'):lossrows.append(dict(baseline=base,role=who,band=bandname(band),category=cat,contrast='baseline_minus_teacher_cash',**fields('loss_contribution',np.array(arrays[base])-arrays['teacher'])))
    outputs.extend((write('CASH',cashrows),write('LOSS',lossrows),write('PURCHASES',purchases),write('PURCHASES_PAIRED',purchasepaired)))
    farmrows=[];farmpaired=[]
    metrics=('hands','land',*('crop_'+x for x in RT_CROPS),*('animal_'+x for x in ('GOOSE','COW','SHEEP')),*('planted_'+x for x in RT_CROPS))
    for who in ('ours','metav4'):
        for band in BANDS:
            for metric in metrics:
                arrays={g:[get(g,p,'farm',(who,band),metric)/(1 if metric.startswith('planted_') else get(g,p,'farm',(who,band),'n')) for p in PAIRS] for g in GROUPS}
                for g in GROUPS:farmrows.append(dict(group=g,role=who,band=bandname(band),metric=metric,**fields('value',arrays[g])))
                for base in ('v3fw','template'):farmpaired.append(dict(baseline=base,role=who,band=bandname(band),metric=metric,contrast='teacher_minus_baseline',**fields('delta',np.array(arrays['teacher'])-arrays[base])))
    outputs.extend((write('FARM',farmrows),write('FARM_PAIRED',farmpaired)))
    orderrows=[]
    for band in BANDS:
        for item in PRODUCTS:
            for g in GROUPS:
                both=values(g,'timing',(band,item),'both_sell_turns')
                row=dict(group=g,band=bandname(band),product=item,**fields('both_sell_turns',both))
                for field in ('ours_first','metav4_first','same_position'):row.update(fields(field+'_turns',values(g,'timing',(band,item),field)));row.update(ratio_fields(field+'_share',values(g,'timing',(band,item),field),both))
                orderrows.append(row)
    outputs.append(write('ORDERING',orderrows))
    paths=[];pathpaired=[]
    for band in range(5):
        for hour in range(24):
            for item in PRODUCTS:
                arrays={g:{f:values(g,'path',(band,hour,item),f) for f in ('price','stock')} for g in GROUPS}
                for g in GROUPS:paths.append(dict(group=g,band=bandname(band),hour=hour,product=item,**fields('price',arrays[g]['price']),**fields('stock',arrays[g]['stock'])))
                for base in ('v3fw','template'):pathpaired.append(dict(baseline=base,band=bandname(band),hour=hour,product=item,contrast='teacher_minus_baseline',**fields('price_delta',np.array(arrays['teacher']['price'])-arrays[base]['price']),**fields('stock_delta',np.array(arrays['teacher']['stock'])-arrays[base]['stock'])))
    outputs.extend((write('PATHS',paths),write('PATHS_PAIRED',pathpaired)))
    windows=[]
    for who in ('ours','metav4'):
        for band in BANDS:
            for window in range(4):
                for item in PRODUCTS:
                    for g in GROUPS:
                        key=(who,band,window,item);q=values(g,'windows',key,'units');r=values(g,'windows',key,'revenue')
                        windows.append(dict(group=g,role=who,band=bandname(band),hours=f'{window*6}-{window*6+5}',product=item,**fields('units',q),**fields('revenue',r),**ratio_fields('unit_price',r,q)))
    outputs.append(write('SELL_WINDOWS',windows))
    stocks=[];stockpaired=[]
    for band in range(5):
        for item in PRODUCTS:
            arrays={g:{f:values(g,'stock',(band,item),f) for f in ('stock','price','ours_above_floor_sales','metav4_above_floor_sales','ours_buys','metav4_buys','town_removed')} for g in GROUPS}
            for g in GROUPS:
                row=dict(group=g,through_band=bandname(band),product=item)
                for field,v in arrays[g].items():row.update(fields(field,v))
                stocks.append(row)
            for base in ('v3fw','template'):
                row=dict(baseline=base,through_band=bandname(band),product=item,contrast='teacher_minus_baseline')
                for field in arrays['teacher']:row.update(fields(field+'_delta',np.array(arrays['teacher'][field])-arrays[base][field]))
                stockpaired.append(row)
    outputs.extend((write('STOCKS',stocks),write('STOCKS_PAIRED',stockpaired)))
    # Independent SQL verifies every paired mean and clustered SE, not the same Python helper twice.
    pq.write_table(pa.Table.from_pylist(paired_raw),OUT/'paired_components.parquet',compression='zstd')
    db=duckdb.connect();db.execute('SET threads=1');db.register('pairs',pa.Table.from_pylist(paired_raw))
    sql="""WITH seeds AS (SELECT baseline,role,band,product,seed,avg(revenue_delta) revenue_delta,avg(quantity_component) quantity_component,avg(price_component) price_component FROM pairs GROUP BY ALL)
    SELECT baseline,role,band,product,avg(revenue_delta),stddev_samp(revenue_delta)/sqrt(count(*)),avg(quantity_component),stddev_samp(quantity_component)/sqrt(count(*)),avg(price_component),stddev_samp(price_component)/sqrt(count(*)) FROM seeds GROUP BY ALL"""
    expected={(r['baseline'],r['role'],r['band'],r['product']):r for r in paired};nchecks=0
    for base,who,band,item,*numbers in db.sql(sql).fetchall():
        r=expected[base,who,band,item];wanted=[r[f+'_'+s] for f in ('revenue_delta','quantity_component','price_component') for s in ('mean','se_seed24')]
        assert np.allclose(numbers,wanted,rtol=1e-10,atol=1e-8),(base,who,band,item,numbers,wanted);nchecks+=len(wanted)
    (OUT/'independent-check.sql').write_text(sql,encoding='utf-8')
    outputs.extend(cash_totals(data))
    decomposition=[]
    for base in ('v3fw','template'):
        for who in ('ours','metav4'):
            row=dict(baseline=base,role=who,contrast='teacher_minus_baseline')
            for field in ('revenue_delta','quantity_component','price_component'):
                sums=Counter()
                for r in paired_raw:
                    if r['baseline']==base and r['role']==who and r['band']=='all':sums[r['seed'],r['seat']]+=r[field]
                row.update(fields(field,[sums[p] for p in PAIRS]))
            decomposition.append(row)
    outputs.append(write('DECOMP_TOTALS',decomposition))
    checks['paired_sql_numeric_checks']=nchecks
    for base in ('v3fw','template'):
        for p in PAIRS:
            for who in ('ours','metav4'):
                total=sum(data[base][p]['cash'][who,-1,c]-data['teacher'][p]['cash'][who,-1,c] for c in categories)
                assert total==data[base][p]['banks'][who]-data['teacher'][p]['banks'][who]
    assert all(sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'] for c in run['sources'])
    protected=json.loads((OUT/'protected-before.json').read_bytes());assert all(sha(REPO/p)==h for p,h in protected.items())
    checks.update(cash_accounting_residual=0,all_288_existing_run_inputs_hash_unchanged=True,protected_source_files_unchanged=len(protected))
    summary=dict(extract_signature=run['signature'],source_index_sha256=digest(run['sources']),analysis_code_hashes={str(p.relative_to(REPO)):sha(p) for p in (Path(__file__),REPO/'tools/market_pressure.py',REPO/'tools/test_market_pressure.py')},cases=144,seeds=24,seats=2,new_games=0,workers=run['workers'],extract_seconds=run['seconds'],report_seconds=time.perf_counter()-begun,checks=checks,outputs=outputs,
        definitions=dict(contrast='teacher minus matched baseline except LOSS: baseline minus teacher cash',primary_se='SE of the 24 seed means, each averaging its two matched seats',secondary_se='SE across 48 matched seed/seat pairs',price='total executed revenue / total executed units; SE is leave-one-seed-out jackknife',decomposition='symmetric quantity/price components within each seed-seat-product-six-day band, summed for all-season; missing zero-quantity price uses the other matchup price',paths='mean pre-action observations within game x band x hour; terminal frame excluded'))
    save(REPO/'reports/MARKET_PRESSURE_CHECKS.json',summary)
    print(json.dumps(summary,separators=(',',':')),flush=True)


RT_CROPS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')
if __name__=='__main__':main()

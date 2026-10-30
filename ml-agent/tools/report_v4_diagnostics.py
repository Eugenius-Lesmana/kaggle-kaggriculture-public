"""Package V tables: native receipts, matched contrasts, seed-cluster standard errors."""
from collections import defaultdict,Counter
import csv
import json
import math
from pathlib import Path
import numpy as np
from v4_diagnostics import OUT,ROOT,REPO,PRODUCTS,sha,load,signature
from report_market_pressure import components

PAIRS=[(s,p) for s in range(20001,20025) for p in (0,1)]
BANDS=[('0-5',range(0,6)),('6-11',range(6,12)),('12-17',range(12,18)),('18-23',range(18,24)),('24-29',range(24,30)),('all',range(30))]
MACRO=('cash','end_cash','land','hands','crops','animals',*('crop_'+s for s in ('wheat','carrot','tomato','strawberry','melon')),*('animal_'+s for s in ('goose','cow','sheep')),'revenue','net_cash','net_spending')


def stats(rows):
    # Rows are seed,seat,value. CR1 intercept-only cluster SE; balanced pairs reduce to SE of 24 seed means.
    values=np.asarray([r[2] for r in rows],float);mean=float(values.mean());by=defaultdict(float)
    for seed,seat,value in rows:by[seed]+=value-mean
    g=len(by);se=math.sqrt(g/(g-1)*sum(v*v for v in by.values()))/len(rows) if g>1 else None
    return dict(mean=mean,se=se,n_games=len(rows),n_seeds=g)


def ratio(rows):
    # Seed-cluster delete-one jackknife for a ratio of totals, not mean of per-game rates.
    by=defaultdict(lambda:[0,0])
    for seed,n,d in rows:by[seed][0]+=n;by[seed][1]+=d
    total=np.sum(list(by.values()),axis=0);g=len(by)
    if total[1]==0:return dict(rate=None,se=None)
    jack=[(total[0]-n)/(total[1]-d) for n,d in by.values() if total[1]>d]
    se=float(np.sqrt((g-1)/g*np.sum((np.array(jack)-np.mean(jack))**2))) if g>1 and len(jack)==g else None
    return dict(rate=float(total[0]/total[1]),se=se)


def write(name,rows):
    assert rows,name;path=REPO/'reports'/f'V4DIAG_{name}.csv';fields=list(dict.fromkeys(k for r in rows for k in r))
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v,separators=(',',':')) if isinstance(v,(dict,list)) else v for k,v in r.items()} for r in rows)


def metric(data,g,p,day,role,key):return data[g][p]['daily'][day,role][key]


def general():
    sources=json.loads((OUT/'sources.json').read_text());data=defaultdict(dict);town={}
    for c in sources:
        assert sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'];d=load(OUT/'cases'/f"{c['group']}-{c['seed']}-seat{c['seat']}.json.gz");assert d['signature']==signature() and d['source']==c
        if c['seed'] in town:assert town[c['seed']]==d['town_fingerprint'],'matched game rules/town schedule differ'
        town[c['seed']]=d['town_fingerprint'];d['daily']={(r['day'],r['role']):r for r in d['days']};data[c['group']][c['seed'],c['seat']]=d
    assert len(sources)==192 and len(town)==24
    write('SOURCES',sources);loss=[p for p in PAIRS if data['v4'][p]['margin']<0];wins=[p for p in PAIRS if data['v4'][p]['margin']>0];assert len(loss)==10 and len(wins)==38
    losses=[]
    for p in loss:
        d=data['v4'][p];gaps=[metric(data,'v4',p,day,'ours','cash')-metric(data,'v4',p,day,'metav4','cash') for day in range(30)]+[d['margin']]
        losses.append(dict(seed=p[0],seat=p[1],shops=d['early_shops'],own_bank=d['banks'][0],metav4_bank=d['banks'][1],margin=d['margin'],first_negative_dawn=next((i for i,v in enumerate(gaps[:30]) if v<0),None),sustained_negative_from=next(i for i in range(31) if all(v<0 for v in gaps[i:]))))
    write('LOSSES',losses)
    cohort=[];cohort_income=[];headline={}
    for name,pairs in [('loss',loss),('win',wins)]:
        headline[name]=stats([(s,p,data['v4'][s,p]['margin']) for s,p in pairs])
        for day in range(30):
            for role in ('ours','metav4'):
                for key in MACRO:
                    cohort.append(dict(cohort=name,day=day,role=role,metric=key,**stats([(s,p,metric(data,'v4',(s,p),day,role,key)) for s,p in pairs])))
            for key in ('cash','end_cash'):
                cohort.append(dict(cohort=name,day=day,role='gap',metric=key,**stats([(s,p,metric(data,'v4',(s,p),day,'ours',key)-metric(data,'v4',(s,p),day,'metav4',key)) for s,p in pairs])))
        for band,days in BANDS:
            for role in ('ours','metav4'):
                for product in PRODUCTS:
                    cohort_income.append(dict(cohort=name,band=band,role=role,product=product,**stats([(s,p,sum(metric(data,'v4',(s,p),day,role,'revenue_'+product.lower()) for day in days)) for s,p in pairs])))
    write('COHORT_DAILY',cohort);write('COHORT_REVENUE',cohort_income)
    scenarios=[]
    for shop in sorted({tuple(d['early_shops']) for d in data['v4'].values()}):
        pairs=[p for p in PAIRS if tuple(data['v4'][p]['early_shops'])==shop];scenarios.append(dict(shops=list(shop),losses=sum(data['v4'][p]['margin']<0 for p in pairs),wins=sum(data['v4'][p]['margin']>0 for p in pairs),**stats([(s,p,data['v4'][s,p]['margin']) for s,p in pairs])))
    write('SHOP_SCENARIOS',scenarios)
    absolute=[]
    for group in ('v4','teacher','v3fw','template'):
        for day in range(30):
            for role in ('ours','metav4'):
                for key in MACRO:absolute.append(dict(player=group,day=day,role=role,metric=key,**stats([(seed,seat,metric(data,group,(seed,seat),day,role,key)) for seed,seat in PAIRS])))
    write('MACRO_DAILY',absolute)
    paired=[];income=[];banks=[];pressure=[]
    for a,b in [('teacher','v4'),('teacher','v3fw'),('v4','v3fw')]:
        contrast=a+'_minus_'+b
        for day in range(30):
            for role in ('ours','metav4'):
                for key in MACRO:paired.append(dict(contrast=contrast,day=day,role=role,metric=key,**stats([(s,p,metric(data,a,(s,p),day,role,key)-metric(data,b,(s,p),day,role,key)) for s,p in PAIRS])))
        for band,days in BANDS:
            for role in ('ours','metav4'):
                for product in PRODUCTS:
                    av=[sum(metric(data,a,p,d,role,'revenue_'+product.lower()) for d in days) for p in PAIRS];bv=[sum(metric(data,b,p,d,role,'revenue_'+product.lower()) for d in days) for p in PAIRS]
                    row=dict(contrast=contrast,band=band,role=role,product=product,a_mean=float(np.mean(av)),b_mean=float(np.mean(bv)),**stats([(s,p,x-y) for (s,p),x,y in zip(PAIRS,av,bv)]));income.append(row)
        for role,index in [('ours',0),('metav4',1),('margin',None)]:
            get=lambda g,p:data[g][p]['margin'] if index is None else data[g][p]['banks'][index]
            banks.append(dict(contrast=contrast,role=role,**stats([(s,p,get(a,(s,p))-get(b,(s,p))) for s,p in PAIRS])))
        # Paired revenue minus net-spending difference independently bridges the terminal bank difference.
        for p in PAIRS:
            for role,index in [('ours',0),('metav4',1)]:
                delta=sum(metric(data,a,p,d,role,'net_cash')-metric(data,b,p,d,role,'net_cash') for d in range(30));assert delta==data[a][p]['banks'][index]-data[b][p]['banks'][index]
    for base in ('v4','v3fw'):
        for band,days in BANDS:
            for product in PRODUCTS:
                values=[];quantity=[];price=[]
                for s,p in PAIRS:
                    def amount(g,f):return sum(metric(data,g,(s,p),d,'metav4',f+'_'+product.lower()) for d in days)
                    qb,rb,qt,rt=amount(base,'units'),amount(base,'revenue'),amount('teacher','units'),amount('teacher','revenue');q,z=components(qb,rb,qt,rt);assert abs(q+z-(rb-rt))<1e-6
                    values.append((s,p,rb-rt));quantity.append((s,p,q));price.append((s,p,z))
                pressure.append(dict(baseline=base,band=band,product=product,quantity_mean=stats(quantity)['mean'],quantity_se=stats(quantity)['se'],price_mean=stats(price)['mean'],price_se=stats(price)['se'],**stats(values)))
        spending=[]
        for s,p in PAIRS:spending.append((s,p,-sum(metric(data,base,(s,p),d,'metav4','net_spending')-metric(data,'teacher',(s,p),d,'metav4','net_spending') for d in range(30))))
        pressure.append(dict(baseline=base,band='all',product='NET_SPENDING',quantity_mean=None,quantity_se=None,price_mean=None,price_se=None,**stats(spending)))
    cashbands=[];cohort_pressure=[];late=[]
    for a,b in [('teacher','v4'),('teacher','v3fw'),('v4','v3fw')]:
        for band,days in BANDS:
            for role in ('ours','metav4'):
                for key in ('net_cash','revenue','net_spending'):
                    cashbands.append(dict(contrast=a+'_minus_'+b,band=band,role=role,metric=key,**stats([(seed,seat,sum(metric(data,a,(seed,seat),d,role,key)-metric(data,b,(seed,seat),d,role,key) for d in days)) for seed,seat in PAIRS])))
    for name,pairs in [('loss',loss),('win',wins)]:
        for product in PRODUCTS:
            cohort_pressure.append(dict(cohort=name,product=product,**stats([(seed,seat,sum(metric(data,'v4',(seed,seat),d,'metav4','revenue_'+product.lower())-metric(data,'teacher',(seed,seat),d,'metav4','revenue_'+product.lower()) for d in range(30))) for seed,seat in pairs])))
        for key in ('land','crops','animals',*('crop_'+c.lower() for c in ('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')),*('animal_'+a.lower() for a in ('GOOSE','COW','SHEEP'))):
            late.append(dict(cohort=name,metric=key,**stats([(seed,seat,float(np.mean([metric(data,'v4',(seed,seat),d,'ours',key) for d in range(24,30)]))) for seed,seat in pairs])))
    write('CASH_BANDS',cashbands);write('COHORT_PRESSURE',cohort_pressure);write('LATE_FARM',late)
    write('PAIRED_DAILY',paired);write('PAIRED_REVENUE',income);write('PAIRED_BANKS',banks);write('MARKET_PRESSURE',pressure)
    summary=dict(cohorts=headline,losses=losses,banks=banks,pressure_top=sorted([r for r in pressure if r['baseline']=='v4' and r['band']=='all'],key=lambda r:r['mean'],reverse=True),checks=dict(native_games=192,daily_cash_bridges=192*30*2,matched_town_seeds=24))
    for name,pairs in [('loss',loss),('win',wins)]:
        gaps=[stats([(s,p,metric(data,'v4',(s,p),d,'ours','cash')-metric(data,'v4',(s,p),d,'metav4','cash')) for s,p in pairs])['mean'] for d in range(30)]+[headline[name]['mean']]
        summary[name+'_mean_sustained_negative_from']=next((i for i in range(31) if all(v<0 for v in gaps[i:])),None)
    return data,summary


def guard():
    selected=json.loads((OUT/'guard-selection.json').read_text());logs=[];episodes=[];jobs=[];games=[];denominators={}
    for c in selected:
        d=load(OUT/'guard'/f"{c['seed']}-seat{c['seat']}.json.gz");m=json.loads(Path(c['metrics']).read_bytes());assert d['gameplay_sha256']==m['gameplay_sha256'] and d['ours_calls']==d['opponent_calls']==719
        base=dict(seed=c['seed'],seat=c['seat'],outcome=c['outcome']);original=load(c['raw']);denominator=sum(1+len(frame[c['seat']]['observation']['farms'][c['seat']]['hands']) for frame in original['steps'][144:696]);denominators[c['seed'],c['seat']]=denominator
        games.append({**base,'gameplay_sha256':d['gameplay_sha256'],'network_worker_decisions':denominator,'overrides':sum(r['changed'] for r in d['logs']),'seconds':d['seconds']})
        logs.extend({**base,**r} for r in d['logs'] if r['changed']);episodes.extend({**base,**r} for r in d['episodes']);jobs.extend({**base,**r} for r in d['jobs'] if r['intervened'])
    write('GUARD_GAMES',games);write('GUARD_OVERRIDES',logs);write('GUARD_EPISODES',episodes);write('GUARD_JOBS',jobs)
    perday=[]
    for c in selected:
        for day in range(6,29):
            for kind in ('FEED','WATER','all'):
                eligible=lambda r:r['seed']==c['seed'] and r['seat']==c['seat'] and r['day']==day and (kind=='all' or r['kind']==kind)
                jj=[r for r in jobs if eligible(r)];ee=[r for r in episodes if eligible(r) and r['overridden_turns']];ll=[r for r in logs if eligible(r)]
                perday.append(dict(seed=c['seed'],seat=c['seat'],outcome=c['outcome'],day=day,kind=kind,overrides=len(ll),assignment_episodes=len(ee),active_turns=sum(r['active_turns'] for r in ee),jobs=len(jj),successes=sum(r['success'] for r in jj),night_losses=sum(r['night_loss'] for r in jj),target_removed=sum(r['target_removed'] for r in jj),failed_cost_proxy=sum(r['failed_cost_proxy'] for r in jj)))
    write('GUARD_PER_DAY',perday);summary=[];daily=[]
    for kind in ('FEED','WATER','all'):
        records=[]
        for c in selected:
            rr=[r for r in perday if r['seed']==c['seed'] and r['seat']==c['seat'] and r['kind']==kind];records.append(dict(seed=c['seed'],seat=c['seat'],**{k:sum(r[k] for r in rr) for k in ('overrides','assignment_episodes','active_turns','jobs','successes','night_losses','target_removed','failed_cost_proxy')}))
        share=ratio([(r['seed'],r['overrides'],denominators[r['seed'],r['seat']]) for r in records]);rate=ratio([(r['seed'],r['successes'],r['jobs']) for r in records]);duration=ratio([(r['seed'],r['active_turns'],r['assignment_episodes']) for r in records]);ee=[r for r in episodes if r['overridden_turns'] and (kind=='all' or r['kind']==kind)]
        row=dict(kind=kind,override_fraction=share['rate'],override_fraction_se=share['se'],**{k:sum(r[k] for r in records) for k in ('overrides','assignment_episodes','active_turns','jobs','successes','night_losses','target_removed','failed_cost_proxy')},success_rate=rate['rate'],success_rate_se=rate['se'],mean_episode_active_turns=duration['rate'],mean_episode_active_turns_se=duration['se'])
        for key in ('overrides','active_turns','jobs','failed_cost_proxy'):
            stat=stats([(r['seed'],r['seat'],r[key]) for r in records]);row[key+'_per_game_mean']=stat['mean'];row[key+'_per_game_se']=stat['se']
        summary.append(row)
        for day in range(6,29):
            rr=[r for r in perday if r['kind']==kind and r['day']==day]
            for key in ('overrides','jobs','successes','failed_cost_proxy'):daily.append(dict(kind=kind,day=day,metric=key,**stats([(r['seed'],r['seat'],r[key]) for r in rr])))
    write('GUARD_SUMMARY',summary);write('GUARD_DAILY',daily);return dict(games=games,summary=summary)


def main():
    data,summary=general();summary['guard']=guard();(OUT/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary),flush=True)

if __name__=='__main__':main()

"""Report H's paired values, actual seed purchases, dawn stocks and planting effects."""
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
import subprocess
import duckdb
import pyarrow as pa
from nodawnseeds_bench import OUT,REPO,SOURCE,PLAYERS,CROPS,sha,signature,case_stem
from report_full import table,se


def main():
    preview=[json.loads(p.read_text()) for p in (OUT/'preview').glob('*.metrics.json')]
    full=[json.loads(p.read_text()) for p in (OUT/'full').glob('*.metrics.json')]
    assert {(m['game'],m['day'],m['turns'],m['player']) for m in preview}=={(g,d,t,n) for g in range(10301,10320) for d in (8,12,16,20,24) for t in (24,72) for n in PLAYERS}
    assert len(preview)==380 and len(full)==96
    assert {(m['game'],m['seat'],m['player']) for m in full}=={(g,s,n) for g in range(20001,20025) for s in (0,1) for n in PLAYERS}
    sig=signature();sources={g:sha(SOURCE/f'{g}.json') for g in range(10301,10320)}
    for m in preview+full:
        assert m['signature']==sig and m['native_check']['reason']=='kept' and m['seed_conservation']
        if 'source_sha256' in m:
            assert m['source_sha256']==sources[m['game']] and not m['policy_errors']['count']
            raw=OUT/'preview'/(case_stem(m['game'],m['day'],m['turns'],m['player'])+'.json.gz')
        else:raw=Path(m['file'])
        assert sha(raw)==m['replay_sha256']
    repeats=[json.loads(p.read_text()) for p in (OUT/'repeats').glob('*.metrics.json')];assert len(repeats)==4
    index={(m['game'],m['day'],m['turns'],m['player']):m for m in preview}
    assert {(m['game'],m['day'],m['turns'],m['player']) for m in repeats}=={(10301,8,t,n) for t in (24,72) for n in PLAYERS}
    for m in repeats:
        assert m['gameplay_sha256']==index[m['game'],m['day'],m['turns'],m['player']]['gameplay_sha256']
        assert sha(OUT/'repeats'/(case_stem(m['game'],m['day'],m['turns'],m['player'])+'.json.gz'))==m['replay_sha256']
    pairs=[]
    for game in range(10301,10320):
        for day in (8,12,16,20,24):
            for turns in (24,72):
                a,b=[index[game,day,turns,n] for n in PLAYERS]
                assert a['dawn'][0]['seeds']==b['dawn'][0]['seeds']
                values={'period_value_per_day':(a['period_value_plus_assets']/(turns/24),b['period_value_plus_assets']/(turns/24))}
                if turns==72:
                    values.update({f'daily_day_{i+1}':(a['daily_value_plus_assets'][i],b['daily_value_plus_assets'][i]) for i in range(3)})
                    values['mean_daily_value']=(statistics.mean(a['daily_value_plus_assets']),statistics.mean(b['daily_value_plus_assets']))
                for metric,(base,variant) in values.items():
                    pairs.append(dict(game=game,day=day,turns=turns,metric=metric,template=base,variant=variant,delta=variant-base))
    groups=defaultdict(list)
    for r in pairs:groups[r['turns'],r['metric']].append(r)
    values=[]
    for (turns,metric),rows in groups.items():
        bygame=defaultdict(list)
        for r in rows:bygame[r['game']].append(r)
        means={k:[statistics.mean(r[k] for r in rs) for rs in bygame.values()] for k in ('template','variant','delta')}
        values.append(dict(turns=turns,metric=metric,games=len(bygame),mornings=len(rows),**{q:v for k,x in means.items()
             for q,v in ((k,statistics.mean(x)),(k+'_game_se',se(x)))},delta_morning_se=se([r['delta'] for r in rows])))
    c=duckdb.connect();c.register('pairs',pa.Table.from_pylist(pairs));numeric=0
    for r in values:
        result=c.execute('''WITH g AS (SELECT game,avg(template) b,avg(variant) v,avg(delta) d FROM pairs WHERE turns=? AND metric=? GROUP BY game)
            SELECT avg(b),stddev_samp(b)/sqrt(count(*)),avg(v),stddev_samp(v)/sqrt(count(*)),avg(d),stddev_samp(d)/sqrt(count(*)) FROM g''',[r['turns'],r['metric']]).fetchone()
        for key,value in zip(('template','template_game_se','variant','variant_game_se','delta','delta_game_se'),result):
            assert abs(r[key]-value)<1e-7,(key,r[key],value);numeric+=1
        morning=c.execute('SELECT stddev_samp(delta)/sqrt(count(*)) FROM pairs WHERE turns=? AND metric=?',[r['turns'],r['metric']]).fetchone()[0]
        assert abs(r['delta_morning_se']-morning)<1e-7;numeric+=1
    purchases=[];stocks=[];plants=[]
    scopes=[('preview',24,[m for m in preview if m['turns']==24]),('preview',72,[m for m in preview if m['turns']==72]),('full',719,full)]
    forbidden=0
    for phase,turns,rows in scopes:
        byname={n:[m for m in rows if m['player']==n] for n in PLAYERS};n=len(byname[PLAYERS[0]])
        assert n==len(byname[PLAYERS[1]])
        total={name:defaultdict(int) for name in PLAYERS}
        for name,ms in byname.items():
            for m in ms:
                for r in m['buys']:total[name][r['crop'],r['hour']]+=r['units']
        for crop in CROPS:
            for hour in range(24):
                a,b=[total[name][crop,hour] for name in PLAYERS]
                purchases.append(dict(phase=phase,turns=turns,crop=crop,hour=hour,cases=n,template_units=a,variant_units=b,
                    template_mean=a/n,variant_mean=b/n,mean_delta=(b-a)/n))
                if crop in ('WHEAT','CARROT') and hour<3:forbidden+=b
        rels=sorted({d['relative_day'] for m in rows for d in m['dawn']})
        for relative in rels:
            dawn={name:[d for m in ms for d in m['dawn'] if d['relative_day']==relative] for name,ms in byname.items()}
            for crop in CROPS:
                a,b=[dawn[name] for name in PLAYERS]
                assert len(a)==len(b)==n
                stocks.append(dict(phase=phase,turns=turns,relative_day=relative,crop=crop,cases=n,
                    template_stock=statistics.mean(d['seeds'][crop] for d in a),variant_stock=statistics.mean(d['seeds'][crop] for d in b),
                    template_zero_fraction=sum(d['seeds'][crop]==0 for d in a)/len(a),variant_zero_fraction=sum(d['seeds'][crop]==0 for d in b)/len(b),
                    template_empty=statistics.mean(d['empty'] for d in a),variant_empty=statistics.mean(d['empty'] for d in b)))
        for crop in (*CROPS,'ALL'):
            selected=CROPS if crop=='ALL' else (crop,)
            data={name:{k:statistics.mean(sum(m[k].get(c,0) for c in selected) for m in ms)
                  for k in ('planted','plant_attempts','zero_stock_plant_noops')} for name,ms in byname.items()}
            plants.append(dict(phase=phase,turns=turns,crop=crop,cases=n,**{name.split(':')[-1]+'_'+k:v for name,ds in data.items() for k,v in ds.items()}))
    assert forbidden==0
    baseline=lambda path:subprocess.check_output(['git','show','7578430:'+path],cwd=REPO,encoding='utf8')
    assert (REPO/'vendor/template_agent/main.py').read_text()==baseline('vendor/template_agent/main.py')
    registration='    if name == "template:nodawnseeds":\n        return TemplatePlayer(Path(__file__).resolve().parents[1] / "agents/template_switches/main.py")\n'
    assert (REPO/'tools/compare_day.py').read_text().replace(registration,'')==baseline('tools/compare_day.py')
    check=dict(preview_cases=len(preview),full_native_cases=len(full),smoke_exact_repeats=len(repeats),test_games_opened=0,
        native_frames=sum(m['native_check']['frames'] for m in preview+full),seed_conservation_cases=len(preview)+len(full),
        forbidden_seed_purchases=forbidden,independent_sql_numeric_checks=numeric,unchanged_template_matches_G=True,signature=sig)
    for name,rows in [('PREVIEW',values),('PREVIEW_PAIRED',pairs),('PURCHASES',purchases),('STOCKS',stocks),('PLANTS',plants)]:
        table(REPO/'reports'/f'NODAWNSEEDS_{name}.csv',rows)
    (REPO/'reports/NODAWNSEEDS_CHECKS.json').write_text(json.dumps(check,indent=2)+'\n')
    print(json.dumps({'values':values,'checks':check,'plants_all':[r for r in plants if r['crop']=='ALL'],
        'seed_totals':[{**{k:r[k] for k in ('phase','turns','crop')},'template':sum(x['template_mean'] for x in purchases if all(x[k]==r[k] for k in ('phase','turns','crop'))),
        'variant':sum(x['variant_mean'] for x in purchases if all(x[k]==r[k] for k in ('phase','turns','crop')))} for r in purchases if r['hour']==0]},indent=2))


if __name__=='__main__':main()

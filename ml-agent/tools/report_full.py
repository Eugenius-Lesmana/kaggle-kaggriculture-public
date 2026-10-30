"""Summarise only audited full games, pairing both seats within each seed.
python tools/report_full.py TAG --prefix FULLGAMES [--baseline-tag TAG]
"""
import argparse
from collections import defaultdict
import csv
import json
from pathlib import Path
import statistics
from run_full import ROOT, runs, save


def se(xs):
    return statistics.stdev(xs)/len(xs)**0.5 if len(xs)>1 else None


def table(path, rows):
    with path.open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)


def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('tag');ap.add_argument('--prefix',default='FULLGAMES')
    ap.add_argument('--baseline-tag');a=ap.parse_args()
    root=runs()/a.tag
    checks=json.loads((root/'checks.json').read_text())
    config=json.loads((root/'config.json').read_text())
    rows=[json.loads(p.read_text()) for p in root.glob('*.metrics.json')]
    assert checks['accepted']==len(rows) and checks['rejected']==0
    if a.baseline_tag:
        base=runs()/a.baseline_tag
        assert json.loads((base/'checks.json').read_text())['rejected']==0
        rows += [json.loads(p.read_text()) for p in base.glob('template-*.metrics.json')]
    keys={(r['name'],r['seed'],r['seat']) for r in rows}
    names=list(dict.fromkeys(r['name'] for r in rows))
    assert len(keys)==len(rows)
    assert keys=={(n,s,p) for n in names for s in config['seeds'] for p in config['seats']}
    summary=[]
    for n in names:
        for buyers in ('all',0,1,2):
            for seat in ('all',0,1):
                group=[r for r in rows if r['name']==n and (buyers=='all' or r['buyers']==buyers) and (seat=='all' or r['seat']==seat)]
                if not group: continue
                paired=defaultdict(list)
                for r in group:paired[r['seed']].append(r)
                assert all(len(v)==(len(config['seats']) if seat=='all' else 1) for v in paired.values())
                means={key:[statistics.mean(r[key] if key=='margin' else r['banks'][0 if key=='bank' else 1] for r in rs) for rs in paired.values()]
                       for key in ('bank','opponent_bank','margin')}
                summary.append(dict(player=n,buyers=buyers,seat=seat,seeds=len(paired),games=len(group),
                    bank=statistics.mean(means['bank']),bank_seed_se=se(means['bank']),
                    opponent_bank=statistics.mean(means['opponent_bank']),opponent_bank_seed_se=se(means['opponent_bank']),
                    margin=statistics.mean(means['margin']),margin_seed_se=se(means['margin']),
                    bank_share=sum(r['banks'][0] for r in group)/sum(r['banks'][1] for r in group),
                    wins=sum(r['win'] for r in group),ties=sum(r['tie'] for r in group),paired_seed_wins=sum(m>0 for m in means['margin'])))
    baseline='template' if 'template' in names else names[0]
    index={(r['name'],r['seed'],r['seat']):r for r in rows}
    paired=[]
    for n in names:
        if n==baseline: continue
        for s in config['seeds']:
            for p in config['seats']:
                r,b=index[n,s,p],index[baseline,s,p]
                assert r['early_shops']==b['early_shops']
                paired.append(dict(player=n,baseline=baseline,seed=s,seat=p,buyers=r['buyers'],bank=r['banks'][0],baseline_bank=b['banks'][0],
                  bank_delta=r['banks'][0]-b['banks'][0],opponent_bank_delta=r['banks'][1]-b['banks'][1],margin_delta=r['margin']-b['margin']))
    differences=[]
    for n in names:
        if n==baseline: continue
        for buyers in ('all',0,1,2):
            for seat in ('all',0,1):
                group=[r for r in paired if r['player']==n and (buyers=='all' or r['buyers']==buyers) and (seat=='all' or r['seat']==seat)]
                if not group:continue
                seeds=defaultdict(list)
                for r in group:seeds[r['seed']].append(r)
                values={k:[statistics.mean(r[k] for r in rs) for rs in seeds.values()] for k in ('bank_delta','opponent_bank_delta','margin_delta')}
                differences.append(dict(player=n,baseline=baseline,buyers=buyers,seat=seat,seeds=len(seeds),games=len(group),
                    **{q:v for k,x in values.items() for q,v in ((k,statistics.mean(x)),(k+'_seed_se',se(x)))},
                    positive_seed_bank_deltas=sum(x>0 for x in values['bank_delta'])))
    speed=[]
    for n in names:
        group=[r for r in rows if r['name']==n]
        times=[t for r in group for t in r['timing']['turn_ms']]
        speed.append(dict(player=n,games=len(group),turns=len(times),median_ms=statistics.median(times),max_ms=max(times),over_1s=sum(t>1000 for t in times)))
    for label,data in [('SUMMARY',summary),('PAIRED',paired),('DELTAS',differences),('TIMING',speed)]:
        if data:table(ROOT/'reports'/f'{a.prefix}_{label}.csv',data)
    save(ROOT/'reports'/f'{a.prefix}_CHECKS.json',checks)
    print(json.dumps({'summary':[r for r in summary if r['buyers']=='all' and r['seat']=='all'],
                      'deltas':[r for r in differences if r['buyers']=='all' and r['seat']=='all'],'timing':speed},indent=2))


if __name__=='__main__':main()

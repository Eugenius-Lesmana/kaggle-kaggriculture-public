"""Conditional, input-pinned live confirmation. Uses unchanged run_full in this worktree."""
import argparse,hashlib,json,math,os,statistics,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'src'))
import run_full as F
from kagml.paths import data_root,runs,models
BASE='net:board-p5:market:overflow:endmask:endwork'
PLAYER=BASE+':mkt=market-gru-v1'
ORIGINAL_SIGNATURE=F.signature
EXPECTED='6a665ffecd0ce844a4037018fdb1117e459a61e328822283d4d37c71a97dc6fd'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def signature(player,opponent):
    original=ORIGINAL_SIGNATURE(player,opponent)
    if ':mkt=' not in player:return original
    name=player.split(':mkt=')[1].split(':')[0]
    return F.digest(dict(base=original,market={str(models()/name/n):sha(models()/name/n) for n in ('model.pt','calibration.json')},wrapper=sha(__file__)))
F.signature=signature

def paired(base,candidate):
    assert set(base)==set(candidate) and len(base)%2==0
    keys=sorted(base);seeds=sorted({k[0] for k in keys});assert all({k[1] for k in keys if k[0]==s}=={0,1} for s in seeds)
    out=dict(games=len(keys),seed_pairs=len(seeds))
    for name,fn in (('margin',lambda b,c:(c[0]-c[1])-(b[0]-b[1])),('our_bank',lambda b,c:c[0]-b[0]),('opponent_bank',lambda b,c:c[1]-b[1])):
        values=[statistics.mean(fn(base[s,p],candidate[s,p]) for p in (0,1)) for s in seeds]
        out[name]=dict(mean=statistics.mean(values),se=statistics.stdev(values)/math.sqrt(len(values)) if len(values)>1 else None,seed_means=values)
    for name,rows in (('baseline',base),('candidate',candidate)):
        out[name]=dict(share=sum(v[0] for v in rows.values())/sum(v[1] for v in rows.values()),wins=sum(v[0]>v[1] for v in rows.values()),ties=sum(v[0]==v[1] for v in rows.values()),our_mean_bank=statistics.mean(v[0] for v in rows.values()),opponent_mean_bank=statistics.mean(v[1] for v in rows.values()))
    assert abs(out['margin']['mean']-(out['our_bank']['mean']-out['opponent_bank']['mean']))<1e-8
    return out

def audit(tag,name,seeds,receipts):
    root=runs()/tag;config=json.loads((root/'config.json').read_text());assert config['players']==[name] and config['seeds']==seeds and config['seats']==[0,1]
    result={}
    for seed in seeds:
        for seat in (0,1):
            m=F.verify(root,name,seed,seat,config['signatures'][name]);result[seed,seat]=m['banks']
            p=Path(str(root/F.stem(name,seed,seat))+'.metrics.json');receipts[str(p)]=sha(p)
    for n,s,p in config['repeat_jobs']:
        m=F.verify(root/'repeats',n,s,p,config['signatures'][n]);old=json.loads(Path(str(root/F.stem(n,s,p))+'.metrics.json').read_text());assert m['gameplay_sha256']==old['gameplay_sha256']
    return result

def run(tag,seeds,opponent):
    sys.argv=['run_full.py',tag,'--players',PLAYER,'--opponent',opponent,'--seeds',str(seeds[0])+'-'+str(seeds[-1]),'--seats','0,1','--workers','3']
    F.main()
    sys.argv=['run_full.py',tag,'--audit'];F.main()

def main():
    ap=argparse.ArgumentParser(__doc__);ap.add_argument('--self-test',action='store_true');a=ap.parse_args()
    if a.self_test:
        b={(s,p):[100,100] for s in (1,2) for p in (0,1)};c={(s,p):[100+10*s,100+s] for s in (1,2) for p in (0,1)}
        z=paired(b,c);assert z['margin']['mean']==13.5 and abs(z['margin']['se']-4.5)<1e-9 and z['our_bank']['mean']==15
        print('Paired seed mean and SE checks passed');return
    assert os.environ.get('PYTHONHASHSEED')=='0'
    cache=ROOT/'.cache/market-train';proof=json.loads((ROOT/'reports/MARKET_TRAIN_ANALYSIS_CHECKS.json').read_text())
    assert proof['passed'] and proof['complete'] and proof['segments']==2590
    result=dict(passed=True,analysis_gate=proof['live_gate'],test_contents_read=0,evaluation_training_or_tuning=False,owned_game_worker_limit=3,comparisons={})
    target=ROOT/'reports/MARKET_TRAIN_LIVE_CHECKS.json'
    if not proof['live_gate']['passed']:
        result.update(status='skipped-analysis-regression',policy_games_started=0)
        F.save(target,result);print(json.dumps(dict(status=result['status'],reasons=proof['live_gate']['reasons'])));return
    opponent=str(data_root()/'opponents/fifth-place/nflow-main-wash8014/main.py')
    campaign=runs()/'market-train-20261030';campaign.mkdir(exist_ok=True)
    paths=list((ROOT/'src/kagml').glob('*.py'))+[ROOT/'tools/run_full.py',ROOT/'tools/compare_day.py',Path(__file__),Path(opponent),models()/'board-p5/model.pt',models()/'market-gru-v1/model.pt',models()/'market-gru-v1/calibration.json',ROOT/'reports/MARKET_TRAIN_ANALYSIS_GATE.json',ROOT/'reports/MARKET_TRAIN_ANALYSIS_CHECKS.json']
    paths+=list((ROOT/'vendor/template_agent').glob('*.py'))
    pins={str(p):sha(p) for p in paths}
    pin_path=campaign/'live-inputs.json'
    if pin_path.exists():assert json.loads(pin_path.read_text())==pins,'Live inputs changed; no automatic repin'
    else:F.save(pin_path,pins)
    def check():
        assert all(sha(p)==v for p,v in pins.items()),'Frozen live input changed'
    def status(phase):
        check();F.save(cache/'status.json',dict(phase=phase,pid=os.getpid(),time=time.time(),workers=3))
    receipts={};s1=list(range(20001,20025));s2=list(range(20025,20049))
    status('audit-baseline-first');b1=audit('nflow-p5-best',BASE,s1,receipts)
    gate=campaign/'default-gate';gate.mkdir(exist_ok=True);expected=F.signature(BASE,opponent)
    gate_metrics=Path(str(gate/F.stem(BASE,20001,0))+'.metrics.json')
    if not gate_metrics.exists():status('default-gate');F.one((str(gate),BASE,opponent,20001,0,expected))
    g=F.verify(gate,BASE,20001,0,expected);assert g['gameplay_sha256']==EXPECTED,'Default play changed'
    result['default_gate']=dict(passed=True,gameplay_sha256=g['gameplay_sha256'],signature=expected)
    status('live-first-48');run('nflow-p5-mkt1',s1,opponent);c1=audit('nflow-p5-mkt1',PLAYER,s1,receipts);first=paired(b1,c1);result['comparisons']['first24']=first
    F.save(campaign/'first-result.json',first);check()
    if first['margin']['mean']>0:
        status('audit-baseline-fresh');b2=audit('nflow-p5-best-s2',BASE,s2,receipts)
        status('live-fresh-48');run('nflow-p5-mkt1-s2',s2,opponent);c2=audit('nflow-p5-mkt1-s2',PLAYER,s2,receipts)
        fresh=paired(b2,c2);pooled=paired({**b1,**b2},{**c1,**c2});result['comparisons'].update(fresh24=fresh,pooled48=pooled)
        result.update(status='live-complete',keep=pooled['margin']['mean']>=2*pooled['margin']['se'] and fresh['margin']['mean']>0,policy_games_started=101,coverage='96 comparisons plus4 deterministic repeats and1 default gate')
    else:result.update(status='rejected-first-margin',keep=False,policy_games_started=51,coverage='48 comparisons plus2 deterministic repeats and1 default gate; fresh stage not authorized by nonpositive first estimate')
    check();assert all(sha(p)==v for p,v in receipts.items()),'Comparison receipt changed'
    result['receipt_sha256']=receipts;result['frozen_input_count']=len(pins);result['player']=PLAYER
    F.save(target,result);F.save(campaign/'complete.json',dict(passed=True,status=result['status'],keep=result['keep']))
    print(json.dumps(dict(status=result['status'],keep=result['keep'],comparisons=result['comparisons'])),flush=True)
if __name__=='__main__':main()

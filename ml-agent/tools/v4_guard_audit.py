"""Transparent guard logging; only the 8 preselected original games are re-played.
PYTHONHASHSEED=0 python tools/v4_guard_audit.py [--smoke] --workers 2
"""
import argparse
from concurrent.futures import ProcessPoolExecutor
import copy
import hashlib
import json
import os
from pathlib import Path
import time
from v4_diagnostics import ROOT,REPO,OUT,RT,sha,load,save,identity,gameplay
from kagml.net_player import NetPlayer
from kagml import net_player as NP
from kagml import board_features as B
from kagml import board_net as BN
from kagml.preview import pin_weeds
from run_full import StrictMeter,actor
from kaggle_environments import make


class LoggedNetPlayer(NetPlayer):
    def __init__(self):
        super().__init__('board-v4:guard');self.logs=[]

    def _apply_guard(self,obs,seat,commands):
        before=copy.deepcopy(commands);result=super()._apply_guard(obs,seat,commands)
        farm=obs['farms'][seat];pos=B.positions(farm);step=int(obs['day'])*24+int(obs['hour'])
        for u,(kind,cell) in self.guarding.items():
            x,y=cell;tile=copy.deepcopy(farm['tiles'][y][x])
            self.logs.append(dict(step=step,day=obs['day'],hour=obs['hour'],unit=u,kind=kind,x=x,y=y,position=list(pos[u]),network=before[u],guard=copy.deepcopy(result[u]),changed=before[u]!=result[u],identity=identity(tile),tile=tile,price=obs['market']['prices'][RT.K.ANIMALS[tile['animal']]['product'] if kind=='FEED' else tile['crop']]))
        assert all(a==b or any(r['step']==step and r['unit']==u and r['changed'] for r in self.logs[-len(self.guarding):]) for u,(a,b) in enumerate(zip(before,result)))
        return result


def signature():
    files=[Path(__file__),Path(NP.__file__),Path(B.__file__),Path(BN.__file__),REPO/'vendor/template_agent/main.py',ROOT/'models/board-v4/model.pt']
    return hashlib.sha256(b''.join(p.read_bytes() for p in files)).hexdigest()


def cost(tile,prices):
    if not isinstance(tile,dict):return (0,0)
    if tile.get('animal'):
        a=RT.K.ANIMALS[tile['animal']];return a['cost'],tile.get('yield_units',0)*prices[a['product']]
    if tile.get('kind')=='PLANT':return RT.K.CROPS[tile['crop']]['seed'],tile.get('yield_units',0)*prices[tile['crop']]
    return (0,0)


def summarize(c,logs,baseline):
    seat=c['seat'];episodes=[];active={};services=baseline['services'];rep=load(c['raw']);nights={r['day']:r for r in baseline['nights']}
    # Contiguous guard assignments; includes unchanged commands to measure the complete errand.
    for r in logs:
        key=(r['day'],r['unit'],r['kind'],r['x'],r['y'],tuple(r['identity']));last=active.get(key)
        if last is None or last['last_step']+1!=r['step']:
            last=dict(day=r['day'],unit=r['unit'],kind=r['kind'],x=r['x'],y=r['y'],identity=r['identity'],start_step=r['step'],last_step=r['step'],active_turns=0,overridden_turns=0,first_network=r['network'],first_guard=r['guard']);episodes.append(last);active[key]=last
        last['last_step']=r['step'];last['active_turns']+=1;last['overridden_turns']+=int(r['changed'])
    jobs={}
    for e in episodes:
        key=(e['day'],e['kind'],e['x'],e['y'],tuple(e['identity']));jobs.setdefault(key,[]).append(e)
    jobrows=[]
    for key,spells in jobs.items():
        day,kind,x,y,ident=key;start=min(e['start_step'] for e in spells);night=nights[day];tile=night['tiles'][seat][y][x]
        done=[r for r in services if r['seat']==seat and start<=r['step']<(day+1)*24 and r['kind']==kind and r['x']==x and r['y']==y and tuple(r['identity'] or [])==ident]
        served=bool(done);same=tuple(identity(tile) or [])==ident;flag='fed_today' if kind=='FEED' else 'watered_today';unserved_risk=same and not tile.get(flag,False) and tile.get('consecutive_unfed' if kind=='FEED' else 'consecutive_unwatered',0)>=1
        dawn=rep['steps'][(day+1)*24][0]['observation']['farms'][seat]['tiles'][y][x];night_loss=not served and unserved_risk and tuple(identity(dawn) or [])!=ident
        replacement,produce=cost(tile,night['prices']) if night_loss else (0,0)
        row=dict(day=day,kind=kind,x=x,y=y,identity=list(ident),start_step=start,assignments=len(spells),active_turns=sum(e['active_turns'] for e in spells),overridden_turns=sum(e['overridden_turns'] for e in spells),intervened=any(e['overridden_turns'] for e in spells),success=served,service_step=done[0]['step'] if done else None,service_unit=done[0]['unit'] if done else None,night_loss=bool(night_loss),target_removed=not served and not same,replacement_cost=replacement,held_produce_value=produce,failed_cost_proxy=replacement+produce)
        jobrows.append(row)
        for e in spells:
            e['success']=any(r['step']>=e['start_step'] for r in done);e['service_by_assigned_worker']=any(r['step']>=e['start_step'] and r['unit']==e['unit'] for r in done);e['night_loss']=bool(night_loss)
    return episodes,jobrows


def one(c):
    start=time.perf_counter();sig=signature();path=OUT/'guard'/f"{c['seed']}-seat{c['seat']}.json.gz"
    if path.exists():
        old=load(path)
        if old['signature']==sig and old['source']==c and old['gameplay_sha256']==json.loads(Path(c['metrics']).read_bytes())['gameplay_sha256']:return dict(seed=c['seed'],seat=c['seat'],seconds=old['seconds'],resumed=True)
    assert sha(c['raw'])==c['raw_sha256'] and sha(c['metrics'])==c['metrics_sha256'];rep=load(c['raw']);m=json.loads(Path(c['metrics']).read_bytes());seat=c['seat'];pin_weeds(True)
    ours=StrictMeter(LoggedNetPlayer());theirs=StrictMeter(actor(m['opponent'],c['seed']));env=make('kaggriculture',configuration={**rep['configuration'],'seed':rep['info']['seed']},debug=False)
    env.run([ours,theirs] if seat==0 else [theirs,ours]);new=env.toJSON()
    if gameplay(new)!=m['gameplay_sha256']:
        differences=[]
        for i,(a,b) in enumerate(zip(new['steps'],rep['steps'])):
            for p in (0,1):
                if a[p]['action']!=b[p]['action']:differences.append(dict(frame=i,seat=p,field='action',actual=a[p]['action'],expected=b[p]['action']))
                for field in ('farms','private','market','town','day','hour','player'):
                    if a[p]['observation'][field]!=b[p]['observation'][field]:differences.append(dict(frame=i,seat=p,field=field))
            if differences:break
        save(OUT/'guard/failures'/f"{c['seed']}-seat{seat}.json.gz",dict(source=c,differences=differences,new_hash=gameplay(new),expected_hash=m['gameplay_sha256'],replay=new))
        raise AssertionError(('logged replay changed',differences))
    assert gameplay(new)==gameplay(rep)==m['gameplay_sha256']
    assert ours.report()['turns']==theirs.report()['turns']==719 and not ours.errors and not theirs.errors
    baseline=load(OUT/'cases'/f"v4-{c['seed']}-seat{seat}.json.gz");episodes,jobs=summarize(c,ours.actor.logs,baseline)
    # Every changed command is exactly the command that was actually executed in the identical replay.
    for r in ours.actor.logs:
        action=new['steps'][r['step']+1][seat]['action'];command=action['farmer'] if r['unit']==0 else action['hands'][r['unit']-1];assert command==r['guard']
    value=dict(source=c,signature=sig,gameplay_sha256=gameplay(new),logs=ours.actor.logs,episodes=episodes,jobs=jobs,seconds=time.perf_counter()-start,ours_calls=719,opponent_calls=719)
    save(path,value);save(OUT/'guard/replays'/f"{c['seed']}-seat{seat}.json.gz",new);return dict(seed=c['seed'],seat=seat,seconds=value['seconds'],changed=sum(r['changed'] for r in value['logs']),jobs=len(jobs),resumed=False)


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--workers',type=int,choices=(1,2),default=2);p.add_argument('--smoke',action='store_true');a=p.parse_args();assert os.environ.get('PYTHONHASHSEED')=='0'
    cases=json.loads((OUT/'guard-selection.json').read_text());jobs=cases[:1] if a.smoke else cases;t=time.perf_counter()
    with ProcessPoolExecutor(max_workers=a.workers) as pool:results=list(pool.map(one,jobs))
    summary=dict(cases=len(jobs),seconds=time.perf_counter()-t,results=results,signature=signature());(OUT/f"guard-{'smoke' if a.smoke else 'full'}.json").write_text(RT.compact(summary));print(RT.compact(summary),flush=True)

if __name__=='__main__':main()

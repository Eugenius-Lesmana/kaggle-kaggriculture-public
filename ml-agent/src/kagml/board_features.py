"""Whole-board inputs and exact sequential command masks. No policy or weight dependency.
Call history.observe(current_obs, seat, previous_action) once, then encode(current_obs, seat, history).
"""
from collections import Counter
import copy
import numpy as np
import kaggle_environments.envs.kaggriculture.kaggriculture as K
from kagml.work_features import History as PriceHistory, PRODUCTS, CROPS, ANIMALS, daily_demand

SIZE=10
MAX_UNITS=14  # User-approved: existing labels include farmer + 13 hands.
STAY_TARGET=100
CROP_NAMES=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON')
ANIMAL_NAMES=('GOOSE','COW','SHEEP')
ITEMS=PRODUCTS+ANIMAL_NAMES
TILE_KINDS=('EMPTY','LOCKED','WEED',*CROP_NAMES,'COOP','PASTURE')
COMMANDS=(('PASS',),('NORTH',),('SOUTH',),('EAST',),('WEST',),
          ('WATER',),('HARVEST',),('FERTILIZE',),('DIG',),('BUILD_COOP',),('BUILD_PASTURE',),
          ('FEED',),('CARE',),('COLLECT_FERTILIZER',),
          *((('PLANT',c) for c in CROP_NAMES)),*((('PICKUP',i) for i in ITEMS)),('DROP',),
          *((('PLACE',i) for i in ITEMS)))
COMMAND_ID={c:i for i,c in enumerate(COMMANDS)}
MOVES={k:tuple(v) for k,v in K.FARMER_MOVES.items()}
APPLY=K._apply_unit_action
TILE_COLUMNS=('x','y','kind','animal','owned','age','next_production','held','max_held','held_fraction',
              'watered','dry_days','fertilizer_days','fed','cared','unfed_days','care_bonus','fertilizer_available',
              'rot_in','ongoing','first_yield_day','production_interval','n_dies_tonight','n_prod_tonight',
              'n_double_tonight','n_escapes_tonight','n_full','n_loss_if_dry','n_loss_if_unfed','seed_cost','animal_cost')
UNIT_COLUMNS=('x','y','is_farmer',*('bag_'+i.lower() for i in ITEMS),'last_move_dx','last_move_dy','since_last_job','last_job_command')
PRICE_COLUMNS=('price','market_stock','price_dawn','price_high_today','price_low_today','price_change_4h','relative_price','daily_demand')
GLOBAL_COLUMNS=('day','hour','turns_left_game','turns_left_day','days_left','cash','opp_cash','cash_gap','hires_today','land_count','hands','shed_total',
                *('land_'+q.lower() for q in ('NW','NE','SW','SE')),*('shed_'+i.lower() for i in ITEMS),
                *('seeds_'+c.lower() for c in CROP_NAMES),*(f'{p.lower()}_{f}' for p in PRODUCTS for f in PRICE_COLUMNS),
                *('opp_crop_'+c.lower() for c in CROP_NAMES),*('opp_animal_'+a.lower() for a in ANIMAL_NAMES),
                *('shop_'+s.lower() for s in K.SHOPS))


def command_id(command):
    if not isinstance(command,list) or not command:raise ValueError('empty/non-list worker command')
    key=tuple(command[:2] if command[0] in ('PLANT','PICKUP','PLACE') else command[:1])
    if key not in COMMAND_ID:raise ValueError(f'unknown command: {command}')
    if len(command)>3:raise ValueError(f'too many command arguments: {command}')
    return COMMAND_ID[key]


def decode(index,amount=1,argc=None):
    command=list(COMMANDS[int(index)])
    if command[0] in ('PICKUP','PLACE') and (argc is None or argc>=3):command.append(int(amount))
    return command


def positions(farm):return [farm['farmer'],*farm['hands']]


def unit_snapshot(farm,private,unit):
    p=K._farmer_position(farm,unit)
    if p is None:return None
    tile=farm['tiles'][p[1]][p[0]]
    return (tuple(p),dict(tile) if isinstance(tile,dict) else tile,dict(private['inventories'][unit]),dict(private['shed']),dict(private['seeds']))


def apply(farm,private,unit,command,day):
    before=unit_snapshot(farm,private,unit)
    APPLY(farm,private,unit,command,SIZE,day,24,100)
    return before!=unit_snapshot(farm,private,unit)


def after_earlier(obs,seat,unit,earlier):
    if len(earlier)!=unit:raise ValueError('earlier must contain exactly units 0..unit-1')
    farm,private=copy.deepcopy((obs['farms'][seat],obs['private']))
    for i,command in enumerate(earlier):apply(farm,private,i,command,int(obs['day']))
    return farm,private


def mask_for_state(farm,private,unit,day):
    out=np.zeros(len(COMMANDS),dtype=np.bool_);pos=K._farmer_position(farm,unit)
    if pos is None:return out
    x,y=pos;tile=farm['tiles'][y][x];bag=private['inventories'][unit];shed=private['shed']
    at_shed=K._is_shed_adjacent((x,y),SIZE);animal=isinstance(tile,dict) and 'animal' in tile
    plant=isinstance(tile,dict) and tile.get('kind')=='PLANT';room=sum(shed.values())<100
    for i,command in enumerate(COMMANDS):
        op=command[0];item=command[1] if len(command)>1 else None
        if op=='PASS':ok=True  # Valid intentional no-op; separate from took_effect.
        elif op in MOVES:
            dx,dy=MOVES[op];ok=0<=x+dx<SIZE and 0<=y+dy<SIZE
        elif op=='DROP':ok=at_shed and bool(bag)  # Native DROP also removes zero keys and discards overflow.
        elif op=='PICKUP':ok=at_shed and shed.get(item,0)>0
        elif op=='PLACE':
            match=item in ANIMALS and isinstance(tile,dict) and tile.get('kind')==ANIMALS[item]['structure'] and 'animal' not in tile
            ok=bag.get(item,0)>0 and (match or (at_shed and room))
        elif tile=='LOCKED':ok=False
        elif op=='PLANT':ok=tile is None and private['seeds'].get(item,0)>0
        elif op in ('BUILD_COOP','BUILD_PASTURE'):ok=tile is None
        elif op=='WATER':ok=plant and not tile.get('watered_today',False)
        elif op=='HARVEST':ok=isinstance(tile,dict) and tile.get('yield_units',0)>0 and (animal or (plant and day-tile['planted_day']>=CROPS[tile['crop']]['first_yield_day']))
        elif op=='FERTILIZE':ok=plant and bag.get('FERTILIZER',0)>0
        elif op=='DIG':ok=tile is not None and not animal
        elif op=='FEED':ok=animal and not tile.get('fed_today',False) and bag.get('WHEAT',0)>0
        elif op=='CARE':ok=animal and not tile.get('cared_today',False)
        elif op=='COLLECT_FERTILIZER':ok=animal and tile.get('fertilizer_available',False)
        else:raise AssertionError(op)
        out[i]=bool(ok)
    return out


def legal(obs,seat,unit,earlier):
    """Native effect legality after earlier actual commands; PASS is an intentional no-op exception."""
    farm,private=after_earlier(obs,seat,unit,earlier)
    return mask_for_state(farm,private,unit,int(obs['day']))


def amount_applies(farm,unit,command):
    if command[0]=='PICKUP':return True
    if command[0]!='PLACE':return False
    p=K._farmer_position(farm,unit)
    if p is None:return False
    tile=farm['tiles'][p[1]][p[0]];item=command[1]
    animal_place=item in ANIMALS and isinstance(tile,dict) and tile.get('kind')==ANIMALS[item]['structure'] and 'animal' not in tile
    return K._is_shed_adjacent(tuple(p),SIZE) and not animal_place


class History(PriceHistory):
    """PriceHistory plus own observable unit memory. observe() once per pre-action observation."""
    def __init__(self,price_history=None):
        super().__init__()
        if price_history is not None:
            for key in ('prices','inventory','our_sold','positions'):setattr(self,key,copy.deepcopy(getattr(price_history,key)))
        self.last_obs=None;self.last_step=None;self.last_job={};self.last_move={}

    def observe(self,obs,seat,previous_action=None,sold=None):
        step=int(obs['day'])*24+int(obs['hour'])
        if self.last_step is not None and step!=self.last_step+1:raise ValueError('observations must advance exactly one turn')
        if int(obs.get('player',seat))!=seat:raise ValueError('observation player disagrees with seat')
        if obs['hour']==0:self.last_job.clear();self.last_move.clear()
        elif self.last_obs is not None:
            farm,private=copy.deepcopy((self.last_obs['farms'][seat],self.last_obs['private']))
            action=previous_action or {};commands=[action.get('farmer',['PASS']),*action.get('hands',[])]
            oldpos=positions(farm);newpos=positions(obs['farms'][seat])
            for unit in range(len(oldpos)):
                command=commands[unit] if unit<len(commands) else ['PASS']
                effective=apply(farm,private,unit,command,self.last_obs['day'])
                if effective and command[0] not in (*MOVES,'PASS'):self.last_job[unit]=(self.last_step,command_id(command))
                if unit<len(newpos) and command[0] in MOVES:
                    dx=newpos[unit][0]-oldpos[unit][0];dy=newpos[unit][1]-oldpos[unit][1]
                    if abs(dx)+abs(dy)==1:self.last_move[unit]=(dx,dy)
        if sold is None:
            sold=Counter({o[1]:int(o[2]) for o in (previous_action or {}).get('market',[]) if o and o[0]=='SELL' and len(o)>2})
        super().add(obs,sold)
        self.last_obs=copy.deepcopy(obs);self.last_step=step


def tile_values(tile,x,y,day,step,prices):
    row=dict.fromkeys(TILE_COLUMNS,0);row.update(x=x,y=y,owned=int(tile!='LOCKED'),next_production=-1,rot_in=999)
    if tile is None:kind='EMPTY'
    elif isinstance(tile,str):kind=tile
    else:kind=tile['crop'] if tile.get('kind')=='PLANT' else tile['kind']
    row['kind']=TILE_KINDS.index(kind)
    if isinstance(tile,dict) and tile.get('kind')=='PLANT':
        c=CROPS[tile['crop']];age=day-tile['planted_day'];held=tile.get('yield_units',0);price=prices[tile['crop']]
        dry=not tile.get('watered_today',False);dies=dry and tile.get('consecutive_unwatered',0)>=1
        ds=day+1-tile['planted_day']-c['first_yield_day']
        prod=bool(c['ongoing'] and ds>=0 and ds%c['interval']==0 and ds//c['interval']+1<=c['max_yield'])
        fert=tile.get('fertilized_until_day',-1)>=day
        row.update(age=age,next_production=(c['first_yield_day']-age) if age<c['first_yield_day'] else ((age-c['first_yield_day'])%c['interval'] if c['ongoing'] else 0),
            held=held,max_held=c['max_yield'],held_fraction=held/c['max_yield'],watered=int(not dry),dry_days=tile.get('consecutive_unwatered',0),
            fertilizer_days=max(0,tile.get('fertilized_until_day',-1)-day+1),rot_in=tile['max_lifespan_step']-step if tile.get('max_lifespan_step',-1)>0 else 999,
            ongoing=int(c['ongoing']),first_yield_day=c['first_yield_day'],production_interval=c['interval'],seed_cost=c['seed'],
            n_dies_tonight=int(dies),n_prod_tonight=int(prod),n_double_tonight=int(prod and fert),
            n_loss_if_dry=held*price+c['seed']+(c['max_yield']-held)*price if dies else (price*(2 if fert else 1) if dry and prod else 0))
    elif isinstance(tile,dict) and 'animal' in tile:
        a=ANIMALS[tile['animal']];since=day+1-tile['placed_day']-a['first_yield_day'];tonight=since>=0 and since%a['interval']==0
        unfed=not tile.get('fed_today',False);escapes=unfed and tile.get('consecutive_unfed',0)>=1;held=tile.get('yield_units',0);price=prices[a['product']]
        row.update(animal=ANIMAL_NAMES.index(tile['animal'])+1,age=day-tile['placed_day'],next_production=0 if tonight else (-since if since<0 else a['interval']-since%a['interval']),
            held=held,max_held=a['max_held'],held_fraction=held/a['max_held'],fed=int(not unfed),cared=int(tile.get('cared_today',False)),unfed_days=tile.get('consecutive_unfed',0),
            care_bonus=tile.get('pending_care_bonus',0),fertilizer_available=int(tile.get('fertilizer_available',False)),first_yield_day=a['first_yield_day'],production_interval=a['interval'],animal_cost=a['cost'],
            n_prod_tonight=int(tonight),n_escapes_tonight=int(escapes),n_full=int(held>=a['max_held']),
            n_loss_if_unfed=a['cost']+held*price if escapes else (price*(1+tile.get('pending_care_bonus',0)) if unfed and tonight else 0))
    return row


def encode(obs,seat,history):
    farm=obs['farms'][seat];private=obs['private'];day=int(obs['day']);hour=int(obs['hour']);step=day*24+hour;pos=positions(farm)
    if len(farm['tiles'])!=SIZE or any(len(row)!=SIZE for row in farm['tiles']):raise ValueError('encoder requires a 10x10 board')
    if len(pos)>MAX_UNITS or len(private['inventories'])<len(pos):raise ValueError('unit count/inventory shape is unsupported')
    prices=obs['market']['prices']
    tiles=np.asarray([[v[k] for k in TILE_COLUMNS] for y,row in enumerate(farm['tiles']) for x,t in enumerate(row) for v in [tile_values(t,x,y,day,step,prices)]],dtype=np.float32)
    units=np.zeros((MAX_UNITS,len(UNIT_COLUMNS)),dtype=np.float32);unit_mask=np.zeros(MAX_UNITS,dtype=np.bool_)
    for u,p in enumerate(pos):
        last=getattr(history,'last_job',{}).get(u);move=getattr(history,'last_move',{}).get(u,(0,0))
        units[u]=[*p,int(u==0),*(private['inventories'][u].get(i,0) for i in ITEMS),*move,step-last[0] if last else 999,last[1] if last else -1];unit_mask[u]=True
    glob=dict(day=day,hour=hour,turns_left_game=719-step,turns_left_day=24-hour,days_left=29-day,cash=farm['money'],opp_cash=obs['farms'][1-seat]['money'],cash_gap=farm['money']-obs['farms'][1-seat]['money'],
              hires_today=farm['hires_today'],land_count=len(farm['unlocked_quadrants']),hands=len(farm['hands']),shed_total=sum(private['shed'].values()))
    glob.update({'land_'+q.lower():int(q in farm['unlocked_quadrants']) for q in ('NW','NE','SW','SE')})
    glob.update({'shed_'+i.lower():private['shed'].get(i,0) for i in ITEMS});glob.update({'seeds_'+c.lower():private['seeds'].get(c,0) for c in CROP_NAMES})
    seen=history.prices if history is not None else [];dawn=seen[max(0,len(seen)-1-hour)] if seen else prices;today=seen[max(0,len(seen)-1-hour):] or [prices]
    demand=daily_demand(obs['town']['unlocked_shops'])
    for item in PRODUCTS:
        values=(prices[item],obs['market']['inventory'][item],dawn[item],max(s[item] for s in today),min(s[item] for s in today),prices[item]-(seen[-5][item] if len(seen)>=5 else prices[item]),prices[item]/K.MARKET_PARAMS[item]['base'],demand[item])
        glob.update({item.lower()+'_'+k:v for k,v in zip(PRICE_COLUMNS,values)})
    opp=[t for row in obs['farms'][1-seat]['tiles'] for t in row if isinstance(t,dict)]
    glob.update({'opp_crop_'+c.lower():sum(t.get('crop')==c for t in opp) for c in CROP_NAMES});glob.update({'opp_animal_'+a.lower():sum(t.get('animal')==a for t in opp) for a in ANIMAL_NAMES})
    glob.update({'shop_'+s.lower():obs['town']['unlocked_shops'].count(s) for s in K.SHOPS})
    return dict(tiles=tiles,units=units,glob=np.asarray([glob[k] for k in GLOBAL_COLUMNS],dtype=np.float32),unit_mask=unit_mask)

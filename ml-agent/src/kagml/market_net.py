"""Independent market model and causal public/own-action history. Opt-in only."""
from collections import deque
import copy
import hashlib
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn

PRODUCTS=('WHEAT','CARROT','TOMATO','STRAWBERRY','MELON','EGG','MILK','WOOL','FERTILIZER')
CROPS=PRODUCTS[:5];ANIMALS=('GOOSE','COW','SHEEP');ITEMS=PRODUCTS+ANIMALS
TOKENS=tuple([('SELL',p) for p in PRODUCTS]+[('BUY_SEED',p) for p in CROPS]+[('BUY_ANIMAL',a) for a in ANIMALS]+[('BUY_PRODUCT',p) for p in PRODUCTS]+[('BUY_LAND',),('HIRE',)])
TOKEN_ID={v:i for i,v in enumerate(TOKENS)}
HISTORY_FEATURES=65;CURRENT_FEATURES=148;VERSION='market-history-v1'

def issued_orders(action):
    result=np.zeros(28,np.float32)
    for order in (action or {}).get('market',[]) or []:
        if not isinstance(order,(tuple,list)) or not order:continue
        key=tuple(order[:1] if order[0] in ('HIRE','BUY_LAND') else order[:2])
        if key not in TOKEN_ID:continue
        try:n=1 if len(key)==1 else max(0,int(order[2]))
        except (IndexError,ValueError,TypeError):continue
        result[TOKEN_ID[key]]+=n
    return result

def current_extras(obs,seat):
    bags=[sum(b.get(item,0) for b in obs['private']['inventories']) for item in ITEMS]
    step=int(obs['day'])*24+int(obs['hour']);phase=[float(step%4==p) for p in range(4)]
    held=dict.fromkeys(PRODUCTS,0)
    for row in obs['farms'][1-seat]['tiles']:
        for tile in row:
            if not isinstance(tile,dict):continue
            product=tile.get('crop') or {'GOOSE':'EGG','COW':'MILK','SHEEP':'WOOL'}.get(tile.get('animal'))
            if product in held:held[product]+=tile.get('yield_units',0)
    return np.asarray(bags+phase+[float(obs['hour']>=22),float(obs['day']>=28)]+[held[p] for p in PRODUCTS],np.float32)

class MarketHistory:
    def __init__(self):
        self.rows=deque(maxlen=24);self.last_step=None;self.last_prices=None;self.last_stock=None;self.extra=None
    def observe(self,obs,seat,previous_action=None):
        step=int(obs['day'])*24+int(obs['hour'])
        if self.last_step is not None and step!=self.last_step+1:raise ValueError('market history must advance exactly one physical step')
        prices=np.asarray([obs['market']['prices'][p] for p in PRODUCTS],np.float32);stock=np.asarray([obs['market']['inventory'][p] for p in PRODUCTS],np.float32)
        if not np.isfinite(prices).all() or not np.isfinite(stock).all():raise ValueError('nonfinite public market state')
        if self.last_step is not None:
            own=issued_orders(previous_action)
            censored=(self.last_prices<=1)|(prices<=1)|(self.last_stock<=0)|(stock<=0)|(own[17:26]>0)
            if previous_action is None:censored[:]=True
            self.rows.append(np.concatenate([self.last_prices,self.last_stock,own,stock-self.last_stock,censored.astype(np.float32),np.ones(1,np.float32)]))
        self.last_step=step;self.last_prices=prices;self.last_stock=stock;self.extra=current_extras(obs,seat)
    def sequence(self):
        result=np.zeros((24,HISTORY_FEATURES),np.float32)
        if self.rows:result[-len(self.rows):]=np.stack(self.rows)
        return result
    def features(self,glob):
        if self.extra is None:raise ValueError('observe before requesting market features')
        current=np.concatenate([np.asarray(glob,np.float32),self.extra])
        if current.shape!=(CURRENT_FEATURES,) or not np.isfinite(current).all():raise ValueError('invalid current market features')
        return self.sequence(),current

class MarketNet(nn.Module):
    def __init__(self,hidden=64):
        super().__init__();self.hidden=hidden
        self.register_buffer('history_mean',torch.zeros(HISTORY_FEATURES));self.register_buffer('history_std',torch.ones(HISTORY_FEATURES));self.register_buffer('current_mean',torch.zeros(CURRENT_FEATURES));self.register_buffer('current_std',torch.ones(CURRENT_FEATURES))
        self.history=nn.GRU(HISTORY_FEATURES,hidden,batch_first=True);self.current=nn.Sequential(nn.Linear(CURRENT_FEATURES,hidden),nn.GELU());self.head=nn.Sequential(nn.Linear(hidden*2,hidden*2),nn.GELU(),nn.Linear(hidden*2,28*11))
    def forward(self,history,current):
        valid=history[:,:,-1:];h=((history-self.history_mean)/self.history_std).clamp(-8,8)*valid;h[:,:,-1:]=valid
        _,last=self.history(h);now=((current-self.current_mean)/self.current_std).clamp(-8,8)
        return self.head(torch.cat([last[-1],self.current(now)],-1)).view(-1,28,11)

def save_model(path,model,metadata):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);temporary=path.with_suffix('.tmp')
    torch.save(dict(kind=VERSION,hidden=model.hidden,state=model.state_dict(),metadata=metadata),temporary);temporary.replace(path)

def load_model(path,device='cpu'):
    checkpoint=torch.load(path,map_location=device,weights_only=True)
    if checkpoint.get('kind')!=VERSION:raise ValueError('unsupported market checkpoint')
    model=MarketNet(checkpoint['hidden']).to(device);model.load_state_dict(checkpoint['state']);return model.eval(),checkpoint['metadata']

class MarketPolicy:
    def __init__(self,model,bias=None):
        self.model=model.eval();self.bias=torch.as_tensor(bias if bias is not None else [0.0]*28,dtype=torch.float32);self.history=MarketHistory()
        if self.bias.shape!=(28,) or not torch.isfinite(self.bias).all():raise ValueError('invalid market calibration')
    @classmethod
    def load(cls,name):
        if not name or name in ('.','..') or Path(name).name!=name or ':' in name:raise ValueError('market model must be a model-directory name')
        from kagml.paths import models
        directory=models()/name;model,metadata=load_model(directory/'model.pt')
        if metadata.get('smoke_only'):raise ValueError('smoke-only model cannot be used for play')
        calibration=json.loads((directory/'calibration.json').read_text())
        if calibration.get('split')!='analysis2':raise ValueError('market calibration must come from analysis2')
        if calibration.get('model_sha256')!=hashlib.sha256((directory/'model.pt').read_bytes()).hexdigest():raise ValueError('calibration does not match market weights')
        return cls(model,calibration['bias'])
    @torch.inference_mode()
    def logits(self,glob):
        h,x=self.history.features(glob);out=self.model(torch.from_numpy(h).unsqueeze(0),torch.from_numpy(x).unsqueeze(0))[0].float();out[:,0]+=self.bias
        out[18:25,1:]=-torch.inf
        return out
    def memory(self):return copy.deepcopy(self.history)
    def restore(self,memory):self.history=copy.deepcopy(memory)

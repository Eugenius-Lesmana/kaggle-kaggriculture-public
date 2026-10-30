"""Independent exhaustive timing schedules and native auctions at the exact price-floor boundary."""
import itertools
from types import SimpleNamespace as NS
import sale_timing_bound as T

def main():
 K=T.engine().K;checks=0
 for p in ('WHEAT','FERTILIZER'):
  lo=K.MARKET_PARAMS[p]['I0'];hi=lo+1024
  while K.market_price(p,hi)>1:hi*=2
  while lo<hi:
   mid=(lo+hi)//2
   if K.market_price(p,mid)>1:lo=mid+1
   else:hi=mid
  floor=lo;price=lambda i:K.market_price(p,i)
  for seat,start in itertools.product((0,1),(floor-1,floor,floor+1)):
   m=K._new_market();m['inventory'][p]=start;farms=[{'money':10**9} for _ in (0,1)];priv=[{'shed':{}} for _ in (0,1)];priv[seat]['shed'][p]=3
   states=[NS(observation=NS(market=m,farms=farms,private=priv[z]),action={'market':[]}) for z in (0,1)];states[seat].action['market']=[['SELL',p,3]];states[1-seat].action['market']=[['BUY_PRODUCT',p,4]]
   K._process_market(states,NS(configuration=NS(boardSize=10,maxMarketOrdersPerTurn=10,shedCapacity=10000)))
   revenue,end=T.transition(start,3,0,4,-1,price);assert revenue==farms[seat]['money']-10**9 and end==m['inventory'][p] and T.curve(start,3,4,-1,price)[3]==revenue;checks+=1
  for Q in range(1,6):
   turns=[dict(step=i,before_available=c,candidates=[dict(slot=z,available=c,curve=T.curve(floor+z-1,Q,4,-1,price)) for z in (0,1)]) for i,c in enumerate((2,1,Q))]
   for stock in (True,False):
    brute=T.NEG
    for qs in itertools.product(range(Q+1),repeat=3):
     if sum(qs)!=Q:continue
     for slots in itertools.product((0,1),repeat=3):
      x=0;r=0;ok=True
      for t,q,z in zip(turns,qs,slots):
       if stock and x+q>t['before_available']:ok=False;break
       r+=int(t['candidates'][z]['curve'][q]);x+=q
      if ok:brute=max(brute,r)
    assert T.solve(turns,Q,stock)[0]==brute;checks+=1
 print({'passed':True,'additional_exact_floor_and_declining_stock_checks':checks,'new_policy_games':0})
if __name__=='__main__':main()
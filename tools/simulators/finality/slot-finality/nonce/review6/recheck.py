import numpy as np
X=[1,5,10,15,20,25,30,100/3]
G={'m10':[0.039,0.098,0.159,0.229,0.322,0.461,0.698,0.962],
   'm15':[0.041,0.103,0.168,0.245,0.352,0.520,0.821,1.173],
   'ceil':[30.2,13.2,9.3,7.6,6.5,5.8,5.3,5.0]}
def g(s,k): return float(np.interp(s*100,X,G[k]))/100
EPY=365.25*86400/648000
print('epochs/yr',EPY, 365*86400/648000)
blocks={20:4379,25:5469,30:6557,100/3:7282}
for s,b in blocks.items():
    print(s, 'yr blocks',round(b*EPY), [round(b*EPY*g(s/100,k)) for k in('m10','m15')], [round(b*48.7*g(s/100,k)) for k in('m10','m15')])
def run(s0,k,y,n,epy=48.7):
    # explicit stake accounting, not the closed recurrence
    S=s0;H=1-s0;rho=y/epy
    for _ in range(n):
        s=S/(S+H); S,H=S*(1+rho*(1+g(s,k))),H*(1+rho)
    return 100*S/(S+H)
for y,ks in((0.0133,('m10','m15','ceil')),(0.10,('ceil',))):
  for k in ks:
    for s0 in (.2,.25,.3,1/3):
        print(y,k,round(100*s0,2),'%.3f %.3f'%(run(s0,k,y,487),run(s0,k,y,2435)))
# variant: fixed total blocks (grinding takes blocks from honest): honest get (1-s(1+g))/(1-s)
def run2(s0,k,y,n,epy=48.7):
    s=s0;rho=y/epy
    for _ in range(n):
        w=s*(1+g(s,k)); R=rho # total reward as fraction of total stake
        s=(s+R*w)/(1+R)
    return 100*s
print('fixed-total variant')
for y,k in((0.0133,'m15'),(0.0133,'ceil'),(0.10,'ceil')):
    for s0 in(.3,1/3): print(y,k,'%.3f %.3f'%(run2(s0,k,y,487),run2(s0,k,y,2435)))
# variant: reward fixed in tokens per block (yield falls as stake grows)
def run3(s0,k,y,n,epy=48.7):
    S=s0;H=1-s0;r=y/epy
    for _ in range(n):
        s=S/(S+H); S,H=S+r*s*(1+g(s,k)),H+r*(1-s)
    return 100*S/(S+H)
print('fixed-token variant')
for y,k in((0.0133,'m15'),(0.0133,'ceil'),(0.10,'ceil')):
    for s0 in(.3,1/3): print(y,k,'%.3f %.3f'%(run3(s0,k,y,487),run3(s0,k,y,2435)))

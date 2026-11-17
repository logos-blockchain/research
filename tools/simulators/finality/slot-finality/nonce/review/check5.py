import sys, numpy as np
from scipy import stats, special
sys.path.insert(0,".")
from model import rates, open_after
a,_=rates(1/3)
for T in (18900, 36000, 51300):
    mean,sd=T*a,(T*a*(1-a))**0.5
    for z in (6,8,8.5,9,9.5,10):
        k=int(mean+z*sd)
        sf=stats.binom.sf(k,T,a); lc=stats.binom.logcdf(k,T,a)
        print(T,z,k,"sf=%.3e logcdf=%.3e  log1p(-sf)=%.3e  n*sf(2^64)=%.3e"%(sf,lc,np.log1p(-sf),sf*2.0**64))
# n=1 column of saved rows vs open_after
for tag,al,d in (("30_10",0.30,10),("30_15",0.30,15),("33_10",1/3,10)):
    r=np.load(f"attack_today_{tag}.npy"); print(tag,r.shape)
    ts=[900*i for i in (4,8,12,16,20,24)]
    o=open_after(al,d,ts)
    print("  n=1 saved:",["%.4e"%r[i-1,0] for i in (4,8,12,16,20,24)]); print("  open_after:",["%.4e"%x for x in o])
    # max pmf correct version for 2^64 at the reported crossing

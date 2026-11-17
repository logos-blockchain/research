import numpy as np
EPS=1e-9
def wait(tag, f):
    c=np.load(f"wait_curve_{tag}.npy"); hit=np.nonzero(c<=EPS/f)[0]; return (hit[0]+1)/3600 if hit.size else float('nan')
for tag in ("30_10","30_15","33_10","33_15"):
    c=np.load(f"wait_curve_{tag}.npy")
    print(tag, "size",c.size,"monotone",bool(np.all(np.diff(c)<=0)), "c[0]",c[0],"c[-1]",c[-1],
          "w(1)=%.3f w(1.21)=%.3f"%(wait(tag,1),wait(tag,1.21)), "absorb18=%.4g absorb10=%.4g"%(EPS/c[18*3600-1], EPS/c[10*3600-1]))
t="33_15"
for lab,f in (("1.171",1.171),("1.021",1.021)):
    print(lab, "squared", f*f, "wait %.3f"%wait(t,f*f), " unsquared wait %.3f"%wait(t,f))
pm=3.48e-4
for base in (1.171,1.021):
    F=base+1e4*pm; print("E=1e4 base",base,"F",F,"wait %.2f"%wait(t,F*F))
    # max machines for 18 h
    c=np.load("wait_curve_33_15.npy"); lim=(EPS/c[18*3600-1])**0.5
    print("  sqrt absorb",lim,"max E",(lim-base)/pm)
    lo,hi=0,10**7
    while hi-lo>1:
        m=(lo+hi)//2
        if wait(t,(base+m*pm)**2)<=18: lo=m
        else: hi=m
    print("  max E by wait<=18:",lo)
# recompute 3 cells of delayed_chain table 1 from the npz curves and from survival_table
z=np.load("delayed_chain_curves.npz")
import sys; sys.path.insert(0,".")
from model import clock
for tag,alpha,delta,hrs in (("33_15",1/3,15,2),("33_10",1/3,10,4),("30_15",0.30,15,3),("33_15",1/3,15,12),("33_15",1/3,15,4.5)):
    ts,s,o=z[tag+"_ts"],z[tag+"_s"],z[tag+"_o"]
    i=int(round(hrs*3600/60))-1
    assert ts[i]==hrs*3600
    rate=1/clock(alpha,delta)
    seen=rate*(ts[i]*s[i]+60*s[i+1:].sum())
    # finer: trapezoid / exact-ish integral bounds
    up=rate*(ts[i]*s[i]+60*s[i:-1].sum())   # left Riemann (upper since s decreasing)
    print(tag,hrs,"s(T)=%.4e o=%.3e seen=%.4e  upper-Riemann seen=%.4e  tail share=%.3f"%(s[i],o[i],seen,up,rate*60*s[i+1:].sum()/seen),
          "F(E=100)=%.4g"%(1+o[i]+100*seen), "wait %.2f"%wait(tag,(1+o[i]+100*seen)**2), "last s",s[-1], "ts[-1]",ts[-1])

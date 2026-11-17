import numpy as np, math, sys
from scipy.stats import binom
N=648000; f=1/30
def pa(al): return 1-(1-f)**al
def gain_exact(nvals, a):
    m=N*a; sd=math.sqrt(N*a*(1-a)); lo=int(m-16*sd); hi=int(m+16*sd)
    k=np.arange(lo,hi+1); sf=binom.sf(k,N,a); l=np.log1p(-sf)
    out=[]
    for n in nvals:
        E=lo+np.sum(-np.expm1(n*l)); out.append(E/m-1)
    return np.array(out)
def sim(al,Delta,ncut=400000,D=200,seed=1):
    rng=np.random.default_rng(seed); a=pa(al); h=pa(1-al)
    T=ncut*500+20000
    nb=int(T/(Delta+1/h)*1.05)+1000
    hp=np.cumsum(Delta+rng.geometric(h,nb)); assert hp[-1]>T
    nc=int(T*a*1.1)+1000
    cp=np.cumsum(rng.geometric(a,nc)); assert cp[-1]>T
    c=20000+500*np.arange(ncut)+rng.integers(0,500,ncut)
    i=np.searchsorted(hp,c,'left')           # hp[i-1] = H_1
    wc=np.searchsorted(cp,c,'left')          # wins < c
    d=np.arange(D)
    pos=hp[i[:,None]-1-d[None,:]]            # H_{d+1}
    W=wc[:,None]-np.searchsorted(cp,pos,'right')
    Wmax=W.max()
    tab=np.zeros((Wmax+1,D))
    for w in range(Wmax+1):
        row=[math.comb(w,k) for k in range(w+1)]
        suf=0
        for k in range(w,0,-1):
            suf+=row[k]
            if k-1<D: tab[w,k-1]=float(suf)   # S_d for d=k-1
    S=tab[W,d[None,:]]
    return a,1+S.max(1),1+S.sum(1),S.argmax(1),(S[:,-20:]>0).mean()
cases=[(0.01,10),(0.1,10),(0.2,10),(0.2,15),(0.3,10),(1/3,10),(1/3,15)]
for al,Dl in cases:
    a=pa(al)
    print(f"\n== alpha={al:.4f} Delta={Dl}  N*a={N*a:.1f}")
    print(" gain(n)% n=2,4,16,256,2^16,2^40:",np.round(100*gain_exact([2,4,16,256,2**16,2**40],a),4))
    _,nm,ns,am,deep=sim(al,Dl)
    print(f" P(n>=2)={100*(nm>=2).mean():.2f}%  mean log2 n|choice={np.log2(nm[nm>=2]).mean():.2f}  P(n>256)={100*(nm>256).mean():.3f}% P(n>2^16)={100*(nm>2**16).mean():.4f}%  P(argmax d>0)={100*(am>0).mean():.2f}% deepfrac={deep:.1e}")
    p2=2.0**np.arange(0,41); g2=gain_exact(p2,a)
    for lab,nn in (("max",nm),("sum",ns)):
        res=[]
        for B in (2**8,2**16,2**40):
            x=np.minimum(nn,B); u,inv=np.unique(x,return_inverse=True)
            g=gain_exact(u,a)[inv]; gi=np.interp(np.log2(x),np.arange(41),g2)
            res.append((100*g.mean(),100*g.std()/math.sqrt(len(g)),100*gi.mean(),100*g.mean()/ (nn>=2).mean(), g.mean()*N*a))
        print(f" [{lab}] mean gain% exact (se) / log2-interp / cond. on choice / blocks:")
        for r in res: print("    %.4f (%.4f)  %.4f   %.3f   %.1f"%r)

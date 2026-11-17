import math, numpy as np
from scipy import stats, special
F=1/30
rng=np.random.default_rng(1)
for alpha in (0.30,1/3):
    a=1-(1-F)**alpha
    for N in (648000,3600):
        mean=N*a; sd=math.sqrt(N*a*(1-a))
        # independent exact: own log-pmf via lgamma, E[max]=sum_k P(max>k)
        k=np.arange(0,int(mean+60*sd)+1)
        lp=special.gammaln(N+1)-special.gammaln(k+1)-special.gammaln(N-k+1)+k*math.log(a)+(N-k)*math.log1p(-a)
        p=np.exp(lp); sf=np.cumsum(p[::-1])[::-1]-p   # P(X>k), summed from the top: accurate tail
        out=[]
        for b in (0,3,8,16,24,40):
            n=2.0**b
            with np.errstate(divide='ignore'):
                emax=np.sum(-np.expm1(n*np.log1p(-np.minimum(sf,1.0))))
            # normal extreme value: quantile at 1-1/(n+1)... use E[max] ~ mean + sd*z, z from Blom
            z=stats.norm.ppf((n-0.375)/(n+0.25)) if b>0 else 0.0
            out.append((emax/mean-1, sd*z/mean))
        mc=[]
        for n in (8,256):
            x=rng.binomial(N,a,size=(100000,n)).max(axis=1)
            mc.append((x.mean()/mean-1, x.std()/math.sqrt(len(x))/mean))
        print(f"alpha {alpha:.3f} N {N}: exact " + ", ".join(f"{100*e:+.2f}" for e,_ in out))
        print("      normal(Blom) " + ", ".join(f"{100*g:+.2f}" for _,g in out))
        print("      MC n=8, 256: " + ", ".join(f"{100*m:+.2f} +- {100*s:.2f}" for m,s in mc))

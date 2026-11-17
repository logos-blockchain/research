import math
from check1 import mc, rates
ref = {(10,3600):(4.903e-3,7.907e-3),(10,7200):(8.620e-5,1.423e-4),(15,3600):(1.913e-2,3.056e-2),(15,7200):(1.094e-3,1.802e-3)}
a, h = rates(1/3)
for delta in (10, 15):
    for T, n in ((3600, 3_000_000), (7200, 5_000_000)):
        sv, op = mc(n, a, h, delta, T, 15000, 4242)
        print(f"MC delta={delta} T={T} n={n}: survival {sv/n:.4e} +- {math.sqrt(sv)/n:.1e} (table {ref[(delta,T)][0]:.3e})  open {op/n:.4e} +- {math.sqrt(op)/n:.1e} (table {ref[(delta,T)][1]:.3e})", flush=True)

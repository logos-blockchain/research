"""Emit a closed-form multi-epoch certificate: one theorem for every depth k >= k0 and
every horizon N (`Cryptarchia/Prob/Closed.lean`).

The automaton tables do not depend on k or N: they depend on the band (f, beta), Delta and
the potential's constants. So the tables and the band family are planned once, with the
band valid from k0 on (its drift conditions only get easier as the period grows), and the
settlement bound's lengths grow with t = k / 20: G' = g t, J = j t, Lw = w t, r = rho t.
Each term of `settleEps3E` is then (N + c) * A * q^t (`settleEps3E_closed`), and the
estimate's band term is 3 / Q^t (`bandEps_closed`).

Usage: python3 emitC.py BETA DELTA DELTA_TSI K NAME OUTDIR K0 [MU] [RHO]
"""
import sys, os, math, pickle, json
from fractions import Fraction as Fr
from gen import lean_q as q, chain
from certnum import rup, rdn
import certE, planE, emitE

M_DIV = 20     # t = k / M_DIV


def closed_floats(P, B, cfg, D, j, w, g, rho, x, yy, Tg):
    """the closed form's constants and rates, in floats (as `closed_section` bounds them)"""
    f = float; m = M_DIV; G = cfg['G']
    e17, tau, lpi, lp, e2, b, lr = f(P['e'][17]), f(Fr(cfg['tau'])), f(P['lpi']), f(P['lp']), f(P['e'][2]), f(P['b']), f(P['lr'])
    c = f(Fr(cfg['c'])); hhi, hlo, elo = f(B['hhi']), f(B['hlo']), f(B['elo'])
    stat = 1 + (b - 1) / (1 - lr)
    nb = 120 * m // (Tg + D); nb0 = -(-(3 + G) // (Tg + D)) + 1
    bs = 1 + (yy - 1) * (1 - (1 - hlo) ** Tg)
    L = math.log
    return dict(A1=(1 - (1 - hhi) ** D) ** (G // D), q2=g * L(1 - hlo), A3=e17 / tau, q3=j * L(e17) - w * L(tau),
                A4=(lp / lpi) ** G * e2 * stat, q4=j * L(lpi), A5=1 / x, q5=w * L(1 + (x - 1) * (1 - elo)) - m * L(x),
                A6=stat / c, q6=-rho * L(c), A7=bs ** -nb0 * yy ** -m, q7=nb * L(bs) - (m + rho) * L(yy))


def closed_value(cf, N, t, g, G):
    """log of the settlement part of the closed form at (N, t)"""
    E = math.exp
    terms = [(N + g * t + 1) * cf['A1'], (N + 1) * E(cf['q2'] * t), (N + g * t + 1) * cf['A3'] * E(cf['q3'] * t),
             (N + g * t + 1) * cf['A4'] * E(cf['q4'] * t), (N + 1) * cf['A5'] * E(cf['q5'] * t),
             (N + G + 1) * cf['A6'] * E(cf['q6'] * t), (N + 2) * cf['A7'] * E(cf['q7'] * t)]
    return math.log(sum(terms))


def opt_params(P, B, cfg, D, N_ref=5184000, k_ref=2160):
    """integer per-t lengths and the free reals, minimizing the closed form at (N_ref, k_ref),
    with every term decaying"""
    from scipy.optimize import minimize
    m = M_DIV; t_ref = k_ref // m; G = cfg['G']
    best = None
    divs = [t - D for t in range(D + 5, 120 * m) if (120 * m) % t == 0]
    for Tg in divs[:14]:
        def obj(p):
            j, w, g, rho, x, yy = p
            if min(j, w, g, rho) <= 0 or x <= 1.0001 or not (0.05 < yy < 0.9999): return 1e9
            cf = closed_floats(P, B, cfg, D, math.ceil(j), math.ceil(w), math.ceil(g), math.ceil(rho), x, yy, Tg)
            if max(cf[k] for k in ('q2', 'q3', 'q4', 'q5', 'q6', 'q7')) >= 0: return 1e9
            return closed_value(cf, N_ref, t_ref, math.ceil(g), G)
        for x0 in [1.15, 1.22]:
            for yy0 in [0.5, 0.8]:
                r = minimize(obj, [9.07 * m, 16.2 * m, 0.85 * m, 0.147 * m, x0, yy0], method='Nelder-Mead',
                             options=dict(maxiter=6000, xatol=1e-7, fatol=1e-10))
                if best is None or r.fun < best[0]: best = (r.fun, Tg, r.x)
    _, Tg, (j, w, g, rho, x, yy) = best
    J, W, Gp, R = math.ceil(j), math.ceil(w), math.ceil(g), math.ceil(rho)
    X, YY = rdn(Fr(x), 5), rdn(Fr(yy), 4)
    cf = closed_floats(P, B, cfg, D, J, W, Gp, R, float(X), float(YY), Tg)
    return dict(j=J, w=W, g=Gp, rho=R, x=X, yy=YY, Tg=Tg,
                rate=max(cf[k] for k in ('q2', 'q3', 'q4', 'q5', 'q6', 'q7')),
                ref=math.exp(closed_value(cf, N_ref, t_ref, Gp, G)))


def closed_section(cfg, T, fam, B, P, D, K, cl):
    """the closed-form numbers, the band's closed form, and the end-to-end theorem"""
    G = cfg['G']; m = M_DIV; k0 = cl['k0']
    j, w, g, rho, Tg, x, yy = cl['j'], cl['w'], cl['g'], cl['rho'], cl['Tg'], cl['x'], cl['yy']
    e17, e2, lp, lr, b, lpi = P['e'][17], P['e'][2], P['lp'], P['lr'], P['b'], P['lpi']
    tau, c = Fr(cfg['tau']), Fr(cfg['c'])
    hhi, hlo, elo = B['hhi'], B['hlo'], B['elo']
    STATv = 1 + (b - 1) / (1 - lr)
    STAT = f"(1 + ({q(b)} - 1) / (1 - {q(lr)}))"
    nb = 120 * m // (Tg + D)
    assert 120 * m == nb * (Tg + D)
    nb0 = -(-(3 + G) // (Tg + D)) + 1
    L = []
    def add(x): L.append(x)
    # ---- the base facts
    base1 = rup(1 - (1 - hhi) ** D, 14)
    l1, A1, h1 = chain(base1, G // D, True, name='cl')
    base2 = rup(1 - hlo, 14)
    l2, q2, h2 = chain(base2, g, True, name='ce')
    A3 = rup(e17 / tau, 14)
    l3a, U3, h3a = chain(e17, j, True, name='csa')
    l3b, L3, h3b = chain(tau, w, False, name='csb')
    q3 = rup(U3 / L3, 14)
    ratio = lp / lpi
    l4r, U4r, h4r = chain(ratio, G, True, name='cfr')
    A4 = rup(U4r * e2 * STATv, 14)
    l4, q4, h4 = chain(lpi, j, True, name='cf')
    A5 = rup(1 / x, 14)
    w5 = 1 + (x - 1) * (1 - elo)
    l5a, U5, h5a = chain(w5, w, True, name='cwa')
    l5b, L5, h5b = chain(x, m, False, name='cwb')
    q5 = rup(U5 / L5, 14)
    A6 = rup(STATv / c, 14)
    l6, L6, h6 = chain(c, rho, False, name='cr')
    q6 = rup(1 / L6, 14)
    bs = 1 + (yy - 1) * (1 - (1 - hlo) ** Tg)
    bs_lo, bs_hi = rdn(bs, 14), rup(bs, 14)
    A7 = rup((1 / bs_lo) ** nb0 * (1 / yy) ** m, 14)
    l7a, U7, h7a = chain(bs_hi, nb, True, name='cga')
    l7b, L7, h7b = chain(yy, m + rho, False, name='cgb')
    q7 = rup(U7 / L7, 14)
    consts = dict(A1=A1, q2=q2, A3=A3, q3=q3, A4=A4, q4=q4, A5=A5, q5=q5, A6=A6, q6=q6, A7=A7, q7=q7)
    QQ = {k: q(v) for k, v in consts.items()}
    PT_ = f"(1 + ({q(yy)} - 1) * (1 - (1 - {q(hlo)}) ^ {Tg}))"
    t_ = "(k / 20)"
    add(f"""/-! ## The closed form -/

/-- **The settlement bound's closed form**, `t = k / 20`. -/
noncomputable def epsS (N t : ℕ) : ℝ :=
  ((N : ℝ) + (({g} * t : ℕ) : ℝ) + 1) * {QQ['A1']} + ((N : ℝ) + 1) * {QQ['q2']} ^ t +
    ((N : ℝ) + (({g} * t : ℕ) : ℝ) + 1) * ({QQ['A3']} * {QQ['q3']} ^ t) +
    ((N : ℝ) + (({g} * t : ℕ) : ℝ) + 1) * ({QQ['A4']} * {QQ['q4']} ^ t) +
    ((N : ℝ) + 1) * ({QQ['A5']} * {QQ['q5']} ^ t) + ((N : ℝ) + (({G} : ℕ) : ℝ) + 1) * ({QQ['A6']} * {QQ['q6']} ^ t) +
    ((N : ℝ) + 2) * ({QQ['A7']} * {QQ['q7']} ^ t)

set_option maxHeartbeats 4000000 in
/-- **The settlement bound in closed form**, for every depth `k ≥ {k0}` and horizon `N`. -/
theorem eps_closed (E : Env) {{k : ℕ}} (hc : E.c = Config.specK k) (hk : {k0} ≤ k) (N : ℕ) :
    settleEps3E E B P {q(lpi)} {G} N {G} ({g} * {t_}) ({j} * {t_}) ({w} * {t_}) ({rho} * {t_}) {Tg} {q(x)} {q(yy)} ≤
      epsS N {t_} := by
  have hck : E.c.k = k := by rw [hc]; rfl
  have p17 : P.e 17 = {q(e17)} := rfl
  have p2 : P.e 2 = {q(e2)} := rfl
  have pτ : P.τ = {q(tau)} := rfl
  have plp : P.lp = {q(lp)} := rfl
  have plr : P.lr = {q(lr)} := rfl
  have pb : P.b = {q(b)} := rfl
  have pc : P.c = {q(c)} := rfl
  have bhhi : B.hhi = {q(hhi)} := rfl
  have bhlo : B.hlo = {q(hlo)} := rfl
  have belo : B.elo = {q(elo)} := rfl
{chr(10).join(l1)}
  have h1 : (1 - (1 - B.hhi) ^ {D}) ^ ({G} / {D}) ≤ {QQ['A1']} := by
    rw [bhhi]
    have hb : (0 : ℝ) ≤ 1 - (1 - {q(hhi)}) ^ {D} := by norm_num
    have hb' : 1 - (1 - {q(hhi)}) ^ {D} ≤ {q(base1)} := by norm_num
    rw [show ({G} / {D} : ℕ) = {G // D} by norm_num]
    exact (pow_le_pow_left₀ hb hb' _).trans {h1}
{chr(10).join(l2)}
  have h2 : (1 - B.hlo) ^ {g} ≤ {QQ['q2']} := by
    rw [bhlo]
    have hb : (0 : ℝ) ≤ 1 - {q(hlo)} := by norm_num
    have hb' : 1 - {q(hlo)} ≤ {q(base2)} := by norm_num
    exact (pow_le_pow_left₀ hb hb' _).trans {h2}
  have h3a : P.e 17 / P.τ ≤ {QQ['A3']} := by rw [p17, pτ]; norm_num
{chr(10).join(l3a)}
{chr(10).join(l3b)}
  have h3 : P.e 17 ^ {j} / P.τ ^ {w} ≤ {QQ['q3']} := by
    rw [p17, pτ]
    exact (div_le_div₀ (by norm_num) {h3a} (by norm_num) {h3b}).trans (by norm_num)
{chr(10).join(l4r)}
  have h4a : (P.lp / {q(lpi)}) ^ {G} * P.e 2 * (1 + (P.b - 1) / (1 - P.lr)) ≤ {QQ['A4']} := by
    rw [plp, p2, pb, plr, show ({q(lp)} / {q(lpi)} : ℝ) = {q(ratio)} by norm_num]
    calc {q(ratio)} ^ {G} * {q(e2)} * {STAT} ≤ {q(U4r)} * {q(e2)} * {STAT} := by
          apply mul_le_mul_of_nonneg_right _ (by norm_num)
          exact mul_le_mul_of_nonneg_right {h4r} (by norm_num)
      _ ≤ {QQ['A4']} := by norm_num
{chr(10).join(l4)}
  have h4 : ({q(lpi)} : ℝ) ^ {j} ≤ {QQ['q4']} := {h4}
  have h5a : 1 / ({q(x)} : ℝ) ≤ {QQ['A5']} := by norm_num
{chr(10).join(l5a)}
{chr(10).join(l5b)}
  have h5 : (1 + ({q(x)} - 1) * (1 - B.elo)) ^ {w} / ({q(x)} : ℝ) ^ {m} ≤ {QQ['q5']} := by
    rw [belo, show (1 + ({q(x)} - 1) * (1 - {q(elo)}) : ℝ) = {q(w5)} by norm_num]
    exact (div_le_div₀ (by norm_num) {h5a} (by norm_num) {h5b}).trans (by norm_num)
  have h6a : (1 + (P.b - 1) / (1 - P.lr)) / P.c ≤ {QQ['A6']} := by rw [pb, plr, pc]; norm_num
{chr(10).join(l6)}
  have h6 : 1 / P.c ^ {rho} ≤ {QQ['q6']} := by
    rw [pc]
    exact (div_le_div_of_nonneg_left (by norm_num) (by norm_num) {h6}).trans (by norm_num)
  have hPT : PT 1 {q(yy)} B.hlo B.hhi {Tg} = 1 - (1 - {q(hlo)}) ^ {Tg} := by
    unfold PT; rw [if_neg (by norm_num), bhlo]
  have hbs : {q(bs_lo)} ≤ 1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg} ∧
      1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg} ≤ {q(bs_hi)} := by
    rw [hPT]; constructor <;> norm_num
  have hb0 : 0 < 1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg} := lt_of_lt_of_le (by norm_num) hbs.1
  have h7a : (1 / (1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg})) ^ {nb0} * (1 / ({q(yy)} : ℝ)) ^ {m} ≤
      {QQ['A7']} := by
    calc (1 / (1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg})) ^ {nb0} * (1 / ({q(yy)} : ℝ)) ^ {m}
        ≤ (1 / ({q(bs_lo)} : ℝ)) ^ {nb0} * (1 / ({q(yy)} : ℝ)) ^ {m} := by
          refine mul_le_mul_of_nonneg_right (pow_le_pow_left₀ (by positivity) ?_ _) (by positivity)
          exact one_div_le_one_div_of_le (by norm_num) hbs.1
      _ ≤ {QQ['A7']} := by norm_num
{chr(10).join(l7a)}
{chr(10).join(l7b)}
  have h7 : (1 + ({q(yy)} - 1) * PT 1 {q(yy)} B.hlo B.hhi {Tg}) ^ {nb} / ({q(yy)} : ℝ) ^ ({m} + {rho}) ≤ {QQ['q7']} := by
    rw [show ({m} + {rho} : ℕ) = {m + rho} by norm_num]
    exact (div_le_div₀ (by norm_num) ((pow_le_pow_left₀ hb0.le hbs.2 _).trans {h7a}) (by norm_num) {h7b}).trans
      (by norm_num)
  have hnb : {nb} * {t_} ≤ nbD E {D} {G} {Tg} + {nb0} := by
    unfold nbD growLen; rw [hc, Config.specK_epochLength, Config.specK_nonceOffset]; omega
  refine (settleEps3E_closed E B P (t := {t_}) (g := {g}) (j := {j}) (w := {w}) (ρ := {rho}) (m := {m})
    (nb := {nb}) (nb0 := {nb0}) rfl rfl rfl rfl (by rw [hck]; omega) (by rw [hck]; omega) hnb
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B])
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) (by show (0 : ℝ) ≤ P.e 2; norm_num [P, Ev])
    h1 h2 h3a h3 h4a h4 h5a h5 h6a h6 hb0 h7a h7).trans ?_
  have hnEp : (nEp E N : ℝ) ≤ (N : ℝ) + 2 := by
    have := Nat.div_le_self (N + 2) E.c.epochLength
    unfold nEp; exact_mod_cast this
  have hq7 : 0 ≤ {QQ['A7']} * {QQ['q7']} ^ {t_} := by positivity
  unfold epsS
  linarith [mul_le_mul_of_nonneg_right hnEp hq7]
""")
    # ---- the band
    dv = certE.tband_derived(T)
    delta = T['delta']
    a1 = dv['ylo'] * dv['clo'] * delta ** 2 / 2
    a2 = dv['ylo'] * dv['clo'] * delta ** 2 * (Fr(1, 2) - Fr(2, 9) * delta)
    nexp = 4096
    p0 = 180 * m
    bl = []; Qs = []
    # exp a ≤ 1 / (1 - a) ≤ Ca, so 1 - 1 / Ca bounds a
    Cs = [rup(1 / (1 - a), 10) for a in (a1, a2)]
    for idx, a in enumerate((a1, a2)):
        a0 = rdn(p0 * a, 8)
        lines, Q, hyp = chain(1 + a0 / nexp, nexp, False, name=f'bq{idx}')
        bl.append((lines, Q, hyp, a0)); Qs.append(Q)
    simpsT = "Tb, TBand.Yh, TBand.Ya, TBand.ylo, TBand.clo, TBand.chi, errHi, errLo"
    exps = [f"Tb.ylo * Tb.clo * Tb.δ ^ 2 / 2", f"Tb.ylo * Tb.clo * Tb.δ ^ 2 * (1 / 2 - 2 / 9 * Tb.δ)"]
    parts = []
    for idx in range(2):
        lines, Q, hyp, a0 = bl[idx]
        ind = chr(10).join('  ' + ln for ln in chr(10).join(lines).split(chr(10)))
        parts.append(f"""  · have ha : {exps[idx]} ≤ {q(1 - 1 / Cs[idx])} := by norm_num [{simpsT}]
    have he : Real.exp ({exps[idx]}) ≤ {q(Cs[idx])} := by
      set a := {exps[idx]} with ha'
      have h1 := Real.add_one_le_exp (-a)
      have hpos : 0 < 1 - a := by linarith
      have h2 : Real.exp a = (Real.exp (-a))⁻¹ := by rw [Real.exp_neg, inv_inv]
      have h3 : (Real.exp (-a))⁻¹ ≤ (1 - a)⁻¹ := inv_anti₀ hpos (by linarith)
      have h4 : (1 - a)⁻¹ ≤ {q(Cs[idx])} := by rw [inv_le_iff_one_le_mul₀ hpos]; linarith
      linarith
{ind}
    have hq : Real.exp (-((({p0} : ℕ) : ℝ) * ({exps[idx]}))) ≤ 1 / {q(Q)} :=
      exp_neg_le_of (a0 := {q(a0)}) {nexp} (by norm_num) (by norm_num) (by norm_num [{simpsT}]) (by norm_num)
        (by rw [show (1 + {q(a0)} / (({nexp} : ℕ) : ℝ)) = {q(1 + a0 / nexp)} by norm_num]; exact {hyp})
    exact mul_le_mul he (pow_le_pow_left₀ (Real.exp_pos _).le hq _) (by positivity) (by norm_num)""")
    add(f"""/-- **The estimate's band in closed form**, for every depth `k ≥ {k0}`. -/
theorem band_closed {{k : ℕ}} (hk : {k0} ≤ k) :
    bandEps Tb (180 * k) ≤ {q(Cs[0])} * (1 / {q(Qs[0])}) ^ {t_} + {q(Cs[1])} * (1 / {q(Qs[1])}) ^ {t_} := by
  have hb := bandEps_closed Tb (P := 180 * k) (t := {t_}) (p0 := {p0}) (by omega)
    (by norm_num [{simpsT}]) (by norm_num [Tb])
  refine hb.trans (add_le_add ?_ ?_)
{chr(10).join(parts)}

/-- **The bound in closed form**: `epsS` plus the estimate's band in each of the
`N / (300 k) + 2` epochs. -/
noncomputable def epsC (N k : ℕ) : ℝ :=
  epsS N {t_} + ((N / (300 * k) + 2 : ℕ) : ℝ) * ({q(Cs[0])} * (1 / {q(Qs[0])}) ^ {t_} + {q(Cs[1])} * (1 / {q(Qs[1])}) ^ {t_})
""")
    # ---- the theorem
    beta = T['beta']; RHO = T['rho']; HMIN = T['hmin']
    add(f"""/-- **Finality in closed form.** f = 1/30, Δ = {D} slots, any depth `k ≥ {k0}` and any horizon
`N`. Under the execution model (`Model`), if the genesis estimate is the genesis stake, the
adversary holds at most {float(beta)} of the participating stake, the canonical chain counts at least
{float(1 - T['mu'])} of each window's honestly won slots, stake drifts by at most a factor {float(RHO)} per
epoch and honest online stake is at least {HMIN}, a finality violation has probability at most
`epsC N k`. Every term of `epsC` decays geometrically in `k / 20`. -/
theorem finality_closed {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) {{k : ℕ}} (hc : E.c = Config.specK k)
    (hk : {k0} ≤ k) (hΔ : E.Δ = {D}) (es : Ω → List Event) (hM : Model μ O E es) {{N : ℕ}}
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(beta)} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} (N / (300 * k) + 2))
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(RHO)} (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(HMIN)}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤ ENNReal.ofReal (epsC N k) := by
  have hEL : E.c.epochLength = 300 * k := by rw [hc, Config.specK_epochLength]
  have hP : E.c.period = 180 * k := by rw [hc, Config.specK_period]
  have hb := Prob.finality (M := N + {G} + {g} * {t_} + {D} + 2) (Ne := N / (300 * k) + 2) es hM hN hΔ
    (D3 E.c.epochLength (by rw [hEL]; omega))
    (fun kk => by fin_cases kk; exacts [{", ".join(f"prod{kk}" for kk in range(K))}])
    (G' := {g} * {t_}) (J := {j} * {t_}) (Lw := {w} * {t_}) (r := {rho} * {t_}) (T := {Tg}) (x := {q(x)}) (yy := {q(yy)})
    (by norm_num) (by norm_num) (by norm_num) (by norm_num) le_rfl
    (by norm_num [B]) (by norm_num [B]) (by norm_num [B]) (by norm_num [B])
    (by rw [hEL]; omega) (by rw [hEL, hc, Config.specK_nonceOffset]; omega)
    (by rw [hc]; exact lotConsts_specK lot k) TbOK (by rw [hc]; rfl) (by rw [hc]; norm_num [Config.specK, Config.spec])
    (by rw [hP, hc]; simp only [Config.specK, Config.spec]; omega) (by rw [hP]; omega) (by rw [hP, hEL]; omega)
    (by rw [hEL, show N + {G} + {g} * {t_} + {D} + 2 = N + ({G} + {g} * {t_} + {D} + 2) by ring]
        exact div_lt_add_two (by omega))
    (mem := mem) (fun kk => by fin_cases kk <;> rfl)
    (fun kk => by fin_cases kk; exacts [{", ".join(f"ok{kk}" for kk in range(K))}]) covM advM
    (ρ := {q(RHO)}) (Hmin := {q(HMIN)}) (by norm_num) (by norm_num)
    (by
      rw [hc, lam0_specK]
      have e : ∀ K' P' : ℝ, Tb.ℓhi * K' * (1 - Tb.μ) * (1 - Tb.δ) * Tb.clo * (P' - 1) / {q(RHO)} =
          (Tb.ℓhi * (1 - Tb.μ) * (1 - Tb.δ) * Tb.clo / {q(RHO)}) * K' * (P' - 1) := by intros; ring
      rw [e]
      exact hup_of_k0 hk (by norm_num) (by norm_num [{simpsT}])
        (by unfold lam0; norm_num [{simpsT}, Config.spec]))
    (by
      rw [hc, lam0_specK]
      have e : ∀ K' P' : ℝ, Tb.ℓlo * K' * (1 + Tb.δ) * Tb.chi * P' * {q(RHO)} =
          (Tb.ℓlo * (1 + Tb.δ) * Tb.chi * {q(RHO)}) * K' * P' := by intros; ring
      rw [e]
      exact hdn_of_k0 hk (by norm_num) (by norm_num) (by unfold lam0; norm_num [{simpsT}, Config.spec]))
    (by rw [hc, lam0_specK]; unfold lam0; norm_num [Tb, Config.spec])
    (by rw [hc, lam0_specK]; unfold lam0; norm_num [Tb, Config.spec])
    hG hS hQ hD hH
  rw [hP] at hb
  have h1 := ENNReal.ofReal_le_ofReal (eps_closed E hc hk N)
  have h2 := ENNReal.ofReal_le_ofReal (band_closed hk)
  refine hb.trans ((add_le_add h1 (mul_le_mul_right h2 _)).trans ?_)
  have hS0 : 0 ≤ epsS N {t_} := by unfold epsS; positivity
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add hS0 (by positivity)]
  exact le_rfl
""")
    # ---- the short form: from t0 = k0 / 20 on, every settlement term under the slowest settlement
    # rate qs, every band term under the slower band rate qb
    t0 = k0 // m
    qi = {2: consts['q2'], 3: consts['q3'], 4: consts['q4'], 5: consts['q5'], 6: consts['q6'], 7: consts['q7']}
    Ai = {2: Fr(1), 3: consts['A3'], 4: consts['A4'], 5: consts['A5'], 6: consts['A6'], 7: consts['A7']}
    qs = rup(max(qi.values()), 6)
    Ri = {i_: rup(Ai[i_] * (qi[i_] / qs) ** t0, 6) for i_ in qi}
    bq = [1 / Q for Q in Qs]
    qb = rup(max(bq), 6)
    Rb = [rup(Cs[i_] * (bq[i_] / qb) ** t0, 6) for i_ in range(2)]
    As = sum(Ri.values()); Ab = sum(Rb)
    short = dict(t0=t0, qs=qs, As=As, qb=qb, Ab=Ab)
    coef = {2: "(N : ℝ) + 1", 3: f"(N : ℝ) + {g} * (t : ℝ) + 1", 4: f"(N : ℝ) + {g} * (t : ℝ) + 1",
            5: "(N : ℝ) + 1", 6: f"(N : ℝ) + {G} + 1", 7: "(N : ℝ) + 2"}
    rs = []
    for i_ in qi:
        rs.append(f"  have r{i_} := geom_le_of (A := {q(Ai[i_])}) (t0 := {t0}) (t := t) (by norm_num) "
                  f"(by norm_num : (0 : ℝ) ≤ {QQ['q' + str(i_)]}) (by norm_num : (0 : ℝ) < {q(qs)}) (by norm_num) ht0 "
                  f"(by norm_num : ({q(Ai[i_])} : ℝ) * ({QQ['q' + str(i_)]} ^ {t0} / {q(qs)} ^ {t0}) ≤ {q(Ri[i_])})")
        rs.append(f"  have k{i_} := mul_le_mul_of_nonneg_left r{i_} (by positivity : (0 : ℝ) ≤ {coef[i_]})")
    for i_ in range(2):
        rs.append(f"  have rb{i_} := geom_le_of (A := {q(Cs[i_])}) (t0 := {t0}) (t := t) (by norm_num) "
                  f"(by norm_num : (0 : ℝ) ≤ 1 / {q(Qs[i_])}) (by norm_num : (0 : ℝ) < {q(qb)}) (by norm_num) ht0 "
                  f"(by norm_num : ({q(Cs[i_])} : ℝ) * ((1 / {q(Qs[i_])}) ^ {t0} / {q(qb)} ^ {t0}) ≤ {q(Rb[i_])})")
    RS = chr(10).join(rs)
    add(f"""/-- **Finality in closed form, short**: with `t = k / 20` and `Ne = N / (300 k) + 2` epochs, a
finality violation has probability at most
`(N + {g} t + {G + 2}) · ({float(consts['A1']):.2g} + {float(As):.4g} · {float(qs):.6f}ᵗ) + Ne · {float(Ab):.4g} · {float(qb):.6f}ᵗ`:
settlement at rate {float(qs):.4f} per 20 blocks of depth, the estimate's band at rate {float(qb):.4f}. -/
theorem finality_closed_short {{Ω : Type*}} [MeasurableSpace Ω] {{μ : MeasureTheory.Measure Ω}}
    [MeasureTheory.IsProbabilityMeasure μ] {{O : Ω → Oracle}} (E : Env) {{k : ℕ}} (hc : E.c = Config.specK k)
    (hk : {k0} ≤ k) (hΔ : E.Δ = {D}) (es : Ω → List Event) (hM : Model μ O E es) {{N : ℕ}}
    (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hG : GenesisOK E)
    (hS : ∀ ω, Exec.StakeOK E (O ω) (es ω) {q(T['beta'])} (1 / 10 ^ 16))
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) {q(T['mu'])} (N / (300 * k) + 2))
    (hD : ∀ ω, Exec.StakeDrift E (O ω) (es ω) {q(T['rho'])} (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) {q(T['hmin'])}) :
    μ {{ω | Unsafe (E.withO (O ω)) (es ω)}} ≤
      ENNReal.ofReal (((N : ℝ) + {g} * ({t_} : ℕ) + {G + 2}) * ({QQ['A1']} + {q(As)} * {q(qs)} ^ {t_}) +
        ((N / (300 * k) + 2 : ℕ) : ℝ) * ({q(Ab)} * {q(qb)} ^ {t_})) := by
  refine (finality_closed E hc hk hΔ es hM hN hG hS hQ hD hH).trans (ENNReal.ofReal_le_ofReal ?_)
  unfold epsC epsS
  have ht0 : {t0} ≤ {t_} := by omega
  set t := {t_} with ht
  simp only [Nat.cast_mul, Nat.cast_ofNat]
{RS}
  have hNe0 : (0 : ℝ) ≤ ((N / (300 * k) + 2 : ℕ) : ℝ) := Nat.cast_nonneg _
  have kb := mul_le_mul_of_nonneg_left (add_le_add rb0 rb1) hNe0
  have hqs : 0 ≤ ({q(qs)} : ℝ) ^ t := by positivity
  have kq := mul_nonneg (Nat.cast_nonneg t : (0 : ℝ) ≤ t) hqs
  have hN0 : (0 : ℝ) ≤ N := Nat.cast_nonneg _
  rw [one_mul] at k2
  linarith
""")
    return "\n".join(L), consts, Qs, nb, nb0, Cs, short


def eval_closed(consts, Qs, Cs, cl, G, N, k):
    """the closed form's value, in floats"""
    t = k // M_DIV; g = cl['g']
    c = {kk: float(v) for kk, v in consts.items()}
    s = ((N + g * t + 1) * c['A1'] + (N + 1) * c['q2'] ** t + (N + g * t + 1) * c['A3'] * c['q3'] ** t +
         (N + g * t + 1) * c['A4'] * c['q4'] ** t + (N + 1) * c['A5'] * c['q5'] ** t + (N + G + 1) * c['A6'] * c['q6'] ** t +
         (N + 2) * c['A7'] * c['q7'] ** t)
    band = (N // (300 * k) + 2) * sum(float(C) * float(1 / Q) ** t for C, Q in zip(Cs, Qs))
    return s, band


if __name__ == "__main__":
    beta, D, delta, K = float(sys.argv[1]), int(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
    name, out_dir, k0 = sys.argv[5], sys.argv[6], int(sys.argv[7])
    mu = float(sys.argv[8]) if len(sys.argv) > 8 else 0.1
    rho = Fr(sys.argv[9]) if len(sys.argv) > 9 else certE.RHO
    pk = f"res_{name}.pkl"
    # the band is valid from depth k0 on: its drift conditions use the period 180 k0
    certE.PERIOD = 180 * k0
    orig = certE.tband
    planE.tband = lambda b_, d_, mu=Fr(0), d=8: orig(b_, d_, mu=mu, d=d, rho=rho)
    if os.path.exists(pk):
        res = pickle.load(open(pk, 'rb'))
    else:
        res = planE.make(beta, D, delta, K, 5184000, mu=mu)
        pickle.dump(res, open(pk, 'wb'))
    cfg, T, fam, B, P, Ts = res
    cl = opt_params(P, B, cfg, D)
    cl['k0'] = k0
    print('closed params', cl)
    # dummy settlement parameters for the shared emitter (the closed section uses its own)
    emitE.emit_all(cfg, T, fam, B, P, Ts, name, out_dir, Fr(1), closed=cl)
    _, consts, Qs, nb, nb0, Cs, short = closed_section(cfg, T, fam, B, P, D, K, cl)
    for (N, k) in [(5184000, 2160), (31536000, 2160), (5184000, 1000), (5184000, 1500), (5184000, 3000)]:
        s, band = eval_closed(consts, Qs, Cs, cl, cfg['G'], N, k)
        print(f'N={N} k={k}: settlement {s:.3e} band {band:.3e} total {s + band:.3e}')
        t = k // M_DIV; f = {kk: float(v) for kk, v in short.items()}
        sh = (N + cl['g'] * t + cfg['G'] + 2) * (float(consts['A1']) + f['As'] * f['qs'] ** t) + (N // (300 * k) + 2) * f['Ab'] * f['qb'] ** t
        print(f'   short form {sh:.3e}')
    json.dump(dict(cfg, closed={kk: str(v) for kk, v in cl.items()}, consts={kk: str(v) for kk, v in consts.items()},
                   Q=[str(Q) for Q in Qs]), open(f"cfgC_{name}.json", "w"), indent=1)

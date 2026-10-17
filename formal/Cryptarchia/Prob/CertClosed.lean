module

public import Cryptarchia.Prob.CertSpec
public import Cryptarchia.Prob.Closed
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Analysis.Complex.UpperHalfPlane.Basic
import Mathlib.Analysis.SpecialFunctions.Bernstein
import Mathlib.Analysis.SpecialFunctions.Gamma.Basic
import Mathlib.Analysis.SpecialFunctions.Trigonometric.DerivHyp
import Mathlib.Combinatorics.Enumerative.DyckWord
import Mathlib.Combinatorics.SimpleGraph.Triangle.Removal
import Mathlib.Data.NNRat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude
import Mathlib.NumberTheory.Chebyshev
import Mathlib.NumberTheory.Height.NumberField
import Mathlib.NumberTheory.Height.Projectivization
import Mathlib.NumberTheory.LucasLehmer
import Mathlib.NumberTheory.SelbergSieve
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.Tactic.Echelon.Zsqrtd
import Mathlib.Tactic.NormNum.Irrational
import Mathlib.Tactic.NormNum.IsCoprime
import Mathlib.Tactic.NormNum.IsSquare
import Mathlib.Tactic.NormNum.LegendreSymbol
import Mathlib.Tactic.NormNum.ModEq
import Mathlib.Tactic.NormNum.NatFib
import Mathlib.Tactic.NormNum.NatLog
import Mathlib.Tactic.NormNum.NatSqrt
import Mathlib.Tactic.NormNum.Ordinal
import Mathlib.Tactic.NormNum.Parity
import Mathlib.Tactic.NormNum.Prime
import Mathlib.Tactic.NormNum.RealSqrt
import Mathlib.Topology.Sheaves.Init
import Mathlib.Algebra.Order.Ring.Star

/-!
# Closed-form certificates from their data

`finality_closed` for every depth `k ≥ k0` and every horizon `N`, at `Config.specK k`, for a
certificate given as data (`CertGen.lean`): the settlement parameters are linear in `t = k / m`
(`G' = g t`, `J = j t`, `Lw = w t`, `r = ρr t`), and each of `settleEps3E`'s terms is bounded by
`(N + c) · A · qᵗ` (`settleEps3E_closed`), the band by `C · Q⁻ᵗ` per epoch (`bandEps_closed`). The
constants' conditions are one check over `ℚ` (`closedChk`), the powers bounded by `powUpQ` and
`powDnQ`.
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory

/-- **A closed-form certificate's chosen numbers** beyond the family and the potential's parameters. -/
structure ClosedData where
  /-- the weight of the cold potential's second term -/
  κ : ℚ
  /-- the phase cut, and the rates per `t = k / m`: empty runs `g t`, spans of `j t` phases and
  `w t` slots, reach `ρr t`; the growth block `T` -/
  G : ℕ
  g : ℕ
  j : ℕ
  w : ℕ
  ρr : ℕ
  T : ℕ
  m : ℕ
  /-- the least depth -/
  k0 : ℕ
  /-- the tilts, the stake drift per epoch, the minimum honest stake -/
  x : ℚ
  yy : ℚ
  ρ : ℚ
  Hmin : ℚ

/-- **A closed-form certificate's derived numbers** (`ClosedData.derive`). -/
structure ClosedDerived where
  /-- the potential's contractions -/
  lp : ℚ
  lpi : ℚ
  /-- growth blocks per `t`, less `nb0` -/
  nb : ℕ
  nb0 : ℕ
  /-- the settlement terms' constants and rates -/
  A1 : ℚ
  q2 : ℚ
  A3 : ℚ
  q3 : ℚ
  A4 : ℚ
  q4 : ℚ
  A5 : ℚ
  q5 : ℚ
  A6 : ℚ
  q6 : ℚ
  A7 : ℚ
  q7 : ℚ
  /-- the band's terms `C · (1 / Q)ᵗ` -/
  C1 : ℚ
  Q1 : ℚ
  C2 : ℚ
  Q2 : ℚ
  /-- the short form, from `t ≥ t0` on: settlement at rate `qs` with constant `As`, the band at `qb`
  with `Ab` -/
  t0 : ℕ
  qs : ℚ
  As : ℚ
  qb : ℚ
  Ab : ℚ
deriving DecidableEq

/-- The band's closed form per epoch. -/
noncomputable def ClosedDerived.bandC (q : ClosedDerived) (t : ℕ) : ℝ :=
  q.C1 * (1 / (q.Q1 : ℝ)) ^ t + q.C2 * (1 / (q.Q2 : ℝ)) ^ t

namespace ClosedData

variable (p : ClosedData) (q : ClosedDerived)

/-- **The settlement bound's closed form**, `t = k / m`. -/
noncomputable def epsS (N t : ℕ) : ℝ :=
  ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * q.A1 + ((N : ℝ) + 1) * (q.q2 : ℝ) ^ t +
    ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * (q.A3 * (q.q3 : ℝ) ^ t) +
    ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * (q.A4 * (q.q4 : ℝ) ^ t) +
    ((N : ℝ) + 1) * (q.A5 * (q.q5 : ℝ) ^ t) + ((N : ℝ) + ((p.G : ℕ) : ℝ) + 1) * (q.A6 * (q.q6 : ℝ) ^ t) +
    ((N : ℝ) + 2) * (q.A7 * (q.q7 : ℝ) ^ t)


/-- **The bound in closed form**: `epsS` plus the band in each of the `N / (300 k) + 2` epochs. -/
noncomputable def epsC (N k : ℕ) : ℝ := p.epsS q N (k / p.m) + ((N / (300 * k) + 2 : ℕ) : ℝ) * q.bandC (k / p.m)

/-- **The short form**: one settlement rate and one band rate. -/
noncomputable def epsShort (N k : ℕ) : ℝ :=
  ((N : ℝ) + p.g * ((k / p.m : ℕ) : ℝ) + ((p.G + 2 : ℕ) : ℝ)) * (q.A1 + q.As * (q.qs : ℝ) ^ (k / p.m)) +
    ((N / (300 * k) + 2 : ℕ) : ℝ) * (q.Ab * (q.qb : ℝ) ^ (k / p.m))

end ClosedData

namespace FamCfg


/-- **The derived numbers** of a closed-form certificate: the contractions from the tables' bounds
(`lpOf`, `lpiOf`), the growth blocks, each settlement term's constant and rate, the band's terms and
the short form's rates, every power bounded outward to 14 digits, as the generator computes them
(`emitC.closed_consts`). -/
def _root_.Cryptarchia.Prob.ClosedData.derive (p : ClosedData) (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData)
    (T : TBandQ) : ClosedDerived :=
  let lp := F.lpOf Bq p.κ dat
  let lpi := F.lpiOf p.κ dat
  let stat := 1 + (bOf dat - 1) / (1 - lrOf dat)
  let up := powUpQ 14
  let dn := powDnQ 14
  let nb := 120 * p.m / (p.T + F.Δ)
  let nb0 := (3 + p.G + (p.T + F.Δ) - 1) / (p.T + F.Δ) + 1
  let bs := 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)
  let A1 := up (rupQ 14 (1 - (1 - Bq.hhi) ^ F.Δ)) (p.G / F.Δ)
  let q2 := up (rupQ 14 (1 - Bq.hlo)) p.g
  let A3 := rupQ 14 (eOf dat 17 / F.τ)
  let q3 := rupQ 14 (up (eOf dat 17) p.j / dn F.τ p.w)
  let A4 := rupQ 14 (up (lp / lpi) p.G * eOf dat 2 * stat)
  let q4 := up lpi p.j
  let A5 := rupQ 14 (1 / p.x)
  let q5 := rupQ 14 (up (1 + (p.x - 1) * (1 - Bq.elo)) p.w / dn p.x p.m)
  let A6 := rupQ 14 (stat / F.c)
  let q6 := rupQ 14 (1 / dn F.c p.ρr)
  let A7 := rupQ 14 ((1 / rdnQ 14 bs) ^ nb0 * (1 / p.yy) ^ p.m)
  let q7 := rupQ 14 (up (rupQ 14 bs) nb / dn p.yy (p.m + p.ρr))
  let a1 := T.ylo * T.clo * T.δ ^ 2 / 2
  let a2 := T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)
  let C1 := rupQ 10 (1 / (1 - a1))
  let Q1 := dn (1 + rdnQ 8 ((180 * p.m : ℕ) * a1) / 4096) 4096
  let C2 := rupQ 10 (1 / (1 - a2))
  let Q2 := dn (1 + rdnQ 8 ((180 * p.m : ℕ) * a2) / 4096) 4096
  let t0 := p.k0 / p.m
  let qs := rupQ 6 ([q3, q4, q5, q6, q7].foldl max q2)
  let qb := rupQ 6 (max (1 / Q1) (1 / Q2))
  let As := rupQ 6 ((q2 / qs) ^ t0) + rupQ 6 (A3 * (q3 / qs) ^ t0) + rupQ 6 (A4 * (q4 / qs) ^ t0) +
    rupQ 6 (A5 * (q5 / qs) ^ t0) + rupQ 6 (A6 * (q6 / qs) ^ t0) + rupQ 6 (A7 * (q7 / qs) ^ t0)
  let Ab := rupQ 6 (C1 * ((1 / Q1) / qb) ^ t0) + rupQ 6 (C2 * ((1 / Q2) / qb) ^ t0)
  ⟨lp, lpi, nb, nb0, A1, q2, A3, q3, A4, q4, A5, q5, A6, q6, A7, q7, C1, Q1, C2, Q2, t0, qs, As, qb, Ab⟩

/-- **Every numeric condition of a closed-form certificate.** -/
def closedChk (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData) (T : TBandQ) (p : ClosedData) (q : ClosedDerived) :
    Bool :=
  decide (0 ≤ 1 - (1 - Bq.hhi) ^ F.Δ) &&
    decide (powUpQ 14 (1 - (1 - Bq.hhi) ^ F.Δ) (p.G / F.Δ) ≤ q.A1) &&
    decide (0 ≤ 1 - Bq.hlo) &&
    decide (powUpQ 14 (1 - Bq.hlo) p.g ≤ q.q2) &&
    decide (eOf dat 17 / F.τ ≤ q.A3) &&
    decide (0 ≤ eOf dat 17) &&
    decide (0 ≤ F.τ) &&
    decide (0 < powDnQ 14 F.τ p.w) &&
    decide (powUpQ 14 (eOf dat 17) p.j / powDnQ 14 F.τ p.w ≤ q.q3) &&
    decide (0 ≤ q.lp / q.lpi) &&
    decide (0 ≤ eOf dat 2) &&
    decide (0 ≤ 1 + (bOf dat - 1) / (1 - lrOf dat)) &&
    decide (powUpQ 14 (q.lp / q.lpi) p.G * eOf dat 2 * (1 + (bOf dat - 1) / (1 - lrOf dat)) ≤ q.A4) &&
    decide (0 < q.lpi) &&
    decide (powUpQ 14 q.lpi p.j ≤ q.q4) &&
    decide (1 / p.x ≤ q.A5) &&
    decide (0 ≤ 1 + (p.x - 1) * (1 - Bq.elo)) &&
    decide (1 ≤ p.x) &&
    decide (0 < powDnQ 14 p.x p.m) &&
    decide (powUpQ 14 (1 + (p.x - 1) * (1 - Bq.elo)) p.w / powDnQ 14 p.x p.m ≤ q.q5) &&
    decide ((1 + (bOf dat - 1) / (1 - lrOf dat)) / F.c ≤ q.A6) &&
    decide (0 ≤ F.c) &&
    decide (0 < powDnQ 14 F.c p.ρr) &&
    decide (1 / powDnQ 14 F.c p.ρr ≤ q.q6) &&
    decide (0 < 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) &&
    decide (0 < p.yy) &&
    decide (p.yy ≤ 1) &&
    decide ((1 / (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T))) ^ q.nb0 *
      (1 / p.yy) ^ p.m ≤ q.A7) &&
    decide (0 < powDnQ 14 p.yy (p.m + p.ρr)) &&
    decide (powUpQ 14 (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) q.nb /
      powDnQ 14 p.yy (p.m + p.ρr) ≤ q.q7) &&
    decide (0 ≤ Bq.hhi) &&
    decide (Bq.hhi ≤ 1) &&
    decide (0 ≤ Bq.hlo) &&
    decide (Bq.hlo ≤ 1) &&
    decide (Bq.elo ≤ 1) &&
    decide (0 < p.m) &&
    decide (1 ≤ p.T) &&
    decide (0 ≤ T.ylo * T.clo * T.δ ^ 2 / 2) &&
    decide (0 ≤ T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) &&
    decide (T.δ ≤ 1) &&
    decide (T.ylo * T.clo * T.δ ^ 2 / 2 ≤ 1 - 1 / q.C1) &&
    decide (0 < q.C1) &&
    decide (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ) ≤ 1 - 1 / q.C2) &&
    decide (0 < q.C2) &&
    decide (0 < q.Q1) &&
    decide (q.Q1 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 / 2) / 4096) 4096) &&
    decide (0 < q.Q2) &&
    decide (q.Q2 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) / 4096) 4096) &&
    T.okQ &&
    decide (F.S.η = T.η) &&
    decide (F.S.ζ = T.ζ) &&
    decide (F.S.β = T.β) &&
    decide (T.η = 1 / 10 ^ 70) &&
    decide (F.S.ys.getD 0 0 ≤ T.ylo) &&
    decide (T.Yh ≤ F.S.ys.getD F.S.K 0) &&
    decide (1 ≤ p.k0) &&
    decide (0 < p.ρ) &&
    decide (0 < p.Hmin) &&
    decide ((1 - T.μ) + 2 * T.ℓhi / (lam0Q Config.spec * p.Hmin) ≤
      T.ℓhi * (1 - T.μ) * (1 - T.δ) * T.clo / p.ρ * (1000 / (180 * (p.k0 : ℚ) * 33)) * (180 * (p.k0 : ℚ) - 1)) &&
    decide (0 ≤ T.ℓhi * (1 - T.μ) * (1 - T.δ) * T.clo / p.ρ) &&
    decide (T.ℓlo * (1 + T.δ) * T.chi * p.ρ * (1000 / 33) + 1000 / (180 * (p.k0 : ℚ) * 33) * p.ρ +
      3 * T.ℓlo / (lam0Q Config.spec * p.Hmin) ≤ 1) &&
    decide (T.ℓlo ≤ lam0Q Config.spec) &&
    decide ((1 - T.μ) * lam0Q Config.spec ≤ T.ℓhi) &&
    decide (F.Δ + 1 ≤ p.G) &&
    decide (p.G + 1 < 300 * p.k0) &&
    decide (p.G + 2 ≤ 120 * p.k0) &&
    decide (0 < q.qs) &&
    decide (0 < q.qb) &&
    decide (q.q2 ^ q.t0 / q.qs ^ q.t0 + q.A3 * (q.q3 ^ q.t0 / q.qs ^ q.t0) + q.A4 * (q.q4 ^ q.t0 / q.qs ^ q.t0) +
      q.A5 * (q.q5 ^ q.t0 / q.qs ^ q.t0) + q.A6 * (q.q6 ^ q.t0 / q.qs ^ q.t0) + q.A7 * (q.q7 ^ q.t0 / q.qs ^ q.t0) ≤ q.As) &&
    decide (q.q2 ≤ q.qs ∧ q.q3 ≤ q.qs ∧ q.q4 ≤ q.qs ∧ q.q5 ≤ q.qs ∧ q.q6 ≤ q.qs ∧ q.q7 ≤ q.qs) &&
    decide (0 ≤ q.A1 ∧ 0 ≤ q.q2 ∧ 0 ≤ q.A3 ∧ 0 ≤ q.q3 ∧ 0 ≤ q.A4 ∧ 0 ≤ q.q4 ∧ 0 ≤ q.A5 ∧ 0 ≤ q.q5 ∧ 0 ≤ q.A6 ∧ 0 ≤ q.q6 ∧ 0 ≤ q.A7 ∧ 0 ≤ q.q7) &&
    decide (q.C1 * ((1 / q.Q1) ^ q.t0 / q.qb ^ q.t0) + q.C2 * ((1 / q.Q2) ^ q.t0 / q.qb ^ q.t0) ≤ q.Ab) &&
    decide (1 / q.Q1 ≤ q.qb ∧ 1 / q.Q2 ≤ q.qb) &&
    decide (p.m * q.t0 ≤ p.k0) &&
    decide (0 ≤ T.ylo * T.clo)

/-- The conditions `closedChk` checks, by name. -/
structure ClosedFacts (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData) (T : TBandQ) (p : ClosedData)
    (q : ClosedDerived) : Prop where
  c1a : 0 ≤ 1 - (1 - Bq.hhi) ^ F.Δ
  c1 : powUpQ 14 (1 - (1 - Bq.hhi) ^ F.Δ) (p.G / F.Δ) ≤ q.A1
  c2a : 0 ≤ 1 - Bq.hlo
  c2 : powUpQ 14 (1 - Bq.hlo) p.g ≤ q.q2
  c3a : eOf dat 17 / F.τ ≤ q.A3
  e17 : 0 ≤ eOf dat 17
  tau0 : 0 ≤ F.τ
  tauw : 0 < powDnQ 14 F.τ p.w
  c3 : powUpQ 14 (eOf dat 17) p.j / powDnQ 14 F.τ p.w ≤ q.q3
  rat0 : 0 ≤ q.lp / q.lpi
  e20 : 0 ≤ eOf dat 2
  F0 : 0 ≤ 1 + (bOf dat - 1) / (1 - lrOf dat)
  c4a : powUpQ 14 (q.lp / q.lpi) p.G * eOf dat 2 * (1 + (bOf dat - 1) / (1 - lrOf dat)) ≤ q.A4
  lpi0 : 0 < q.lpi
  c4 : powUpQ 14 q.lpi p.j ≤ q.q4
  c5a : 1 / p.x ≤ q.A5
  w50 : 0 ≤ 1 + (p.x - 1) * (1 - Bq.elo)
  x1 : 1 ≤ p.x
  xm : 0 < powDnQ 14 p.x p.m
  c5 : powUpQ 14 (1 + (p.x - 1) * (1 - Bq.elo)) p.w / powDnQ 14 p.x p.m ≤ q.q5
  c6a : (1 + (bOf dat - 1) / (1 - lrOf dat)) / F.c ≤ q.A6
  c0 : 0 ≤ F.c
  cr : 0 < powDnQ 14 F.c p.ρr
  c6 : 1 / powDnQ 14 F.c p.ρr ≤ q.q6
  bs0 : 0 < 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)
  yy0 : 0 < p.yy
  yy1 : p.yy ≤ 1
  c7a : (1 / (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T))) ^ q.nb0 *
      (1 / p.yy) ^ p.m ≤ q.A7
  yym : 0 < powDnQ 14 p.yy (p.m + p.ρr)
  c7 : powUpQ 14 (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) q.nb /
      powDnQ 14 p.yy (p.m + p.ρr) ≤ q.q7
  hhi0 : 0 ≤ Bq.hhi
  hhi1 : Bq.hhi ≤ 1
  hlo0 : 0 ≤ Bq.hlo
  hlo1 : Bq.hlo ≤ 1
  helo1 : Bq.elo ≤ 1
  m0 : 0 < p.m
  T1 : 1 ≤ p.T
  a10 : 0 ≤ T.ylo * T.clo * T.δ ^ 2 / 2
  a20 : 0 ≤ T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)
  δ1 : T.δ ≤ 1
  C1 : T.ylo * T.clo * T.δ ^ 2 / 2 ≤ 1 - 1 / q.C1
  C10 : 0 < q.C1
  C2 : T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ) ≤ 1 - 1 / q.C2
  C20 : 0 < q.C2
  Q10 : 0 < q.Q1
  Q1 : q.Q1 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 / 2) / 4096) 4096
  Q20 : 0 < q.Q2
  Q2 : q.Q2 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) / 4096) 4096
  ok : T.okQ = true
  hη : F.S.η = T.η
  hζ : F.S.ζ = T.ζ
  hβ : F.S.β = T.β
  hηlot : T.η = 1 / 10 ^ 70
  cov0 : F.S.ys.getD 0 0 ≤ T.ylo
  cov1 : T.Yh ≤ F.S.ys.getD F.S.K 0
  k01 : 1 ≤ p.k0
  ρ0 : 0 < p.ρ
  Hm0 : 0 < p.Hmin
  up : (1 - T.μ) + 2 * T.ℓhi / (lam0Q Config.spec * p.Hmin) ≤
      T.ℓhi * (1 - T.μ) * (1 - T.δ) * T.clo / p.ρ * (1000 / (180 * (p.k0 : ℚ) * 33)) * (180 * (p.k0 : ℚ) - 1)
  upC : 0 ≤ T.ℓhi * (1 - T.μ) * (1 - T.δ) * T.clo / p.ρ
  dn : T.ℓlo * (1 + T.δ) * T.chi * p.ρ * (1000 / 33) + 1000 / (180 * (p.k0 : ℚ) * 33) * p.ρ +
      3 * T.ℓlo / (lam0Q Config.spec * p.Hmin) ≤ 1
  g1 : T.ℓlo ≤ lam0Q Config.spec
  g2 : (1 - T.μ) * lam0Q Config.spec ≤ T.ℓhi
  G1 : F.Δ + 1 ≤ p.G
  GEL : p.G + 1 < 300 * p.k0
  OG : p.G + 2 ≤ 120 * p.k0
  qs0 : 0 < q.qs
  qb0 : 0 < q.qb
  sh : q.q2 ^ q.t0 / q.qs ^ q.t0 + q.A3 * (q.q3 ^ q.t0 / q.qs ^ q.t0) + q.A4 * (q.q4 ^ q.t0 / q.qs ^ q.t0) +
      q.A5 * (q.q5 ^ q.t0 / q.qs ^ q.t0) + q.A6 * (q.q6 ^ q.t0 / q.qs ^ q.t0) + q.A7 * (q.q7 ^ q.t0 / q.qs ^ q.t0) ≤ q.As
  shq : q.q2 ≤ q.qs ∧ q.q3 ≤ q.qs ∧ q.q4 ≤ q.qs ∧ q.q5 ≤ q.qs ∧ q.q6 ≤ q.qs ∧ q.q7 ≤ q.qs
  shA : 0 ≤ q.A1 ∧ 0 ≤ q.q2 ∧ 0 ≤ q.A3 ∧ 0 ≤ q.q3 ∧ 0 ≤ q.A4 ∧ 0 ≤ q.q4 ∧ 0 ≤ q.A5 ∧ 0 ≤ q.q5 ∧ 0 ≤ q.A6 ∧ 0 ≤ q.q6 ∧ 0 ≤ q.A7 ∧ 0 ≤ q.q7
  shb : q.C1 * ((1 / q.Q1) ^ q.t0 / q.qb ^ q.t0) + q.C2 * ((1 / q.Q2) ^ q.t0 / q.qb ^ q.t0) ≤ q.Ab
  shbq : 1 / q.Q1 ≤ q.qb ∧ 1 / q.Q2 ≤ q.qb
  t0 : p.m * q.t0 ≤ p.k0
  yc0 : 0 ≤ T.ylo * T.clo

theorem closedChk.facts {F : FamCfg} {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} {p : ClosedData}
    {q : ClosedDerived} (h : closedChk F Bq dat T p q = true) : ClosedFacts F Bq dat T p q := by
  simp only [closedChk, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨c1a, c1⟩, c2a⟩, c2⟩, c3a⟩, e17⟩, tau0⟩, tauw⟩, c3⟩, rat0⟩, e20⟩, F0⟩, c4a⟩, lpi0⟩, c4⟩, c5a⟩, w50⟩, x1⟩, xm⟩, c5⟩, c6a⟩, c0⟩, cr⟩, c6⟩, bs0⟩, yy0⟩, yy1⟩, c7a⟩, yym⟩, c7⟩, hhi0⟩, hhi1⟩, hlo0⟩, hlo1⟩, helo1⟩, m0⟩, T1⟩, a10⟩, a20⟩, δ1⟩, C1⟩, C10⟩, C2⟩, C20⟩, Q10⟩, Q1⟩, Q20⟩, Q2⟩, ok⟩, hη⟩, hζ⟩, hβ⟩, hηlot⟩, cov0⟩, cov1⟩, k01⟩, ρ0⟩, Hm0⟩, up⟩, upC⟩, dn⟩, g1⟩, g2⟩, G1⟩, GEL⟩, OG⟩, qs0⟩, qb0⟩, sh⟩, shq⟩, shA⟩, shb⟩, shbq⟩, t0⟩, yc0⟩ := h
  exact ⟨c1a, c1, c2a, c2, c3a, e17, tau0, tauw, c3, rat0, e20, F0, c4a, lpi0, c4, c5a, w50, x1, xm, c5, c6a, c0, cr, c6, bs0, yy0, yy1, c7a, yym, c7, hhi0, hhi1, hlo0, hlo1, helo1, m0, T1, a10, a20, δ1, C1, C10, C2, C20, Q10, Q1, Q20, Q2, ok, hη, hζ, hβ, hηlot, cov0, cov1, k01, ρ0, Hm0, up, upC, dn, g1, g2, G1, GEL, OG, qs0, qb0, sh, shq, shA, shb, shbq, t0, yc0⟩

theorem pt_cast (yy hhi hlo : ℚ) (T : ℕ) : PT 1 (yy : ℝ) (hlo : ℝ) (hhi : ℝ) T =
    ((if 1 ≤ yy then 1 - (1 - hhi) ^ T else 1 - (1 - hlo) ^ T : ℚ) : ℝ) := by
  unfold PT
  by_cases h : (1 : ℚ) ≤ yy
  · rw [if_pos (by exact_mod_cast h), if_pos h]; push_cast; ring
  · rw [if_neg (by exact_mod_cast h), if_neg h]; push_cast; ring

theorem mul_div_succ_ge {k m : ℕ} (hm : 0 < m) : k + 1 ≤ m * (k / m + 1) := by
  have h1 := Nat.div_add_mod k m
  have h2 := Nat.mod_lt k hm
  rw [Nat.mul_succ]; omega

/-- **The settlement bound in closed form**, from the checks. -/
theorem eps_closed_gen (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} (p : ClosedData) (q : ClosedDerived)
    (hM : F.mainChk Bq p.κ q.lp q.lpi dat = true) (hf : closedChk F Bq dat T p q = true)
    (E : Env) {k : ℕ} (hk : E.c.k = k) (N : ℕ) (hnb : q.nb * (k / p.m) ≤ nbD E F.Δ p.G p.T + q.nb0) :
    settleEps3E E Bq.toBand (cert2 hM) q.lpi p.G N p.G (p.g * (k / p.m)) (p.j * (k / p.m)) (p.w * (k / p.m))
      (p.ρr * (k / p.m)) p.T p.x p.yy ≤ p.epsS q N (k / p.m) := by
  have f := closedChk.facts hf
  set bsQ : ℚ := 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T) with hbsQ
  have hbs : 1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T = (bsQ : ℝ) := by
    simp only [BandR.toBand_hlo, BandR.toBand_hhi]; rw [pt_cast, hbsQ]; push_cast; ring
  have hF : (0 : ℝ) ≤ 1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ)) := by exact_mod_cast f.F0
  have he2 : (0 : ℝ) ≤ (eOf dat 2 : ℚ) := by exact_mod_cast f.e20
  have h1 : (1 - (1 - Bq.toBand.hhi) ^ F.Δ) ^ (p.G / F.Δ) ≤ (q.A1 : ℝ) :=
    pow_le_of_powUpQ 14 _ (by simp only [BandR.toBand_hhi]; push_cast; ring) rfl f.c1a f.c1
  have h2 : (1 - Bq.toBand.hlo) ^ p.g ≤ (q.q2 : ℝ) :=
    pow_le_of_powUpQ 14 _ (by simp only [BandR.toBand_hlo]; push_cast; ring) rfl f.c2a f.c2
  have h3a : (cert2 hM).e 17 / (cert2 hM).τ ≤ (q.A3 : ℝ) := by
    show ((eOf dat 17 : ℚ) : ℝ) / (F.τ : ℝ) ≤ q.A3; exact_mod_cast f.c3a
  have h3 : (cert2 hM).e 17 ^ p.j / (cert2 hM).τ ^ p.w ≤ (q.q3 : ℝ) := by
    show ((eOf dat 17 : ℚ) : ℝ) ^ p.j / (F.τ : ℝ) ^ p.w ≤ q.q3
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast f.e17) _) (pow_le_powUpQ 14 f.e17 p.j)
      (by exact_mod_cast f.tauw) (powDnQ_le_pow 14 f.tau0 p.w)).trans ?_
    exact_mod_cast f.c3
  have h4a : ((cert2 hM).lp / q.lpi) ^ p.G * (cert2 hM).e 2 * (1 + ((cert2 hM).b - 1) / (1 - (cert2 hM).lr)) ≤
      (q.A4 : ℝ) := by
    show ((q.lp : ℝ) / (q.lpi : ℝ)) ^ p.G * ((eOf dat 2 : ℚ) : ℝ) * (1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ))) ≤ q.A4
    have ra := pow_le_powUpQ 14 f.rat0 p.G
    push_cast at ra
    refine (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right ra he2) hF).trans ?_
    exact_mod_cast f.c4a
  have h4 : (q.lpi : ℝ) ^ p.j ≤ (q.q4 : ℝ) := pow_le_of_powUpQ 14 _ rfl rfl f.lpi0.le f.c4
  have h5a : 1 / (p.x : ℝ) ≤ (q.A5 : ℝ) := by exact_mod_cast f.c5a
  have h5 : (1 + ((p.x : ℝ) - 1) * (1 - Bq.toBand.elo)) ^ p.w / (p.x : ℝ) ^ p.m ≤ (q.q5 : ℝ) := by
    have hb : 1 + ((p.x : ℝ) - 1) * (1 - Bq.toBand.elo) = ((1 + (p.x - 1) * (1 - Bq.elo) : ℚ) : ℝ) := by
      simp only [BandR.toBand_elo]; push_cast; ring
    rw [hb]
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast f.w50) _) (pow_le_powUpQ 14 f.w50 p.w)
      (by exact_mod_cast f.xm) (powDnQ_le_pow 14 (by linarith [f.x1]) p.m)).trans ?_
    exact_mod_cast f.c5
  have h6a : (1 + ((cert2 hM).b - 1) / (1 - (cert2 hM).lr)) / (cert2 hM).c ≤ (q.A6 : ℝ) := by
    show (1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ))) / (F.c : ℝ) ≤ q.A6; exact_mod_cast f.c6a
  have h6 : 1 / (cert2 hM).c ^ p.ρr ≤ (q.q6 : ℝ) := by
    show 1 / (F.c : ℝ) ^ p.ρr ≤ q.q6
    refine (one_div_le_one_div_of_le (by exact_mod_cast f.cr) (powDnQ_le_pow 14 f.c0 _)).trans ?_
    exact_mod_cast f.c6
  have hb0 : 0 < 1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T := by
    rw [hbs]; exact_mod_cast f.bs0
  have hbs0 : (0 : ℚ) < bsQ := f.bs0
  have h7a : (1 / (1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T)) ^ q.nb0 *
      (1 / (p.yy : ℝ)) ^ p.m ≤ (q.A7 : ℝ) := by
    rw [hbs]
    exact_mod_cast f.c7a
  have h7 : (1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T) ^ q.nb /
      (p.yy : ℝ) ^ (p.m + p.ρr) ≤ (q.q7 : ℝ) := by
    rw [hbs]
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast hbs0.le) _) (pow_le_powUpQ 14 hbs0.le q.nb)
      (by exact_mod_cast f.yym) (powDnQ_le_pow 14 f.yy0.le (p.m + p.ρr))).trans ?_
    exact_mod_cast f.c7
  refine (settleEps3E_closed E Bq.toBand (cert2 hM) (t := k / p.m) (g := p.g) (j := p.j) (w := p.w) (ρ := p.ρr)
    (m := p.m) (nb := q.nb) (nb0 := q.nb0) rfl rfl rfl rfl (by rw [hk]; exact Nat.mul_div_le k p.m)
    (by rw [hk]; exact mul_div_succ_ge f.m0) hnb
    (by simp only [BandR.toBand_hhi]; exact_mod_cast f.hhi0) (by simp only [BandR.toBand_hhi]; exact_mod_cast f.hhi1)
    (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo0) (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo1)
    (by simp only [BandR.toBand_elo]; exact_mod_cast f.helo1)
    (by exact_mod_cast f.x1) (by exact_mod_cast f.yy0) (by exact_mod_cast f.yy1) (by exact_mod_cast f.lpi0) he2
    h1 h2 h3a h3 h4a h4 h5a h5 h6a h6 hb0 h7a h7).trans ?_
  have hnEp : (nEp E N : ℝ) ≤ (N : ℝ) + 2 := by
    have := Nat.div_le_self (N + 2) E.c.epochLength
    unfold nEp; exact_mod_cast this
  obtain ⟨-, -, -, -, -, -, -, -, -, -, hA7, hq7⟩ := f.shA
  have hq7' : (0 : ℝ) ≤ (q.A7 : ℝ) * (q.q7 : ℝ) ^ (k / p.m) :=
    mul_nonneg (by exact_mod_cast hA7) (pow_nonneg (by exact_mod_cast hq7) _)
  unfold ClosedData.epsS
  linarith [mul_le_mul_of_nonneg_right hnEp hq7']

/-- One of the band's terms: `exp a · exp (-p0 a)ᵗ ≤ C · (1 / Q)ᵗ`. -/
theorem exp_term_le {a C Q : ℚ} {p0 t : ℕ} (ha0 : 0 ≤ a) (ha : a ≤ 1 - 1 / C) (hC : 0 < C) (hQ0 : 0 < Q)
    (hQ : Q ≤ powDnQ 14 (1 + (p0 : ℚ) * a / 4096) 4096) :
    Real.exp a * Real.exp (-((p0 : ℝ) * a)) ^ t ≤ (C : ℝ) * (1 / (Q : ℝ)) ^ t := by
  have hC' : (0 : ℝ) < C := by exact_mod_cast hC
  have ha' : (a : ℝ) ≤ 1 - 1 / C := by exact_mod_cast ha
  have h1 : 0 < 1 - (a : ℝ) := by
    have : (0 : ℝ) < 1 / C := by positivity
    linarith
  have he : Real.exp a ≤ C := by
    have h2 := Real.add_one_le_exp (-(a : ℝ))
    have h3 : Real.exp (a : ℝ) = (Real.exp (-(a : ℝ)))⁻¹ := by rw [Real.exp_neg, inv_inv]
    have h4 : (Real.exp (-(a : ℝ)))⁻¹ ≤ (1 - (a : ℝ))⁻¹ := inv_anti₀ h1 (by linarith)
    have h5 : (1 - (a : ℝ))⁻¹ ≤ C := by
      rw [inv_le_iff_one_le_mul₀ h1]
      have : 1 / (C : ℝ) * C = 1 := by field_simp
      nlinarith
    linarith
  have hb : (0 : ℚ) ≤ 1 + (p0 : ℚ) * a / 4096 := by positivity
  have hq : Real.exp (-((p0 : ℝ) * a)) ≤ 1 / Q :=
    exp_neg_le_of (a := (p0 : ℝ) * a) (a0 := (p0 : ℝ) * a) (Q := (Q : ℝ)) 4096 (by norm_num) (by positivity) le_rfl
      (by exact_mod_cast hQ0)
      (by have := powDnQ_le_pow 14 hb 4096; push_cast at this; exact (show ((Q : ℚ) : ℝ) ≤ _ by exact_mod_cast hQ).trans this)
  exact mul_le_mul he (pow_le_pow_left₀ (Real.exp_pos _).le hq _) (by positivity) hC'.le

/-- **The estimate's band in closed form**, from the checks. -/
theorem band_closed_gen (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} (p : ClosedData) (q : ClosedDerived)
    (hf : closedChk F Bq dat T p q = true) (k : ℕ) : bandEps T.toTBand (180 * k) ≤ q.bandC (k / p.m) := by
  have f := closedChk.facts hf
  have hyc : T.toTBand.ylo * T.toTBand.clo = ((T.ylo * T.clo : ℚ) : ℝ) := by
    rw [← TBandQ.ylo_cast, ← TBandQ.clo_cast]; push_cast; ring
  have hδ : T.toTBand.δ = (T.δ : ℝ) := rfl
  have hb := bandEps_closed T.toTBand (P := 180 * k) (t := k / p.m) (p0 := 180 * p.m)
    (by rw [Nat.mul_assoc]; exact Nat.mul_le_mul_left _ (Nat.mul_div_le k p.m))
    (by rw [hyc]; exact_mod_cast f.yc0)
    (by rw [hδ]; exact_mod_cast f.δ1)
  rw [hyc, hδ] at hb
  refine hb.trans ?_
  unfold ClosedDerived.bandC
  refine add_le_add ?_ ?_
  · have := exp_term_le (p0 := 180 * p.m) (t := k / p.m) f.a10 f.C1 f.C10 f.Q10 f.Q1
    push_cast at this ⊢; exact this
  · have := exp_term_le (p0 := 180 * p.m) (t := k / p.m) f.a20 f.C2 f.C20 f.Q20 f.Q2
    push_cast at this ⊢; exact this

theorem epsS_nonneg (p : ClosedData) (q : ClosedDerived) (hA : 0 ≤ q.A1 ∧ 0 ≤ q.q2 ∧ 0 ≤ q.A3 ∧ 0 ≤ q.q3 ∧ 0 ≤ q.A4 ∧ 0 ≤ q.q4 ∧
    0 ≤ q.A5 ∧ 0 ≤ q.q5 ∧ 0 ≤ q.A6 ∧ 0 ≤ q.q6 ∧ 0 ≤ q.A7 ∧ 0 ≤ q.q7) (N t : ℕ) : 0 ≤ p.epsS q N t := by
  obtain ⟨a1, q2, a3, q3, a4, q4, a5, q5, a6, q6, a7, q7⟩ := hA
  have c : ∀ x : ℚ, 0 ≤ x → (0 : ℝ) ≤ x := fun x h => by exact_mod_cast h
  have hN : (0 : ℝ) ≤ N := Nat.cast_nonneg _
  have hg : (0 : ℝ) ≤ ((p.g * t : ℕ) : ℝ) := Nat.cast_nonneg _
  have hG : (0 : ℝ) ≤ ((p.G : ℕ) : ℝ) := Nat.cast_nonneg _
  unfold ClosedData.epsS
  have t1 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) (c _ a1)
  have t2 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + 1) (pow_nonneg (c _ q2) t)
  have t3 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) (mul_nonneg (c _ a3) (pow_nonneg (c _ q3) t))
  have t4 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) (mul_nonneg (c _ a4) (pow_nonneg (c _ q4) t))
  have t5 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + 1) (mul_nonneg (c _ a5) (pow_nonneg (c _ q5) t))
  have t6 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + ((p.G : ℕ) : ℝ) + 1) (mul_nonneg (c _ a6) (pow_nonneg (c _ q6) t))
  have t7 := mul_nonneg (by positivity : (0 : ℝ) ≤ (N : ℝ) + 2) (mul_nonneg (c _ a7) (pow_nonneg (c _ q7) t))
  linarith

theorem bandC_nonneg (q : ClosedDerived) (h1 : 0 < q.C1) (h2 : 0 < q.C2) (h3 : 0 < q.Q1) (h4 : 0 < q.Q2) (t : ℕ) :
    0 ≤ q.bandC t := by
  have c : ∀ x : ℚ, 0 < x → (0 : ℝ) < x := fun x h => by exact_mod_cast h
  unfold ClosedDerived.bandC
  have := c _ h1; have := c _ h2; have := c _ h3; have := c _ h4
  positivity

/-- **Finality in closed form, from a certificate's data.** For every depth `k ≥ k0` and horizon `N`,
at `Config.specK k`, a finality violation has probability at most `p.epsC N k`. Three facts about
the rates' growth in `k` (`hnb`, `hLw`, `hNe`) are left to the certificate. -/
theorem finality_closed_gen {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} (p : ClosedData) (q : ClosedDerived)
    (hM : F.mainChk Bq p.κ q.lp q.lpi dat = true) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D)
    (hBq : Bq = F.S.weakest) (hidx : ∀ i : Fin 19, F.idxChk i (dat i) = true) {n : ℕ} (hK : F.S.K = n + 1)
    (T : TBandQ) (hf : closedChk F Bq dat T p q = true)
    (hnb : ∀ k, p.k0 ≤ k → q.nb * (k / p.m) ≤ (300 * k - 180 * k - F.Δ - 3 - p.G + F.Δ) / (p.T + F.Δ) + q.nb0)
    (hLw : ∀ k, p.k0 ≤ k → p.w * (k / p.m) + p.G < 300 * k)
    (hNe : ∀ k, p.k0 ≤ k → p.G + p.g * (k / p.m) + F.Δ + 2 < 300 * k)
    (E : Env) {k : ℕ} (hc : E.c = Config.specK k) (hk : p.k0 ≤ k) (hΔ : E.Δ = F.Δ) (es : Ω → List Event)
    (hMod : Model μ O E es) {N : ℕ} (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hG : GenesisOK E)
    (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β T.ζ)
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ (N / (300 * k) + 2))
    (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) p.ρ (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) p.Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (p.epsC q N k) := by
  have f := closedChk.facts hf
  have hEL : E.c.epochLength = 300 * k := by rw [hc, Config.specK_epochLength]
  have hP : E.c.period = 180 * k := by rw [hc, Config.specK_period]
  have hck : E.c.k = k := by rw [hc]; rfl
  have hk1 : 1 ≤ k := le_trans f.k01 hk
  have hnbD : q.nb * (k / p.m) ≤ nbD E F.Δ p.G p.T + q.nb0 := by
    unfold nbD growLen; rw [hc, Config.specK_epochLength, Config.specK_nonceOffset]; exact hnb k hk
  have h1 := ENNReal.ofReal_le_ofReal (eps_closed_gen F p q hM hf E hck N hnbD)
  have h2 := ENNReal.ofReal_le_ofReal (band_closed_gen F p q hf k)
  have hS0 := epsS_nonneg p q f.shA N (k / p.m)
  have hB0 := bandC_nonneg q f.C10 f.C20 f.Q10 f.Q20 (k / p.m)
  obtain ⟨⟨Δ, c, z, s, d', τ⟩, ⟨η, ζ, β, d, dy, K, ys⟩, famZL, Dz⟩ := F
  simp only at hK
  subst hK
  have hβ1 : β < 1 := by
    have h := (TBandQ.ok_of f.ok).β1
    simp only [TBandQ.toTBand] at h
    have hb := f.hβ
    simp only at hb
    rw [hb]; exact_mod_cast h
  have hρ : (0 : ℝ) < p.ρ := by exact_mod_cast f.ρ0
  have hb := Prob.finality (M := N + p.G + p.g * (k / p.m) + Δ + 2) (Ne := N / (300 * k) + 2) (Tb := T.toTBand)
    es hMod hN hΔ
    (cert3E hM hS hD hBq hidx E.c.epochLength p.G f.G1 (by rw [hEL]; have := f.GEL; omega)) (FamSpec.prod hS)
    (G' := p.g * (k / p.m)) (J := p.j * (k / p.m)) (Lw := p.w * (k / p.m)) (r := p.ρr * (k / p.m)) (T := p.T)
    (x := p.x) (yy := p.yy)
    (by exact_mod_cast f.x1) (by exact_mod_cast f.yy0) (by exact_mod_cast f.yy1) f.T1 le_rfl
    (by simp only [BandR.toBand_hhi]; exact_mod_cast f.hhi1) (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo0)
    (by simp only [BandR.toBand_hlo]; exact_mod_cast f.hlo1) (by simp only [BandR.toBand_elo]; exact_mod_cast f.helo1)
    (by rw [hEL]; exact hLw k hk) (by rw [hEL, hc, Config.specK_nonceOffset]; have := f.OG; omega)
    (by rw [hc]; simp only [TBandQ.toTBand, f.hηlot]; exact lotConsts_specK (by convert lot_spec using 2; norm_num) k)
    (TBandQ.ok_of f.ok) (by rw [hc]; rfl) (by rw [hc]; simp only [Config.specK, Config.spec]; norm_num)
    (by rw [hP, hc]; simp only [Config.specK, Config.spec]; positivity) (by rw [hP]; omega) (by rw [hP, hEL]; omega)
    (by rw [hEL, show N + p.G + p.g * (k / p.m) + Δ + 2 = N + (p.G + p.g * (k / p.m) + Δ + 2) by ring]
        exact div_lt_add_two (hNe k hk))
    (mem := FamSpec.mem ⟨η, ζ, β, d, dy, n + 1, ys⟩) (fun _ => rfl)
    (fun k => by have := FamSpec.ok hS k; simp only [TBandQ.toTBand, ← f.hη, ← f.hζ]; exact this)
    (cover_of_chain (by simpa using FamSpec.chained ⟨η, ζ, β, d, dy, n + 1, ys⟩ rfl)
      (by rw [← TBandQ.ylo_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_ylo, memberOfQ_ylo,
        Fin.val_zero]; exact_mod_cast f.cov0)
      (by rw [← TBandQ.Yh_cast]; simp only [FamSpec.mem, FamSpec.mQ, MemberQ.toMember_yhi, memberOfQ_yhi,
        Fin.val_last]; exact_mod_cast f.cov1))
    (fun k => memberOfQ_adv hβ1 (by have hb := f.hβ; simp only at hb; simp only [TBandQ.toTBand, hb]))
    (ρ := p.ρ) (Hmin := p.Hmin) hρ (by exact_mod_cast f.Hm0)
    (by
      rw [hc, lam0_specK]
      have e : ∀ K' P' : ℝ, T.toTBand.ℓhi * K' * (1 - T.toTBand.μ) * (1 - T.toTBand.δ) * T.toTBand.clo * (P' - 1) / p.ρ =
          (T.toTBand.ℓhi * (1 - T.toTBand.μ) * (1 - T.toTBand.δ) * T.toTBand.clo / p.ρ) * K' * (P' - 1) := by
        intros; ring
      rw [e]
      refine hup_of_k0 hk f.k01 ?_ ?_
      · rw [← TBandQ.clo_cast]; simp only [TBandQ.toTBand]; exact_mod_cast f.upC
      · rw [← TBandQ.clo_cast, ← lam0Q_cast]; simp only [TBandQ.toTBand]
        have h := Rat.cast_le (K := ℝ) |>.2 f.up
        push_cast at h ⊢
        linarith)
    (by
      rw [hc, lam0_specK]
      have e : ∀ K' P' : ℝ, T.toTBand.ℓlo * K' * (1 + T.toTBand.δ) * T.toTBand.chi * P' * p.ρ =
          (T.toTBand.ℓlo * (1 + T.toTBand.δ) * T.toTBand.chi * p.ρ) * K' * P' := by intros; ring
      rw [e]
      refine hdn_of_k0 hk f.k01 hρ.le ?_
      rw [← TBandQ.chi_cast, ← lam0Q_cast]; simp only [TBandQ.toTBand]
      have h := Rat.cast_le (K := ℝ) |>.2 f.dn
      push_cast at h ⊢
      linarith)
    (by rw [hc, lam0_specK, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast f.g1)
    (by rw [hc, lam0_specK, ← lam0Q_cast]; simp only [TBandQ.toTBand]; exact_mod_cast f.g2)
    hG hSt hQ hDr hH
  rw [hP] at hb
  refine hb.trans ((add_le_add h1 (mul_le_mul_right h2 _)).trans ?_)
  unfold ClosedData.epsC
  rw [← ENNReal.ofReal_natCast, ← ENNReal.ofReal_mul (by positivity), ← ENNReal.ofReal_add hS0 (by positivity)]

/-- **The short form**: from `t ≥ t0` on, the closed form under one settlement rate and one band rate. -/
theorem epsC_le_short (p : ClosedData) (q : ClosedDerived) {T : TBandQ} {F : FamCfg} {Bq : BandR}
    {dat : Fin 19 → IdxData} (hf : closedChk F Bq dat T p q = true) (N : ℕ) {k : ℕ} (hk : p.k0 ≤ k) : p.epsC q N k ≤ p.epsShort q N k := by
  have f := closedChk.facts hf
  obtain ⟨a1, q2, a3, q3, a4, q4, a5, q5, a6, q6, a7, q7⟩ := f.shA
  obtain ⟨s2, s3, s4, s5, s6, s7⟩ := f.shq
  obtain ⟨b1, b2⟩ := f.shbq
  have c : ∀ x : ℚ, 0 ≤ x → (0 : ℝ) ≤ x := fun x h => by exact_mod_cast h
  have cl : ∀ x y : ℚ, x ≤ y → (x : ℝ) ≤ y := fun x y h => by exact_mod_cast h
  have ht0 : q.t0 ≤ k / p.m := (Nat.le_div_iff_mul_le f.m0).2 (le_trans (by rw [Nat.mul_comm]; exact f.t0) hk)
  set t := k / p.m with ht
  have hqs : (0 : ℝ) < q.qs := by exact_mod_cast f.qs0
  have hqb : (0 : ℝ) < q.qb := by exact_mod_cast f.qb0
  have g : ∀ A r : ℚ, 0 ≤ A → 0 ≤ r → r ≤ q.qs →
      (A : ℝ) * (r : ℝ) ^ t ≤ ((A : ℝ) * ((r : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0)) * (q.qs : ℝ) ^ t :=
    fun A r hA hr hrQ => geom_le_of (c _ hA) (c _ hr) hqs (cl _ _ hrQ) ht0 le_rfl
  have r2 := g 1 q.q2 (by norm_num) q2 s2
  have r3 := g q.A3 q.q3 a3 q3 s3
  have r4 := g q.A4 q.q4 a4 q4 s4
  have r5 := g q.A5 q.q5 a5 q5 s5
  have r6 := g q.A6 q.q6 a6 q6 s6
  have r7 := g q.A7 q.q7 a7 q7 s7
  push_cast at r2
  simp only [one_mul] at r2
  have hsh : ((q.q2 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) + (q.A3 : ℝ) * ((q.q3 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) +
      (q.A4 : ℝ) * ((q.q4 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) + (q.A5 : ℝ) * ((q.q5 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) +
      (q.A6 : ℝ) * ((q.q6 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) + (q.A7 : ℝ) * ((q.q7 : ℝ) ^ q.t0 / (q.qs : ℝ) ^ q.t0) ≤ q.As := by
    exact_mod_cast f.sh
  have gb : ∀ C Q : ℚ, 0 < C → 0 < Q → 1 / Q ≤ q.qb →
      (C : ℝ) * (1 / (Q : ℝ)) ^ t ≤ ((C : ℝ) * ((1 / (Q : ℝ)) ^ q.t0 / (q.qb : ℝ) ^ q.t0)) * (q.qb : ℝ) ^ t := by
    intro C Q hC hQ hqQ
    have hQ' : (0 : ℝ) < Q := by exact_mod_cast hQ
    have hq' : 1 / (Q : ℝ) ≤ q.qb := by have := cl _ _ hqQ; push_cast at this; exact this
    exact geom_le_of (c _ hC.le) (by positivity) hqb hq' ht0 le_rfl
  have rb1 := gb q.C1 q.Q1 f.C10 f.Q10 b1
  have rb2 := gb q.C2 q.Q2 f.C20 f.Q20 b2
  have hshb : (q.C1 : ℝ) * ((1 / (q.Q1 : ℝ)) ^ q.t0 / (q.qb : ℝ) ^ q.t0) +
      (q.C2 : ℝ) * ((1 / (q.Q2 : ℝ)) ^ q.t0 / (q.qb : ℝ) ^ q.t0) ≤ q.Ab := by exact_mod_cast f.shb
  -- the coefficients are at most `N + g t + G + 2`
  have hN : (0 : ℝ) ≤ N := Nat.cast_nonneg _
  have hgt : (0 : ℝ) ≤ (p.g : ℝ) * (t : ℝ) := by positivity
  have hG : (0 : ℝ) ≤ (p.G : ℝ) := Nat.cast_nonneg _
  have hX : ∀ i, (0 : ℝ) ≤ (q.qs : ℝ) ^ i := fun i => pow_nonneg hqs.le i
  have hNe : (0 : ℝ) ≤ ((N / (300 * k) + 2 : ℕ) : ℝ) := Nat.cast_nonneg _
  unfold ClosedData.epsC ClosedData.epsS ClosedData.epsShort ClosedDerived.bandC
  push_cast
  set cN : ℝ := (N : ℝ) + (p.g : ℝ) * (t : ℝ) + ((p.G : ℝ) + 2)
  have hcN : 0 ≤ cN := by positivity
  have e1 : ((N : ℝ) + (p.g : ℝ) * (t : ℝ) + 1) * (q.A1 : ℝ) ≤ cN * q.A1 := mul_le_mul_of_nonneg_right (by linarith) (c _ a1)
  have k2 := mul_le_mul (show (N : ℝ) + 1 ≤ cN by linarith) r2 (pow_nonneg (c _ q2) _) hcN
  have k3 := mul_le_mul (show (N : ℝ) + (p.g : ℝ) * (t : ℝ) + 1 ≤ cN by linarith) r3
    (mul_nonneg (c _ a3) (pow_nonneg (c _ q3) _)) hcN
  have k4 := mul_le_mul (show (N : ℝ) + (p.g : ℝ) * (t : ℝ) + 1 ≤ cN by linarith) r4
    (mul_nonneg (c _ a4) (pow_nonneg (c _ q4) _)) hcN
  have k5 := mul_le_mul (show (N : ℝ) + 1 ≤ cN by linarith) r5 (mul_nonneg (c _ a5) (pow_nonneg (c _ q5) _)) hcN
  have k6 := mul_le_mul (show (N : ℝ) + (p.G : ℝ) + 1 ≤ cN by linarith) r6
    (mul_nonneg (c _ a6) (pow_nonneg (c _ q6) _)) hcN
  have k7 := mul_le_mul (show (N : ℝ) + 2 ≤ cN by linarith) r7 (mul_nonneg (c _ a7) (pow_nonneg (c _ q7) _)) hcN
  have ks := mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_right hsh (hX t)) hcN
  have kb := mul_le_mul_of_nonneg_left (add_le_add rb1 rb2) hNe
  have kb2 := mul_le_mul_of_nonneg_left (mul_le_mul_of_nonneg_right hshb (pow_nonneg hqb.le t)) hNe
  simp only [← ht]
  push_cast at kb kb2
  linarith [ks, kb, kb2, k2, k3, k4, k5, k6, k7, e1]

end FamCfg

end Cryptarchia.Prob

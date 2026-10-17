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
  /-- the potential's `κ` and contractions -/
  κ : ℚ
  lp : ℚ
  lpi : ℚ
  /-- the phase cut, and the rates per `t = k / m`: empty runs `g t`, spans of `j t` phases and
  `w t` slots, reach `ρr t`; the growth block `T` -/
  G : ℕ
  g : ℕ
  j : ℕ
  w : ℕ
  ρr : ℕ
  T : ℕ
  m : ℕ
  /-- growth blocks per `t`, less `nb0` -/
  nb : ℕ
  nb0 : ℕ
  /-- the least depth -/
  k0 : ℕ
  /-- the tilts, the stake drift per epoch, the minimum honest stake -/
  x : ℚ
  yy : ℚ
  ρ : ℚ
  Hmin : ℚ
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

namespace ClosedData

variable (p : ClosedData)

/-- **The settlement bound's closed form**, `t = k / m`. -/
noncomputable def epsS (N t : ℕ) : ℝ :=
  ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * p.A1 + ((N : ℝ) + 1) * (p.q2 : ℝ) ^ t +
    ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * (p.A3 * (p.q3 : ℝ) ^ t) +
    ((N : ℝ) + ((p.g * t : ℕ) : ℝ) + 1) * (p.A4 * (p.q4 : ℝ) ^ t) +
    ((N : ℝ) + 1) * (p.A5 * (p.q5 : ℝ) ^ t) + ((N : ℝ) + ((p.G : ℕ) : ℝ) + 1) * (p.A6 * (p.q6 : ℝ) ^ t) +
    ((N : ℝ) + 2) * (p.A7 * (p.q7 : ℝ) ^ t)

/-- The band's closed form per epoch. -/
noncomputable def bandC (t : ℕ) : ℝ := p.C1 * (1 / (p.Q1 : ℝ)) ^ t + p.C2 * (1 / (p.Q2 : ℝ)) ^ t

/-- **The bound in closed form**: `epsS` plus the band in each of the `N / (300 k) + 2` epochs. -/
noncomputable def epsC (N k : ℕ) : ℝ := p.epsS N (k / p.m) + ((N / (300 * k) + 2 : ℕ) : ℝ) * p.bandC (k / p.m)

/-- **The short form**: one settlement rate and one band rate. -/
noncomputable def epsShort (N k : ℕ) : ℝ :=
  ((N : ℝ) + p.g * ((k / p.m : ℕ) : ℝ) + ((p.G + 2 : ℕ) : ℝ)) * (p.A1 + p.As * (p.qs : ℝ) ^ (k / p.m)) +
    ((N / (300 * k) + 2 : ℕ) : ℝ) * (p.Ab * (p.qb : ℝ) ^ (k / p.m))

end ClosedData

namespace FamCfg

/-- **Every numeric condition of a closed-form certificate.** -/
def closedChk (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData) (T : TBandQ) (p : ClosedData) : Bool :=
  decide (0 ≤ 1 - (1 - Bq.hhi) ^ F.Δ) &&
    decide (powUpQ 14 (1 - (1 - Bq.hhi) ^ F.Δ) (p.G / F.Δ) ≤ p.A1) &&
    decide (0 ≤ 1 - Bq.hlo) &&
    decide (powUpQ 14 (1 - Bq.hlo) p.g ≤ p.q2) &&
    decide (eOf dat 17 / F.τ ≤ p.A3) &&
    decide (0 ≤ eOf dat 17) &&
    decide (0 ≤ F.τ) &&
    decide (0 < powDnQ 14 F.τ p.w) &&
    decide (powUpQ 14 (eOf dat 17) p.j / powDnQ 14 F.τ p.w ≤ p.q3) &&
    decide (0 ≤ p.lp / p.lpi) &&
    decide (0 ≤ eOf dat 2) &&
    decide (0 ≤ 1 + (bOf dat - 1) / (1 - lrOf dat)) &&
    decide (powUpQ 14 (p.lp / p.lpi) p.G * eOf dat 2 * (1 + (bOf dat - 1) / (1 - lrOf dat)) ≤ p.A4) &&
    decide (0 < p.lpi) &&
    decide (powUpQ 14 p.lpi p.j ≤ p.q4) &&
    decide (1 / p.x ≤ p.A5) &&
    decide (0 ≤ 1 + (p.x - 1) * (1 - Bq.elo)) &&
    decide (1 ≤ p.x) &&
    decide (0 < powDnQ 14 p.x p.m) &&
    decide (powUpQ 14 (1 + (p.x - 1) * (1 - Bq.elo)) p.w / powDnQ 14 p.x p.m ≤ p.q5) &&
    decide ((1 + (bOf dat - 1) / (1 - lrOf dat)) / F.c ≤ p.A6) &&
    decide (0 ≤ F.c) &&
    decide (0 < powDnQ 14 F.c p.ρr) &&
    decide (1 / powDnQ 14 F.c p.ρr ≤ p.q6) &&
    decide (0 < 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) &&
    decide (0 < p.yy) &&
    decide (p.yy ≤ 1) &&
    decide ((1 / (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T))) ^ p.nb0 *
      (1 / p.yy) ^ p.m ≤ p.A7) &&
    decide (0 < powDnQ 14 p.yy (p.m + p.ρr)) &&
    decide (powUpQ 14 (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) p.nb /
      powDnQ 14 p.yy (p.m + p.ρr) ≤ p.q7) &&
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
    decide (T.ylo * T.clo * T.δ ^ 2 / 2 ≤ 1 - 1 / p.C1) &&
    decide (0 < p.C1) &&
    decide (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ) ≤ 1 - 1 / p.C2) &&
    decide (0 < p.C2) &&
    decide (0 < p.Q1) &&
    decide (p.Q1 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 / 2) / 4096) 4096) &&
    decide (0 < p.Q2) &&
    decide (p.Q2 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) / 4096) 4096) &&
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
    decide (0 < p.qs) &&
    decide (0 < p.qb) &&
    decide (p.q2 ^ p.t0 / p.qs ^ p.t0 + p.A3 * (p.q3 ^ p.t0 / p.qs ^ p.t0) + p.A4 * (p.q4 ^ p.t0 / p.qs ^ p.t0) +
      p.A5 * (p.q5 ^ p.t0 / p.qs ^ p.t0) + p.A6 * (p.q6 ^ p.t0 / p.qs ^ p.t0) + p.A7 * (p.q7 ^ p.t0 / p.qs ^ p.t0) ≤ p.As) &&
    decide (p.q2 ≤ p.qs ∧ p.q3 ≤ p.qs ∧ p.q4 ≤ p.qs ∧ p.q5 ≤ p.qs ∧ p.q6 ≤ p.qs ∧ p.q7 ≤ p.qs) &&
    decide (0 ≤ p.A1 ∧ 0 ≤ p.q2 ∧ 0 ≤ p.A3 ∧ 0 ≤ p.q3 ∧ 0 ≤ p.A4 ∧ 0 ≤ p.q4 ∧ 0 ≤ p.A5 ∧ 0 ≤ p.q5 ∧ 0 ≤ p.A6 ∧ 0 ≤ p.q6 ∧ 0 ≤ p.A7 ∧ 0 ≤ p.q7) &&
    decide (p.C1 * ((1 / p.Q1) ^ p.t0 / p.qb ^ p.t0) + p.C2 * ((1 / p.Q2) ^ p.t0 / p.qb ^ p.t0) ≤ p.Ab) &&
    decide (1 / p.Q1 ≤ p.qb ∧ 1 / p.Q2 ≤ p.qb) &&
    decide (p.m * p.t0 ≤ p.k0) &&
    decide (0 ≤ T.ylo * T.clo)

/-- The conditions `closedChk` checks, by name. -/
structure ClosedFacts (F : FamCfg) (Bq : BandR) (dat : Fin 19 → IdxData) (T : TBandQ) (p : ClosedData) : Prop where
  c1a : 0 ≤ 1 - (1 - Bq.hhi) ^ F.Δ
  c1 : powUpQ 14 (1 - (1 - Bq.hhi) ^ F.Δ) (p.G / F.Δ) ≤ p.A1
  c2a : 0 ≤ 1 - Bq.hlo
  c2 : powUpQ 14 (1 - Bq.hlo) p.g ≤ p.q2
  c3a : eOf dat 17 / F.τ ≤ p.A3
  e17 : 0 ≤ eOf dat 17
  tau0 : 0 ≤ F.τ
  tauw : 0 < powDnQ 14 F.τ p.w
  c3 : powUpQ 14 (eOf dat 17) p.j / powDnQ 14 F.τ p.w ≤ p.q3
  rat0 : 0 ≤ p.lp / p.lpi
  e20 : 0 ≤ eOf dat 2
  F0 : 0 ≤ 1 + (bOf dat - 1) / (1 - lrOf dat)
  c4a : powUpQ 14 (p.lp / p.lpi) p.G * eOf dat 2 * (1 + (bOf dat - 1) / (1 - lrOf dat)) ≤ p.A4
  lpi0 : 0 < p.lpi
  c4 : powUpQ 14 p.lpi p.j ≤ p.q4
  c5a : 1 / p.x ≤ p.A5
  w50 : 0 ≤ 1 + (p.x - 1) * (1 - Bq.elo)
  x1 : 1 ≤ p.x
  xm : 0 < powDnQ 14 p.x p.m
  c5 : powUpQ 14 (1 + (p.x - 1) * (1 - Bq.elo)) p.w / powDnQ 14 p.x p.m ≤ p.q5
  c6a : (1 + (bOf dat - 1) / (1 - lrOf dat)) / F.c ≤ p.A6
  c0 : 0 ≤ F.c
  cr : 0 < powDnQ 14 F.c p.ρr
  c6 : 1 / powDnQ 14 F.c p.ρr ≤ p.q6
  bs0 : 0 < 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)
  yy0 : 0 < p.yy
  yy1 : p.yy ≤ 1
  c7a : (1 / (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T))) ^ p.nb0 *
      (1 / p.yy) ^ p.m ≤ p.A7
  yym : 0 < powDnQ 14 p.yy (p.m + p.ρr)
  c7 : powUpQ 14 (1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T)) p.nb /
      powDnQ 14 p.yy (p.m + p.ρr) ≤ p.q7
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
  C1 : T.ylo * T.clo * T.δ ^ 2 / 2 ≤ 1 - 1 / p.C1
  C10 : 0 < p.C1
  C2 : T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ) ≤ 1 - 1 / p.C2
  C20 : 0 < p.C2
  Q10 : 0 < p.Q1
  Q1 : p.Q1 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 / 2) / 4096) 4096
  Q20 : 0 < p.Q2
  Q2 : p.Q2 ≤ powDnQ 14 (1 + (180 * p.m : ℕ) * (T.ylo * T.clo * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)) / 4096) 4096
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
  qs0 : 0 < p.qs
  qb0 : 0 < p.qb
  sh : p.q2 ^ p.t0 / p.qs ^ p.t0 + p.A3 * (p.q3 ^ p.t0 / p.qs ^ p.t0) + p.A4 * (p.q4 ^ p.t0 / p.qs ^ p.t0) +
      p.A5 * (p.q5 ^ p.t0 / p.qs ^ p.t0) + p.A6 * (p.q6 ^ p.t0 / p.qs ^ p.t0) + p.A7 * (p.q7 ^ p.t0 / p.qs ^ p.t0) ≤ p.As
  shq : p.q2 ≤ p.qs ∧ p.q3 ≤ p.qs ∧ p.q4 ≤ p.qs ∧ p.q5 ≤ p.qs ∧ p.q6 ≤ p.qs ∧ p.q7 ≤ p.qs
  shA : 0 ≤ p.A1 ∧ 0 ≤ p.q2 ∧ 0 ≤ p.A3 ∧ 0 ≤ p.q3 ∧ 0 ≤ p.A4 ∧ 0 ≤ p.q4 ∧ 0 ≤ p.A5 ∧ 0 ≤ p.q5 ∧ 0 ≤ p.A6 ∧ 0 ≤ p.q6 ∧ 0 ≤ p.A7 ∧ 0 ≤ p.q7
  shb : p.C1 * ((1 / p.Q1) ^ p.t0 / p.qb ^ p.t0) + p.C2 * ((1 / p.Q2) ^ p.t0 / p.qb ^ p.t0) ≤ p.Ab
  shbq : 1 / p.Q1 ≤ p.qb ∧ 1 / p.Q2 ≤ p.qb
  t0 : p.m * p.t0 ≤ p.k0
  yc0 : 0 ≤ T.ylo * T.clo

theorem closedChk.facts {F : FamCfg} {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} {p : ClosedData}
    (h : closedChk F Bq dat T p = true) : ClosedFacts F Bq dat T p := by
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
theorem eps_closed_gen (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} (p : ClosedData)
    (hM : F.mainChk Bq p.κ p.lp p.lpi dat = true) (hf : closedChk F Bq dat T p = true)
    (E : Env) {k : ℕ} (hk : E.c.k = k) (N : ℕ) (hnb : p.nb * (k / p.m) ≤ nbD E F.Δ p.G p.T + p.nb0) :
    settleEps3E E Bq.toBand (cert2 hM) p.lpi p.G N p.G (p.g * (k / p.m)) (p.j * (k / p.m)) (p.w * (k / p.m))
      (p.ρr * (k / p.m)) p.T p.x p.yy ≤ p.epsS N (k / p.m) := by
  have f := closedChk.facts hf
  set bsQ : ℚ := 1 + (p.yy - 1) * (if 1 ≤ p.yy then 1 - (1 - Bq.hhi) ^ p.T else 1 - (1 - Bq.hlo) ^ p.T) with hbsQ
  have hbs : 1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T = (bsQ : ℝ) := by
    simp only [BandR.toBand_hlo, BandR.toBand_hhi]; rw [pt_cast, hbsQ]; push_cast; ring
  have hF : (0 : ℝ) ≤ 1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ)) := by exact_mod_cast f.F0
  have he2 : (0 : ℝ) ≤ (eOf dat 2 : ℚ) := by exact_mod_cast f.e20
  have h1 : (1 - (1 - Bq.toBand.hhi) ^ F.Δ) ^ (p.G / F.Δ) ≤ (p.A1 : ℝ) :=
    pow_le_of_powUpQ 14 _ (by simp only [BandR.toBand_hhi]; push_cast; ring) rfl f.c1a f.c1
  have h2 : (1 - Bq.toBand.hlo) ^ p.g ≤ (p.q2 : ℝ) :=
    pow_le_of_powUpQ 14 _ (by simp only [BandR.toBand_hlo]; push_cast; ring) rfl f.c2a f.c2
  have h3a : (cert2 hM).e 17 / (cert2 hM).τ ≤ (p.A3 : ℝ) := by
    show ((eOf dat 17 : ℚ) : ℝ) / (F.τ : ℝ) ≤ p.A3; exact_mod_cast f.c3a
  have h3 : (cert2 hM).e 17 ^ p.j / (cert2 hM).τ ^ p.w ≤ (p.q3 : ℝ) := by
    show ((eOf dat 17 : ℚ) : ℝ) ^ p.j / (F.τ : ℝ) ^ p.w ≤ p.q3
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast f.e17) _) (pow_le_powUpQ 14 f.e17 p.j)
      (by exact_mod_cast f.tauw) (powDnQ_le_pow 14 f.tau0 p.w)).trans ?_
    exact_mod_cast f.c3
  have h4a : ((cert2 hM).lp / p.lpi) ^ p.G * (cert2 hM).e 2 * (1 + ((cert2 hM).b - 1) / (1 - (cert2 hM).lr)) ≤
      (p.A4 : ℝ) := by
    show ((p.lp : ℝ) / (p.lpi : ℝ)) ^ p.G * ((eOf dat 2 : ℚ) : ℝ) * (1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ))) ≤ p.A4
    have ra := pow_le_powUpQ 14 f.rat0 p.G
    push_cast at ra
    refine (mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right ra he2) hF).trans ?_
    exact_mod_cast f.c4a
  have h4 : (p.lpi : ℝ) ^ p.j ≤ (p.q4 : ℝ) := pow_le_of_powUpQ 14 _ rfl rfl f.lpi0.le f.c4
  have h5a : 1 / (p.x : ℝ) ≤ (p.A5 : ℝ) := by exact_mod_cast f.c5a
  have h5 : (1 + ((p.x : ℝ) - 1) * (1 - Bq.toBand.elo)) ^ p.w / (p.x : ℝ) ^ p.m ≤ (p.q5 : ℝ) := by
    have hb : 1 + ((p.x : ℝ) - 1) * (1 - Bq.toBand.elo) = ((1 + (p.x - 1) * (1 - Bq.elo) : ℚ) : ℝ) := by
      simp only [BandR.toBand_elo]; push_cast; ring
    rw [hb]
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast f.w50) _) (pow_le_powUpQ 14 f.w50 p.w)
      (by exact_mod_cast f.xm) (powDnQ_le_pow 14 (by linarith [f.x1]) p.m)).trans ?_
    exact_mod_cast f.c5
  have h6a : (1 + ((cert2 hM).b - 1) / (1 - (cert2 hM).lr)) / (cert2 hM).c ≤ (p.A6 : ℝ) := by
    show (1 + ((bOf dat : ℚ) - 1) / (1 - (lrOf dat : ℚ))) / (F.c : ℝ) ≤ p.A6; exact_mod_cast f.c6a
  have h6 : 1 / (cert2 hM).c ^ p.ρr ≤ (p.q6 : ℝ) := by
    show 1 / (F.c : ℝ) ^ p.ρr ≤ p.q6
    refine (one_div_le_one_div_of_le (by exact_mod_cast f.cr) (powDnQ_le_pow 14 f.c0 _)).trans ?_
    exact_mod_cast f.c6
  have hb0 : 0 < 1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T := by
    rw [hbs]; exact_mod_cast f.bs0
  have hbs0 : (0 : ℚ) < bsQ := f.bs0
  have h7a : (1 / (1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T)) ^ p.nb0 *
      (1 / (p.yy : ℝ)) ^ p.m ≤ (p.A7 : ℝ) := by
    rw [hbs]
    exact_mod_cast f.c7a
  have h7 : (1 + ((p.yy : ℝ) - 1) * PT 1 (p.yy : ℝ) Bq.toBand.hlo Bq.toBand.hhi p.T) ^ p.nb /
      (p.yy : ℝ) ^ (p.m + p.ρr) ≤ (p.q7 : ℝ) := by
    rw [hbs]
    refine (div_le_div_of_bounds (pow_nonneg (by exact_mod_cast hbs0.le) _) (pow_le_powUpQ 14 hbs0.le p.nb)
      (by exact_mod_cast f.yym) (powDnQ_le_pow 14 f.yy0.le (p.m + p.ρr))).trans ?_
    exact_mod_cast f.c7
  refine (settleEps3E_closed E Bq.toBand (cert2 hM) (t := k / p.m) (g := p.g) (j := p.j) (w := p.w) (ρ := p.ρr)
    (m := p.m) (nb := p.nb) (nb0 := p.nb0) rfl rfl rfl rfl (by rw [hk]; exact Nat.mul_div_le k p.m)
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
  have hq7' : (0 : ℝ) ≤ (p.A7 : ℝ) * (p.q7 : ℝ) ^ (k / p.m) :=
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
theorem band_closed_gen (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} {T : TBandQ} (p : ClosedData)
    (hf : closedChk F Bq dat T p = true) (k : ℕ) : bandEps T.toTBand (180 * k) ≤ p.bandC (k / p.m) := by
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
  unfold ClosedData.bandC
  refine add_le_add ?_ ?_
  · have := exp_term_le (p0 := 180 * p.m) (t := k / p.m) f.a10 f.C1 f.C10 f.Q10 f.Q1
    push_cast at this ⊢; exact this
  · have := exp_term_le (p0 := 180 * p.m) (t := k / p.m) f.a20 f.C2 f.C20 f.Q20 f.Q2
    push_cast at this ⊢; exact this

theorem epsS_nonneg (p : ClosedData) (hA : 0 ≤ p.A1 ∧ 0 ≤ p.q2 ∧ 0 ≤ p.A3 ∧ 0 ≤ p.q3 ∧ 0 ≤ p.A4 ∧ 0 ≤ p.q4 ∧
    0 ≤ p.A5 ∧ 0 ≤ p.q5 ∧ 0 ≤ p.A6 ∧ 0 ≤ p.q6 ∧ 0 ≤ p.A7 ∧ 0 ≤ p.q7) (N t : ℕ) : 0 ≤ p.epsS N t := by
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

theorem bandC_nonneg (p : ClosedData) (h1 : 0 < p.C1) (h2 : 0 < p.C2) (h3 : 0 < p.Q1) (h4 : 0 < p.Q2) (t : ℕ) :
    0 ≤ p.bandC t := by
  have c : ∀ x : ℚ, 0 < x → (0 : ℝ) < x := fun x h => by exact_mod_cast h
  unfold ClosedData.bandC
  have := c _ h1; have := c _ h2; have := c _ h3; have := c _ h4
  positivity

/-- **Finality in closed form, from a certificate's data.** For every depth `k ≥ k0` and horizon `N`,
at `Config.specK k`, a finality violation has probability at most `p.epsC N k`. Three facts about
the rates' growth in `k` (`hnb`, `hLw`, `hNe`) are left to the certificate. -/
theorem finality_closed_gen {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
    (F : FamCfg) {Bq : BandR} {dat : Fin 19 → IdxData} (p : ClosedData)
    (hM : F.mainChk Bq p.κ p.lp p.lpi dat = true) (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D)
    (hBq : Bq = F.S.weakest) (hidx : ∀ i : Fin 19, F.idxChk i (dat i) = true) {n : ℕ} (hK : F.S.K = n + 1)
    (T : TBandQ) (hf : closedChk F Bq dat T p = true)
    (hnb : ∀ k, p.k0 ≤ k → p.nb * (k / p.m) ≤ (300 * k - 180 * k - F.Δ - 3 - p.G + F.Δ) / (p.T + F.Δ) + p.nb0)
    (hLw : ∀ k, p.k0 ≤ k → p.w * (k / p.m) + p.G < 300 * k)
    (hNe : ∀ k, p.k0 ≤ k → p.G + p.g * (k / p.m) + F.Δ + 2 < 300 * k)
    (E : Env) {k : ℕ} (hc : E.c = Config.specK k) (hk : p.k0 ≤ k) (hΔ : E.Δ = F.Δ) (es : Ω → List Event)
    (hMod : Model μ O E es) {N : ℕ} (hN : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N) (hG : GenesisOK E)
    (hSt : ∀ ω, Exec.StakeOK E (O ω) (es ω) T.β T.ζ)
    (hQ : ∀ ω, Exec.ChainQuality E (O ω) (es ω) T.μ (N / (300 * k) + 2))
    (hDr : ∀ ω, Exec.StakeDrift E (O ω) (es ω) p.ρ (N / (300 * k) + 2))
    (hH : ∀ ω, Exec.MinStake E (O ω) (es ω) p.Hmin) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (p.epsC N k) := by
  have f := closedChk.facts hf
  have hEL : E.c.epochLength = 300 * k := by rw [hc, Config.specK_epochLength]
  have hP : E.c.period = 180 * k := by rw [hc, Config.specK_period]
  have hck : E.c.k = k := by rw [hc]; rfl
  have hk1 : 1 ≤ k := le_trans f.k01 hk
  have hnbD : p.nb * (k / p.m) ≤ nbD E F.Δ p.G p.T + p.nb0 := by
    unfold nbD growLen; rw [hc, Config.specK_epochLength, Config.specK_nonceOffset]; exact hnb k hk
  have h1 := ENNReal.ofReal_le_ofReal (eps_closed_gen F p hM hf E hck N hnbD)
  have h2 := ENNReal.ofReal_le_ofReal (band_closed_gen F p hf k)
  have hS0 := epsS_nonneg p f.shA N (k / p.m)
  have hB0 := bandC_nonneg p f.C10 f.C20 f.Q10 f.Q20 (k / p.m)
  obtain ⟨⟨η, ζ, β, d, dy, K, ys⟩, famZL, Dz, Δ, c, z, s, d', τ⟩ := F
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
theorem epsC_le_short (p : ClosedData) {T : TBandQ} {F : FamCfg} {Bq : BandR} {dat : Fin 19 → IdxData}
    (hf : closedChk F Bq dat T p = true) (N : ℕ) {k : ℕ} (hk : p.k0 ≤ k) : p.epsC N k ≤ p.epsShort N k := by
  have f := closedChk.facts hf
  obtain ⟨a1, q2, a3, q3, a4, q4, a5, q5, a6, q6, a7, q7⟩ := f.shA
  obtain ⟨s2, s3, s4, s5, s6, s7⟩ := f.shq
  obtain ⟨b1, b2⟩ := f.shbq
  have c : ∀ x : ℚ, 0 ≤ x → (0 : ℝ) ≤ x := fun x h => by exact_mod_cast h
  have cl : ∀ x y : ℚ, x ≤ y → (x : ℝ) ≤ y := fun x y h => by exact_mod_cast h
  have ht0 : p.t0 ≤ k / p.m := (Nat.le_div_iff_mul_le f.m0).2 (le_trans (by rw [Nat.mul_comm]; exact f.t0) hk)
  set t := k / p.m with ht
  have hqs : (0 : ℝ) < p.qs := by exact_mod_cast f.qs0
  have hqb : (0 : ℝ) < p.qb := by exact_mod_cast f.qb0
  have g : ∀ A q : ℚ, 0 ≤ A → 0 ≤ q → q ≤ p.qs →
      (A : ℝ) * (q : ℝ) ^ t ≤ ((A : ℝ) * ((q : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0)) * (p.qs : ℝ) ^ t :=
    fun A q hA hq hqQ => geom_le_of (c _ hA) (c _ hq) hqs (cl _ _ hqQ) ht0 le_rfl
  have r2 := g 1 p.q2 (by norm_num) q2 s2
  have r3 := g p.A3 p.q3 a3 q3 s3
  have r4 := g p.A4 p.q4 a4 q4 s4
  have r5 := g p.A5 p.q5 a5 q5 s5
  have r6 := g p.A6 p.q6 a6 q6 s6
  have r7 := g p.A7 p.q7 a7 q7 s7
  push_cast at r2
  simp only [one_mul] at r2
  have hsh : ((p.q2 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) + (p.A3 : ℝ) * ((p.q3 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) +
      (p.A4 : ℝ) * ((p.q4 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) + (p.A5 : ℝ) * ((p.q5 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) +
      (p.A6 : ℝ) * ((p.q6 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) + (p.A7 : ℝ) * ((p.q7 : ℝ) ^ p.t0 / (p.qs : ℝ) ^ p.t0) ≤ p.As := by
    exact_mod_cast f.sh
  have gb : ∀ C Q : ℚ, 0 < C → 0 < Q → 1 / Q ≤ p.qb →
      (C : ℝ) * (1 / (Q : ℝ)) ^ t ≤ ((C : ℝ) * ((1 / (Q : ℝ)) ^ p.t0 / (p.qb : ℝ) ^ p.t0)) * (p.qb : ℝ) ^ t := by
    intro C Q hC hQ hqQ
    have hQ' : (0 : ℝ) < Q := by exact_mod_cast hQ
    have hq' : 1 / (Q : ℝ) ≤ p.qb := by have := cl _ _ hqQ; push_cast at this; exact this
    exact geom_le_of (c _ hC.le) (by positivity) hqb hq' ht0 le_rfl
  have rb1 := gb p.C1 p.Q1 f.C10 f.Q10 b1
  have rb2 := gb p.C2 p.Q2 f.C20 f.Q20 b2
  have hshb : (p.C1 : ℝ) * ((1 / (p.Q1 : ℝ)) ^ p.t0 / (p.qb : ℝ) ^ p.t0) +
      (p.C2 : ℝ) * ((1 / (p.Q2 : ℝ)) ^ p.t0 / (p.qb : ℝ) ^ p.t0) ≤ p.Ab := by exact_mod_cast f.shb
  -- the coefficients are at most `N + g t + G + 2`
  have hN : (0 : ℝ) ≤ N := Nat.cast_nonneg _
  have hgt : (0 : ℝ) ≤ (p.g : ℝ) * (t : ℝ) := by positivity
  have hG : (0 : ℝ) ≤ (p.G : ℝ) := Nat.cast_nonneg _
  have hX : ∀ i, (0 : ℝ) ≤ (p.qs : ℝ) ^ i := fun i => pow_nonneg hqs.le i
  have hNe : (0 : ℝ) ≤ ((N / (300 * k) + 2 : ℕ) : ℝ) := Nat.cast_nonneg _
  unfold ClosedData.epsC ClosedData.epsS ClosedData.epsShort ClosedData.bandC
  push_cast
  set cN : ℝ := (N : ℝ) + (p.g : ℝ) * (t : ℝ) + ((p.G : ℝ) + 2)
  have hcN : 0 ≤ cN := by positivity
  have e1 : ((N : ℝ) + (p.g : ℝ) * (t : ℝ) + 1) * (p.A1 : ℝ) ≤ cN * p.A1 := mul_le_mul_of_nonneg_right (by linarith) (c _ a1)
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

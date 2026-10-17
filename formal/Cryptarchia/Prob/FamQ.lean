module

public import Cryptarchia.Prob.AutoZ
public import Cryptarchia.Prob.Pick
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

/-!
# Band families computed from their breakpoints

A multi-epoch certificate splits the honest exponent into members `[y k, y (k + 1)]`, each with a
band (`Member`, `Stake.lean`). Here the members are computed from the breakpoints alone, as the
generator computes them (`emit_gen.member_band`, `certE.epoch_members`): each band field is the
bound `Member.OK` asks for, rounded outward to significant digits (`rupQ`, `rdnQ`). So a member
satisfies `Member.OK` and `Band.Prod` once a few numeric side conditions hold (`MemberQ.chk`,
`memberOfQ_OK`, `memberOfQ_prod`), consecutive members chain by construction
(`chained_memberOfQ`), and a certificate states only the breakpoints.
-/

@[expose] public section

namespace Cryptarchia.Prob

/-! ## The bounds of `Member.OK` over `ℚ` -/

def ElQ (y : ℚ) : ℚ := 1 - y + y ^ 2 / 2 - 2 / 9 * y ^ 3

def EhQ (y : ℚ) : ℚ := 1 - y + y ^ 2 / 2

def errLoQ (η ζ Y : ℚ) : ℚ := 2 * (η * Y ^ 2 + ζ)

def errHiQ (η ζ Y : ℚ) : ℚ := 2 * (2 / 9 * Y ^ 3 + η * Y ^ 2 + ζ)

theorem ElQ_cast (y : ℚ) : ((ElQ y : ℚ) : ℝ) = Elo y := by unfold ElQ Elo; push_cast; ring

theorem EhQ_cast (y : ℚ) : ((EhQ y : ℚ) : ℝ) = Ehi y := by unfold EhQ Ehi; push_cast; ring

theorem errLoQ_cast (η ζ Y : ℚ) : ((errLoQ η ζ Y : ℚ) : ℝ) = errLo η ζ Y := by unfold errLoQ errLo; push_cast; ring

theorem errHiQ_cast (η ζ Y : ℚ) : ((errHiQ η ζ Y : ℚ) : ℝ) = errHi η ζ Y := by unfold errHiQ errHi; push_cast; ring

/-! ## Bands and members over `ℚ` -/

/-- A band with rational fields. -/
structure BandR where
  hhi : ℚ
  hlo : ℚ
  amax : ℚ
  hahi : ℚ
  slo : ℚ
  hnlo : ℚ
  elo : ℚ
  alo : ℚ
  halo : ℚ

noncomputable def BandR.toBand (b : BandR) : Band := ⟨b.hhi, b.hlo, b.amax, b.hahi, b.slo, b.hnlo, b.elo, b.alo, b.halo⟩

section Proj
variable (b : BandR)
@[simp] theorem BandR.toBand_hhi : b.toBand.hhi = b.hhi := rfl
@[simp] theorem BandR.toBand_hlo : b.toBand.hlo = b.hlo := rfl
@[simp] theorem BandR.toBand_amax : b.toBand.amax = b.amax := rfl
@[simp] theorem BandR.toBand_hahi : b.toBand.hahi = b.hahi := rfl
@[simp] theorem BandR.toBand_slo : b.toBand.slo = b.slo := rfl
@[simp] theorem BandR.toBand_hnlo : b.toBand.hnlo = b.hnlo := rfl
@[simp] theorem BandR.toBand_elo : b.toBand.elo = b.elo := rfl
@[simp] theorem BandR.toBand_alo : b.toBand.alo = b.alo := rfl
@[simp] theorem BandR.toBand_halo : b.toBand.halo = b.halo := rfl
end Proj

/-- The fields `slot4` reads. -/
def BandR.toQ (b : BandR) : BandQ := ⟨b.hhi, b.hlo, b.amax, b.hahi, b.alo, b.halo⟩

theorem BandR.agrees (b : BandR) : b.toQ.Agrees b.toBand := ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- The fields `slot4` reads, as integers over `D`: exact when `D` clears their denominators,
which `BandZ.Rep` checks. -/
def BandR.toZ (D : ℤ) (b : BandR) : BandZ :=
  ⟨⌊b.hhi * D⌋, ⌊b.hlo * D⌋, ⌊b.amax * D⌋, ⌊b.hahi * D⌋, ⌊b.alo * D⌋, ⌊b.halo * D⌋⟩

/-- The fields `slot4` reads, as integers over `D`, listed: for computing a family's integer
bands once, at elaboration time (`eval%`). -/
def BandR.toZList (D : ℤ) (b : BandR) : List ℤ :=
  [⌊b.hhi * D⌋, ⌊b.hlo * D⌋, ⌊b.amax * D⌋, ⌊b.hahi * D⌋, ⌊b.alo * D⌋, ⌊b.halo * D⌋]

/-- A band's `slot4` fields from their list. -/
def BandZ.ofList (l : List ℤ) : BandZ := ⟨l.getD 0 0, l.getD 1 0, l.getD 2 0, l.getD 3 0, l.getD 4 0, l.getD 5 0⟩

/-- `H` is weaker than `b`, as a check. -/
def BandR.weakerQ (H b : BandR) : Bool :=
  decide (b.hhi ≤ H.hhi) && decide (H.hlo ≤ b.hlo) && decide (b.amax ≤ H.amax) && decide (b.hahi ≤ H.hahi) &&
    decide (H.slo ≤ b.slo) && decide (H.hnlo ≤ b.hnlo) && decide (H.elo ≤ b.elo) && decide (H.alo ≤ b.alo) &&
    decide (H.halo ≤ b.halo)

theorem BandR.weaker_of {H b : BandR} (h : H.weakerQ b = true) : H.toBand.Weaker b.toBand := by
  simp only [BandR.weakerQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax,
    BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo]
  exacts [by exact_mod_cast h1, by exact_mod_cast h2, by exact_mod_cast h3, by exact_mod_cast h4,
    by exact_mod_cast h5, by exact_mod_cast h6, by exact_mod_cast h7, by exact_mod_cast h8, by exact_mod_cast h9]

/-- **The band of a member** with honest exponent in `[ylo, yhi]` and adversarial exponent at
most `ahi`: each field the bound of `Member.OK`, rounded outward to `d` significant digits. -/
def memberBandQ (η ζ : ℚ) (d : ℕ) (ylo yhi ahi : ℚ) : BandR :=
  let P0lo := ElQ yhi * (1 - errLoQ η ζ yhi)
  let P0hi := EhQ ylo * (1 + 2 * errHiQ η ζ yhi)
  let amax := rupQ d (1 - ElQ ahi * (1 - errLoQ η ζ ahi))
  let hhi := rupQ d (1 - P0lo)
  let hlo := rdnQ d (1 - P0hi)
  ⟨hhi, hlo, amax, rupQ d (hhi * amax), rdnQ d (P0lo * (ylo - errHiQ η ζ yhi) * (1 - amax)),
    rdnQ d (hlo * (1 - amax)), rdnQ d (P0lo * (1 - amax)), amax, rdnQ d (hlo * amax)⟩

/-- A member with rational data. -/
structure MemberQ where
  ylo : ℚ
  yhi : ℚ
  ahi : ℚ
  B : BandR

noncomputable def MemberQ.toMember (m : MemberQ) : Member := ⟨m.ylo, m.yhi, m.ahi, m.B.toBand⟩

section Proj
variable (m : MemberQ)
@[simp] theorem MemberQ.toMember_ylo : m.toMember.ylo = m.ylo := rfl
@[simp] theorem MemberQ.toMember_yhi : m.toMember.yhi = m.yhi := rfl
@[simp] theorem MemberQ.toMember_ahi : m.toMember.ahi = m.ahi := rfl
@[simp] theorem MemberQ.toMember_B : m.toMember.B = m.B.toBand := rfl
end Proj

/-- **Member `k` of the family with breakpoints `ys`**: the adversarial bound is
`β / (1 - β)` times the honest one, rounded up to `dy` digits, and the band's fields are
rounded to `d` digits. -/
def memberOfQ (η ζ β : ℚ) (d dy : ℕ) (ys : List ℚ) (k : ℕ) : MemberQ :=
  ⟨ys.getD k 0, ys.getD (k + 1) 0, rupQ dy (β / (1 - β) * ys.getD (k + 1) 0),
    memberBandQ η ζ d (ys.getD k 0) (ys.getD (k + 1) 0) (rupQ dy (β / (1 - β) * ys.getD (k + 1) 0))⟩

section Proj
variable (η ζ β : ℚ) (d dy : ℕ) (ys : List ℚ) (k : ℕ)
@[simp] theorem memberOfQ_ylo : (memberOfQ η ζ β d dy ys k).ylo = ys.getD k 0 := rfl
@[simp] theorem memberOfQ_yhi : (memberOfQ η ζ β d dy ys k).yhi = ys.getD (k + 1) 0 := rfl
end Proj

/-- The numeric conditions a member needs beyond its construction. -/
def MemberQ.chk (η ζ : ℚ) (m : MemberQ) : Bool :=
  decide (0 ≤ m.ylo) && decide (m.ylo ≤ m.yhi) && decide (m.yhi ≤ 1 / 2) && decide (0 ≤ m.ahi) &&
    decide (m.ahi ≤ 1 / 2) && decide (errLoQ η ζ m.yhi ≤ 1) && decide (errLoQ η ζ m.ahi ≤ 1) &&
    decide (errHiQ η ζ m.yhi ≤ 1) && decide (errHiQ η ζ m.yhi ≤ m.ylo) && decide (0 ≤ m.B.amax) &&
    decide (m.B.amax ≤ 1) && decide (0 ≤ m.B.elo)

section Members

variable {η ζ β : ℚ} {d dy : ℕ} {ys : List ℚ} {k : ℕ}

theorem memberOfQ_OK (h : (memberOfQ η ζ β d dy ys k).chk η ζ = true) :
    (memberOfQ η ζ β d dy ys k).toMember.OK η ζ := by
  simp only [MemberQ.chk, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩, -⟩, h11⟩, -⟩ := h
  simp only [memberOfQ, memberBandQ] at h1 h2 h3 h4 h5 h6 h7 h8 h9 h11
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    simp only [MemberQ.toMember_ylo, MemberQ.toMember_yhi, MemberQ.toMember_ahi, MemberQ.toMember_B, BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax, BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo, memberOfQ, memberBandQ, ← ElQ_cast, ← EhQ_cast, ← errLoQ_cast, ← errHiQ_cast]
  exacts [by exact_mod_cast h1, by exact_mod_cast h2,
    by rw [show (1 / 2 : ℝ) = ((1 / 2 : ℚ) : ℝ) by norm_num]; exact_mod_cast h3, by exact_mod_cast h4,
    by rw [show (1 / 2 : ℝ) = ((1 / 2 : ℚ) : ℝ) by norm_num]; exact_mod_cast h5, by exact_mod_cast h6, by exact_mod_cast h7, by exact_mod_cast h8, by exact_mod_cast h9,
    by exact_mod_cast le_rupQ d _, by exact_mod_cast rdnQ_le d _, by exact_mod_cast le_rupQ d _,
    by exact_mod_cast h11, by exact_mod_cast rdnQ_le d _, by exact_mod_cast rdnQ_le d _, by exact_mod_cast rdnQ_le d _]

theorem memberOfQ_prod (h : (memberOfQ η ζ β d dy ys k).chk η ζ = true) :
    (memberOfQ η ζ β d dy ys k).toMember.B.Prod := by
  simp only [MemberQ.chk, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨-, h10⟩, h11⟩, -⟩ := h
  simp only [memberOfQ, memberBandQ] at h10 h11
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> simp only [MemberQ.toMember_ylo, MemberQ.toMember_yhi, MemberQ.toMember_ahi, MemberQ.toMember_B, BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax, BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo, memberOfQ, memberBandQ]
  exacts [by exact_mod_cast h10, by exact_mod_cast h11, le_rfl, by exact_mod_cast le_rupQ d _,
    by exact_mod_cast rdnQ_le d _]

theorem memberOfQ_elo (h : (memberOfQ η ζ β d dy ys k).chk η ζ = true) :
    0 ≤ (memberOfQ η ζ β d dy ys k).toMember.B.elo := by
  simp only [MemberQ.chk, Bool.and_eq_true, decide_eq_true_eq] at h
  simp only [MemberQ.toMember_ylo, MemberQ.toMember_yhi, MemberQ.toMember_ahi, MemberQ.toMember_B, BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax, BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo]
  exact_mod_cast h.2

/-- The adversarial bound covers `β / (1 - β)` times the honest one. -/
theorem memberOfQ_adv (hβ : β < 1) {β' : ℝ} (hb : (β : ℝ) = β') :
    β' * (memberOfQ η ζ β d dy ys k).toMember.yhi ≤ (1 - β') * (memberOfQ η ζ β d dy ys k).toMember.ahi := by
  subst hb
  have h := le_rupQ dy (β / (1 - β) * ys.getD (k + 1) 0)
  have h1 : (0 : ℚ) < 1 - β := by linarith
  have h2 : β * ys.getD (k + 1) 0 ≤ (1 - β) * rupQ dy (β / (1 - β) * ys.getD (k + 1) 0) := by
    calc β * ys.getD (k + 1) 0 = (1 - β) * (β / (1 - β) * ys.getD (k + 1) 0) := by field_simp
      _ ≤ _ := mul_le_mul_of_nonneg_left h h1.le
  simp only [MemberQ.toMember_ylo, MemberQ.toMember_yhi, MemberQ.toMember_ahi, MemberQ.toMember_B, BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax, BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo, memberOfQ]
  exact_mod_cast h2

/-- **Consecutive members chain**: each starts where the previous one ends. -/
theorem chained_memberOfQ (η ζ β : ℚ) (d dy : ℕ) (ys : List ℚ) : ∀ (n j : ℕ),
    Chained (memberOfQ η ζ β d dy ys j).toMember
      (List.ofFn fun k : Fin n => (memberOfQ η ζ β d dy ys (j + k + 1)).toMember)
  | 0, _ => by simp [Chained]
  | n + 1, j => by
    rw [List.ofFn_succ]
    refine ⟨by simp only [MemberQ.toMember_ylo, MemberQ.toMember_yhi, MemberQ.toMember_ahi, MemberQ.toMember_B, BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_amax, BandR.toBand_hahi, BandR.toBand_slo, BandR.toBand_hnlo, BandR.toBand_elo, BandR.toBand_alo, BandR.toBand_halo, memberOfQ, Fin.val_zero, Nat.add_zero], ?_⟩
    have := chained_memberOfQ η ζ β d dy ys n (j + 1)
    simp only [Fin.val_zero, Nat.add_zero, Fin.val_succ] at this ⊢
    convert this using 3
    congr 2
    omega

/-- The crossing bound, rounded down. -/
theorem patQ_le (D : ℕ) (b : BandR) (d : ℕ) :
    ((rdnQ d (b.slo * b.elo ^ D) : ℚ) : ℝ) ≤ b.toBand.slo * b.toBand.elo ^ D := by
  simp only [BandR.toBand_slo, BandR.toBand_elo]
  exact_mod_cast rdnQ_le d _

end Members

end Cryptarchia.Prob

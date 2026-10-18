module

public import Cryptarchia.Prob.AutoZ
public import Cryptarchia.Prob.Pick
public import Cryptarchia.Prob.Tail3E
public import Cryptarchia.Prob.TSIRO
public import Cryptarchia.Prob.ExpBound
public import Cryptarchia.Prob.Final3E

/-!
# Certificates from their data

A multi-epoch certificate is the data a search chose: the band family's breakpoints, the
potential's parameters and the settlement parameters. Everything else is computed, and the
results checked by the kernel; this file holds the generic constructions, so that a certificate
states no proofs of its own.

* `FamSpec`: the band family from its breakpoints, with one check per member (`FamSpec.chk`)
  giving `Member.OK`, `Band.Prod`, the weakest band below it, and its integer bands.
* `FamCfg`, `IdxData`: one phase index's tables, given by seeds computed at elaboration time,
  and the bounds they give; `idxChk` checks them, and `idx_sw`, `idx_one` give what `Cert2E`
  needs from them.
* `Cert2.ofQ`, `FamCfg.cert2E`, `FamCfg.cert3E`: the certificates from the data and the checks.
  The potential's expectations `e i`, `lr` and `b` are the tables' bounds (`eOf`, `lrOf`, `bOf`).
-/

@[expose] public section

namespace Cryptarchia.Prob

/-!
## Band families computed from their breakpoints

A multi-epoch certificate splits the honest exponent into members `[y k, y (k + 1)]`, each with a
band (`Member`, `Stake.lean`). Here the members are computed from the breakpoints alone, as the
generator computes them (`emit_gen.member_band`, `certE.epoch_members`): each band field is the
bound `Member.OK` asks for, rounded outward to significant digits (`rupQ`, `rdnQ`). So a member
satisfies `Member.OK` and `Band.Prod` once a few numeric side conditions hold (`MemberQ.chk`,
`memberOfQ_OK`, `memberOfQ_prod`), consecutive members chain by construction
(`chained_memberOfQ`), and a certificate states only the breakpoints.
-/

section

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

end

/-!
## Numeric bounds by computation

A certificate bounds large powers (`β ^ n` with `n` up to about `10 ^ 5`). `powUpQ` and `powDnQ`
compute them by binary powering, rounding every step outward to `d` significant digits, so
the numbers stay short; each is a bound on the exact power (`pow_le_powUpQ`, `powDnQ_le_pow`).
`settleEps3EQ` is `settleEps3E` with these bounds for its powers, and `settleEps3E_le_Q` bounds
one by the other once a few signs check (`settleChkQ`); likewise `bandEpsQ` for the estimate's
band (`bandEps_le_Q`). A certificate's bounds are then kernel evaluations, with no chain of
numeric steps.
-/

section

theorem rdnQ_nonneg (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : 0 ≤ rdnQ d x := by
  unfold rdnQ
  split_ifs with h
  · exact le_rfl
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    exact mul_nonneg (by exact_mod_cast Int.floor_nonneg.2 (div_nonneg hx hq.le)) hq.le

/-! ## Powers by binary powering, rounded outward -/

/-- `x ^ n` from above: binary powering with fuel `f`, each step rounded up to `d` digits
(the exact power once the fuel runs out). -/
def powUpF (d : ℕ) (x : ℚ) : ℕ → ℕ → ℚ
  | 0, n => x ^ n
  | f + 1, n =>
    if n = 0 then 1 else
      rupQ d (powUpF d x f (n / 2) * powUpF d x f (n / 2) * (if n % 2 = 1 then x else 1))

/-- `x ^ n` from below, likewise. -/
def powDnF (d : ℕ) (x : ℚ) : ℕ → ℕ → ℚ
  | 0, n => x ^ n
  | f + 1, n =>
    if n = 0 then 1 else
      rdnQ d (powDnF d x f (n / 2) * powDnF d x f (n / 2) * (if n % 2 = 1 then x else 1))

/-- `x ^ n` from above, to `d` significant digits. -/
def powUpQ (d : ℕ) (x : ℚ) (n : ℕ) : ℚ := powUpF d x 64 n

/-- `x ^ n` from below, to `d` significant digits. -/
def powDnQ (d : ℕ) (x : ℚ) (n : ℕ) : ℚ := powDnF d x 64 n

theorem pow_split (x : ℚ) (n : ℕ) : x ^ n = x ^ (n / 2) * x ^ (n / 2) * (if n % 2 = 1 then x else 1) := by
  rw [← pow_add]
  split_ifs with h
  · rw [← pow_succ]; congr 1; omega
  · rw [mul_one]; congr 1; omega

theorem pow_le_powUpF (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : ∀ f n, x ^ n ≤ powUpF d x f n
  | 0, n => le_rfl
  | f + 1, n => by
    unfold powUpF
    by_cases h0 : n = 0
    · subst h0; simp
    · rw [if_neg h0]
      have ih := pow_le_powUpF d hx f (n / 2)
      have h1 : 0 ≤ x ^ (n / 2) := pow_nonneg hx _
      have h2 : (0 : ℚ) ≤ if n % 2 = 1 then x else 1 := by split_ifs <;> linarith
      rw [pow_split x n]
      exact le_trans (mul_le_mul_of_nonneg_right (mul_le_mul ih ih h1 (h1.trans ih)) h2) (le_rupQ d _)

theorem powDnF_le_pow (d : ℕ) {x : ℚ} (hx : 0 ≤ x) : ∀ f n, 0 ≤ powDnF d x f n ∧ powDnF d x f n ≤ x ^ n
  | 0, n => ⟨pow_nonneg hx n, le_rfl⟩
  | f + 1, n => by
    unfold powDnF
    by_cases h0 : n = 0
    · subst h0; simp
    · rw [if_neg h0]
      obtain ⟨ih0, ih⟩ := powDnF_le_pow d hx f (n / 2)
      have h2 : (0 : ℚ) ≤ if n % 2 = 1 then x else 1 := by split_ifs <;> linarith
      refine ⟨rdnQ_nonneg d (mul_nonneg (mul_nonneg ih0 ih0) h2), ?_⟩
      rw [pow_split x n]
      exact le_trans (rdnQ_le d _) (mul_le_mul_of_nonneg_right (mul_le_mul ih ih ih0 (ih0.trans ih)) h2)

theorem pow_le_powUpQ (d : ℕ) {x : ℚ} (hx : 0 ≤ x) (n : ℕ) : (x : ℝ) ^ n ≤ (powUpQ d x n : ℝ) := by
  exact_mod_cast pow_le_powUpF d hx 64 n

theorem powDnQ_le_pow (d : ℕ) {x : ℚ} (hx : 0 ≤ x) (n : ℕ) : (powDnQ d x n : ℝ) ≤ (x : ℝ) ^ n := by
  exact_mod_cast (powDnF_le_pow d hx 64 n).2

/-! ## The settlement bound -/

/-- `settleEps3E` over `ℚ`, its powers bounded outward to `d` digits: `k` the depth, `ne` and `nb`
the values of `nEp` and `nbD`. -/
def settleEps3EQ (d Δ : ℕ) (Bq : BandR) (e17 τ lp e2 b lr c lpi x yy : ℚ) (k ne nb Ccap N G G' J Lw r T : ℕ) : ℚ :=
  (N + G' + 1) * powUpQ d (1 - (1 - Bq.hhi) ^ Δ) (G / Δ) +
  (N + 1) * powUpQ d (1 - Bq.hlo) G' +
  (N + G' + 1) * (powUpQ d e17 (J + 1) / powDnQ d τ (Lw + 1)) +
  (N + G' + 1) * (powUpQ d lpi J * powUpQ d (lp / lpi) Ccap * e2 * (1 + (b - 1) / (1 - lr))) +
  (N + 1) * (powUpQ d (1 + (x - 1) * (1 - Bq.elo)) Lw / powDnQ d x (k + 1)) +
  (N + G + 1) * ((1 + (b - 1) / (1 - lr)) / powDnQ d c (r + 1)) +
  ne * (powUpQ d (1 + (yy - 1) * (if 1 ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T)) nb /
    powDnQ d yy (k + r))

/-- The signs `settleEps3E_le_Q` needs. -/
def settleChkQ (d Δ : ℕ) (Bq : BandR) (e17 τ lp e2 b lr c lpi x yy : ℚ) (k Ccap Lw r T : ℕ) : Bool :=
  decide (0 ≤ 1 - (1 - Bq.hhi) ^ Δ) && decide (0 ≤ 1 - Bq.hlo) && decide (0 ≤ e17) &&
    decide (0 < powDnQ d τ (Lw + 1)) && decide (0 ≤ lpi) && decide (0 ≤ lp / lpi) && decide (0 ≤ e2) &&
    decide (0 ≤ 1 + (b - 1) / (1 - lr)) && decide (0 ≤ 1 + (x - 1) * (1 - Bq.elo)) &&
    decide (0 < powDnQ d x (k + 1)) && decide (0 < powDnQ d c (r + 1)) &&
    decide (0 ≤ 1 + (yy - 1) * (if 1 ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T)) &&
    decide (0 ≤ yy) && decide (0 < powDnQ d yy (k + r)) && decide (0 ≤ τ) && decide (0 ≤ x) && decide (0 ≤ c)

theorem div_le_div_of_bounds {a A b B : ℝ} (ha : 0 ≤ a) (hA : a ≤ A) (hB0 : 0 < B) (hB : B ≤ b) : a / b ≤ A / B :=
  div_le_div₀ (ha.trans hA) hA hB0 hB

/-- **The settlement bound, bounded by computation.** -/
theorem settleEps3E_le_Q {Δ : ℕ} {E : Env} {B : Band} (P : Cert2 B Δ) (Bq : BandR) (hB : B = Bq.toBand)
    {d : ℕ} {e17 τ lp e2 b lr c lpi x yy : ℚ} (h17 : P.e 17 = e17) (hτ : P.τ = τ) (hlp : P.lp = lp)
    (h2 : P.e 2 = e2) (hb : P.b = b) (hlr : P.lr = lr) (hc : P.c = c) {k ne nb Ccap N G G' J Lw r T : ℕ}
    (hk : E.c.k = k) (hne : nEp E N = ne) (hnb : nbD E Δ G T = nb)
    (hchk : settleChkQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k Ccap Lw r T = true) :
    settleEps3E E B P lpi Ccap N G G' J Lw r T x yy ≤
      (settleEps3EQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k ne nb Ccap N G G' J Lw r T : ℝ) := by
  simp only [settleChkQ, Bool.and_eq_true, decide_eq_true_eq] at hchk
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨c1, c2⟩, c3⟩, c4⟩, c5⟩, c6⟩, c7⟩, c8⟩, c9⟩, c10⟩, c11⟩, c12⟩, c13⟩, c14⟩, c15⟩, c16⟩, c17⟩ := hchk
  subst hB
  unfold settleEps3E PT settleEps3EQ
  rw [hk, hne, hnb, h17, hτ, hlp, h2, hb, hlr, hc]
  simp only [BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_elo]
  set ptQ : ℚ := if (1 : ℚ) ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T with hptQ
  have hpt : (if (1 : ℝ) ≤ yy then 1 - (1 - (Bq.hhi : ℝ)) ^ T else 1 - (1 - (Bq.hlo : ℝ)) ^ T) = (ptQ : ℝ) := by
    rw [hptQ]
    by_cases h : (1 : ℚ) ≤ yy
    · have hR : (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_pos hR, if_pos h]; push_cast; ring
    · have hR : ¬ (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_neg hR, if_neg h]; push_cast; ring
  rw [hpt]
  have hF : (0 : ℝ) ≤ 1 + ((b : ℝ) - 1) / (1 - lr) := by exact_mod_cast c8
  have e2n : (0 : ℝ) ≤ e2 := by exact_mod_cast c7
  -- each term
  have t1 := pow_le_powUpQ d c1 (G / Δ)
  have t2 := pow_le_powUpQ d c2 G'
  have t3 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c3) _) (pow_le_powUpQ d c3 (J + 1))
    (by exact_mod_cast c4) (powDnQ_le_pow d c15 (Lw + 1))
  have t4a := pow_le_powUpQ d c5 J
  have t4b := pow_le_powUpQ d c6 Ccap
  have hl : (0 : ℝ) ≤ (lpi : ℝ) ^ J := pow_nonneg (by exact_mod_cast c5) _
  have hr : (0 : ℝ) ≤ ((lp / lpi : ℚ) : ℝ) ^ Ccap := pow_nonneg (by exact_mod_cast c6) _
  have t4 := mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right (mul_le_mul t4a t4b hr (hl.trans t4a)) e2n) hF
  have t5 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c9) _) (pow_le_powUpQ d c9 Lw)
    (by exact_mod_cast c10) (powDnQ_le_pow d c16 (k + 1))
  have t6 := div_le_div_of_nonneg_left hF (by exact_mod_cast c11) (powDnQ_le_pow d c17 (r + 1))
  have t7 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c12) _) (pow_le_powUpQ d c12 nb)
    (by exact_mod_cast c14) (powDnQ_le_pow d c13 (k + r))
  push_cast at t1 t2 t3 t4 t5 t6 t7 ⊢
  gcongr
  all_goals first
    | exact t1 | exact t2 | exact t3 | exact t4 | exact t5 | exact t6 | exact t7

/-- **The settlement bound with a failed-check potential's contractions, bounded by computation.** -/
theorem settleEps3G_le_Q {Δ : ℕ} {E : Env} {B : Band} (P : Cert2 B Δ) (Bq : BandR) (hB : B = Bq.toBand)
    {d : ℕ} {e17 τ lp e2 b lr c lpi x yy : ℚ} {lpR e2R : ℝ} (h17 : P.e 17 = e17) (hτ : P.τ = τ) (hlp : lpR = lp)
    (h2 : e2R = e2) (hb : P.b = b) (hlr : P.lr = lr) (hc : P.c = c) {k ne nb Ccap N G G' J Lw r T : ℕ}
    (hk : E.c.k = k) (hne : nEp E N = ne) (hnb : nbD E Δ G T = nb)
    (hchk : settleChkQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k Ccap Lw r T = true) :
    settleEps3G E B P lpR lpi e2R Ccap N G G' J Lw r T x yy ≤
      (settleEps3EQ d Δ Bq e17 τ lp e2 b lr c lpi x yy k ne nb Ccap N G G' J Lw r T : ℝ) := by
  simp only [settleChkQ, Bool.and_eq_true, decide_eq_true_eq] at hchk
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨c1, c2⟩, c3⟩, c4⟩, c5⟩, c6⟩, c7⟩, c8⟩, c9⟩, c10⟩, c11⟩, c12⟩, c13⟩, c14⟩, c15⟩, c16⟩, c17⟩ := hchk
  subst hB
  unfold settleEps3G PT settleEps3EQ
  rw [hk, hne, hnb, h17, hτ, hlp, h2, hb, hlr, hc]
  simp only [BandR.toBand_hhi, BandR.toBand_hlo, BandR.toBand_elo]
  set ptQ : ℚ := if (1 : ℚ) ≤ yy then 1 - (1 - Bq.hhi) ^ T else 1 - (1 - Bq.hlo) ^ T with hptQ
  have hpt : (if (1 : ℝ) ≤ yy then 1 - (1 - (Bq.hhi : ℝ)) ^ T else 1 - (1 - (Bq.hlo : ℝ)) ^ T) = (ptQ : ℝ) := by
    rw [hptQ]
    by_cases h : (1 : ℚ) ≤ yy
    · have hR : (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_pos hR, if_pos h]; push_cast; ring
    · have hR : ¬ (1 : ℝ) ≤ yy := by exact_mod_cast h
      rw [if_neg hR, if_neg h]; push_cast; ring
  rw [hpt]
  have hF : (0 : ℝ) ≤ 1 + ((b : ℝ) - 1) / (1 - lr) := by exact_mod_cast c8
  have e2n : (0 : ℝ) ≤ e2 := by exact_mod_cast c7
  -- each term
  have t1 := pow_le_powUpQ d c1 (G / Δ)
  have t2 := pow_le_powUpQ d c2 G'
  have t3 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c3) _) (pow_le_powUpQ d c3 (J + 1))
    (by exact_mod_cast c4) (powDnQ_le_pow d c15 (Lw + 1))
  have t4a := pow_le_powUpQ d c5 J
  have t4b := pow_le_powUpQ d c6 Ccap
  have hl : (0 : ℝ) ≤ (lpi : ℝ) ^ J := pow_nonneg (by exact_mod_cast c5) _
  have hr : (0 : ℝ) ≤ ((lp / lpi : ℚ) : ℝ) ^ Ccap := pow_nonneg (by exact_mod_cast c6) _
  have t4 := mul_le_mul_of_nonneg_right (mul_le_mul_of_nonneg_right (mul_le_mul t4a t4b hr (hl.trans t4a)) e2n) hF
  have t5 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c9) _) (pow_le_powUpQ d c9 Lw)
    (by exact_mod_cast c10) (powDnQ_le_pow d c16 (k + 1))
  have t6 := div_le_div_of_nonneg_left hF (by exact_mod_cast c11) (powDnQ_le_pow d c17 (r + 1))
  have t7 := div_le_div_of_bounds (pow_nonneg (by exact_mod_cast c12) _) (pow_le_powUpQ d c12 nb)
    (by exact_mod_cast c14) (powDnQ_le_pow d c13 (k + r))
  push_cast at t1 t2 t3 t4 t5 t6 t7 ⊢
  gcongr
  all_goals first
    | exact t1 | exact t2 | exact t3 | exact t4 | exact t5 | exact t6 | exact t7


/-! ## The estimate's band -/

/-- `TBand` with rational constants. -/
structure TBandQ where
  ℓlo : ℚ
  ℓhi : ℚ
  μ : ℚ
  β : ℚ
  δ : ℚ
  η : ℚ
  ζ : ℚ

noncomputable def TBandQ.toTBand (T : TBandQ) : TBand := ⟨T.ℓlo, T.ℓhi, T.μ, T.β, T.δ, T.η, T.ζ⟩

namespace TBandQ

variable (T : TBandQ)

def Yh : ℚ := T.ℓhi / (1 - T.μ)

def ylo : ℚ := (1 - T.β) * T.ℓlo

def clo : ℚ := 1 - T.Yh / 2 - 2 * errHiQ T.η T.ζ T.Yh / T.ylo

theorem ylo_cast : (T.ylo : ℝ) = T.toTBand.ylo := by
  simp only [ylo, TBand.ylo, toTBand]; push_cast; ring

theorem clo_cast : (T.clo : ℝ) = T.toTBand.clo := by
  simp only [clo, TBand.clo, TBand.Yh, TBand.ylo, Yh, ylo, toTBand]; push_cast; rw [errHiQ_cast]; push_cast; ring

/-- The exponents of `bandEps`. -/
def a1 (P : ℕ) : ℚ := ((P : ℚ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 / 2

def a2 (P : ℕ) : ℚ := ((P : ℚ) - 1) * (T.ylo * T.clo) * T.δ ^ 2 * (1 / 2 - 2 / 9 * T.δ)

end TBandQ

/-- `bandEps` from above: `exp (-a) ≤ 1 / (1 + a / n) ^ n`, the power bounded below to `d` digits. -/
def bandEpsQ (d n : ℕ) (T : TBandQ) (P : ℕ) : ℚ :=
  1 / powDnQ d (1 + T.a1 P / n) n + 1 / powDnQ d (1 + T.a2 P / n) n

/-- The signs `bandEps_le_Q` needs. -/
def bandChkQ (d n : ℕ) (T : TBandQ) (P : ℕ) : Bool :=
  decide (0 < n) && decide (0 ≤ T.a1 P) && decide (0 ≤ T.a2 P) && decide (0 < powDnQ d (1 + T.a1 P / n) n) &&
    decide (0 < powDnQ d (1 + T.a2 P / n) n)

/-- **The estimate's band, bounded by computation.** -/
theorem bandEps_le_Q {d n : ℕ} {T : TBandQ} {P : ℕ} (h : bandChkQ d n T P = true) :
    bandEps T.toTBand P ≤ (bandEpsQ d n T P : ℝ) := by
  simp only [bandChkQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨hn, h1⟩, h2⟩, h3⟩, h4⟩ := h
  have e1 : ∀ a : ℚ, 0 ≤ a → 0 < powDnQ d (1 + a / n) n →
      Real.exp (-(a : ℝ)) ≤ ((1 / powDnQ d (1 + a / n) n : ℚ) : ℝ) := fun a ha hp => by
    have hb : (0 : ℚ) ≤ 1 + a / n := by positivity
    have := exp_neg_le_of (a := a) (a0 := a) (Q := (powDnQ d (1 + a / n) n : ℝ)) n hn (by exact_mod_cast ha) le_rfl (by exact_mod_cast hp)
      (by have := powDnQ_le_pow d hb n; push_cast at this; exact this)
    push_cast; exact this
  unfold bandEps bandEpsQ
  push_cast
  have q1 := e1 _ h1 h3
  have q2 := e1 _ h2 h4
  simp only [TBandQ.a1, TBandQ.a2] at q1 q2
  push_cast at q1 q2
  rw [← T.ylo_cast, ← T.clo_cast]
  have hδ : T.toTBand.δ = (T.δ : ℝ) := rfl
  rw [hδ]
  exact add_le_add q1 q2

/-! ## Single powers -/

/-- `b ^ n ≤ q'`, from `powUpQ`. -/
theorem pow_le_of_powUpQ {b q' : ℝ} {bq q : ℚ} (d n : ℕ) (hb : b = bq) (hq : (q : ℝ) = q') (h0 : 0 ≤ bq)
    (h : powUpQ d bq n ≤ q) : b ^ n ≤ q' := by
  subst hb hq
  exact (pow_le_powUpQ d h0 n).trans (by exact_mod_cast h)

/-- `q' ≤ b ^ n`, from `powDnQ`. -/
theorem le_pow_of_powDnQ {b q' : ℝ} {bq q : ℚ} (d n : ℕ) (hb : b = bq) (hq : (q : ℝ) = q') (h0 : 0 ≤ bq)
    (h : q ≤ powDnQ d bq n) : q' ≤ b ^ n := by
  subst hb hq
  exact (show ((q : ℚ) : ℝ) ≤ powDnQ d bq n by exact_mod_cast h).trans (powDnQ_le_pow d h0 n)

end

/-! ## Band families from their breakpoints -/

/-- A band family: member `k` has honest exponent in `[ys k, ys (k + 1)]` (`memberOfQ`). -/
structure FamSpec where
  η : ℚ
  ζ : ℚ
  β : ℚ
  d : ℕ
  dy : ℕ
  K : ℕ
  ys : List ℚ

namespace FamSpec

variable (S : FamSpec)

def mQ (k : Fin S.K) : MemberQ := memberOfQ S.η S.ζ S.β S.d S.dy S.ys k.val

noncomputable def mem (k : Fin S.K) : Member := (S.mQ k).toMember

noncomputable def fam (k : Fin S.K) : Band := (S.mQ k).B.toBand

def famQ (k : Fin S.K) : BandQ := (S.mQ k).B.toQ

/-- Two bands' weakest combination: the larger upper and the smaller lower bounds. -/
def weak2 (H b : BandR) : BandR :=
  ⟨max H.hhi b.hhi, min H.hlo b.hlo, max H.amax b.amax, max H.hahi b.hahi, min H.slo b.slo, min H.hnlo b.hnlo,
    min H.elo b.elo, min H.alo b.alo, min H.halo b.halo⟩

/-- **The weakest band**, weaker than every member's. -/
def weakest : BandR :=
  match (List.finRange S.K).map fun k => (S.mQ k).B with
  | [] => ⟨0, 0, 0, 0, 0, 0, 0, 0, 0⟩
  | b :: bs => bs.foldl weak2 b

/-- The common denominator of the members' `slot4` fields. -/
def DZ : ℤ :=
  ((List.finRange S.K).foldl (fun m k => let b := (S.mQ k).B;
    [b.hhi, b.hlo, b.amax, b.hahi, b.alo, b.halo].foldl (fun m q => Nat.lcm m q.den) m) 1 : ℕ)

/-- The members' integer bands over `D`, listed: computed once, at elaboration time. -/
def famZList (D : ℤ) : List (List ℤ) := (List.finRange S.K).map fun k => (S.mQ k).B.toZList D

/-- Each member's crossing bound. -/
def patQ (Δ : ℕ) (k : Fin S.K) : ℚ := rdnQ 13 ((S.mQ k).B.slo * (S.mQ k).B.elo ^ Δ)

/-- **Every member's checks**: its numeric conditions, the weakest band below it, and its integer
band `famZ k` over `D`. -/
def chk (famZ : Fin S.K → BandZ) (D : ℤ) : Bool :=
  (List.finRange S.K).all fun k => (S.mQ k).chk S.η S.ζ && S.weakest.weakerQ (S.mQ k).B &&
    decide ((famZ k).Rep D (S.famQ k))

section Chk

variable {S} {famZ : Fin S.K → BandZ} {D : ℤ} (h : S.chk famZ D = true)
include h

theorem chk_k (k : Fin S.K) : ((S.mQ k).chk S.η S.ζ && S.weakest.weakerQ (S.mQ k).B &&
    decide ((famZ k).Rep D (S.famQ k))) = true :=
  List.all_eq_true.1 h k (List.mem_finRange k)

theorem ok (k : Fin S.K) : (S.mem k).OK S.η S.ζ := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_OK this.1.1

theorem prod (k : Fin S.K) : (S.fam k).Prod := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_prod this.1.1

theorem elo (k : Fin S.K) : 0 ≤ (S.fam k).elo := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact memberOfQ_elo this.1.1

theorem weak (k : Fin S.K) : S.weakest.toBand.Weaker (S.fam k) := by
  have := chk_k h k; simp only [Bool.and_eq_true] at this; exact BandR.weaker_of this.1.2

theorem rep (k : Fin S.K) : (famZ k).Rep D (S.famQ k) := by
  have := chk_k h k; simp only [Bool.and_eq_true, decide_eq_true_eq] at this; exact this.2

end Chk

theorem agrees (k : Fin S.K) : (S.famQ k).Agrees (S.fam k) := (S.mQ k).B.agrees

theorem pat_le (Δ : ℕ) (k : Fin S.K) : ((S.patQ Δ k : ℚ) : ℝ) ≤ (S.fam k).slo * (S.fam k).elo ^ Δ :=
  patQ_le Δ (S.mQ k).B 13

theorem hfam (k : Fin S.K) : (S.mem k).B = S.fam k := rfl

/-- **Consecutive members chain.** -/
theorem chained {n : ℕ} (hK : S.K = n + 1) :
    Chained (S.mem (hK ▸ 0)) (List.ofFn fun k : Fin n => S.mem (hK ▸ k.succ)) := by
  obtain ⟨η, ζ, β, d, dy, K, ys⟩ := S
  simp only at hK
  subst hK
  simpa only [mem, mQ, Fin.val_zero, Fin.val_succ, Nat.zero_add] using chained_memberOfQ η ζ β d dy ys n 0

end FamSpec

/-! ## One phase index, from its seeds -/

/-- The potential's parameters, and the network delay. -/
structure PotCfg where
  /-- the network delay, in slots -/
  Δ : ℕ
  /-- the potential's base for the reach, and for the margin when cold -/
  c : ℚ
  z : ℚ
  /-- the cold potential's first term's weight, and its second term's base -/
  s : ℚ
  d : ℚ
  /-- the span term's base per slot -/
  τ : ℚ

/-- What a certificate's index checks depend on: the potential's parameters, the band family, and its
integer bands over `D` (listed, as computed once at elaboration time). -/
structure FamCfg extends PotCfg where
  S : FamSpec
  famZL : List (List ℤ)
  D : ℤ

/-- One index's data, computed at elaboration time: each member's post- and pre-switch seeds,
in-epoch bound and the largest pre-switch bound, and the switching table's seeds and largest
bound. -/
structure IdxData where
  post : List (List ℤ)
  pre : List (List ℤ)
  eIn : List ℚ
  eE : ℚ
  vs : List ℤ
  eS : ℚ

namespace FamCfg

variable (F : FamCfg)

def famZ (k : Fin F.S.K) : BandZ := BandZ.ofList (F.famZL.getD k.val [])

def famL : List BandZ := (List.finRange F.S.K).map F.famZ

/-- Phase expectation `i` over the integers. -/
def X (i : ℕ) : PhZ := PhZ.ofQ (xgNQ F.c F.z F.s F.d F.τ i)

/-- The terminal table's entries at `(0, a, true)`, where the seeds start. -/
def floor (i : ℕ) : List ℤ := [gFloorZ (F.X i) SZ 0 0 true, gFloorZ (F.X i) SZ 0 1 true, gFloorZ (F.X i) SZ 0 2 true]

/-- The solver's settings: differences of `2 ^ 32`, a pad of `2 ^ 8`, three Newton steps for the first
member and two for each later one, then up to 200 steps of the recursion. -/
def postSeeds (i : ℕ) : List (List ℤ) :=
  seedsZ F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (2 ^ 32) (2 ^ 8) 3 2 200 F.famL (F.floor i)

def preSeeds (i : ℕ) (post : List (List ℤ)) : List (List ℤ) :=
  preSeedsZ F.famL F.D F.Δ (F.X i) SZ (2 ^ 32) (2 ^ 8) 0 200 post

def swSeeds (i : ℕ) : List ℤ :=
  solveSeedsZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (2 ^ 32) (2 ^ 8) 3 200 (F.floor i)

def postTop (dat : IdxData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (dat.post.getD k.val [])

def preTop (dat : IdxData) (k : Fin F.S.K) : Fin 3 → ℤ := seedL (dat.pre.getD k.val [])

def eIn (dat : IdxData) (k : Fin F.S.K) : ℚ := dat.eIn.getD k.val 0

/-- A table's bound over the integers, as a rational. -/
def boundQ (B : BandZ) (i : ℕ) (v : ℕ → Fin 3 → Bool → ℤ) : ℚ :=
  (autoBoundZ B F.D (F.X i) SZ v : ℚ) / ((F.X i).M F.D * SZ : ℤ)

/-- The members' in-epoch bounds, rounded up to 13 digits. -/
def eInList (i : ℕ) (post : List (List ℤ)) : List ℚ := eInListQ F.famL F.D F.Δ (F.X i) SZ 13 post

/-- The largest pre-switch bound, rounded up to 13 digits. -/
def eEOf (i : ℕ) (post pre : List (List ℤ)) : ℚ :=
  let vm := vmaxListZ F.famL F.D F.Δ (F.X i) SZ post
  (List.zipWith (fun B t => rupQ 13 (F.boundQ B i (tabZ (fillRowsZ [B] F.D F.Δ (F.X i) SZ (tabZ vm) (seedL t) 0 F.Δ))))
    F.famL pre).foldl max 0

/-- The switching table's largest bound, rounded up to 13 digits. -/
def eSOf (i : ℕ) (vs : List ℤ) : ℚ :=
  let v := tabZ (fillRowsZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (seedL vs) 0 F.Δ)
  (F.famL.map fun B => rupQ 13 (F.boundQ B i v)).foldl max 0

/-- The indices with a switching table, and with one-switch tables. -/
def isSw (i : ℕ) : Bool := i == 0 || i == 1 || i == 2 || i == 17

def isOne (i : ℕ) : Bool := !(i == 2 || i == 17)

/-- **Every check of index `i`.** -/
def idxChk (i : ℕ) (dat : IdxData) : Bool :=
  decide ((F.X i).Rep (xgNQ F.c F.z F.s F.d F.τ i).1 (xgNQ F.c F.z F.s F.d F.τ i).2.1 (xgNQ F.c F.z F.s F.d F.τ i).2.2) &&
    (!isSw i || (List.finRange F.S.K).all (chkSwF F.famZ F.D F.Δ (F.X i) SZ (seedL dat.vs) fun _ => dat.eS)) &&
    (!isOne i || (List.finRange F.S.K).all (chkOneF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) (F.preTop dat) (F.eIn dat) dat.eE))

/-- The tables, over `ℝ`. -/
noncomputable def vsR (i : ℕ) (dat : IdxData) : ℕ → Fin 3 → Bool → ℝ :=
  castZ SZ (fillAllZ F.famL F.D F.Δ (F.X i) SZ (gFloorZ (F.X i) SZ) (seedL dat.vs))

noncomputable def vpostR (i : ℕ) (dat : IdxData) (k : Fin F.S.K) : ℕ → Fin 3 → Bool → ℝ :=
  castZ SZ (postF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) k)

noncomputable def vpreR (i : ℕ) (dat : IdxData) (k : Fin F.S.K) : ℕ → Fin 3 → Bool → ℝ :=
  castZ SZ (preF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat) (F.preTop dat) k)

noncomputable def vmaxR (i : ℕ) (dat : IdxData) : ℕ → Fin 3 → Bool → ℝ :=
  castZ SZ (vmaxF F.famZ F.D F.Δ (F.X i) SZ (F.postTop dat))

/-- `xg` at the potential's parameters, over `ℝ`. -/
noncomputable abbrev xgR (i : Fin 19) := xg F.c F.z F.s F.d F.τ i

section Sound

variable {F} (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) {i : Fin 19} {dat : IdxData}
  (h : F.idxChk i dat = true)
include hS hD h

theorem idx_rep : (F.X i).Rep (xgNQ F.c F.z F.s F.d F.τ i).1 (xgNQ F.c F.z F.s F.d F.τ i).2.1
    (xgNQ F.c F.z F.s F.d F.τ i).2.2 := by
  simp only [idxChk, Bool.and_eq_true, decide_eq_true_eq] at h; exact h.1.1

/-- **A switching index's table** solves every member's recursion within its bound. -/
theorem idx_sw (hi : isSw i = true) :
    (∀ k, AutoSol (F.S.fam k) F.Δ (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat)) ∧
      ∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vsR i dat) ≤ dat.eS := by
  have hX := idx_rep hS hD h
  simp only [idxChk, hi, Bool.not_true, Bool.false_or, Bool.and_eq_true] at h
  have := switchF_sound (eS := fun _ => dat.eS) (F.S.rep hS) F.S.agrees hD hX SZ_pos h.1.2
  rw [xgR, xg_ofQ rfl rfl rfl rfl rfl i]
  exact this

/-- **A one-switch index's tables** solve every member's recursions within their bounds. -/
theorem idx_one (hi : isOne i = true) :
    AutoSolE F.S.fam F.Δ (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpreR i dat) (F.vpostR i dat) (F.vmaxR i dat) ∧
      (∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpostR i dat k) ≤ F.eIn dat k) ∧
      ∀ k, autoBound (F.S.fam k) (F.xgR i).1 (F.xgR i).2.1 (F.xgR i).2.2 (F.vpreR i dat k) ≤ dat.eE := by
  have hX := idx_rep hS hD h
  simp only [idxChk, hi, Bool.not_true, Bool.false_or, Bool.and_eq_true] at h
  have := oneSwitchF_sound (F.S.rep hS) F.S.agrees hD hX SZ_pos h.2
  rw [xgR, xg_ofQ rfl rfl rfl rfl rfl i]
  exact this

end Sound

/-! ## The potential's expectations from the tables -/

/-- `e i`: the one-switch bound, or the switching one for indices 2 and 17. -/
def eOf (dat : Fin 19 → IdxData) (i : Fin 19) : ℚ := if isOne i then (dat i).eE else (dat i).eS

def lrOf (dat : Fin 19 → IdxData) : ℚ := max (dat 0).eS (dat 0).eE

def bOf (dat : Fin 19 → IdxData) : ℚ := max (max (dat 1).eS (dat 1).eE) 1

end FamCfg

/-! ## The certificates -/

/-- The basic conditions of `Cert2`, the class conditions and the reach recursion, over `ℚ`. -/
def cert2ChkQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ) : Bool :=
  decide (1 ≤ c) && decide (1 ≤ z) && decide (1 ≤ s) && decide (0 ≤ κ) && decide (0 < d) && decide (d ≤ 1) &&
    decide (s + κ ≤ z) && decide (1 ≤ τ) && decide (0 ≤ lp) && decide (lp < 1) && decide (0 ≤ lr) && decide (lr < 1) &&
    decide (1 ≤ b) && decide (0 ≤ Bq.elo) && decide (0 < Δ) && decide (1 ≤ e 17) && decide (e 0 ≤ lr) && decide (e 1 ≤ b) &&
    classOKQ c z s κ d lp e (Bq.slo * Bq.elo ^ Δ)

/-- The conditions `cert2ChkQ` checks, by name (those `Cert2` uses). -/
structure Cert2FactsQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ) : Prop where
  hc : 1 ≤ c
  hz : 1 ≤ z
  hs : 1 ≤ s
  hκ : 0 ≤ κ
  hd0 : 0 < d
  hd1 : d ≤ 1
  hsz : s + κ ≤ z
  hτ : 1 ≤ τ
  hlp0 : 0 ≤ lp
  hlr0 : 0 ≤ lr
  hlr1 : lr < 1
  hb1 : 1 ≤ b
  helo : 0 ≤ Bq.elo
  hΔ : 0 < Δ
  he17 : 1 ≤ e 17
  cls : classOKQ c z s κ d lp e (Bq.slo * Bq.elo ^ Δ) = true

theorem cert2ChkQ.facts {Bq : BandR} {Δ : ℕ} {c z s κ d τ lp lr b : ℚ} {e : Fin 19 → ℚ}
    (h : cert2ChkQ Bq Δ c z s κ d τ lp lr b e = true) : Cert2FactsQ Bq Δ c z s κ d τ lp lr b e := by
  simp only [cert2ChkQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨hc, hz⟩, hs⟩, hκ⟩, hd0⟩, hd1⟩, hsz⟩, hτ⟩, hlp0⟩, -⟩, hlr0⟩, hlr1⟩, hb1⟩, helo⟩, hΔ⟩, he17⟩, -⟩, -⟩,
    cls⟩ := h
  exact ⟨hc, hz, hs, hκ, hd0, hd1, hsz, hτ, hlp0, hlr0, hlr1, hb1, helo, hΔ, he17, cls⟩

/-- **The potential certificate** from its numbers (`Cert2E` gives the phase bounds). -/
noncomputable def Cert2.ofQ (Bq : BandR) (Δ : ℕ) (c z s κ d τ lp lr b : ℚ) (e : Fin 19 → ℚ)
    (h : cert2ChkQ Bq Δ c z s κ d τ lp lr b e = true) : Cert2 Bq.toBand Δ where
  c := c
  z := z
  s := s
  κ := κ
  d := d
  τ := τ
  lp := lp
  lr := lr
  b := b
  e := fun i => e i
  hc := by exact_mod_cast (cert2ChkQ.facts h).hc
  hz := by exact_mod_cast (cert2ChkQ.facts h).hz
  hs := by exact_mod_cast (cert2ChkQ.facts h).hs
  hκ := by exact_mod_cast (cert2ChkQ.facts h).hκ
  hd0 := by exact_mod_cast (cert2ChkQ.facts h).hd0
  hd1 := by exact_mod_cast (cert2ChkQ.facts h).hd1
  hsz := by exact_mod_cast (cert2ChkQ.facts h).hsz
  hτ := by exact_mod_cast (cert2ChkQ.facts h).hτ
  hlp0 := by exact_mod_cast (cert2ChkQ.facts h).hlp0
  hlr0 := by exact_mod_cast (cert2ChkQ.facts h).hlr0
  hlr1 := by exact_mod_cast (cert2ChkQ.facts h).hlr1
  hb1 := by exact_mod_cast (cert2ChkQ.facts h).hb1
  helo := by simp only [BandR.toBand_elo]; exact_mod_cast (cert2ChkQ.facts h).helo
  hΔ := (cert2ChkQ.facts h).hΔ
  he17 := by exact_mod_cast (cert2ChkQ.facts h).he17
  cls := ClassOK.ofQ rfl rfl rfl rfl rfl rfl (fun _ => rfl) (by simp only [BandR.toBand_slo, BandR.toBand_elo]; push_cast; rfl)
    (cert2ChkQ.facts h).cls

namespace FamCfg

variable (F : FamCfg)

theorem isOne_of {i : Fin 19} (h2 : i ≠ 2) (h17 : i ≠ 17) : isOne i = true := by
  revert h2 h17; revert i; decide

theorem isSw_of {i : Fin 19} (hi : i = 0 ∨ i = 1 ∨ i = 2 ∨ i = 17) : isSw i = true := by
  rcases hi with rfl | rfl | rfl | rfl <;> rfl

/-- Each member's in-epoch bounds, by index (`0` where there is no one-switch table). -/
def eiQ (dat : Fin 19 → IdxData) (k : Fin F.S.K) (i : Fin 19) : ℚ := if isOne i then F.eIn (dat i) k else 0

/-- **The checks of the main file**: the potential's conditions, the in-epoch contraction, and
every member's class conditions. -/
def mainChk (Bq : BandR) (κ lp lpi : ℚ) (dat : Fin 19 → IdxData) : Bool :=
  cert2ChkQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) && decide (0 < lpi) &&
    decide (lpi ≤ lp) && (List.finRange F.S.K).all fun k => classOKQ F.c F.z F.s κ F.d lpi (F.eiQ dat k) (F.S.patQ F.Δ k)

section Certs

variable {F} {Bq : BandR} {κ lp lpi : ℚ} {dat : Fin 19 → IdxData} (hM : F.mainChk Bq κ lp lpi dat = true)
include hM

theorem mainChk_P : cert2ChkQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) = true := by
  simp only [mainChk, Bool.and_eq_true] at hM; exact hM.1.1.1

/-- **The potential certificate**, its expectations the tables' bounds. -/
noncomputable def cert2 : Cert2 Bq.toBand F.Δ :=
  Cert2.ofQ Bq F.Δ F.c F.z F.s κ F.d F.τ lp (lrOf dat) (bOf dat) (eOf dat) (mainChk_P hM)

variable (hS : F.S.chk F.famZ F.D = true) (hD : 0 < F.D) (hBq : Bq = F.S.weakest)
  (hidx : ∀ i : Fin 19, F.idxChk i (dat i) = true)

/-- **The multi-epoch certificate** from the index checks. -/
noncomputable def cert2E (EL G : ℕ) (hG : F.Δ + 1 ≤ G) (hGEL : G + 1 < EL) : Cert2E Bq.toBand F.Δ F.S.fam EL G where
  P := cert2 hM
  weakF := fun k => hBq ▸ F.S.weak hS k
  hG := hG
  hGEL := hGEL
  vs := fun i => F.vsR i (dat i)
  solS := fun i hi k => (idx_sw hS hD (hidx i) (isSw_of hi)).1 k
  heS0 := fun k => ((idx_sw hS hD (hidx 0) rfl).2 k).trans (by
    show ((dat 0).eS : ℝ) ≤ ((max (dat 0).eS (dat 0).eE : ℚ) : ℝ); exact_mod_cast le_max_left _ _)
  heS1 := fun k => ((idx_sw hS hD (hidx 1) rfl).2 k).trans (by
    show ((dat 1).eS : ℝ) ≤ ((max (max (dat 1).eS (dat 1).eE) 1 : ℚ) : ℝ)
    exact_mod_cast (le_max_left _ _).trans (le_max_left _ _))
  heS2 := fun k => ((idx_sw hS hD (hidx 2) rfl).2 k).trans le_rfl
  heS17 := fun k => ((idx_sw hS hD (hidx 17) rfl).2 k).trans le_rfl
  vpre := fun i => F.vpreR i (dat i)
  vpost := fun i => F.vpostR i (dat i)
  vmax := fun i => F.vmaxR i (dat i)
  solE := fun i h2 h17 => (idx_one hS hD (hidx i) (isOne_of h2 h17)).1
  heE := fun i h2 h17 k => ((idx_one hS hD (hidx i) (isOne_of h2 h17)).2.2 k).trans (by
    show ((dat i).eE : ℝ) ≤ ((eOf dat i : ℚ) : ℝ); rw [eOf, if_pos (isOne_of h2 h17)])

/-- **The certificate with an in-epoch contraction.** -/
noncomputable def cert3E (EL G : ℕ) (hG : F.Δ + 1 ≤ G) (hGEL : G + 1 < EL) : Cert3E Bq.toBand F.Δ F.S.fam EL G where
  C := cert2E hM hS hD hBq hidx EL G hG hGEL
  lpi := lpi
  ei := fun k i => F.eiQ dat k i
  pat0 := fun k => F.S.patQ F.Δ k
  hcl := fun k => by
    simp only [mainChk, Bool.and_eq_true] at hM
    exact ClassOK.ofQ rfl rfl rfl rfl rfl rfl (fun _ => rfl) rfl (List.all_eq_true.1 hM.2 k (List.mem_finRange k))
  hlpi0 := by simp only [mainChk, Bool.and_eq_true, decide_eq_true_eq] at hM; exact_mod_cast hM.1.1.2
  hlpi := by
    show (lpi : ℝ) ≤ (lp : ℝ)
    simp only [mainChk, Bool.and_eq_true, decide_eq_true_eq] at hM; exact_mod_cast hM.1.2
  hpat := F.S.pat_le F.Δ
  helo := F.S.elo hS
  heIn := fun i h2 h17 k => ((idx_one hS hD (hidx i) (isOne_of h2 h17)).2.1 k).trans (by
    show ((F.eIn (dat i) k : ℚ) : ℝ) ≤ ((F.eiQ dat k i : ℚ) : ℝ); rw [eiQ, if_pos (isOne_of h2 h17)])

end Certs

end FamCfg


/-! ## The contractions from the expectations -/

/-- The candidates for the least contraction meeting the class conditions (`classOKQ`) with crossing
bound `pat`, as the generator computes them (`cert2.lp_exact`). -/
def lpCands (c z s κ d pat : ℚ) (e : Fin 19 → ℚ) : List ℚ :=
  let two := fun (ia ib : Fin 19) (r : ℕ) => (s * c ^ r * e ia + κ * d ^ r * e ib) / (s * c ^ r + κ * d ^ r)
  let three := fun (ia ib iab : Fin 19) =>
    let wa := s * c ^ 3
    let wb := κ * d ^ 3
    let lo := max (e ia) ((wa * e ia + κ * e iab) / wa)
    if e ib ≤ lo then lo else max ((wa * e ia + wb * e ib + κ * e iab) / (wa + wb)) (e ia)
  [e 0, e 1 - (1 - (s + κ) / z) * pat, two 3 7 0, two 4 8 1, two 4 9 2, two 5 11 0, two 6 12 1, two 6 13 2,
    three 4 10 15, three 6 14 16]

/-- **The least contraction** meeting the class conditions, rounded up to 13 digits. -/
def lpExactQ (c z s κ d pat : ℚ) (e : Fin 19 → ℚ) : ℚ :=
  match lpCands c z s κ d pat e with
  | [] => 0
  | x :: xs => rupQ 13 (xs.foldl max x)

namespace FamCfg

/-- The potential's contraction, from the tables' bounds. -/
def lpOf (F : FamCfg) (Bq : BandR) (κ : ℚ) (dat : Fin 19 → IdxData) : ℚ :=
  lpExactQ F.c F.z F.s κ F.d (Bq.slo * Bq.elo ^ F.Δ) (eOf dat)

/-- The in-epoch contraction: the largest of the members' least contractions. -/
def lpiOf (F : FamCfg) (κ : ℚ) (dat : Fin 19 → IdxData) : ℚ :=
  ((List.finRange F.S.K).map fun k => lpExactQ F.c F.z F.s κ F.d (F.S.patQ F.Δ k) (F.eiQ dat k)).foldl max 0

end FamCfg

end Cryptarchia.Prob

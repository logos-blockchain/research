module

public import Cryptarchia.Prob.Table
public import Cryptarchia.Prob.CertGen

/-!
# A table potential over the rationals

A certificate gives a table potential (`TabPot`, `Table.lean`) as rational data (`TabQ`): the box's warm
and cold values as lists, the extension factors and the automaton's factor. Its value at a state is
computed over `ℚ` (`TabQ.VQ`) and agrees with the real one (`TabQ.V_cast`). The shape conditions and the
ties to a certificate's reach potential and check base are decidable checks over `ℚ` (`shapeQ`,
`tiesQ`), sound for the real conditions (`shape_of`, `ties_of`).
-/

@[expose] public section

namespace Cryptarchia.Prob

/-- **A table potential as rational data**: warm values `w` (`R + 1` of them), cold values `c` (`R + 1`
rows of `M`), the extension factors `cw`, `zc` and the automaton's factor `x`. -/
structure TabQ where
  R : ℕ
  M : ℕ
  cw : ℚ
  zc : ℚ
  x : ℚ
  w : List ℚ
  c : List (List ℚ)

namespace TabQ

variable (Q : TabQ)

def wQ (r : ℕ) : ℚ := Q.w.getD r 0

def cQ (r j : ℕ) : ℚ := (Q.c.getD r []).getD j 0

/-- The table over `ℝ`. -/
noncomputable def toPot : TabPot := ⟨Q.R, Q.M, Q.cw, Q.zc, Q.x, fun r => (Q.wQ r : ℝ), fun r j => (Q.cQ r j : ℝ)⟩

/-- **The potential over `ℚ`.** -/
def VQ (st : ℤ × ℤ) : ℚ :=
  if 0 ≤ st.2 then Q.wQ (min st.1.toNat Q.R) * Q.cw ^ (st.1.toNat - Q.R)
  else Q.cQ (min st.1.toNat Q.R) (min (TabPot.dep st.2) (Q.M - 1)) * Q.cw ^ (st.1.toNat - Q.R) *
    Q.zc⁻¹ ^ (TabPot.dep st.2 - (Q.M - 1))

theorem V_cast (st : ℤ × ℤ) : Q.toPot.V st = (Q.VQ st : ℝ) := by
  unfold TabPot.V VQ toPot
  split_ifs <;> push_cast <;> rfl

/-- The crossing's credit over `ℚ`. -/
def crQ (s : ℤ × ℤ) : ℚ := Q.VQ (stepO s 0 1 false) - Q.VQ (stepO s 0 1 true)

theorem crT_cast (s : ℤ × ℤ) : Q.toPot.crT s = (Q.crQ s : ℝ) := by
  unfold TabPot.crT crQ; rw [V_cast, V_cast]; push_cast; rfl

@[simp] theorem toPot_R : Q.toPot.R = Q.R := rfl
@[simp] theorem toPot_M : Q.toPot.M = Q.M := rfl
@[simp] theorem toPot_cw : Q.toPot.cw = (Q.cw : ℝ) := rfl
@[simp] theorem toPot_zc : Q.toPot.zc = (Q.zc : ℝ) := rfl
@[simp] theorem toPot_x : Q.toPot.x = (Q.x : ℝ) := rfl
@[simp] theorem toPot_w (r : ℕ) : Q.toPot.w r = (Q.wQ r : ℝ) := rfl
@[simp] theorem toPot_c (r j : ℕ) : Q.toPot.c r j = (Q.cQ r j : ℝ) := rfl

/-- **The shape conditions over `ℚ`.** -/
def shapeQ : Bool :=
  decide (0 < Q.M) && decide (1 ≤ Q.cw) && decide (1 ≤ Q.zc) && decide (Q.cw * Q.zc ≤ Q.x) &&
    (List.range (Q.R + 1)).all (fun r => decide (0 < Q.wQ r)) &&
    (List.range (Q.R + 1)).all (fun r => decide (Q.zc * Q.cQ r 0 ≤ Q.wQ r)) &&
    (List.range Q.R).all (fun r => decide (Q.wQ r ≤ Q.wQ (r + 1))) &&
    (List.range Q.R).all (fun r => decide (Q.wQ (r + 1) ≤ Q.cw * Q.wQ r)) &&
    (List.range (Q.R + 1)).all (fun r => (List.range Q.M).all fun j => decide (0 < Q.cQ r j)) &&
    (List.range Q.R).all (fun r => (List.range Q.M).all fun j => decide (Q.cQ r j ≤ Q.cQ (r + 1) j)) &&
    (List.range (Q.R + 1)).all (fun r => (List.range (Q.M - 1)).all fun j => decide (Q.zc * Q.cQ r (j + 1) ≤ Q.cQ r j))

variable {Q}

theorem shape_of (h : Q.shapeQ = true) : Q.toPot.Shape := by
  simp only [shapeQ, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.mem_range] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨hM, hcw⟩, hzc⟩, hx⟩, hw0⟩, htop⟩, hwm⟩, hwg⟩, hc0⟩, hcm⟩, hcd⟩ := h
  refine ⟨hM, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [toPot_R, toPot_M, toPot_cw, toPot_zc, toPot_x,
    toPot_w, toPot_c]
  · exact_mod_cast hcw
  · exact_mod_cast hzc
  · intro r hr; exact_mod_cast hw0 r (by omega)
  · intro r hr j hj; exact_mod_cast hc0 r (by omega) j hj
  · intro r hr; exact_mod_cast hwm r hr
  · intro r hr j hj; exact_mod_cast hcm r hr j hj
  · intro r hr j hj; exact_mod_cast hcd r (by omega) j (by omega)
  · intro r hr; exact_mod_cast htop r (by omega)
  · intro r hr; exact_mod_cast hwg r hr
  · exact_mod_cast hx

variable (Q) in
/-- **The ties over `ℚ`**, to a reach base `c` and a check base `z`. -/
def tiesQ (c z : ℚ) : Bool :=
  (List.range (Q.R + 1)).all (fun r => decide (Q.wQ r ≤ c ^ r)) && decide (Q.cw ≤ c) && decide (1 ≤ Q.wQ 0) &&
    (List.range Q.M).all (fun j => decide (1 ≤ Q.cQ 0 j * z ^ (j + 1))) && decide (Q.zc ≤ z)

theorem ties_of {B : Band} {Δ : ℕ} {c z : ℚ} (h : Q.tiesQ c z = true) (P : Cert2 B Δ) (hc : P.c = c) (hz : P.z = z) :
    Q.toPot.Ties P := by
  simp only [tiesQ, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true, List.mem_range] at h
  obtain ⟨⟨⟨⟨hw, hcw⟩, hw0⟩, hcz⟩, hzc⟩ := h
  refine ⟨?_, ?_, ?_, ?_, ?_⟩ <;> simp only [toPot_R, toPot_M, toPot_cw, toPot_zc, toPot_w, toPot_c, hc, hz]
  · intro r hr; exact_mod_cast hw r (by omega)
  · exact_mod_cast hcw
  · exact_mod_cast hw0
  · intro j hj; exact_mod_cast hcz j hj
  · exact_mod_cast hzc

end TabQ

end Cryptarchia.Prob

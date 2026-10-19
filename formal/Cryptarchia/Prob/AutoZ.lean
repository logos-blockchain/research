module

public import Cryptarchia.Prob.Auto
public import Cryptarchia.Prob.Cold2
public import Cryptarchia.Prob.EvalLit
public import Mathlib.Algebra.Order.Floor.Defs
public import Mathlib.Data.Rat.Floor
import Mathlib.Data.Nat.Choose.Multinomial
import Mathlib.Geometry.Euclidean.Altitude

/-!
# Automaton checks over the integers, with computed tables

A certificate checks its automaton tables (`AutoSol`, `PreSol`, the domination by `vmax`,
`autoBound ≤ e`) by `decide +kernel`, in integer arithmetic. A band's `slot4` fields are
integers over a common denominator `D` (`BandZ.Rep`, against the rational fields `BandQ`), a
phase expectation's `x`, `θ`, `g` integers over their own denominators (`PhZ.Rep`, against
the rational `xgNQ`), and a table integers over a scale `S` (`castZ`). A recursion step and a
phase bound are then integers exactly proportional to the real ones (`stepZ_cast`,
`autoBoundZ_cast`), so an integer comparison gives the real one (`stepZ_le`, `autoBoundZ_le`),
and the kernel evaluates it with its arbitrary-precision `Nat` arithmetic. This adds no axioms.

A table refers back to itself only through the three entries `v 0 a true`, the state just
after an honest success; every other entry is one recursion step from the next row. `fillZ`
computes the table from those three entries (`top`), row by row from `q = Δ - 1` down, each
step rounded up to the scale and floored at `lo`; `fillAllZ` does the same with the step's
maximum over several bands. A certificate gives only the three entries per table.
-/

@[expose] public section

namespace Cryptarchia.Prob

section

/-- The fields of a band that `slot4` reads, over `ℚ`. -/
structure BandQ where
  hhi : ℚ
  hlo : ℚ
  amax : ℚ
  hahi : ℚ
  alo : ℚ
  halo : ℚ

/-- `B` has the values of `b` in the fields `slot4` reads. -/
structure BandQ.Agrees (b : BandQ) (B : Band) : Prop where
  hhi : B.hhi = b.hhi
  hlo : B.hlo = b.hlo
  amax : B.amax = b.amax
  hahi : B.hahi = b.hahi
  alo : B.alo = b.alo
  halo : B.halo = b.halo

/-! ## Tables -/

/-- A terminal table over `ℚ`, cast to `ℝ`. -/
noncomputable def castG (g : Fin 3 → Bool → Bool → ℚ) : Fin 3 → Bool → Bool → ℝ := fun a b u => g a b u

/-- `gtab` over `ℚ`. -/
def gtabQ (t0 t1 t2 : Bool → Bool → ℚ) : Fin 3 → Bool → Bool → ℚ := fun a b u =>
  if a.val = 0 then t0 b u else if a.val = 1 then t1 b u else t2 b u

/-- `xgN` over `ℚ`. -/
def xgNQ (c z s d τ : ℚ) : ℕ → ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)
  | 0 => (c, 1, gtabQ (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1) (fun b _ => if b then c⁻¹ else 1))
  | 1 => (c, 1, fun _ _ _ => 1)
  | 2 => (z, 1, gtabQ (fun b _ => if b then 1 else 0) (fun _ _ => 1) (fun _ _ => 1))
  | 3 => (c, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  | 4 => (c, 1, gtabQ (fun b _ => if b then (c * z)⁻¹ else 1) (fun _ _ => z / s) (fun _ _ => z / s))
  | 5 => (c * z, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then z⁻¹ else 1) (fun b _ => if b then s⁻¹ else 1))
  | 6 => (c * z, 1, gtabQ (fun b _ => if b then (c * z)⁻¹ else 1) (fun b _ => if b then (c * z)⁻¹ else 1)
      (fun b _ => if b then s⁻¹ else 1))
  | 7 => (d * z, 1, gtabQ (fun b _ => if b then z⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 8 => (d * z, 1, gtabQ (fun b _ => if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 9 => (d * z, 1, gtabQ (fun b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 10 => (d * z, 1, gtabQ (fun b u => if u then 0 else if b then (d * z)⁻¹ else 1) (fun _ _ => 0) (fun _ _ => 0))
  | 11 => (d * z, 1, fun _ b _ => if b then z⁻¹ else 1)
  | 12 => (d * z, 1, fun _ b _ => if b then (d * z)⁻¹ else 1)
  | 13 => (d * z, 1, fun _ b u => if b then (if u then (d * d * z)⁻¹ else (d * z)⁻¹) else 1)
  | 14 => (d * z, 1, fun _ b u => if u then 0 else if b then (d * z)⁻¹ else 1)
  | 15 => (z, 1, gtabQ (fun _ u => if u then z⁻¹ else 0) (fun _ _ => 0) (fun _ _ => 0))
  | 16 => (z, 1, fun _ _ u => if u then z⁻¹ else 0)
  | 17 => (1, τ, fun _ _ _ => 1)
  | _ => (1, 1, fun _ _ _ => 1)

/-- A triple over `ℚ`, cast to `ℝ`. -/
noncomputable def castX (p : ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)) : ℝ × ℝ × (Fin 3 → Bool → Bool → ℝ) :=
  ((p.1 : ℝ), (p.2.1 : ℝ), castG p.2.2)

theorem xgN_ofQ (c z s d τ : ℚ) (i : ℕ) :
    xgN (c : ℝ) z s d τ i = castX (xgNQ c z s d τ i) := by
  rcases i with _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | _ | i <;>
    refine Prod.ext ?_ (Prod.ext ?_ ?_) <;> simp only [xgN, xgNQ, castX] <;> (try funext a b u) <;>
    (try simp only [castG, gtab, gtabQ]) <;> (try split_ifs) <;> push_cast <;> rfl

/-- `xg` at rational parameters, given as real literals. -/
theorem xg_ofQ {c z s d τ : ℚ} {c' z' s' d' τ' : ℝ} (hc : (c : ℝ) = c') (hz : (z : ℝ) = z')
    (hs : (s : ℝ) = s') (hd : (d : ℝ) = d') (hτ : (τ : ℝ) = τ') (i : Fin 19) :
    xg c' z' s' d' τ' i = castX (xgNQ c z s d τ i.val) := by
  subst hc hz hs hd hτ; exact xgN_ofQ c z s d τ i.val

/-! ## Over the integers -/

/-- The fields of a band that `slot4` reads, as integers over a common denominator. -/
structure BandZ where
  hhi : ℤ
  hlo : ℤ
  amax : ℤ
  hahi : ℤ
  alo : ℤ
  halo : ℤ

/-- `B / D` has the values of `b`. -/
structure BandZ.Rep (B : BandZ) (D : ℤ) (b : BandQ) : Prop where
  hhi : b.hhi = (B.hhi : ℚ) / D
  hlo : b.hlo = (B.hlo : ℚ) / D
  amax : b.amax = (B.amax : ℚ) / D
  hahi : b.hahi = (B.hahi : ℚ) / D
  alo : b.alo = (B.alo : ℚ) / D
  halo : b.halo = (B.halo : ℚ) / D

instance (B : BandZ) (D : ℤ) (b : BandQ) : Decidable (B.Rep D b) :=
  decidable_of_iff (b.hhi = (B.hhi : ℚ) / D ∧ b.hlo = (B.hlo : ℚ) / D ∧ b.amax = (B.amax : ℚ) / D ∧
      b.hahi = (B.hahi : ℚ) / D ∧ b.alo = (B.alo : ℚ) / D ∧ b.halo = (B.halo : ℚ) / D)
    ⟨fun ⟨h1, h2, h3, h4, h5, h6⟩ => ⟨h1, h2, h3, h4, h5, h6⟩,
      fun h => ⟨h.hhi, h.hlo, h.amax, h.hahi, h.alo, h.halo⟩⟩

/-- `slot4`, times `D`, over the integers. -/
def slot4Z (B : BandZ) (D : ℤ) (F : Bool → Bool → ℤ) : ℤ :=
  F false false * D + (F false true - F false false) * (if F false false ≤ F false true then B.amax else B.alo) +
    (F true false - F false false) * (if F false false ≤ F true false then B.hhi else B.hlo) +
    (F true true - F true false - F false true + F false false) *
      (if F true false + F false true ≤ F true true + F false false then B.hahi else B.halo)

theorem slot4Z_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D)
    (F : Bool → Bool → ℤ) {c : ℝ} (hc : 0 < c) : (slot4Z B D F : ℝ) = D * c * slot4 Bb (fun h a => (F h a : ℝ) / c) := by
  have hD' : (0 : ℝ) < D := by exact_mod_cast hD
  have e1 : ∀ x y : ℤ, ((x : ℝ) / c ≤ (y : ℝ) / c ↔ x ≤ y) := fun x y => by
    rw [div_le_div_iff_of_pos_right hc, Int.cast_le]
  have e2 : ∀ x y z w : ℤ, ((x : ℝ) / c + (y : ℝ) / c ≤ (z : ℝ) / c + (w : ℝ) / c ↔ x + y ≤ z + w) :=
    fun x y z w => by
      rw [← add_div, ← add_div, div_le_div_iff_of_pos_right hc, ← Int.cast_add, ← Int.cast_add, Int.cast_le]
  unfold slot4Z slot4
  simp only [e1, e2, hA.hhi, hA.hlo, hA.amax, hA.hahi, hA.alo, hA.halo, hR.hhi, hR.hlo, hR.amax, hR.hahi, hR.alo,
    hR.halo]
  split_ifs <;> push_cast <;> field_simp

/-- A phase expectation's numbers over the integers: `x = xn / xd`, `θ = θn / θd`,
`g = gn / gd`. -/
structure PhZ where
  xn : ℤ
  xd : ℤ
  θn : ℤ
  θd : ℤ
  gn : Fin 3 → Bool → Bool → ℤ
  gd : ℤ

/-- `X` has the values `x`, `θ`, `g`, with positive denominators. -/
structure PhZ.Rep (X : PhZ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) : Prop where
  xd : 0 < X.xd
  θd : 0 < X.θd
  gd : 0 < X.gd
  x : x = (X.xn : ℚ) / X.xd
  θ : θ = (X.θn : ℚ) / X.θd
  g : ∀ a b u, g a b u = (X.gn a b u : ℚ) / X.gd

instance (X : PhZ) (x θ : ℚ) (g : Fin 3 → Bool → Bool → ℚ) : Decidable (X.Rep x θ g) :=
  decidable_of_iff (0 < X.xd ∧ 0 < X.θd ∧ 0 < X.gd ∧ x = (X.xn : ℚ) / X.xd ∧ θ = (X.θn : ℚ) / X.θd ∧
      ∀ a b u, g a b u = (X.gn a b u : ℚ) / X.gd)
    ⟨fun ⟨h1, h2, h3, h4, h5, h6⟩ => ⟨h1, h2, h3, h4, h5, h6⟩,
      fun h => ⟨h.xd, h.θd, h.gd, h.x, h.θ, h.g⟩⟩

/-- The scale of a step over the integers, apart from the table's: `θd · D · xd · gd`. -/
def PhZ.M (X : PhZ) (D : ℤ) : ℤ := X.θd * D * X.xd * X.gd

theorem PhZ.M_pos {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {D : ℤ} (hD : 0 < D) :
    0 < X.M D := by
  unfold PhZ.M; have := hX.xd; have := hX.θd; have := hX.gd; positivity

/-- The tables' scale: `2⁶⁴`. -/
def SZ : ℤ := 18446744073709551616

theorem SZ_pos : 0 < SZ := by decide

/-- A table of integers at scale `S`, over `ℝ`. -/
noncomputable def castZ (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℝ := fun q a u => (v q a u : ℝ) / S

/-- A table from its integers listed by `(q, a, u)` in lexicographic order; `0` beyond. -/
def tabZ (l : List ℤ) : ℕ → Fin 3 → Bool → ℤ := fun q a u =>
  l.getD (6 * q + 2 * a.val + if u then 1 else 0) 0

/-- The left side of the recursion step, times `M · S`, for a successor table `w` at scale `S`. -/
def stepZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (w : ℕ → Fin 3 → Bool → ℤ) (q : ℕ) (a : Fin 3)
    (u : Bool) : ℤ :=
  X.θn * slot4Z B D (fun hh aa => (if aa then X.xn else X.xd) *
    (if hh then w 0 (acap (a.val + if aa then 1 else 0)) true * X.gd
      else if q + 1 = Δ then X.gn (acap (a.val + if aa then 1 else 0)) true u * S
        else w (q + 1) (acap (a.val + if aa then 1 else 0)) u * X.gd))

theorem stepZ_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D)
    {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) (Δ : ℕ)
    (w : ℕ → Fin 3 → Bool → ℤ) (q : ℕ) (a : Fin 3) (u : Bool) :
    (stepZ B D Δ X S w q a u : ℝ) = (X.M D : ℝ) * S * stepR Bb Δ x θ (castG g) (castZ S w) q a u := by
  have hxd : (0 : ℝ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℝ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  unfold stepZ stepR
  rw [Int.cast_mul, slot4Z_cast hR hA hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then w 0 (acap (a.val + if aa then 1 else 0)) true * X.gd
        else if q + 1 = Δ then X.gn (acap (a.val + if aa then 1 else 0)) true u * S
          else w (q + 1) (acap (a.val + if aa then 1 else 0)) u * X.gd) : ℤ) : ℝ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then (x : ℝ) else 1) *
        (if hh then castZ S w 0 (acap (a.val + if aa then 1 else 0)) true
          else if q + 1 = Δ then castG g (acap (a.val + if aa then 1 else 0)) true u
            else castZ S w (q + 1) (acap (a.val + if aa then 1 else 0)) u)) := by
    funext hh aa
    simp only [castZ, castG, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-- `autoBound`, times `M · S`, over the integers. -/
def autoBoundZ (B : BandZ) (D : ℤ) (X : PhZ) (S : ℤ) (v : ℕ → Fin 3 → Bool → ℤ) : ℤ :=
  X.θn * slot4Z B D (fun hh aa => (if aa then X.xn else X.xd) *
    (if hh then v 0 (acap (if aa then 1 else 0)) false * X.gd else X.gn (acap (if aa then 1 else 0)) false false * S))

theorem autoBoundZ_cast {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb)
    (hD : 0 < D) {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S)
    (v : ℕ → Fin 3 → Bool → ℤ) :
    (autoBoundZ B D X S v : ℝ) = (X.M D : ℝ) * S * autoBound Bb x θ (castG g) (castZ S v) := by
  have hxd : (0 : ℝ) < X.xd := by exact_mod_cast hX.xd
  have hθd : (0 : ℝ) < X.θd := by exact_mod_cast hX.θd
  have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  unfold autoBoundZ autoBound
  rw [Int.cast_mul, slot4Z_cast hR hA hD _ (c := X.xd * S * X.gd) (by positivity)]
  have hF : (fun (h aa : Bool) => (((if aa then X.xn else X.xd) *
      (if h then v 0 (acap (if aa then 1 else 0)) false * X.gd
        else X.gn (acap (if aa then 1 else 0)) false false * S) : ℤ) : ℝ) / (X.xd * S * X.gd)) =
      (fun (hh aa : Bool) => (if aa then (x : ℝ) else 1) *
        (if hh then castZ S v 0 (acap (if aa then 1 else 0)) false else castG g (acap (if aa then 1 else 0)) false false)) := by
    funext hh aa
    simp only [castZ, castG, hX.x, hX.g]
    split_ifs <;> push_cast <;> field_simp
  rw [hF, hX.θ]
  unfold PhZ.M
  push_cast
  field_simp

/-! ## The checks -/

section Checks

variable {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D) {X : PhZ}
  {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S)
include hR hA hD hX hS

/-- The recursion over the integers at a state gives it over `ℝ`. -/
theorem stepZ_le {Δ : ℕ} {w : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} {a : Fin 3} {u : Bool}
    (h : stepZ B D Δ X S w q a u ≤ w q a u * X.M D) : stepR Bb Δ x θ (castG g) (castZ S w) q a u ≤ castZ S w q a u := by
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have h2 : (stepZ B D Δ X S w q a u : ℝ) ≤ (w q a u : ℝ) * X.M D := by exact_mod_cast h
  rw [stepZ_cast hR hA hD hX hS] at h2
  rw [castZ, le_div_iff₀ hS']
  nlinarith [mul_pos hM hS']

/-- A phase bound over the integers gives it over `ℝ`. -/
theorem autoBoundZ_le {v : ℕ → Fin 3 → Bool → ℤ} {e : ℚ} (h : (autoBoundZ B D X S v : ℚ) ≤ e * (X.M D * S : ℤ)) :
    autoBound Bb x θ (castG g) (castZ S v) ≤ e := by
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have h2 : (autoBoundZ B D X S v : ℝ) ≤ (e : ℝ) * (X.M D * S : ℤ) := by exact_mod_cast h
  rw [autoBoundZ_cast hR hA hD hX hS] at h2
  push_cast at h2
  nlinarith [mul_pos hM hS']

end Checks

theorem castZ_le {S : ℤ} (hS : 0 < S) {v w : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} {a : Fin 3} {u : Bool}
    (h : v q a u ≤ w q a u) : castZ S v q a u ≤ castZ S w q a u :=
  div_le_div_of_nonneg_right (by exact_mod_cast h) (by exact_mod_cast hS.le)

/-! ## Tables by backward recursion -/

/-- `n / m` rounded up, for `0 < m`. -/
def cdivZ (n m : ℤ) : ℤ := -((-n) / m)

/-- The row at `q` from the row at `q + 1` (`nxt`, six entries by `(a, u)`): the step's maximum
over the bands `Bs`, rounded up to the scale, floored at `lo`; `top a` at `(0, a, true)`. -/
def fillRowZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (top : Fin 3 → ℤ)
    (q : ℕ) (nxt : List ℤ) : List ℤ :=
  let w : ℕ → Fin 3 → Bool → ℤ := fun q' a u =>
    if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0
  let f : Fin 3 → Bool → ℤ := fun a u =>
    if q = 0 ∧ u = true then top a else
      Bs.foldl (fun m B => let s := cdivZ (stepZ B D Δ X S w q a u) (X.M D); if m ≤ s then s else m) (lo q a u)
  [f 0 false, f 0 true, f 1 false, f 1 true, f 2 false, f 2 true]

/-- The rows `q, …, q + n - 1`, listed by `(q, a, u)`. -/
def fillRowsZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (top : Fin 3 → ℤ) : ℕ → ℕ → List ℤ
  | _, 0 => []
  | q, n + 1 =>
    let r := fillRowsZ Bs D Δ X S lo top (q + 1) n
    fillRowZ Bs D Δ X S lo top q r ++ r

/-- The table for the bands `Bs` with entries `top a` at `(0, a, true)`, floored at `lo`. -/
def fillAllZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (top : Fin 3 → ℤ) : ℕ → Fin 3 → Bool → ℤ :=
  tabZ (fillRowsZ Bs D Δ X S lo top 0 Δ)

/-- The table for one band. -/
def fillZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (top : Fin 3 → ℤ) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillAllZ [B] D Δ X S lo top

/-- The terminal table `g` at scale `S`, rounded up: the floor of a post-switch table. -/
def gFloorZ (X : PhZ) (S : ℤ) : ℕ → Fin 3 → Bool → ℤ := fun _ a u => cdivZ (X.gn a true u * S) X.gd

/-! ## The class conditions -/

/-- `ClassOK` as a check over `ℚ`, at the potential's parameters `c z s κ d`. -/
def classOKQ (c z s κ d lp : ℚ) (e : Fin 19 → ℚ) (pat : ℚ) : Bool :=
  decide (e 0 ≤ lp) && decide (e 1 - (1 - (s + κ) * z⁻¹) * pat ≤ lp) &&
    decide (s * (e 3 - lp) + κ * (e 7 - lp) ≤ 0) && decide (s * c * (e 4 - lp) + κ * d * (e 8 - lp) ≤ 0) &&
    decide (s * c ^ 2 * (e 4 - lp) + κ * d ^ 2 * (e 9 - lp) ≤ 0) && decide (e 4 ≤ lp) &&
    decide (s * c ^ 3 * (e 4 - lp) + κ * d ^ 3 * max (e 10 - lp) 0 + κ * e 15 ≤ 0) &&
    decide (s * (e 5 - lp) + κ * (e 11 - lp) ≤ 0) && decide (s * c * (e 6 - lp) + κ * d * (e 12 - lp) ≤ 0) &&
    decide (s * c ^ 2 * (e 6 - lp) + κ * d ^ 2 * (e 13 - lp) ≤ 0) && decide (e 6 ≤ lp) &&
    decide (s * c ^ 3 * (e 6 - lp) + κ * d ^ 3 * max (e 14 - lp) 0 + κ * e 16 ≤ 0)

theorem ClassOK.ofQ {c z s κ d lp pat : ℚ} {e : Fin 19 → ℚ} {c' z' s' κ' d' lp' pat' : ℝ}
    {e' : Fin 19 → ℝ} (hc : c' = c) (hz : z' = z) (hs : s' = s) (hκ : κ' = κ) (hd : d' = d) (hlp : lp' = lp)
    (he : ∀ i, e' i = e i) (hpat : pat' = pat)
    (h : classOKQ c z s κ d lp e pat = true) : ClassOK c' z' s' κ' d' lp' e' pat' := by
  simp only [classOKQ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩, h7⟩, h8⟩, h9⟩, h10⟩, h11⟩, h12⟩ := h
  subst hc hz hs hκ hd hlp hpat
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_, ?_⟩ <;> simp only [he] <;>
    exact_mod_cast ‹_›

end

/-!
## Automaton tables computed by the kernel

The seeds (the three entries at `(0, a, true)`) are computed as well, so a certificate
needs no tables at all.

* **Fills are solutions by construction** (`fillAllZ_entry`). Every entry of a fill other
  than a seed is at least its floor `lo` and at least each band's step, rounded up. So the
  recursion holds everywhere once it holds at the three seeds (`seedOKZ`): the fill is an
  `AutoSol` or a `PreSol` with no pass over the table (`fill_autoSol`, `fill_preSol`), and
  below the entrywise maximum `vmax` by construction (`le_maxTabZ`).
* **Seeds by Newton's method** (`solveSeedsZ`). The seeds are a fixed point of a monotone,
  piecewise affine map of three integers. Newton steps on finite differences find it, raised
  by a small pad, then steps of the map itself until the seeds are a solution. Across a band
  family each member starts from the previous member's seeds (`seedsZ`, `preSeedsZ`). A
  certificate runs the solver at elaboration time (`eval%`, `EvalLit.lean`) and the kernel
  only checks its result, so the solver needs no soundness theorem.
* **One check per phase index** (`oneSwitchF_sound`, `switchF_sound`): the one-switch
  tables (`AutoSolE`) or the switching table, for the whole family, with their bounds.
-/

/-! ## Rounding and folds -/

theorem cdivZ_mul_ge {n m : ℤ} (hm : 0 < m) : n ≤ cdivZ n m * m := by
  unfold cdivZ
  have := Int.ediv_mul_le (-n) hm.ne'
  linarith [neg_mul ((-n) / m) m]

theorem le_of_cdivZ_le {n m v : ℤ} (hm : 0 < m) (h : cdivZ n m ≤ v) : n ≤ v * m :=
  (cdivZ_mul_ge hm).trans (mul_le_mul_of_nonneg_right h hm.le)

/-- A running maximum is above its start and above every value it folds in. -/
theorem foldl_ite_max {α : Type*} (s : α → ℤ) : ∀ (l : List α) (m : ℤ),
    m ≤ l.foldl (fun m B => if m ≤ s B then s B else m) m ∧
      ∀ B ∈ l, s B ≤ l.foldl (fun m B => if m ≤ s B then s B else m) m
  | [], m => ⟨le_rfl, by simp⟩
  | B :: l, m => by
    have h1 : m ≤ (if m ≤ s B then s B else m) := by split_ifs <;> omega
    have h2 : s B ≤ (if m ≤ s B then s B else m) := by split_ifs <;> omega
    obtain ⟨ih1, ih2⟩ := foldl_ite_max s l (if m ≤ s B then s B else m)
    refine ⟨h1.trans ih1, fun B' hB' => ?_⟩
    rcases List.mem_cons.1 hB' with rfl | h
    · exact h2.trans ih1
    · exact ih2 B' h

theorem foldl_max_ge {α : Type*} (s : α → ℤ) : ∀ (l : List α) (m : ℤ),
    m ≤ l.foldl (fun m t => max m (s t)) m ∧ ∀ t ∈ l, s t ≤ l.foldl (fun m t => max m (s t)) m
  | [], m => ⟨le_rfl, by simp⟩
  | t :: l, m => by
    obtain ⟨ih1, ih2⟩ := foldl_max_ge s l (max m (s t))
    refine ⟨(le_max_left _ _).trans ih1, fun t' ht' => ?_⟩
    rcases List.mem_cons.1 ht' with rfl | h
    · exact (le_max_right _ _).trans ih1
    · exact ih2 t' h

/-! ## Fills are solutions by construction -/

section Fill

variable {Bs : List BandZ} {D : ℤ} {Δ : ℕ} {X : PhZ} {S : ℤ} {lo : ℕ → Fin 3 → Bool → ℤ} {top : Fin 3 → ℤ}

theorem fillRowZ_length (q : ℕ) (nxt : List ℤ) : (fillRowZ Bs D Δ X S lo top q nxt).length = 6 := rfl

theorem fillRowsZ_getD : ∀ (j n q i : ℕ), j < n → i < 6 →
    (fillRowsZ Bs D Δ X S lo top q n).getD (6 * j + i) 0 =
      (fillRowZ Bs D Δ X S lo top (q + j) (fillRowsZ Bs D Δ X S lo top (q + j + 1) (n - j - 1))).getD i 0
  | 0, n + 1, q, i, _, hi => by
    simp only [fillRowsZ, Nat.mul_zero, Nat.zero_add, Nat.add_zero]
    exact List.getD_append _ _ _ _ (by rw [fillRowZ_length]; exact hi)
  | j + 1, n + 1, q, i, hj, hi => by
    simp only [fillRowsZ]
    rw [List.getD_append_right _ _ _ _ (by rw [fillRowZ_length]; omega), fillRowZ_length,
      show 6 * (j + 1) + i - 6 = 6 * j + i by omega,
      fillRowsZ_getD j n (q + 1) i (by omega) hi]
    simp only [show q + 1 + j = q + (j + 1) by omega, show n - j - 1 = n + 1 - (j + 1) - 1 by omega]

theorem fillAllZ_eq {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    fillAllZ Bs D Δ X S lo top q a u =
      (fillRowZ Bs D Δ X S lo top q (fillRowsZ Bs D Δ X S lo top (q + 1) (Δ - q - 1))).getD
        (2 * a.val + if u then 1 else 0) 0 := by
  have ha := a.isLt
  unfold fillAllZ tabZ
  rw [show 6 * q + 2 * a.val + (if u then 1 else 0) = 6 * q + (2 * a.val + if u then 1 else 0) by omega,
    fillRowsZ_getD q Δ 0 _ hq (by split <;> omega)]
  simp only [Nat.zero_add]

theorem fillRowZ_getD (q : ℕ) (nxt : List ℤ) (a : Fin 3) (u : Bool) :
    (fillRowZ Bs D Δ X S lo top q nxt).getD (2 * a.val + if u then 1 else 0) 0 =
      if q = 0 ∧ u = true then top a else
        Bs.foldl (fun m B => if m ≤ cdivZ (stepZ B D Δ X S (fun q' a u =>
          if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0) q a u) (X.M D) then
            cdivZ (stepZ B D Δ X S (fun q' a u =>
              if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0) q a u) (X.M D)
          else m) (lo q a u) := by
  fin_cases a <;> cases u <;> rfl

theorem fillAllZ_seed (hΔ : 0 < Δ) (a : Fin 3) : fillAllZ Bs D Δ X S lo top 0 a true = top a := by
  rw [fillAllZ_eq hΔ, fillRowZ_getD, if_pos ⟨rfl, rfl⟩]

/-- `stepZ` reads a table only at the seeds and at the next row. -/
theorem stepZ_congr (B : BandZ) {w w' : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (hq : q < Δ)
    (h0 : ∀ a, w 0 a true = w' 0 a true) (h1 : q + 1 < Δ → ∀ a u, w (q + 1) a u = w' (q + 1) a u)
    (a : Fin 3) (u : Bool) : stepZ B D Δ X S w q a u = stepZ B D Δ X S w' q a u := by
  unfold stepZ
  by_cases hΔ : q + 1 = Δ
  · simp only [hΔ, h0, ite_true]
  · simp only [hΔ, h0, h1 (by omega), ite_false]

/-- **Every entry of a fill but the seeds is a solution of the recursion**, for every band
it was filled for, and above its floor. -/
theorem fillAllZ_entry (hM : 0 < X.M D) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool)
    (hnt : ¬(q = 0 ∧ u = true)) :
    lo q a u ≤ fillAllZ Bs D Δ X S lo top q a u ∧
      ∀ B ∈ Bs, stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u ≤
        fillAllZ Bs D Δ X S lo top q a u * X.M D := by
  rw [fillAllZ_eq hq, fillRowZ_getD, if_neg hnt]
  set nxt := fillRowsZ Bs D Δ X S lo top (q + 1) (Δ - q - 1)
  set w : ℕ → Fin 3 → Bool → ℤ := fun q' a u => if q' = 0 then top a else nxt.getD (2 * a.val + if u then 1 else 0) 0
  have hw : ∀ B, stepZ B D Δ X S w q a u = stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u := fun B =>
    stepZ_congr B hq (fun a => by simp only [w, ite_true]; exact (fillAllZ_seed (by omega) a).symm)
      (fun hq1 a u => by
        simp only [w, Nat.add_one_ne_zero, ite_false, nxt]
        rw [fillAllZ_eq hq1, show 2 * a.val + (if u then 1 else 0) = 6 * 0 + (2 * a.val + if u then 1 else 0) by omega,
          fillRowsZ_getD 0 _ _ _ (by omega) (by have := a.isLt; split <;> omega)]
        simp only [Nat.add_zero, Nat.mul_zero, Nat.zero_add, show Δ - q - 1 - 0 - 1 = Δ - (q + 1) - 1 by omega]) a u
  obtain ⟨h1, h2⟩ := foldl_ite_max (fun B => cdivZ (stepZ B D Δ X S w q a u) (X.M D)) Bs (lo q a u)
  refine ⟨h1, fun B hB => ?_⟩
  rw [← hw B]
  exact le_of_cdivZ_le hM (h2 B hB)

/-- The seeds of a fill solve the recursion for `B` and lie above the floor. -/
def seedOKZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo v : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  let p : Fin 3 → Bool := fun a =>
    decide (lo 0 a true ≤ v 0 a true) && decide (stepZ B D Δ X S v 0 a true ≤ v 0 a true * X.M D)
  p 0 && p 1 && p 2

theorem seedOKZ_sound {B : BandZ} {v : ℕ → Fin 3 → Bool → ℤ} (h : seedOKZ B D Δ X S lo v = true) (a : Fin 3) :
    lo 0 a true ≤ v 0 a true ∧ stepZ B D Δ X S v 0 a true ≤ v 0 a true * X.M D := by
  simp only [seedOKZ, Bool.and_eq_true, decide_eq_true_eq] at h
  fin_cases a
  exacts [h.1.1, h.1.2, h.2]

/-- Every entry of a fill whose seeds check is above its floor and solves the recursion. -/
theorem fillAllZ_sol (hM : 0 < X.M D) {B : BandZ} (hB : B ∈ Bs)
    (hs : seedOKZ B D Δ X S lo (fillAllZ Bs D Δ X S lo top) = true) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    lo q a u ≤ fillAllZ Bs D Δ X S lo top q a u ∧
      stepZ B D Δ X S (fillAllZ Bs D Δ X S lo top) q a u ≤ fillAllZ Bs D Δ X S lo top q a u * X.M D := by
  by_cases hnt : q = 0 ∧ u = true
  · obtain ⟨rfl, rfl⟩ := hnt
    exact seedOKZ_sound hs a
  · obtain ⟨h1, h2⟩ := fillAllZ_entry (top := top) hM hq a u hnt
    exact ⟨h1, h2 B hB⟩

end Fill

/-- The terminal table rounded up is a floor above `g`. -/
theorem gFloorZ_ge {X : PhZ} {S : ℤ} (hgd : 0 < X.gd) (q : ℕ) (a : Fin 3) (u : Bool) :
    X.gn a true u * S ≤ gFloorZ X S q a u * X.gd := cdivZ_mul_ge hgd

section Sol

variable {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D) {X : PhZ}
  {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ} {Bs : List BandZ}
  (hB : B ∈ Bs) {top : Fin 3 → ℤ}
include hR hA hD hX hS hB

/-- **A fill floored at `g` whose seeds check solves the recursion.** -/
theorem fill_autoSol (hs : seedOKZ B D Δ X S (gFloorZ X S) (fillAllZ Bs D Δ X S (gFloorZ X S) top) = true) :
    AutoSol Bb Δ x θ (castG g) (castZ S (fillAllZ Bs D Δ X S (gFloorZ X S) top)) where
  term q hq a u := by
    have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
    have hS' : (0 : ℝ) < S := by exact_mod_cast hS
    refine le_trans ?_ (castZ_le hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).1)
    rw [castG, castZ, hX.g]
    push_cast
    rw [div_le_div_iff₀ hgd hS']
    exact_mod_cast gFloorZ_ge hX.gd q a u
  step q hq a u := stepZ_le hR hA hD hX hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).2

/-- **A fill floored at `vmax` whose seeds check is a pre-switch table.** -/
theorem fill_preSol {vmax : ℕ → Fin 3 → Bool → ℤ}
    (hs : seedOKZ B D Δ X S vmax (fillAllZ Bs D Δ X S vmax top) = true) :
    PreSol Bb Δ x θ (castG g) (castZ S vmax) (castZ S (fillAllZ Bs D Δ X S vmax top)) where
  dom _ hq a u := castZ_le hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).1
  step _ hq a u := stepZ_le hR hA hD hX hS (fillAllZ_sol (X.M_pos hX hD) hB hs hq a u).2

end Sol

/-! ## Tables listed once -/

/-- The rows `q, …, q + n - 1` of a table, listed by `(q, a, u)`. -/
def matRowsZ (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → ℕ → List ℤ
  | _, 0 => []
  | q, n + 1 => [v q 0 false, v q 0 true, v q 1 false, v q 1 true, v q 2 false, v q 2 true] ++ matRowsZ v (q + 1) n

theorem matRowsZ_getD (v : ℕ → Fin 3 → Bool → ℤ) : ∀ (j n q : ℕ) (a : Fin 3) (u : Bool), j < n →
    (matRowsZ v q n).getD (6 * j + (2 * a.val + if u then 1 else 0)) 0 = v (q + j) a u
  | 0, n + 1, q, a, u, _ => by
    rw [matRowsZ, Nat.mul_zero, Nat.zero_add, List.getD_append _ _ _ _ (by simp; have := a.isLt; split <;> omega)]
    fin_cases a <;> cases u <;> rfl
  | j + 1, n + 1, q, a, u, hj => by
    have ha := a.isLt
    rw [matRowsZ, List.getD_append_right _ _ _ _ (by simp; omega)]
    simp only [List.length_cons, List.length_nil]
    rw [show 6 * (j + 1) + (2 * a.val + if u then 1 else 0) - 6 = 6 * j + (2 * a.val + if u then 1 else 0) by
      split <;> omega, matRowsZ_getD v j n (q + 1) a u (by omega), show q + 1 + j = q + (j + 1) by omega]

/-- A table evaluated once and listed, so that later lookups do not recompute it. -/
def memoZ (Δ : ℕ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℤ := tabZ (matRowsZ v 0 Δ)

theorem memoZ_eq {Δ : ℕ} {v : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    memoZ Δ v q a u = v q a u := by
  unfold memoZ tabZ
  rw [show 6 * q + 2 * a.val + (if u then 1 else 0) = 6 * q + (2 * a.val + if u then 1 else 0) by omega,
    matRowsZ_getD v q Δ 0 a u hq, Nat.zero_add]

/-- The entrywise maximum of tables (at least `0`), listed once. -/
def maxTabZ (Δ : ℕ) (ts : List (ℕ → Fin 3 → Bool → ℤ)) : ℕ → Fin 3 → Bool → ℤ :=
  memoZ Δ fun q a u => ts.foldl (fun m t => max m (t q a u)) 0

theorem le_maxTabZ {Δ : ℕ} {ts : List (ℕ → Fin 3 → Bool → ℤ)} {t : ℕ → Fin 3 → Bool → ℤ} (ht : t ∈ ts)
    {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) : t q a u ≤ maxTabZ Δ ts q a u := by
  unfold maxTabZ
  rw [memoZ_eq hq]
  exact (foldl_max_ge (fun t => t q a u) ts 0).2 t ht

/-! ## Seeds by Newton's method -/

/-- Three seeds as a function. -/
def seedL (l : List ℤ) : Fin 3 → ℤ := fun a => l.getD a.val 0

/-- The step at `(0, a, true)` for the table with seeds `t`: its maximum over the bands,
rounded up, at least the floor. The seeds solve the recursion iff this is at most `t`. -/
def seedStepZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (t : List ℤ) : List ℤ :=
  -- the rows listed once, so that compiled code does not recompute them at each lookup
  let w := tabZ (fillRowsZ Bs D Δ X S lo (seedL t) 0 Δ)
  [0, 1, 2].map fun a : Fin 3 =>
    Bs.foldl (fun m B => max m (cdivZ (stepZ B D Δ X S w 0 a true) (X.M D))) (lo 0 a true)

def det3Z (a b c d e f g h i : ℤ) : ℤ := a * (e * i - f * h) - b * (d * i - f * g) + c * (d * h - e * g)

/-- One Newton step for the fixed point of `seedStepZ` from `t`, on differences of size `h`,
rounded up; `t` itself if the linear system is singular. -/
def newtonZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (h : ℤ) (t : List ℤ) : List ℤ :=
  let F := seedStepZ Bs D Δ X S lo
  let f := F t
  let t0 := t.getD 0 0
  let t1 := t.getD 1 0
  let t2 := t.getD 2 0
  let g0 := F [t0 + h, t1, t2]
  let g1 := F [t0, t1 + h, t2]
  let g2 := F [t0, t1, t2 + h]
  -- the slopes times `h`, column `j` from `gj`
  let d := fun (g : List ℤ) (i : ℕ) => g.getD i 0 - f.getD i 0
  -- `(h I - D) x = h f - D t`
  let r := fun i => h * f.getD i 0 - (d g0 i * t0 + d g1 i * t1 + d g2 i * t2)
  let m := det3Z (h - d g0 0) (-d g1 0) (-d g2 0) (-d g0 1) (h - d g1 1) (-d g2 1) (-d g0 2) (-d g1 2) (h - d g2 2)
  if m ≤ 0 then t else
    [cdivZ (det3Z (r 0) (-d g1 0) (-d g2 0) (r 1) (h - d g1 1) (-d g2 1) (r 2) (-d g1 2) (h - d g2 2)) m,
     cdivZ (det3Z (h - d g0 0) (r 0) (-d g2 0) (-d g0 1) (r 1) (-d g2 1) (-d g0 2) (r 2) (h - d g2 2)) m,
     cdivZ (det3Z (h - d g0 0) (-d g1 0) (r 0) (-d g0 1) (h - d g1 1) (r 1) (-d g0 2) (-d g1 2) (r 2)) m]

def leL (l m : List ℤ) : Bool := (List.zipWith (fun x y => decide (x ≤ y)) l m).all id

/-- Seeds solving the recursion at `(0, a, true)`: `n` Newton steps from `t`, each raised by
`pad` and floored at `lo`, then up to `k` steps of the recursion itself (which only raise the
seeds) while they are not yet a solution. -/
def solveSeedsZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ)
    (h pad : ℤ) (n k : ℕ) (t : List ℤ) : List ℤ :=
  let N := fun t => List.zipWith max [lo 0 0 true, lo 0 1 true, lo 0 2 true]
    ((newtonZ Bs D Δ X S lo h t).map (· + pad))
  let rec go : ℕ → List ℤ → List ℤ
    | 0, x => x
    | k + 1, x => let y := seedStepZ Bs D Δ X S lo x; if leL y x then x else go k (List.zipWith max x y)
  go k (N^[n] t)

/-- The seeds of each member in turn, by `n` Newton steps for the first member (from `t`) and
`n'` for each later one, from the previous member's seeds. -/
def seedsZ (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) (h pad : ℤ) (n n' k : ℕ) :
    List BandZ → List ℤ → List (List ℤ)
  | [], _ => []
  | B :: Bs, t =>
    let x := solveSeedsZ [B] D Δ X S lo h pad n k t
    x :: seedsZ D Δ X S lo h pad n' n' k Bs x

/-- `vmax` listed by `(q, a, u)`, from every member's post-switch seeds. -/
def vmaxListZ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (seeds : List (List ℤ)) : List ℤ :=
  (List.zipWith (fun B t => fillRowsZ [B] D Δ X S (gFloorZ X S) (seedL t) 0 Δ) famL seeds).foldl
    (List.zipWith max) (List.replicate (6 * Δ) 0)

/-- Every member's pre-switch seeds, from `vmax`'s (`n` Newton steps, then up to `k` steps of
the recursion). -/
def preSeedsZ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (h pad : ℤ) (n k : ℕ)
    (seeds : List (List ℤ)) : List (List ℤ) :=
  let vm := vmaxListZ famL D Δ X S seeds
  famL.map fun B => solveSeedsZ [B] D Δ X S (tabZ vm) h pad n k [vm.getD 1 0, vm.getD 3 0, vm.getD 5 0]

/-! ## Rounding to significant digits -/

/-- The number of decimal digits of `n` (one for `0`), with fuel `f`. -/
def ndigits : ℕ → ℕ → ℕ
  | 0, _ => 0
  | f + 1, n => if n < 10 then 1 else ndigits f (n / 10) + 1

/-- `⌊log₁₀ x⌋` for `0 < x`, computed as the generator computes it (`certnum.flog10`). -/
def flog10Q (x : ℚ) : ℤ :=
  let e : ℤ := (ndigits 1000 x.num.natAbs : ℤ) - (ndigits 1000 x.den : ℤ)
  let e := if x < (10 : ℚ) ^ e then e - 1 else e
  if (10 : ℚ) ^ (e + 1) ≤ x then e + 1 else e

/-- `x` rounded up to `d` significant digits (`certnum.rup`). -/
def rupQ (d : ℕ) (x : ℚ) : ℚ :=
  if x = 0 then 0 else ⌈x / (10 : ℚ) ^ (flog10Q x - d + 1)⌉ * (10 : ℚ) ^ (flog10Q x - d + 1)

/-- `x` rounded down to `d` significant digits (`certnum.rdn`). -/
def rdnQ (d : ℕ) (x : ℚ) : ℚ :=
  if x = 0 then 0 else ⌊x / (10 : ℚ) ^ (flog10Q x - d + 1)⌋ * (10 : ℚ) ^ (flog10Q x - d + 1)

theorem le_rupQ (d : ℕ) (x : ℚ) : x ≤ rupQ d x := by
  unfold rupQ
  split_ifs with h
  · exact h.le
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    calc x = x / 10 ^ (flog10Q x - d + 1) * 10 ^ (flog10Q x - d + 1) := by field_simp
      _ ≤ _ := mul_le_mul_of_nonneg_right (Int.le_ceil _) hq.le

theorem rdnQ_le (d : ℕ) (x : ℚ) : rdnQ d x ≤ x := by
  unfold rdnQ
  split_ifs with h
  · exact h.ge
  · have hq : (0 : ℚ) < 10 ^ (flog10Q x - d + 1) := zpow_pos (by norm_num) _
    calc _ ≤ x / 10 ^ (flog10Q x - d + 1) * 10 ^ (flog10Q x - d + 1) :=
          mul_le_mul_of_nonneg_right (Int.floor_le _) hq.le
      _ = x := by field_simp

/-! ## Data computed for a certificate -/

/-- A phase expectation's numbers over the integers, from their rational values: `x`, `θ` as
fractions, `g` over the least common denominator of its entries. -/
def PhZ.ofQ (p : ℚ × ℚ × (Fin 3 → Bool → Bool → ℚ)) : PhZ :=
  let gs := [p.2.2 0 false false, p.2.2 0 false true, p.2.2 0 true false, p.2.2 0 true true,
    p.2.2 1 false false, p.2.2 1 false true, p.2.2 1 true false, p.2.2 1 true true,
    p.2.2 2 false false, p.2.2 2 false true, p.2.2 2 true false, p.2.2 2 true true]
  let gd : ℕ := gs.foldl (fun m q => Nat.lcm m q.den) 1
  ⟨p.1.num, p.1.den, p.2.1.num, p.2.1.den, fun a b u => (p.2.2 a b u * gd).num, gd⟩

/-- Each member's in-epoch phase bound: its post-switch table's bound, rounded up to `d`
significant digits. -/
def eInListQ (famL : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (d : ℕ) (seeds : List (List ℤ)) : List ℚ :=
  List.zipWith (fun B t => rupQ d ((autoBoundZ B D X S (tabZ (fillRowsZ [B] D Δ X S (gFloorZ X S) (seedL t) 0 Δ)) : ℚ) /
    (X.M D * S : ℤ))) famL seeds

/-! ## One check per phase index -/

section Index

variable {K : ℕ} {famZ : Fin K → BandZ} {D : ℤ} {famQ : Fin K → BandQ} {fam : Fin K → Band}
  {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} {S : ℤ} {Δ : ℕ}

/-- The post-switch table of a member, from its seeds. -/
def postF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ) (k : Fin K) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillZ (famZ k) D Δ X S (gFloorZ X S) (postTop k)

/-- `vmax`: the entrywise maximum of the post-switch tables. -/
def vmaxF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ) :
    ℕ → Fin 3 → Bool → ℤ :=
  maxTabZ Δ ((List.finRange K).map (postF famZ D Δ X S postTop))

/-- The pre-switch table of a member, from its seeds: floored at `vmax`. -/
def preF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop preTop : Fin K → Fin 3 → ℤ) (k : Fin K) :
    ℕ → Fin 3 → Bool → ℤ :=
  fillZ (famZ k) D Δ X S (vmaxF famZ D Δ X S postTop) (preTop k)

/-- Every check of member `k` of a one-switch index. -/
def chkOneF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop preTop : Fin K → Fin 3 → ℤ)
    (eIn : Fin K → ℚ) (eE : ℚ) (k : Fin K) : Bool :=
  let post := postF famZ D Δ X S postTop k
  let pre := preF famZ D Δ X S postTop preTop k
  seedOKZ (famZ k) D Δ X S (gFloorZ X S) post && seedOKZ (famZ k) D Δ X S (vmaxF famZ D Δ X S postTop) pre &&
    decide ((autoBoundZ (famZ k) D X S post : ℚ) ≤ eIn k * (X.M D * S : ℤ)) &&
    decide ((autoBoundZ (famZ k) D X S pre : ℚ) ≤ eE * (X.M D * S : ℤ))

/-- **The one-switch tables of an index, for the whole family, from seeds alone.** -/
theorem oneSwitchF_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {postTop preTop : Fin K → Fin 3 → ℤ} {eIn : Fin K → ℚ} {eE : ℚ}
    (h : (List.finRange K).all (chkOneF famZ D Δ X S postTop preTop eIn eE) = true) :
    AutoSolE fam Δ x θ (castG g) (fun k => castZ S (preF famZ D Δ X S postTop preTop k))
        (fun k => castZ S (postF famZ D Δ X S postTop k)) (castZ S (vmaxF famZ D Δ X S postTop)) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castZ S (postF famZ D Δ X S postTop k)) ≤ eIn k) ∧
      (∀ k, autoBound (fam k) x θ (castG g) (castZ S (preF famZ D Δ X S postTop preTop k)) ≤ eE) := by
  have hk : ∀ k, _ := fun k => List.all_eq_true.1 h k (List.mem_finRange k)
  simp only [chkOneF, Bool.and_eq_true, decide_eq_true_eq] at hk
  have hB := fun k => List.mem_singleton_self (famZ k)
  refine ⟨⟨fun k => fill_autoSol (hR k) (hA k) hD hX hS (hB k) (hk k).1.1.1,
    fun k q hq a u => castZ_le hS (le_maxTabZ (List.mem_map.2 ⟨k, List.mem_finRange k, rfl⟩) hq a u),
    fun k => fill_preSol (hR k) (hA k) hD hX hS (hB k) (hk k).1.1.2⟩,
    fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).1.2, fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).2⟩

/-- Every check of member `k` against a switching table. -/
def chkSwF (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (top : Fin 3 → ℤ) (eS : Fin K → ℚ)
    (k : Fin K) : Bool :=
  let vs := fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top
  seedOKZ (famZ k) D Δ X S (gFloorZ X S) vs && decide ((autoBoundZ (famZ k) D X S vs : ℚ) ≤ eS k * (X.M D * S : ℤ))

/-- **A switching table of an index, for the whole family, from its seeds alone.** -/
theorem switchF_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {top : Fin 3 → ℤ} {eS : Fin K → ℚ}
    (h : (List.finRange K).all (chkSwF famZ D Δ X S top eS) = true) :
    (∀ k, AutoSol (fam k) Δ x θ (castG g) (castZ S (fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top))) ∧
      (∀ k, autoBound (fam k) x θ (castG g)
        (castZ S (fillAllZ ((List.finRange K).map famZ) D Δ X S (gFloorZ X S) top)) ≤ eS k) := by
  have hk : ∀ k, _ := fun k => List.all_eq_true.1 h k (List.mem_finRange k)
  simp only [chkSwF, Bool.and_eq_true, decide_eq_true_eq] at hk
  exact ⟨fun k => fill_autoSol (hR k) (hA k) hD hX hS (List.mem_map.2 ⟨k, List.mem_finRange k, rfl⟩) (hk k).1,
    fun k => autoBoundZ_le (hR k) (hA k) hD hX hS (hk k).2⟩

/-! ## Delayed tables

A phase that starts more than `R` slots before the next boundary is bounded by its group's delayed tables
(`phase_autoD`): from `vmax`, each slot one recursion step of the one before, the largest over the group's
members (`stepTabGZ`, rounded up), `R` times, the last one checked to satisfy each member's recursion. -/

/-- A table from its rows, each listed by `(a, u)`; `0` beyond. A lookup walks at most the rows and six
entries. -/
def tabRZ (rows : List (List ℤ)) : ℕ → Fin 3 → Bool → ℤ := fun q a u =>
  (rows.getD q []).getD (2 * a.val + if u then 1 else 0) 0

/-- The rows `q, …, q + n - 1` of a table. -/
def rowsZ (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → ℕ → List (List ℤ)
  | _, 0 => []
  | q, n + 1 => [v q 0 false, v q 0 true, v q 1 false, v q 1 true, v q 2 false, v q 2 true] :: rowsZ v (q + 1) n

theorem rowsZ_getD (v : ℕ → Fin 3 → Bool → ℤ) : ∀ (j n q : ℕ) (a : Fin 3) (u : Bool), j < n →
    tabRZ (rowsZ v q n) j a u = v (q + j) a u
  | 0, n + 1, q, a, u, _ => by
    simp only [tabRZ, rowsZ, List.getD_cons_zero, Nat.add_zero]
    fin_cases a <;> cases u <;> rfl
  | j + 1, n + 1, q, a, u, hj => by
    have := rowsZ_getD v j n (q + 1) a u (by omega)
    simp only [tabRZ, rowsZ, List.getD_cons_succ] at this ⊢
    rw [this, show q + 1 + j = q + (j + 1) by omega]

/-- A table evaluated once and kept by rows. -/
def memoRZ (Δ : ℕ) (v : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℤ := tabRZ (rowsZ v 0 Δ)

theorem memoRZ_eq {Δ : ℕ} {v : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    memoRZ Δ v q a u = v q a u := by
  unfold memoRZ; rw [rowsZ_getD v q Δ 0 a u hq, Nat.zero_add]

/-- One recursion step, the largest over the bands `Bs` and at least `0`, rounded up to the scale, as a
table kept by rows. -/
def stepTabGZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (w : ℕ → Fin 3 → Bool → ℤ) : ℕ → Fin 3 → Bool → ℤ :=
  memoRZ Δ fun q a u => Bs.foldl (fun m B => max m (cdivZ (stepZ B D Δ X S w q a u) (X.M D))) 0

/-- Every entry `q < Δ` of `w` at least `lo`'s. -/
def leTabZ (Δ : ℕ) (lo w : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  (List.range Δ).all fun q => (List.finRange 3).all fun a => decide (lo q a false ≤ w q a false) &&
    decide (lo q a true ≤ w q a true)

theorem leTabZ_sound {Δ : ℕ} {lo w : ℕ → Fin 3 → Bool → ℤ} (h : leTabZ Δ lo w = true) {q : ℕ} (hq : q < Δ)
    (a : Fin 3) (u : Bool) : lo q a u ≤ w q a u := by
  simp only [leTabZ, List.all_eq_true, List.mem_range, List.mem_finRange, Bool.and_eq_true, decide_eq_true_eq,
    forall_const] at h
  cases u
  exacts [(h q hq a).1, (h q hq a).2]

/-- Every entry `q < Δ` of `w` solves band `B`'s recursion. -/
def solTabZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (w : ℕ → Fin 3 → Bool → ℤ) : Bool :=
  (List.range Δ).all fun q => (List.finRange 3).all fun a =>
    decide (stepZ B D Δ X S w q a false ≤ w q a false * X.M D) && decide (stepZ B D Δ X S w q a true ≤ w q a true * X.M D)

theorem solTabZ_sound {B : BandZ} {D : ℤ} {Δ : ℕ} {X : PhZ} {S : ℤ} {w : ℕ → Fin 3 → Bool → ℤ}
    (h : solTabZ B D Δ X S w = true) {q : ℕ} (hq : q < Δ) (a : Fin 3) (u : Bool) :
    stepZ B D Δ X S w q a u ≤ w q a u * X.M D := by
  simp only [solTabZ, List.all_eq_true, List.mem_range, List.mem_finRange, Bool.and_eq_true, decide_eq_true_eq,
    forall_const] at h
  cases u
  exacts [(h q hq a).1, (h q hq a).2]

/-- `stepTabGZ` on a table's rows (`tabRZ`), as rows: the delayed tables are passed as data, so that
evaluation does not recompute them. -/
def stepLGZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (l : List (List ℤ)) : List (List ℤ) :=
  rowsZ (fun q a u => Bs.foldl (fun m B => max m (cdivZ (stepZ B D Δ X S (tabRZ l) q a u) (X.M D))) 0) 0 Δ

/-- `R` delayed steps from the table listed by `l`, each table checked above `lo`: whether all are, and
the last table's list. -/
def dlyGoZ (Bs : List BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (lo : ℕ → Fin 3 → Bool → ℤ) :
    ℕ → List (List ℤ) → Bool × List (List ℤ)
  | 0, l => (leTabZ Δ lo (tabRZ l), l)
  | r + 1, l =>
    let p := dlyGoZ Bs D Δ X S lo r (stepLGZ Bs D Δ X S l)
    (leTabZ Δ lo (tabRZ l) && p.1, p.2)

theorem dlyGoZ_spec {Bs : List BandZ} {D : ℤ} {Δ : ℕ} {X : PhZ} {S : ℤ} {lo : ℕ → Fin 3 → Bool → ℤ} :
    ∀ (n : ℕ) (l : List (List ℤ)), tabRZ (dlyGoZ Bs D Δ X S lo n l).2 = (stepTabGZ Bs D Δ X S)^[n] (tabRZ l) ∧
      ((dlyGoZ Bs D Δ X S lo n l).1 = true → ∀ r ≤ n, leTabZ Δ lo ((stepTabGZ Bs D Δ X S)^[r] (tabRZ l)) = true)
  | 0, l => ⟨rfl, fun h r hr => by rw [Nat.le_zero.1 hr]; exact h⟩
  | n + 1, l => by
    obtain ⟨h2, h1⟩ := dlyGoZ_spec n (stepLGZ Bs D Δ X S l)
    have hs : stepTabGZ Bs D Δ X S (tabRZ l) = tabRZ (stepLGZ Bs D Δ X S l) := rfl
    refine ⟨by rw [Function.iterate_succ_apply, hs]; exact h2, fun h r hr => ?_⟩
    simp only [dlyGoZ, Bool.and_eq_true] at h
    rcases r with _ | r
    · exact h.1
    · rw [Function.iterate_succ_apply, hs]; exact h1 h.2 r (by omega)

section DlySound

variable {B : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D) {X : PhZ}
  {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (hX : X.Rep x θ g) {S : ℤ} (hS : 0 < S) {Δ : ℕ}
include hR hA hD hX hS

/-- A rounded-up step over bands including `B` is above `B`'s recursion step. -/
theorem stepTabGZ_sound {Bs : List BandZ} (hB : B ∈ Bs) (w : ℕ → Fin 3 → Bool → ℤ) {q : ℕ} (hq : q < Δ) (a : Fin 3)
    (u : Bool) : stepR Bb Δ x θ (castG g) (castZ S w) q a u ≤ castZ S (stepTabGZ Bs D Δ X S w) q a u := by
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have h1 : stepZ B D Δ X S w q a u ≤ stepTabGZ Bs D Δ X S w q a u * X.M D := by
    unfold stepTabGZ; rw [memoRZ_eq hq]
    refine le_trans (cdivZ_mul_ge (X.M_pos hX hD)) (Int.mul_le_mul_of_nonneg_right ?_ (X.M_pos hX hD).le)
    exact (foldl_max_ge (fun B' => cdivZ (stepZ B' D Δ X S w q a u) (X.M D)) Bs 0).2 B hB
  have h2 : (stepZ B D Δ X S w q a u : ℝ) ≤ (stepTabGZ Bs D Δ X S w q a u : ℝ) * X.M D := by exact_mod_cast h1
  rw [stepZ_cast hR hA hD hX hS] at h2
  rw [castZ, le_div_iff₀ hS']
  nlinarith [mul_pos hM hS']

/-- A table above the terminal table's floor is above `g`. -/
theorem gFloor_term {w : ℕ → Fin 3 → Bool → ℤ} {q : ℕ} (a : Fin 3) (u : Bool) (h : gFloorZ X S q a u ≤ w q a u) :
    castG g a true u ≤ castZ S w q a u := by
  have hgd : (0 : ℝ) < X.gd := by exact_mod_cast hX.gd
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  refine le_trans ?_ (castZ_le hS h)
  rw [castG, castZ, hX.g]
  push_cast
  rw [div_le_div_iff₀ hgd hS']
  exact_mod_cast gFloorZ_ge hX.gd q a u

end DlySound

/-- **A group's delayed tables, checked**: `R` steps from `vmax` over the members `ks`, each above the
terminal floor, the last solving each member's recursion with phase bound at most `eD k`. -/
def chkDlyG {K : ℕ} (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ)
    (ks : List (Fin K)) (R : ℕ) (eD : Fin K → ℚ) : Bool :=
  let p := dlyGoZ (ks.map famZ) D Δ X S (gFloorZ X S) R (rowsZ (vmaxF famZ D Δ X S postTop) 0 Δ)
  p.1 && ks.all fun k => solTabZ (famZ k) D Δ X S (tabRZ p.2) &&
    decide ((autoBoundZ (famZ k) D X S (tabRZ p.2) : ℚ) ≤ eD k * (X.M D * S : ℤ))

/-- A group's `r`-th delayed table. -/
def dlyTabGZ {K : ℕ} (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ)
    (ks : List (Fin K)) (r : ℕ) : ℕ → Fin 3 → Bool → ℤ :=
  (stepTabGZ (ks.map famZ) D Δ X S)^[r] (tabRZ (rowsZ (vmaxF famZ D Δ X S postTop) 0 Δ))

/-- **A group's delayed tables, from their check**, for each member `k` of the group: the first is `vmax`,
each is above `k`'s recursion step of the one before, the last above its own, all above `g`, and the
last's phase bound at most `eD k`. -/
theorem dlyG_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {postTop : Fin K → Fin 3 → ℤ} {ks : List (Fin K)} {R : ℕ} {eD : Fin K → ℚ}
    (h : chkDlyG famZ D Δ X S postTop ks R eD = true) {k : Fin K} (hk : k ∈ ks) :
    (∀ q < Δ, ∀ a u, castZ S (vmaxF famZ D Δ X S postTop) q a u ≤ castZ S (dlyTabGZ famZ D Δ X S postTop ks 0) q a u) ∧
    (∀ r < R, ∀ q < Δ, ∀ a u, stepR (fam k) Δ x θ (castG g) (castZ S (dlyTabGZ famZ D Δ X S postTop ks r)) q a u ≤
      castZ S (dlyTabGZ famZ D Δ X S postTop ks (r + 1)) q a u) ∧
    (∀ q < Δ, ∀ a u, stepR (fam k) Δ x θ (castG g) (castZ S (dlyTabGZ famZ D Δ X S postTop ks R)) q a u ≤
      castZ S (dlyTabGZ famZ D Δ X S postTop ks R) q a u) ∧
    (∀ r ≤ R, ∀ q < Δ, ∀ a u, castG g a true u ≤ castZ S (dlyTabGZ famZ D Δ X S postTop ks r) q a u) ∧
    autoBound (fam k) x θ (castG g) (castZ S (dlyTabGZ famZ D Δ X S postTop ks R)) ≤ eD k := by
  simp only [chkDlyG, Bool.and_eq_true, List.all_eq_true, decide_eq_true_eq] at h
  obtain ⟨h1, h2⟩ := h
  obtain ⟨he, hle⟩ := dlyGoZ_spec R (rowsZ (vmaxF famZ D Δ X S postTop) 0 Δ)
    (Bs := ks.map famZ) (D := D) (Δ := Δ) (X := X) (S := S) (lo := gFloorZ X S)
  obtain ⟨h3, h4⟩ := h2 k hk
  rw [he] at h3 h4
  have hB : famZ k ∈ ks.map famZ := List.mem_map_of_mem hk
  refine ⟨fun q hq a u => ?_, fun r _ q hq a u => ?_, fun q hq a u => ?_, fun r hr q hq a u => ?_, ?_⟩
  · unfold dlyTabGZ; rw [Function.iterate_zero, id]
    exact le_of_eq (by unfold castZ; congr 1; exact_mod_cast (memoRZ_eq (v := vmaxF famZ D Δ X S postTop) hq a u).symm)
  · unfold dlyTabGZ
    rw [Function.iterate_succ_apply']
    exact stepTabGZ_sound (hR k) (hA k) hD hX hS hB _ hq a u
  · exact stepZ_le (hR k) (hA k) hD hX hS (solTabZ_sound h3 hq a u)
  · exact gFloor_term (hR k) (hA k) hD hX hS a u (leTabZ_sound (hle h1 r hr) hq a u)
  · exact autoBoundZ_le (hR k) (hA k) hD hX hS h4

/-! ## A geometric envelope of the delayed tables

Instead of `R` explicit steps, a member's delayed tables are bounded by `P + λ^r Z` (`phase_autoEnv`),
with `P` its post-switch table: one check of `Z` (`chkEnvZ`) covers every `R`. -/

/-- The phase expectation with the terminal table at `0`. -/
def PhZ.zeroG (X : PhZ) : PhZ := { X with gn := fun _ _ _ => 0 }

theorem PhZ.zeroG_rep {X : PhZ} {x θ : ℚ} {g : Fin 3 → Bool → Bool → ℚ} (h : X.Rep x θ g) :
    X.zeroG.Rep x θ (fun _ _ _ => 0) :=
  ⟨h.xd, h.θd, h.gd, h.x, h.θ, fun _ _ _ => by simp [PhZ.zeroG]⟩

@[simp] theorem PhZ.zeroG_M (X : PhZ) (D : ℤ) : X.zeroG.M D = X.M D := rfl

/-- Every entry `q < Δ` passes `p`. -/
def allTabZ (Δ : ℕ) (p : ℕ → Fin 3 → Bool → Bool) : Bool :=
  (List.range Δ).all fun q => (List.finRange 3).all fun a => p q a false && p q a true

theorem allTabZ_sound {Δ : ℕ} {p : ℕ → Fin 3 → Bool → Bool} (h : allTabZ Δ p = true) {q : ℕ} (hq : q < Δ)
    (a : Fin 3) (u : Bool) : p q a u = true := by
  simp only [allTabZ, List.all_eq_true, List.mem_range, List.mem_finRange, Bool.and_eq_true, forall_const] at h
  cases u
  exacts [(h q hq a).1, (h q hq a).2]

/-- **A member's envelope, checked**: `Z` (by rows) nonnegative and above `vmax` less the member's
post-switch table, its step without the terminal table at most `lam` times it, `0 ≤ lam ≤ 1`, and its
phase bound without the terminal table at most `aZ`. -/
def chkEnvZ {K : ℕ} (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (postTop : Fin K → Fin 3 → ℤ)
    (k : Fin K) (Z : List (List ℤ)) (lam aZ : ℚ) : Bool :=
  let vm := vmaxF famZ D Δ X S postTop
  let P := postF famZ D Δ X S postTop k
  let z := tabRZ Z
  allTabZ Δ (fun q a u => decide (0 ≤ z q a u) && decide (vm q a u ≤ P q a u + z q a u) &&
    decide ((lam.den : ℤ) * stepZ (famZ k) D Δ X.zeroG S z q a u ≤ lam.num * (z q a u * X.M D))) &&
    decide (0 ≤ lam) && decide (lam ≤ 1) && decide ((autoBoundZ (famZ k) D X.zeroG S z : ℚ) ≤ aZ * (X.M D * S : ℤ))

/-- **A member's envelope, from its check.** -/
theorem env_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {postTop : Fin K → Fin 3 → ℤ} {k : Fin K} {Z : List (List ℤ)} {lam aZ : ℚ}
    (h : chkEnvZ famZ D Δ X S postTop k Z lam aZ = true) :
    (∀ q < Δ, ∀ a u, 0 ≤ castZ S (tabRZ Z) q a u) ∧
    (∀ q < Δ, ∀ a u, castZ S (vmaxF famZ D Δ X S postTop) q a u ≤
      castZ S (postF famZ D Δ X S postTop k) q a u + castZ S (tabRZ Z) q a u) ∧
    (∀ q < Δ, ∀ a u, stepR (fam k) Δ x θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) q a u ≤ lam * castZ S (tabRZ Z) q a u) ∧
    (0 : ℝ) ≤ lam ∧ (lam : ℝ) ≤ 1 ∧
    autoBound (fam k) x θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) ≤ aZ := by
  simp only [chkEnvZ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨hall, hl0⟩, hl1⟩, hb⟩ := h
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have hX0 := PhZ.zeroG_rep hX
  have hg0 : castG (fun _ _ _ => (0 : ℚ)) = fun _ _ _ => (0 : ℝ) := by funext a b u; simp [castG]
  have e := fun q (hq : q < Δ) a u => allTabZ_sound hall hq a u
  simp only [Bool.and_eq_true, decide_eq_true_eq] at e
  refine ⟨fun q hq a u => ?_, fun q hq a u => ?_, fun q hq a u => ?_, by exact_mod_cast hl0, by exact_mod_cast hl1, ?_⟩
  · exact div_nonneg (by exact_mod_cast (e q hq a u).1.1) hS'.le
  · unfold castZ; rw [← add_div]; exact div_le_div_of_nonneg_right (by exact_mod_cast (e q hq a u).1.2) hS'.le
  · have h3 := (e q hq a u).2
    have hc := stepZ_cast (hR k) (hA k) hD hX0 hS Δ (tabRZ Z) q a u
    rw [hg0] at hc
    have hd : (0 : ℝ) < lam.den := by exact_mod_cast lam.den_pos
    have h3' : ((lam.den : ℤ) : ℝ) * (stepZ (famZ k) D Δ X.zeroG S (tabRZ Z) q a u : ℝ) ≤
        (lam.num : ℝ) * ((tabRZ Z q a u : ℝ) * (X.M D : ℝ)) := by exact_mod_cast h3
    rw [hc, PhZ.zeroG_M] at h3'
    have hlam : (lam : ℝ) = lam.num / lam.den := by exact_mod_cast (Rat.num_div_den lam).symm
    rw [hlam, castZ, div_mul_div_comm, le_div_iff₀ (by positivity)]
    push_cast at h3'
    set st := stepR (fam k) Δ (x : ℝ) θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) q a u
    have key : st * ((lam.den : ℝ) * S) * (X.M D : ℝ) ≤ (lam.num : ℝ) * (tabRZ Z q a u : ℝ) * (X.M D : ℝ) := by
      nlinarith
    exact le_of_mul_le_mul_right key hM
  · have := autoBoundZ_le (hR k) (hA k) hD hX0 hS (by rw [PhZ.zeroG_M]; exact hb)
    rwa [hg0] at this

/-- **A member's envelope, by rule**: from `Y₀ = (vmax - P)⁺ + 1` at a scale `2^32` finer, the iterates
`Yᵢ₊₁` of the step without the terminal table (rounded up), `Z = Σ_{i<n} Yᵢ / μ^i` by Horner's rule, rounded
up to the table's scale, and the least `λ` with `L(Z) ≤ λ Z` and `Z`'s phase bound, rounded up to 13
digits; `λ = 1` when `Z` has a zero entry where its step is not. The `+ 1` keeps `Z` positive where
`vmax - P` is only rounding. The tables are passed by rows. -/
def envZ (B : BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (P vm : List (List ℤ)) (mu : ℚ) (n : ℕ) :
    List (List ℤ) × ℚ × ℚ :=
  let X0 := X.zeroG
  let m := X.M D
  let L : List (List ℤ) → List (List ℤ) := fun Y =>
    rowsZ (fun q a u => max 0 (cdivZ (stepZ B D Δ X0 S (tabRZ Y) q a u) m)) 0 Δ
  let T : ℤ := 2 ^ 32
  let Y0 := rowsZ (fun q a u => (max 0 (tabRZ vm q a u - tabRZ P q a u) + 1) * T) 0 Δ
  let ys := (List.range n).foldl (fun acc _ => acc ++ [L (acc.getLast?.getD Y0)]) [Y0]
  let acc := (ys.take n).reverse.foldl (fun acc Y =>
    rowsZ (fun q a u => tabRZ Y q a u + cdivZ (tabRZ acc q a u * mu.den) mu.num) 0 Δ) (rowsZ (fun _ _ _ => 0) 0 Δ)
  let hor := rowsZ (fun q a u => cdivZ (tabRZ acc q a u) T) 0 Δ
  let z := tabRZ hor
  let ent := (List.range Δ).flatMap fun q => (List.finRange 3).flatMap fun a => [(q, a, false), (q, a, true)]
  let lam := ent.foldl (fun l e => let zz := z e.1 e.2.1 e.2.2
    let lz := stepZ B D Δ X0 S z e.1 e.2.1 e.2.2
    if zz = 0 then (if lz ≤ 0 then l else 1) else max l ((lz : ℚ) / (zz * m))) 0
  (hor, rupQ 13 lam, rupQ 13 ((autoBoundZ B D X0 S z : ℚ) / (m * S)))

/-! ## The worst band

The members' post-switch tables are all bounded by one table for the family's worst band (larger upper
fields, smaller lower ones), as `slot4` is monotone in the band (`AutoSol.of_worse`); so is the pre-switch
table. One table each then serves every member, with each of the start's group's members' own post-switch
table for its in-epoch bound (`chkOneW`). -/

/-- `B'` is worse than `B`, as a check. -/
def worseZ (B B' : BandZ) : Bool :=
  decide (B.hhi ≤ B'.hhi) && decide (B'.hlo ≤ B.hlo) && decide (B.amax ≤ B'.amax) && decide (B'.alo ≤ B.alo) &&
    decide (B.hahi ≤ B'.hahi) && decide (B'.halo ≤ B.halo)

/-- The family's worst band, field by field. -/
def worstZ (l : List BandZ) : BandZ :=
  let b0 := l.headD ⟨0, 0, 0, 0, 0, 0⟩
  l.foldl (fun w B => ⟨max w.hhi B.hhi, min w.hlo B.hlo, max w.amax B.amax, max w.hahi B.hahi, min w.alo B.alo,
    min w.halo B.halo⟩) b0

/-- A band over `ℚ` from its integers. -/
def BandZ.toQ (B : BandZ) (D : ℤ) : BandQ :=
  ⟨(B.hhi : ℚ) / D, (B.hlo : ℚ) / D, (B.amax : ℚ) / D, (B.hahi : ℚ) / D, (B.alo : ℚ) / D, (B.halo : ℚ) / D⟩

theorem BandZ.rep_toQ (B : BandZ) (D : ℤ) : B.Rep D (B.toQ D) := ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

/-- A band with the fields `slot4` reads, the others `0`. -/
noncomputable def BandQ.toBandR (b : BandQ) : Band :=
  { hhi := b.hhi, hlo := b.hlo, amax := b.amax, hahi := b.hahi, slo := 0, hnlo := 0, elo := 0, alo := b.alo,
    halo := b.halo }

theorem BandQ.agrees_toBandR (b : BandQ) : b.Agrees b.toBandR := ⟨rfl, rfl, rfl, rfl, rfl, rfl⟩

theorem worse_of {B B' : BandZ} {D : ℤ} {b : BandQ} {Bb : Band} (hR : B.Rep D b) (hA : b.Agrees Bb) (hD : 0 < D)
    (h : worseZ B B' = true) : Bb.Worse (B'.toQ D).toBandR := by
  simp only [worseZ, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨⟨⟨h1, h2⟩, h3⟩, h4⟩, h5⟩, h6⟩ := h
  have hD' : (0 : ℝ) < D := by exact_mod_cast hD
  have c : ∀ a c : ℤ, a ≤ c → (a : ℝ) / D ≤ (c : ℝ) / D := fun a c h =>
    div_le_div_of_nonneg_right (by exact_mod_cast h) hD'.le
  simp only [BandQ.toBandR, BandZ.toQ]
  refine ⟨?_, ?_, ?_, ?_, ?_, ?_⟩ <;>
    simp only [hA.hhi, hA.hlo, hA.amax, hA.alo, hA.hahi, hA.halo, hR.hhi, hR.hlo, hR.amax, hR.alo, hR.hahi, hR.halo] <;>
    push_cast <;> first | exact c _ _ h1 | exact c _ _ h2 | exact c _ _ h3 | exact c _ _ h4 | exact c _ _ h5 | exact c _ _ h6

/-- **The one-switch tables from the worst band**: `W` for `BW` floored at `g` and the pre-switch table
`PW` floored at `W`, each from its seeds; `BW` worse than every member; and each of the members `ks`'s own
post-switch table from its seeds, with its in-epoch bound at most `eIn k` and the pre-switch bound at
most `eE`. -/
def chkOneW (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (BW : BandZ) (wTop pwTop : Fin 3 → ℤ)
    (postTop : Fin K → Fin 3 → ℤ) (ks : List (Fin K)) (eIn : Fin K → ℚ) (eE : ℚ) : Bool :=
  let W := fillZ BW D Δ X S (gFloorZ X S) wTop
  let PW := fillZ BW D Δ X S W pwTop
  decide (0 ≤ X.θn) && (List.finRange K).all (fun k => worseZ (famZ k) BW) &&
    seedOKZ BW D Δ X S (gFloorZ X S) W && seedOKZ BW D Δ X S W PW &&
    ks.all fun k => seedOKZ (famZ k) D Δ X S (gFloorZ X S) (postF famZ D Δ X S postTop k) &&
      decide ((autoBoundZ (famZ k) D X S (postF famZ D Δ X S postTop k) : ℚ) ≤ eIn k * (X.M D * S : ℤ)) &&
      decide ((autoBoundZ (famZ k) D X S PW : ℚ) ≤ eE * (X.M D * S : ℤ))

theorem oneSwitchW_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {BW : BandZ} {wTop pwTop : Fin 3 → ℤ} {postTop : Fin K → Fin 3 → ℤ}
    {ks : List (Fin K)} {eIn : Fin K → ℚ} {eE : ℚ}
    (h : chkOneW famZ D Δ X S BW wTop pwTop postTop ks eIn eE = true) :
    AutoSolE fam Δ x θ (castG g) (fun _ => castZ S (fillZ BW D Δ X S (fillZ BW D Δ X S (gFloorZ X S) wTop) pwTop))
        (fun _ => castZ S (fillZ BW D Δ X S (gFloorZ X S) wTop)) (castZ S (fillZ BW D Δ X S (gFloorZ X S) wTop)) ∧
      (∀ k ∈ ks, AutoSol (fam k) Δ x θ (castG g) (castZ S (postF famZ D Δ X S postTop k)) ∧
        autoBound (fam k) x θ (castG g) (castZ S (postF famZ D Δ X S postTop k)) ≤ eIn k ∧
        autoBound (fam k) x θ (castG g)
          (castZ S (fillZ BW D Δ X S (fillZ BW D Δ X S (gFloorZ X S) wTop) pwTop)) ≤ eE) := by
  simp only [chkOneW, Bool.and_eq_true, decide_eq_true_eq, List.all_eq_true] at h
  obtain ⟨⟨⟨⟨hθn, hw⟩, hW⟩, hPW⟩, hks⟩ := h
  have hθ : (0 : ℝ) ≤ θ := by
    have : (θ : ℚ) = X.θn / X.θd := hX.θ
    have h0 : (0 : ℚ) ≤ X.θn / X.θd := div_nonneg (by exact_mod_cast hθn) (by exact_mod_cast hX.θd.le)
    exact_mod_cast this ▸ h0
  have hRW := BandZ.rep_toQ BW D
  have hAW := (BW.toQ D).agrees_toBandR
  have hB : BW ∈ [BW] := List.mem_singleton_self _
  have sW := fill_autoSol hRW hAW hD hX hS hB hW
  have sPW := fill_preSol hRW hAW hD hX hS hB hPW
  have hwk : ∀ k, (fam k).Worse (BW.toQ D).toBandR := fun k =>
    worse_of (hR k) (hA k) hD (hw k (List.mem_finRange k))
  refine ⟨⟨fun k => AutoSol.of_worse (hwk k) hθ sW, fun k q _ a u => le_rfl,
    fun k => ⟨sPW.dom, fun q hq a u => (stepR_mono (hwk k) hθ _ _ q a u).trans (sPW.step q hq a u)⟩⟩,
    fun k hk => ?_⟩
  obtain ⟨⟨hs, hb⟩, he⟩ := hks k hk
  have hBk : famZ k ∈ [famZ k] := List.mem_singleton_self _
  exact ⟨fill_autoSol (hR k) (hA k) hD hX hS hBk hs, autoBoundZ_le (hR k) (hA k) hD hX hS hb,
    autoBoundZ_le (hR k) (hA k) hD hX hS he⟩

/-- **A member's envelope against `W`, checked**: as `chkEnvZ`, with `W` in place of `vmax`. -/
def chkEnvW (famZ : Fin K → BandZ) (D : ℤ) (Δ : ℕ) (X : PhZ) (S : ℤ) (W : ℕ → Fin 3 → Bool → ℤ)
    (postTop : Fin K → Fin 3 → ℤ) (k : Fin K) (Z : List (List ℤ)) (lam aZ : ℚ) : Bool :=
  let P := postF famZ D Δ X S postTop k
  let z := tabRZ Z
  allTabZ Δ (fun q a u => decide (0 ≤ z q a u) && decide (W q a u ≤ P q a u + z q a u) &&
    decide ((lam.den : ℤ) * stepZ (famZ k) D Δ X.zeroG S z q a u ≤ lam.num * (z q a u * X.M D))) &&
    decide (0 ≤ lam) && decide (lam ≤ 1) && decide ((autoBoundZ (famZ k) D X.zeroG S z : ℚ) ≤ aZ * (X.M D * S : ℤ))

theorem envW_sound (hR : ∀ k, (famZ k).Rep D (famQ k)) (hA : ∀ k, (famQ k).Agrees (fam k)) (hD : 0 < D)
    (hX : X.Rep x θ g) (hS : 0 < S) {W : ℕ → Fin 3 → Bool → ℤ} {postTop : Fin K → Fin 3 → ℤ} {k : Fin K}
    {Z : List (List ℤ)} {lam aZ : ℚ} (h : chkEnvW famZ D Δ X S W postTop k Z lam aZ = true) :
    (∀ q < Δ, ∀ a u, 0 ≤ castZ S (tabRZ Z) q a u) ∧
    (∀ q < Δ, ∀ a u, castZ S W q a u ≤ castZ S (postF famZ D Δ X S postTop k) q a u + castZ S (tabRZ Z) q a u) ∧
    (∀ q < Δ, ∀ a u, stepR (fam k) Δ x θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) q a u ≤ lam * castZ S (tabRZ Z) q a u) ∧
    (0 : ℝ) ≤ lam ∧ (lam : ℝ) ≤ 1 ∧
    autoBound (fam k) x θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) ≤ aZ := by
  simp only [chkEnvW, Bool.and_eq_true, decide_eq_true_eq] at h
  obtain ⟨⟨⟨hall, hl0⟩, hl1⟩, hb⟩ := h
  have hS' : (0 : ℝ) < S := by exact_mod_cast hS
  have hM : (0 : ℝ) < X.M D := by exact_mod_cast X.M_pos hX hD
  have hX0 := PhZ.zeroG_rep hX
  have hg0 : castG (fun _ _ _ => (0 : ℚ)) = fun _ _ _ => (0 : ℝ) := by funext a b u; simp [castG]
  have e := fun q (hq : q < Δ) a u => allTabZ_sound hall hq a u
  simp only [Bool.and_eq_true, decide_eq_true_eq] at e
  refine ⟨fun q hq a u => ?_, fun q hq a u => ?_, fun q hq a u => ?_, by exact_mod_cast hl0, by exact_mod_cast hl1, ?_⟩
  · exact div_nonneg (by exact_mod_cast (e q hq a u).1.1) hS'.le
  · unfold castZ; rw [← add_div]; exact div_le_div_of_nonneg_right (by exact_mod_cast (e q hq a u).1.2) hS'.le
  · have h3 := (e q hq a u).2
    have hc := stepZ_cast (hR k) (hA k) hD hX0 hS Δ (tabRZ Z) q a u
    rw [hg0] at hc
    have hd : (0 : ℝ) < lam.den := by exact_mod_cast lam.den_pos
    have h3' : ((lam.den : ℤ) : ℝ) * (stepZ (famZ k) D Δ X.zeroG S (tabRZ Z) q a u : ℝ) ≤
        (lam.num : ℝ) * ((tabRZ Z q a u : ℝ) * (X.M D : ℝ)) := by exact_mod_cast h3
    rw [hc, PhZ.zeroG_M] at h3'
    have hlam : (lam : ℝ) = lam.num / lam.den := by exact_mod_cast (Rat.num_div_den lam).symm
    rw [hlam, castZ, div_mul_div_comm, le_div_iff₀ (by positivity)]
    push_cast at h3'
    set st := stepR (fam k) Δ (x : ℝ) θ (fun _ _ _ => 0) (castZ S (tabRZ Z)) q a u
    have key : st * ((lam.den : ℝ) * S) * (X.M D : ℝ) ≤ (lam.num : ℝ) * (tabRZ Z q a u : ℝ) * (X.M D : ℝ) := by
      nlinarith
    exact le_of_mul_le_mul_right key hM
  · have := autoBoundZ_le (hR k) (hA k) hD hX0 hS (by rw [PhZ.zeroG_M]; exact hb)
    rwa [hg0] at this

end Index

end Cryptarchia.Prob

import Cryptarchia.Spec.Params

/-!
# Cryptarchia: the leadership lottery

`cryptarchia-proof-of-leadership.md`, *Circuit Public Inputs* (item 3),
*Circuit Constraints* (items 4–6) and *Lottery Approximation*.

For the epoch's inferred total stake `D`, every node pre-computes
`t0 = ⌊t0Const / D⌋` and `t1 = p - ⌊t1Const / D²⌋`. A note of value `v` wins slot
`sl` iff its ticket `hash(LEAD_V1 ‖ η ‖ sl ‖ noteID ‖ sk)`, an element of `𝔽_p`, is
below the threshold `v·(t0 + t1·v)` computed in `𝔽_p`. The model keeps every
operation exactly as specified: the two floor divisions, and the threshold
reduced mod `p` (which is what makes very large notes wrap around; see
*Corner Case* in the specification).

The ticket is a Poseidon2 output; the model treats Poseidon2 as a random oracle,
so a ticket is uniform on `[0, p)` and independent across distinct inputs. The
per-note win probability is then `threshold / p`.
-/

namespace Cryptarchia

variable (c : Config)

/-- `t0 = ⌊t0Const / D⌋`. -/
def t0 (D : ℕ) : ℕ := c.t0Const / D

/-- `t1 = p - ⌊t1Const / D²⌋`, i.e. `-⌊t1Const / D²⌋` in `𝔽_p`. -/
def t1 (D : ℕ) : ℕ := c.p - c.t1Const / D ^ 2

/-- The threshold `v·(t0 + t1·v)` in `𝔽_p`. -/
def threshold (D v : ℕ) : ℕ := v * (t0 c D + t1 c D * v) % c.p

/-- A ticket wins iff it is below the threshold. -/
def wins (D v ticket : ℕ) : Bool := decide (ticket < threshold c D v)

theorem threshold_lt (hp : 0 < c.p) (D v : ℕ) : threshold c D v < c.p := Nat.mod_lt _ hp

/-- **Without wrap-around.** When `v·⌊t1Const/D²⌋·v ≤ v·t0`, the field threshold
is the integer `v·t0 - v²·⌊t1Const/D²⌋`, provided that is below `p`. -/
theorem threshold_eq (D v : ℕ) (hle : v * (c.t1Const / D ^ 2) * v ≤ v * t0 c D)
    (hlt : v * t0 c D - v * (c.t1Const / D ^ 2) * v < c.p) (ht1 : c.t1Const / D ^ 2 ≤ c.p) :
    threshold c D v = v * t0 c D - v * (c.t1Const / D ^ 2) * v := by
  unfold threshold t1
  set a := c.t1Const / D ^ 2
  have : v * (t0 c D + (c.p - a) * v) = (v * t0 c D - v * a * v) + v * v * c.p := by
    have h1 : (c.p - a) * v + a * v = c.p * v := by
      rw [← Nat.add_mul, Nat.sub_add_cancel ht1]
    have h2 : v * ((c.p - a) * v) + v * a * v = v * v * c.p := by
      calc v * ((c.p - a) * v) + v * a * v = v * ((c.p - a) * v + a * v) := by ring
        _ = v * v * c.p := by rw [h1]; ring
    rw [Nat.mul_add]
    omega
  rw [this, Nat.add_mul_mod_self_right, Nat.mod_eq_of_lt hlt]

end Cryptarchia

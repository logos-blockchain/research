import Mathlib

/-!
# Cryptarchia: protocol constants

Every constant is taken from the specification (`logos-lips`,
`docs/blockchain/raw/`, at commit `2cfdf03b`):

* `cryptarchia-v1-protocol.md` rev 1.2.3, *Constants* and *Notation*;
* `cryptarchia-total-stake-inference.md` rev 1.1.0, *Parameters and variables*
  and *Algorithm*;
* `cryptarchia-proof-of-leadership.md`, *Lottery Approximation*;
* `fork-choice.md` rev 1.1.0, *Definitions*.

The model is stated for any `Config`; `Config.spec` is the specified instance.
The slot activation coefficient `f` is kept as a rational `fNum / fDen`, because
the specification uses it in three different forms, which the model keeps apart:

* exactly (`1/30`), inside the lottery constants `t0Const`, `t1Const`, which the
  specification pre-computes from `ln(1 - 1/30)` at 512-bit precision;
* as `⌊k / f⌋`, `⌊W / f⌋`, `⌊k / (4f)⌋` in the slot geometry;
* as `f_p = truncate(f · PRECISION) = 33` (so `0.033`, not `1/30`) in the total
  stake inference.
-/

namespace Cryptarchia

/-- The protocol constants. -/
structure Config where
  /-- Slot activation coefficient `f = fNum / fDen`. -/
  fNum : ℕ
  fDen : ℕ
  /-- Security parameter: block-depth finality. -/
  k : ℕ
  /-- Uncle reference window, in expected block intervals. -/
  W : ℕ
  /-- Maximum number of uncles a block may reference. -/
  maxUncles : ℕ
  /-- Fixed-point precision of the total stake inference. -/
  precision : ℕ
  /-- `truncate(beta · PRECISION)`, the learning rate in fixed point. -/
  betaP : ℕ
  /-- `truncate(f · PRECISION)`, the target activation rate in fixed point. -/
  fP : ℕ
  /-- Order of the BN254 scalar field (the range of lottery tickets). -/
  p : ℕ
  /-- `⌊-p · ln(1 - f)⌋`. -/
  t0Const : ℕ
  /-- `⌊p · ln²(1 - f) / 2⌋`. -/
  t1Const : ℕ

namespace Config

variable (c : Config)

/-- `⌊k / f⌋`. -/
def kf : ℕ := c.k * c.fDen / c.fNum

/-- Slot security parameter `s = 3⌊k/f⌋`. -/
def s : ℕ := 3 * c.kf

/-- Epoch length `10⌊k/f⌋` slots (stake snapshot `s`, buffer `s`, lottery
constants finalization `4⌊k/f⌋`). -/
def epochLength : ℕ := 10 * c.kf

/-- Total stake inference observation period `PERIOD = 6⌊k/f⌋`. -/
def period : ℕ := 6 * c.kf

/-- Offset of the epoch-nonce snapshot into an epoch: the start of the lottery
constants finalization phase, `2s = 6⌊k/f⌋`. -/
def nonceOffset : ℕ := 2 * c.s

/-- Uncle reference window in slots, `⌊W / f⌋`. -/
def uncleWindow : ℕ := c.W * c.fDen / c.fNum

/-- Density check window of the bootstrap rule, `s_gen = ⌊k / (4f)⌋`. -/
def sGen : ℕ := c.k * c.fDen / (4 * c.fNum)

/-- The epoch of a slot. -/
def epochOf (sl : ℕ) : ℕ := sl / c.epochLength

/-- The first slot of an epoch. -/
def epochStart (ep : ℕ) : ℕ := ep * c.epochLength

end Config

/-- The specified constants. -/
def Config.spec : Config where
  fNum := 1
  fDen := 30
  k := 2160
  W := 12
  maxUncles := 4
  precision := 1000
  betaP := 1000
  fP := 33
  p := 0x30644E72E131A029B85045B68181585D2833E84879B9709143E1F593F0000001
  t0Const := 0x1a3fb997fd5838f2a1585ee090a95c88129ab25cc4d2e2d28f1a95f81d85465
  t1Const := 0x71e790b4199113a9a00298d823c5716ddac764a110a45fe3b770bbb3e8a57

/-! The derived quantities, as the specification states them. -/

example : Config.spec.kf = 64800 := by decide
example : Config.spec.s = 194400 := by decide
example : Config.spec.epochLength = 648000 := by decide
example : Config.spec.period = 388800 := by decide
example : Config.spec.nonceOffset = 388800 := by decide
example : Config.spec.uncleWindow = 360 := by decide
example : Config.spec.sGen = 16200 := by decide
/-- `f_p = truncate(f · PRECISION)`: with `f = 1/30`, `⌊1000/30⌋ = 33`. -/
example : Config.spec.fP = Config.spec.precision * Config.spec.fNum / Config.spec.fDen := by decide
/-- `beta = 1.0`. -/
example : Config.spec.betaP = Config.spec.precision := rfl

end Cryptarchia

import TokenEconomics.BlockReward

/-!
# A simulator of the supply projection

Executable `Float` code, not proven, used by `TokenEconomicsTest/Projection.lean` to reproduce
the annex of Block Rewards and to compare it with the proven noise-free value
(`noiseFree_growth`). It follows the annex's assumptions:

* the stake deviation `δ = 10^{-t}` (`e^{-t/τ}`, `τ = 2/ln 100`), read once per epoch of
  21,600 blocks, plus a Gaussian noise of standard deviation `σ` per epoch;
* fees pooled at `0.5% (1 - 10^{-t})` of `S_cap` a year, with a daily log-normal noise of
  volatility `v` (mean preserving);
* the emission factor `A = clip(25 δ + p / I_max)` and the per-block growth `A (m - D)` of
  `steady_growth`, `m = 62,500/657` and `D` the pooled fee of a block, over half-days (1,440
  blocks, so that every epoch boundary falls on a step), the fees being equal within a day, the
  annex's third scenario.

Returns the net circulating growth after 10 years, in fractions of `S_cap`.
-/

namespace TokenEconomics.Simulation

/-- splitmix64. -/
def nextSeed (s : UInt64) : UInt64 := s + 0x9E3779B97F4A7C15

def mix (s : UInt64) : UInt64 :=
  let z := (s ^^^ (s >>> 30)) * 0xBF58476D1CE4E5B9
  let z := (z ^^^ (z >>> 27)) * 0x94D049BB133111EB
  z ^^^ (z >>> 31)

/-- A uniform draw in `(0, 1)` and the next seed. -/
def uniform (s : UInt64) : Float × UInt64 :=
  let s' := nextSeed s
  (((mix s') >>> 11).toFloat + 0.5) / 9007199254740992.0 |> fun u => (u, s')

/-- A standard Gaussian draw (Box–Muller) and the next seed. -/
def gaussian (s : UInt64) : Float × UInt64 :=
  let (u1, s1) := uniform s
  let (u2, s2) := uniform s1
  (Float.sqrt (-2.0 * Float.log u1) * Float.cos (2.0 * 3.141592653589793 * u2), s2)

/-- The net circulating growth after 10 years, for a stake noise `σ`, a daily fee volatility
`v` and a seed. -/
def run (σ v : Float) (seed : UInt64) : Float := Id.run do
  let m := 62500.0 / 657.0
  let blocksPerYear := 365.0 * 2880.0
  let sCap := 1.0e10
  let mut s := seed
  let mut growth := 0.0
  let mut δ := 1.0
  let mut feeNoise := 1.0
  for h in [0:7300] do
    let t := h.toFloat / 730.0
    -- a new epoch every 15 half-days: read the stake
    if h % 15 == 0 then
      let (z, s') := gaussian s
      s := s'
      δ := Float.pow 10.0 (-t) + σ * z
    -- a new day every 2 half-days: draw the fee noise
    if h % 2 == 0 then
      let (z, s') := gaussian s
      s := s'
      feeNoise := Float.exp (v * z - v * v / 2.0)
    let p := 0.005 * (1.0 - Float.pow 10.0 (-t)) * feeNoise
    let a := max 0.0 (min 1.0 (25.0 * δ + p / 0.01))
    let d := p * sCap / blocksPerYear
    growth := growth + 1440.0 * a * (m - d)
  return growth / sCap

/-- `n` runs from consecutive seeds: their mean, minimum and maximum. -/
def runs (σ v : Float) (n : Nat) : Float × Float × Float := Id.run do
  let mut sum := 0.0
  let mut lo := 1.0e9
  let mut hi := -1.0e9
  for i in [0:n] do
    let g := run σ v (UInt64.ofNat (1000 + i) * 0x2545F4914F6CDD1D)
    sum := sum + g
    lo := min lo g
    hi := max hi g
  return (sum / n.toFloat, lo, hi)

end TokenEconomics.Simulation

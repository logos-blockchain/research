module

public import Cryptarchia.Proof.Bridge
public import Cryptarchia.Proof.Trace
public import Cryptarchia.Settle.Phases
public import Cryptarchia.Settle.TreeBasic
import Cryptarchia.Proof.NodeStep
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
import Mathlib.Tactic.ENatToNat
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
import Std.Tactic.BVDecide.Normalize.Prop

/-!
# Cryptarchia settlement: the main induction

**Scope.** An execution from genesis, over any number of epochs (for parameters
laid out as the specification does, `Config.Sane`), with every honest node online throughout, running the
online rule. The theorems hold for every tip order and both readings of
`on_block`.

**Assumptions** (`Assm`), on the environment only: tip orders are permutations;
honest nodes crash-stop; honest payloads execute; honest nodes are distinct; the
config is laid out as the spec does; honest stakers never spend their notes. There
is no delivery assumption: honest blocks not delivered within Δ are `Late` and
count as adversarial.

**The good event** (`GoodLSW`; `GoodCondW` on the characteristic string of the
execution's settlement tree), for a settlement window `W t` (in slots, possibly
depending on the time `t`; constant `Lw` in `GoodLS`) and a phase decomposition `e`:
* `cold`: at every time `t > W t`, the margin bound for divergence before
  `t - W t` is cold at the start of the phase containing `t - 1`;
* `window`: the `W t` slots before `t` hold at most `k` occupied slots.
The probability layer bounds the chance that these fail.

**Result** (`main`): at every point of the execution, every honest node's local
chain is dominant: at least as high as every honest block at least `Δ + 1` slots
old. Honest blocks more than `Δ` apart have increasing heights (A2), so the
settlement tree is a valid PoS tree. The settlement theorems in
`Settlement.lean` follow.
-/

@[expose] public section

namespace Cryptarchia

open Settle

variable (E : Env) (es : List Event) (K : ℕ → Prop)

/-- The final world. -/
abbrev wF : World := wAt E es es.length

open Classical in
/-- The settlement tree of the execution, over the blocks satisfying `K` (all
blocks for `K = True`; consistent chains for the multi-epoch analysis). -/
noncomputable abbrev FT : PTree :=
  stree E.c E.L E.O E.G (wF E es).st (Late E es) ((wF E es).used.filter (fun b => decide (K b))) (wF E es).now

open Classical in
/-- Its characteristic string. -/
noncomputable abbrev WS : CStr :=
  sstr E.c E.L E.O E.G (wF E es).st (Late E es) ((wF E es).used.filter (fun b => decide (K b))) (wF E es).now

/-- **The good event on a string `w`**, up to `N`. -/
structure GoodLSW (w : CStr) (N : ℕ) (W : ℕ → ℕ) (e : ℕ → ℕ) : Prop where
  e0 : e 0 = 0
  mono : ∀ k, e k ≤ e (k + 1)
  quiet : ∀ k, e k ≤ N → Quiet E.Δ w (e k)
  unb : ∀ t, ∃ k, t ≤ e k
  cold : ∀ t k, W t < t → t ≤ N → e k + 1 ≤ t → t ≤ e (k + 1) →
    (bnd E.Δ w (t - W t) e k).2 < -(advCnt w (e k) (e (k + 1)) : ℤ)
  window : ∀ t, t ≤ N → occCnt w (t - W t) t ≤ E.c.k

/-- The good event with a constant settlement window `Lw`. -/
abbrev GoodLS (w : CStr) (N Lw : ℕ) (e : ℕ → ℕ) : Prop := GoodLSW E w N (fun _ => Lw) e

/-- The good event of the execution, up to the horizon `H` (the whole execution for
`H = now`), with a settlement window `W t` (in slots) that may depend on the time `t`. -/
abbrev GoodCondW (W : ℕ → ℕ) (e : ℕ → ℕ) (H : ℕ) : Prop := GoodLSW E (WS E es K) H W e

/-- Honest blocks up to `t` satisfy the depth axiom (A2). -/
def A2Upto (t : ℕ) : Prop :=
  ∀ u ∈ (FT E es K).V, ∀ v ∈ (FT E es K).V, honL (wF E es).st (Late E es) u = true →
    honL (wF E es).st (Late E es) v = true →
    slotOf (wF E es).st v ≤ t → slotOf (wF E es).st u + E.Δ < slotOf (wF E es).st v →
    height (wF E es).st u < height (wF E es).st v

/-- The block predicate holds for genesis and is closed under parents. -/
structure KBase : Prop where
  gen : K genesisId
  par : ∀ b, Rooted (wF E es).st b → K b → K (parentOf (wF E es).st b)

variable {E es K}

open Classical in
theorem mem_FTused {b : ℕ} : b ∈ (wF E es).used.filter (fun b => decide (K b)) ↔
    b ∈ (wF E es).used ∧ K b := by
  rw [List.mem_filter, decide_eq_true_iff]

open Classical in
/-- The block set of the tree contains genesis and is closed under parents of
good blocks. -/
theorem FTused_ok (hA : Assm E) (hK : KBase E es K) :
    genesisId ∈ (wF E es).used.filter (fun b => decide (K b)) ∧
      ∀ b ∈ (wF E es).used.filter (fun b => decide (K b)),
        GoodAt E.c E.L E.O E.G (wF E es).st (wF E es).now b →
          parentOf (wF E es).st b ∈ (wF E es).used.filter (fun b => decide (K b)) := by
  classical
  have hw := wAt_ok (es := es) hA es.length
  refine ⟨mem_FTused.2 ⟨(hw.used _).1 hw.store.rooted_gen.exists_blk, hK.gen⟩, ?_⟩
  intro b hb hg
  rw [mem_FTused] at hb ⊢
  have hp := hg.parent hw.store
  exact ⟨(hw.used _).1 hp.1.exists_blk, hK.par b hg.1 hb.2⟩

theorem restrict_hd {F : PTree} {t m : ℕ} (hm : m ≤ t) : (F.restrict t).hd m = F.hd m := by
  classical
  unfold PTree.hd
  congr 1
  ext v
  simp only [Finset.mem_filter, mem_restrict]
  constructor
  · rintro ⟨⟨h1, -⟩, h2⟩; exact ⟨h1, h2⟩
  · rintro ⟨h1, h2, h3⟩; exact ⟨⟨h1, show F.lab v ≤ t by
      exact le_trans h3 hm⟩, h2, h3⟩

/-- The phase containing `t - 1`. -/
theorem phase_of {e : ℕ → ℕ} (he0 : e 0 = 0) (hunb : ∀ t, ∃ k, t ≤ e k)
    {t : ℕ} (ht : 1 ≤ t) : ∃ k, e k + 1 ≤ t ∧ t ≤ e (k + 1) := by
  classical
  have hex : ∃ k, t ≤ e k := hunb t
  let k₀ := Nat.find hex
  have hk₀ : t ≤ e k₀ := Nat.find_spec hex
  have hk₀0 : k₀ ≠ 0 := by
    intro h; have := hk₀; rw [h, he0] at this; omega
  obtain ⟨k, hk⟩ : ∃ k, k₀ = k + 1 := ⟨k₀ - 1, by omega⟩
  refine ⟨k, ?_, by rw [← hk]; exact hk₀⟩
  have := Nat.find_min hex (show k < k₀ by omega)
  omega

open Classical in
/-- **Near.** At any time `t` of the execution, two blocks of the settlement tree
with slots up to `t`, at least as high as the honest depth at the start of the
phase, meet within `k` blocks below the first. -/
theorem nearAt (hA : Assm E) (hK : KBase E es K) {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ} (hG : GoodCondW E es K W e H) {t : ℕ}
    (htH : t ≤ H) (hA2 : A2Upto E es K t) {k : ℕ}
    (hk : e k + 1 ≤ t ∧ t ≤ e (k + 1)) {u v : ℕ} (hu : u ∈ (FT E es K).V) (hv : v ∈ (FT E es K).V)
    (hsu : slotOf (wF E es).st u ≤ t) (hsv : slotOf (wF E es).st v ≤ t)
    (hdu : (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st u)
    (hdv : (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st v) :
    ∃ x, x ∈ chainIds (wF E es).st u ∧ x ∈ chainIds (wF E es).st v ∧
      height (wF E es).st u - height (wF E es).st x ≤ E.c.k := by
  have hw := wAt_ok (es := es) hA es.length
  have hS := hw.store
  have hFt := tree_valid_upto (c := E.c) (L := E.L) (O := E.O) (G := E.G) hS E.Δ t
    (FTused_ok hA hK).1 (FTused_ok hA hK).2 hA2
  set Ft := (FT E es K).restrict t
  have hur : Rooted (wF E es).st u := (mem_stree.1 hu).2.1
  have hvr : Rooted (wF E es).st v := (mem_stree.1 hv).2.1
  have hu' : u ∈ Ft.V := mem_restrict.2 ⟨hu, hsu⟩
  have hv' : v ∈ Ft.V := mem_restrict.2 ⟨hv, hsv⟩
  -- the depth of a segment ending at `u` above `x`, from the window condition
  have hdepth : ∀ x, Ft.Anc x u → t - W t ≤ slotOf (wF E es).st x →
      height (wF E es).st u - height (wF E es).st x ≤ E.c.k := by
    intro x hx hxl
    have := hFt.seg_le_occ _ x u hu' hx rfl
    have hw' := hG.window t htH
    have hm : occCnt (WS E es K) (Ft.lab x) (Ft.lab u) ≤ occCnt (WS E es K) (t - W t) t :=
      occCnt_mono hxl hsu
    exact le_trans this (le_trans hm hw')
  have hancu : ∀ x, Ft.Anc x u ↔ x ∈ chainIds (wF E es).st u := fun x =>
    anc_iff (c := E.c) (L := E.L) (O := E.O) (G := E.G)
      (late := Late E es) (used := (wF E es).used.filter (fun b => decide (K b))) (N := (wF E es).now) hS hur
  have hancv : ∀ x, Ft.Anc x v ↔ x ∈ chainIds (wF E es).st v := fun x =>
    anc_iff (c := E.c) (L := E.L) (O := E.O) (G := E.G)
      (late := Late E es) (used := (wF E es).used.filter (fun b => decide (K b))) (N := (wF E es).now) hS hvr
  by_cases hLt : t ≤ W t
  · refine ⟨genesisId, genesis_mem_chainIds hS hur, genesis_mem_chainIds hS hvr, ?_⟩
    apply hdepth
    · exact (hancu _).2 (genesis_mem_chainIds hS hur)
    · rw [slotOf_genesis hS]; omega
  · push Not at hLt
    have hhd : Ft.hd (e k - E.Δ) = (FT E es K).hd (e k - E.Δ) := restrict_hd (by omega)
    have hsim := PTree.Valid.settled hFt (t - W t) e hG.e0 hG.mono (fun k hk => hG.quiet k (le_trans hk htH)) k t
      (by omega) hk.2 le_rfl (hG.cold t k hLt htH hk.1 hk.2) hu' hv' hsu hsv (by rw [hhd]; exact hdu) (by rw [hhd]; exact hdv)
    obtain ⟨x, hx, hxu, hxv, hxl⟩ := hsim
    refine ⟨x, (hancu x).1 hxu, (hancv x).1 hxv, hdepth x hxu hxl⟩

/-! ## Honest depth in the settlement tree -/

theorem FT_le_hd {v m : ℕ} (hv : v ∈ (FT E es K).V) (hh : honL (wF E es).st (Late E es) v = true)
    (hl : slotOf (wF E es).st v ≤ m) : height (wF E es).st v ≤ (FT E es K).hd m := by
  classical
  unfold PTree.hd
  exact Finset.le_sup (f := (FT E es K).dep) (Finset.mem_filter.2 ⟨hv, hh, hl⟩)

theorem FT_hd_exists (hA : Assm E) (hK : KBase E es K) (m : ℕ) :
    ∃ v ∈ (FT E es K).V, honL (wF E es).st (Late E es) v = true ∧ slotOf (wF E es).st v ≤ m ∧
      height (wF E es).st v = (FT E es K).hd m := by
  classical
  have hw := wAt_ok (es := es) hA es.length
  have hS := hw.store
  have hg : genesisId ∈ (FT E es K).V := mem_stree.2 ⟨(FTused_ok hA hK).1, good_genesis hS _⟩
  have hne : ((FT E es K).V.filter (fun v => (FT E es K).hon v = true ∧ (FT E es K).lab v ≤ m)).Nonempty :=
    ⟨genesisId, Finset.mem_filter.2 ⟨hg, honL_genesis (st := (wF E es).st) (late := Late E es), by
      show slotOf (wF E es).st genesisId ≤ m; rw [slotOf_genesis hS]; omega⟩⟩
  obtain ⟨v, hv, he⟩ := Finset.exists_mem_eq_sup _ hne (FT E es K).dep
  rw [Finset.mem_filter] at hv
  exact ⟨v, hv.1, hv.2.1, hv.2.2, he.symm⟩

theorem FT_hd_mono {m m' : ℕ} (h : m ≤ m') : (FT E es K).hd m ≤ (FT E es K).hd m' := by
  classical
  unfold PTree.hd
  apply Finset.sup_mono
  intro v hv
  rw [Finset.mem_filter] at hv ⊢
  exact ⟨hv.1, hv.2.1, le_trans hv.2.2 h⟩

/-- Honest blocks of the tree other than genesis are stored honest-signed blocks. -/
theorem honB_signed {st : Store} {v : ℕ} (hh : honB st v = true) (hv0 : v ≠ genesisId)
    (hvs : ∃ B, st v = some B) : ∃ B, st v = some B ∧ IsHon B := by
  obtain ⟨B, hB⟩ := hvs
  refine ⟨B, hB, ?_⟩
  unfold honB at hh
  rw [hB] at hh
  simp only [Bool.or_eq_true, decide_eq_true_eq, hv0, false_or] at hh
  split at hh
  · rename_i j hj; exact ⟨j, hj⟩
  · simp at hh

/-! ## The invariant -/

/-- Every honest node's local chain is at least as high as the tree's honest depth
at `m`. -/
def DomAt (n m : ℕ) : Prop :=
  ∀ i ∈ E.nodes, E.online i (wAt E es n).now = true →
    (FT E es K).hd m ≤ height (wF E es).st ((wAt E es n).node i).cloc

/-- Every stored honest block extends a chain at least as high as the honest
depth `Δ + 1` slots before it. -/
def HonAt (n : ℕ) : Prop :=
  ∀ b B, (wAt E es n).st b = some B → IsHon B →
    (FT E es K).hd (B.hdr.slot - E.Δ - 1) ≤ height (wF E es).st B.hdr.parent

/-- **The invariant at index `n`**: `DomAt` with the honest depth `Δ + 1` slots
back, and `HonAt`. -/
abbrev InvAt (E : Env) (es : List Event) (K : ℕ → Prop) (n : ℕ) : Prop :=
  DomAt (E := E) (es := es) (K := K) n ((wAt E es n).now - E.Δ - 1) ∧ HonAt (E := E) (es := es) (K := K) n

/-- The obligations on the block predicate: genesis, closure under parents, and,
given the invariant before index `n`, every chain through a node's immutable block
at `n` satisfies it. -/
structure KOK (E : Env) (es : List Event) (K : ℕ → Prop) (H : ℕ) : Prop extends KBase E es K where
  step : ∀ n ≤ es.length, (wAt E es n).now ≤ H → (∀ m < n, InvAt E es K m) →
    ∀ i ∈ E.nodes, E.online i (wAt E es n).now = true →
      ∀ cl, Rooted (wAt E es n).st cl → slotOf (wAt E es n).st cl ≤ (wAt E es n).now →
      ((wAt E es n).node i).bimm ∈ chainIds (wAt E es n).st cl → K cl

/-- **A2 from the parent bound.** -/
theorem A2_of_Hon (hA : Assm E) {n : ℕ} (hn : n ≤ es.length) (hH : HonAt (E := E) (es := es) (K := K) n) :
    A2Upto E es K (wAt E es n).now := by
  intro u hu v hv huh hvh hvn huv
  have hw := wAt_ok (es := es) hA es.length
  have hS := hw.store
  have hvr := (mem_stree.1 hv).2.1
  have hv0 : v ≠ genesisId := by
    intro h; subst h; rw [slotOf_genesis hS] at huv; omega
  obtain ⟨B, hB, hBh⟩ := honB_signed (honB_of_honL hvh) hv0 hvr.exists_blk
  -- `v` is already stored at `n`
  have hvn' := (wAt_le (es := es) hA hn).old hB hBh (by rw [slotOf_eq hB] at hvn; exact hvn)
  have hpar := hH v B hvn' hBh
  obtain ⟨blk, hbk, hpr, hsl⟩ := hvr.inv hv0
  have hBb : B = blk := by rw [hbk] at hB; exact (Option.some_inj.1 hB).symm
  rw [hBb] at hpar
  have hht := height_step hbk hv0 hpr hsl
  have hu' := FT_le_hd (E := E) (es := es) hu huh (m := blk.hdr.slot - E.Δ - 1) (by
    rw [slotOf_eq hbk] at huv; omega)
  omega

/-- A block good in a store the final one extends, not after the horizon, is in
the settlement tree. -/
theorem goodAt_FT (hA : Assm E) {st : Store} (hS : StoreOK st) (hext : StoreExt st (wF E es).st)
    {t cl : ℕ} (htN : t ≤ (wF E es).now) (hg : GoodAt E.c E.L E.O E.G st t cl) (hKc : K cl) :
    cl ∈ (FT E es K).V := by
  have hw := wAt_ok (es := es) hA es.length
  have hg' := hg.mono hS hext htN
  exact mem_stree.2 ⟨mem_FTused.2 ⟨(hw.used cl).1 hg'.1.exists_blk, hKc⟩, hg'⟩

/-- **The settlement input for Claims A and B**, at time `t` of the execution. -/
theorem near_now (hA : Assm E) (hK : KBase E es K) {W : ℕ → ℕ} {e : ℕ → ℕ} {H : ℕ} (hG : GoodCondW E es K W e H) {t : ℕ}
    (ht1 : 1 ≤ t) (htN : t ≤ (wF E es).now) (htH : t ≤ H) (hA2 : A2Upto E es K t)
    {st : Store} (hS : StoreOK st) (hext : StoreExt st (wF E es).st) {H0 h : ℕ}
    (hH0 : (FT E es K).hd (t - E.Δ - 1) ≤ H0) (hhr : Rooted st h) (hhF : h ∈ (FT E es K).V)
    (hsh : slotOf st h ≤ t) (hdh : ∀ k, e k + 1 ≤ t → (FT E es K).hd (e k - E.Δ) ≤ height st h) {z : ℕ}
    (hKc : ∀ cl, GoodAt E.c E.L E.O E.G st t cl → z ∈ chainIds st cl → K cl) :
    Near E.c E.L E.O E.G st t H0 h z := by
  intro cl hg hcl hz
  have hclF := goodAt_FT hA hS hext htN hg (hKc cl hg hz)
  obtain ⟨k, hk1, hk2⟩ := phase_of hG.e0 hG.unb ht1
  have hclr := hg.1
  have e1 : height (wF E es).st cl = height st cl := height_ext hext hclr
  have e2 : height (wF E es).st h = height st h := height_ext hext hhr
  have hdcl : (FT E es K).hd (e k - E.Δ) ≤ height (wF E es).st cl := by
    rw [e1]; exact le_trans (FT_hd_mono (by omega)) (le_trans hH0 hcl)
  obtain ⟨x, hx1, hx2, hx3⟩ := nearAt hA hK hG htH hA2 ⟨hk1, hk2⟩ hclF hhF
    (by rw [slotOf_ext hext hclr.exists_blk]; exact hg.2.1)
    (by rw [slotOf_ext hext hhr.exists_blk]; exact hsh) hdcl (by rw [e2]; exact hdh k hk1)
  rw [chainIds_ext hext hclr] at hx1
  rw [chainIds_ext hext hhr] at hx2
  have hxr := (anc_height hS hclr hx1).1
  refine ⟨x, hx1, hx2, ?_⟩
  rw [← e1, ← height_ext hext hxr]; exact hx3

/-- Heights at a point of the execution are heights in the final store. -/
theorem height_wF (hA : Assm E) {m x : ℕ} (hm : m ≤ es.length) (hx : Rooted (wAt E es m).st x) :
    height (wF E es).st x = height (wAt E es m).st x := height_ext (store_mono hA hm) hx

/-- A node's local chain never loses height, in the final store. -/
theorem cloc_mono (hA : Assm E) {n m : ℕ} (hnm : n ≤ m) (hm : m ≤ es.length) (i : ℕ) :
    height (wF E es).st ((wAt E es n).node i).cloc ≤ height (wF E es).st ((wAt E es m).node i).cloc := by
  rw [height_wF hA (hnm.trans hm) ((wAt_ok hA n).nodes i).cloc_rooted,
    height_wF hA hm ((wAt_ok hA m).nodes i).cloc_rooted]
  exact (wAt_le hA hnm).mono i

theorem genesis_not_hon (hA : Assm E) {n : ℕ} {B : Block}
    (hB : (wAt E es n).st genesisId = some B) : ¬ IsHon B := by
  rw [store_genesis hA n] at hB; cases hB
  rintro ⟨j, hj⟩; simp [genesisBlock] at hj

/-- An honest block stored at some point is rooted there, with a slot of at least
one and at most the current time. -/
theorem hon_stored (hA : Assm E) {m h : ℕ} {B : Block}
    (hB : (wAt E es m).st h = some B) (hBh : IsHon B) :
    GoodAt E.c E.L E.O E.G (wAt E es m).st (wAt E es m).now h ∧ 1 ≤ slotOf (wAt E es m).st h ∧
      h ≠ genesisId := by
  have hg := (wAt_ok (es := es) hA m).good hB hBh
  have h0 : h ≠ genesisId := by
    intro h0; subst h0; exact genesis_not_hon hA hB hBh
  refine ⟨hg, ?_, h0⟩
  obtain ⟨blk, hbk, -, hsl⟩ := hg.1.inv h0
  rw [slotOf_eq hbk]; omega

/-- **Claim C.** When honest node `i` receives an honest block `h` within `Δ`
of its slot, and `h` is at least as high as the honest depth `Δ + 1` slots
before the delivery, `i`'s local chain afterwards is at least as high as `h`. -/
theorem claimC (hA : Assm E) {Hh : ℕ} (hK : KOK E es K Hh) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e Hh) {d : ℕ}
    (hd : d < es.length) (hdH : (wAt E es d).now ≤ Hh) {i h : ℕ} (hev : es[d] = .deliver i h) (hi : i ∈ E.nodes)
    (hion : E.online i (wAt E es d).now = true)
    (hhF : h ∈ (FT E es K).V) {H : Block} (hH : (wF E es).st h = some H) (hHh : IsHon H)
    (hs1 : slotOf (wF E es).st h ≤ (wAt E es d).now)
    (hht : (FT E es K).hd ((wAt E es d).now - 1 - E.Δ) ≤ height (wF E es).st h)
    (hIH : ∀ m ≤ d, InvAt E es K m) :
    height (wF E es).st h ≤ height (wF E es).st ((wAt E es (d + 1)).node i).cloc := by
  have hextF : ∀ m, m ≤ es.length → StoreExt (wAt E es m).st (wF E es).st :=
    fun m hm => store_mono hA hm
  -- the settlement input at any time `m ≤ d` at which `h` is stored
  have hnear_m : ∀ m, m ≤ d → ∀ (Bm : Block), (wAt E es m).st h = some Bm →
      Near E.c E.L E.O E.G (wAt E es m).st (wAt E es m).now
        (height (wAt E es m).st ((wAt E es m).node i).cloc) h ((wAt E es m).node i).bimm := by
    intro m hmd Bm hBm
    have hwm := wAt_ok (es := es) hA m
    have hBmh : IsHon Bm := by
      have := hextF m (by omega) h Bm hBm; rw [hH] at this
      rw [← Option.some_inj.1 this]; exact hHh
    obtain ⟨hg, hs1', -⟩ := hon_stored hA hBm hBmh
    have hnd := now_mono (E := E) (es := es) hmd (by omega)
    have honm : E.online i (wAt E es m).now = true := hA.crash i _ _ hnd hion
    have hDom := (hIH m hmd).1 i hi honm
    have hHon := (hIH m hmd).2
    have hH0 : (FT E es K).hd ((wAt E es m).now - E.Δ - 1) ≤
        height (wAt E es m).st ((wAt E es m).node i).cloc := by
      rw [← height_wF hA (by omega) (hwm.nodes i).cloc_rooted]; exact hDom
    have hdh : ∀ k, e k + 1 ≤ (wAt E es m).now →
        (FT E es K).hd (e k - E.Δ) ≤ height (wAt E es m).st h := by
      intro k hk
      rw [← height_wF hA (by omega) hg.1]
      refine le_trans (FT_hd_mono ?_) hht
      omega
    exact near_now hA hK.toKBase hG (by have := hg.2.1; omega) (now_mono (by omega) le_rfl)
      (le_trans (now_mono (E := E) (es := es) hmd (by omega)) hdH) (A2_of_Hon hA (by omega) hHon) hwm.store (hextF m (by omega)) hH0 hg.1 hhF hg.2.1 hdh
      (fun cl hcl hz => hK.step m (by omega) (le_trans (now_mono (E := E) (es := es) hmd (by omega)) hdH)
        (fun m' hm' => hIH m' (by omega)) i hi honm cl hcl.1 hcl.2.1 hz)
  -- `Q m`: once `h` is in `i`'s tree, `i`'s local chain is at least as high
  have hQ : ∀ m, m ≤ d + 1 → h ∈ ((wAt E es m).node i).tree →
      height (wF E es).st h ≤ height (wF E es).st ((wAt E es m).node i).cloc := by
    intro m
    induction m with
    | zero =>
      intro _ hin
      rw [wAt_zero] at hin; simp [World.init] at hin; subst hin
      exact absurd hHh (genesis_not_hon hA hH)
    | succ m ih =>
      intro hm hin
      have hml : m < es.length := by omega
      have hwm := wAt_ok (es := es) hA m
      by_cases hold : h ∈ ((wAt E es m).node i).tree
      · exact le_trans (ih (by omega) hold) (cloc_mono hA (Nat.le_succ m) (by omega) i)
      have hw1 := wAt_ok (es := es) hA (m + 1)
      rw [height_wF hA (by omega) ((hw1.nodes i).rooted h hin),
        height_wF hA (by omega) (hw1.nodes i).cloc_rooted]
      rw [wAt_succ E es hml] at hin ⊢
      rcases step_node (E := E) (wAt E es m) es[m] i with hev' | hsame | ⟨b, hst, hrec⟩
      · rw [hev'] at hin ⊢; exact tick_tree hA hwm i h hin hold
      · rw [hsame] at hin; exact absurd hin hold
      · rw [hrec] at hin; rw [hst, hrec]
        obtain ⟨Bm, hBm⟩ := ((receive_step hwm.store (hwm.nodes i) E.fastPath (E.ord i) (hA.ord i)
          (wAt E es m).now b).ok.rooted h hin).exists_blk
        exact fold_adds hwm.store (hnear_m m (by omega) Bm hBm) E.fastPath (E.ord i) (hA.ord i)
          (chainUp (wAt E es m).st b) (fun x hx => mem_chainUp hwm.store hx)
          ((wAt E es m).node i) (hwm.foldInv i) hold hin
  -- at the delivery itself, `h` is accepted
  apply hQ (d + 1) le_rfl
  have hwd := wAt_ok (es := es) hA d
  -- `h` is stored at `d`: its slot is not after the delivery
  have hBd := (wAt_le (es := es) hA (show d ≤ es.length by omega)).old hH hHh
    (by rw [slotOf_eq hH] at hs1; exact hs1)
  obtain ⟨hg, -, -⟩ := hon_stored hA hBd hHh
  have hB := claimB hwd.store hg.1 hg.2.2 hg.2.1 (hnear_m d le_rfl H hBd) E.fastPath (E.ord i)
    (hA.ord i) hg.1 (self_mem_chainIds hwd.store hg.1) (hwd.foldInv i)
  rw [wAt_succ E es hd, hev]
  simp only [World.step]
  rw [if_pos (by simp [hion]; exact hi)]
  simp only [if_true]
  exact hB.1 h (self_mem_chainIds hwd.store hg.1)

/-- **Dominance at a tick.** Just before the honest leaders of the new slot
propose, every honest node's local chain is at least as high as every honest
block `Δ + 1` slots older than the new slot. -/
theorem tickD (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H) {n : ℕ}
    (hn : n < es.length) (hnH : (wAt E es n).now ≤ H) (htick : es[n] = .tick)
    (hIH : ∀ m < n, InvAt E es K m) :
    DomAt (E := E) (es := es) (K := K) n ((wAt E es n).now + 1 - E.Δ - 1) := by
  intro i hi hon
  have hwF := wAt_ok (es := es) hA es.length
  have hS := hwF.store
  obtain ⟨v, hv, hvh, hvl, hve⟩ := FT_hd_exists hA hK.toKBase ((wAt E es n).now + 1 - E.Δ - 1)
  rw [← hve]
  by_cases hv0 : v = genesisId
  · subst hv0; rw [height_genesis hS]; exact Nat.zero_le _
  obtain ⟨V, hV, hVh⟩ := honB_signed (honB_of_honL hvh) hv0 (mem_stree.1 hv).2.1.exists_blk
  have hv1 : 1 ≤ slotOf (wF E es).st v := by
    obtain ⟨blk, hbk, -, hs⟩ := (mem_stree.1 hv).2.1.inv hv0
    rw [slotOf_eq hbk]; omega
  have hnow1 : (wAt E es (n + 1)).now = (wAt E es n).now + 1 := by
    rw [wAt_succ E es hn, step_now, htick]
  have hNF := now_mono (E := E) (es := es) (m := es.length) (n := n + 1) hn le_rfl
  -- the Δ-delivery of `v` to `i`
  have hlog := (hwF.hon v V _ hV hVh.choose_spec).log
  have hsl : slotOf (wF E es).st v = V.hdr.slot := slotOf_eq hV
  -- `v` is timely: honest vertices of the tree are the honest blocks not late
  have hdel : Delivered E es v := not_not.mp (not_late_of_honL hvh hv0)
  unfold Delivered at hdel
  simp only at hdel
  rw [← wAt_length] at hdel
  obtain ⟨d, hd, hdev, hd1, hd2⟩ := hdel V.hdr.slot hlog (by
      rw [← hsl]; rw [wAt_length] at hNF ⊢; omega) i hi
    (fun t _ ht => hA.crash i t _ (by rw [hsl] at hvl; omega) hon)
  rw [trace_getElem E es World.init d hd.le] at hd1 hd2
  simp only [Option.map_some, Option.getD_some] at hd1 hd2
  change V.hdr.slot ≤ (wAt E es d).now at hd1
  change (wAt E es d).now ≤ V.hdr.slot + E.Δ at hd2
  have hdev' : es[d] = .deliver i v := by
    generalize hx : es[d] = ev at hdev
    cases ev with
    | deliver j b' => obtain ⟨rfl, rfl⟩ := hdev; rfl
    | tick => exact absurd hdev id
    | create B => exact absurd hdev id
  -- the delivery came before the tick
  have hdn : d < n := by
    by_contra hge
    push Not at hge
    rcases Nat.eq_or_lt_of_le hge with h | h
    · subst h; rw [htick] at hdev'; cases hdev'
    · have := now_mono (E := E) (es := es) (show n + 1 ≤ d by omega) hd.le
      rw [hsl] at hvl; omega
  have hC := claimC hA hK hG hd (le_trans (now_mono (E := E) (es := es) hdn.le hn.le) hnH) hdev' hi
    (hA.crash i _ _ (now_mono (E := E) (es := es) hdn.le hn.le) hon) hv hV hVh (by rw [hsl]; exact hd1)
    (by rw [hve]; exact FT_hd_mono (by
      have := now_mono (E := E) (es := es) hdn.le hn.le; omega))
    (fun m hm => hIH m (by omega))
  exact le_trans hC (cloc_mono hA (show d + 1 ≤ n by omega) hn.le i)

/-- **The main invariant.** Throughout the execution, every honest node's local
chain is at least as high as every honest block `Δ + 1` slots old, and every
honest block extends such a chain. -/
theorem main (hA : Assm E) {H : ℕ} (hK : KOK E es K H) {W : ℕ → ℕ} {e : ℕ → ℕ} (hG : GoodCondW E es K W e H) :
    ∀ n ≤ es.length, (wAt E es n).now ≤ H → InvAt E es K n := by
  have hwF := wAt_ok (es := es) hA es.length
  have hS := hwF.store
  intro n
  induction n using Nat.strong_induction_on with
  | _ n ih =>
    intro hn hnH
    rcases n with _ | n
    · -- the initial world: every chain is genesis, no honest block
      refine ⟨?_, ?_⟩
      · intro i hi _
        obtain ⟨v, hv, -, hvl, hve⟩ := FT_hd_exists hA hK.toKBase ((wAt E es 0).now - E.Δ - 1)
        rw [← hve]
        rw [wAt_zero] at hvl ⊢
        simp only [World.init, Nat.zero_sub] at hvl ⊢
        have : v = genesisId := by
          by_contra h0
          obtain ⟨blk, hbk, -, hs⟩ := (mem_stree.1 hv).2.1.inv h0
          rw [slotOf_eq hbk] at hvl; omega
        subst this; rw [height_genesis hS]
      · intro b B hb hBh
        rw [wAt_zero] at hb
        simp only [World.init] at hb
        split at hb
        · cases hb; obtain ⟨j, hj⟩ := hBh; simp [genesisBlock] at hj
        · simp at hb
    · have hnl : n < es.length := by omega
      have hIH : ∀ m < n + 1, InvAt E es K m := fun m hm =>
        ih m hm (by omega) (le_trans (now_mono (E := E) (es := es) (show m ≤ n + 1 by omega) hn) hnH)
      have hstep := wAt_succ E es hnl
      have h1 := wAt_le (es := es) hA (Nat.le_succ n)
      have hnow : (wAt E es (n + 1)).now =
          (wAt E es n).now + (match es[n] with | .tick => 1 | _ => 0) := by rw [hstep]; exact step_now _ _
      -- dominance at the new time, by the local chains before the event
      have hD : ∀ i ∈ E.nodes, E.online i (wAt E es (n + 1)).now = true →
          (FT E es K).hd ((wAt E es (n + 1)).now - E.Δ - 1) ≤
            height (wF E es).st ((wAt E es n).node i).cloc := by
        intro i hi hon
        cases hev : es[n] with
        | tick =>
          rw [hev] at hnow; rw [hnow] at hon ⊢
          exact tickD hA hK hG hnl (le_trans (now_mono (Nat.le_succ n) hn) hnH) hev
            (fun m hm => hIH m (by omega)) i hi (hA.crash i _ _ (Nat.le_succ _) hon)
        | deliver j b | create C =>
          rw [hev] at hnow; simp only [Nat.add_zero] at hnow; rw [hnow] at hon ⊢
          exact (hIH n (by omega)).1 i hi hon
      refine ⟨fun i hi hon => le_trans (hD i hi hon) (cloc_mono hA (Nat.le_succ n) hn i), ?_⟩
      intro b B hb hBh
      by_cases hold : (wAt E es n).st b = none
      · -- a block created by the event: by a tick, on a node's local chain
        obtain ⟨hev, j, hj, hpar, hsl, hjon⟩ := new_hon hA hnl hb hold hBh
        rw [hev] at hnow
        rw [hpar, hsl, ← hnow]
        exact hD j hj (by rw [hnow]; exact hjon)
      · obtain ⟨B', hB'⟩ := Option.ne_none_iff_exists'.1 hold
        obtain rfl : B' = B := Option.some_inj.1 ((h1.ext b B' hB').symm.trans hb)
        exact (hIH n (by omega)).2 b B' hB' hBh

end Cryptarchia

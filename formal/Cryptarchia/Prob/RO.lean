module

public import Cryptarchia.Prob.Worst
public import Cryptarchia.Prob.Final
public import Cryptarchia.Prob.Tail2
public import Mathlib.Order.CompletePartialOrder
public import Mathlib.Probability.Independence.Basic
import Std.Tactic.BVDecide.Normalize.BitVec
import Std.Tactic.BVDecide.Normalize.Prop
import Mathlib.Algebra.Order.Floor.Extended
import Mathlib.Algebra.Order.Interval.Basic
import Mathlib.Algebra.Order.Star.Real
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
import Mathlib.Probability.Independence.Integration
import Mathlib.RingTheory.Radical.NatInt
import Mathlib.RingTheory.WittVector.IsPoly
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
import Mathlib.Tactic.ReduceModChar
import Mathlib.Topology.Sheaves.Init

/-!
# The lottery law from a random oracle

The probabilistic bounds need the law of the lottery string. This file derives each
slot's law from a random-oracle model of the note lottery.

**The model.** The oracle is random: `O ω`. The ticket of note `id` at slot `i`
under nonce `η` is `(O ω).ticket η i id`. Slot `i`'s **ticket table**
`tk O i ω = fun η id => (O ω).ticket η i id` holds all of them.

* `RandomOracle`: within one table and one nonce, the tickets of distinct notes
  are independent and uniform on `[0, p)`.
* `Fresh`, the no-grinding idealization: slot `i`'s table is independent of the
  earlier tables and of the epoch states of slots up to `i`. The state a slot's
  lottery runs under, including its nonce, is fixed before anything about that
  slot's tickets is known.

Under Δ-delivery, slot `i` of the lottery string is a function of the slot's epoch
state and its ticket table (`slotOut`, `enc_lotStr`). Given the past, its law is the
state's slot law (`freeze`). A random oracle makes that law the product of an
honest part and an adversarial part with explicit probabilities (`slot_law`).
-/

@[expose] public section

namespace Cryptarchia.Prob

open MeasureTheory ProbabilityTheory Finset Settle
open scoped ENNReal

instance : Countable Signer := by
  refine Function.Injective.countable (f := fun s : Signer => match s with | .honest i => some i | .adv => none) ?_
  intro a b h; cases a <;> cases b <;> simp_all

instance : Countable Note :=
  Function.Injective.countable (f := fun n : Note => (n.id, n.value, n.owner))
    (fun a b h => by cases a; cases b; simp_all)

instance : Countable EpochState :=
  Function.Injective.countable (f := fun s : EpochState => (s.lead, s.eta, s.D))
    (fun a b h => by cases a; cases b; simp_all)

instance : MeasurableSpace EpochState := ⊤

instance : MeasurableSingletonClass EpochState := ⟨fun _ => trivial⟩

/-! ## The slot outcome as a function of the state and the tickets -/

/-- A ticket table: `T η id`. -/
abbrev Tab := ℕ → ℕ → ℕ

/-- Honest node `j` holds a winning note under `s` with tickets `T`. -/
def honW (c : Config) (s : EpochState) (T : Tab) (j : ℕ) : Bool :=
  s.lead.any (fun n => decide (n.owner = .honest j) && wins c s.D n.value (T s.eta n.id))

/-- The adversary holds a winning note under `s` with tickets `T`. -/
def advW (c : Config) (s : EpochState) (T : Tab) : Bool :=
  s.lead.any (fun n => decide (n.owner = .adv) && wins c s.D n.value (T s.eta n.id))

/-- The number of online honest nodes that win slot `i`. -/
def honCount (E : Env) (i : ℕ) (s : EpochState) (T : Tab) : ℕ :=
  (E.nodes.filter (fun j => E.online j i && honW E.c s T j)).length

/-- **Slot `i`'s outcome** under state `s` with tickets `T`. -/
def slotOut (E : Env) (i : ℕ) (s : EpochState) (T : Tab) : Out :=
  enc (honCount E i s T, advW E.c s T)

/-- Slot `i`'s ticket table. -/
def tk {Ω : Type*} (O : Ω → Oracle) (i : ℕ) (ω : Ω) : Tab := fun η id => (O ω).ticket η i id

/-- Under Δ-delivery, the lottery string is the slot outcomes. -/
theorem enc_lotStr {E : Env} {O : Oracle} {es : List Event} (hD : DeltaDelivery (E.withO O) es) (i : ℕ) :
    enc (lotStr (E.withO O) es i) = slotOut E i (σE (E.withO O) es i) (fun η id => O.ticket η i id) := by
  rw [lotStr, lotStrS_of_delivery hD]
  rfl

/-! ## Measurability -/

theorem measurable_listAny {α ι : Type*} [MeasurableSpace α] (L : List ι) {f : ι → α → Bool}
    (hf : ∀ i, Measurable (f i)) : Measurable fun a => L.any (fun i => f i a) := by
  induction L with
  | nil => simp only [List.any_nil]; exact measurable_const
  | cons i L ih =>
    simp only [List.any_cons]
    exact (measurable_of_countable (fun p : Bool × Bool => p.1 || p.2)).comp ((hf i).prodMk ih)

theorem measurable_filterLength {α ι : Type*} [MeasurableSpace α] (L : List ι) {f : ι → α → Bool}
    (hf : ∀ i, Measurable (f i)) : Measurable fun a => (L.filter (fun i => f i a)).length := by
  induction L with
  | nil => simp only [List.filter_nil, List.length_nil]; exact measurable_const
  | cons i L ih =>
    have e : (fun a => ((i :: L).filter (fun i => f i a)).length) =
        (fun p : Bool × ℕ => (if p.1 then 1 else 0) + p.2) ∘ (fun a => (f i a, (L.filter (fun i => f i a)).length)) := by
      funext a; simp only [List.filter_cons, Function.comp]; split_ifs <;> simp [add_comm]
    rw [e]
    exact (measurable_of_countable _).comp ((hf i).prodMk ih)

theorem measurable_ticket (η id : ℕ) : Measurable fun T : Tab => T η id :=
  (measurable_pi_apply id).comp (measurable_pi_apply η)

theorem measurable_win (c : Config) (s : EpochState) (P : Note → Bool) :
    Measurable fun T : Tab => s.lead.any (fun n => P n && wins c s.D n.value (T s.eta n.id)) :=
  measurable_listAny _ fun n =>
    (measurable_of_countable fun t : ℕ => P n && wins c s.D n.value t).comp (measurable_ticket s.eta n.id)

theorem measurable_slotOut (E : Env) (i : ℕ) (s : EpochState) : Measurable (slotOut E i s) := by
  have h1 : Measurable fun T => honCount E i s T :=
    measurable_filterLength _ fun j => (measurable_of_countable fun b : Bool => E.online j i && b).comp
      (measurable_win E.c s (fun n => decide (n.owner = .honest j)))
  have h2 : Measurable fun T => advW E.c s T := measurable_win E.c s (fun n => decide (n.owner = .adv))
  exact (measurable_of_countable fun p : ℕ × Bool => enc p).comp (h1.prodMk h2)

theorem measurable_slotOut₂ (E : Env) (i : ℕ) : Measurable fun p : Tab × EpochState => slotOut E i p.2 p.1 :=
  measurable_from_prod_countable_left fun s => measurable_slotOut E i s

/-! ## Freezing the state -/

/-- **Freezing.** If `Y` is known under `m` and `T` is independent of `m`, then
weighted by any `m`-measurable `f`, the event `g Y T = o` has the probability it
has for `Y` frozen at its value. -/
theorem freeze {Ω α β : Type*} {m : MeasurableSpace Ω} [mΩ : MeasurableSpace Ω] {μ : Measure Ω} [IsFiniteMeasure μ]
    [MeasurableSpace α] [Countable α] [MeasurableSingletonClass α] [mβ : MeasurableSpace β]
    (hm : m ≤ mΩ) {Y : Ω → α} (hY : Measurable[m] Y) {T : Ω → β} (hT : Measurable T)
    (hind : Indep m (MeasurableSpace.comap T mβ) μ) {g : α → β → Out} (hg : ∀ a, Measurable (g a)) (o : Out)
    {f : Ω → ℝ≥0∞} (hf : Measurable[m] f) :
    ∫⁻ ω, f ω * (if g (Y ω) (T ω) = o then 1 else 0) ∂μ =
      ∫⁻ ω, f ω * μ {ω' | g (Y ω) (T ω') = o} ∂μ := by
  classical
  have hTm : MeasurableSpace.comap T mβ ≤ mΩ := hT.comap_le
  have hYa : ∀ a, MeasurableSet[m] {ω | Y ω = a} := fun a => hY (measurableSet_singleton a)
  have hTa : ∀ a, MeasurableSet[MeasurableSpace.comap T mβ] {ω | g a (T ω) = o} :=
    fun a => (comap_measurable T) ((hg a) (measurableSet_singleton o))
  have hT' : ∀ a, Measurable[MeasurableSpace.comap T mβ] fun ω => (if g a (T ω) = o then (1 : ℝ≥0∞) else 0) :=
    fun a => Measurable.ite (hTa a) measurable_const measurable_const
  have hsum : ∀ ω (h : α → ℝ≥0∞), h (Y ω) = ∑' a, (if Y ω = a then 1 else 0) * h a := by
    intro ω h
    rw [tsum_eq_single (Y ω) (fun a ha => by simp [Ne.symm ha])]
    simp
  have hfa : ∀ a, Measurable[m] fun ω => f ω * (if Y ω = a then 1 else 0) := fun a =>
    hf.mul (Measurable.ite (hYa a) measurable_const measurable_const)
  calc ∫⁻ ω, f ω * (if g (Y ω) (T ω) = o then 1 else 0) ∂μ
      = ∫⁻ ω, ∑' a, (f ω * (if Y ω = a then 1 else 0)) * (if g a (T ω) = o then 1 else 0) ∂μ := by
        refine lintegral_congr fun ω => ?_
        rw [hsum ω (fun a => if g a (T ω) = o then 1 else 0), ← ENNReal.tsum_mul_left]
        exact tsum_congr fun a => by ring
    _ = ∑' a, ∫⁻ ω, (f ω * (if Y ω = a then 1 else 0)) * (if g a (T ω) = o then 1 else 0) ∂μ :=
        lintegral_tsum fun a => (((hfa a).mono hm le_rfl).mul ((hT' a).mono hTm le_rfl)).aemeasurable
    _ = ∑' a, (∫⁻ ω, f ω * (if Y ω = a then 1 else 0) ∂μ) * μ {ω' | g a (T ω') = o} := by
        refine tsum_congr fun a => ?_
        rw [lintegral_mul_eq_lintegral_mul_lintegral_of_independent_measurableSpace hm hTm hind (hfa a) (hT' a)]
        congr 1
        rw [← lintegral_indicator_one (hTm _ (hTa a))]
        refine lintegral_congr fun ω => ?_
        simp [Set.indicator]
    _ = ∑' a, ∫⁻ ω, f ω * (if Y ω = a then 1 else 0) * μ {ω' | g a (T ω') = o} ∂μ :=
        tsum_congr fun a => (lintegral_mul_const _ ((hfa a).mono hm le_rfl)).symm
    _ = ∫⁻ ω, ∑' a, f ω * (if Y ω = a then 1 else 0) * μ {ω' | g a (T ω') = o} ∂μ :=
        (lintegral_tsum fun a => (((hfa a).mono hm le_rfl).mul_const _).aemeasurable).symm
    _ = ∫⁻ ω, f ω * μ {ω' | g (Y ω) (T ω') = o} ∂μ := by
        refine lintegral_congr fun ω => ?_
        rw [hsum ω (fun a => μ {ω' | g a (T ω') = o}), ← ENNReal.tsum_mul_left]
        exact tsum_congr fun a => by ring

/-! ## The random oracle -/

/-- **A random oracle** for the tickets: within one slot's table and one nonce, the
tickets of distinct notes are independent and uniform on `[0, p)`. -/
structure RandomOracle {Ω : Type*} [MeasurableSpace Ω] (μ : Measure Ω) (O : Ω → Oracle) (p : ℕ) : Prop where
  pos : 0 < p
  meas : ∀ i, Measurable (tk O i)
  indep : ∀ i η, iIndepFun (fun id ω => tk O i ω η id) μ
  unif : ∀ i η id t, t ≤ p → μ {ω | tk O i ω η id < t} = ENNReal.ofReal ((t : ℝ) / p)

/-- The win probability of a note under a state. -/
noncomputable def wn (c : Config) (s : EpochState) (n : Note) : ℝ := (threshold c s.D n.value : ℝ) / c.p

/-- The probability that every note of a list loses. -/
noncomputable def loss (c : Config) (s : EpochState) (L : List Note) : ℝ := (L.map fun n => 1 - wn c s n).prod

/-- The notes of the online honest nodes in `K`. -/
def honNotes (E : Env) (i : ℕ) (s : EpochState) (K : List ℕ) : List Note :=
  s.lead.filter fun n => K.any fun j => E.online j i && decide (n.owner = .honest j)

/-- The adversary's notes. -/
def advNotes (s : EpochState) : List Note := s.lead.filter fun n => decide (n.owner = .adv)

/-- The probability that no online honest node wins. -/
noncomputable def pZero (E : Env) (i : ℕ) (s : EpochState) : ℝ := loss E.c s (honNotes E i s E.nodes)

/-- The probability that exactly one online honest node wins. -/
noncomputable def pOne (E : Env) (i : ℕ) (s : EpochState) : ℝ :=
  (E.nodes.map fun j => loss E.c s (honNotes E i s (E.nodes.erase j)) - pZero E i s).sum

/-- **The honest part of slot `i`'s law** under `s`: no honest leader, one, two or more. -/
noncomputable def qhRO (E : Env) (i : ℕ) (s : EpochState) : Fin 3 → ℝ := fun h =>
  if h.val = 0 then pZero E i s else if h.val = 1 then pOne E i s else 1 - pZero E i s - pOne E i s

/-- **The adversary's win probability** under `s`. -/
noncomputable def qaRO (c : Config) (s : EpochState) : ℝ := 1 - loss c s (advNotes s)

/-- A note loses. -/
def Lose (c : Config) (s : EpochState) (T : Tab) (n : Note) : Prop := wins c s.D n.value (T s.eta n.id) = false

theorem find_id_of_nodup : ∀ (L : List Note), (L.map Note.id).Nodup → ∀ n ∈ L,
    L.find? (fun m => decide (m.id = n.id)) = some n
  | [], _, n, hn => absurd hn (by simp)
  | a :: L, hL, n, hn => by
    rw [List.map_cons, List.nodup_cons] at hL
    rcases List.mem_cons.1 hn with h | h
    · subst h; simp
    · have hne : a.id ≠ n.id := fun he => hL.1 (he ▸ List.mem_map_of_mem h)
      rw [List.find?_cons_of_neg (by simpa using hne)]
      exact find_id_of_nodup L hL.2 n h

theorem ofReal_list_prod {ι : Type*} (L : List ι) (f : ι → ℝ) (hf : ∀ i, 0 ≤ f i) :
    (L.map fun i => ENNReal.ofReal (f i)).prod = ENNReal.ofReal ((L.map f).prod) := by
  induction L with
  | nil => simp
  | cons a L ih =>
    simp only [List.map_cons, List.prod_cons, ih]
    rw [ENNReal.ofReal_mul (hf a)]

theorem wn_le_one {c : Config} (hp : 0 < c.p) (s : EpochState) (n : Note) : wn c s n ≤ 1 := by
  unfold wn
  rw [div_le_one (by exact_mod_cast hp)]
  exact_mod_cast (threshold_lt c hp s.D n.value).le

theorem wn_nonneg (c : Config) (s : EpochState) (n : Note) : 0 ≤ wn c s n := by unfold wn; positivity

variable {Ω : Type*} [MeasurableSpace Ω] {μ : Measure Ω} [IsProbabilityMeasure μ] {O : Ω → Oracle}
  {E : Env}

omit [IsProbabilityMeasure μ] in
theorem measurableSet_lose (hO : RandomOracle μ O E.c.p) (i : ℕ) (s : EpochState) (L : List Note) :
    MeasurableSet {ω | ∀ n ∈ L, Lose E.c s (tk O i ω) n} := by
  have : {ω | ∀ n ∈ L, Lose E.c s (tk O i ω) n} = ⋂ n ∈ {n | n ∈ L}, {ω | Lose E.c s (tk O i ω) n} := by
    ext ω; simp
  rw [this]
  refine MeasurableSet.biInter (Set.to_countable _) fun n _ => ?_
  exact ((measurable_ticket s.eta n.id).comp (hO.meas i)) (MeasurableSet.of_discrete (s := {t | wins E.c s.D n.value t = false}))

/-- **Every note of a list loses**, with independent losses. -/
theorem rect (hO : RandomOracle μ O E.c.p) (i : ℕ) (s : EpochState) (L : List Note) (hL : (L.map Note.id).Nodup) :
    μ {ω | ∀ n ∈ L, Lose E.c s (tk O i ω) n} = ENNReal.ofReal (loss E.c s L) := by
  classical
  set val : ℕ → ℕ := fun id => ((L.find? fun n => decide (n.id = id)).map Note.value).getD 0 with hvaldef
  have hval : ∀ n ∈ L, val n.id = n.value := fun n hn => by
    simp only [hvaldef, find_id_of_nodup L hL n hn]; rfl
  set f' : ℕ → Set Ω := fun id => {ω | wins E.c s.D (val id) (tk O i ω s.eta id) = false} with hf'
  have hset : {ω | ∀ n ∈ L, Lose E.c s (tk O i ω) n} = ⋂ id ∈ (L.map Note.id).toFinset, f' id := by
    ext ω
    simp only [Set.mem_setOf_eq, Set.mem_iInter, List.mem_toFinset, List.mem_map, hf', Lose]
    constructor
    · rintro h id ⟨n, hn, rfl⟩; rw [hval n hn]; exact h n hn
    · intro h n hn; have := h n.id ⟨n, hn, rfl⟩; rwa [hval n hn] at this
  have hmeas : ∀ id ∈ (L.map Note.id).toFinset,
      MeasurableSet[MeasurableSpace.comap (fun ω => tk O i ω s.eta id) inferInstance] (f' id) :=
    fun id _ => ⟨{t | wins E.c s.D (val id) t = false}, MeasurableSet.of_discrete, rfl⟩
  rw [hset, (hO.indep i s.eta).meas_biInter hmeas, List.prod_toFinset _ hL, List.map_map]
  have hone : ∀ n ∈ L, μ (f' n.id) = ENNReal.ofReal (1 - wn E.c s n) := by
    intro n hn
    have hc : f' n.id = {ω | tk O i ω s.eta n.id < threshold E.c s.D n.value}ᶜ := by
      ext ω; simp [hf', hval n hn, wins]
    have hms : MeasurableSet {ω | tk O i ω s.eta n.id < threshold E.c s.D n.value} :=
      ((measurable_ticket s.eta n.id).comp (hO.meas i)) (MeasurableSet.of_discrete (s := {t | t < threshold E.c s.D n.value}))
    rw [hc, prob_compl_eq_one_sub hms,
      hO.unif i s.eta n.id _ (threshold_lt E.c hO.pos s.D n.value).le, ← ENNReal.ofReal_one,
      ← ENNReal.ofReal_sub _ (by positivity)]
    rfl
  rw [List.map_congr_left (fun n hn => by simpa using hone n hn)]
  exact ofReal_list_prod L _ fun n => by linarith [wn_le_one hO.pos s n]

/-! ## Events of a slot -/

theorem honW_false_iff {c : Config} {s : EpochState} {T : Tab} {j : ℕ} :
    honW c s T j = false ↔ ∀ n ∈ s.lead, n.owner = .honest j → Lose c s T n := by
  unfold honW Lose
  simp only [List.any_eq_false, Bool.and_eq_true, decide_eq_true_eq, not_and, Bool.not_eq_true]

theorem advW_false_iff {c : Config} {s : EpochState} {T : Tab} :
    advW c s T = false ↔ ∀ n ∈ advNotes s, Lose c s T n := by
  unfold advW advNotes Lose
  simp only [List.any_eq_false, Bool.and_eq_true, decide_eq_true_eq, not_and, Bool.not_eq_true,
    List.mem_filter]
  exact ⟨fun h n hn => h n hn.1 hn.2, fun h n hn ho => h n ⟨hn, ho⟩⟩

theorem lose_honNotes_iff {i : ℕ} {s : EpochState} {T : Tab} {K : List ℕ} :
    (∀ n ∈ honNotes E i s K, Lose E.c s T n) ↔ ∀ j ∈ K, E.online j i = true → honW E.c s T j = false := by
  simp only [honNotes, List.mem_filter, List.any_eq_true, Bool.and_eq_true, decide_eq_true_eq, honW_false_iff]
  constructor
  · intro h j hj ho n hn hown; exact h n ⟨hn, j, hj, ho, hown⟩
  · rintro h n ⟨hn, j, hj, ho, hown⟩; exact h j hj ho n hn hown

theorem count_zero_iff {i : ℕ} {s : EpochState} {T : Tab} :
    honCount E i s T = 0 ↔ ∀ j ∈ E.nodes, E.online j i = true → honW E.c s T j = false := by
  unfold honCount
  rw [List.length_eq_zero_iff, List.filter_eq_nil_iff]
  simp only [Bool.and_eq_true, not_and, Bool.not_eq_true]

theorem count_one_iff (hnd : E.nodes.Nodup) {i : ℕ} {s : EpochState} {T : Tab} :
    honCount E i s T = 1 ↔ ∃ j ∈ E.nodes, (E.online j i = true ∧ honW E.c s T j = true) ∧
      ∀ k ∈ E.nodes, k ≠ j → E.online k i = true → honW E.c s T k = false := by
  classical
  unfold honCount
  rw [← List.toFinset_card_of_nodup (hnd.filter _), Finset.card_eq_one]
  constructor
  · rintro ⟨j, hj⟩
    have hjm : j ∈ (E.nodes.filter fun j => E.online j i && honW E.c s T j).toFinset := by rw [hj]; simp
    simp only [List.mem_toFinset, List.mem_filter, Bool.and_eq_true] at hjm
    refine ⟨j, hjm.1, hjm.2, fun k hk hkj ho => ?_⟩
    by_contra hw
    have : k ∈ (E.nodes.filter fun j => E.online j i && honW E.c s T j).toFinset := by
      simp only [List.mem_toFinset, List.mem_filter, Bool.and_eq_true]
      exact ⟨hk, ho, by simpa using hw⟩
    rw [hj, Finset.mem_singleton] at this
    exact hkj this
  · rintro ⟨j, hj, hjw, hk⟩
    refine ⟨j, Finset.ext fun k => ?_⟩
    simp only [List.mem_toFinset, List.mem_filter, Bool.and_eq_true, Finset.mem_singleton]
    constructor
    · rintro ⟨hkm, ho, hw⟩
      by_contra hkj
      have := hk k hkm hkj ho
      rw [this] at hw; exact Bool.false_ne_true hw
    · rintro rfl; exact ⟨hj, hjw⟩

theorem nodup_honNotes {i : ℕ} {s : EpochState} (hs : (s.lead.map Note.id).Nodup) (K : List ℕ) :
    ((honNotes E i s K).map Note.id).Nodup :=
  hs.sublist ((List.filter_sublist).map Note.id)

theorem nodup_advNotes {s : EpochState} (hs : (s.lead.map Note.id).Nodup) : ((advNotes s).map Note.id).Nodup :=
  hs.sublist ((List.filter_sublist).map Note.id)

theorem nodup_hon_adv {i : ℕ} {s : EpochState} (hs : (s.lead.map Note.id).Nodup) (K : List ℕ) :
    ((honNotes E i s K ++ advNotes s).map Note.id).Nodup := by
  set p : Note → Bool := fun n => K.any fun j => E.online j i && decide (n.owner = .honest j)
  have hsub : List.Sublist (advNotes s) (s.lead.filter (fun n => !p n)) := by
    unfold advNotes
    apply List.monotone_filter_right
    intro n hn
    simp only [decide_eq_true_eq] at hn
    simp [p, hn]
  have hperm := List.filter_append_perm p s.lead
  have h1 : List.Sublist (honNotes E i s K ++ advNotes s) (s.lead.filter p ++ s.lead.filter (fun n => !p n)) :=
    (List.Sublist.refl _).append hsub
  exact ((hperm.map Note.id).nodup_iff.2 hs).sublist (h1.map _)

theorem loss_append (c : Config) (s : EpochState) (L L' : List Note) :
    loss c s (L ++ L') = loss c s L * loss c s L' := by
  unfold loss; rw [List.map_append, List.prod_append]

theorem measurable_honCount (i : ℕ) (s : EpochState) : Measurable fun T => honCount E i s T :=
  measurable_filterLength _ fun j => (measurable_of_countable fun b : Bool => E.online j i && b).comp
    (measurable_win E.c s (fun n => decide (n.owner = .honest j)))

/-- The event that the online honest nodes in `K` all lose. -/
def RK (O : Ω → Oracle) (E : Env) (i : ℕ) (s : EpochState) (K : List ℕ) : Set Ω :=
  {ω | ∀ n ∈ honNotes E i s K, Lose E.c s (tk O i ω) n}

/-- The event that the adversary loses. -/
def RA (O : Ω → Oracle) (E : Env) (i : ℕ) (s : EpochState) : Set Ω :=
  {ω | ∀ n ∈ advNotes s, Lose E.c s (tk O i ω) n}

/-- **The honest count against an event that factors.** -/
theorem count_probs (hO : RandomOracle μ O E.c.p) (hnd : E.nodes.Nodup) (i : ℕ) (s : EpochState)
    {X : Set Ω} (hXm : MeasurableSet X) {x : ℝ} (hXr : μ.real X = x)
    (hX : ∀ K : List ℕ, μ.real (RK O E i s K ∩ X) = loss E.c s (honNotes E i s K) * x) :
    μ.real ({ω | honCount E i s (tk O i ω) = 0} ∩ X) = pZero E i s * x ∧
    μ.real ({ω | honCount E i s (tk O i ω) = 1} ∩ X) = pOne E i s * x ∧
    μ.real ({ω | 2 ≤ honCount E i s (tk O i ω)} ∩ X) = (1 - pZero E i s - pOne E i s) * x := by
  classical
  have hcm : Measurable fun ω => honCount E i s (tk O i ω) := (measurable_honCount i s).comp (hO.meas i)
  have hRm : ∀ K, MeasurableSet (RK O E i s K) := fun K => measurableSet_lose hO i s _
  have h0set : {ω | honCount E i s (tk O i ω) = 0} = RK O E i s E.nodes := by
    ext ω; simp only [Set.mem_setOf_eq, RK, count_zero_iff, lose_honNotes_iff]
  have hsub : ∀ j, RK O E i s E.nodes ∩ X ⊆ RK O E i s (E.nodes.erase j) ∩ X := by
    intro j ω ⟨h, hx⟩
    refine ⟨?_, hx⟩
    simp only [RK, Set.mem_setOf_eq, lose_honNotes_iff] at h ⊢
    exact fun k hk ho => h k (List.mem_of_mem_erase hk) ho
  have h1set : {ω | honCount E i s (tk O i ω) = 1} ∩ X =
      ⋃ j ∈ E.nodes.toFinset, ((RK O E i s (E.nodes.erase j) ∩ X) \ (RK O E i s E.nodes ∩ X)) := by
    ext ω
    simp only [Set.mem_inter_iff, Set.mem_setOf_eq, count_one_iff hnd, Set.mem_iUnion, List.mem_toFinset,
      Set.mem_diff, RK, lose_honNotes_iff, hnd.mem_erase_iff]
    constructor
    · rintro ⟨⟨j, hj, ⟨ho, hw⟩, hk⟩, hx⟩
      refine ⟨j, hj, ⟨fun k ⟨hkj, hk'⟩ ho' => hk k hk' hkj ho', hx⟩, fun ⟨h, _⟩ => ?_⟩
      rw [h j hj ho] at hw; exact Bool.false_ne_true hw
    · rintro ⟨j, hj, ⟨hk, hx⟩, hn⟩
      refine ⟨⟨j, hj, ?_, fun k hk' hkj ho => hk k ⟨hkj, hk'⟩ ho⟩, hx⟩
      by_contra hc
      apply hn
      refine ⟨fun k hk' ho => ?_, hx⟩
      by_cases hkj : k = j
      · subst hkj
        by_contra hw
        exact hc ⟨ho, by simpa using hw⟩
      · exact hk k ⟨hkj, hk'⟩ ho
  have hwin : ∀ j ∈ E.nodes, ∀ ω ∈ (RK O E i s (E.nodes.erase j) ∩ X) \ (RK O E i s E.nodes ∩ X),
      E.online j i = true ∧ honW E.c s (tk O i ω) j = true := by
    rintro j hj ω ⟨⟨hj', hx⟩, hn⟩
    simp only [RK, Set.mem_setOf_eq, lose_honNotes_iff, Set.mem_inter_iff, not_and] at hj' hn
    by_contra hc
    apply hn _ hx
    intro k hk ho
    by_cases hkj : k = j
    · subst hkj
      by_contra hw
      exact hc ⟨ho, by simpa using hw⟩
    · exact hj' k ((hnd.mem_erase_iff).2 ⟨hkj, hk⟩) ho
  have hp0 : μ.real ({ω | honCount E i s (tk O i ω) = 0} ∩ X) = pZero E i s * x := by
    rw [h0set, hX]; rfl
  have hp1 : μ.real ({ω | honCount E i s (tk O i ω) = 1} ∩ X) = pOne E i s * x := by
    rw [h1set, measureReal_biUnion_finset]
    · rw [Finset.sum_congr rfl fun j _ => measureReal_diff (hsub j) ((hRm _).inter hXm)]
      simp only [hX]
      unfold pOne pZero
      rw [List.sum_toFinset _ hnd, ← List.sum_map_mul_right]
      exact congrArg List.sum (List.map_congr_left fun j _ => by ring)
    · intro j hj k hk hjk
      simp only [Function.onFun]
      rw [Set.disjoint_left]
      intro ω hωj hωk
      have wj := hwin j (List.mem_toFinset.1 hj) ω hωj
      have := hωk.1.1
      simp only [RK, Set.mem_setOf_eq, lose_honNotes_iff] at this
      rw [this j ((hnd.mem_erase_iff).2 ⟨hjk, List.mem_toFinset.1 hj⟩) wj.1] at wj
      exact Bool.false_ne_true wj.2
    · exact fun j _ => ((hRm _).inter hXm).diff ((hRm _).inter hXm)
  refine ⟨hp0, hp1, ?_⟩
  have hpart : X = ({ω | honCount E i s (tk O i ω) = 0} ∩ X) ∪
      (({ω | honCount E i s (tk O i ω) = 1} ∩ X) ∪ ({ω | 2 ≤ honCount E i s (tk O i ω)} ∩ X)) := by
    ext ω; simp only [Set.mem_union, Set.mem_inter_iff, Set.mem_setOf_eq]
    generalize honCount E i s (tk O i ω) = c
    constructor
    · intro hx
      rcases Nat.lt_or_ge c 2 with h | h
      · interval_cases c <;> simp_all
      · exact Or.inr (Or.inr ⟨h, hx⟩)
    · rintro (⟨_, hx⟩ | ⟨_, hx⟩ | ⟨_, hx⟩) <;> exact hx
  have hm1 : MeasurableSet ({ω | honCount E i s (tk O i ω) = 1} ∩ X) :=
    (hcm (measurableSet_singleton 1)).inter hXm
  have hm2 : MeasurableSet ({ω | 2 ≤ honCount E i s (tk O i ω)} ∩ X) :=
    (hcm (MeasurableSet.of_discrete (s := {n | 2 ≤ n}))).inter hXm
  have hx := hXr
  rw [hpart, measureReal_union (by
      rw [Set.disjoint_left]; intro ω h h'
      simp only [Set.mem_inter_iff, Set.mem_setOf_eq, Set.mem_union] at h h'; omega) (hm1.union hm2),
    measureReal_union (by
      rw [Set.disjoint_left]; intro ω h h'
      simp only [Set.mem_inter_iff, Set.mem_setOf_eq] at h h'; omega) hm2, hp0, hp1] at hx
  linarith

theorem loss_nonneg {c : Config} (hp : 0 < c.p) (s : EpochState) (L : List Note) : 0 ≤ loss c s L := by
  unfold loss
  exact List.prod_nonneg fun x hx => by
    obtain ⟨n, -, rfl⟩ := List.mem_map.1 hx
    linarith [wn_le_one hp s n]

theorem enc_eq_iff (n : ℕ) (b : Bool) (h : Fin 3) (b' : Bool) :
    enc (n, b) = ⟨h, b'⟩ ↔ ((h.val = 0 ∧ n = 0) ∨ (h.val = 1 ∧ n = 1) ∨ (h.val = 2 ∧ 2 ≤ n)) ∧ b = b' := by
  unfold enc
  simp only [Out.mk.injEq]
  constructor
  · rintro ⟨hh, rfl⟩
    refine ⟨?_, rfl⟩
    split_ifs at hh with h0 h1 <;> subst hh <;> simp <;> omega
  · rintro ⟨hh, rfl⟩
    refine ⟨?_, rfl⟩
    rcases hh with ⟨hv, hn⟩ | ⟨hv, hn⟩ | ⟨hv, hn⟩ <;> apply Fin.ext <;> split_ifs <;> simp_all

/-- **The law of a slot under a random oracle.** For a state whose lead notes have
distinct identifiers, slot `i`'s outcome has the law `qhRO ⊗ Bern(qaRO)`. -/
theorem slot_law (hO : RandomOracle μ O E.c.p) (hnd : E.nodes.Nodup) (i : ℕ) (s : EpochState)
    (hs : (s.lead.map Note.id).Nodup) (o : Out) :
    μ {ω | slotOut E i s (tk O i ω) = o} = ENNReal.ofReal (prodLaw (qhRO E i s) (qaRO E.c s) o) := by
  classical
  have hp := hO.pos
  have toR : ∀ {A : Set Ω} {x : ℝ}, 0 ≤ x → μ A = ENNReal.ofReal x → μ.real A = x := by
    intro A x hx h; rw [measureReal_def, h, ENNReal.toReal_ofReal hx]
  have hRK : ∀ K, μ.real (RK O E i s K) = loss E.c s (honNotes E i s K) := fun K =>
    toR (loss_nonneg hp s _) (rect hO i s _ (nodup_honNotes hs K))
  have hRKA : ∀ K, μ.real (RK O E i s K ∩ RA O E i s) = loss E.c s (honNotes E i s K) * loss E.c s (advNotes s) := by
    intro K
    have e : RK O E i s K ∩ RA O E i s = {ω | ∀ n ∈ honNotes E i s K ++ advNotes s, Lose E.c s (tk O i ω) n} := by
      ext ω; simp only [RK, RA, Set.mem_inter_iff, Set.mem_setOf_eq, List.mem_append]
      exact ⟨fun ⟨h1, h2⟩ n hn => hn.elim (h1 n) (h2 n), fun h => ⟨fun n hn => h n (Or.inl hn), fun n hn => h n (Or.inr hn)⟩⟩
    rw [e, toR (loss_nonneg hp s _) (rect hO i s _ (nodup_hon_adv hs K)), loss_append]
  have hRAm : MeasurableSet (RA O E i s) := measurableSet_lose hO i s _
  have hRA : μ.real (RA O E i s) = loss E.c s (advNotes s) := toR (loss_nonneg hp s _) (rect hO i s _ (nodup_advNotes hs))
  obtain ⟨a0, a1, a2⟩ := count_probs hO hnd i s hRAm hRA hRKA
  have hRKc : ∀ K, μ.real (RK O E i s K ∩ (RA O E i s)ᶜ) =
      loss E.c s (honNotes E i s K) * (1 - loss E.c s (advNotes s)) := by
    intro K
    have e : RK O E i s K ∩ (RA O E i s)ᶜ = RK O E i s K \ (RK O E i s K ∩ RA O E i s) := by
      ext ω; simp only [Set.mem_inter_iff, Set.mem_compl_iff, Set.mem_diff, not_and]; tauto
    rw [e, measureReal_diff Set.inter_subset_left
      ((show MeasurableSet (RK O E i s K) from measurableSet_lose hO i s _).inter hRAm), hRK, hRKA]
    ring
  have hRAc : μ.real (RA O E i s)ᶜ = 1 - loss E.c s (advNotes s) := by
    rw [probReal_compl_eq_one_sub hRAm, hRA]
  obtain ⟨b0, b1, b2⟩ := count_probs hO hnd i s hRAm.compl hRAc hRKc
  rw [← ofReal_measureReal (measure_ne_top μ _)]
  congr 1
  obtain ⟨h, b⟩ := o
  have hset : {ω | slotOut E i s (tk O i ω) = ⟨h, b⟩} =
      {ω | (h.val = 0 ∧ honCount E i s (tk O i ω) = 0) ∨ (h.val = 1 ∧ honCount E i s (tk O i ω) = 1) ∨
        (h.val = 2 ∧ 2 ≤ honCount E i s (tk O i ω))} ∩ (if b then (RA O E i s)ᶜ else RA O E i s) := by
    ext ω
    simp only [Set.mem_setOf_eq, slotOut, enc_eq_iff, Set.mem_inter_iff]
    refine and_congr Iff.rfl ?_
    cases b
    · simp only [Bool.false_eq_true, ↓reduceIte, RA, Set.mem_setOf_eq, ← advW_false_iff]
    · simp only [↓reduceIte, RA, Set.mem_compl_iff, Set.mem_setOf_eq, ← advW_false_iff, Bool.not_eq_false]
  rw [hset]
  fin_cases h <;> cases b <;> simp [prodLaw, qhRO, qaRO, a0, a1, a2, b0, b1, b2]

/-! ## From an unsafe execution to an event closed under adversarial slots -/

/-- **An unsafe execution's lottery string fails the good event robustly**: every
outcome list with its honest leaders and at least its adversarial slots fails it. -/
theorem unsafe_up (E : Env) (hA : Assm E) {O : Oracle} {es : List Event} {N M Lw r G : ℕ}
    (hNF : (wF (E.withO O) es).now ≤ N) (hNM : N + G < M) (hU : Unsafe (E.withO O) es) :
    slots (lotStr (E.withO O) es) M ∈ RBad E N M Lw r G := by
  intro l' hl hg
  obtain ⟨w, hdom, hgw⟩ := good_dom (E.withO O) (by omega)
    (fun ep hep _ => by have := ((hA.withO O).sane.fix_ok ep hep).1; omega) hl hg.withO
  obtain ⟨n, n', i, j, hnn, hn', hi, hj, hio, hjo, hb⟩ := hU
  exact hb (final_bimm_dom (hA.withO O) hNF hdom hgw.1 hgw.2 hnn hn' hi hj hio hjo)

/-! ## Probabilistic finality from the random oracle -/

/-- What is known before slot `i`'s tickets are drawn: the earlier slots' ticket
tables and the epoch states of the slots up to `i`. -/
@[instance_reducible]
def hist (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) (i : ℕ) : MeasurableSpace Ω :=
  (⨆ j ∈ Finset.range i, MeasurableSpace.comap (tk O j) inferInstance) ⊔
    (⨆ j ∈ Finset.range (i + 1), MeasurableSpace.comap (fun ω => σ ω j) inferInstance)

/-- **Fresh lotteries** (no grinding): each slot's ticket table is independent of
what is known before it, including the epoch state the slot's lottery runs under. -/
def Fresh (μ : Measure Ω) (O : Ω → Oracle) (σ : Ω → ℕ → EpochState) : Prop :=
  ∀ i, Indep (hist O σ i) (MeasurableSpace.comap (tk O i) inferInstance) μ

/-- **The band condition on an epoch state** for slot `i`: the honest part of the
slot's law is in the band's honest polytope, and the adversary wins with probability
at most `amax`. -/
structure SlotBand (B : Band) (E : Env) (i : ℕ) (s : EpochState) : Prop where
  hon : qhRO E i s ∈ HB B
  adv : qaRO E.c s ≤ B.amax

theorem loss_le_one {c : Config} (hp : 0 < c.p) (s : EpochState) (L : List Note) : loss c s L ≤ 1 := by
  unfold loss
  induction L with
  | nil => simp
  | cons n L ih =>
    simp only [List.map_cons, List.prod_cons]
    have h1 : 1 - wn c s n ≤ 1 := by linarith [wn_nonneg c s n]
    have h0 : 0 ≤ 1 - wn c s n := by linarith [wn_le_one hp s n]
    have := loss_nonneg hp s L
    unfold loss at this
    nlinarith

end Cryptarchia.Prob

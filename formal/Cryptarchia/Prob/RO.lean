import Cryptarchia.Prob.Worst
import Cryptarchia.Prob.Final2

/-!
# The lottery law from a random oracle

`final_bimm_prob2` assumes the law of the lottery string (`hlaw`). This file derives
it from a random-oracle model of the note lottery.

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

/-- The environment with oracle `O`. -/
def _root_.Cryptarchia.Env.withO (E : Env) (O : Oracle) : Env := { E with O := O }

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

/-- The assumptions do not involve the oracle. -/
theorem _root_.Cryptarchia.Assm.withO {E : Env} (h : Assm E) (O : Oracle) : Assm (E.withO O) :=
  ⟨h.ord, h.crash, h.exec, h.nodup, h.sane, h.stake⟩

/-- The good event does not involve the oracle. -/
theorem goodLS_withO {E : Env} {O : Oracle} {w : CStr} {N Lw : ℕ} {e : ℕ → ℕ} (h : GoodLS E w N Lw e) :
    GoodLS (E.withO O) w N Lw e :=
  ⟨h.e0, h.mono, h.quiet, h.unb, h.cold, h.window⟩

/-! ## From an unsafe execution to an event closed under adversarial slots -/

theorem enc_hon_zero (p : ℕ × Bool) : (enc p).hon.val = 0 ↔ p.1 = 0 := by
  unfold enc; split_ifs <;> simp_all

theorem enc_hon_one (p : ℕ × Bool) : (enc p).hon.val = 1 ↔ p.1 = 1 := by
  unfold enc; split_ifs <;> simp_all

theorem slots_get (w : CStr) (M k : ℕ) (hk : k < (slots w M).length) :
    (slots w M)[k] = enc (w (k + 1)) := by
  simp [slots]

/-- **Unsafe executions are bad for every dominating outcome list.** If an execution
is unsafe, then every outcome list with the lottery string's honest leaders and at
least its adversarial slots fails the good event. -/
theorem unsafe_up (E : Env) (hA : Assm E) {es : List Event} {N M Lw r G : ℕ} (hNF : (wF E es).now ≤ N)
    (hNM : N + G < M) (hU : Unsafe E es) {l' : List Out}
    (hl : List.Forall₂ OutLe (slots (lotStr E es) M) l') :
    ¬ (GoodLS E (strOf l') N Lw (gend E.Δ M (strOf l')) ∧ GrowthS E (strOf l') (gend E.Δ M (strOf l')) N r G) := by
  classical
  intro hg
  set lot := lotStr E es with hlot
  obtain ⟨hlen, hget⟩ := List.forall₂_iff_get.1 hl
  rw [slots_length] at hlen
  -- the outcome at slot `i` of `l'` dominates the lottery string's
  have hdom1 : ∀ i, 1 ≤ i → i ≤ M → OutLe (enc (lot i)) (l'.getD (i - 1) Out.empty) := by
    intro i h1 h2
    have hk1 : i - 1 < (slots lot M).length := by rw [slots_length]; omega
    have hk2 : i - 1 < l'.length := by omega
    have := hget (i - 1) hk1 hk2
    rw [List.getD_eq_getElem _ _ hk2]
    simp only [List.get_eq_getElem, slots_get, show i - 1 + 1 = i by omega] at this
    exact this
  set w : CStr := fun i => if 1 ≤ i ∧ i ≤ M then ((lot i).1, (strOf l' i).2) else lot i with hw
  have hstr : ∀ i, 1 ≤ i → strOf l' i = (l'.getD (i - 1) Out.empty).toPair := by
    intro i hi; unfold strOf; rw [if_neg (by omega)]
  have hdom : AdvLeW N lot w := by
    refine ⟨fun i _ _ => by simp only [hw]; split_ifs <;> rfl, fun i hi => ?_⟩
    simp only [hw]
    split_ifs with h
    · rw [hstr i h.1]
      exact (hdom1 i h.1 h.2).2 (by simpa [enc] using hi)
    · exact hi
  have hsim : SimOn (strOf l') w 0 M := by
    intro i h1 h2
    have hd := hdom1 i (by omega) h2
    simp only [hw, if_pos (show 1 ≤ i ∧ i ≤ M by omega)]
    rw [hstr i (by omega)]
    simp only [Out.toPair]
    rw [← hd.1]
    exact ⟨enc_hon_zero _, enc_hon_one _, trivial⟩
  have hgw := good_congr E rfl hA.sane hsim hNM hg
  obtain ⟨n, n', i, j, hnn, hn', hi, hj, hio, hjo, hb⟩ := hU
  exact hb (final_bimm_dom hA hNF hdom hgw.1 hgw.2 hnn hn' hi hj hio hjo)

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

/-- **The band condition on an epoch state** for slot `i`: the lead notes have
distinct identifiers, the honest part of the slot's law is in the band's honest
polytope, and the adversary wins with probability at most `amax`. -/
structure SlotBand (B : Band) (E : Env) (i : ℕ) (s : EpochState) : Prop where
  nodup : (s.lead.map Note.id).Nodup
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

/-- **Probabilistic finality from a random oracle.**

The oracle is random (`O ω`) and the adversary's strategy is anything (`es ω`); all
clocks stay below `N`. Assume:
* `hO`: tickets are a random oracle (independent and uniform per note);
* `hfresh`: each slot's tickets are fresh given the past and the slot's epoch state
  (no grinding);
* `hdel`: Δ-delivery of honest blocks;
* `hband`: every epoch state a slot's lottery can run under is within the band.
Then a finality violation has probability at most `settleEps2`. -/
theorem final_bimm_ro (hA : Assm E) (es : Ω → List Event) {N M : ℕ}
    (hNF : ∀ ω, (wF (E.withO (O ω)) (es ω)).now ≤ N)
    (hdel : ∀ ω, DeltaDelivery (E.withO (O ω)) (es ω))
    (hO : RandomOracle μ O E.c.p)
    (hσm : ∀ i, Measurable fun ω => σE (E.withO (O ω)) (es ω) i)
    (hfresh : Fresh μ O fun ω => σE (E.withO (O ω)) (es ω))
    {B : Band} {Δ : ℕ} (hΔ : E.Δ = Δ) (P : Cert2 B Δ) (hBp : ∀ B' ∈ P.Bs, B'.Prod)
    (hband : ∀ ω i, 1 ≤ i → i ≤ M → ∃ B' ∈ P.Bs, SlotBand B' E i (σE (E.withO (O ω)) (es ω) i))
    {G G' J Lw r T : ℕ} {x yy : ℝ} (hx : 1 ≤ x) (hyy0 : 0 < yy)
    (hyy1 : yy ≤ 1) (hT : 1 ≤ T) (hNM : N + G + Δ + 2 ≤ M) (hNM' : N + G' + Δ + 1 < M)
    (hhi1 : B.hhi ≤ 1) (hlo0 : 0 ≤ B.hlo) (hlo1 : B.hlo ≤ 1) (helo1 : B.elo ≤ 1) :
    μ {ω | Unsafe (E.withO (O ω)) (es ω)} ≤ ENNReal.ofReal (settleEps2 E B P N G G' J Lw r T x yy) := by
  classical
  subst hΔ
  set σ : Ω → ℕ → EpochState := fun ω => σE (E.withO (O ω)) (es ω) with hσ
  set X : ℕ → Ω → Out := fun k ω => slotOut E (k + 1) (σ ω (k + 1)) (tk O (k + 1) ω) with hX
  have hslots : ∀ ω, slots (lotStr (E.withO (O ω)) (es ω)) M = List.ofFn (fun k : Fin M => X k ω) := by
    intro ω
    apply List.ext_getElem (by simp [slots_length])
    intro k h1 h2
    rw [slots_get, List.getElem_ofFn]
    exact enc_lotStr (hdel ω) (k + 1)
  -- measurability
  have hm : ∀ n, hist O σ n ≤ ‹MeasurableSpace Ω› := fun n =>
    sup_le (iSup₂_le fun j _ => (hO.meas j).comap_le) (iSup₂_le fun j _ => (hσm j).comap_le)
  have hTh : ∀ n j, j < n → Measurable[hist O σ n] (tk O j) := fun n j hj =>
    (comap_measurable (tk O j)).mono (le_sup_of_le_left (le_iSup₂_of_le j (Finset.mem_range.2 hj) le_rfl)) le_rfl
  have hσh : ∀ n j, j ≤ n → Measurable[hist O σ n] (fun ω => σ ω j) := fun n j hj =>
    (comap_measurable (fun ω => σ ω j)).mono
      (le_sup_of_le_right (le_iSup₂_of_le j (Finset.mem_range.2 (by omega)) le_rfl)) le_rfl
  have hXm : ∀ j, Measurable (X j) := fun j =>
    (measurable_slotOut₂ E (j + 1)).comp ((hO.meas (j + 1)).prodMk (hσm (j + 1)))
  have hXh : ∀ n j, j < n → Measurable[hist O σ (n + 1)] (X j) := fun n j hj =>
    (measurable_slotOut₂ E (j + 1)).comp ((hTh (n + 1) (j + 1) (by omega)).prodMk (hσh (n + 1) (j + 1) (by omega)))
  -- the bad set, and its closure under adding adversarial slots
  set Bad : Set (List Out) := {l | ¬ (GoodLS E (strOf l) N Lw (gend E.Δ M (strOf l)) ∧
    GrowthS E (strOf l) (gend E.Δ M (strOf l)) N r G)} with hBad
  set S : Set (List Out) := {l | ∀ l', List.Forall₂ OutLe l l' → l' ∈ Bad} with hSdef
  have hS : UpClosed S := fun l l2 h hl l' h' => hl l' (forall₂_trans h h')
  have hsub : {ω | Unsafe (E.withO (O ω)) (es ω)} ⊆ {ω | List.ofFn (fun k : Fin M => X k ω) ∈ S} := by
    intro ω hU
    simp only [Set.mem_setOf_eq, hSdef]
    rw [← hslots ω]
    intro l' hl'
    simp only [hBad, Set.mem_setOf_eq]
    intro hg
    exact unsafe_up (E.withO (O ω)) (hA.withO (O ω)) (Lw := Lw) (r := r) (G := G) (hNF ω) (by omega) hU hl'
      ⟨goodLS_withO hg.1, hg.2⟩
  obtain ⟨κ, hκ, hbound⟩ := law_le μ hBp (M := M) (by omega) X hXm (fun n => hist O σ (n + 1)) (fun n => hm _)
    hXh (fun n ω => qhRO E (n + 1) (σ ω (n + 1))) (fun n ω => qaRO E.c (σ ω (n + 1)))
    (fun n hn ω => by
      obtain ⟨B', hB', hb⟩ := hband ω (n + 1) (by omega) (by omega)
      exact ⟨B', hB', hb.hon, by unfold qaRO; linarith [loss_le_one hO.pos (σ ω (n + 1)) (advNotes (σ ω (n + 1)))],
        hb.adv⟩)
    (fun n _ o => (measurable_of_countable fun s : EpochState =>
      ENNReal.ofReal (prodLaw (qhRO E (n + 1) s) (qaRO E.c s) o)).comp (hσh (n + 1) (n + 1) le_rfl))
    (fun n hn f hf o => by
      have h := freeze (m := hist O σ (n + 1)) (μ := μ) (hm _) (hσh (n + 1) (n + 1) le_rfl) (hO.meas (n + 1))
        (hfresh (n + 1)) (g := fun s T => slotOut E (n + 1) s T) (fun s => measurable_slotOut E (n + 1) s) o hf
      refine h.trans (lintegral_congr fun ω => ?_)
      rw [slot_law hO hA.nodup (n + 1) (σ ω (n + 1))
        (hband ω (n + 1) (by omega) (by omega)).choose_spec.2.nodup o])
    hS
  refine (measure_mono hsub).trans (hbound.trans (ENNReal.ofReal_le_ofReal ?_))
  refine le_trans ?_ (settle_bound2 E rfl hA.sane P hκ hx hyy0 hyy1 hT hNM hNM' hhi1 hlo0 hlo1 helo1)
  apply Ex_mono_len
  intro t _
  simp only [List.nil_append]
  by_cases ht : t ∈ S
  · have hb : t ∈ Bad := ht t (forall₂_refl t)
    rw [Set.indicator_of_mem ht]
    simp only [hBad, Set.mem_setOf_eq] at hb
    rw [if_neg hb]; rfl
  · rw [Set.indicator_of_notMem ht]
    split_ifs <;> norm_num

end Cryptarchia.Prob

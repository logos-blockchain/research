import Mantle.Ledger

/-!
# The value held by a note set

Notes are private: the ledger holds commitments and nullifiers only. Under a collision-free
hash, a commitment opens to at most one note (`cmValue` is its value) and determines the
nullifier its holder derives (`cmNf`). The value a set holds is then a function of its
commitments and nullifiers:

* `Unspent N c`: the nullifier of `c`, if any, is not in `N`. A commitment whose public key
  has no secret key can never be spent, and keeps counting;
* `supply cms N`: the total value of the **distinct** unspent commitments.

Distinctness matters: two notes with the same fields share a commitment and a nullifier, so
only one of them can ever be spent (RFC-480, *Leader reward in the block*). Appending a
commitment twice therefore adds its value once, which is why value can be lost but, as the
lemmas below show, never created:

* `supply_append_le`: adding commitments adds at most their values;
* `supply_spend`: consuming distinct unspent notes by their nullifiers removes exactly their
  values;
* **`supply_spend_append_le`**: both at once, the consumed notes being among the old
  commitments or the new ones.
-/

namespace Mantle

open Classical

noncomputable section

variable (H : Hash)

/-- The nullifier of `c`, if `c` has one, is not in `N`. -/
def Unspent (N : Finset Fr) (c : Fr) : Prop := ∀ nf, cmNf H c = some nf → nf ∉ N

/-- The value of the distinct unspent commitments of `cms`. -/
def supply (cms : List Fr) (N : Finset Fr) : ℕ :=
  ∑ c ∈ cms.toFinset.filter (Unspent H N), cmValue H c

/-- The value of a list of commitments. -/
def listValue (l : List Fr) : ℕ := (l.map (cmValue H)).sum

variable {H}

theorem listValue_append (a b : List Fr) : listValue H (a ++ b) = listValue H a + listValue H b := by
  simp [listValue]

@[simp] theorem listValue_nil : listValue H [] = 0 := rfl

theorem listValue_cons (a : Fr) (l : List Fr) : listValue H (a :: l) = cmValue H a + listValue H l := by
  simp [listValue]

theorem listValue_flatMap {α : Type*} (l : List α) (f : α → List Fr) :
    listValue H (l.flatMap f) = (l.map fun a => listValue H (f a)).sum := by
  induction l with
  | nil => rfl
  | cons a l ih => simp [List.flatMap_cons, listValue_append, ih]

theorem finset_sum_toFinset_le (l : List Fr) (f : Fr → ℕ) :
    ∑ c ∈ l.toFinset, f c ≤ (l.map f).sum := by
  rw [Finset.sum_list_map_count]
  apply Finset.sum_le_sum
  intro c hc
  have : 1 ≤ l.count c := List.count_pos_iff.2 (List.mem_toFinset.1 hc)
  simp only [smul_eq_mul]
  nlinarith [Nat.zero_le (f c)]

theorem sum_toFinset_of_nodup {l : List Fr} (hl : l.Nodup) (f : Fr → ℕ) :
    ∑ c ∈ l.toFinset, f c = (l.map f).sum := by
  rw [List.sum_toFinset _ hl]

/-- Adding commitments adds at most their values. -/
theorem supply_append_le (cms outs : List Fr) (N : Finset Fr) :
    supply H (cms ++ outs) N ≤ supply H cms N + listValue H outs := by
  unfold supply
  rw [List.toFinset_append, Finset.filter_union]
  calc _ ≤ ∑ c ∈ cms.toFinset.filter (Unspent H N), cmValue H c +
        ∑ c ∈ outs.toFinset.filter (Unspent H N), cmValue H c := by
          have := Finset.sum_union_inter (s₁ := cms.toFinset.filter (Unspent H N))
            (s₂ := outs.toFinset.filter (Unspent H N)) (f := cmValue H)
          omega
    _ ≤ _ := by
      gcongr
      calc _ ≤ ∑ c ∈ outs.toFinset, cmValue H c :=
            Finset.sum_le_sum_of_subset (Finset.filter_subset _ _)
        _ ≤ _ := finset_sum_toFinset_le _ _

theorem forall₂_mem_right {α β : Type*} {R : α → β → Prop} {l₁ : List α} {l₂ : List β}
    (h : List.Forall₂ R l₁ l₂) {b : β} (hb : b ∈ l₂) : ∃ a ∈ l₁, R a b := by
  induction h with
  | nil => simp at hb
  | cons hr _ ih =>
    rcases List.mem_cons.1 hb with rfl | hb
    · exact ⟨_, List.mem_cons_self .., hr⟩
    · obtain ⟨a, ha, hra⟩ := ih hb
      exact ⟨a, List.mem_cons_of_mem _ ha, hra⟩

theorem forall₂_mem_left {α β : Type*} {R : α → β → Prop} {l₁ : List α} {l₂ : List β}
    (h : List.Forall₂ R l₁ l₂) {a : α} (ha : a ∈ l₁) : ∃ b ∈ l₂, R a b := by
  induction h with
  | nil => simp at ha
  | cons hr _ ih =>
    rcases List.mem_cons.1 ha with rfl | ha
    · exact ⟨_, List.mem_cons_self .., hr⟩
    · obtain ⟨b, hb, hrb⟩ := ih ha
      exact ⟨b, List.mem_cons_of_mem _ hb, hrb⟩

/-- Consumed notes, named by their nullifiers: `cs` are the commitments of the nullifiers
`ins`. -/
abbrev Names (H : Hash) (ins cs : List Fr) : Prop :=
  List.Forall₂ (fun nf c => cmNf H c = some nf) ins cs

/-- Distinct nullifiers name distinct commitments. -/
theorem Names.nodup {ins cs : List Fr} (h : Names H ins cs) (hn : ins.Nodup) : cs.Nodup := by
  induction h with
  | nil => exact List.nodup_nil
  | @cons nf c ins cs hc htl ih =>
    rw [List.nodup_cons] at hn ⊢
    refine ⟨fun hmem => ?_, ih hn.2⟩
    obtain ⟨nf', hnf', hc'⟩ := forall₂_mem_right htl hmem
    rw [hc] at hc'
    cases hc'
    exact hn.1 hnf'

theorem Names.append {a b ca cb : List Fr} (ha : Names H a ca) (hb : Names H b cb) :
    Names H (a ++ b) (ca ++ cb) := List.rel_append ha hb

/-- Consuming distinct unspent notes by their nullifiers removes exactly their values. -/
theorem supply_spend {cms ins cs : List Fr} {N : Finset Fr} (hnames : Names H ins cs)
    (hn : ins.Nodup) (hcs : ∀ c ∈ cs, c ∈ cms) (hfresh : ∀ nf ∈ ins, nf ∉ N) :
    supply H cms (N ∪ ins.toFinset) + listValue H cs = supply H cms N := by
  have hcsn := hnames.nodup hn
  -- the commitments `cs` are unspent before
  have hU : ∀ c ∈ cs, Unspent H N c := by
    intro c hc nf' hnf'
    obtain ⟨nf, hnf, hcnf⟩ := forall₂_mem_right hnames hc
    rw [hcnf] at hnf'
    exact Option.some_inj.1 hnf' ▸ hfresh nf hnf
  -- and they are exactly the ones that become spent
  have hfilter : cms.toFinset.filter (Unspent H N) =
      cms.toFinset.filter (Unspent H (N ∪ ins.toFinset)) ∪ cs.toFinset := by
    ext c
    simp only [Finset.mem_filter, List.mem_toFinset, Finset.mem_union]
    constructor
    · rintro ⟨hc, hu⟩
      by_cases hcs' : c ∈ cs
      · exact Or.inr hcs'
      · refine Or.inl ⟨hc, fun nf hnf hmem => ?_⟩
        rcases Finset.mem_union.1 hmem with h | h
        · exact hu nf hnf h
        · obtain ⟨c', hc', hc'nf⟩ := forall₂_mem_left hnames (List.mem_toFinset.1 h)
          exact hcs' (cmNf_injective hnf hc'nf ▸ hc')
    · rintro (⟨hc, hu⟩ | hc)
      · exact ⟨hc, fun nf hnf hmem => hu nf hnf (Finset.mem_union_left _ hmem)⟩
      · exact ⟨hcs c hc, hU c hc⟩
  have hdisj : Disjoint (cms.toFinset.filter (Unspent H (N ∪ ins.toFinset))) cs.toFinset := by
    rw [Finset.disjoint_left]
    intro c hc hcs'
    simp only [Finset.mem_filter] at hc
    obtain ⟨nf, hnf, hcnf⟩ := forall₂_mem_right hnames (List.mem_toFinset.1 hcs')
    exact hc.2 nf hcnf (Finset.mem_union_right _ (List.mem_toFinset.2 hnf))
  unfold supply
  rw [hfilter, Finset.sum_union hdisj, sum_toFinset_of_nodup hcsn]
  rfl

/-- **Consuming and creating notes never creates value**: the consumed notes, named by distinct
fresh nullifiers, may be old commitments or new ones. -/
theorem supply_spend_append_le {cms outs ins cs : List Fr} {N : Finset Fr}
    (hnames : Names H ins cs) (hn : ins.Nodup) (hcs : ∀ c ∈ cs, c ∈ cms ∨ c ∈ outs)
    (hfresh : ∀ nf ∈ ins, nf ∉ N) :
    supply H (cms ++ outs) (N ∪ ins.toFinset) + listValue H cs ≤
      supply H cms N + listValue H outs := by
  rw [supply_spend hnames hn (fun c hc => List.mem_append.2 (hcs c hc)) hfresh]
  exact supply_append_le cms outs N

end

end Mantle

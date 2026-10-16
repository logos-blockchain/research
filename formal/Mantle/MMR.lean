import Mantle.Merkle

/-!
# The commitment Merkle Mountain Range

Mantle, *Commitment Merkle Mountain Range*: the ledger keeps only the peaks of the commitment
tree of each note set, `mmr_append` adds a commitment and merges the last two peaks while
their heights are equal, and `mmr_root` folds the peaks from the right with the roots of the
empty subtrees. The specification claims that this root is the root of the depth-`32` Merkle
tree whose leaves are the commitments in insertion order, empty leaves holding `0`.

Here `Peaks` lists the peaks **rightmost first** (the specification's list reversed, so that
`peaks[-1]` is the head), and

* `mergePeaks`, `mmrAppend` are `mmr_append`; `mmrPeaks l` appends the list `l` to no peak;
* `raiseTo` is the `while height < target` loop, `rootStep` one iteration of the loop over
  `reversed(peaks)`, and `mmrRoot` is `mmr_root`.

Results:

* `mmrPeaks_eq`: the peaks of `n` commitments are the roots of the perfect subtrees given by
  the binary digits of `n` (`peaksAux`);
* **`mmrRoot_mmrPeaks`**: for fewer than `2^32` commitments, `mmr_root` is the root of the
  depth-`32` tree over them, padded with `0`;
* **`mem_of_mmrRoot`**: under a collision-free hash, a non-zero leaf proven by a path of length
  `32` under the MMR root of `l` is an element of `l`; `exists_path_of_mem` is the converse;
* `mmrRoot_full`: with exactly `2^32` commitments the fold ends one level too high, at
  `zkhash(root, empty_root(32))`. The capacity of the MMR is `2^32 - 1` commitments, and the
  specification does not say what happens to a set that reaches it (see `Gas.lean`,
  `blocks_to_fill_set`).
-/

namespace Mantle

variable (H : Hash)

/-- The peaks of a commitment MMR with their heights, **rightmost first**. -/
abbrev Peaks := List (Fr × ℕ)

/-- The merge loop of `mmr_append`: while the last two peaks have the same height, replace
them by their parent. -/
def mergePeaks : Peaks → Peaks
  | (r, h) :: (l, h') :: rest =>
    if h = h' then mergePeaks ((H.node l r, h + 1) :: rest) else (r, h) :: (l, h') :: rest
  | s => s
termination_by s => s.length

/-- `mmr_append(peaks, note_cm)`. -/
def mmrAppend (peaks : Peaks) (cm : Fr) : Peaks := mergePeaks H ((cm, 0) :: peaks)

/-- The peaks of the MMR holding the commitments of `l`, appended in order. -/
def mmrPeaks (l : List Fr) : Peaks := l.foldl (mmrAppend H) []

/-- `while height < target: root = zkhash(root, empty_root(height)); height += 1`. -/
def raiseTo (root : Fr) (a t : ℕ) : Fr :=
  if a < t then raiseTo (H.node root (emptyRoot H a)) (a + 1) t else root
termination_by t - a

/-- One iteration of the loop of `mmr_root` over `reversed(peaks)`. -/
def rootStep (st : Fr × ℕ) (pk : Fr × ℕ) : Fr × ℕ :=
  (H.node pk.1 (raiseTo H st.1 st.2 pk.2), max st.2 pk.2 + 1)

/-- The depth of the commitment tree. -/
def DEPTH : ℕ := 32

/-- `mmr_root(peaks)`. -/
def mmrRoot (peaks : Peaks) : Fr :=
  let st := peaks.foldl (rootStep H) (0, 0)
  raiseTo H st.1 st.2 DEPTH

/-- The leaves of a list: its elements, then `0`. -/
def leafFn (l : List Fr) (i : ℕ) : Fr := l.getD i 0

/-- The peaks of the first `m · 2^h` leaves of `g` above height `h`: one peak per binary digit
of `m`, rightmost first. -/
def peaksAux (g : ℕ → Fr) (m h : ℕ) : Peaks :=
  if m = 0 then [] else
    if m % 2 = 1 then (subtree H g h (m - 1), h) :: peaksAux g (m / 2) (h + 1)
    else peaksAux g (m / 2) (h + 1)
termination_by m
decreasing_by all_goals omega

variable {H}

/-! ## `mmr_append` -/

theorem mergePeaks_eq (r l : Fr) (h : ℕ) (rest : Peaks) :
    mergePeaks H ((r, h) :: (l, h) :: rest) = mergePeaks H ((H.node l r, h + 1) :: rest) := by
  rw [mergePeaks, ite_eq_left rfl]

theorem mergePeaks_ne (r l : Fr) {h h' : ℕ} (hh : h ≠ h') (rest : Peaks) :
    mergePeaks H ((r, h) :: (l, h') :: rest) = (r, h) :: (l, h') :: rest := by
  rw [mergePeaks, ite_eq_right hh]

theorem mergePeaks_single (x : Fr × ℕ) : mergePeaks H [x] = [x] := by
  rw [mergePeaks]
  intro _ _ _ _ _ h
  simp at h

theorem peaksAux_zero (g : ℕ → Fr) (h : ℕ) : peaksAux H g 0 h = [] := by
  rw [peaksAux, ite_eq_left rfl]

theorem peaksAux_odd (g : ℕ → Fr) {m : ℕ} (h : ℕ) (hm : m % 2 = 1) :
    peaksAux H g m h = (subtree H g h (m - 1), h) :: peaksAux H g (m / 2) (h + 1) := by
  rw [peaksAux, ite_eq_right (by omega), ite_eq_left hm]

theorem peaksAux_even (g : ℕ → Fr) {m : ℕ} (h : ℕ) (hm0 : m ≠ 0) (hm : m % 2 = 0) :
    peaksAux H g m h = peaksAux H g (m / 2) (h + 1) := by
  rw [peaksAux, ite_eq_right hm0, ite_eq_right (by omega)]

theorem le_height_of_mem_peaksAux (g : ℕ → Fr) (m : ℕ) :
    ∀ h, ∀ x ∈ peaksAux H g m h, h ≤ x.2 := by
  induction m using Nat.strong_induction_on with
  | _ m ih =>
    intro h x hx
    rcases Nat.eq_zero_or_pos m with rfl | hm
    · simp [peaksAux_zero] at hx
    rcases Nat.mod_two_eq_zero_or_one m with he | ho
    · rw [peaksAux_even g h hm.ne' he] at hx
      have := ih (m / 2) (by omega) (h + 1) x hx
      omega
    · rw [peaksAux_odd g h ho] at hx
      rcases List.mem_cons.1 hx with rfl | hx
      · exact le_rfl
      · have := ih (m / 2) (by omega) (h + 1) x hx
        omega

/-- Appending the subtree of index `m` at height `h` carries like a binary counter. -/
theorem mergePeaks_peaksAux (g : ℕ → Fr) (m : ℕ) :
    ∀ h, mergePeaks H ((subtree H g h m, h) :: peaksAux H g m h) = peaksAux H g (m + 1) h := by
  induction m using Nat.strong_induction_on with
  | _ m ih =>
    intro h
    rcases Nat.eq_zero_or_pos m with rfl | hm
    · rw [peaksAux_zero, mergePeaks_single, peaksAux_odd g h (by norm_num), peaksAux_zero]
    rcases Nat.mod_two_eq_zero_or_one m with he | ho
    · -- no carry: the new peak is alone at its height
      rw [peaksAux_even g h hm.ne' he, peaksAux_odd g h (by omega : (m + 1) % 2 = 1),
        show (m + 1) / 2 = m / 2 by omega, show m + 1 - 1 = m by omega]
      cases hrest : peaksAux H g (m / 2) (h + 1) with
      | nil => exact mergePeaks_single _
      | cons y rest =>
        obtain ⟨l, h'⟩ := y
        have : h + 1 ≤ h' := le_height_of_mem_peaksAux g (m / 2) (h + 1) (l, h')
          (by rw [hrest]; exact List.mem_cons_self ..)
        exact mergePeaks_ne _ _ (by omega) _
    · -- carry: merge with the peak of the same height, then carry one level up
      rw [peaksAux_odd g h ho, mergePeaks_eq, node_subtree_odd g h m ho,
        ih (m / 2) (by omega) (h + 1), peaksAux_even g h (by omega) (by omega),
        show (m + 1) / 2 = m / 2 + 1 by omega]

/-- The peaks of the first `n` leaves of `L`. -/
theorem mmrPeaks_take (L : List Fr) (n : ℕ) (hn : n ≤ L.length) :
    mmrPeaks H (L.take n) = peaksAux H (leafFn L) n 0 := by
  induction n with
  | zero => simp [mmrPeaks, peaksAux_zero]
  | succ n ih =>
    have hlt : n < L.length := by omega
    rw [← List.take_append_getElem hlt, mmrPeaks, List.foldl_append, ← mmrPeaks, ih (by omega)]
    simp only [List.foldl_cons, List.foldl_nil, mmrAppend]
    have : L[n] = subtree H (leafFn L) 0 n := by simp [subtree, leafFn, hlt]
    rw [this, mergePeaks_peaksAux]

/-- The peaks of `n` commitments are given by the binary digits of `n`. -/
theorem mmrPeaks_eq (l : List Fr) : mmrPeaks H l = peaksAux H (leafFn l) l.length 0 := by
  simpa using mmrPeaks_take l l.length le_rfl

/-- Appending a list appends its commitments one by one. -/
theorem mmrPeaks_append (l l' : List Fr) :
    mmrPeaks H (l ++ l') = l'.foldl (mmrAppend H) (mmrPeaks H l) := by
  simp [mmrPeaks, List.foldl_append]

/-! ## `mmr_root` -/

section Root

variable {g : ℕ → Fr} {n : ℕ}

/-- The state of the fold of `mmr_root` at height `a` is the subtree of height `a` holding
the position `n`, the first empty leaf. -/
def RootValid (g : ℕ → Fr) (n : ℕ) (st : Fr × ℕ) : Prop := st.1 = subtree H g st.2 (n / 2 ^ st.2)

theorem lt_succ_div_mul (n a : ℕ) : n < (n / 2 ^ a + 1) * 2 ^ a := by
  have h1 := Nat.div_add_mod n (2 ^ a)
  have h2 := Nat.mod_lt n (show 2 ^ a > 0 by positivity)
  nlinarith

theorem raiseTo_eq (hz : ∀ j, n ≤ j → g j = 0) (t : ℕ) :
    ∀ a root, a ≤ t → root = subtree H g a (n / 2 ^ a) →
      (∀ j, a ≤ j → j < t → n / 2 ^ j % 2 = 0) → raiseTo H root a t = subtree H g t (n / 2 ^ t) := by
  intro a
  induction h : t - a generalizing a with
  | zero =>
    intro root hat hroot _
    have : a = t := by omega
    subst this
    rw [raiseTo, ite_eq_right (lt_irrefl _), hroot]
  | succ k ih =>
    intro root hat hroot hbits
    have hlt : a < t := by omega
    rw [raiseTo, ite_eq_left hlt]
    apply ih (a + 1) (by omega) _ (by omega) _ (fun j h1 h2 => hbits j (by omega) h2)
    have hq := hbits a le_rfl hlt
    have hempty : emptyRoot H a = subtree H g a (n / 2 ^ a + 1) := by
      symm
      apply subtree_eq_emptyRoot
      intro j h1 _
      exact hz j (by have := lt_succ_div_mul n a; omega)
    rw [hroot, hempty, node_subtree_even g a _ hq, Nat.div_div_eq_div_mul, ← pow_succ]

theorem foldl_rootStep_peaksAux (hz : ∀ j, n ≤ j → g j = 0) (hn : n < 2 ^ 32) (m : ℕ) :
    ∀ h (st : Fr × ℕ), m = n / 2 ^ h → st.2 ≤ h → st.2 ≤ 32 → RootValid (H := H) g n st →
      (∀ j, st.2 ≤ j → j < h → n / 2 ^ j % 2 = 0) →
      let st' := (peaksAux H g m h).foldl (rootStep H) st
      st'.2 ≤ 32 ∧ RootValid (H := H) g n st' ∧ ∀ j, st'.2 ≤ j → n / 2 ^ j % 2 = 0 := by
  induction m using Nat.strong_induction_on with
  | _ m ih =>
    intro h st hm hsth hst32 hvalid hbits
    rcases Nat.eq_zero_or_pos m with rfl | hm0
    · simp only [peaksAux_zero, List.foldl_nil]
      refine ⟨hst32, hvalid, fun j hj => ?_⟩
      rcases lt_or_ge j h with hjh | hjh
      · exact hbits j hj hjh
      · have : n / 2 ^ j = 0 := by
          rw [show j = h + (j - h) by omega, pow_add, ← Nat.div_div_eq_div_mul, ← hm]
          simp
        simp [this]
    rcases Nat.mod_two_eq_zero_or_one m with he | ho
    · rw [peaksAux_even g h hm0.ne' he]
      apply ih (m / 2) (by omega) (h + 1) st
        (by rw [hm, Nat.div_div_eq_div_mul, ← pow_succ]) (by omega) hst32 hvalid
      intro j h1 h2
      rcases lt_or_ge j h with hjh | hjh
      · exact hbits j h1 hjh
      · rw [show j = h by omega, ← hm, he]
    · rw [peaksAux_odd g h ho, List.foldl_cons]
      have hh32 : h < 32 := by
        by_contra hc
        have : 2 ^ 32 ≤ 2 ^ h := Nat.pow_le_pow_right (by norm_num) (by omega)
        have : n / 2 ^ h = 0 := Nat.div_eq_of_lt (by omega)
        omega
      have hraise := raiseTo_eq hz h st.2 st.1 hsth hvalid hbits
      apply ih (m / 2) (by omega) (h + 1)
      · rw [hm, Nat.div_div_eq_div_mul, ← pow_succ]
      · simp [rootStep]; omega
      · simp [rootStep]; omega
      · simp only [RootValid, rootStep, show max st.2 h = h by omega]
        rw [hraise, ← hm, node_subtree_odd g h m ho, hm, Nat.div_div_eq_div_mul, ← pow_succ]
      · intro j h1 h2
        simp [rootStep] at h1
        omega

/-- **`mmr_root` is the root of the depth-32 tree** of the leaves `g`, when fewer than `2^32`
positions are filled. -/
theorem mmrRoot_peaksAux (hz : ∀ j, n ≤ j → g j = 0) (hn : n < 2 ^ 32) :
    mmrRoot H (peaksAux H g n 0) = subtree H g 32 0 := by
  obtain ⟨h32, hvalid, hbits⟩ := foldl_rootStep_peaksAux hz hn n 0 (0, 0) (by simp) le_rfl
    (by norm_num) (by simp [RootValid, subtree, hz n le_rfl]) (fun j h1 h2 => by omega)
  rw [mmrRoot, DEPTH, raiseTo_eq hz 32 _ _ h32 hvalid (fun j h1 _ => hbits j h1),
    Nat.div_eq_of_lt hn]

end Root

/-- **`mmr_root` of the MMR of `l` is the root of the depth-32 Merkle tree whose leaves are
the elements of `l` in order, then `0`.** -/
theorem mmrRoot_mmrPeaks (l : List Fr) (hl : l.length < 2 ^ 32) :
    mmrRoot H (mmrPeaks H l) = subtree H (leafFn l) 32 0 := by
  rw [mmrPeaks_eq]
  exact mmrRoot_peaksAux (fun j hj => by simp [leafFn, hj]) hl

/-- **Membership.** Under a collision-free hash, a non-zero leaf proven by a path of length
`32` under the MMR root of `l` is an element of `l`. -/
theorem mem_of_mmrRoot {l : List Fr} (hl : l.length < 2 ^ 32) {cm : Fr} (hcm : cm ≠ 0)
    {p : List (Bool × Fr)} (hp : p.length = 32)
    (h : rootFromPath H cm p = mmrRoot H (mmrPeaks H l)) : cm ∈ l := by
  rw [mmrRoot_mmrPeaks l hl, ← hp] at h
  have := rootFromPath_eq_subtree h
  simp only [leafFn] at this
  rw [List.getD_eq_getElem?_getD] at this
  cases hget : l[pathIndex p]? with
  | none => simp [hget] at this; exact absurd this hcm
  | some x =>
    simp only [hget, Option.getD_some] at this
    subst this
    exact List.mem_of_getElem? hget

/-- Conversely, every element of `l` has a path of length `32` under the MMR root of `l`. -/
theorem exists_path_of_mem {l : List Fr} (hl : l.length < 2 ^ 32) {cm : Fr} (hcm : cm ∈ l) :
    ∃ p : List (Bool × Fr), p.length = 32 ∧ rootFromPath H cm p = mmrRoot H (mmrPeaks H l) := by
  obtain ⟨i, hi, rfl⟩ := List.getElem_of_mem hcm
  refine ⟨pathOf H (leafFn l) 32 i, length_pathOf _ _ _, ?_⟩
  have : l[i] = leafFn l i := by simp [leafFn, hi]
  rw [this, rootFromPath_pathOf, mmrRoot_mmrPeaks l hl, Nat.div_eq_of_lt (by omega)]

/-! ## The full tree -/

theorem peaksAux_pow (g : ℕ → Fr) (k : ℕ) :
    ∀ h, peaksAux H g (2 ^ k) h = [(subtree H g (h + k) 0, h + k)] := by
  induction k with
  | zero =>
    intro h
    rw [pow_zero, peaksAux_odd g h (by norm_num)]
    simp [peaksAux_zero]
  | succ k ih =>
    intro h
    rw [peaksAux_even g h (by positivity) (by rw [pow_succ]; omega),
      show 2 ^ (k + 1) / 2 = 2 ^ k by rw [pow_succ]; omega, ih (h + 1)]
    simp [Nat.add_right_comm, Nat.add_assoc]

theorem raiseTo_emptyRoot (t : ℕ) : ∀ a, a ≤ t → raiseTo H (emptyRoot H a) a t = emptyRoot H t := by
  intro a
  induction h : t - a generalizing a with
  | zero => intro hat; rw [raiseTo, ite_eq_right (by omega), show a = t by omega]
  | succ k ih =>
    intro hat
    rw [raiseTo, ite_eq_left (by omega)]
    exact ih (a + 1) (by omega) (by omega)

/-- With exactly `2^32` commitments, the fold of `mmr_root` ends at height `33`, one level above
the depth-`32` tree: the MMR of a set holds at most `2^32 - 1` commitments. -/
theorem mmrRoot_full (g : ℕ → Fr) :
    mmrRoot H (peaksAux H g (2 ^ 32) 0) = H.node (subtree H g 32 0) (emptyRoot H 32) := by
  rw [peaksAux_pow g 32 0, mmrRoot]
  simp only [zero_add, List.foldl_cons, List.foldl_nil, rootStep, DEPTH]
  have h0 : raiseTo H 0 0 32 = emptyRoot H 32 := raiseTo_emptyRoot 32 0 (by norm_num)
  simp only [h0]
  rw [raiseTo, ite_eq_right (by norm_num)]

end Mantle

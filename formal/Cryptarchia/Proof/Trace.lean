import Cryptarchia.Proof.Local

/-!
# Executions as indexed traces

`wAt es n` is the world after the first `n` events. Time moves only at ticks,
by one slot; the store only grows; node trees hold only stored blocks from the
past; and every honest block is logged with its slot, is never from the future,
and has a valid chain (within the first epoch, given that honest payloads
execute).
-/

namespace Cryptarchia

variable (E : Env) (es : List Event)

/-- The world after the first `n` events. -/
def wAt (n : ℕ) : World := run E World.init (es.take n)

theorem wAt_zero : wAt E es 0 = World.init := by simp [wAt, run]

theorem wAt_succ {n : ℕ} (hn : n < es.length) : wAt E es (n + 1) = (wAt E es n).step E es[n] := by
  simp only [wAt, run]
  rw [List.take_succ, List.getElem?_eq_getElem hn, Option.toList_some, List.foldl_append]
  rfl

theorem wAt_length : wAt E es es.length = run E World.init es := by simp [wAt]

theorem trace_getElem : ∀ (es : List Event) (w : World) (n : ℕ), n ≤ es.length →
    (trace E w es)[n]? = some (run E w (es.take n)) := by
  intro es
  induction es with
  | nil => intro w n hn; simp at hn; subst hn; simp [trace, run]
  | cons e es ih =>
    intro w n hn
    rcases n with _ | n
    · simp [trace, run]
    · simp only [trace, List.getElem?_cons_succ, List.take_succ_cons]
      rw [ih _ n (by simpa using hn)]
      simp [run]

variable {E es}

/-- How an event moves the clock. -/
theorem step_now (w : World) (e : Event) :
    (w.step E e).now = w.now + (match e with | .tick => 1 | _ => 0) := by
  cases e with
  | tick =>
    simp only [World.step]
    have : ∀ (l : List ℕ) (w₀ : World), (l.foldl (World.lead E) w₀).now = w₀.now := by
      intro l; induction l with
      | nil => intro; rfl
      | cons i is ih =>
        intro w₀; simp only [List.foldl_cons]; rw [ih]
        unfold World.lead; split
        · rfl
        · split
          · rfl
          · rfl
    rw [this]
  | deliver i b => simp only [World.step]; split <;> rfl
  | create B => simp only [World.step]; split <;> rfl

theorem now_mono {n m : ℕ} (hnm : n ≤ m) (hm : m ≤ es.length) : (wAt E es n).now ≤ (wAt E es m).now := by
  induction m with
  | zero => have : n = 0 := by omega
            subst this; rfl
  | succ m ih =>
    rcases Nat.eq_or_lt_of_le hnm with h | h
    · rw [h]
    · rw [wAt_succ E es (by omega), step_now]
      have := ih (by omega) (by omega); omega

theorem wAt_ok (hord : E.OrderOK) (n : ℕ) : WorldOK E (wAt E es n) :=
  (run_ok E hord _ _ (init_ok E)).1

theorem store_mono (hord : E.OrderOK) {n m : ℕ} (hnm : n ≤ m) :
    StoreExt (wAt E es n).st (wAt E es m).st := by
  have hd : (es.take m).take n = es.take n := by rw [List.take_take, min_eq_left hnm]
  unfold wAt
  conv_rhs => rw [← List.take_append_drop n (es.take m), hd]
  simp only [run, List.foldl_append]
  exact (run_ok E hord _ _ (wAt_ok hord n)).2.1

theorem height_mono_idx (hord : E.OrderOK) {n m : ℕ} (hnm : n ≤ m) (j : ℕ) :
    height (wAt E es n).st ((wAt E es n).node j).cloc ≤ height (wAt E es m).st ((wAt E es m).node j).cloc := by
  have hd : (es.take m).take n = es.take n := by rw [List.take_take, min_eq_left hnm]
  unfold wAt
  conv_rhs => rw [← List.take_append_drop n (es.take m), hd]
  simp only [run, List.foldl_append]
  exact (run_ok E hord _ _ (wAt_ok hord n)).2.2 j

end Cryptarchia

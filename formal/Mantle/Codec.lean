import Mathlib

/-!
# Verified codecs

A `Codec α` is an encoder and a decoder for the well-formed values of `α`, with the two laws
that make an encoding **canonical** in the sense of the specification ("every valid value has
exactly one byte representation, and every byte string decodes to at most one value"):

* `dec_enc`: decoding the encoding of a well-formed value, followed by any bytes, returns it
  and those bytes;
* `enc_dec`: whatever the decoder accepts is a well-formed value followed by the rest: the
  bytes it consumed are exactly the encoding of what it returned.

Consequences: `enc_injective` (distinct values have distinct encodings), `decodeAll_iff`
(a frame decodes exactly to the values it encodes), `prefix_free`.

The combinators build codecs whose laws follow from those of their parts: little-endian
unsigned integers (`uint`), fixed byte strings (`bytes`), length-prefixed byte strings and
lists with a bound on the length (`varBytes`, `list`), lists of a known length (`exactList`),
dependent pairs (`bind`), filters checked by the decoder (`filter`), bit masks (`bitmask`) and
isomorphisms onto structures (`iso`).
-/

namespace Mantle.Encoding

abbrev Bytes := List UInt8

/-- An encoder and a decoder for the well-formed values of `α`, inverse to each other. -/
structure Codec (α : Type) where
  wf : α → Prop
  enc : α → Bytes
  dec : Bytes → Option (α × Bytes)
  dec_enc : ∀ {a : α} (r : Bytes), wf a → dec (enc a ++ r) = some (a, r)
  enc_dec : ∀ {b : Bytes} {a : α} {r : Bytes}, dec b = some (a, r) → wf a ∧ b = enc a ++ r

namespace Codec

variable {α β : Type}

/-- Distinct well-formed values have distinct encodings. -/
theorem enc_injective (C : Codec α) {a b : α} (ha : C.wf a) (hb : C.wf b)
    (h : C.enc a = C.enc b) : a = b := by
  have h1 := C.dec_enc [] ha
  have h2 := C.dec_enc [] hb
  rw [h, h2] at h1
  simp only [Option.some.injEq, Prod.mk.injEq, and_true] at h1
  exact h1.symm

/-- No encoding is a proper prefix of another. -/
theorem prefix_free (C : Codec α) {a b : α} {r r' : Bytes} (ha : C.wf a) (hb : C.wf b)
    (h : C.enc a ++ r = C.enc b ++ r') : a = b ∧ r = r' := by
  have h1 := C.dec_enc r ha
  have h2 := C.dec_enc r' hb
  rw [h, h2] at h1
  simp only [Option.some.injEq, Prod.mk.injEq] at h1
  exact ⟨h1.1.symm, h1.2.symm⟩

/-- Decoding a whole frame: no byte may be left. -/
def decodeAll (C : Codec α) (b : Bytes) : Option α :=
  match C.dec b with
  | some (a, []) => some a
  | _ => none

/-- **A frame decodes to `a` iff it is the encoding of the well-formed `a`.** -/
theorem decodeAll_iff (C : Codec α) {b : Bytes} {a : α} :
    C.decodeAll b = some a ↔ C.wf a ∧ b = C.enc a := by
  constructor
  · intro h
    unfold decodeAll at h
    split at h
    · rename_i a' h'
      simp only [Option.some.injEq] at h
      subst h
      obtain ⟨hw, hb⟩ := C.enc_dec h'
      exact ⟨hw, by simpa using hb⟩
    · simp at h
  · rintro ⟨hw, rfl⟩
    have := C.dec_enc [] hw
    simp only [List.append_nil] at this
    simp [decodeAll, this]

/-! ## Combinators -/

/-- A dependent pair: the codec of the second component may depend on the first. -/
def bind (A : Codec α) (B : α → Codec β) : Codec (α × β) where
  wf p := A.wf p.1 ∧ (B p.1).wf p.2
  enc p := A.enc p.1 ++ (B p.1).enc p.2
  dec b := (A.dec b).bind fun ar => ((B ar.1).dec ar.2).map fun xr => ((ar.1, xr.1), xr.2)
  dec_enc := by
    intro p r h
    rw [List.append_assoc, A.dec_enc _ h.1]
    simp [(B p.1).dec_enc r h.2]
  enc_dec := by
    intro b p r h
    simp only [Option.bind_eq_some_iff, Option.map_eq_some_iff] at h
    obtain ⟨⟨a, r1⟩, h1, ⟨x, r2⟩, h2, he⟩ := h
    simp only [Prod.mk.injEq] at he
    obtain ⟨rfl, rfl⟩ := he
    obtain ⟨w1, rfl⟩ := A.enc_dec h1
    obtain ⟨w2, rfl⟩ := (B a).enc_dec h2
    exact ⟨⟨w1, w2⟩, by simp⟩

/-- A pair. -/
def pair (A : Codec α) (B : Codec β) : Codec (α × β) := bind A fun _ => B

/-- Values of `β` encoded through `α`: `f` decodes, `g` encodes, and `P` is what `β` adds to
the well-formedness of `α` (such as being a given constructor). -/
def iso (A : Codec α) (f : α → β) (g : β → α) (P : β → Prop)
    (hfg : ∀ b, P b → f (g b) = b) (hgf : ∀ a, A.wf a → g (f a) = a ∧ P (f a)) : Codec β where
  wf b := A.wf (g b) ∧ P b
  enc b := A.enc (g b)
  dec b := (A.dec b).map fun ar => (f ar.1, ar.2)
  dec_enc := by
    intro b r h
    simp [A.dec_enc r h.1, hfg b h.2]
  enc_dec := by
    intro b x r h
    simp only [Option.map_eq_some_iff, Prod.mk.injEq] at h
    obtain ⟨⟨a, r'⟩, h1, rfl, rfl⟩ := h
    obtain ⟨w, rfl⟩ := A.enc_dec h1
    obtain ⟨e, hp⟩ := hgf a w
    exact ⟨⟨by rw [e]; exact w, hp⟩, by rw [e]⟩

/-- A codec whose decoder also checks `p`. -/
def filter (A : Codec α) (p : α → Prop) [DecidablePred p] : Codec α where
  wf a := A.wf a ∧ p a
  enc := A.enc
  dec b := (A.dec b).bind fun ar => if p ar.1 then some ar else none
  dec_enc := by
    intro a r h
    simp [A.dec_enc r h.1, h.2]
  enc_dec := by
    intro b a r h
    simp only [Option.bind_eq_some_iff] at h
    obtain ⟨⟨a', r'⟩, h1, h2⟩ := h
    split_ifs at h2 with hp
    simp only [Option.some.injEq, Prod.mk.injEq] at h2
    obtain ⟨rfl, rfl⟩ := h2
    obtain ⟨w, rfl⟩ := A.enc_dec h1
    exact ⟨⟨w, hp⟩, rfl⟩

/-- The empty encoding of the unit value (`EmptyProof = 0Byte`). -/
def empty : Codec Unit where
  wf _ := True
  enc _ := []
  dec b := some ((), b)
  dec_enc := by intros; rfl
  enc_dec := by
    intro b a r h
    simp only [Option.some.injEq, Prod.mk.injEq] at h
    exact ⟨trivial, by simp [h.2]⟩

/-! ### Little-endian unsigned integers -/

/-- The `k` little-endian bytes of `n`. -/
def leBytes : ℕ → ℕ → Bytes
  | 0, _ => []
  | k + 1, n => (n % 256).toUInt8 :: leBytes k (n / 256)

/-- Byte-lexicographic order, first byte first. -/
def lexLe : Bytes → Bytes → Bool
  | [], _ => true
  | _ :: _, [] => false
  | x :: a, y :: b => x < y || (x == y && lexLe a b)

/-- Read a `k`-byte little-endian integer. -/
def readLE : ℕ → Bytes → Option (ℕ × Bytes)
  | 0, b => some (0, b)
  | _ + 1, [] => none
  | k + 1, x :: b => (readLE k b).map fun mr => (x.toNat + 256 * mr.1, mr.2)

theorem readLE_leBytes (k : ℕ) : ∀ (n : ℕ) (r : Bytes), n < 256 ^ k →
    readLE k (leBytes k n ++ r) = some (n, r) := by
  induction k with
  | zero => intro n r h; simp at h; subst h; rfl
  | succ k ih =>
    intro n r h
    simp only [leBytes, List.cons_append, readLE]
    rw [ih (n / 256) r (by rw [pow_succ] at h; omega)]
    simp only [Option.map_some, Option.some.injEq, Prod.mk.injEq, and_true]
    have : ((n % 256).toUInt8).toNat = n % 256 := by
      simp [Nat.toUInt8]
    omega

theorem readLE_spec (k : ℕ) : ∀ {b : Bytes} {n : ℕ} {r : Bytes}, readLE k b = some (n, r) →
    n < 256 ^ k ∧ b = leBytes k n ++ r := by
  induction k with
  | zero =>
    intro b n r h
    simp only [readLE, Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    simp [leBytes]
  | succ k ih =>
    intro b n r h
    cases b with
    | nil => simp [readLE] at h
    | cons x b =>
      simp only [readLE, Option.map_eq_some_iff, Prod.mk.injEq] at h
      obtain ⟨⟨m, r'⟩, h1, rfl, rfl⟩ := h
      obtain ⟨hm, rfl⟩ := ih h1
      have hx := x.toNat_lt
      refine ⟨by rw [pow_succ]; simp only at hm ⊢; omega, ?_⟩
      simp only [leBytes, List.cons_append, List.cons.injEq]
      constructor
      · apply UInt8.toNat_inj.1
        simp [Nat.toUInt8]
      · congr 2
        omega

/-- A `k`-byte little-endian unsigned integer (`Byte`, `UINT16`, `UINT32`, `UINT64`, and the
32-, 64- and 128-byte strings read as integers). -/
def uint (k : ℕ) : Codec ℕ where
  wf n := n < 256 ^ k
  enc := leBytes k
  dec := readLE k
  dec_enc := fun r h => readLE_leBytes k _ r h
  enc_dec := fun h => readLE_spec k h

theorem length_leBytes (k n : ℕ) : (leBytes k n).length = k := by
  induction k generalizing n with
  | zero => rfl
  | succ k ih => simp [leBytes, ih]

/-! ### Byte strings and lists -/

/-- `n` raw bytes. -/
def bytes (n : ℕ) : Codec Bytes where
  wf b := b.length = n
  enc b := b
  dec b := if n ≤ b.length then some (b.take n, b.drop n) else none
  dec_enc := by
    intro a r h
    subst h
    simp
  enc_dec := by
    intro b a r h
    split_ifs at h with hn
    simp only [Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    exact ⟨by simp [hn], (List.take_append_drop _ _).symm⟩

/-- Decode `n` values in a row. -/
def decN (A : Codec α) : ℕ → Bytes → Option (List α × Bytes)
  | 0, r => some ([], r)
  | n + 1, r => (A.dec r).bind fun ar => (decN A n ar.2).map fun lr => (ar.1 :: lr.1, lr.2)

theorem decN_enc (A : Codec α) (l : List α) (r : Bytes) (h : ∀ x ∈ l, A.wf x) :
    decN A l.length ((l.map A.enc).flatten ++ r) = some (l, r) := by
  induction l with
  | nil => rfl
  | cons a l ih =>
    simp only [List.length_cons, List.map_cons, List.flatten_cons, List.append_assoc, decN]
    rw [A.dec_enc _ (h a (by simp))]
    simp [ih fun x hx => h x (by simp [hx])]

theorem decN_spec (A : Codec α) (n : ℕ) : ∀ {b : Bytes} {l : List α} {r : Bytes},
    decN A n b = some (l, r) → l.length = n ∧ (∀ x ∈ l, A.wf x) ∧ b = (l.map A.enc).flatten ++ r := by
  induction n with
  | zero =>
    intro b l r h
    simp only [decN, Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    simp
  | succ n ih =>
    intro b l r h
    simp only [decN, Option.bind_eq_some_iff, Option.map_eq_some_iff, Prod.mk.injEq] at h
    obtain ⟨⟨a, r1⟩, h1, ⟨l', r2⟩, h2, rfl, rfl⟩ := h
    obtain ⟨w, rfl⟩ := A.enc_dec h1
    obtain ⟨hl, hw, rfl⟩ := ih h2
    refine ⟨by simp [hl], ?_, by simp⟩
    intro x hx
    rcases List.mem_cons.1 hx with rfl | hx
    · exact w
    · exact hw x hx

/-- Exactly `n` values, without a count (`IC = 4G1Point`, the proofs of a step). -/
def exactList (n : ℕ) (A : Codec α) : Codec (List α) where
  wf l := l.length = n ∧ ∀ x ∈ l, A.wf x
  enc l := (l.map A.enc).flatten
  dec := decN A n
  dec_enc := by
    intro l r h
    rw [← h.1]
    exact decN_enc A l r h.2
  enc_dec := by
    intro b l r h
    obtain ⟨h1, h2, h3⟩ := decN_spec A n h
    exact ⟨⟨h1, h2⟩, h3⟩

/-- A list prefixed by its `k`-byte count, of at most `max` elements. -/
def list (k max : ℕ) (hmax : max < 256 ^ k) (A : Codec α) : Codec (List α) where
  wf l := l.length ≤ max ∧ ∀ x ∈ l, A.wf x
  enc l := leBytes k l.length ++ (l.map A.enc).flatten
  dec b := (readLE k b).bind fun nr =>
    if nr.1 ≤ max then decN A nr.1 nr.2 else none
  dec_enc := by
    intro l r h
    rw [List.append_assoc, readLE_leBytes k _ _ (lt_of_le_of_lt h.1 hmax)]
    simp [h.1, decN_enc A l r h.2]
  enc_dec := by
    intro b l r h
    simp only [Option.bind_eq_some_iff] at h
    obtain ⟨⟨n, r1⟩, h1, h2⟩ := h
    split_ifs at h2 with hn
    obtain ⟨-, rfl⟩ := readLE_spec k h1
    obtain ⟨hl, hw, rfl⟩ := decN_spec A n h2
    exact ⟨⟨by omega, hw⟩, by simp [hl]⟩

/-- A byte string prefixed by its `k`-byte length, of at most `max` bytes. -/
def varBytes (k max : ℕ) (hmax : max < 256 ^ k) : Codec Bytes :=
  iso (list k max hmax (bytes 1)) (fun l => l.flatten) (fun b => b.map fun x => [x])
    (fun _ => True)
    (by intro b _; induction b <;> simp_all)
    (by
      intro l hl
      refine ⟨?_, trivial⟩
      have : ∀ x ∈ l, x.length = 1 := hl.2
      clear hl
      induction l with
      | nil => rfl
      | cons x l ih =>
        have hx := this x (by simp)
        obtain ⟨y, rfl⟩ := List.length_eq_one_iff.1 hx
        simp [ih fun z hz => this z (by simp [hz])])

/-! ### Bit masks -/

/-- The bits of a list of flags, least significant first. -/
def boolsToNat : List Bool → ℕ
  | [] => 0
  | b :: l => (if b then 1 else 0) + 2 * boolsToNat l

/-- The `m` low bits of `x`, least significant first. -/
def natToBools : ℕ → ℕ → List Bool
  | 0, _ => []
  | m + 1, x => (x % 2 = 1) :: natToBools m (x / 2)

theorem boolsToNat_lt (l : List Bool) : boolsToNat l < 2 ^ l.length := by
  induction l with
  | nil => simp [boolsToNat]
  | cons b l ih => simp only [boolsToNat, List.length_cons, pow_succ]; split_ifs <;> omega

theorem natToBools_boolsToNat (l : List Bool) : natToBools l.length (boolsToNat l) = l := by
  induction l with
  | nil => rfl
  | cons b l ih =>
    have h1 : ((if b then 1 else 0) + 2 * boolsToNat l) / 2 = boolsToNat l := by
      split_ifs <;> omega
    simp only [List.length_cons, natToBools, boolsToNat, h1, ih, List.cons.injEq, and_true]
    cases b <;> simp

theorem boolsToNat_natToBools (m : ℕ) : ∀ x, x < 2 ^ m → boolsToNat (natToBools m x) = x := by
  induction m with
  | zero => intro x h; simp at h; subst h; rfl
  | succ m ih =>
    intro x h
    simp only [natToBools, boolsToNat]
    rw [ih (x / 2) (by rw [pow_succ] at h; omega)]
    split_ifs with hx <;> simp at hx <;> omega

theorem length_natToBools (m x : ℕ) : (natToBools m x).length = m := by
  induction m generalizing x with
  | zero => rfl
  | succ m ih => simp [natToBools, ih]

/-- `m ≤ 8` flags in one byte, the bits from `m` up being `0` (rejected otherwise). -/
def bitmask (m : ℕ) : Codec (List Bool) :=
  iso (filter (uint 1) (· < 2 ^ m)) (natToBools m) boolsToNat (fun l => l.length = m)
    (by intro l hl; rw [← hl]; exact natToBools_boolsToNat l)
    (by
      intro x hx
      exact ⟨boolsToNat_natToBools m x hx.2, length_natToBools m x⟩)

theorem bitmask_wf {m : ℕ} (hm : m ≤ 8) {l : List Bool} (h : l.length = m) :
    (bitmask m).wf l := by
  refine ⟨⟨?_, ?_⟩, h⟩
  · show boolsToNat l < 256 ^ 1
    have := boolsToNat_lt l
    have : 2 ^ l.length ≤ 2 ^ 8 := Nat.pow_le_pow_right (by norm_num) (by omega)
    simp only [pow_one]; omega
  · show boolsToNat l < 2 ^ m
    rw [← h]; exact boolsToNat_lt l

/-- The empty list, encoded by nothing. -/
def nil : Codec (List α) where
  wf l := l = []
  enc _ := []
  dec b := some ([], b)
  dec_enc := by intro l r h; subst h; rfl
  enc_dec := by
    intro b l r h
    simp only [Option.some.injEq, Prod.mk.injEq] at h
    obtain ⟨rfl, rfl⟩ := h
    exact ⟨rfl, rfl⟩

/-- One value per element of `gs`, each with the codec its element selects, without a count
(the proofs of the Operations, of the steps of an inscription). -/
def depList {γ : Type} [Inhabited α] (C : γ → Codec α) : List γ → Codec (List α)
  | [] => nil
  | g :: gs => iso (pair (C g) (depList C gs)) (fun p => p.1 :: p.2)
      (fun l => (l.headD default, l.tail)) (fun l => l ≠ [])
      (by intro l hl; cases l with
        | nil => exact absurd rfl hl
        | cons a l => rfl)
      (by intro p _; exact ⟨rfl, by simp⟩)

end Codec

end Mantle.Encoding

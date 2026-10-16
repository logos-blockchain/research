import Mathlib

/-!
# Idealized cryptography, notes, commitments and nullifiers

Field elements of BN254 are represented by their canonical natural numbers. The ZK hash
`zkhash` is idealized as **collision free** (`Function.Injective`) and never `0`: this is the
symbolic model of a collision-resistant hash, under which every binding argument of the
specification becomes an equality argument. Nothing else is assumed about the hash, and no
axiom is added: the assumptions are fields of `Hash`, and `Hash.model` shows they are
satisfiable.

`FiniteField(x)` of the specification is the identity on the naturals used here (values,
lengths and domain separation tags are far below `p`), and a domain separation tag is the
little-endian integer of its ASCII bytes, as `FiniteField(b"...", byte_order="little")`.

Notes (Mantle, *Notes*; RFC-481 §1) carry five fields, and

* `noteCm`  is `derive_note_cm`:  `zkhash(NOTE_CM_V1, value, nonce, public_key, program, data)`;
* `noteNf`  is `derive_note_nf`:  `zkhash(NOTE_NF_V1, cm, sk)`;
* `kdf`     derives a public key: `zkhash(KDF, sk)`;
* `noteNonce` is `derive_note_nonce(op_id, output_number, value, public_key)`.

Binding lemmas: `noteCm_injective`, `noteNf_injective`, `kdf_injective`, and the facts that
a nullifier, a commitment and a key are never `0`.
-/

namespace Mantle

/-- A field element of BN254, by its canonical representative. -/
notation "Fr" => ℕ

/-- `FiniteField(bytes, byte_order="little")` for a short ASCII string (an ASCII character is
its own UTF-8 byte). -/
def tag (s : String) : Fr :=
  s.toList.foldr (fun c acc => c.toNat + 256 * acc) 0

/-- Domain separation tags of the specification. -/
def NOTE_CM_V1 : Fr := tag "NOTE_CM_V1"
def NOTE_NF_V1 : Fr := tag "NOTE_NF_V1"
def NOTE_NONCE_V1 : Fr := tag "NOTE_NONCE_V1"
def KDF : Fr := tag "KDF"
def CHANNEL_STEP_V1 : Fr := tag "CHANNEL_STEP_V1"
def PROGRAM_PAYMENT_V1 : Fr := tag "PROGRAM_PAYMENT_V1"
def PROGRAM_PAYMENTS_V1 : Fr := tag "PROGRAM_PAYMENTS_V1"
def PROGRAM_SPEND_NOTES_V1 : Fr := tag "PROGRAM_SPEND_NOTES_V1"
def NULLIFIER_IMT_LEAF_V1 : Fr := tag "NULLIFIER_IMT_LEAF_V1"
def ELIGIBLE_SET_LEAF_V1 : Fr := tag "ELIGIBLE_SET_LEAF_V1"

/-- The idealized ZK hash: collision free and never `0`. -/
structure Hash where
  zkhash : List Fr → Fr
  injective : Function.Injective zkhash
  ne_zero : ∀ l, zkhash l ≠ 0

/-- The hypotheses of `Hash` are satisfiable (so no theorem below is vacuous): hash a list
of naturals by its `Encodable` code, plus one. -/
def Hash.model : Hash where
  zkhash l := Encodable.encode l + 1
  injective _ _ h := Encodable.encode_injective (Nat.succ_injective h)
  ne_zero _ := Nat.succ_ne_zero _

/-- `UINT64_MAX + 1`: `TokenValue` is a `uint64`. -/
def TOKEN_BOUND : ℕ := 2 ^ 64

/-- `class Note` (Mantle, *Notes*). `program = 0` and `data = 0` for a user note. -/
structure Note where
  value : ℕ
  nonce : Fr
  publicKey : Fr
  program : Fr := 0
  data : Fr := 0
deriving DecidableEq

namespace Note

/-- A user note: moved by its holder alone. -/
def IsUser (n : Note) : Prop := n.program = 0 ∧ n.data = 0

instance (n : Note) : Decidable n.IsUser := inferInstanceAs (Decidable (_ ∧ _))

end Note

variable (H : Hash)

/-- The two-to-one node hash of the Merkle trees: `zkhash(left, right)`. -/
def Hash.node (l r : Fr) : Fr := H.zkhash [l, r]

/-- `derive_note_cm`. -/
def noteCm (n : Note) : Fr :=
  H.zkhash [NOTE_CM_V1, n.value, n.nonce, n.publicKey, n.program, n.data]

/-- `derive_note_nf`. -/
def noteNf (cm sk : Fr) : Fr := H.zkhash [NOTE_NF_V1, cm, sk]

/-- The public key of a secret key, `zkhash(KDF, sk)`. -/
def kdf (sk : Fr) : Fr := H.zkhash [KDF, sk]

/-- `derive_note_nonce(op_id, output_number, value, public_key)`. -/
def noteNonce (opId outputNumber value publicKey : Fr) : Fr :=
  H.zkhash [NOTE_NONCE_V1, opId, outputNumber, value, publicKey]

variable {H}

theorem Hash.node_injective {l r l' r' : Fr} (h : H.node l r = H.node l' r') :
    l = l' ∧ r = r' := by
  have := H.injective h
  simp only [List.cons.injEq, and_true] at this
  exact this

theorem noteCm_injective : Function.Injective (noteCm H) := by
  intro a b h
  have := H.injective h
  simp only [List.cons.injEq, and_true, true_and] at this
  obtain ⟨h1, h2, h3, h4, h5⟩ := this
  cases a; cases b; simp_all

theorem noteNf_injective {cm sk cm' sk' : Fr} (h : noteNf H cm sk = noteNf H cm' sk') :
    cm = cm' ∧ sk = sk' := by
  have := H.injective h
  simp only [List.cons.injEq, and_true, true_and] at this
  exact this

theorem kdf_injective : Function.Injective (kdf H) := by
  intro a b h
  have := H.injective h
  simp only [List.cons.injEq, and_true, true_and] at this
  exact this

theorem noteCm_ne_zero (n : Note) : noteCm H n ≠ 0 := H.ne_zero _

theorem noteNf_ne_zero (cm sk : Fr) : noteNf H cm sk ≠ 0 := H.ne_zero _

theorem node_ne_zero (l r : Fr) : H.node l r ≠ 0 := H.ne_zero _

/-- A commitment determines its note, and so whether it is a user note. -/
theorem noteCm_eq_iff {a b : Note} : noteCm H a = noteCm H b ↔ a = b :=
  noteCm_injective.eq_iff

/-- A program note never shares the commitment of a user note. -/
theorem noteCm_ne_of_program {a b : Note} (ha : a.program ≠ 0) (hb : b.IsUser) :
    noteCm H a ≠ noteCm H b := by
  intro h
  exact ha ((noteCm_injective h).symm ▸ hb.1)

/-! ## The unique opening of a commitment

Under a collision-free hash, a commitment has at most one opening, and a key at most one
secret key. These are the "ghost" values of the ledger: they are functions of the hash only,
not of the state. -/

open Classical in
/-- The note a commitment opens to, if any. -/
noncomputable def opening (H : Hash) (cm : Fr) : Option Note :=
  if h : ∃ n, noteCm H n = cm then some h.choose else none

open Classical in
/-- The secret key of a public key, if any. -/
noncomputable def secretKey (H : Hash) (pk : Fr) : Option Fr :=
  if h : ∃ sk, kdf H sk = pk then some h.choose else none

theorem opening_noteCm (n : Note) : opening H (noteCm H n) = some n := by
  have h : ∃ m, noteCm H m = noteCm H n := ⟨n, rfl⟩
  rw [opening, dite_eq_left h]
  exact congrArg some (noteCm_injective h.choose_spec)

theorem secretKey_kdf (sk : Fr) : secretKey H (kdf H sk) = some sk := by
  have h : ∃ s, kdf H s = kdf H sk := ⟨sk, rfl⟩
  rw [secretKey, dite_eq_left h]
  exact congrArg some (kdf_injective h.choose_spec)

/-- The value of the note behind a commitment, `0` if it opens to none. -/
noncomputable def cmValue (H : Hash) (cm : Fr) : ℕ := ((opening H cm).map Note.value).getD 0

theorem cmValue_noteCm (n : Note) : cmValue H (noteCm H n) = n.value := by
  simp [cmValue, opening_noteCm]

/-- The nullifier its holder derives for a commitment, if the commitment opens to a note
whose public key has a secret key. -/
noncomputable def cmNf (H : Hash) (cm : Fr) : Option Fr :=
  (opening H cm).bind fun n => (secretKey H n.publicKey).map (noteNf H cm)

theorem cmNf_of_kdf (n : Note) (sk : Fr) (hpk : n.publicKey = kdf H sk) :
    cmNf H (noteCm H n) = some (noteNf H (noteCm H n) sk) := by
  simp [cmNf, opening_noteCm, hpk, secretKey_kdf]

/-- The nullifier of a commitment determines it. -/
theorem cmNf_injective {cm cm' nf : Fr} (h : cmNf H cm = some nf) (h' : cmNf H cm' = some nf) :
    cm = cm' := by
  simp only [cmNf, Option.bind_eq_some_iff, Option.map_eq_some_iff] at h h'
  obtain ⟨_, _, _, _, rfl⟩ := h
  obtain ⟨_, _, _, _, he⟩ := h'
  exact (noteNf_injective he).1.symm

end Mantle

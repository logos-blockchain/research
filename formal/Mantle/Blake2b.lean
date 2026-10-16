import Mathlib

/-!
# BLAKE2b

A direct implementation of BLAKE2b (RFC 7693), unkeyed, with any digest length, used to check
the test vectors of the specification (`MantleTest/Vectors.lean`): `op_id`, `mantle_txhash`
and `declaration_id`. It is executable code, checked against the RFC's own vectors, not a
proof.
-/

namespace Mantle.Blake2b

def IV : Array UInt64 := #[0x6a09e667f3bcc908, 0xbb67ae8584caa73b, 0x3c6ef372fe94f82b,
  0xa54ff53a5f1d36f1, 0x510e527fade682d1, 0x9b05688c2b3e6c1f, 0x1f83d9abfb41bd6b,
  0x5be0cd19137e2179]

def SIGMA : Array (Array Nat) := #[
  #[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
  #[14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
  #[11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
  #[7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
  #[9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
  #[2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
  #[12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
  #[13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
  #[6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
  #[10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0]]

def rotr (x : UInt64) (n : UInt64) : UInt64 := (x >>> n) ||| (x <<< (64 - n))

def G (v : Array UInt64) (a b c d : Nat) (x y : UInt64) : Array UInt64 := Id.run do
  let mut v := v
  v := v.set! a (v[a]! + v[b]! + x)
  v := v.set! d (rotr (v[d]! ^^^ v[a]!) 32)
  v := v.set! c (v[c]! + v[d]!)
  v := v.set! b (rotr (v[b]! ^^^ v[c]!) 24)
  v := v.set! a (v[a]! + v[b]! + y)
  v := v.set! d (rotr (v[d]! ^^^ v[a]!) 16)
  v := v.set! c (v[c]! + v[d]!)
  v := v.set! b (rotr (v[b]! ^^^ v[c]!) 63)
  return v

/-- The compression function on one block of sixteen words. -/
def compress (h : Array UInt64) (m : Array UInt64) (t : Nat) (last : Bool) : Array UInt64 :=
  Id.run do
    let mut v := h ++ IV
    v := v.set! 12 (v[12]! ^^^ (t % 2 ^ 64).toUInt64)
    v := v.set! 13 (v[13]! ^^^ (t / 2 ^ 64).toUInt64)
    if last then v := v.set! 14 (v[14]! ^^^ 0xFFFFFFFFFFFFFFFF)
    for i in [0:12] do
      let s := SIGMA[i % 10]!
      v := G v 0 4 8 12 m[s[0]!]! m[s[1]!]!
      v := G v 1 5 9 13 m[s[2]!]! m[s[3]!]!
      v := G v 2 6 10 14 m[s[4]!]! m[s[5]!]!
      v := G v 3 7 11 15 m[s[6]!]! m[s[7]!]!
      v := G v 0 5 10 15 m[s[8]!]! m[s[9]!]!
      v := G v 1 6 11 12 m[s[10]!]! m[s[11]!]!
      v := G v 2 7 8 13 m[s[12]!]! m[s[13]!]!
      v := G v 3 4 9 14 m[s[14]!]! m[s[15]!]!
    let mut h := h
    for i in [0:8] do
      h := h.set! i (h[i]! ^^^ v[i]! ^^^ v[i + 8]!)
    return h

/-- The sixteen little-endian words of a 128-byte block. -/
def words (block : List UInt8) : Array UInt64 :=
  (List.range 16).toArray.map fun i =>
    (List.range 8).foldr (fun j acc => (acc <<< 8) ||| (block.getD (8 * i + j) 0).toUInt64) 0

/-- BLAKE2b with an `nn`-byte digest. -/
def hash (nn : Nat) (msg : List UInt8) : List UInt8 := Id.run do
  let mut h := IV.set! 0 (IV[0]! ^^^ 0x01010000 ^^^ nn.toUInt64)
  let n := msg.length
  let blocks := if n = 0 then 1 else (n + 127) / 128
  for i in [0:blocks - 1] do
    h := compress h (words (msg.drop (128 * i))) (128 * (i + 1)) false
  h := compress h (words (msg.drop (128 * (blocks - 1)))) n true
  let out := (List.range 8).flatMap fun i =>
    (List.range 8).map fun j => (h[i]! >>> (8 * j).toUInt64).toUInt8
  return out.take nn

/-- BLAKE2b-256. -/
def hash256 (msg : List UInt8) : List UInt8 := hash 32 msg

/-! ## Hexadecimal -/

def hexDigit (c : Char) : Nat :=
  if '0' ≤ c ∧ c ≤ '9' then c.toNat - '0'.toNat
  else if 'a' ≤ c ∧ c ≤ 'f' then c.toNat - 'a'.toNat + 10
  else if 'A' ≤ c ∧ c ≤ 'F' then c.toNat - 'A'.toNat + 10 else 0

/-- The bytes of a hexadecimal string, with or without `0x`. -/
def ofHex (s : String) : List UInt8 :=
  let cs := if s.startsWith "0x" then s.toList.drop 2 else s.toList
  let rec go : List Char → List UInt8
    | a :: b :: rest => (16 * hexDigit a + hexDigit b).toUInt8 :: go rest
    | _ => []
  go cs

/-- The bytes of an ASCII string. -/
def ascii (s : String) : List UInt8 := s.toList.map fun c => c.toNat.toUInt8

end Mantle.Blake2b

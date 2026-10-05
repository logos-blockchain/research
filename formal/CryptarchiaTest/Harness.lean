import Cryptarchia

/-! Helpers for the differential tests (`tools/difftest/cryptarchia_diff.py`). -/

namespace Cryptarchia.Test

/-- A block from `(id, parent, slot, uncles)`, each uncle `(id, parent, slot)`. -/
def mkBlock (b : ℕ × ℕ × ℕ × List (ℕ × ℕ × ℕ)) : Block :=
  { hdr := { id := b.1, parent := b.2.1, slot := b.2.2.1, note := 0, signer := .adv, payload := 0 }
    uncles := b.2.2.2.map (fun u => { id := u.1, parent := u.2.1, slot := u.2.2, note := 0,
                                      signer := .adv, payload := 0 }) }

/-- A store from a list of blocks. -/
def mkStore (bs : List (ℕ × ℕ × ℕ × List (ℕ × ℕ × ℕ))) : Store :=
  fun i => (bs.find? (fun b => b.1 = i)).map mkBlock

/-- A small configuration for tests (the slot geometry scaled down). -/
def cfg (k W fDen : ℕ) : Config :=
  { Config.spec with k := k, W := W, fNum := 1, fDen := fDen, fP := 1000 / fDen }

end Cryptarchia.Test

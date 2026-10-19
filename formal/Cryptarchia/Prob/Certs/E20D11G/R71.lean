module

public import Cryptarchia.Prob.Certs.E20D11G.R63
meta import Cryptarchia.Prob.Certs.E20D11G.R63

/-! # E20D11G: (group, representative) entries 781 to 791, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r71_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 253 (0, 0))
def r71_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 254 (0, 0))
def r71_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 255 (0, 0))
def r71_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 256 (0, 0))
def r71_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 257 (0, 0))
def r71_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 258 (0, 0))
def r71_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 259 (0, 0))
def r71_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 260 (0, 0))
def r71_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 261 (0, 0))
def r71_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 262 (0, 0))
def r71_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 263 (0, 0))

theorem c71_0 : F.repChkAG (Q.tab r71_0.1) γ nG r71_0.1 Rd cst r71_0.2.1 r71_0.2.2 = true := by decide +kernel
theorem c71_1 : F.repChkAG (Q.tab r71_1.1) γ nG r71_1.1 Rd cst r71_1.2.1 r71_1.2.2 = true := by decide +kernel
theorem c71_2 : F.repChkAG (Q.tab r71_2.1) γ nG r71_2.1 Rd cst r71_2.2.1 r71_2.2.2 = true := by decide +kernel
theorem c71_3 : F.repChkAG (Q.tab r71_3.1) γ nG r71_3.1 Rd cst r71_3.2.1 r71_3.2.2 = true := by decide +kernel
theorem c71_4 : F.repChkAG (Q.tab r71_4.1) γ nG r71_4.1 Rd cst r71_4.2.1 r71_4.2.2 = true := by decide +kernel
theorem c71_5 : F.repChkAG (Q.tab r71_5.1) γ nG r71_5.1 Rd cst r71_5.2.1 r71_5.2.2 = true := by decide +kernel
theorem c71_6 : F.repChkAG (Q.tab r71_6.1) γ nG r71_6.1 Rd cst r71_6.2.1 r71_6.2.2 = true := by decide +kernel
theorem c71_7 : F.repChkAG (Q.tab r71_7.1) γ nG r71_7.1 Rd cst r71_7.2.1 r71_7.2.2 = true := by decide +kernel
theorem c71_8 : F.repChkAG (Q.tab r71_8.1) γ nG r71_8.1 Rd cst r71_8.2.1 r71_8.2.2 = true := by decide +kernel
theorem c71_9 : F.repChkAG (Q.tab r71_9.1) γ nG r71_9.1 Rd cst r71_9.2.1 r71_9.2.2 = true := by decide +kernel
theorem c71_10 : F.repChkAG (Q.tab r71_10.1) γ nG r71_10.1 Rd cst r71_10.2.1 r71_10.2.2 = true := by decide +kernel

def D71 : List (ℕ × (ℤ × ℤ) × RepData) := [r71_0, r71_1, r71_2, r71_3, r71_4, r71_5, r71_6, r71_7, r71_8, r71_9, r71_10]

theorem chkA71 : D71.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D71, List.all_cons, List.all_nil, c71_0, c71_1, c71_2, c71_3, c71_4, c71_5, c71_6, c71_7, c71_8, c71_9, c71_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

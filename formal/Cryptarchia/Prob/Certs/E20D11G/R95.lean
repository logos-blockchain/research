module

public import Cryptarchia.Prob.Certs.E20D11G.R87
meta import Cryptarchia.Prob.Certs.E20D11G.R87

/-! # E20D11G: (group, representative) entries 1045 to 1055, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r95_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 253 (0, 0))
def r95_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 254 (0, 0))
def r95_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 255 (0, 0))
def r95_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 256 (0, 0))
def r95_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 257 (0, 0))
def r95_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 258 (0, 0))
def r95_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 259 (0, 0))
def r95_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 260 (0, 0))
def r95_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 261 (0, 0))
def r95_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 262 (0, 0))
def r95_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 263 (0, 0))

theorem c95_0 : F.repChkAG (Q.tab r95_0.1) γ nG r95_0.1 Rd cst r95_0.2.1 r95_0.2.2 = true := by decide +kernel
theorem c95_1 : F.repChkAG (Q.tab r95_1.1) γ nG r95_1.1 Rd cst r95_1.2.1 r95_1.2.2 = true := by decide +kernel
theorem c95_2 : F.repChkAG (Q.tab r95_2.1) γ nG r95_2.1 Rd cst r95_2.2.1 r95_2.2.2 = true := by decide +kernel
theorem c95_3 : F.repChkAG (Q.tab r95_3.1) γ nG r95_3.1 Rd cst r95_3.2.1 r95_3.2.2 = true := by decide +kernel
theorem c95_4 : F.repChkAG (Q.tab r95_4.1) γ nG r95_4.1 Rd cst r95_4.2.1 r95_4.2.2 = true := by decide +kernel
theorem c95_5 : F.repChkAG (Q.tab r95_5.1) γ nG r95_5.1 Rd cst r95_5.2.1 r95_5.2.2 = true := by decide +kernel
theorem c95_6 : F.repChkAG (Q.tab r95_6.1) γ nG r95_6.1 Rd cst r95_6.2.1 r95_6.2.2 = true := by decide +kernel
theorem c95_7 : F.repChkAG (Q.tab r95_7.1) γ nG r95_7.1 Rd cst r95_7.2.1 r95_7.2.2 = true := by decide +kernel
theorem c95_8 : F.repChkAG (Q.tab r95_8.1) γ nG r95_8.1 Rd cst r95_8.2.1 r95_8.2.2 = true := by decide +kernel
theorem c95_9 : F.repChkAG (Q.tab r95_9.1) γ nG r95_9.1 Rd cst r95_9.2.1 r95_9.2.2 = true := by decide +kernel
theorem c95_10 : F.repChkAG (Q.tab r95_10.1) γ nG r95_10.1 Rd cst r95_10.2.1 r95_10.2.2 = true := by decide +kernel

def D95 : List (ℕ × (ℤ × ℤ) × RepData) := [r95_0, r95_1, r95_2, r95_3, r95_4, r95_5, r95_6, r95_7, r95_8, r95_9, r95_10]

theorem chkA95 : D95.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D95, List.all_cons, List.all_nil, c95_0, c95_1, c95_2, c95_3, c95_4, c95_5, c95_6, c95_7, c95_8, c95_9, c95_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R79
meta import Cryptarchia.Prob.Certs.E20D11G.R79

/-! # E20D11G: (group, representative) entries 957 to 967, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r87_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 165 (0, 0))
def r87_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 166 (0, 0))
def r87_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 167 (0, 0))
def r87_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 168 (0, 0))
def r87_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 169 (0, 0))
def r87_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 170 (0, 0))
def r87_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 171 (0, 0))
def r87_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 172 (0, 0))
def r87_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 173 (0, 0))
def r87_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 174 (0, 0))
def r87_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 175 (0, 0))

theorem c87_0 : F.repChkAG (Q.tab r87_0.1) γ nG r87_0.1 Rd cst r87_0.2.1 r87_0.2.2 = true := by decide +kernel
theorem c87_1 : F.repChkAG (Q.tab r87_1.1) γ nG r87_1.1 Rd cst r87_1.2.1 r87_1.2.2 = true := by decide +kernel
theorem c87_2 : F.repChkAG (Q.tab r87_2.1) γ nG r87_2.1 Rd cst r87_2.2.1 r87_2.2.2 = true := by decide +kernel
theorem c87_3 : F.repChkAG (Q.tab r87_3.1) γ nG r87_3.1 Rd cst r87_3.2.1 r87_3.2.2 = true := by decide +kernel
theorem c87_4 : F.repChkAG (Q.tab r87_4.1) γ nG r87_4.1 Rd cst r87_4.2.1 r87_4.2.2 = true := by decide +kernel
theorem c87_5 : F.repChkAG (Q.tab r87_5.1) γ nG r87_5.1 Rd cst r87_5.2.1 r87_5.2.2 = true := by decide +kernel
theorem c87_6 : F.repChkAG (Q.tab r87_6.1) γ nG r87_6.1 Rd cst r87_6.2.1 r87_6.2.2 = true := by decide +kernel
theorem c87_7 : F.repChkAG (Q.tab r87_7.1) γ nG r87_7.1 Rd cst r87_7.2.1 r87_7.2.2 = true := by decide +kernel
theorem c87_8 : F.repChkAG (Q.tab r87_8.1) γ nG r87_8.1 Rd cst r87_8.2.1 r87_8.2.2 = true := by decide +kernel
theorem c87_9 : F.repChkAG (Q.tab r87_9.1) γ nG r87_9.1 Rd cst r87_9.2.1 r87_9.2.2 = true := by decide +kernel
theorem c87_10 : F.repChkAG (Q.tab r87_10.1) γ nG r87_10.1 Rd cst r87_10.2.1 r87_10.2.2 = true := by decide +kernel

def D87 : List (ℕ × (ℤ × ℤ) × RepData) := [r87_0, r87_1, r87_2, r87_3, r87_4, r87_5, r87_6, r87_7, r87_8, r87_9, r87_10]

theorem chkA87 : D87.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D87, List.all_cons, List.all_nil, c87_0, c87_1, c87_2, c87_3, c87_4, c87_5, c87_6, c87_7, c87_8, c87_9, c87_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

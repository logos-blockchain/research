module

public import Cryptarchia.Prob.Certs.E20D11G.R1
meta import Cryptarchia.Prob.Certs.E20D11G.R1

/-! # E20D11G: (group, representative) entries 99 to 109, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r9_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 99 (0, 0))
def r9_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 100 (0, 0))
def r9_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 101 (0, 0))
def r9_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 102 (0, 0))
def r9_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 103 (0, 0))
def r9_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 104 (0, 0))
def r9_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 105 (0, 0))
def r9_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 106 (0, 0))
def r9_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 107 (0, 0))
def r9_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 108 (0, 0))
def r9_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 109 (0, 0))

theorem c9_0 : F.repChkAG (Q.tab r9_0.1) γ nG r9_0.1 Rd cst r9_0.2.1 r9_0.2.2 = true := by decide +kernel
theorem c9_1 : F.repChkAG (Q.tab r9_1.1) γ nG r9_1.1 Rd cst r9_1.2.1 r9_1.2.2 = true := by decide +kernel
theorem c9_2 : F.repChkAG (Q.tab r9_2.1) γ nG r9_2.1 Rd cst r9_2.2.1 r9_2.2.2 = true := by decide +kernel
theorem c9_3 : F.repChkAG (Q.tab r9_3.1) γ nG r9_3.1 Rd cst r9_3.2.1 r9_3.2.2 = true := by decide +kernel
theorem c9_4 : F.repChkAG (Q.tab r9_4.1) γ nG r9_4.1 Rd cst r9_4.2.1 r9_4.2.2 = true := by decide +kernel
theorem c9_5 : F.repChkAG (Q.tab r9_5.1) γ nG r9_5.1 Rd cst r9_5.2.1 r9_5.2.2 = true := by decide +kernel
theorem c9_6 : F.repChkAG (Q.tab r9_6.1) γ nG r9_6.1 Rd cst r9_6.2.1 r9_6.2.2 = true := by decide +kernel
theorem c9_7 : F.repChkAG (Q.tab r9_7.1) γ nG r9_7.1 Rd cst r9_7.2.1 r9_7.2.2 = true := by decide +kernel
theorem c9_8 : F.repChkAG (Q.tab r9_8.1) γ nG r9_8.1 Rd cst r9_8.2.1 r9_8.2.2 = true := by decide +kernel
theorem c9_9 : F.repChkAG (Q.tab r9_9.1) γ nG r9_9.1 Rd cst r9_9.2.1 r9_9.2.2 = true := by decide +kernel
theorem c9_10 : F.repChkAG (Q.tab r9_10.1) γ nG r9_10.1 Rd cst r9_10.2.1 r9_10.2.2 = true := by decide +kernel

def D9 : List (ℕ × (ℤ × ℤ) × RepData) := [r9_0, r9_1, r9_2, r9_3, r9_4, r9_5, r9_6, r9_7, r9_8, r9_9, r9_10]

theorem chkA9 : D9.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D9, List.all_cons, List.all_nil, c9_0, c9_1, c9_2, c9_3, c9_4, c9_5, c9_6, c9_7, c9_8, c9_9, c9_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

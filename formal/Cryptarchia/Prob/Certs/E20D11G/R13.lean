module

public import Cryptarchia.Prob.Certs.E20D11G.R5
meta import Cryptarchia.Prob.Certs.E20D11G.R5

/-! # E20D11G: (group, representative) entries 143 to 153, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r13_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 143 (0, 0))
def r13_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 144 (0, 0))
def r13_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 145 (0, 0))
def r13_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 146 (0, 0))
def r13_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 147 (0, 0))
def r13_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 148 (0, 0))
def r13_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 149 (0, 0))
def r13_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 150 (0, 0))
def r13_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 151 (0, 0))
def r13_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 152 (0, 0))
def r13_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 153 (0, 0))

theorem c13_0 : F.repChkAG (Q.tab r13_0.1) γ nG r13_0.1 Rd cst r13_0.2.1 r13_0.2.2 = true := by decide +kernel
theorem c13_1 : F.repChkAG (Q.tab r13_1.1) γ nG r13_1.1 Rd cst r13_1.2.1 r13_1.2.2 = true := by decide +kernel
theorem c13_2 : F.repChkAG (Q.tab r13_2.1) γ nG r13_2.1 Rd cst r13_2.2.1 r13_2.2.2 = true := by decide +kernel
theorem c13_3 : F.repChkAG (Q.tab r13_3.1) γ nG r13_3.1 Rd cst r13_3.2.1 r13_3.2.2 = true := by decide +kernel
theorem c13_4 : F.repChkAG (Q.tab r13_4.1) γ nG r13_4.1 Rd cst r13_4.2.1 r13_4.2.2 = true := by decide +kernel
theorem c13_5 : F.repChkAG (Q.tab r13_5.1) γ nG r13_5.1 Rd cst r13_5.2.1 r13_5.2.2 = true := by decide +kernel
theorem c13_6 : F.repChkAG (Q.tab r13_6.1) γ nG r13_6.1 Rd cst r13_6.2.1 r13_6.2.2 = true := by decide +kernel
theorem c13_7 : F.repChkAG (Q.tab r13_7.1) γ nG r13_7.1 Rd cst r13_7.2.1 r13_7.2.2 = true := by decide +kernel
theorem c13_8 : F.repChkAG (Q.tab r13_8.1) γ nG r13_8.1 Rd cst r13_8.2.1 r13_8.2.2 = true := by decide +kernel
theorem c13_9 : F.repChkAG (Q.tab r13_9.1) γ nG r13_9.1 Rd cst r13_9.2.1 r13_9.2.2 = true := by decide +kernel
theorem c13_10 : F.repChkAG (Q.tab r13_10.1) γ nG r13_10.1 Rd cst r13_10.2.1 r13_10.2.2 = true := by decide +kernel

def D13 : List (ℕ × (ℤ × ℤ) × RepData) := [r13_0, r13_1, r13_2, r13_3, r13_4, r13_5, r13_6, r13_7, r13_8, r13_9, r13_10]

theorem chkA13 : D13.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D13, List.all_cons, List.all_nil, c13_0, c13_1, c13_2, c13_3, c13_4, c13_5, c13_6, c13_7, c13_8, c13_9, c13_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R47
meta import Cryptarchia.Prob.Certs.E20D11G.R47

/-! # E20D11G: (group, representative) entries 605 to 615, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r55_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 143 (0, 0))
def r55_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 144 (0, 0))
def r55_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 145 (0, 0))
def r55_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 146 (0, 0))
def r55_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 147 (0, 0))
def r55_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 148 (0, 0))
def r55_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 149 (0, 0))
def r55_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 150 (0, 0))
def r55_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 151 (0, 0))
def r55_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 152 (0, 0))
def r55_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 153 (0, 0))

theorem c55_0 : F.repChkAG (Q.tab r55_0.1) γ nG r55_0.1 Rd cst r55_0.2.1 r55_0.2.2 = true := by decide +kernel
theorem c55_1 : F.repChkAG (Q.tab r55_1.1) γ nG r55_1.1 Rd cst r55_1.2.1 r55_1.2.2 = true := by decide +kernel
theorem c55_2 : F.repChkAG (Q.tab r55_2.1) γ nG r55_2.1 Rd cst r55_2.2.1 r55_2.2.2 = true := by decide +kernel
theorem c55_3 : F.repChkAG (Q.tab r55_3.1) γ nG r55_3.1 Rd cst r55_3.2.1 r55_3.2.2 = true := by decide +kernel
theorem c55_4 : F.repChkAG (Q.tab r55_4.1) γ nG r55_4.1 Rd cst r55_4.2.1 r55_4.2.2 = true := by decide +kernel
theorem c55_5 : F.repChkAG (Q.tab r55_5.1) γ nG r55_5.1 Rd cst r55_5.2.1 r55_5.2.2 = true := by decide +kernel
theorem c55_6 : F.repChkAG (Q.tab r55_6.1) γ nG r55_6.1 Rd cst r55_6.2.1 r55_6.2.2 = true := by decide +kernel
theorem c55_7 : F.repChkAG (Q.tab r55_7.1) γ nG r55_7.1 Rd cst r55_7.2.1 r55_7.2.2 = true := by decide +kernel
theorem c55_8 : F.repChkAG (Q.tab r55_8.1) γ nG r55_8.1 Rd cst r55_8.2.1 r55_8.2.2 = true := by decide +kernel
theorem c55_9 : F.repChkAG (Q.tab r55_9.1) γ nG r55_9.1 Rd cst r55_9.2.1 r55_9.2.2 = true := by decide +kernel
theorem c55_10 : F.repChkAG (Q.tab r55_10.1) γ nG r55_10.1 Rd cst r55_10.2.1 r55_10.2.2 = true := by decide +kernel

def D55 : List (ℕ × (ℤ × ℤ) × RepData) := [r55_0, r55_1, r55_2, r55_3, r55_4, r55_5, r55_6, r55_7, r55_8, r55_9, r55_10]

theorem chkA55 : D55.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D55, List.all_cons, List.all_nil, c55_0, c55_1, c55_2, c55_3, c55_4, c55_5, c55_6, c55_7, c55_8, c55_9, c55_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

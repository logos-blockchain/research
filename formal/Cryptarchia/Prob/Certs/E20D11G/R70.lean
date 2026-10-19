module

public import Cryptarchia.Prob.Certs.E20D11G.R62
meta import Cryptarchia.Prob.Certs.E20D11G.R62

/-! # E20D11G: (group, representative) entries 770 to 780, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r70_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 242 (0, 0))
def r70_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 243 (0, 0))
def r70_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 244 (0, 0))
def r70_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 245 (0, 0))
def r70_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 246 (0, 0))
def r70_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 247 (0, 0))
def r70_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 248 (0, 0))
def r70_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 249 (0, 0))
def r70_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 250 (0, 0))
def r70_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 251 (0, 0))
def r70_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 252 (0, 0))

theorem c70_0 : F.repChkAG (Q.tab r70_0.1) γ nG r70_0.1 Rd cst r70_0.2.1 r70_0.2.2 = true := by decide +kernel
theorem c70_1 : F.repChkAG (Q.tab r70_1.1) γ nG r70_1.1 Rd cst r70_1.2.1 r70_1.2.2 = true := by decide +kernel
theorem c70_2 : F.repChkAG (Q.tab r70_2.1) γ nG r70_2.1 Rd cst r70_2.2.1 r70_2.2.2 = true := by decide +kernel
theorem c70_3 : F.repChkAG (Q.tab r70_3.1) γ nG r70_3.1 Rd cst r70_3.2.1 r70_3.2.2 = true := by decide +kernel
theorem c70_4 : F.repChkAG (Q.tab r70_4.1) γ nG r70_4.1 Rd cst r70_4.2.1 r70_4.2.2 = true := by decide +kernel
theorem c70_5 : F.repChkAG (Q.tab r70_5.1) γ nG r70_5.1 Rd cst r70_5.2.1 r70_5.2.2 = true := by decide +kernel
theorem c70_6 : F.repChkAG (Q.tab r70_6.1) γ nG r70_6.1 Rd cst r70_6.2.1 r70_6.2.2 = true := by decide +kernel
theorem c70_7 : F.repChkAG (Q.tab r70_7.1) γ nG r70_7.1 Rd cst r70_7.2.1 r70_7.2.2 = true := by decide +kernel
theorem c70_8 : F.repChkAG (Q.tab r70_8.1) γ nG r70_8.1 Rd cst r70_8.2.1 r70_8.2.2 = true := by decide +kernel
theorem c70_9 : F.repChkAG (Q.tab r70_9.1) γ nG r70_9.1 Rd cst r70_9.2.1 r70_9.2.2 = true := by decide +kernel
theorem c70_10 : F.repChkAG (Q.tab r70_10.1) γ nG r70_10.1 Rd cst r70_10.2.1 r70_10.2.2 = true := by decide +kernel

def D70 : List (ℕ × (ℤ × ℤ) × RepData) := [r70_0, r70_1, r70_2, r70_3, r70_4, r70_5, r70_6, r70_7, r70_8, r70_9, r70_10]

theorem chkA70 : D70.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D70, List.all_cons, List.all_nil, c70_0, c70_1, c70_2, c70_3, c70_4, c70_5, c70_6, c70_7, c70_8, c70_9, c70_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R65
meta import Cryptarchia.Prob.Certs.E20D11G.R65

/-! # E20D11G: (group, representative) entries 803 to 813, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r73_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 11 (0, 0))
def r73_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 12 (0, 0))
def r73_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 13 (0, 0))
def r73_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 14 (0, 0))
def r73_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 15 (0, 0))
def r73_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 16 (0, 0))
def r73_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 17 (0, 0))
def r73_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 18 (0, 0))
def r73_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 19 (0, 0))
def r73_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 20 (0, 0))
def r73_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 21 (0, 0))

theorem c73_0 : F.repChkAG (Q.tab r73_0.1) γ nG r73_0.1 Rd cst r73_0.2.1 r73_0.2.2 = true := by decide +kernel
theorem c73_1 : F.repChkAG (Q.tab r73_1.1) γ nG r73_1.1 Rd cst r73_1.2.1 r73_1.2.2 = true := by decide +kernel
theorem c73_2 : F.repChkAG (Q.tab r73_2.1) γ nG r73_2.1 Rd cst r73_2.2.1 r73_2.2.2 = true := by decide +kernel
theorem c73_3 : F.repChkAG (Q.tab r73_3.1) γ nG r73_3.1 Rd cst r73_3.2.1 r73_3.2.2 = true := by decide +kernel
theorem c73_4 : F.repChkAG (Q.tab r73_4.1) γ nG r73_4.1 Rd cst r73_4.2.1 r73_4.2.2 = true := by decide +kernel
theorem c73_5 : F.repChkAG (Q.tab r73_5.1) γ nG r73_5.1 Rd cst r73_5.2.1 r73_5.2.2 = true := by decide +kernel
theorem c73_6 : F.repChkAG (Q.tab r73_6.1) γ nG r73_6.1 Rd cst r73_6.2.1 r73_6.2.2 = true := by decide +kernel
theorem c73_7 : F.repChkAG (Q.tab r73_7.1) γ nG r73_7.1 Rd cst r73_7.2.1 r73_7.2.2 = true := by decide +kernel
theorem c73_8 : F.repChkAG (Q.tab r73_8.1) γ nG r73_8.1 Rd cst r73_8.2.1 r73_8.2.2 = true := by decide +kernel
theorem c73_9 : F.repChkAG (Q.tab r73_9.1) γ nG r73_9.1 Rd cst r73_9.2.1 r73_9.2.2 = true := by decide +kernel
theorem c73_10 : F.repChkAG (Q.tab r73_10.1) γ nG r73_10.1 Rd cst r73_10.2.1 r73_10.2.2 = true := by decide +kernel

def D73 : List (ℕ × (ℤ × ℤ) × RepData) := [r73_0, r73_1, r73_2, r73_3, r73_4, r73_5, r73_6, r73_7, r73_8, r73_9, r73_10]

theorem chkA73 : D73.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D73, List.all_cons, List.all_nil, c73_0, c73_1, c73_2, c73_3, c73_4, c73_5, c73_6, c73_7, c73_8, c73_9, c73_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

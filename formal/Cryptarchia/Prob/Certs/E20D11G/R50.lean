module

public import Cryptarchia.Prob.Certs.E20D11G.R42
meta import Cryptarchia.Prob.Certs.E20D11G.R42

/-! # E20D11G: (group, representative) entries 550 to 560, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r50_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 22 (0, 0))
def r50_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 23 (0, 0))
def r50_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 24 (0, 0))
def r50_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 25 (0, 0))
def r50_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 26 (0, 0))
def r50_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 27 (0, 0))
def r50_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 28 (0, 0))
def r50_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 29 (0, 0))
def r50_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 30 (0, 0))
def r50_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 31 (0, 0))
def r50_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 32 (0, 0))

theorem c50_0 : F.repChkAG (Q.tab r50_0.1) γ nG r50_0.1 Rd cst r50_0.2.1 r50_0.2.2 = true := by decide +kernel
theorem c50_1 : F.repChkAG (Q.tab r50_1.1) γ nG r50_1.1 Rd cst r50_1.2.1 r50_1.2.2 = true := by decide +kernel
theorem c50_2 : F.repChkAG (Q.tab r50_2.1) γ nG r50_2.1 Rd cst r50_2.2.1 r50_2.2.2 = true := by decide +kernel
theorem c50_3 : F.repChkAG (Q.tab r50_3.1) γ nG r50_3.1 Rd cst r50_3.2.1 r50_3.2.2 = true := by decide +kernel
theorem c50_4 : F.repChkAG (Q.tab r50_4.1) γ nG r50_4.1 Rd cst r50_4.2.1 r50_4.2.2 = true := by decide +kernel
theorem c50_5 : F.repChkAG (Q.tab r50_5.1) γ nG r50_5.1 Rd cst r50_5.2.1 r50_5.2.2 = true := by decide +kernel
theorem c50_6 : F.repChkAG (Q.tab r50_6.1) γ nG r50_6.1 Rd cst r50_6.2.1 r50_6.2.2 = true := by decide +kernel
theorem c50_7 : F.repChkAG (Q.tab r50_7.1) γ nG r50_7.1 Rd cst r50_7.2.1 r50_7.2.2 = true := by decide +kernel
theorem c50_8 : F.repChkAG (Q.tab r50_8.1) γ nG r50_8.1 Rd cst r50_8.2.1 r50_8.2.2 = true := by decide +kernel
theorem c50_9 : F.repChkAG (Q.tab r50_9.1) γ nG r50_9.1 Rd cst r50_9.2.1 r50_9.2.2 = true := by decide +kernel
theorem c50_10 : F.repChkAG (Q.tab r50_10.1) γ nG r50_10.1 Rd cst r50_10.2.1 r50_10.2.2 = true := by decide +kernel

def D50 : List (ℕ × (ℤ × ℤ) × RepData) := [r50_0, r50_1, r50_2, r50_3, r50_4, r50_5, r50_6, r50_7, r50_8, r50_9, r50_10]

theorem chkA50 : D50.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D50, List.all_cons, List.all_nil, c50_0, c50_1, c50_2, c50_3, c50_4, c50_5, c50_6, c50_7, c50_8, c50_9, c50_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

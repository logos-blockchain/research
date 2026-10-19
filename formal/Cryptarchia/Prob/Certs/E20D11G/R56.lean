module

public import Cryptarchia.Prob.Certs.E20D11G.R48
meta import Cryptarchia.Prob.Certs.E20D11G.R48

/-! # E20D11G: (group, representative) entries 616 to 626, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r56_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 88 (0, 0))
def r56_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 89 (0, 0))
def r56_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 90 (0, 0))
def r56_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 91 (0, 0))
def r56_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 92 (0, 0))
def r56_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 93 (0, 0))
def r56_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 94 (0, 0))
def r56_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 95 (0, 0))
def r56_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 96 (0, 0))
def r56_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 97 (0, 0))
def r56_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 98 (0, 0))

theorem c56_0 : F.repChkAG (Q.tab r56_0.1) γ nG r56_0.1 Rd cst r56_0.2.1 r56_0.2.2 = true := by decide +kernel
theorem c56_1 : F.repChkAG (Q.tab r56_1.1) γ nG r56_1.1 Rd cst r56_1.2.1 r56_1.2.2 = true := by decide +kernel
theorem c56_2 : F.repChkAG (Q.tab r56_2.1) γ nG r56_2.1 Rd cst r56_2.2.1 r56_2.2.2 = true := by decide +kernel
theorem c56_3 : F.repChkAG (Q.tab r56_3.1) γ nG r56_3.1 Rd cst r56_3.2.1 r56_3.2.2 = true := by decide +kernel
theorem c56_4 : F.repChkAG (Q.tab r56_4.1) γ nG r56_4.1 Rd cst r56_4.2.1 r56_4.2.2 = true := by decide +kernel
theorem c56_5 : F.repChkAG (Q.tab r56_5.1) γ nG r56_5.1 Rd cst r56_5.2.1 r56_5.2.2 = true := by decide +kernel
theorem c56_6 : F.repChkAG (Q.tab r56_6.1) γ nG r56_6.1 Rd cst r56_6.2.1 r56_6.2.2 = true := by decide +kernel
theorem c56_7 : F.repChkAG (Q.tab r56_7.1) γ nG r56_7.1 Rd cst r56_7.2.1 r56_7.2.2 = true := by decide +kernel
theorem c56_8 : F.repChkAG (Q.tab r56_8.1) γ nG r56_8.1 Rd cst r56_8.2.1 r56_8.2.2 = true := by decide +kernel
theorem c56_9 : F.repChkAG (Q.tab r56_9.1) γ nG r56_9.1 Rd cst r56_9.2.1 r56_9.2.2 = true := by decide +kernel
theorem c56_10 : F.repChkAG (Q.tab r56_10.1) γ nG r56_10.1 Rd cst r56_10.2.1 r56_10.2.2 = true := by decide +kernel

def D56 : List (ℕ × (ℤ × ℤ) × RepData) := [r56_0, r56_1, r56_2, r56_3, r56_4, r56_5, r56_6, r56_7, r56_8, r56_9, r56_10]

theorem chkA56 : D56.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D56, List.all_cons, List.all_nil, c56_0, c56_1, c56_2, c56_3, c56_4, c56_5, c56_6, c56_7, c56_8, c56_9, c56_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

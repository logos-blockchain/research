module

public import Cryptarchia.Prob.Certs.E20D11G.R29
meta import Cryptarchia.Prob.Certs.E20D11G.R29

/-! # E20D11G: (group, representative) entries 407 to 417, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r37_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 143 (0, 0))
def r37_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 144 (0, 0))
def r37_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 145 (0, 0))
def r37_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 146 (0, 0))
def r37_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 147 (0, 0))
def r37_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 148 (0, 0))
def r37_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 149 (0, 0))
def r37_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 150 (0, 0))
def r37_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 151 (0, 0))
def r37_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 152 (0, 0))
def r37_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 153 (0, 0))

theorem c37_0 : F.repChkAG (Q.tab r37_0.1) γ nG r37_0.1 Rd r37_0.2.1 r37_0.2.2 = true := by decide +kernel
theorem c37_1 : F.repChkAG (Q.tab r37_1.1) γ nG r37_1.1 Rd r37_1.2.1 r37_1.2.2 = true := by decide +kernel
theorem c37_2 : F.repChkAG (Q.tab r37_2.1) γ nG r37_2.1 Rd r37_2.2.1 r37_2.2.2 = true := by decide +kernel
theorem c37_3 : F.repChkAG (Q.tab r37_3.1) γ nG r37_3.1 Rd r37_3.2.1 r37_3.2.2 = true := by decide +kernel
theorem c37_4 : F.repChkAG (Q.tab r37_4.1) γ nG r37_4.1 Rd r37_4.2.1 r37_4.2.2 = true := by decide +kernel
theorem c37_5 : F.repChkAG (Q.tab r37_5.1) γ nG r37_5.1 Rd r37_5.2.1 r37_5.2.2 = true := by decide +kernel
theorem c37_6 : F.repChkAG (Q.tab r37_6.1) γ nG r37_6.1 Rd r37_6.2.1 r37_6.2.2 = true := by decide +kernel
theorem c37_7 : F.repChkAG (Q.tab r37_7.1) γ nG r37_7.1 Rd r37_7.2.1 r37_7.2.2 = true := by decide +kernel
theorem c37_8 : F.repChkAG (Q.tab r37_8.1) γ nG r37_8.1 Rd r37_8.2.1 r37_8.2.2 = true := by decide +kernel
theorem c37_9 : F.repChkAG (Q.tab r37_9.1) γ nG r37_9.1 Rd r37_9.2.1 r37_9.2.2 = true := by decide +kernel
theorem c37_10 : F.repChkAG (Q.tab r37_10.1) γ nG r37_10.1 Rd r37_10.2.1 r37_10.2.2 = true := by decide +kernel

def D37 : List (ℕ × (ℤ × ℤ) × RepData) := [r37_0, r37_1, r37_2, r37_3, r37_4, r37_5, r37_6, r37_7, r37_8, r37_9, r37_10]

theorem chkA37 : D37.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D37, List.all_cons, List.all_nil, c37_0, c37_1, c37_2, c37_3, c37_4, c37_5, c37_6, c37_7, c37_8, c37_9, c37_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

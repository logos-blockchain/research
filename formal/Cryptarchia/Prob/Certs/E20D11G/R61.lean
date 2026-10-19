module

public import Cryptarchia.Prob.Certs.E20D11G.R53
meta import Cryptarchia.Prob.Certs.E20D11G.R53

/-! # E20D11G: (group, representative) entries 671 to 681, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r61_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 143 (0, 0))
def r61_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 144 (0, 0))
def r61_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 145 (0, 0))
def r61_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 146 (0, 0))
def r61_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 147 (0, 0))
def r61_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 148 (0, 0))
def r61_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 149 (0, 0))
def r61_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 150 (0, 0))
def r61_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 151 (0, 0))
def r61_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 152 (0, 0))
def r61_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 153 (0, 0))

theorem c61_0 : F.repChkAG (Q.tab r61_0.1) γ nG r61_0.1 Rd r61_0.2.1 r61_0.2.2 = true := by decide +kernel
theorem c61_1 : F.repChkAG (Q.tab r61_1.1) γ nG r61_1.1 Rd r61_1.2.1 r61_1.2.2 = true := by decide +kernel
theorem c61_2 : F.repChkAG (Q.tab r61_2.1) γ nG r61_2.1 Rd r61_2.2.1 r61_2.2.2 = true := by decide +kernel
theorem c61_3 : F.repChkAG (Q.tab r61_3.1) γ nG r61_3.1 Rd r61_3.2.1 r61_3.2.2 = true := by decide +kernel
theorem c61_4 : F.repChkAG (Q.tab r61_4.1) γ nG r61_4.1 Rd r61_4.2.1 r61_4.2.2 = true := by decide +kernel
theorem c61_5 : F.repChkAG (Q.tab r61_5.1) γ nG r61_5.1 Rd r61_5.2.1 r61_5.2.2 = true := by decide +kernel
theorem c61_6 : F.repChkAG (Q.tab r61_6.1) γ nG r61_6.1 Rd r61_6.2.1 r61_6.2.2 = true := by decide +kernel
theorem c61_7 : F.repChkAG (Q.tab r61_7.1) γ nG r61_7.1 Rd r61_7.2.1 r61_7.2.2 = true := by decide +kernel
theorem c61_8 : F.repChkAG (Q.tab r61_8.1) γ nG r61_8.1 Rd r61_8.2.1 r61_8.2.2 = true := by decide +kernel
theorem c61_9 : F.repChkAG (Q.tab r61_9.1) γ nG r61_9.1 Rd r61_9.2.1 r61_9.2.2 = true := by decide +kernel
theorem c61_10 : F.repChkAG (Q.tab r61_10.1) γ nG r61_10.1 Rd r61_10.2.1 r61_10.2.2 = true := by decide +kernel

def D61 : List (ℕ × (ℤ × ℤ) × RepData) := [r61_0, r61_1, r61_2, r61_3, r61_4, r61_5, r61_6, r61_7, r61_8, r61_9, r61_10]

theorem chkA61 : D61.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D61, List.all_cons, List.all_nil, c61_0, c61_1, c61_2, c61_3, c61_4, c61_5, c61_6, c61_7, c61_8, c61_9, c61_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

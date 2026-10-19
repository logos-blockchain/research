module

public import Cryptarchia.Prob.Certs.E20D11G.R40
meta import Cryptarchia.Prob.Certs.E20D11G.R40

/-! # E20D11G: (group, representative) entries 528 to 538, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r48_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 0 (0, 0))
def r48_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 1 (0, 0))
def r48_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 2 (0, 0))
def r48_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 3 (0, 0))
def r48_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 4 (0, 0))
def r48_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 5 (0, 0))
def r48_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 6 (0, 0))
def r48_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 7 (0, 0))
def r48_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 8 (0, 0))
def r48_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 9 (0, 0))
def r48_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 10 (0, 0))

theorem c48_0 : F.repChkAG (Q.tab r48_0.1) γ nG r48_0.1 Rd r48_0.2.1 r48_0.2.2 = true := by decide +kernel
theorem c48_1 : F.repChkAG (Q.tab r48_1.1) γ nG r48_1.1 Rd r48_1.2.1 r48_1.2.2 = true := by decide +kernel
theorem c48_2 : F.repChkAG (Q.tab r48_2.1) γ nG r48_2.1 Rd r48_2.2.1 r48_2.2.2 = true := by decide +kernel
theorem c48_3 : F.repChkAG (Q.tab r48_3.1) γ nG r48_3.1 Rd r48_3.2.1 r48_3.2.2 = true := by decide +kernel
theorem c48_4 : F.repChkAG (Q.tab r48_4.1) γ nG r48_4.1 Rd r48_4.2.1 r48_4.2.2 = true := by decide +kernel
theorem c48_5 : F.repChkAG (Q.tab r48_5.1) γ nG r48_5.1 Rd r48_5.2.1 r48_5.2.2 = true := by decide +kernel
theorem c48_6 : F.repChkAG (Q.tab r48_6.1) γ nG r48_6.1 Rd r48_6.2.1 r48_6.2.2 = true := by decide +kernel
theorem c48_7 : F.repChkAG (Q.tab r48_7.1) γ nG r48_7.1 Rd r48_7.2.1 r48_7.2.2 = true := by decide +kernel
theorem c48_8 : F.repChkAG (Q.tab r48_8.1) γ nG r48_8.1 Rd r48_8.2.1 r48_8.2.2 = true := by decide +kernel
theorem c48_9 : F.repChkAG (Q.tab r48_9.1) γ nG r48_9.1 Rd r48_9.2.1 r48_9.2.2 = true := by decide +kernel
theorem c48_10 : F.repChkAG (Q.tab r48_10.1) γ nG r48_10.1 Rd r48_10.2.1 r48_10.2.2 = true := by decide +kernel

def D48 : List (ℕ × (ℤ × ℤ) × RepData) := [r48_0, r48_1, r48_2, r48_3, r48_4, r48_5, r48_6, r48_7, r48_8, r48_9, r48_10]

theorem chkA48 : D48.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D48, List.all_cons, List.all_nil, c48_0, c48_1, c48_2, c48_3, c48_4, c48_5, c48_6, c48_7, c48_8, c48_9, c48_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

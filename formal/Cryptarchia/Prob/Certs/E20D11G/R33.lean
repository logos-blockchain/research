module

public import Cryptarchia.Prob.Certs.E20D11G.R29
meta import Cryptarchia.Prob.Certs.E20D11G.R29

/-! # E20D11G: (group, representative) entries 363 to 373, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r33_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 99 (0, 0))
def r33_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 100 (0, 0))
def r33_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 101 (0, 0))
def r33_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 102 (0, 0))
def r33_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 103 (0, 0))
def r33_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 104 (0, 0))
def r33_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 105 (0, 0))
def r33_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 106 (0, 0))
def r33_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 107 (0, 0))
def r33_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 108 (0, 0))
def r33_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 109 (0, 0))

theorem c33_0 : F.repChkAG (Q.tab r33_0.1) γ r33_0.2.1 r33_0.2.2 = true := by decide +kernel
theorem c33_1 : F.repChkAG (Q.tab r33_1.1) γ r33_1.2.1 r33_1.2.2 = true := by decide +kernel
theorem c33_2 : F.repChkAG (Q.tab r33_2.1) γ r33_2.2.1 r33_2.2.2 = true := by decide +kernel
theorem c33_3 : F.repChkAG (Q.tab r33_3.1) γ r33_3.2.1 r33_3.2.2 = true := by decide +kernel
theorem c33_4 : F.repChkAG (Q.tab r33_4.1) γ r33_4.2.1 r33_4.2.2 = true := by decide +kernel
theorem c33_5 : F.repChkAG (Q.tab r33_5.1) γ r33_5.2.1 r33_5.2.2 = true := by decide +kernel
theorem c33_6 : F.repChkAG (Q.tab r33_6.1) γ r33_6.2.1 r33_6.2.2 = true := by decide +kernel
theorem c33_7 : F.repChkAG (Q.tab r33_7.1) γ r33_7.2.1 r33_7.2.2 = true := by decide +kernel
theorem c33_8 : F.repChkAG (Q.tab r33_8.1) γ r33_8.2.1 r33_8.2.2 = true := by decide +kernel
theorem c33_9 : F.repChkAG (Q.tab r33_9.1) γ r33_9.2.1 r33_9.2.2 = true := by decide +kernel
theorem c33_10 : F.repChkAG (Q.tab r33_10.1) γ r33_10.2.1 r33_10.2.2 = true := by decide +kernel

def D33 : List (ℕ × (ℤ × ℤ) × RepData) := [r33_0, r33_1, r33_2, r33_3, r33_4, r33_5, r33_6, r33_7, r33_8, r33_9, r33_10]

theorem chkA33 : D33.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D33, List.all_cons, List.all_nil, c33_0, c33_1, c33_2, c33_3, c33_4, c33_5, c33_6, c33_7, c33_8, c33_9, c33_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

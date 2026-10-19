module

public import Cryptarchia.Prob.Certs.E20D11G.R3
meta import Cryptarchia.Prob.Certs.E20D11G.R3

/-! # E20D11G: (group, representative) entries 77 to 87, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r7_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 77 (0, 0))
def r7_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 78 (0, 0))
def r7_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 79 (0, 0))
def r7_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 80 (0, 0))
def r7_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 81 (0, 0))
def r7_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 82 (0, 0))
def r7_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 83 (0, 0))
def r7_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 84 (0, 0))
def r7_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 85 (0, 0))
def r7_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 86 (0, 0))
def r7_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 87 (0, 0))

theorem c7_0 : F.repChkAG (Q.tab r7_0.1) γ r7_0.2.1 r7_0.2.2 = true := by decide +kernel
theorem c7_1 : F.repChkAG (Q.tab r7_1.1) γ r7_1.2.1 r7_1.2.2 = true := by decide +kernel
theorem c7_2 : F.repChkAG (Q.tab r7_2.1) γ r7_2.2.1 r7_2.2.2 = true := by decide +kernel
theorem c7_3 : F.repChkAG (Q.tab r7_3.1) γ r7_3.2.1 r7_3.2.2 = true := by decide +kernel
theorem c7_4 : F.repChkAG (Q.tab r7_4.1) γ r7_4.2.1 r7_4.2.2 = true := by decide +kernel
theorem c7_5 : F.repChkAG (Q.tab r7_5.1) γ r7_5.2.1 r7_5.2.2 = true := by decide +kernel
theorem c7_6 : F.repChkAG (Q.tab r7_6.1) γ r7_6.2.1 r7_6.2.2 = true := by decide +kernel
theorem c7_7 : F.repChkAG (Q.tab r7_7.1) γ r7_7.2.1 r7_7.2.2 = true := by decide +kernel
theorem c7_8 : F.repChkAG (Q.tab r7_8.1) γ r7_8.2.1 r7_8.2.2 = true := by decide +kernel
theorem c7_9 : F.repChkAG (Q.tab r7_9.1) γ r7_9.2.1 r7_9.2.2 = true := by decide +kernel
theorem c7_10 : F.repChkAG (Q.tab r7_10.1) γ r7_10.2.1 r7_10.2.2 = true := by decide +kernel

def D7 : List (ℕ × (ℤ × ℤ) × RepData) := [r7_0, r7_1, r7_2, r7_3, r7_4, r7_5, r7_6, r7_7, r7_8, r7_9, r7_10]

theorem chkA7 : D7.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D7, List.all_cons, List.all_nil, c7_0, c7_1, c7_2, c7_3, c7_4, c7_5, c7_6, c7_7, c7_8, c7_9, c7_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

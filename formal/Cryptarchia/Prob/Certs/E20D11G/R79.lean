module

public import Cryptarchia.Prob.Certs.E20D11G.R75
meta import Cryptarchia.Prob.Certs.E20D11G.R75

/-! # E20D11G: (group, representative) entries 869 to 879, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r79_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 77 (0, 0))
def r79_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 78 (0, 0))
def r79_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 79 (0, 0))
def r79_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 80 (0, 0))
def r79_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 81 (0, 0))
def r79_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 82 (0, 0))
def r79_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 83 (0, 0))
def r79_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 84 (0, 0))
def r79_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 85 (0, 0))
def r79_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 86 (0, 0))
def r79_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 87 (0, 0))

theorem c79_0 : F.repChkAG (Q.tab r79_0.1) γ r79_0.2.1 r79_0.2.2 = true := by decide +kernel
theorem c79_1 : F.repChkAG (Q.tab r79_1.1) γ r79_1.2.1 r79_1.2.2 = true := by decide +kernel
theorem c79_2 : F.repChkAG (Q.tab r79_2.1) γ r79_2.2.1 r79_2.2.2 = true := by decide +kernel
theorem c79_3 : F.repChkAG (Q.tab r79_3.1) γ r79_3.2.1 r79_3.2.2 = true := by decide +kernel
theorem c79_4 : F.repChkAG (Q.tab r79_4.1) γ r79_4.2.1 r79_4.2.2 = true := by decide +kernel
theorem c79_5 : F.repChkAG (Q.tab r79_5.1) γ r79_5.2.1 r79_5.2.2 = true := by decide +kernel
theorem c79_6 : F.repChkAG (Q.tab r79_6.1) γ r79_6.2.1 r79_6.2.2 = true := by decide +kernel
theorem c79_7 : F.repChkAG (Q.tab r79_7.1) γ r79_7.2.1 r79_7.2.2 = true := by decide +kernel
theorem c79_8 : F.repChkAG (Q.tab r79_8.1) γ r79_8.2.1 r79_8.2.2 = true := by decide +kernel
theorem c79_9 : F.repChkAG (Q.tab r79_9.1) γ r79_9.2.1 r79_9.2.2 = true := by decide +kernel
theorem c79_10 : F.repChkAG (Q.tab r79_10.1) γ r79_10.2.1 r79_10.2.2 = true := by decide +kernel

def D79 : List (ℕ × (ℤ × ℤ) × RepData) := [r79_0, r79_1, r79_2, r79_3, r79_4, r79_5, r79_6, r79_7, r79_8, r79_9, r79_10]

theorem chkA79 : D79.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D79, List.all_cons, List.all_nil, c79_0, c79_1, c79_2, c79_3, c79_4, c79_5, c79_6, c79_7, c79_8, c79_9, c79_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

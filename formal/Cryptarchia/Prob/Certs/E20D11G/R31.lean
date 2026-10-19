module

public import Cryptarchia.Prob.Certs.E20D11G.R27
meta import Cryptarchia.Prob.Certs.E20D11G.R27

/-! # E20D11G: (group, representative) entries 341 to 351, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r31_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 77 (0, 0))
def r31_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 78 (0, 0))
def r31_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 79 (0, 0))
def r31_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 80 (0, 0))
def r31_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 81 (0, 0))
def r31_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 82 (0, 0))
def r31_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 83 (0, 0))
def r31_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 84 (0, 0))
def r31_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 85 (0, 0))
def r31_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 86 (0, 0))
def r31_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 87 (0, 0))

theorem c31_0 : F.repChkAG (Q.tab r31_0.1) γ r31_0.2.1 r31_0.2.2 = true := by decide +kernel
theorem c31_1 : F.repChkAG (Q.tab r31_1.1) γ r31_1.2.1 r31_1.2.2 = true := by decide +kernel
theorem c31_2 : F.repChkAG (Q.tab r31_2.1) γ r31_2.2.1 r31_2.2.2 = true := by decide +kernel
theorem c31_3 : F.repChkAG (Q.tab r31_3.1) γ r31_3.2.1 r31_3.2.2 = true := by decide +kernel
theorem c31_4 : F.repChkAG (Q.tab r31_4.1) γ r31_4.2.1 r31_4.2.2 = true := by decide +kernel
theorem c31_5 : F.repChkAG (Q.tab r31_5.1) γ r31_5.2.1 r31_5.2.2 = true := by decide +kernel
theorem c31_6 : F.repChkAG (Q.tab r31_6.1) γ r31_6.2.1 r31_6.2.2 = true := by decide +kernel
theorem c31_7 : F.repChkAG (Q.tab r31_7.1) γ r31_7.2.1 r31_7.2.2 = true := by decide +kernel
theorem c31_8 : F.repChkAG (Q.tab r31_8.1) γ r31_8.2.1 r31_8.2.2 = true := by decide +kernel
theorem c31_9 : F.repChkAG (Q.tab r31_9.1) γ r31_9.2.1 r31_9.2.2 = true := by decide +kernel
theorem c31_10 : F.repChkAG (Q.tab r31_10.1) γ r31_10.2.1 r31_10.2.2 = true := by decide +kernel

def D31 : List (ℕ × (ℤ × ℤ) × RepData) := [r31_0, r31_1, r31_2, r31_3, r31_4, r31_5, r31_6, r31_7, r31_8, r31_9, r31_10]

theorem chkA31 : D31.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D31, List.all_cons, List.all_nil, c31_0, c31_1, c31_2, c31_3, c31_4, c31_5, c31_6, c31_7, c31_8, c31_9, c31_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

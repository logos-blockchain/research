module

public import Cryptarchia.Prob.Certs.E20D11G.R8
meta import Cryptarchia.Prob.Certs.E20D11G.R8

/-! # E20D11G: (group, representative) entries 132 to 142, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r12_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 132 (0, 0))
def r12_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 133 (0, 0))
def r12_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 134 (0, 0))
def r12_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 135 (0, 0))
def r12_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 136 (0, 0))
def r12_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 137 (0, 0))
def r12_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 138 (0, 0))
def r12_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 139 (0, 0))
def r12_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 140 (0, 0))
def r12_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 141 (0, 0))
def r12_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 142 (0, 0))

theorem c12_0 : F.repChkAG (Q.tab r12_0.1) γ r12_0.2.1 r12_0.2.2 = true := by decide +kernel
theorem c12_1 : F.repChkAG (Q.tab r12_1.1) γ r12_1.2.1 r12_1.2.2 = true := by decide +kernel
theorem c12_2 : F.repChkAG (Q.tab r12_2.1) γ r12_2.2.1 r12_2.2.2 = true := by decide +kernel
theorem c12_3 : F.repChkAG (Q.tab r12_3.1) γ r12_3.2.1 r12_3.2.2 = true := by decide +kernel
theorem c12_4 : F.repChkAG (Q.tab r12_4.1) γ r12_4.2.1 r12_4.2.2 = true := by decide +kernel
theorem c12_5 : F.repChkAG (Q.tab r12_5.1) γ r12_5.2.1 r12_5.2.2 = true := by decide +kernel
theorem c12_6 : F.repChkAG (Q.tab r12_6.1) γ r12_6.2.1 r12_6.2.2 = true := by decide +kernel
theorem c12_7 : F.repChkAG (Q.tab r12_7.1) γ r12_7.2.1 r12_7.2.2 = true := by decide +kernel
theorem c12_8 : F.repChkAG (Q.tab r12_8.1) γ r12_8.2.1 r12_8.2.2 = true := by decide +kernel
theorem c12_9 : F.repChkAG (Q.tab r12_9.1) γ r12_9.2.1 r12_9.2.2 = true := by decide +kernel
theorem c12_10 : F.repChkAG (Q.tab r12_10.1) γ r12_10.2.1 r12_10.2.2 = true := by decide +kernel

def D12 : List (ℕ × (ℤ × ℤ) × RepData) := [r12_0, r12_1, r12_2, r12_3, r12_4, r12_5, r12_6, r12_7, r12_8, r12_9, r12_10]

theorem chkA12 : D12.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D12, List.all_cons, List.all_nil, c12_0, c12_1, c12_2, c12_3, c12_4, c12_5, c12_6, c12_7, c12_8, c12_9, c12_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

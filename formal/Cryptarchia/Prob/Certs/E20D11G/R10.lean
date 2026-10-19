module

public import Cryptarchia.Prob.Certs.E20D11G.R6
meta import Cryptarchia.Prob.Certs.E20D11G.R6

/-! # E20D11G: (group, representative) entries 110 to 120, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r10_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 110 (0, 0))
def r10_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 111 (0, 0))
def r10_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 112 (0, 0))
def r10_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 113 (0, 0))
def r10_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 114 (0, 0))
def r10_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 115 (0, 0))
def r10_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 116 (0, 0))
def r10_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 117 (0, 0))
def r10_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 118 (0, 0))
def r10_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 119 (0, 0))
def r10_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 120 (0, 0))

theorem c10_0 : F.repChkAG (Q.tab r10_0.1) γ r10_0.2.1 r10_0.2.2 = true := by decide +kernel
theorem c10_1 : F.repChkAG (Q.tab r10_1.1) γ r10_1.2.1 r10_1.2.2 = true := by decide +kernel
theorem c10_2 : F.repChkAG (Q.tab r10_2.1) γ r10_2.2.1 r10_2.2.2 = true := by decide +kernel
theorem c10_3 : F.repChkAG (Q.tab r10_3.1) γ r10_3.2.1 r10_3.2.2 = true := by decide +kernel
theorem c10_4 : F.repChkAG (Q.tab r10_4.1) γ r10_4.2.1 r10_4.2.2 = true := by decide +kernel
theorem c10_5 : F.repChkAG (Q.tab r10_5.1) γ r10_5.2.1 r10_5.2.2 = true := by decide +kernel
theorem c10_6 : F.repChkAG (Q.tab r10_6.1) γ r10_6.2.1 r10_6.2.2 = true := by decide +kernel
theorem c10_7 : F.repChkAG (Q.tab r10_7.1) γ r10_7.2.1 r10_7.2.2 = true := by decide +kernel
theorem c10_8 : F.repChkAG (Q.tab r10_8.1) γ r10_8.2.1 r10_8.2.2 = true := by decide +kernel
theorem c10_9 : F.repChkAG (Q.tab r10_9.1) γ r10_9.2.1 r10_9.2.2 = true := by decide +kernel
theorem c10_10 : F.repChkAG (Q.tab r10_10.1) γ r10_10.2.1 r10_10.2.2 = true := by decide +kernel

def D10 : List (ℕ × (ℤ × ℤ) × RepData) := [r10_0, r10_1, r10_2, r10_3, r10_4, r10_5, r10_6, r10_7, r10_8, r10_9, r10_10]

theorem chkA10 : D10.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D10, List.all_cons, List.all_nil, c10_0, c10_1, c10_2, c10_3, c10_4, c10_5, c10_6, c10_7, c10_8, c10_9, c10_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R4
meta import Cryptarchia.Prob.Certs.E20D11G.R4

/-! # E20D11G: (group, representative) entries 88 to 98, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r8_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 88 (0, 0))
def r8_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 89 (0, 0))
def r8_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 90 (0, 0))
def r8_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 91 (0, 0))
def r8_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 92 (0, 0))
def r8_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 93 (0, 0))
def r8_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 94 (0, 0))
def r8_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 95 (0, 0))
def r8_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 96 (0, 0))
def r8_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 97 (0, 0))
def r8_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ s)) ((Q.tab 0).repList.getD 98 (0, 0))

theorem c8_0 : F.repChkAG (Q.tab r8_0.1) γ r8_0.2.1 r8_0.2.2 = true := by decide +kernel
theorem c8_1 : F.repChkAG (Q.tab r8_1.1) γ r8_1.2.1 r8_1.2.2 = true := by decide +kernel
theorem c8_2 : F.repChkAG (Q.tab r8_2.1) γ r8_2.2.1 r8_2.2.2 = true := by decide +kernel
theorem c8_3 : F.repChkAG (Q.tab r8_3.1) γ r8_3.2.1 r8_3.2.2 = true := by decide +kernel
theorem c8_4 : F.repChkAG (Q.tab r8_4.1) γ r8_4.2.1 r8_4.2.2 = true := by decide +kernel
theorem c8_5 : F.repChkAG (Q.tab r8_5.1) γ r8_5.2.1 r8_5.2.2 = true := by decide +kernel
theorem c8_6 : F.repChkAG (Q.tab r8_6.1) γ r8_6.2.1 r8_6.2.2 = true := by decide +kernel
theorem c8_7 : F.repChkAG (Q.tab r8_7.1) γ r8_7.2.1 r8_7.2.2 = true := by decide +kernel
theorem c8_8 : F.repChkAG (Q.tab r8_8.1) γ r8_8.2.1 r8_8.2.2 = true := by decide +kernel
theorem c8_9 : F.repChkAG (Q.tab r8_9.1) γ r8_9.2.1 r8_9.2.2 = true := by decide +kernel
theorem c8_10 : F.repChkAG (Q.tab r8_10.1) γ r8_10.2.1 r8_10.2.2 = true := by decide +kernel

def D8 : List (ℕ × (ℤ × ℤ) × RepData) := [r8_0, r8_1, r8_2, r8_3, r8_4, r8_5, r8_6, r8_7, r8_8, r8_9, r8_10]

theorem chkA8 : D8.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D8, List.all_cons, List.all_nil, c8_0, c8_1, c8_2, c8_3, c8_4, c8_5, c8_6, c8_7, c8_8, c8_9, c8_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R28
meta import Cryptarchia.Prob.Certs.E20D11G.R28

/-! # E20D11G: (group, representative) entries 352 to 362, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r32_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 88 (0, 0))
def r32_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 89 (0, 0))
def r32_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 90 (0, 0))
def r32_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 91 (0, 0))
def r32_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 92 (0, 0))
def r32_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 93 (0, 0))
def r32_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 94 (0, 0))
def r32_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 95 (0, 0))
def r32_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 96 (0, 0))
def r32_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 97 (0, 0))
def r32_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 98 (0, 0))

theorem c32_0 : F.repChkAG (Q.tab r32_0.1) γ r32_0.2.1 r32_0.2.2 = true := by decide +kernel
theorem c32_1 : F.repChkAG (Q.tab r32_1.1) γ r32_1.2.1 r32_1.2.2 = true := by decide +kernel
theorem c32_2 : F.repChkAG (Q.tab r32_2.1) γ r32_2.2.1 r32_2.2.2 = true := by decide +kernel
theorem c32_3 : F.repChkAG (Q.tab r32_3.1) γ r32_3.2.1 r32_3.2.2 = true := by decide +kernel
theorem c32_4 : F.repChkAG (Q.tab r32_4.1) γ r32_4.2.1 r32_4.2.2 = true := by decide +kernel
theorem c32_5 : F.repChkAG (Q.tab r32_5.1) γ r32_5.2.1 r32_5.2.2 = true := by decide +kernel
theorem c32_6 : F.repChkAG (Q.tab r32_6.1) γ r32_6.2.1 r32_6.2.2 = true := by decide +kernel
theorem c32_7 : F.repChkAG (Q.tab r32_7.1) γ r32_7.2.1 r32_7.2.2 = true := by decide +kernel
theorem c32_8 : F.repChkAG (Q.tab r32_8.1) γ r32_8.2.1 r32_8.2.2 = true := by decide +kernel
theorem c32_9 : F.repChkAG (Q.tab r32_9.1) γ r32_9.2.1 r32_9.2.2 = true := by decide +kernel
theorem c32_10 : F.repChkAG (Q.tab r32_10.1) γ r32_10.2.1 r32_10.2.2 = true := by decide +kernel

def D32 : List (ℕ × (ℤ × ℤ) × RepData) := [r32_0, r32_1, r32_2, r32_3, r32_4, r32_5, r32_6, r32_7, r32_8, r32_9, r32_10]

theorem chkA32 : D32.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D32, List.all_cons, List.all_nil, c32_0, c32_1, c32_2, c32_3, c32_4, c32_5, c32_6, c32_7, c32_8, c32_9, c32_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

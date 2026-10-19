module

public import Cryptarchia.Prob.Certs.E20D11G.R76
meta import Cryptarchia.Prob.Certs.E20D11G.R76

/-! # E20D11G: (group, representative) entries 880 to 890, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r80_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 88 (0, 0))
def r80_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 89 (0, 0))
def r80_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 90 (0, 0))
def r80_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 91 (0, 0))
def r80_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 92 (0, 0))
def r80_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 93 (0, 0))
def r80_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 94 (0, 0))
def r80_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 95 (0, 0))
def r80_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 96 (0, 0))
def r80_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 97 (0, 0))
def r80_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 98 (0, 0))

theorem c80_0 : F.repChkAG (Q.tab r80_0.1) γ r80_0.2.1 r80_0.2.2 = true := by decide +kernel
theorem c80_1 : F.repChkAG (Q.tab r80_1.1) γ r80_1.2.1 r80_1.2.2 = true := by decide +kernel
theorem c80_2 : F.repChkAG (Q.tab r80_2.1) γ r80_2.2.1 r80_2.2.2 = true := by decide +kernel
theorem c80_3 : F.repChkAG (Q.tab r80_3.1) γ r80_3.2.1 r80_3.2.2 = true := by decide +kernel
theorem c80_4 : F.repChkAG (Q.tab r80_4.1) γ r80_4.2.1 r80_4.2.2 = true := by decide +kernel
theorem c80_5 : F.repChkAG (Q.tab r80_5.1) γ r80_5.2.1 r80_5.2.2 = true := by decide +kernel
theorem c80_6 : F.repChkAG (Q.tab r80_6.1) γ r80_6.2.1 r80_6.2.2 = true := by decide +kernel
theorem c80_7 : F.repChkAG (Q.tab r80_7.1) γ r80_7.2.1 r80_7.2.2 = true := by decide +kernel
theorem c80_8 : F.repChkAG (Q.tab r80_8.1) γ r80_8.2.1 r80_8.2.2 = true := by decide +kernel
theorem c80_9 : F.repChkAG (Q.tab r80_9.1) γ r80_9.2.1 r80_9.2.2 = true := by decide +kernel
theorem c80_10 : F.repChkAG (Q.tab r80_10.1) γ r80_10.2.1 r80_10.2.2 = true := by decide +kernel

def D80 : List (ℕ × (ℤ × ℤ) × RepData) := [r80_0, r80_1, r80_2, r80_3, r80_4, r80_5, r80_6, r80_7, r80_8, r80_9, r80_10]

theorem chkA80 : D80.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D80, List.all_cons, List.all_nil, c80_0, c80_1, c80_2, c80_3, c80_4, c80_5, c80_6, c80_7, c80_8, c80_9, c80_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

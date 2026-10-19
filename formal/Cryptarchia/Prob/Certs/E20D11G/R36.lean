module

public import Cryptarchia.Prob.Certs.E20D11G.R32
meta import Cryptarchia.Prob.Certs.E20D11G.R32

/-! # E20D11G: (group, representative) entries 396 to 406, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r36_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 132 (0, 0))
def r36_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 133 (0, 0))
def r36_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 134 (0, 0))
def r36_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 135 (0, 0))
def r36_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 136 (0, 0))
def r36_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 137 (0, 0))
def r36_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 138 (0, 0))
def r36_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 139 (0, 0))
def r36_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 140 (0, 0))
def r36_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 141 (0, 0))
def r36_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 142 (0, 0))

theorem c36_0 : F.repChkAG (Q.tab r36_0.1) γ r36_0.2.1 r36_0.2.2 = true := by decide +kernel
theorem c36_1 : F.repChkAG (Q.tab r36_1.1) γ r36_1.2.1 r36_1.2.2 = true := by decide +kernel
theorem c36_2 : F.repChkAG (Q.tab r36_2.1) γ r36_2.2.1 r36_2.2.2 = true := by decide +kernel
theorem c36_3 : F.repChkAG (Q.tab r36_3.1) γ r36_3.2.1 r36_3.2.2 = true := by decide +kernel
theorem c36_4 : F.repChkAG (Q.tab r36_4.1) γ r36_4.2.1 r36_4.2.2 = true := by decide +kernel
theorem c36_5 : F.repChkAG (Q.tab r36_5.1) γ r36_5.2.1 r36_5.2.2 = true := by decide +kernel
theorem c36_6 : F.repChkAG (Q.tab r36_6.1) γ r36_6.2.1 r36_6.2.2 = true := by decide +kernel
theorem c36_7 : F.repChkAG (Q.tab r36_7.1) γ r36_7.2.1 r36_7.2.2 = true := by decide +kernel
theorem c36_8 : F.repChkAG (Q.tab r36_8.1) γ r36_8.2.1 r36_8.2.2 = true := by decide +kernel
theorem c36_9 : F.repChkAG (Q.tab r36_9.1) γ r36_9.2.1 r36_9.2.2 = true := by decide +kernel
theorem c36_10 : F.repChkAG (Q.tab r36_10.1) γ r36_10.2.1 r36_10.2.2 = true := by decide +kernel

def D36 : List (ℕ × (ℤ × ℤ) × RepData) := [r36_0, r36_1, r36_2, r36_3, r36_4, r36_5, r36_6, r36_7, r36_8, r36_9, r36_10]

theorem chkA36 : D36.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D36, List.all_cons, List.all_nil, c36_0, c36_1, c36_2, c36_3, c36_4, c36_5, c36_6, c36_7, c36_8, c36_9, c36_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

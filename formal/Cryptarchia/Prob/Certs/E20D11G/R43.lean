module

public import Cryptarchia.Prob.Certs.E20D11G.R39
meta import Cryptarchia.Prob.Certs.E20D11G.R39

/-! # E20D11G: (group, representative) entries 473 to 483, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r43_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 209 (0, 0))
def r43_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 210 (0, 0))
def r43_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 211 (0, 0))
def r43_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 212 (0, 0))
def r43_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 213 (0, 0))
def r43_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 214 (0, 0))
def r43_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 215 (0, 0))
def r43_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 216 (0, 0))
def r43_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 217 (0, 0))
def r43_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 218 (0, 0))
def r43_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ s)) ((Q.tab 1).repList.getD 219 (0, 0))

theorem c43_0 : F.repChkAG (Q.tab r43_0.1) γ r43_0.2.1 r43_0.2.2 = true := by decide +kernel
theorem c43_1 : F.repChkAG (Q.tab r43_1.1) γ r43_1.2.1 r43_1.2.2 = true := by decide +kernel
theorem c43_2 : F.repChkAG (Q.tab r43_2.1) γ r43_2.2.1 r43_2.2.2 = true := by decide +kernel
theorem c43_3 : F.repChkAG (Q.tab r43_3.1) γ r43_3.2.1 r43_3.2.2 = true := by decide +kernel
theorem c43_4 : F.repChkAG (Q.tab r43_4.1) γ r43_4.2.1 r43_4.2.2 = true := by decide +kernel
theorem c43_5 : F.repChkAG (Q.tab r43_5.1) γ r43_5.2.1 r43_5.2.2 = true := by decide +kernel
theorem c43_6 : F.repChkAG (Q.tab r43_6.1) γ r43_6.2.1 r43_6.2.2 = true := by decide +kernel
theorem c43_7 : F.repChkAG (Q.tab r43_7.1) γ r43_7.2.1 r43_7.2.2 = true := by decide +kernel
theorem c43_8 : F.repChkAG (Q.tab r43_8.1) γ r43_8.2.1 r43_8.2.2 = true := by decide +kernel
theorem c43_9 : F.repChkAG (Q.tab r43_9.1) γ r43_9.2.1 r43_9.2.2 = true := by decide +kernel
theorem c43_10 : F.repChkAG (Q.tab r43_10.1) γ r43_10.2.1 r43_10.2.2 = true := by decide +kernel

def D43 : List (ℕ × (ℤ × ℤ) × RepData) := [r43_0, r43_1, r43_2, r43_3, r43_4, r43_5, r43_6, r43_7, r43_8, r43_9, r43_10]

theorem chkA43 : D43.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D43, List.all_cons, List.all_nil, c43_0, c43_1, c43_2, c43_3, c43_4, c43_5, c43_6, c43_7, c43_8, c43_9, c43_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

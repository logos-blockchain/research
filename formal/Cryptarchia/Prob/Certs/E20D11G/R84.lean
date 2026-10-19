module

public import Cryptarchia.Prob.Certs.E20D11G.R76
meta import Cryptarchia.Prob.Certs.E20D11G.R76

/-! # E20D11G: (group, representative) entries 924 to 934, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r84_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 132 (0, 0))
def r84_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 133 (0, 0))
def r84_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 134 (0, 0))
def r84_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 135 (0, 0))
def r84_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 136 (0, 0))
def r84_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 137 (0, 0))
def r84_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 138 (0, 0))
def r84_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 139 (0, 0))
def r84_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 140 (0, 0))
def r84_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 141 (0, 0))
def r84_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 142 (0, 0))

theorem c84_0 : F.repChkAG (Q.tab r84_0.1) γ nG r84_0.1 Rd r84_0.2.1 r84_0.2.2 = true := by decide +kernel
theorem c84_1 : F.repChkAG (Q.tab r84_1.1) γ nG r84_1.1 Rd r84_1.2.1 r84_1.2.2 = true := by decide +kernel
theorem c84_2 : F.repChkAG (Q.tab r84_2.1) γ nG r84_2.1 Rd r84_2.2.1 r84_2.2.2 = true := by decide +kernel
theorem c84_3 : F.repChkAG (Q.tab r84_3.1) γ nG r84_3.1 Rd r84_3.2.1 r84_3.2.2 = true := by decide +kernel
theorem c84_4 : F.repChkAG (Q.tab r84_4.1) γ nG r84_4.1 Rd r84_4.2.1 r84_4.2.2 = true := by decide +kernel
theorem c84_5 : F.repChkAG (Q.tab r84_5.1) γ nG r84_5.1 Rd r84_5.2.1 r84_5.2.2 = true := by decide +kernel
theorem c84_6 : F.repChkAG (Q.tab r84_6.1) γ nG r84_6.1 Rd r84_6.2.1 r84_6.2.2 = true := by decide +kernel
theorem c84_7 : F.repChkAG (Q.tab r84_7.1) γ nG r84_7.1 Rd r84_7.2.1 r84_7.2.2 = true := by decide +kernel
theorem c84_8 : F.repChkAG (Q.tab r84_8.1) γ nG r84_8.1 Rd r84_8.2.1 r84_8.2.2 = true := by decide +kernel
theorem c84_9 : F.repChkAG (Q.tab r84_9.1) γ nG r84_9.1 Rd r84_9.2.1 r84_9.2.2 = true := by decide +kernel
theorem c84_10 : F.repChkAG (Q.tab r84_10.1) γ nG r84_10.1 Rd r84_10.2.1 r84_10.2.2 = true := by decide +kernel

def D84 : List (ℕ × (ℤ × ℤ) × RepData) := [r84_0, r84_1, r84_2, r84_3, r84_4, r84_5, r84_6, r84_7, r84_8, r84_9, r84_10]

theorem chkA84 : D84.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D84, List.all_cons, List.all_nil, c84_0, c84_1, c84_2, c84_3, c84_4, c84_5, c84_6, c84_7, c84_8, c84_9, c84_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

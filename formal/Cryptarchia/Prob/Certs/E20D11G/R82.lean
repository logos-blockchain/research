module

public import Cryptarchia.Prob.Certs.E20D11G.R74
meta import Cryptarchia.Prob.Certs.E20D11G.R74

/-! # E20D11G: (group, representative) entries 902 to 912, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r82_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 110 (0, 0))
def r82_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 111 (0, 0))
def r82_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 112 (0, 0))
def r82_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 113 (0, 0))
def r82_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 114 (0, 0))
def r82_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 115 (0, 0))
def r82_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 116 (0, 0))
def r82_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 117 (0, 0))
def r82_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 118 (0, 0))
def r82_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 119 (0, 0))
def r82_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 120 (0, 0))

theorem c82_0 : F.repChkAG (Q.tab r82_0.1) γ nG r82_0.1 Rd r82_0.2.1 r82_0.2.2 = true := by decide +kernel
theorem c82_1 : F.repChkAG (Q.tab r82_1.1) γ nG r82_1.1 Rd r82_1.2.1 r82_1.2.2 = true := by decide +kernel
theorem c82_2 : F.repChkAG (Q.tab r82_2.1) γ nG r82_2.1 Rd r82_2.2.1 r82_2.2.2 = true := by decide +kernel
theorem c82_3 : F.repChkAG (Q.tab r82_3.1) γ nG r82_3.1 Rd r82_3.2.1 r82_3.2.2 = true := by decide +kernel
theorem c82_4 : F.repChkAG (Q.tab r82_4.1) γ nG r82_4.1 Rd r82_4.2.1 r82_4.2.2 = true := by decide +kernel
theorem c82_5 : F.repChkAG (Q.tab r82_5.1) γ nG r82_5.1 Rd r82_5.2.1 r82_5.2.2 = true := by decide +kernel
theorem c82_6 : F.repChkAG (Q.tab r82_6.1) γ nG r82_6.1 Rd r82_6.2.1 r82_6.2.2 = true := by decide +kernel
theorem c82_7 : F.repChkAG (Q.tab r82_7.1) γ nG r82_7.1 Rd r82_7.2.1 r82_7.2.2 = true := by decide +kernel
theorem c82_8 : F.repChkAG (Q.tab r82_8.1) γ nG r82_8.1 Rd r82_8.2.1 r82_8.2.2 = true := by decide +kernel
theorem c82_9 : F.repChkAG (Q.tab r82_9.1) γ nG r82_9.1 Rd r82_9.2.1 r82_9.2.2 = true := by decide +kernel
theorem c82_10 : F.repChkAG (Q.tab r82_10.1) γ nG r82_10.1 Rd r82_10.2.1 r82_10.2.2 = true := by decide +kernel

def D82 : List (ℕ × (ℤ × ℤ) × RepData) := [r82_0, r82_1, r82_2, r82_3, r82_4, r82_5, r82_6, r82_7, r82_8, r82_9, r82_10]

theorem chkA82 : D82.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D82, List.all_cons, List.all_nil, c82_0, c82_1, c82_2, c82_3, c82_4, c82_5, c82_6, c82_7, c82_8, c82_9, c82_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

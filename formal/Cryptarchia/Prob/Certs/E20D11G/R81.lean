module

public import Cryptarchia.Prob.Certs.E20D11G.R73
meta import Cryptarchia.Prob.Certs.E20D11G.R73

/-! # E20D11G: (group, representative) entries 891 to 901, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r81_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 99 (0, 0))
def r81_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 100 (0, 0))
def r81_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 101 (0, 0))
def r81_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 102 (0, 0))
def r81_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 103 (0, 0))
def r81_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 104 (0, 0))
def r81_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 105 (0, 0))
def r81_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 106 (0, 0))
def r81_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 107 (0, 0))
def r81_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 108 (0, 0))
def r81_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 109 (0, 0))

theorem c81_0 : F.repChkAG (Q.tab r81_0.1) γ nG r81_0.1 Rd r81_0.2.1 r81_0.2.2 = true := by decide +kernel
theorem c81_1 : F.repChkAG (Q.tab r81_1.1) γ nG r81_1.1 Rd r81_1.2.1 r81_1.2.2 = true := by decide +kernel
theorem c81_2 : F.repChkAG (Q.tab r81_2.1) γ nG r81_2.1 Rd r81_2.2.1 r81_2.2.2 = true := by decide +kernel
theorem c81_3 : F.repChkAG (Q.tab r81_3.1) γ nG r81_3.1 Rd r81_3.2.1 r81_3.2.2 = true := by decide +kernel
theorem c81_4 : F.repChkAG (Q.tab r81_4.1) γ nG r81_4.1 Rd r81_4.2.1 r81_4.2.2 = true := by decide +kernel
theorem c81_5 : F.repChkAG (Q.tab r81_5.1) γ nG r81_5.1 Rd r81_5.2.1 r81_5.2.2 = true := by decide +kernel
theorem c81_6 : F.repChkAG (Q.tab r81_6.1) γ nG r81_6.1 Rd r81_6.2.1 r81_6.2.2 = true := by decide +kernel
theorem c81_7 : F.repChkAG (Q.tab r81_7.1) γ nG r81_7.1 Rd r81_7.2.1 r81_7.2.2 = true := by decide +kernel
theorem c81_8 : F.repChkAG (Q.tab r81_8.1) γ nG r81_8.1 Rd r81_8.2.1 r81_8.2.2 = true := by decide +kernel
theorem c81_9 : F.repChkAG (Q.tab r81_9.1) γ nG r81_9.1 Rd r81_9.2.1 r81_9.2.2 = true := by decide +kernel
theorem c81_10 : F.repChkAG (Q.tab r81_10.1) γ nG r81_10.1 Rd r81_10.2.1 r81_10.2.2 = true := by decide +kernel

def D81 : List (ℕ × (ℤ × ℤ) × RepData) := [r81_0, r81_1, r81_2, r81_3, r81_4, r81_5, r81_6, r81_7, r81_8, r81_9, r81_10]

theorem chkA81 : D81.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D81, List.all_cons, List.all_nil, c81_0, c81_1, c81_2, c81_3, c81_4, c81_5, c81_6, c81_7, c81_8, c81_9, c81_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

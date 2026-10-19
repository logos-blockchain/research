module

public import Cryptarchia.Prob.Certs.E20D11G.R51
meta import Cryptarchia.Prob.Certs.E20D11G.R51

/-! # E20D11G: (group, representative) entries 649 to 659, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r59_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 121 (0, 0))
def r59_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 122 (0, 0))
def r59_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 123 (0, 0))
def r59_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 124 (0, 0))
def r59_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 125 (0, 0))
def r59_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 126 (0, 0))
def r59_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 127 (0, 0))
def r59_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 128 (0, 0))
def r59_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 129 (0, 0))
def r59_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 130 (0, 0))
def r59_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 131 (0, 0))

theorem c59_0 : F.repChkAG (Q.tab r59_0.1) γ nG r59_0.1 Rd r59_0.2.1 r59_0.2.2 = true := by decide +kernel
theorem c59_1 : F.repChkAG (Q.tab r59_1.1) γ nG r59_1.1 Rd r59_1.2.1 r59_1.2.2 = true := by decide +kernel
theorem c59_2 : F.repChkAG (Q.tab r59_2.1) γ nG r59_2.1 Rd r59_2.2.1 r59_2.2.2 = true := by decide +kernel
theorem c59_3 : F.repChkAG (Q.tab r59_3.1) γ nG r59_3.1 Rd r59_3.2.1 r59_3.2.2 = true := by decide +kernel
theorem c59_4 : F.repChkAG (Q.tab r59_4.1) γ nG r59_4.1 Rd r59_4.2.1 r59_4.2.2 = true := by decide +kernel
theorem c59_5 : F.repChkAG (Q.tab r59_5.1) γ nG r59_5.1 Rd r59_5.2.1 r59_5.2.2 = true := by decide +kernel
theorem c59_6 : F.repChkAG (Q.tab r59_6.1) γ nG r59_6.1 Rd r59_6.2.1 r59_6.2.2 = true := by decide +kernel
theorem c59_7 : F.repChkAG (Q.tab r59_7.1) γ nG r59_7.1 Rd r59_7.2.1 r59_7.2.2 = true := by decide +kernel
theorem c59_8 : F.repChkAG (Q.tab r59_8.1) γ nG r59_8.1 Rd r59_8.2.1 r59_8.2.2 = true := by decide +kernel
theorem c59_9 : F.repChkAG (Q.tab r59_9.1) γ nG r59_9.1 Rd r59_9.2.1 r59_9.2.2 = true := by decide +kernel
theorem c59_10 : F.repChkAG (Q.tab r59_10.1) γ nG r59_10.1 Rd r59_10.2.1 r59_10.2.2 = true := by decide +kernel

def D59 : List (ℕ × (ℤ × ℤ) × RepData) := [r59_0, r59_1, r59_2, r59_3, r59_4, r59_5, r59_6, r59_7, r59_8, r59_9, r59_10]

theorem chkA59 : D59.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D59, List.all_cons, List.all_nil, c59_0, c59_1, c59_2, c59_3, c59_4, c59_5, c59_6, c59_7, c59_8, c59_9, c59_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

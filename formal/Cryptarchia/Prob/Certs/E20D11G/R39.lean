module

public import Cryptarchia.Prob.Certs.E20D11G.R31
meta import Cryptarchia.Prob.Certs.E20D11G.R31

/-! # E20D11G: (group, representative) entries 429 to 439, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r39_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 121 (0, 0))
def r39_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 122 (0, 0))
def r39_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 123 (0, 0))
def r39_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 124 (0, 0))
def r39_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 125 (0, 0))
def r39_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 126 (0, 0))
def r39_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 127 (0, 0))
def r39_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 128 (0, 0))
def r39_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 129 (0, 0))
def r39_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 130 (0, 0))
def r39_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 131 (0, 0))

theorem c39_0 : F.repChkAG (Q.tab r39_0.1) γ nG r39_0.1 Rd cst r39_0.2.1 r39_0.2.2 = true := by decide +kernel
theorem c39_1 : F.repChkAG (Q.tab r39_1.1) γ nG r39_1.1 Rd cst r39_1.2.1 r39_1.2.2 = true := by decide +kernel
theorem c39_2 : F.repChkAG (Q.tab r39_2.1) γ nG r39_2.1 Rd cst r39_2.2.1 r39_2.2.2 = true := by decide +kernel
theorem c39_3 : F.repChkAG (Q.tab r39_3.1) γ nG r39_3.1 Rd cst r39_3.2.1 r39_3.2.2 = true := by decide +kernel
theorem c39_4 : F.repChkAG (Q.tab r39_4.1) γ nG r39_4.1 Rd cst r39_4.2.1 r39_4.2.2 = true := by decide +kernel
theorem c39_5 : F.repChkAG (Q.tab r39_5.1) γ nG r39_5.1 Rd cst r39_5.2.1 r39_5.2.2 = true := by decide +kernel
theorem c39_6 : F.repChkAG (Q.tab r39_6.1) γ nG r39_6.1 Rd cst r39_6.2.1 r39_6.2.2 = true := by decide +kernel
theorem c39_7 : F.repChkAG (Q.tab r39_7.1) γ nG r39_7.1 Rd cst r39_7.2.1 r39_7.2.2 = true := by decide +kernel
theorem c39_8 : F.repChkAG (Q.tab r39_8.1) γ nG r39_8.1 Rd cst r39_8.2.1 r39_8.2.2 = true := by decide +kernel
theorem c39_9 : F.repChkAG (Q.tab r39_9.1) γ nG r39_9.1 Rd cst r39_9.2.1 r39_9.2.2 = true := by decide +kernel
theorem c39_10 : F.repChkAG (Q.tab r39_10.1) γ nG r39_10.1 Rd cst r39_10.2.1 r39_10.2.2 = true := by decide +kernel

def D39 : List (ℕ × (ℤ × ℤ) × RepData) := [r39_0, r39_1, r39_2, r39_3, r39_4, r39_5, r39_6, r39_7, r39_8, r39_9, r39_10]

theorem chkA39 : D39.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D39, List.all_cons, List.all_nil, c39_0, c39_1, c39_2, c39_3, c39_4, c39_5, c39_6, c39_7, c39_8, c39_9, c39_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

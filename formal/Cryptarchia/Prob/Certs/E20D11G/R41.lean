module

public import Cryptarchia.Prob.Certs.E20D11G.R33
meta import Cryptarchia.Prob.Certs.E20D11G.R33

/-! # E20D11G: (group, representative) entries 451 to 461, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r41_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 187 (0, 0))
def r41_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 188 (0, 0))
def r41_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 189 (0, 0))
def r41_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 190 (0, 0))
def r41_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 191 (0, 0))
def r41_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 192 (0, 0))
def r41_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 193 (0, 0))
def r41_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 194 (0, 0))
def r41_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 195 (0, 0))
def r41_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 196 (0, 0))
def r41_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 197 (0, 0))

theorem c41_0 : F.repChkAG (Q.tab r41_0.1) γ nG r41_0.1 Rd cst r41_0.2.1 r41_0.2.2 = true := by decide +kernel
theorem c41_1 : F.repChkAG (Q.tab r41_1.1) γ nG r41_1.1 Rd cst r41_1.2.1 r41_1.2.2 = true := by decide +kernel
theorem c41_2 : F.repChkAG (Q.tab r41_2.1) γ nG r41_2.1 Rd cst r41_2.2.1 r41_2.2.2 = true := by decide +kernel
theorem c41_3 : F.repChkAG (Q.tab r41_3.1) γ nG r41_3.1 Rd cst r41_3.2.1 r41_3.2.2 = true := by decide +kernel
theorem c41_4 : F.repChkAG (Q.tab r41_4.1) γ nG r41_4.1 Rd cst r41_4.2.1 r41_4.2.2 = true := by decide +kernel
theorem c41_5 : F.repChkAG (Q.tab r41_5.1) γ nG r41_5.1 Rd cst r41_5.2.1 r41_5.2.2 = true := by decide +kernel
theorem c41_6 : F.repChkAG (Q.tab r41_6.1) γ nG r41_6.1 Rd cst r41_6.2.1 r41_6.2.2 = true := by decide +kernel
theorem c41_7 : F.repChkAG (Q.tab r41_7.1) γ nG r41_7.1 Rd cst r41_7.2.1 r41_7.2.2 = true := by decide +kernel
theorem c41_8 : F.repChkAG (Q.tab r41_8.1) γ nG r41_8.1 Rd cst r41_8.2.1 r41_8.2.2 = true := by decide +kernel
theorem c41_9 : F.repChkAG (Q.tab r41_9.1) γ nG r41_9.1 Rd cst r41_9.2.1 r41_9.2.2 = true := by decide +kernel
theorem c41_10 : F.repChkAG (Q.tab r41_10.1) γ nG r41_10.1 Rd cst r41_10.2.1 r41_10.2.2 = true := by decide +kernel

def D41 : List (ℕ × (ℤ × ℤ) × RepData) := [r41_0, r41_1, r41_2, r41_3, r41_4, r41_5, r41_6, r41_7, r41_8, r41_9, r41_10]

theorem chkA41 : D41.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D41, List.all_cons, List.all_nil, c41_0, c41_1, c41_2, c41_3, c41_4, c41_5, c41_6, c41_7, c41_8, c41_9, c41_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

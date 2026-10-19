module

public import Cryptarchia.Prob.Certs.E20D11G.R26
meta import Cryptarchia.Prob.Certs.E20D11G.R26

/-! # E20D11G: (group, representative) entries 374 to 384, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r34_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 110 (0, 0))
def r34_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 111 (0, 0))
def r34_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 112 (0, 0))
def r34_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 113 (0, 0))
def r34_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 114 (0, 0))
def r34_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 115 (0, 0))
def r34_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 116 (0, 0))
def r34_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 117 (0, 0))
def r34_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 118 (0, 0))
def r34_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 119 (0, 0))
def r34_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 120 (0, 0))

theorem c34_0 : F.repChkAG (Q.tab r34_0.1) γ nG r34_0.1 Rd cst r34_0.2.1 r34_0.2.2 = true := by decide +kernel
theorem c34_1 : F.repChkAG (Q.tab r34_1.1) γ nG r34_1.1 Rd cst r34_1.2.1 r34_1.2.2 = true := by decide +kernel
theorem c34_2 : F.repChkAG (Q.tab r34_2.1) γ nG r34_2.1 Rd cst r34_2.2.1 r34_2.2.2 = true := by decide +kernel
theorem c34_3 : F.repChkAG (Q.tab r34_3.1) γ nG r34_3.1 Rd cst r34_3.2.1 r34_3.2.2 = true := by decide +kernel
theorem c34_4 : F.repChkAG (Q.tab r34_4.1) γ nG r34_4.1 Rd cst r34_4.2.1 r34_4.2.2 = true := by decide +kernel
theorem c34_5 : F.repChkAG (Q.tab r34_5.1) γ nG r34_5.1 Rd cst r34_5.2.1 r34_5.2.2 = true := by decide +kernel
theorem c34_6 : F.repChkAG (Q.tab r34_6.1) γ nG r34_6.1 Rd cst r34_6.2.1 r34_6.2.2 = true := by decide +kernel
theorem c34_7 : F.repChkAG (Q.tab r34_7.1) γ nG r34_7.1 Rd cst r34_7.2.1 r34_7.2.2 = true := by decide +kernel
theorem c34_8 : F.repChkAG (Q.tab r34_8.1) γ nG r34_8.1 Rd cst r34_8.2.1 r34_8.2.2 = true := by decide +kernel
theorem c34_9 : F.repChkAG (Q.tab r34_9.1) γ nG r34_9.1 Rd cst r34_9.2.1 r34_9.2.2 = true := by decide +kernel
theorem c34_10 : F.repChkAG (Q.tab r34_10.1) γ nG r34_10.1 Rd cst r34_10.2.1 r34_10.2.2 = true := by decide +kernel

def D34 : List (ℕ × (ℤ × ℤ) × RepData) := [r34_0, r34_1, r34_2, r34_3, r34_4, r34_5, r34_6, r34_7, r34_8, r34_9, r34_10]

theorem chkA34 : D34.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D34, List.all_cons, List.all_nil, c34_0, c34_1, c34_2, c34_3, c34_4, c34_5, c34_6, c34_7, c34_8, c34_9, c34_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

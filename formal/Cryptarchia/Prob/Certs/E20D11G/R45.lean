module

public import Cryptarchia.Prob.Certs.E20D11G.R37
meta import Cryptarchia.Prob.Certs.E20D11G.R37

/-! # E20D11G: (group, representative) entries 495 to 505, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r45_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 231 (0, 0))
def r45_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 232 (0, 0))
def r45_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 233 (0, 0))
def r45_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 234 (0, 0))
def r45_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 235 (0, 0))
def r45_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 236 (0, 0))
def r45_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 237 (0, 0))
def r45_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 238 (0, 0))
def r45_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 239 (0, 0))
def r45_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 240 (0, 0))
def r45_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 241 (0, 0))

theorem c45_0 : F.repChkAG (Q.tab r45_0.1) γ nG r45_0.1 Rd cst r45_0.2.1 r45_0.2.2 = true := by decide +kernel
theorem c45_1 : F.repChkAG (Q.tab r45_1.1) γ nG r45_1.1 Rd cst r45_1.2.1 r45_1.2.2 = true := by decide +kernel
theorem c45_2 : F.repChkAG (Q.tab r45_2.1) γ nG r45_2.1 Rd cst r45_2.2.1 r45_2.2.2 = true := by decide +kernel
theorem c45_3 : F.repChkAG (Q.tab r45_3.1) γ nG r45_3.1 Rd cst r45_3.2.1 r45_3.2.2 = true := by decide +kernel
theorem c45_4 : F.repChkAG (Q.tab r45_4.1) γ nG r45_4.1 Rd cst r45_4.2.1 r45_4.2.2 = true := by decide +kernel
theorem c45_5 : F.repChkAG (Q.tab r45_5.1) γ nG r45_5.1 Rd cst r45_5.2.1 r45_5.2.2 = true := by decide +kernel
theorem c45_6 : F.repChkAG (Q.tab r45_6.1) γ nG r45_6.1 Rd cst r45_6.2.1 r45_6.2.2 = true := by decide +kernel
theorem c45_7 : F.repChkAG (Q.tab r45_7.1) γ nG r45_7.1 Rd cst r45_7.2.1 r45_7.2.2 = true := by decide +kernel
theorem c45_8 : F.repChkAG (Q.tab r45_8.1) γ nG r45_8.1 Rd cst r45_8.2.1 r45_8.2.2 = true := by decide +kernel
theorem c45_9 : F.repChkAG (Q.tab r45_9.1) γ nG r45_9.1 Rd cst r45_9.2.1 r45_9.2.2 = true := by decide +kernel
theorem c45_10 : F.repChkAG (Q.tab r45_10.1) γ nG r45_10.1 Rd cst r45_10.2.1 r45_10.2.2 = true := by decide +kernel

def D45 : List (ℕ × (ℤ × ℤ) × RepData) := [r45_0, r45_1, r45_2, r45_3, r45_4, r45_5, r45_6, r45_7, r45_8, r45_9, r45_10]

theorem chkA45 : D45.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D45, List.all_cons, List.all_nil, c45_0, c45_1, c45_2, c45_3, c45_4, c45_5, c45_6, c45_7, c45_8, c45_9, c45_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R61
meta import Cryptarchia.Prob.Certs.E20D11G.R61

/-! # E20D11G: (group, representative) entries 759 to 769, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r69_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 231 (0, 0))
def r69_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 232 (0, 0))
def r69_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 233 (0, 0))
def r69_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 234 (0, 0))
def r69_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 235 (0, 0))
def r69_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 236 (0, 0))
def r69_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 237 (0, 0))
def r69_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 238 (0, 0))
def r69_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 239 (0, 0))
def r69_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 240 (0, 0))
def r69_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 241 (0, 0))

theorem c69_0 : F.repChkAG (Q.tab r69_0.1) γ nG r69_0.1 Rd cst r69_0.2.1 r69_0.2.2 = true := by decide +kernel
theorem c69_1 : F.repChkAG (Q.tab r69_1.1) γ nG r69_1.1 Rd cst r69_1.2.1 r69_1.2.2 = true := by decide +kernel
theorem c69_2 : F.repChkAG (Q.tab r69_2.1) γ nG r69_2.1 Rd cst r69_2.2.1 r69_2.2.2 = true := by decide +kernel
theorem c69_3 : F.repChkAG (Q.tab r69_3.1) γ nG r69_3.1 Rd cst r69_3.2.1 r69_3.2.2 = true := by decide +kernel
theorem c69_4 : F.repChkAG (Q.tab r69_4.1) γ nG r69_4.1 Rd cst r69_4.2.1 r69_4.2.2 = true := by decide +kernel
theorem c69_5 : F.repChkAG (Q.tab r69_5.1) γ nG r69_5.1 Rd cst r69_5.2.1 r69_5.2.2 = true := by decide +kernel
theorem c69_6 : F.repChkAG (Q.tab r69_6.1) γ nG r69_6.1 Rd cst r69_6.2.1 r69_6.2.2 = true := by decide +kernel
theorem c69_7 : F.repChkAG (Q.tab r69_7.1) γ nG r69_7.1 Rd cst r69_7.2.1 r69_7.2.2 = true := by decide +kernel
theorem c69_8 : F.repChkAG (Q.tab r69_8.1) γ nG r69_8.1 Rd cst r69_8.2.1 r69_8.2.2 = true := by decide +kernel
theorem c69_9 : F.repChkAG (Q.tab r69_9.1) γ nG r69_9.1 Rd cst r69_9.2.1 r69_9.2.2 = true := by decide +kernel
theorem c69_10 : F.repChkAG (Q.tab r69_10.1) γ nG r69_10.1 Rd cst r69_10.2.1 r69_10.2.2 = true := by decide +kernel

def D69 : List (ℕ × (ℤ × ℤ) × RepData) := [r69_0, r69_1, r69_2, r69_3, r69_4, r69_5, r69_6, r69_7, r69_8, r69_9, r69_10]

theorem chkA69 : D69.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D69, List.all_cons, List.all_nil, c69_0, c69_1, c69_2, c69_3, c69_4, c69_5, c69_6, c69_7, c69_8, c69_9, c69_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

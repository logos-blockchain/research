module

public import Cryptarchia.Prob.Certs.E20D11G.R10
meta import Cryptarchia.Prob.Certs.E20D11G.R10

/-! # E20D11G: (group, representative) entries 198 to 208, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r18_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 44 (0, 0))
def r18_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 45 (0, 0))
def r18_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 46 (0, 0))
def r18_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 47 (0, 0))
def r18_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 48 (0, 0))
def r18_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 49 (0, 0))
def r18_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 50 (0, 0))
def r18_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 51 (0, 0))
def r18_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 52 (0, 0))
def r18_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 53 (0, 0))
def r18_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 54 (0, 0))

theorem c18_0 : F.repChkAG (Q.tab r18_0.1) γ nG r18_0.1 Rd cst r18_0.2.1 r18_0.2.2 = true := by decide +kernel
theorem c18_1 : F.repChkAG (Q.tab r18_1.1) γ nG r18_1.1 Rd cst r18_1.2.1 r18_1.2.2 = true := by decide +kernel
theorem c18_2 : F.repChkAG (Q.tab r18_2.1) γ nG r18_2.1 Rd cst r18_2.2.1 r18_2.2.2 = true := by decide +kernel
theorem c18_3 : F.repChkAG (Q.tab r18_3.1) γ nG r18_3.1 Rd cst r18_3.2.1 r18_3.2.2 = true := by decide +kernel
theorem c18_4 : F.repChkAG (Q.tab r18_4.1) γ nG r18_4.1 Rd cst r18_4.2.1 r18_4.2.2 = true := by decide +kernel
theorem c18_5 : F.repChkAG (Q.tab r18_5.1) γ nG r18_5.1 Rd cst r18_5.2.1 r18_5.2.2 = true := by decide +kernel
theorem c18_6 : F.repChkAG (Q.tab r18_6.1) γ nG r18_6.1 Rd cst r18_6.2.1 r18_6.2.2 = true := by decide +kernel
theorem c18_7 : F.repChkAG (Q.tab r18_7.1) γ nG r18_7.1 Rd cst r18_7.2.1 r18_7.2.2 = true := by decide +kernel
theorem c18_8 : F.repChkAG (Q.tab r18_8.1) γ nG r18_8.1 Rd cst r18_8.2.1 r18_8.2.2 = true := by decide +kernel
theorem c18_9 : F.repChkAG (Q.tab r18_9.1) γ nG r18_9.1 Rd cst r18_9.2.1 r18_9.2.2 = true := by decide +kernel
theorem c18_10 : F.repChkAG (Q.tab r18_10.1) γ nG r18_10.1 Rd cst r18_10.2.1 r18_10.2.2 = true := by decide +kernel

def D18 : List (ℕ × (ℤ × ℤ) × RepData) := [r18_0, r18_1, r18_2, r18_3, r18_4, r18_5, r18_6, r18_7, r18_8, r18_9, r18_10]

theorem chkA18 : D18.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D18, List.all_cons, List.all_nil, c18_0, c18_1, c18_2, c18_3, c18_4, c18_5, c18_6, c18_7, c18_8, c18_9, c18_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

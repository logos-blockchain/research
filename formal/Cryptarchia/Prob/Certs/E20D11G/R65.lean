module

public import Cryptarchia.Prob.Certs.E20D11G.R57
meta import Cryptarchia.Prob.Certs.E20D11G.R57

/-! # E20D11G: (group, representative) entries 715 to 725, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r65_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 187 (0, 0))
def r65_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 188 (0, 0))
def r65_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 189 (0, 0))
def r65_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 190 (0, 0))
def r65_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 191 (0, 0))
def r65_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 192 (0, 0))
def r65_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 193 (0, 0))
def r65_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 194 (0, 0))
def r65_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 195 (0, 0))
def r65_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 196 (0, 0))
def r65_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 197 (0, 0))

theorem c65_0 : F.repChkAG (Q.tab r65_0.1) γ nG r65_0.1 Rd cst r65_0.2.1 r65_0.2.2 = true := by decide +kernel
theorem c65_1 : F.repChkAG (Q.tab r65_1.1) γ nG r65_1.1 Rd cst r65_1.2.1 r65_1.2.2 = true := by decide +kernel
theorem c65_2 : F.repChkAG (Q.tab r65_2.1) γ nG r65_2.1 Rd cst r65_2.2.1 r65_2.2.2 = true := by decide +kernel
theorem c65_3 : F.repChkAG (Q.tab r65_3.1) γ nG r65_3.1 Rd cst r65_3.2.1 r65_3.2.2 = true := by decide +kernel
theorem c65_4 : F.repChkAG (Q.tab r65_4.1) γ nG r65_4.1 Rd cst r65_4.2.1 r65_4.2.2 = true := by decide +kernel
theorem c65_5 : F.repChkAG (Q.tab r65_5.1) γ nG r65_5.1 Rd cst r65_5.2.1 r65_5.2.2 = true := by decide +kernel
theorem c65_6 : F.repChkAG (Q.tab r65_6.1) γ nG r65_6.1 Rd cst r65_6.2.1 r65_6.2.2 = true := by decide +kernel
theorem c65_7 : F.repChkAG (Q.tab r65_7.1) γ nG r65_7.1 Rd cst r65_7.2.1 r65_7.2.2 = true := by decide +kernel
theorem c65_8 : F.repChkAG (Q.tab r65_8.1) γ nG r65_8.1 Rd cst r65_8.2.1 r65_8.2.2 = true := by decide +kernel
theorem c65_9 : F.repChkAG (Q.tab r65_9.1) γ nG r65_9.1 Rd cst r65_9.2.1 r65_9.2.2 = true := by decide +kernel
theorem c65_10 : F.repChkAG (Q.tab r65_10.1) γ nG r65_10.1 Rd cst r65_10.2.1 r65_10.2.2 = true := by decide +kernel

def D65 : List (ℕ × (ℤ × ℤ) × RepData) := [r65_0, r65_1, r65_2, r65_3, r65_4, r65_5, r65_6, r65_7, r65_8, r65_9, r65_10]

theorem chkA65 : D65.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D65, List.all_cons, List.all_nil, c65_0, c65_1, c65_2, c65_3, c65_4, c65_5, c65_6, c65_7, c65_8, c65_9, c65_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

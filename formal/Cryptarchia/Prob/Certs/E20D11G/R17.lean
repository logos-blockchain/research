module

public import Cryptarchia.Prob.Certs.E20D11G.R9
meta import Cryptarchia.Prob.Certs.E20D11G.R9

/-! # E20D11G: (group, representative) entries 187 to 197, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r17_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 187 (0, 0))
def r17_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 188 (0, 0))
def r17_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 189 (0, 0))
def r17_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 190 (0, 0))
def r17_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 191 (0, 0))
def r17_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 192 (0, 0))
def r17_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 193 (0, 0))
def r17_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 194 (0, 0))
def r17_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 195 (0, 0))
def r17_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 196 (0, 0))
def r17_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (0, s, F.repDataG (Q.tab 0) γ nG 0 Rd s)) ((Q.tab 0).repList.getD 197 (0, 0))

theorem c17_0 : F.repChkAG (Q.tab r17_0.1) γ nG r17_0.1 Rd cst r17_0.2.1 r17_0.2.2 = true := by decide +kernel
theorem c17_1 : F.repChkAG (Q.tab r17_1.1) γ nG r17_1.1 Rd cst r17_1.2.1 r17_1.2.2 = true := by decide +kernel
theorem c17_2 : F.repChkAG (Q.tab r17_2.1) γ nG r17_2.1 Rd cst r17_2.2.1 r17_2.2.2 = true := by decide +kernel
theorem c17_3 : F.repChkAG (Q.tab r17_3.1) γ nG r17_3.1 Rd cst r17_3.2.1 r17_3.2.2 = true := by decide +kernel
theorem c17_4 : F.repChkAG (Q.tab r17_4.1) γ nG r17_4.1 Rd cst r17_4.2.1 r17_4.2.2 = true := by decide +kernel
theorem c17_5 : F.repChkAG (Q.tab r17_5.1) γ nG r17_5.1 Rd cst r17_5.2.1 r17_5.2.2 = true := by decide +kernel
theorem c17_6 : F.repChkAG (Q.tab r17_6.1) γ nG r17_6.1 Rd cst r17_6.2.1 r17_6.2.2 = true := by decide +kernel
theorem c17_7 : F.repChkAG (Q.tab r17_7.1) γ nG r17_7.1 Rd cst r17_7.2.1 r17_7.2.2 = true := by decide +kernel
theorem c17_8 : F.repChkAG (Q.tab r17_8.1) γ nG r17_8.1 Rd cst r17_8.2.1 r17_8.2.2 = true := by decide +kernel
theorem c17_9 : F.repChkAG (Q.tab r17_9.1) γ nG r17_9.1 Rd cst r17_9.2.1 r17_9.2.2 = true := by decide +kernel
theorem c17_10 : F.repChkAG (Q.tab r17_10.1) γ nG r17_10.1 Rd cst r17_10.2.1 r17_10.2.2 = true := by decide +kernel

def D17 : List (ℕ × (ℤ × ℤ) × RepData) := [r17_0, r17_1, r17_2, r17_3, r17_4, r17_5, r17_6, r17_7, r17_8, r17_9, r17_10]

theorem chkA17 : D17.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D17, List.all_cons, List.all_nil, c17_0, c17_1, c17_2, c17_3, c17_4, c17_5, c17_6, c17_7, c17_8, c17_9, c17_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

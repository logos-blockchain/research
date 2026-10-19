module

public import Cryptarchia.Prob.Certs.E20D11G.R83
meta import Cryptarchia.Prob.Certs.E20D11G.R83

/-! # E20D11G: (group, representative) entries 1001 to 1011, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r91_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 209 (0, 0))
def r91_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 210 (0, 0))
def r91_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 211 (0, 0))
def r91_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 212 (0, 0))
def r91_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 213 (0, 0))
def r91_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 214 (0, 0))
def r91_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 215 (0, 0))
def r91_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 216 (0, 0))
def r91_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 217 (0, 0))
def r91_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 218 (0, 0))
def r91_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 219 (0, 0))

theorem c91_0 : F.repChkAG (Q.tab r91_0.1) γ nG r91_0.1 Rd cst r91_0.2.1 r91_0.2.2 = true := by decide +kernel
theorem c91_1 : F.repChkAG (Q.tab r91_1.1) γ nG r91_1.1 Rd cst r91_1.2.1 r91_1.2.2 = true := by decide +kernel
theorem c91_2 : F.repChkAG (Q.tab r91_2.1) γ nG r91_2.1 Rd cst r91_2.2.1 r91_2.2.2 = true := by decide +kernel
theorem c91_3 : F.repChkAG (Q.tab r91_3.1) γ nG r91_3.1 Rd cst r91_3.2.1 r91_3.2.2 = true := by decide +kernel
theorem c91_4 : F.repChkAG (Q.tab r91_4.1) γ nG r91_4.1 Rd cst r91_4.2.1 r91_4.2.2 = true := by decide +kernel
theorem c91_5 : F.repChkAG (Q.tab r91_5.1) γ nG r91_5.1 Rd cst r91_5.2.1 r91_5.2.2 = true := by decide +kernel
theorem c91_6 : F.repChkAG (Q.tab r91_6.1) γ nG r91_6.1 Rd cst r91_6.2.1 r91_6.2.2 = true := by decide +kernel
theorem c91_7 : F.repChkAG (Q.tab r91_7.1) γ nG r91_7.1 Rd cst r91_7.2.1 r91_7.2.2 = true := by decide +kernel
theorem c91_8 : F.repChkAG (Q.tab r91_8.1) γ nG r91_8.1 Rd cst r91_8.2.1 r91_8.2.2 = true := by decide +kernel
theorem c91_9 : F.repChkAG (Q.tab r91_9.1) γ nG r91_9.1 Rd cst r91_9.2.1 r91_9.2.2 = true := by decide +kernel
theorem c91_10 : F.repChkAG (Q.tab r91_10.1) γ nG r91_10.1 Rd cst r91_10.2.1 r91_10.2.2 = true := by decide +kernel

def D91 : List (ℕ × (ℤ × ℤ) × RepData) := [r91_0, r91_1, r91_2, r91_3, r91_4, r91_5, r91_6, r91_7, r91_8, r91_9, r91_10]

theorem chkA91 : D91.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D91, List.all_cons, List.all_nil, c91_0, c91_1, c91_2, c91_3, c91_4, c91_5, c91_6, c91_7, c91_8, c91_9, c91_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R44
meta import Cryptarchia.Prob.Certs.E20D11G.R44

/-! # E20D11G: (group, representative) entries 572 to 582, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r52_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 110 (0, 0))
def r52_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 111 (0, 0))
def r52_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 112 (0, 0))
def r52_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 113 (0, 0))
def r52_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 114 (0, 0))
def r52_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 115 (0, 0))
def r52_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 116 (0, 0))
def r52_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 117 (0, 0))
def r52_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 118 (0, 0))
def r52_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 119 (0, 0))
def r52_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 120 (0, 0))

theorem c52_0 : F.repChkAG (Q.tab r52_0.1) γ nG r52_0.1 Rd cst r52_0.2.1 r52_0.2.2 = true := by decide +kernel
theorem c52_1 : F.repChkAG (Q.tab r52_1.1) γ nG r52_1.1 Rd cst r52_1.2.1 r52_1.2.2 = true := by decide +kernel
theorem c52_2 : F.repChkAG (Q.tab r52_2.1) γ nG r52_2.1 Rd cst r52_2.2.1 r52_2.2.2 = true := by decide +kernel
theorem c52_3 : F.repChkAG (Q.tab r52_3.1) γ nG r52_3.1 Rd cst r52_3.2.1 r52_3.2.2 = true := by decide +kernel
theorem c52_4 : F.repChkAG (Q.tab r52_4.1) γ nG r52_4.1 Rd cst r52_4.2.1 r52_4.2.2 = true := by decide +kernel
theorem c52_5 : F.repChkAG (Q.tab r52_5.1) γ nG r52_5.1 Rd cst r52_5.2.1 r52_5.2.2 = true := by decide +kernel
theorem c52_6 : F.repChkAG (Q.tab r52_6.1) γ nG r52_6.1 Rd cst r52_6.2.1 r52_6.2.2 = true := by decide +kernel
theorem c52_7 : F.repChkAG (Q.tab r52_7.1) γ nG r52_7.1 Rd cst r52_7.2.1 r52_7.2.2 = true := by decide +kernel
theorem c52_8 : F.repChkAG (Q.tab r52_8.1) γ nG r52_8.1 Rd cst r52_8.2.1 r52_8.2.2 = true := by decide +kernel
theorem c52_9 : F.repChkAG (Q.tab r52_9.1) γ nG r52_9.1 Rd cst r52_9.2.1 r52_9.2.2 = true := by decide +kernel
theorem c52_10 : F.repChkAG (Q.tab r52_10.1) γ nG r52_10.1 Rd cst r52_10.2.1 r52_10.2.2 = true := by decide +kernel

def D52 : List (ℕ × (ℤ × ℤ) × RepData) := [r52_0, r52_1, r52_2, r52_3, r52_4, r52_5, r52_6, r52_7, r52_8, r52_9, r52_10]

theorem chkA52 : D52.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D52, List.all_cons, List.all_nil, c52_0, c52_1, c52_2, c52_3, c52_4, c52_5, c52_6, c52_7, c52_8, c52_9, c52_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

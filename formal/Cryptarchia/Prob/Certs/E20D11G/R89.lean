module

public import Cryptarchia.Prob.Certs.E20D11G.R81
meta import Cryptarchia.Prob.Certs.E20D11G.R81

/-! # E20D11G: (group, representative) entries 979 to 989, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r89_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 187 (0, 0))
def r89_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 188 (0, 0))
def r89_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 189 (0, 0))
def r89_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 190 (0, 0))
def r89_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 191 (0, 0))
def r89_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 192 (0, 0))
def r89_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 193 (0, 0))
def r89_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 194 (0, 0))
def r89_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 195 (0, 0))
def r89_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 196 (0, 0))
def r89_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 197 (0, 0))

theorem c89_0 : F.repChkAG (Q.tab r89_0.1) γ nG r89_0.1 Rd cst r89_0.2.1 r89_0.2.2 = true := by decide +kernel
theorem c89_1 : F.repChkAG (Q.tab r89_1.1) γ nG r89_1.1 Rd cst r89_1.2.1 r89_1.2.2 = true := by decide +kernel
theorem c89_2 : F.repChkAG (Q.tab r89_2.1) γ nG r89_2.1 Rd cst r89_2.2.1 r89_2.2.2 = true := by decide +kernel
theorem c89_3 : F.repChkAG (Q.tab r89_3.1) γ nG r89_3.1 Rd cst r89_3.2.1 r89_3.2.2 = true := by decide +kernel
theorem c89_4 : F.repChkAG (Q.tab r89_4.1) γ nG r89_4.1 Rd cst r89_4.2.1 r89_4.2.2 = true := by decide +kernel
theorem c89_5 : F.repChkAG (Q.tab r89_5.1) γ nG r89_5.1 Rd cst r89_5.2.1 r89_5.2.2 = true := by decide +kernel
theorem c89_6 : F.repChkAG (Q.tab r89_6.1) γ nG r89_6.1 Rd cst r89_6.2.1 r89_6.2.2 = true := by decide +kernel
theorem c89_7 : F.repChkAG (Q.tab r89_7.1) γ nG r89_7.1 Rd cst r89_7.2.1 r89_7.2.2 = true := by decide +kernel
theorem c89_8 : F.repChkAG (Q.tab r89_8.1) γ nG r89_8.1 Rd cst r89_8.2.1 r89_8.2.2 = true := by decide +kernel
theorem c89_9 : F.repChkAG (Q.tab r89_9.1) γ nG r89_9.1 Rd cst r89_9.2.1 r89_9.2.2 = true := by decide +kernel
theorem c89_10 : F.repChkAG (Q.tab r89_10.1) γ nG r89_10.1 Rd cst r89_10.2.1 r89_10.2.2 = true := by decide +kernel

def D89 : List (ℕ × (ℤ × ℤ) × RepData) := [r89_0, r89_1, r89_2, r89_3, r89_4, r89_5, r89_6, r89_7, r89_8, r89_9, r89_10]

theorem chkA89 : D89.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D89, List.all_cons, List.all_nil, c89_0, c89_1, c89_2, c89_3, c89_4, c89_5, c89_6, c89_7, c89_8, c89_9, c89_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

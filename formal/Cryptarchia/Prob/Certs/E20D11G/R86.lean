module

public import Cryptarchia.Prob.Certs.E20D11G.R78
meta import Cryptarchia.Prob.Certs.E20D11G.R78

/-! # E20D11G: (group, representative) entries 946 to 956, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r86_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 154 (0, 0))
def r86_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 155 (0, 0))
def r86_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 156 (0, 0))
def r86_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 157 (0, 0))
def r86_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 158 (0, 0))
def r86_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 159 (0, 0))
def r86_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 160 (0, 0))
def r86_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 161 (0, 0))
def r86_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 162 (0, 0))
def r86_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 163 (0, 0))
def r86_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 164 (0, 0))

theorem c86_0 : F.repChkAG (Q.tab r86_0.1) γ nG r86_0.1 Rd cst r86_0.2.1 r86_0.2.2 = true := by decide +kernel
theorem c86_1 : F.repChkAG (Q.tab r86_1.1) γ nG r86_1.1 Rd cst r86_1.2.1 r86_1.2.2 = true := by decide +kernel
theorem c86_2 : F.repChkAG (Q.tab r86_2.1) γ nG r86_2.1 Rd cst r86_2.2.1 r86_2.2.2 = true := by decide +kernel
theorem c86_3 : F.repChkAG (Q.tab r86_3.1) γ nG r86_3.1 Rd cst r86_3.2.1 r86_3.2.2 = true := by decide +kernel
theorem c86_4 : F.repChkAG (Q.tab r86_4.1) γ nG r86_4.1 Rd cst r86_4.2.1 r86_4.2.2 = true := by decide +kernel
theorem c86_5 : F.repChkAG (Q.tab r86_5.1) γ nG r86_5.1 Rd cst r86_5.2.1 r86_5.2.2 = true := by decide +kernel
theorem c86_6 : F.repChkAG (Q.tab r86_6.1) γ nG r86_6.1 Rd cst r86_6.2.1 r86_6.2.2 = true := by decide +kernel
theorem c86_7 : F.repChkAG (Q.tab r86_7.1) γ nG r86_7.1 Rd cst r86_7.2.1 r86_7.2.2 = true := by decide +kernel
theorem c86_8 : F.repChkAG (Q.tab r86_8.1) γ nG r86_8.1 Rd cst r86_8.2.1 r86_8.2.2 = true := by decide +kernel
theorem c86_9 : F.repChkAG (Q.tab r86_9.1) γ nG r86_9.1 Rd cst r86_9.2.1 r86_9.2.2 = true := by decide +kernel
theorem c86_10 : F.repChkAG (Q.tab r86_10.1) γ nG r86_10.1 Rd cst r86_10.2.1 r86_10.2.2 = true := by decide +kernel

def D86 : List (ℕ × (ℤ × ℤ) × RepData) := [r86_0, r86_1, r86_2, r86_3, r86_4, r86_5, r86_6, r86_7, r86_8, r86_9, r86_10]

theorem chkA86 : D86.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd cst p.2.1 p.2.2) = true := by
  simp only [D86, List.all_cons, List.all_nil, c86_0, c86_1, c86_2, c86_3, c86_4, c86_5, c86_6, c86_7, c86_8, c86_9, c86_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

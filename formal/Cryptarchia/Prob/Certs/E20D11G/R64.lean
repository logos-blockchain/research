module

public import Cryptarchia.Prob.Certs.E20D11G.R56
meta import Cryptarchia.Prob.Certs.E20D11G.R56

/-! # E20D11G: (group, representative) entries 704 to 714, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r64_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 176 (0, 0))
def r64_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 177 (0, 0))
def r64_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 178 (0, 0))
def r64_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 179 (0, 0))
def r64_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 180 (0, 0))
def r64_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 181 (0, 0))
def r64_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 182 (0, 0))
def r64_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 183 (0, 0))
def r64_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 184 (0, 0))
def r64_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 185 (0, 0))
def r64_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ nG 2 Rd s)) ((Q.tab 2).repList.getD 186 (0, 0))

theorem c64_0 : F.repChkAG (Q.tab r64_0.1) γ nG r64_0.1 Rd r64_0.2.1 r64_0.2.2 = true := by decide +kernel
theorem c64_1 : F.repChkAG (Q.tab r64_1.1) γ nG r64_1.1 Rd r64_1.2.1 r64_1.2.2 = true := by decide +kernel
theorem c64_2 : F.repChkAG (Q.tab r64_2.1) γ nG r64_2.1 Rd r64_2.2.1 r64_2.2.2 = true := by decide +kernel
theorem c64_3 : F.repChkAG (Q.tab r64_3.1) γ nG r64_3.1 Rd r64_3.2.1 r64_3.2.2 = true := by decide +kernel
theorem c64_4 : F.repChkAG (Q.tab r64_4.1) γ nG r64_4.1 Rd r64_4.2.1 r64_4.2.2 = true := by decide +kernel
theorem c64_5 : F.repChkAG (Q.tab r64_5.1) γ nG r64_5.1 Rd r64_5.2.1 r64_5.2.2 = true := by decide +kernel
theorem c64_6 : F.repChkAG (Q.tab r64_6.1) γ nG r64_6.1 Rd r64_6.2.1 r64_6.2.2 = true := by decide +kernel
theorem c64_7 : F.repChkAG (Q.tab r64_7.1) γ nG r64_7.1 Rd r64_7.2.1 r64_7.2.2 = true := by decide +kernel
theorem c64_8 : F.repChkAG (Q.tab r64_8.1) γ nG r64_8.1 Rd r64_8.2.1 r64_8.2.2 = true := by decide +kernel
theorem c64_9 : F.repChkAG (Q.tab r64_9.1) γ nG r64_9.1 Rd r64_9.2.1 r64_9.2.2 = true := by decide +kernel
theorem c64_10 : F.repChkAG (Q.tab r64_10.1) γ nG r64_10.1 Rd r64_10.2.1 r64_10.2.2 = true := by decide +kernel

def D64 : List (ℕ × (ℤ × ℤ) × RepData) := [r64_0, r64_1, r64_2, r64_3, r64_4, r64_5, r64_6, r64_7, r64_8, r64_9, r64_10]

theorem chkA64 : D64.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D64, List.all_cons, List.all_nil, c64_0, c64_1, c64_2, c64_3, c64_4, c64_5, c64_6, c64_7, c64_8, c64_9, c64_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

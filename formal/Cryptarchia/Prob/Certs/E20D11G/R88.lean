module

public import Cryptarchia.Prob.Certs.E20D11G.R80
meta import Cryptarchia.Prob.Certs.E20D11G.R80

/-! # E20D11G: (group, representative) entries 968 to 978, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r88_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 176 (0, 0))
def r88_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 177 (0, 0))
def r88_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 178 (0, 0))
def r88_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 179 (0, 0))
def r88_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 180 (0, 0))
def r88_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 181 (0, 0))
def r88_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 182 (0, 0))
def r88_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 183 (0, 0))
def r88_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 184 (0, 0))
def r88_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 185 (0, 0))
def r88_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 186 (0, 0))

theorem c88_0 : F.repChkAG (Q.tab r88_0.1) γ nG r88_0.1 Rd r88_0.2.1 r88_0.2.2 = true := by decide +kernel
theorem c88_1 : F.repChkAG (Q.tab r88_1.1) γ nG r88_1.1 Rd r88_1.2.1 r88_1.2.2 = true := by decide +kernel
theorem c88_2 : F.repChkAG (Q.tab r88_2.1) γ nG r88_2.1 Rd r88_2.2.1 r88_2.2.2 = true := by decide +kernel
theorem c88_3 : F.repChkAG (Q.tab r88_3.1) γ nG r88_3.1 Rd r88_3.2.1 r88_3.2.2 = true := by decide +kernel
theorem c88_4 : F.repChkAG (Q.tab r88_4.1) γ nG r88_4.1 Rd r88_4.2.1 r88_4.2.2 = true := by decide +kernel
theorem c88_5 : F.repChkAG (Q.tab r88_5.1) γ nG r88_5.1 Rd r88_5.2.1 r88_5.2.2 = true := by decide +kernel
theorem c88_6 : F.repChkAG (Q.tab r88_6.1) γ nG r88_6.1 Rd r88_6.2.1 r88_6.2.2 = true := by decide +kernel
theorem c88_7 : F.repChkAG (Q.tab r88_7.1) γ nG r88_7.1 Rd r88_7.2.1 r88_7.2.2 = true := by decide +kernel
theorem c88_8 : F.repChkAG (Q.tab r88_8.1) γ nG r88_8.1 Rd r88_8.2.1 r88_8.2.2 = true := by decide +kernel
theorem c88_9 : F.repChkAG (Q.tab r88_9.1) γ nG r88_9.1 Rd r88_9.2.1 r88_9.2.2 = true := by decide +kernel
theorem c88_10 : F.repChkAG (Q.tab r88_10.1) γ nG r88_10.1 Rd r88_10.2.1 r88_10.2.2 = true := by decide +kernel

def D88 : List (ℕ × (ℤ × ℤ) × RepData) := [r88_0, r88_1, r88_2, r88_3, r88_4, r88_5, r88_6, r88_7, r88_8, r88_9, r88_10]

theorem chkA88 : D88.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D88, List.all_cons, List.all_nil, c88_0, c88_1, c88_2, c88_3, c88_4, c88_5, c88_6, c88_7, c88_8, c88_9, c88_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R68
meta import Cryptarchia.Prob.Certs.E20D11G.R68

/-! # E20D11G: (group, representative) entries 836 to 846, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r76_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 44 (0, 0))
def r76_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 45 (0, 0))
def r76_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 46 (0, 0))
def r76_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 47 (0, 0))
def r76_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 48 (0, 0))
def r76_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 49 (0, 0))
def r76_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 50 (0, 0))
def r76_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 51 (0, 0))
def r76_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 52 (0, 0))
def r76_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 53 (0, 0))
def r76_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ nG 3 Rd s)) ((Q.tab 3).repList.getD 54 (0, 0))

theorem c76_0 : F.repChkAG (Q.tab r76_0.1) γ nG r76_0.1 Rd r76_0.2.1 r76_0.2.2 = true := by decide +kernel
theorem c76_1 : F.repChkAG (Q.tab r76_1.1) γ nG r76_1.1 Rd r76_1.2.1 r76_1.2.2 = true := by decide +kernel
theorem c76_2 : F.repChkAG (Q.tab r76_2.1) γ nG r76_2.1 Rd r76_2.2.1 r76_2.2.2 = true := by decide +kernel
theorem c76_3 : F.repChkAG (Q.tab r76_3.1) γ nG r76_3.1 Rd r76_3.2.1 r76_3.2.2 = true := by decide +kernel
theorem c76_4 : F.repChkAG (Q.tab r76_4.1) γ nG r76_4.1 Rd r76_4.2.1 r76_4.2.2 = true := by decide +kernel
theorem c76_5 : F.repChkAG (Q.tab r76_5.1) γ nG r76_5.1 Rd r76_5.2.1 r76_5.2.2 = true := by decide +kernel
theorem c76_6 : F.repChkAG (Q.tab r76_6.1) γ nG r76_6.1 Rd r76_6.2.1 r76_6.2.2 = true := by decide +kernel
theorem c76_7 : F.repChkAG (Q.tab r76_7.1) γ nG r76_7.1 Rd r76_7.2.1 r76_7.2.2 = true := by decide +kernel
theorem c76_8 : F.repChkAG (Q.tab r76_8.1) γ nG r76_8.1 Rd r76_8.2.1 r76_8.2.2 = true := by decide +kernel
theorem c76_9 : F.repChkAG (Q.tab r76_9.1) γ nG r76_9.1 Rd r76_9.2.1 r76_9.2.2 = true := by decide +kernel
theorem c76_10 : F.repChkAG (Q.tab r76_10.1) γ nG r76_10.1 Rd r76_10.2.1 r76_10.2.2 = true := by decide +kernel

def D76 : List (ℕ × (ℤ × ℤ) × RepData) := [r76_0, r76_1, r76_2, r76_3, r76_4, r76_5, r76_6, r76_7, r76_8, r76_9, r76_10]

theorem chkA76 : D76.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D76, List.all_cons, List.all_nil, c76_0, c76_1, c76_2, c76_3, c76_4, c76_5, c76_6, c76_7, c76_8, c76_9, c76_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

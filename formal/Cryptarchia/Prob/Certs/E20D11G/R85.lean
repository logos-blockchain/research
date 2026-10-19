module

public import Cryptarchia.Prob.Certs.E20D11G.R81
meta import Cryptarchia.Prob.Certs.E20D11G.R81

/-! # E20D11G: (group, representative) entries 935 to 945, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r85_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 143 (0, 0))
def r85_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 144 (0, 0))
def r85_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 145 (0, 0))
def r85_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 146 (0, 0))
def r85_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 147 (0, 0))
def r85_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 148 (0, 0))
def r85_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 149 (0, 0))
def r85_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 150 (0, 0))
def r85_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 151 (0, 0))
def r85_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 152 (0, 0))
def r85_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 153 (0, 0))

theorem c85_0 : F.repChkAG (Q.tab r85_0.1) γ r85_0.2.1 r85_0.2.2 = true := by decide +kernel
theorem c85_1 : F.repChkAG (Q.tab r85_1.1) γ r85_1.2.1 r85_1.2.2 = true := by decide +kernel
theorem c85_2 : F.repChkAG (Q.tab r85_2.1) γ r85_2.2.1 r85_2.2.2 = true := by decide +kernel
theorem c85_3 : F.repChkAG (Q.tab r85_3.1) γ r85_3.2.1 r85_3.2.2 = true := by decide +kernel
theorem c85_4 : F.repChkAG (Q.tab r85_4.1) γ r85_4.2.1 r85_4.2.2 = true := by decide +kernel
theorem c85_5 : F.repChkAG (Q.tab r85_5.1) γ r85_5.2.1 r85_5.2.2 = true := by decide +kernel
theorem c85_6 : F.repChkAG (Q.tab r85_6.1) γ r85_6.2.1 r85_6.2.2 = true := by decide +kernel
theorem c85_7 : F.repChkAG (Q.tab r85_7.1) γ r85_7.2.1 r85_7.2.2 = true := by decide +kernel
theorem c85_8 : F.repChkAG (Q.tab r85_8.1) γ r85_8.2.1 r85_8.2.2 = true := by decide +kernel
theorem c85_9 : F.repChkAG (Q.tab r85_9.1) γ r85_9.2.1 r85_9.2.2 = true := by decide +kernel
theorem c85_10 : F.repChkAG (Q.tab r85_10.1) γ r85_10.2.1 r85_10.2.2 = true := by decide +kernel

def D85 : List (ℕ × (ℤ × ℤ) × RepData) := [r85_0, r85_1, r85_2, r85_3, r85_4, r85_5, r85_6, r85_7, r85_8, r85_9, r85_10]

theorem chkA85 : D85.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D85, List.all_cons, List.all_nil, c85_0, c85_1, c85_2, c85_3, c85_4, c85_5, c85_6, c85_7, c85_8, c85_9, c85_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

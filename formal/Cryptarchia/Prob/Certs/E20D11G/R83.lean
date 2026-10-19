module

public import Cryptarchia.Prob.Certs.E20D11G.R79
meta import Cryptarchia.Prob.Certs.E20D11G.R79

/-! # E20D11G: (group, representative) entries 913 to 923, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r83_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 121 (0, 0))
def r83_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 122 (0, 0))
def r83_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 123 (0, 0))
def r83_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 124 (0, 0))
def r83_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 125 (0, 0))
def r83_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 126 (0, 0))
def r83_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 127 (0, 0))
def r83_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 128 (0, 0))
def r83_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 129 (0, 0))
def r83_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 130 (0, 0))
def r83_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 131 (0, 0))

theorem c83_0 : F.repChkAG (Q.tab r83_0.1) γ r83_0.2.1 r83_0.2.2 = true := by decide +kernel
theorem c83_1 : F.repChkAG (Q.tab r83_1.1) γ r83_1.2.1 r83_1.2.2 = true := by decide +kernel
theorem c83_2 : F.repChkAG (Q.tab r83_2.1) γ r83_2.2.1 r83_2.2.2 = true := by decide +kernel
theorem c83_3 : F.repChkAG (Q.tab r83_3.1) γ r83_3.2.1 r83_3.2.2 = true := by decide +kernel
theorem c83_4 : F.repChkAG (Q.tab r83_4.1) γ r83_4.2.1 r83_4.2.2 = true := by decide +kernel
theorem c83_5 : F.repChkAG (Q.tab r83_5.1) γ r83_5.2.1 r83_5.2.2 = true := by decide +kernel
theorem c83_6 : F.repChkAG (Q.tab r83_6.1) γ r83_6.2.1 r83_6.2.2 = true := by decide +kernel
theorem c83_7 : F.repChkAG (Q.tab r83_7.1) γ r83_7.2.1 r83_7.2.2 = true := by decide +kernel
theorem c83_8 : F.repChkAG (Q.tab r83_8.1) γ r83_8.2.1 r83_8.2.2 = true := by decide +kernel
theorem c83_9 : F.repChkAG (Q.tab r83_9.1) γ r83_9.2.1 r83_9.2.2 = true := by decide +kernel
theorem c83_10 : F.repChkAG (Q.tab r83_10.1) γ r83_10.2.1 r83_10.2.2 = true := by decide +kernel

def D83 : List (ℕ × (ℤ × ℤ) × RepData) := [r83_0, r83_1, r83_2, r83_3, r83_4, r83_5, r83_6, r83_7, r83_8, r83_9, r83_10]

theorem chkA83 : D83.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D83, List.all_cons, List.all_nil, c83_0, c83_1, c83_2, c83_3, c83_4, c83_5, c83_6, c83_7, c83_8, c83_9, c83_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

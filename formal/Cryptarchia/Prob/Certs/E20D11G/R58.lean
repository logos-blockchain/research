module

public import Cryptarchia.Prob.Certs.E20D11G.R54
meta import Cryptarchia.Prob.Certs.E20D11G.R54

/-! # E20D11G: (group, representative) entries 638 to 648, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r58_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 110 (0, 0))
def r58_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 111 (0, 0))
def r58_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 112 (0, 0))
def r58_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 113 (0, 0))
def r58_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 114 (0, 0))
def r58_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 115 (0, 0))
def r58_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 116 (0, 0))
def r58_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 117 (0, 0))
def r58_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 118 (0, 0))
def r58_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 119 (0, 0))
def r58_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (2, s, F.repDataG (Q.tab 2) γ s)) ((Q.tab 2).repList.getD 120 (0, 0))

theorem c58_0 : F.repChkAG (Q.tab r58_0.1) γ r58_0.2.1 r58_0.2.2 = true := by decide +kernel
theorem c58_1 : F.repChkAG (Q.tab r58_1.1) γ r58_1.2.1 r58_1.2.2 = true := by decide +kernel
theorem c58_2 : F.repChkAG (Q.tab r58_2.1) γ r58_2.2.1 r58_2.2.2 = true := by decide +kernel
theorem c58_3 : F.repChkAG (Q.tab r58_3.1) γ r58_3.2.1 r58_3.2.2 = true := by decide +kernel
theorem c58_4 : F.repChkAG (Q.tab r58_4.1) γ r58_4.2.1 r58_4.2.2 = true := by decide +kernel
theorem c58_5 : F.repChkAG (Q.tab r58_5.1) γ r58_5.2.1 r58_5.2.2 = true := by decide +kernel
theorem c58_6 : F.repChkAG (Q.tab r58_6.1) γ r58_6.2.1 r58_6.2.2 = true := by decide +kernel
theorem c58_7 : F.repChkAG (Q.tab r58_7.1) γ r58_7.2.1 r58_7.2.2 = true := by decide +kernel
theorem c58_8 : F.repChkAG (Q.tab r58_8.1) γ r58_8.2.1 r58_8.2.2 = true := by decide +kernel
theorem c58_9 : F.repChkAG (Q.tab r58_9.1) γ r58_9.2.1 r58_9.2.2 = true := by decide +kernel
theorem c58_10 : F.repChkAG (Q.tab r58_10.1) γ r58_10.2.1 r58_10.2.2 = true := by decide +kernel

def D58 : List (ℕ × (ℤ × ℤ) × RepData) := [r58_0, r58_1, r58_2, r58_3, r58_4, r58_5, r58_6, r58_7, r58_8, r58_9, r58_10]

theorem chkA58 : D58.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D58, List.all_cons, List.all_nil, c58_0, c58_1, c58_2, c58_3, c58_4, c58_5, c58_6, c58_7, c58_8, c58_9, c58_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

module

public import Cryptarchia.Prob.Certs.E20D11G.R88
meta import Cryptarchia.Prob.Certs.E20D11G.R88

/-! # E20D11G: (group, representative) entries 1012 to 1022, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r92_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 220 (0, 0))
def r92_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 221 (0, 0))
def r92_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 222 (0, 0))
def r92_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 223 (0, 0))
def r92_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 224 (0, 0))
def r92_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 225 (0, 0))
def r92_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 226 (0, 0))
def r92_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 227 (0, 0))
def r92_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 228 (0, 0))
def r92_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 229 (0, 0))
def r92_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (3, s, F.repDataG (Q.tab 3) γ s)) ((Q.tab 3).repList.getD 230 (0, 0))

theorem c92_0 : F.repChkAG (Q.tab r92_0.1) γ r92_0.2.1 r92_0.2.2 = true := by decide +kernel
theorem c92_1 : F.repChkAG (Q.tab r92_1.1) γ r92_1.2.1 r92_1.2.2 = true := by decide +kernel
theorem c92_2 : F.repChkAG (Q.tab r92_2.1) γ r92_2.2.1 r92_2.2.2 = true := by decide +kernel
theorem c92_3 : F.repChkAG (Q.tab r92_3.1) γ r92_3.2.1 r92_3.2.2 = true := by decide +kernel
theorem c92_4 : F.repChkAG (Q.tab r92_4.1) γ r92_4.2.1 r92_4.2.2 = true := by decide +kernel
theorem c92_5 : F.repChkAG (Q.tab r92_5.1) γ r92_5.2.1 r92_5.2.2 = true := by decide +kernel
theorem c92_6 : F.repChkAG (Q.tab r92_6.1) γ r92_6.2.1 r92_6.2.2 = true := by decide +kernel
theorem c92_7 : F.repChkAG (Q.tab r92_7.1) γ r92_7.2.1 r92_7.2.2 = true := by decide +kernel
theorem c92_8 : F.repChkAG (Q.tab r92_8.1) γ r92_8.2.1 r92_8.2.2 = true := by decide +kernel
theorem c92_9 : F.repChkAG (Q.tab r92_9.1) γ r92_9.2.1 r92_9.2.2 = true := by decide +kernel
theorem c92_10 : F.repChkAG (Q.tab r92_10.1) γ r92_10.2.1 r92_10.2.2 = true := by decide +kernel

def D92 : List (ℕ × (ℤ × ℤ) × RepData) := [r92_0, r92_1, r92_2, r92_3, r92_4, r92_5, r92_6, r92_7, r92_8, r92_9, r92_10]

theorem chkA92 : D92.all (fun p => F.repChkAG (Q.tab p.1) γ p.2.1 p.2.2) = true := by
  simp only [D92, List.all_cons, List.all_nil, c92_0, c92_1, c92_2, c92_3, c92_4, c92_5, c92_6, c92_7, c92_8, c92_9, c92_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

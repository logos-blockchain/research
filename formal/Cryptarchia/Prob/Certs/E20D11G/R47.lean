module

public import Cryptarchia.Prob.Certs.E20D11G.R39
meta import Cryptarchia.Prob.Certs.E20D11G.R39

/-! # E20D11G: (group, representative) entries 517 to 527, their data
computed at elaboration time (`FamCfg.repDataG`) and their tables checked (`FamCfg.repChkAG`), one kernel
check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11G

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r47_0 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 253 (0, 0))
def r47_1 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 254 (0, 0))
def r47_2 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 255 (0, 0))
def r47_3 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 256 (0, 0))
def r47_4 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 257 (0, 0))
def r47_5 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 258 (0, 0))
def r47_6 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 259 (0, 0))
def r47_7 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 260 (0, 0))
def r47_8 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 261 (0, 0))
def r47_9 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 262 (0, 0))
def r47_10 : ℕ × (ℤ × ℤ) × RepData := eval% (fun s => (1, s, F.repDataG (Q.tab 1) γ nG 1 Rd s)) ((Q.tab 1).repList.getD 263 (0, 0))

theorem c47_0 : F.repChkAG (Q.tab r47_0.1) γ nG r47_0.1 Rd r47_0.2.1 r47_0.2.2 = true := by decide +kernel
theorem c47_1 : F.repChkAG (Q.tab r47_1.1) γ nG r47_1.1 Rd r47_1.2.1 r47_1.2.2 = true := by decide +kernel
theorem c47_2 : F.repChkAG (Q.tab r47_2.1) γ nG r47_2.1 Rd r47_2.2.1 r47_2.2.2 = true := by decide +kernel
theorem c47_3 : F.repChkAG (Q.tab r47_3.1) γ nG r47_3.1 Rd r47_3.2.1 r47_3.2.2 = true := by decide +kernel
theorem c47_4 : F.repChkAG (Q.tab r47_4.1) γ nG r47_4.1 Rd r47_4.2.1 r47_4.2.2 = true := by decide +kernel
theorem c47_5 : F.repChkAG (Q.tab r47_5.1) γ nG r47_5.1 Rd r47_5.2.1 r47_5.2.2 = true := by decide +kernel
theorem c47_6 : F.repChkAG (Q.tab r47_6.1) γ nG r47_6.1 Rd r47_6.2.1 r47_6.2.2 = true := by decide +kernel
theorem c47_7 : F.repChkAG (Q.tab r47_7.1) γ nG r47_7.1 Rd r47_7.2.1 r47_7.2.2 = true := by decide +kernel
theorem c47_8 : F.repChkAG (Q.tab r47_8.1) γ nG r47_8.1 Rd r47_8.2.1 r47_8.2.2 = true := by decide +kernel
theorem c47_9 : F.repChkAG (Q.tab r47_9.1) γ nG r47_9.1 Rd r47_9.2.1 r47_9.2.2 = true := by decide +kernel
theorem c47_10 : F.repChkAG (Q.tab r47_10.1) γ nG r47_10.1 Rd r47_10.2.1 r47_10.2.2 = true := by decide +kernel

def D47 : List (ℕ × (ℤ × ℤ) × RepData) := [r47_0, r47_1, r47_2, r47_3, r47_4, r47_5, r47_6, r47_7, r47_8, r47_9, r47_10]

theorem chkA47 : D47.all (fun p => F.repChkAG (Q.tab p.1) γ nG p.1 Rd p.2.1 p.2.2) = true := by
  simp only [D47, List.all_cons, List.all_nil, c47_0, c47_1, c47_2, c47_3, c47_4, c47_5, c47_6, c47_7, c47_8, c47_9, c47_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11G

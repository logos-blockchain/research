module

public import Cryptarchia.Prob.Certs.E20D11T.R5
meta import Cryptarchia.Prob.Certs.E20D11T.R5

/-! # E20D11T: representatives 99 to 109, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r9_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 99 (0, 0))
def r9_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 100 (0, 0))
def r9_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 101 (0, 0))
def r9_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 102 (0, 0))
def r9_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 103 (0, 0))
def r9_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 104 (0, 0))
def r9_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 105 (0, 0))
def r9_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 106 (0, 0))
def r9_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 107 (0, 0))
def r9_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 108 (0, 0))
def r9_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 109 (0, 0))

theorem c9_0 : F.repChkA Q r9_0.1 r9_0.2 = true := by decide +kernel
theorem c9_1 : F.repChkA Q r9_1.1 r9_1.2 = true := by decide +kernel
theorem c9_2 : F.repChkA Q r9_2.1 r9_2.2 = true := by decide +kernel
theorem c9_3 : F.repChkA Q r9_3.1 r9_3.2 = true := by decide +kernel
theorem c9_4 : F.repChkA Q r9_4.1 r9_4.2 = true := by decide +kernel
theorem c9_5 : F.repChkA Q r9_5.1 r9_5.2 = true := by decide +kernel
theorem c9_6 : F.repChkA Q r9_6.1 r9_6.2 = true := by decide +kernel
theorem c9_7 : F.repChkA Q r9_7.1 r9_7.2 = true := by decide +kernel
theorem c9_8 : F.repChkA Q r9_8.1 r9_8.2 = true := by decide +kernel
theorem c9_9 : F.repChkA Q r9_9.1 r9_9.2 = true := by decide +kernel
theorem c9_10 : F.repChkA Q r9_10.1 r9_10.2 = true := by decide +kernel

def D9 : List ((ℤ × ℤ) × RepData) := [r9_0, r9_1, r9_2, r9_3, r9_4, r9_5, r9_6, r9_7, r9_8, r9_9, r9_10]

theorem chkA9 : D9.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D9, List.all_cons, List.all_nil, c9_0, c9_1, c9_2, c9_3, c9_4, c9_5, c9_6, c9_7, c9_8, c9_9, c9_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

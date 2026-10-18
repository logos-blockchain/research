module

public import Cryptarchia.Prob.Certs.E20D11T.R6
meta import Cryptarchia.Prob.Certs.E20D11T.R6

/-! # E20D11T: representatives 110 to 120, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r10_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 110 (0, 0))
def r10_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 111 (0, 0))
def r10_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 112 (0, 0))
def r10_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 113 (0, 0))
def r10_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 114 (0, 0))
def r10_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 115 (0, 0))
def r10_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 116 (0, 0))
def r10_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 117 (0, 0))
def r10_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 118 (0, 0))
def r10_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 119 (0, 0))
def r10_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 120 (0, 0))

theorem c10_0 : F.repChkA Q r10_0.1 r10_0.2 = true := by decide +kernel
theorem c10_1 : F.repChkA Q r10_1.1 r10_1.2 = true := by decide +kernel
theorem c10_2 : F.repChkA Q r10_2.1 r10_2.2 = true := by decide +kernel
theorem c10_3 : F.repChkA Q r10_3.1 r10_3.2 = true := by decide +kernel
theorem c10_4 : F.repChkA Q r10_4.1 r10_4.2 = true := by decide +kernel
theorem c10_5 : F.repChkA Q r10_5.1 r10_5.2 = true := by decide +kernel
theorem c10_6 : F.repChkA Q r10_6.1 r10_6.2 = true := by decide +kernel
theorem c10_7 : F.repChkA Q r10_7.1 r10_7.2 = true := by decide +kernel
theorem c10_8 : F.repChkA Q r10_8.1 r10_8.2 = true := by decide +kernel
theorem c10_9 : F.repChkA Q r10_9.1 r10_9.2 = true := by decide +kernel
theorem c10_10 : F.repChkA Q r10_10.1 r10_10.2 = true := by decide +kernel

def D10 : List ((ℤ × ℤ) × RepData) := [r10_0, r10_1, r10_2, r10_3, r10_4, r10_5, r10_6, r10_7, r10_8, r10_9, r10_10]

theorem chkA10 : D10.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D10, List.all_cons, List.all_nil, c10_0, c10_1, c10_2, c10_3, c10_4, c10_5, c10_6, c10_7, c10_8, c10_9, c10_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

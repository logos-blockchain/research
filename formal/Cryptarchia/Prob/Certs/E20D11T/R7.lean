module

public import Cryptarchia.Prob.Certs.E20D11T.R3
meta import Cryptarchia.Prob.Certs.E20D11T.R3

/-! # E20D11T: representatives 77 to 87, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r7_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 77 (0, 0))
def r7_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 78 (0, 0))
def r7_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 79 (0, 0))
def r7_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 80 (0, 0))
def r7_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 81 (0, 0))
def r7_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 82 (0, 0))
def r7_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 83 (0, 0))
def r7_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 84 (0, 0))
def r7_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 85 (0, 0))
def r7_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 86 (0, 0))
def r7_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 87 (0, 0))

theorem c7_0 : F.repChkA Q r7_0.1 r7_0.2 = true := by decide +kernel
theorem c7_1 : F.repChkA Q r7_1.1 r7_1.2 = true := by decide +kernel
theorem c7_2 : F.repChkA Q r7_2.1 r7_2.2 = true := by decide +kernel
theorem c7_3 : F.repChkA Q r7_3.1 r7_3.2 = true := by decide +kernel
theorem c7_4 : F.repChkA Q r7_4.1 r7_4.2 = true := by decide +kernel
theorem c7_5 : F.repChkA Q r7_5.1 r7_5.2 = true := by decide +kernel
theorem c7_6 : F.repChkA Q r7_6.1 r7_6.2 = true := by decide +kernel
theorem c7_7 : F.repChkA Q r7_7.1 r7_7.2 = true := by decide +kernel
theorem c7_8 : F.repChkA Q r7_8.1 r7_8.2 = true := by decide +kernel
theorem c7_9 : F.repChkA Q r7_9.1 r7_9.2 = true := by decide +kernel
theorem c7_10 : F.repChkA Q r7_10.1 r7_10.2 = true := by decide +kernel

def D7 : List ((ℤ × ℤ) × RepData) := [r7_0, r7_1, r7_2, r7_3, r7_4, r7_5, r7_6, r7_7, r7_8, r7_9, r7_10]

theorem chkA7 : D7.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D7, List.all_cons, List.all_nil, c7_0, c7_1, c7_2, c7_3, c7_4, c7_5, c7_6, c7_7, c7_8, c7_9, c7_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

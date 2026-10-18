module

public import Cryptarchia.Prob.Certs.E20D11T.Tab
meta import Cryptarchia.Prob.Certs.E20D11T.Tab

/-! # E20D11T: representatives 0 to 10, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r0_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 0 (0, 0))
def r0_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 1 (0, 0))
def r0_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 2 (0, 0))
def r0_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 3 (0, 0))
def r0_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 4 (0, 0))
def r0_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 5 (0, 0))
def r0_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 6 (0, 0))
def r0_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 7 (0, 0))
def r0_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 8 (0, 0))
def r0_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 9 (0, 0))
def r0_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 10 (0, 0))

theorem c0_0 : F.repChkA Q r0_0.1 r0_0.2 = true := by decide +kernel
theorem c0_1 : F.repChkA Q r0_1.1 r0_1.2 = true := by decide +kernel
theorem c0_2 : F.repChkA Q r0_2.1 r0_2.2 = true := by decide +kernel
theorem c0_3 : F.repChkA Q r0_3.1 r0_3.2 = true := by decide +kernel
theorem c0_4 : F.repChkA Q r0_4.1 r0_4.2 = true := by decide +kernel
theorem c0_5 : F.repChkA Q r0_5.1 r0_5.2 = true := by decide +kernel
theorem c0_6 : F.repChkA Q r0_6.1 r0_6.2 = true := by decide +kernel
theorem c0_7 : F.repChkA Q r0_7.1 r0_7.2 = true := by decide +kernel
theorem c0_8 : F.repChkA Q r0_8.1 r0_8.2 = true := by decide +kernel
theorem c0_9 : F.repChkA Q r0_9.1 r0_9.2 = true := by decide +kernel
theorem c0_10 : F.repChkA Q r0_10.1 r0_10.2 = true := by decide +kernel

def D0 : List ((ℤ × ℤ) × RepData) := [r0_0, r0_1, r0_2, r0_3, r0_4, r0_5, r0_6, r0_7, r0_8, r0_9, r0_10]

theorem chkA0 : D0.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D0, List.all_cons, List.all_nil, c0_0, c0_1, c0_2, c0_3, c0_4, c0_5, c0_6, c0_7, c0_8, c0_9, c0_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

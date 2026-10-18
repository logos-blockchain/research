module

public import Cryptarchia.Prob.Certs.E20D11T.Tab
meta import Cryptarchia.Prob.Certs.E20D11T.Tab

/-! # E20D11T: representatives 11 to 21, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r1_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 11 (0, 0))
def r1_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 12 (0, 0))
def r1_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 13 (0, 0))
def r1_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 14 (0, 0))
def r1_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 15 (0, 0))
def r1_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 16 (0, 0))
def r1_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 17 (0, 0))
def r1_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 18 (0, 0))
def r1_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 19 (0, 0))
def r1_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 20 (0, 0))
def r1_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 21 (0, 0))

theorem c1_0 : F.repChkA Q r1_0.1 r1_0.2 = true := by decide +kernel
theorem c1_1 : F.repChkA Q r1_1.1 r1_1.2 = true := by decide +kernel
theorem c1_2 : F.repChkA Q r1_2.1 r1_2.2 = true := by decide +kernel
theorem c1_3 : F.repChkA Q r1_3.1 r1_3.2 = true := by decide +kernel
theorem c1_4 : F.repChkA Q r1_4.1 r1_4.2 = true := by decide +kernel
theorem c1_5 : F.repChkA Q r1_5.1 r1_5.2 = true := by decide +kernel
theorem c1_6 : F.repChkA Q r1_6.1 r1_6.2 = true := by decide +kernel
theorem c1_7 : F.repChkA Q r1_7.1 r1_7.2 = true := by decide +kernel
theorem c1_8 : F.repChkA Q r1_8.1 r1_8.2 = true := by decide +kernel
theorem c1_9 : F.repChkA Q r1_9.1 r1_9.2 = true := by decide +kernel
theorem c1_10 : F.repChkA Q r1_10.1 r1_10.2 = true := by decide +kernel

def D1 : List ((ℤ × ℤ) × RepData) := [r1_0, r1_1, r1_2, r1_3, r1_4, r1_5, r1_6, r1_7, r1_8, r1_9, r1_10]

theorem chkA1 : D1.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D1, List.all_cons, List.all_nil, c1_0, c1_1, c1_2, c1_3, c1_4, c1_5, c1_6, c1_7, c1_8, c1_9, c1_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

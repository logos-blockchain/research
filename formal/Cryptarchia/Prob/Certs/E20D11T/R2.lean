module

public import Cryptarchia.Prob.Certs.E20D11T.Tab
meta import Cryptarchia.Prob.Certs.E20D11T.Tab

/-! # E20D11T: representatives 22 to 32, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r2_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 22 (0, 0))
def r2_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 23 (0, 0))
def r2_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 24 (0, 0))
def r2_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 25 (0, 0))
def r2_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 26 (0, 0))
def r2_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 27 (0, 0))
def r2_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 28 (0, 0))
def r2_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 29 (0, 0))
def r2_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 30 (0, 0))
def r2_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 31 (0, 0))
def r2_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 32 (0, 0))

theorem c2_0 : F.repChkA Q r2_0.1 r2_0.2 = true := by decide +kernel
theorem c2_1 : F.repChkA Q r2_1.1 r2_1.2 = true := by decide +kernel
theorem c2_2 : F.repChkA Q r2_2.1 r2_2.2 = true := by decide +kernel
theorem c2_3 : F.repChkA Q r2_3.1 r2_3.2 = true := by decide +kernel
theorem c2_4 : F.repChkA Q r2_4.1 r2_4.2 = true := by decide +kernel
theorem c2_5 : F.repChkA Q r2_5.1 r2_5.2 = true := by decide +kernel
theorem c2_6 : F.repChkA Q r2_6.1 r2_6.2 = true := by decide +kernel
theorem c2_7 : F.repChkA Q r2_7.1 r2_7.2 = true := by decide +kernel
theorem c2_8 : F.repChkA Q r2_8.1 r2_8.2 = true := by decide +kernel
theorem c2_9 : F.repChkA Q r2_9.1 r2_9.2 = true := by decide +kernel
theorem c2_10 : F.repChkA Q r2_10.1 r2_10.2 = true := by decide +kernel

def D2 : List ((ℤ × ℤ) × RepData) := [r2_0, r2_1, r2_2, r2_3, r2_4, r2_5, r2_6, r2_7, r2_8, r2_9, r2_10]

theorem chkA2 : D2.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D2, List.all_cons, List.all_nil, c2_0, c2_1, c2_2, c2_3, c2_4, c2_5, c2_6, c2_7, c2_8, c2_9, c2_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

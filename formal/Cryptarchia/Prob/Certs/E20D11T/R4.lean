module

public import Cryptarchia.Prob.Certs.E20D11T.R0
meta import Cryptarchia.Prob.Certs.E20D11T.R0

/-! # E20D11T: representatives 44 to 54, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r4_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 44 (0, 0))
def r4_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 45 (0, 0))
def r4_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 46 (0, 0))
def r4_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 47 (0, 0))
def r4_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 48 (0, 0))
def r4_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 49 (0, 0))
def r4_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 50 (0, 0))
def r4_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 51 (0, 0))
def r4_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 52 (0, 0))
def r4_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 53 (0, 0))
def r4_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 54 (0, 0))

theorem c4_0 : F.repChkA Q r4_0.1 r4_0.2 = true := by decide +kernel
theorem c4_1 : F.repChkA Q r4_1.1 r4_1.2 = true := by decide +kernel
theorem c4_2 : F.repChkA Q r4_2.1 r4_2.2 = true := by decide +kernel
theorem c4_3 : F.repChkA Q r4_3.1 r4_3.2 = true := by decide +kernel
theorem c4_4 : F.repChkA Q r4_4.1 r4_4.2 = true := by decide +kernel
theorem c4_5 : F.repChkA Q r4_5.1 r4_5.2 = true := by decide +kernel
theorem c4_6 : F.repChkA Q r4_6.1 r4_6.2 = true := by decide +kernel
theorem c4_7 : F.repChkA Q r4_7.1 r4_7.2 = true := by decide +kernel
theorem c4_8 : F.repChkA Q r4_8.1 r4_8.2 = true := by decide +kernel
theorem c4_9 : F.repChkA Q r4_9.1 r4_9.2 = true := by decide +kernel
theorem c4_10 : F.repChkA Q r4_10.1 r4_10.2 = true := by decide +kernel

def D4 : List ((ℤ × ℤ) × RepData) := [r4_0, r4_1, r4_2, r4_3, r4_4, r4_5, r4_6, r4_7, r4_8, r4_9, r4_10]

theorem chkA4 : D4.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D4, List.all_cons, List.all_nil, c4_0, c4_1, c4_2, c4_3, c4_4, c4_5, c4_6, c4_7, c4_8, c4_9, c4_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

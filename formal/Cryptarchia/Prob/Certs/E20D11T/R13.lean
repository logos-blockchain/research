module

public import Cryptarchia.Prob.Certs.E20D11T.R9
meta import Cryptarchia.Prob.Certs.E20D11T.R9

/-! # E20D11T: representatives 143 to 153, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r13_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 143 (0, 0))
def r13_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 144 (0, 0))
def r13_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 145 (0, 0))
def r13_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 146 (0, 0))
def r13_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 147 (0, 0))
def r13_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 148 (0, 0))
def r13_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 149 (0, 0))
def r13_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 150 (0, 0))
def r13_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 151 (0, 0))
def r13_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 152 (0, 0))
def r13_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 153 (0, 0))

theorem c13_0 : F.repChkA Q r13_0.1 r13_0.2 = true := by decide +kernel
theorem c13_1 : F.repChkA Q r13_1.1 r13_1.2 = true := by decide +kernel
theorem c13_2 : F.repChkA Q r13_2.1 r13_2.2 = true := by decide +kernel
theorem c13_3 : F.repChkA Q r13_3.1 r13_3.2 = true := by decide +kernel
theorem c13_4 : F.repChkA Q r13_4.1 r13_4.2 = true := by decide +kernel
theorem c13_5 : F.repChkA Q r13_5.1 r13_5.2 = true := by decide +kernel
theorem c13_6 : F.repChkA Q r13_6.1 r13_6.2 = true := by decide +kernel
theorem c13_7 : F.repChkA Q r13_7.1 r13_7.2 = true := by decide +kernel
theorem c13_8 : F.repChkA Q r13_8.1 r13_8.2 = true := by decide +kernel
theorem c13_9 : F.repChkA Q r13_9.1 r13_9.2 = true := by decide +kernel
theorem c13_10 : F.repChkA Q r13_10.1 r13_10.2 = true := by decide +kernel

def D13 : List ((ℤ × ℤ) × RepData) := [r13_0, r13_1, r13_2, r13_3, r13_4, r13_5, r13_6, r13_7, r13_8, r13_9, r13_10]

theorem chkA13 : D13.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D13, List.all_cons, List.all_nil, c13_0, c13_1, c13_2, c13_3, c13_4, c13_5, c13_6, c13_7, c13_8, c13_9, c13_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

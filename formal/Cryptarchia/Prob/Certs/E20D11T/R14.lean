module

public import Cryptarchia.Prob.Certs.E20D11T.R10
meta import Cryptarchia.Prob.Certs.E20D11T.R10

/-! # E20D11T: representatives 154 to 164, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r14_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 154 (0, 0))
def r14_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 155 (0, 0))
def r14_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 156 (0, 0))
def r14_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 157 (0, 0))
def r14_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 158 (0, 0))
def r14_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 159 (0, 0))
def r14_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 160 (0, 0))
def r14_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 161 (0, 0))
def r14_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 162 (0, 0))
def r14_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 163 (0, 0))
def r14_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 164 (0, 0))

theorem c14_0 : F.repChkA Q r14_0.1 r14_0.2 = true := by decide +kernel
theorem c14_1 : F.repChkA Q r14_1.1 r14_1.2 = true := by decide +kernel
theorem c14_2 : F.repChkA Q r14_2.1 r14_2.2 = true := by decide +kernel
theorem c14_3 : F.repChkA Q r14_3.1 r14_3.2 = true := by decide +kernel
theorem c14_4 : F.repChkA Q r14_4.1 r14_4.2 = true := by decide +kernel
theorem c14_5 : F.repChkA Q r14_5.1 r14_5.2 = true := by decide +kernel
theorem c14_6 : F.repChkA Q r14_6.1 r14_6.2 = true := by decide +kernel
theorem c14_7 : F.repChkA Q r14_7.1 r14_7.2 = true := by decide +kernel
theorem c14_8 : F.repChkA Q r14_8.1 r14_8.2 = true := by decide +kernel
theorem c14_9 : F.repChkA Q r14_9.1 r14_9.2 = true := by decide +kernel
theorem c14_10 : F.repChkA Q r14_10.1 r14_10.2 = true := by decide +kernel

def D14 : List ((ℤ × ℤ) × RepData) := [r14_0, r14_1, r14_2, r14_3, r14_4, r14_5, r14_6, r14_7, r14_8, r14_9, r14_10]

theorem chkA14 : D14.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D14, List.all_cons, List.all_nil, c14_0, c14_1, c14_2, c14_3, c14_4, c14_5, c14_6, c14_7, c14_8, c14_9, c14_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

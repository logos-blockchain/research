module

public import Cryptarchia.Prob.Certs.E20D11T.R14
meta import Cryptarchia.Prob.Certs.E20D11T.R14

/-! # E20D11T: representatives 198 to 208, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r18_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 198 (0, 0))
def r18_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 199 (0, 0))
def r18_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 200 (0, 0))
def r18_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 201 (0, 0))
def r18_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 202 (0, 0))
def r18_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 203 (0, 0))
def r18_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 204 (0, 0))
def r18_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 205 (0, 0))
def r18_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 206 (0, 0))
def r18_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 207 (0, 0))
def r18_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 208 (0, 0))

theorem c18_0 : F.repChkA Q r18_0.1 r18_0.2 = true := by decide +kernel
theorem c18_1 : F.repChkA Q r18_1.1 r18_1.2 = true := by decide +kernel
theorem c18_2 : F.repChkA Q r18_2.1 r18_2.2 = true := by decide +kernel
theorem c18_3 : F.repChkA Q r18_3.1 r18_3.2 = true := by decide +kernel
theorem c18_4 : F.repChkA Q r18_4.1 r18_4.2 = true := by decide +kernel
theorem c18_5 : F.repChkA Q r18_5.1 r18_5.2 = true := by decide +kernel
theorem c18_6 : F.repChkA Q r18_6.1 r18_6.2 = true := by decide +kernel
theorem c18_7 : F.repChkA Q r18_7.1 r18_7.2 = true := by decide +kernel
theorem c18_8 : F.repChkA Q r18_8.1 r18_8.2 = true := by decide +kernel
theorem c18_9 : F.repChkA Q r18_9.1 r18_9.2 = true := by decide +kernel
theorem c18_10 : F.repChkA Q r18_10.1 r18_10.2 = true := by decide +kernel

def D18 : List ((ℤ × ℤ) × RepData) := [r18_0, r18_1, r18_2, r18_3, r18_4, r18_5, r18_6, r18_7, r18_8, r18_9, r18_10]

theorem chkA18 : D18.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D18, List.all_cons, List.all_nil, c18_0, c18_1, c18_2, c18_3, c18_4, c18_5, c18_6, c18_7, c18_8, c18_9, c18_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

module

public import Cryptarchia.Prob.Certs.E20D11T.R16
meta import Cryptarchia.Prob.Certs.E20D11T.R16

/-! # E20D11T: representatives 220 to 230, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r20_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 220 (0, 0))
def r20_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 221 (0, 0))
def r20_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 222 (0, 0))
def r20_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 223 (0, 0))
def r20_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 224 (0, 0))
def r20_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 225 (0, 0))
def r20_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 226 (0, 0))
def r20_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 227 (0, 0))
def r20_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 228 (0, 0))
def r20_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 229 (0, 0))
def r20_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 230 (0, 0))

theorem c20_0 : F.repChkA Q r20_0.1 r20_0.2 = true := by decide +kernel
theorem c20_1 : F.repChkA Q r20_1.1 r20_1.2 = true := by decide +kernel
theorem c20_2 : F.repChkA Q r20_2.1 r20_2.2 = true := by decide +kernel
theorem c20_3 : F.repChkA Q r20_3.1 r20_3.2 = true := by decide +kernel
theorem c20_4 : F.repChkA Q r20_4.1 r20_4.2 = true := by decide +kernel
theorem c20_5 : F.repChkA Q r20_5.1 r20_5.2 = true := by decide +kernel
theorem c20_6 : F.repChkA Q r20_6.1 r20_6.2 = true := by decide +kernel
theorem c20_7 : F.repChkA Q r20_7.1 r20_7.2 = true := by decide +kernel
theorem c20_8 : F.repChkA Q r20_8.1 r20_8.2 = true := by decide +kernel
theorem c20_9 : F.repChkA Q r20_9.1 r20_9.2 = true := by decide +kernel
theorem c20_10 : F.repChkA Q r20_10.1 r20_10.2 = true := by decide +kernel

def D20 : List ((ℤ × ℤ) × RepData) := [r20_0, r20_1, r20_2, r20_3, r20_4, r20_5, r20_6, r20_7, r20_8, r20_9, r20_10]

theorem chkA20 : D20.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D20, List.all_cons, List.all_nil, c20_0, c20_1, c20_2, c20_3, c20_4, c20_5, c20_6, c20_7, c20_8, c20_9, c20_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

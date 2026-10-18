module

public import Cryptarchia.Prob.Certs.E20D11T.R13
meta import Cryptarchia.Prob.Certs.E20D11T.R13

/-! # E20D11T: representatives 187 to 197, their data computed at elaboration time
(`FamCfg.repData`) and their tables checked (`FamCfg.repChkA`), one kernel check each -/

@[expose] public section

namespace Cryptarchia.Prob.Certs.E20D11T

open Cryptarchia Cryptarchia.Prob

set_option maxRecDepth 100000
set_option maxHeartbeats 0

def r17_0 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 187 (0, 0))
def r17_1 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 188 (0, 0))
def r17_2 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 189 (0, 0))
def r17_3 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 190 (0, 0))
def r17_4 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 191 (0, 0))
def r17_5 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 192 (0, 0))
def r17_6 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 193 (0, 0))
def r17_7 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 194 (0, 0))
def r17_8 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 195 (0, 0))
def r17_9 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 196 (0, 0))
def r17_10 : (ℤ × ℤ) × RepData := eval% (fun s => (s, F.repData Q s)) (Q.repList.getD 197 (0, 0))

theorem c17_0 : F.repChkA Q r17_0.1 r17_0.2 = true := by decide +kernel
theorem c17_1 : F.repChkA Q r17_1.1 r17_1.2 = true := by decide +kernel
theorem c17_2 : F.repChkA Q r17_2.1 r17_2.2 = true := by decide +kernel
theorem c17_3 : F.repChkA Q r17_3.1 r17_3.2 = true := by decide +kernel
theorem c17_4 : F.repChkA Q r17_4.1 r17_4.2 = true := by decide +kernel
theorem c17_5 : F.repChkA Q r17_5.1 r17_5.2 = true := by decide +kernel
theorem c17_6 : F.repChkA Q r17_6.1 r17_6.2 = true := by decide +kernel
theorem c17_7 : F.repChkA Q r17_7.1 r17_7.2 = true := by decide +kernel
theorem c17_8 : F.repChkA Q r17_8.1 r17_8.2 = true := by decide +kernel
theorem c17_9 : F.repChkA Q r17_9.1 r17_9.2 = true := by decide +kernel
theorem c17_10 : F.repChkA Q r17_10.1 r17_10.2 = true := by decide +kernel

def D17 : List ((ℤ × ℤ) × RepData) := [r17_0, r17_1, r17_2, r17_3, r17_4, r17_5, r17_6, r17_7, r17_8, r17_9, r17_10]

theorem chkA17 : D17.all (fun p => F.repChkA Q p.1 p.2) = true := by
  simp only [D17, List.all_cons, List.all_nil, c17_0, c17_1, c17_2, c17_3, c17_4, c17_5, c17_6, c17_7, c17_8, c17_9, c17_10, Bool.and_self]

end Cryptarchia.Prob.Certs.E20D11T

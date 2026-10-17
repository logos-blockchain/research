module

public meta import Lean.Elab.SyntheticMVars
public meta import Lean.Meta.Eval
public import Lean.Parser.Term

/-!
# Values computed at elaboration time

`eval% e` evaluates the closed term `e` with compiled code while the file is elaborated, and
stands for its value as a literal. A certificate uses it for data that its kernel checks then
verify, such as the seeds of an automaton table: the evaluation is not trusted, since a wrong
value only makes a check fail, and it adds no axiom (unlike `native_decide`, which trusts
compiled code for a proof).
-/

public section

namespace Cryptarchia.Prob

open Lean Elab Term Meta

/-- `eval% e`: the value of `e`, computed at elaboration time, as a literal. -/
syntax (name := evalLit) "eval% " term : term

/-- The value of `e : α` as a literal: integers, rationals and lists of them directly, any other
type through its `ToExpr` instance. -/
meta unsafe def evalLitImpl (e ty : Expr) : MetaM Expr := do
  if ← isDefEq ty (mkConst ``Int) then
    return toExpr (← evalExpr Int ty e)
  if ← isDefEq ty (mkApp (mkConst ``List [0]) (mkConst ``Int)) then
    return toExpr (← evalExpr (List Int) ty e)
  if ← isDefEq ty (mkApp (mkConst ``List [0]) (mkApp (mkConst ``List [0]) (mkConst ``Int))) then
    return toExpr (← evalExpr (List (List Int)) ty e)
  if ← isDefEq ty (Lean.mkConst ``Rat) then
    let q ← evalExpr Rat ty e
    return mkApp2 (Lean.mkConst ``Rat.divInt) (toExpr q.num) (toExpr (q.den : Int))
  if ← isDefEq ty (mkApp (mkConst ``List [0]) (mkConst ``Rat)) then
    let qs ← evalExpr (List Rat) ty e
    let rat := Lean.mkConst ``Rat
    return qs.foldr (fun q l => mkApp3 (Lean.mkConst ``List.cons [0]) rat
      (mkApp2 (Lean.mkConst ``Rat.divInt) (toExpr q.num) (toExpr (q.den : Int))) l) (mkApp (Lean.mkConst ``List.nil [0]) rat)
  -- any other type with a `ToExpr` instance, such as a record of derived numbers
  let u ← decLevel (← getLevel ty)
  let inst ← synthInstance (mkApp (mkConst ``ToExpr [u]) ty)
  evalExpr Expr (mkConst ``Expr) (mkApp3 (mkConst ``ToExpr.toExpr [u]) ty inst e)

@[implemented_by evalLitImpl]
meta opaque evalLitCore (e ty : Expr) : MetaM Expr

@[term_elab evalLit]
meta def elabEvalLit : TermElab := fun stx expectedType? => do
  let e ← elabTerm stx[1] expectedType?
  synthesizeSyntheticMVarsNoPostponing
  let e ← instantiateMVars e
  if e.hasMVar || e.hasFVar then throwError "eval%: the term must be closed"
  evalLitCore e (← inferType e)

end Cryptarchia.Prob

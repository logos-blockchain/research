import CryptarchiaCerts

/-!
# The certified statements use only the specification and the claim

`#check_claim c` follows every definition the statement of `c` depends on: through the types of
constants and the values of definitions, not through proofs (a proof cannot change what a statement
means). It fails if one of them comes from a module of this project outside `Cryptarchia.Spec` and
`Cryptarchia.Claim`, so a reader can check the certified statements (`CryptarchiaCerts.lean`) by
reading those two layers alone.
-/

open Lean Elab Command

/-- A module a certified statement may use: outside this project, or in its specification or claim
layer. -/
def claimModuleOK (m : Name) : Bool :=
  let s := m.toString
  !(s.startsWith "Cryptarchia" || s.startsWith "StochasticRecurrence" || s.startsWith "MiningOnboarding") ||
    s.startsWith "Cryptarchia.Spec." || s.startsWith "Cryptarchia.Claim."

elab "#check_claim " ids:ident* : command => do
  let env ← getEnv
  for id in ids do
    let c ← liftCoreM <| realizeGlobalConstNoOverloadWithInfo id
    let some ci := env.find? c | throwError "unknown constant {c}"
    let mut todo := ci.type.getUsedConstants.toList
    let mut seen : NameSet := {}
    let mut bad : Array (Name × Name) := #[]
    let mut ours := 0
    while !todo.isEmpty do
      let d := todo.head!
      todo := todo.tail!
      if seen.contains d then continue
      seen := seen.insert d
      let some info := env.find? d | continue
      if info matches .thmInfo _ then continue
      if let some i := env.getModuleIdxFor? d then
        let m := env.header.moduleNames[i.toNat]!
        if !claimModuleOK m then bad := bad.push (d, m)
        if m.toString.startsWith "Cryptarchia" then ours := ours + 1
      todo := todo ++ info.type.getUsedConstants.toList
      match info with
      | .defnInfo v => todo := todo ++ v.value.getUsedConstants.toList
      | .inductInfo v =>
        for k in v.ctors do
          if let some ki := env.find? k then todo := todo ++ ki.type.getUsedConstants.toList
      | _ => pure ()
    unless bad.isEmpty do
      throwError m!"{c} depends on definitions outside Cryptarchia.Spec and Cryptarchia.Claim:\n" ++
        MessageData.joinSep (bad.toList.map fun (d, m) => m!"  {d} ({m})") "\n"
    logInfo m!"{c}: {ours} definitions of this project, all in Cryptarchia.Spec and Cryptarchia.Claim"

#check_claim Cryptarchia.Certified.two_months Cryptarchia.Certified.one_year Cryptarchia.Certified.closed

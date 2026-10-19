import Mantle

/-!
The axiom gate of `Mantle`: every declaration of its modules may use only `propext`,
`Classical.choice` and `Quot.sound`. A `sorry` or any other axiom fails the build:

  lake build MantleTest
-/

open Lean

/-- The axioms the library is meant to depend on. -/
def expectedAxioms : List Name := [``propext, ``Classical.choice, ``Quot.sound]

/-- A declaration of one of the modules of `Mantle`. -/
def isOurs (env : Environment) (n : Name) : Bool :=
  match env.getModuleIdxFor? n with
  | none => false
  | some idx =>
    match env.header.moduleNames[idx.toNat]? with
    | some m => (`Mantle).isPrefixOf m
    | none => false

run_cmd Elab.Command.liftCoreM do
  let env ← getEnv
  let mut checked : Nat := 0
  for (n, _) in env.constants.toList do
    unless isOurs env n && !n.isInternal && !n.hasMacroScopes do continue
    checked := checked + 1
    let axs ← collectAxioms n
    if axs.contains ``sorryAx then throwError "unproved: {n}"
    let bad := axs.filter (!expectedAxioms.contains ·)
    unless bad.isEmpty do throwError "unexpected axioms on {n}: {bad.toList}"
  if checked < 100 then
    throwError "only {checked} declarations checked: the module filter is wrong"

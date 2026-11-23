import PEqualNP.Defs


def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s


theorem research_result :
    ∀ (b1 b2 : Bool) (u v : List Bool),
      popTrace 2 (true :: b1 :: u) = popTrace 2 (true :: b2 :: v) → b1 = b2 := by
  intro b1 b2 u v h
  cases b1 <;> cases b2
  · rfl
  · exfalso
    have h' : some false = some true := by
      exact List.cons.inj' (List.cons.inj' h).2
    cases h'
  · exfalso
    have h' : some true = some false := by
      exact List.cons.inj' (List.cons.inj' h).2
    cases h'
  · rfl

#print axioms research_result

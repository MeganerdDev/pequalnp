import PEqualNP.Defs


def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

lemma popTrace_two_true_false (u : List Bool) :
    popTrace 2 (true :: false :: u) = [some true, some false] := by
  rfl

lemma popTrace_two_true_true (u : List Bool) :
    popTrace 2 (true :: true :: u) = [some true, some true] := by
  rfl

theorem research_result : ∀ (u : List Bool),
    popTrace 2 (true :: false :: u) ≠ popTrace 2 (true :: true :: u) := by
  intro u
  rw [popTrace_two_true_false, popTrace_two_true_true]
  decide

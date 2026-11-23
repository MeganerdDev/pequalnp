import PEqualNP.Defs

theorem research_result :
  ((false, false, false) : Bool × Bool × Bool).2 =
    ((true, false, false) : Bool × Bool × Bool).2 ∧
  ((false, false, false) : Bool × Bool × Bool) ≠
    ((true, false, false) : Bool × Bool × Bool) := by
  constructor
  · rfl
  · intro h
    cases h

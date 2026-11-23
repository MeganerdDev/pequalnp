import PEqualNP.Defs

theorem research_result :
  ((false, false, false) : Bool × Bool × Bool).2 = ((true, false, false) : Bool × Bool × Bool).2 := by
  rfl

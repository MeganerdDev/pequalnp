import PEqualNP.Defs

theorem research_result (a b c : Nat) (h : a ≠ b) :
    (([a, c, 1] : List Nat).length = ([b, c, 1] : List Nat).length) ∧
    (([a, c, 1] : List Nat).getLast (by decide) = ([b, c, 1] : List Nat).getLast (by decide)) ∧
    (([a, c, 1] : List Nat).get ⟨1, by decide⟩ = ([b, c, 1] : List Nat).get ⟨1, by decide⟩) ∧
    (([a, c, 1] : List Nat).get ⟨0, by decide⟩ ≠ ([b, c, 1] : List Nat).get ⟨0, by decide⟩) := by
  simpa using And.intro rfl (And.intro rfl (And.intro rfl h))

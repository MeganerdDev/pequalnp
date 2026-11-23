import PEqualNP.Defs

theorem research_result :
    (([1, 0, 1] : List Nat).length = ([0, 0, 1] : List Nat).length) ∧
    (([1, 0, 1] : List Nat).getLast (by decide) = ([0, 0, 1] : List Nat).getLast (by decide)) ∧
    (([1, 0, 1] : List Nat).get ⟨1, by decide⟩ = ([0, 0, 1] : List Nat).get ⟨1, by decide⟩) ∧
    (([1, 0, 1] : List Nat).get ⟨0, by decide⟩ ≠ ([0, 0, 1] : List Nat).get ⟨0, by decide⟩) := by
  decide

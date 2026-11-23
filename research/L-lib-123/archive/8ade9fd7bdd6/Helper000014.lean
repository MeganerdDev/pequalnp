import PEqualNP

 theorem research_result :
    ([1, 0, 1].length = [0, 0, 1].length) ∧
    ([1, 0, 1].getLast (by decide) = [0, 0, 1].getLast (by decide)) ∧
    ([1, 0, 1].get ⟨1, by decide⟩ = [0, 0, 1].get ⟨1, by decide⟩) ∧
    ([1, 0, 1].get ⟨0, by decide⟩ ≠ [0, 0, 1].get ⟨0, by decide⟩) := by
  decide

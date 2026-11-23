import PEqualNP.Defs

theorem research_result (a b c : Nat) (h : a ≠ b) :
    (([a, c, 1] : List Nat).length = ([b, c, 1] : List Nat).length) ∧
    (([a, c, 1] : List Nat).getLast (by simp) = ([b, c, 1] : List Nat).getLast (by simp)) ∧
    (([a, c, 1] : List Nat).get ⟨1, by simp⟩ = ([b, c, 1] : List Nat).get ⟨1, by simp⟩) ∧
    (([a, c, 1] : List Nat).get ⟨0, by simp⟩ ≠ ([b, c, 1] : List Nat).get ⟨0, by simp⟩) := by
  simp [h]

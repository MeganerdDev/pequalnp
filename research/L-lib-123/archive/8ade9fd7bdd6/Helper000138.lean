import PEqualNP.Defs

theorem research_result : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ True := by
  refine ⟨1, 2, ?_⟩
  constructor
  · decide
  constructor
  · decide
  · trivial

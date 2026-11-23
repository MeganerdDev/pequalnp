import PEqualNP.Defs

theorem research_result : ∃ p q : ℕ, 1 ≤ p ∧ p < q := by
  refine ⟨1, 2, ?_⟩
  exact ⟨by decide, by decide⟩

import PEqualNP.Defs

theorem research_result : ∀ m s t : ℕ, s + t < m → ¬ (m ≤ s + t) := by
  intro m s t hlt hle
  exact Nat.not_le_of_gt hlt hle

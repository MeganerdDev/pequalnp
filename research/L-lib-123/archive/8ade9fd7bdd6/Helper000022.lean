import PEqualNP.Defs

theorem research_result : PEqualNP.Library.FP3 1 2 ↔
    ∀ L ∈ PEqualNP.Library.DTIMEO (fun m => 2 ^ (2 * m)),
      ∃ K : ℕ, 1 ≤ K ∧ L ∈ PEqualNP.Library.SigmaV 3 (fun m => K * 2 ^ (1 * m) + K) := by
  rfl

import PEqualNP.Defs

open PEqualNP
open PEqualNP.Library

theorem research_result (p q : ℕ) :
    FP3 p q ↔
      ∀ L ∈ DTIMEO (fun m => 2 ^ (q * m)),
        ∃ K : ℕ, 1 ≤ K ∧ L ∈ SigmaV 3 (fun m => K * 2 ^ (p * m) + K) := by
  rfl

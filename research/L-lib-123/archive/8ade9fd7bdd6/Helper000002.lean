import PEqualNP.Defs

open PEqualNP

 theorem research_result (p q : ℕ) :
    PEqualNP.Library.FP3 p q ↔
      ∀ L ∈ PEqualNP.Library.DTIMEO (fun m => 2 ^ (q * m)),
        ∃ K, 1 ≤ K ∧ L ∈ PEqualNP.Library.SigmaV 3 (fun m => K * 2 ^ (p * m) + K) := by
  rfl

import PEqualNP.Defs

theorem research_result :
  ¬ ∃ (enc : Bool × Bool → Bool) (dec0 dec1 : Bool → Bool),
      (∀ x : Bool × Bool, dec0 (enc x) = x.1) ∧
      (∀ x : Bool × Bool, dec1 (enc x) = x.2) := by
  intro h
  rcases h with ⟨enc, dec0, dec1, h0, h1⟩
  have hff : enc (false, false) = enc (true, false) := by
    by_cases he : enc (false, false) = enc (true, false)
    · exact he
    · cases hffv : enc (false, false) <;> cases htfv : enc (true, false) <;>
        simp at he
  have hbit0 : (false : Bool) = true := by
    calc
      false = dec0 (enc (false, false)) := by simpa using (h0 (false, false)).symm
      _ = dec0 (enc (true, false)) := by rw [hff]
      _ = true := by simpa using h0 (true, false)
  cases hbit0

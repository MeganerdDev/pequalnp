import PEqualNP.Defs

theorem research_result :
  ¬ ∃ (enc : Bool × Bool → Bool) (dec0 dec1 : Bool → Bool),
      (∀ x : Bool × Bool, dec0 (enc x) = x.1) ∧
      (∀ x : Bool × Bool, dec1 (enc x) = x.2) := by
  intro h
  rcases h with ⟨enc, dec0, dec1, h0, h1⟩
  cases hff : enc (false, false) <;> cases htf : enc (true, false)
  · have hbit0 : (false : Bool) = true := by
      calc
        false = dec0 (enc (false, false)) := by simpa using (h0 (false, false)).symm
        _ = dec0 false := by rw [hff]
        _ = true := by simpa [htf] using h0 (true, false)
    cases hbit0
  · have hdec0f : dec0 false = false := by simpa [hff] using h0 (false, false)
    have hdec0t : dec0 true = true := by simpa [htf] using h0 (true, false)
    have hdec1f : dec1 false = false := by simpa [hff] using h1 (false, false)
    cases hft : enc (false, true)
    · have hbit1 : (false : Bool) = true := by
        calc
          false = dec1 (enc (false, false)) := by simpa using (h1 (false, false)).symm
          _ = dec1 false := by rw [hff]
          _ = dec1 (enc (false, true)) := by rw [hft]
          _ = true := by simpa using h1 (false, true)
      cases hbit1
    · have hdec1t : dec1 true = true := by simpa [hft] using h1 (false, true)
      cases htt : enc (true, true)
      · have hbit1 : (false : Bool) = true := by
          calc
            false = dec1 (enc (false, false)) := by simpa using (h1 (false, false)).symm
            _ = dec1 false := by rw [hff]
            _ = dec1 (enc (true, true)) := by rw [htt]
            _ = true := by simpa using h1 (true, true)
        cases hbit1
      · have hbit1 : (false : Bool) = true := by
          calc
            false = dec1 (enc (true, false)) := by simpa using (h1 (true, false)).symm
            _ = dec1 (enc (true, true)) := by rw [htf, htt]
            _ = true := by simpa using h1 (true, true)
        cases hbit1
  · have hdec0t : dec0 true = false := by simpa [hff] using h0 (false, false)
    have hdec0f : dec0 false = true := by simpa [htf] using h0 (true, false)
    have hdec1t : dec1 true = false := by simpa [hff] using h1 (false, false)
    have hdec1f : dec1 false = false := by simpa [htf] using h1 (true, false)
    cases hft : enc (false, true)
    · have hbit1 : (false : Bool) = true := by
        calc
          false = dec1 (enc (true, false)) := by simpa using (h1 (true, false)).symm
          _ = dec1 (enc (false, true)) := by rw [htf, hft]
          _ = true := by simpa using h1 (false, true)
      cases hbit1
    · have hbit1 : (false : Bool) = true := by
        calc
          false = dec1 (enc (false, false)) := by simpa using (h1 (false, false)).symm
          _ = dec1 (enc (false, true)) := by rw [hff, hft]
          _ = true := by simpa using h1 (false, true)
      cases hbit1
  · have hbit0 : (false : Bool) = true := by
      calc
        false = dec0 (enc (false, false)) := by simpa using (h0 (false, false)).symm
        _ = dec0 (enc (true, false)) := by rw [hff, htf]
        _ = true := by simpa using h0 (true, false)
    cases hbit0

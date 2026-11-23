import PEqualNP.Defs

theorem research_result :
  ¬ ∃ (enc : Bool × Bool × Bool → Bool × Bool)
      (dec0 dec1 dec2 : Bool × Bool → Bool),
      (∀ x : Bool × Bool × Bool, dec0 (enc x) = x.2.2) ∧
      (∀ x : Bool × Bool × Bool, dec1 (enc x) = x.2.1) ∧
      (∀ x : Bool × Bool × Bool, dec2 (enc x) = x.1) := by
  intro h
  rcases h with ⟨enc, dec0, dec1, dec2, h0, h1, h2⟩
  have hff : enc (false, false, false) ≠ enc (true, false, false) := by
    intro heq
    have hbit : (false : Bool) = true := by
      calc
        false = dec2 (enc (false, false, false)) := by simpa using (h2 (false, false, false)).symm
        _ = dec2 (enc (true, false, false)) := by rw [heq]
        _ = true := by simpa using h2 (true, false, false)
    cases hbit
  have hft : enc (false, true, false) ≠ enc (true, true, false) := by
    intro heq
    have hbit : (false : Bool) = true := by
      calc
        false = dec2 (enc (false, true, false)) := by simpa using (h2 (false, true, false)).symm
        _ = dec2 (enc (true, true, false)) := by rw [heq]
        _ = true := by simpa using h2 (true, true, false)
    cases hbit
  have htf : enc (false, false, true) ≠ enc (true, false, true) := by
    intro heq
    have hbit : (false : Bool) = true := by
      calc
        false = dec2 (enc (false, false, true)) := by simpa using (h2 (false, false, true)).symm
        _ = dec2 (enc (true, false, true)) := by rw [heq]
        _ = true := by simpa using h2 (true, false, true)
    cases hbit
  have htt : enc (false, true, true) ≠ enc (true, true, true) := by
    intro heq
    have hbit : (false : Bool) = true := by
      calc
        false = dec2 (enc (false, true, true)) := by simpa using (h2 (false, true, true)).symm
        _ = dec2 (enc (true, true, true)) := by rw [heq]
        _ = true := by simpa using h2 (true, true, true)
    cases hbit
  cases h00 : enc (false, false, false) with
  | mk a0 b0 =>
    cases a0 <;> cases b0
    · have htop0 : dec0 (false, false) = false := by simpa [h00] using h0 (false, false, false)
      have hmid0 : dec1 (false, false) = false := by simpa [h00] using h1 (false, false, false)
      have hbad1 : enc (true, false, false) ≠ (false, false) := by simpa [h00] using hff
      have hbad2 : enc (false, true, false) ≠ (false, false) := by
        intro heq
        have hbit : (false : Bool) = true := by
          calc
            false = dec1 (enc (false, false, false)) := by simpa using (h1 (false, false, false)).symm
            _ = dec1 (enc (false, true, false)) := by rw [h00, heq]
            _ = true := by simpa using h1 (false, true, false)
        cases hbit
      have hbad3 : enc (false, false, true) ≠ (false, false) := by
        intro heq
        have hbit : (false : Bool) = true := by
          calc
            false = dec0 (enc (false, false, false)) := by simpa using (h0 (false, false, false)).symm
            _ = dec0 (enc (false, false, true)) := by rw [h00, heq]
            _ = true := by simpa using h0 (false, false, true)
        cases hbit
      cases h10 : enc (true, false, false) with
      | mk a1 b1 =>
        cases a1 <;> cases b1
        · exact (hbad1 rfl).elim
        · have htop1 : dec0 (false, true) = false := by simpa [h10] using h0 (true, false, false)
          have hmid1 : dec1 (false, true) = false := by simpa [h10] using h1 (true, false, false)
          have hbad4 : enc (false, true, false) ≠ (false, true) := by
            intro heq
            have hbit : (false : Bool) = true := by
              calc
                false = dec1 (enc (true, false, false)) := by simpa using (h1 (true, false, false)).symm
                _ = dec1 (enc (false, true, false)) := by rw [h10, heq]
                _ = true := by simpa using h1 (false, true, false)
            cases hbit
          have hbad5 : enc (false, false, true) ≠ (false, true) := by
            intro heq
            have hbit : (false : Bool) = true := by
              calc
                false = dec0 (enc (true, false, false)) := by simpa using (h0 (true, false, false)).symm
                _ = dec0 (enc (false, false, true)) := by rw [h10, heq]
                _ = true := by simpa using h0 (false, false, true)
            cases hbit
          cases h20 : enc (false, true, false) with
          | mk a2 b2 =>
            cases a2 <;> cases b2
            · exact (hbad2 rfl).elim
            · exact (hbad4 rfl).elim
            · have htop2 : dec0 (true, false) = false := by simpa [h20] using h0 (false, true, false)
              have hmid2 : dec1 (true, false) = true := by simpa [h20] using h1 (false, true, false)
              have hbad6 : enc (false, false, true) ≠ (true, false) := by
                intro heq
                have hbit : (false : Bool) = true := by
                  calc
                    false = dec0 (enc (false, true, false)) := by simpa using (h0 (false, true, false)).symm
                    _ = dec0 (enc (false, false, true)) := by rw [h20, heq]
                    _ = true := by simpa using h0 (false, false, true)
                cases hbit
              exact hbad6 (by simpa using htf)
            · exact hbad5 (by simpa using htf)
        · have htop1 : dec0 (true, false) = false := by simpa [h10] using h0 (true, false, false)
          have hmid1 : dec1 (true, false) = false := by simpa [h10] using h1 (true, false, false)
          have hbad4 : enc (false, true, false) ≠ (true, false) := by
            intro heq
            have hbit : (false : Bool) = true := by
              calc
                false = dec1 (enc (true, false, false)) := by simpa using (h1 (true, false, false)).symm
                _ = dec1 (enc (false, true, false)) := by rw [h10, heq]
                _ = true := by simpa using h1 (false, true, false)
            cases hbit
          have hbad5 : enc (false, false, true) ≠ (true, false) := by
            intro heq
            have hbit : (false : Bool) = true := by
              calc
                false = dec0 (enc (true, false, false)) := by simpa using (h0 (true, false, false)).symm
                _ = dec0 (enc (false, false, true)) := by rw [h10, heq]
                _ = true := by simpa using h0 (false, false, true)
            cases hbit
          cases h20 : enc (false, true, false) with
          | mk a2 b2 =>
            cases a2 <;> cases b2
            · exact (hbad2 rfl).elim
            · exact (hbad4 rfl).elim
            · exact (hbad5 (by simpa using htf)).elim
            · have htop2 : dec0 (true, true) = false := by simpa [h20] using h0 (false, true, false)
              have hmid2 : dec1 (true, true) = true := by simpa [h20] using h1 (false, true, false)
              exact htt (by simpa [h20] using rfl)
        · have htop1 : dec0 (true, true) = false := by simpa [h10] using h0 (true, false, false)
          have hmid1 : dec1 (true, true) = false := by simpa [h10] using h1 (true, false, false)
          exact htt (by simpa [h10] using rfl)
    · have htop0 : dec0 (false, true) = false := by simpa [h00] using h0 (false, false, false)
      have hmid0 : dec1 (false, true) = false := by simpa [h00] using h1 (false, false, false)
      have hbad1 : enc (true, false, false) ≠ (false, true) := by simpa [h00] using hff
      have hbad2 : enc (false, true, false) ≠ (false, true) := by
        intro heq
        have hbit : (false : Bool) = true := by
          calc
            false = dec1 (enc (false, false, false)) := by simpa using (h1 (false, false, false)).symm
            _ = dec1 (enc (false, true, false)) := by rw [h00, heq]
            _ = true := by simpa using h1 (false, true, false)
        cases hbit
      exact hbad2 (by simpa [h00] using rfl)
    · have htop0 : dec0 (true, false) = false := by simpa [h00] using h0 (false, false, false)
      have hmid0 : dec1 (true, false) = false := by simpa [h00] using h1 (false, false, false)
      have hbad1 : enc (true, false, false) ≠ (true, false) := by simpa [h00] using hff
      have hbad2 : enc (false, false, true) ≠ (true, false) := by
        intro heq
        have hbit : (false : Bool) = true := by
          calc
            false = dec0 (enc (false, false, false)) := by simpa using (h0 (false, false, false)).symm
            _ = dec0 (enc (false, false, true)) := by rw [h00, heq]
            _ = true := by simpa using h0 (false, false, true)
        cases hbit
      exact hbad2 (by simpa [h00] using rfl)
    · have htop0 : dec0 (true, true) = false := by simpa [h00] using h0 (false, false, false)
      have hmid0 : dec1 (true, true) = false := by simpa [h00] using h1 (false, false, false)
      exact htt (by simpa [h00] using rfl)

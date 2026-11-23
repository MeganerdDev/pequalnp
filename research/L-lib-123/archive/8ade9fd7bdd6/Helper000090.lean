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
        false = dec0 (enc (false, false)) := by simpa [hff] using (h0 (false, false)).symm
        _ = dec0 false := by rw [hff]
        _ = true := by simpa [htf] using h0 (true, false)
    cases hbit0
  · have hfalse : dec0 false = false := by simpa [hff] using h0 (false, false)
    have htrue : dec0 true = true := by simpa [htf] using h0 (true, false)
    cases hdf : dec0 false <;> cases hdt : dec0 true
    · rw [hdf] at hfalse
    · rw [hdf] at hfalse
      cases hfalse
    · rw [hdt] at htrue
      cases htrue
    · rw [hdf] at hfalse
      cases hfalse
  · have htrue : dec0 true = false := by simpa [hff] using h0 (false, false)
    have hfalse : dec0 false = true := by simpa [htf] using h0 (true, false)
    cases hdf : dec0 false <;> cases hdt : dec0 true
    · rw [hdt] at htrue
      cases htrue
    · rw [hdt] at htrue
      cases htrue
    · rw [hdf] at hfalse
      cases hfalse
    · rw [hdf] at hfalse
  · have hbit0 : (false : Bool) = true := by
      calc
        false = dec0 (enc (false, false)) := by simpa [hff] using (h0 (false, false)).symm
        _ = dec0 true := by rw [hff]
        _ = true := by simpa [htf] using h0 (true, false)
    cases hbit0

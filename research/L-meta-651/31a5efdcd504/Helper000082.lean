import PEqualNP.Defs

def petersenEdgeFn (x : Fin 10 → Bool) : Bool :=
  (x 0 && x 1) ||
  (x 1 && x 2) ||
  (x 2 && x 3) ||
  (x 3 && x 4) ||
  (x 4 && x 0) ||
  (x 0 && x 5) ||
  (x 1 && x 6) ||
  (x 2 && x 7) ||
  (x 3 && x 8) ||
  (x 4 && x 9) ||
  (x 5 && x 7) ||
  (x 7 && x 9) ||
  (x 9 && x 6) ||
  (x 6 && x 8) ||
  (x 8 && x 5)

theorem research_result (x : Fin 10 → Bool) (h5 : x 5 = true) (h9 : x 9 = true)
    (hrest : ∀ j, j ≠ (5 : Fin 10) → j ≠ (9 : Fin 10) → x j = false) : petersenEdgeFn x = false := by
  have h0 : x 0 = false := hrest 0 (by decide) (by decide)
  have h1 : x 1 = false := hrest 1 (by decide) (by decide)
  have h2 : x 2 = false := hrest 2 (by decide) (by decide)
  have h3 : x 3 = false := hrest 3 (by decide) (by decide)
  have h4 : x 4 = false := hrest 4 (by decide) (by decide)
  have h6 : x 6 = false := hrest 6 (by decide) (by decide)
  have h7 : x 7 = false := hrest 7 (by decide) (by decide)
  have h8 : x 8 = false := hrest 8 (by decide) (by decide)
  simp [petersenEdgeFn, h0, h1, h2, h3, h4, h5, h6, h7, h8, h9]

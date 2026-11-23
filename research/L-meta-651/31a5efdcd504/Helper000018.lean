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

theorem research_result (x : Fin 10 → Bool) (h0 : x 0 = true) (h3 : x 3 = true)
    (hrest : ∀ j, j ≠ (0 : Fin 10) → j ≠ (3 : Fin 10) → x j = false) :
    petersenEdgeFn x = false := by
  have h1 : x 1 = false := hrest 1 (by decide) (by decide)
  have h2 : x 2 = false := hrest 2 (by decide) (by decide)
  have h4 : x 4 = false := hrest 4 (by decide) (by decide)
  have h5 : x 5 = false := hrest 5 (by decide) (by decide)
  have h6 : x 6 = false := hrest 6 (by decide) (by decide)
  have h7 : x 7 = false := hrest 7 (by decide) (by decide)
  have h8 : x 8 = false := hrest 8 (by decide) (by decide)
  have h9 : x 9 = false := hrest 9 (by decide) (by decide)
  simp [petersenEdgeFn, h0, h3, h1, h2, h4, h5, h6, h7, h8, h9]

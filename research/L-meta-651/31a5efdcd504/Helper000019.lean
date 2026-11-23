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

theorem research_result (x : Fin 10 → Bool) (h0 : x 0 = true) (h4 : x 4 = true) : petersenEdgeFn x = true := by
  simp [petersenEdgeFn, h0, h4]

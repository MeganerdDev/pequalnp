import PEqualNP.Defs

namespace Helper000006

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

theorem research_result
    (i : Fin 10) (x : Fin 10 → Bool)
    (hi : x i = true)
    (hrest : ∀ j, j ≠ i → x j = false) :
    petersenEdgeFn x = false := by
  fin_cases i <;> native_decide [petersenEdgeFn, hi, hrest]

end Helper000006

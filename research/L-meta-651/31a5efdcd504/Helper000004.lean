import PEqualNP.Defs

namespace Helper000004

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

def isEdge : Fin 10 → Fin 10 → Prop
  | 0, 1 => True
  | 1, 0 => True
  | 1, 2 => True
  | 2, 1 => True
  | 2, 3 => True
  | 3, 2 => True
  | 3, 4 => True
  | 4, 3 => True
  | 4, 0 => True
  | 0, 4 => True
  | 0, 5 => True
  | 5, 0 => True
  | 1, 6 => True
  | 6, 1 => True
  | 2, 7 => True
  | 7, 2 => True
  | 3, 8 => True
  | 8, 3 => True
  | 4, 9 => True
  | 9, 4 => True
  | 5, 7 => True
  | 7, 5 => True
  | 7, 9 => True
  | 9, 7 => True
  | 9, 6 => True
  | 6, 9 => True
  | 6, 8 => True
  | 8, 6 => True
  | 8, 5 => True
  | 5, 8 => True
  | _, _ => False

theorem research_result
    (i j : Fin 10) (hij : i ≠ j) (x : Fin 10 → Bool)
    (hi : x i = true) (hj : x j = true)
    (hrest : ∀ k, k ≠ i → k ≠ j → x k = false) :
    petersenEdgeFn x = decide (isEdge i j) := by
  fin_cases i <;> fin_cases j
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · native_decide [petersenEdgeFn, isEdge, hi, hj, hrest]
  · cases (hij rfl)

end Helper000004

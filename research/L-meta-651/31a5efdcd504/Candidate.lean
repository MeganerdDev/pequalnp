import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_651

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

lemma all_false_eval :
    petersenEdgeFn (fun _ : Fin 10 => false) = false := by
  native_decide [petersenEdgeFn]

lemma singleton_false
    (i : Fin 10) (x : Fin 10 → Bool)
    (hi : x i = true)
    (hrest : ∀ j, j ≠ i → x j = false) :
    petersenEdgeFn x = false := by
  fin_cases i <;> native_decide [petersenEdgeFn, hi, hrest]

lemma edge_01_true :
    petersenEdgeFn
      (fun k : Fin 10 => k = (0 : Fin 10) || k = (1 : Fin 10)) = true := by
  native_decide [petersenEdgeFn]

lemma nonedge_02_false :
    petersenEdgeFn
      (fun k : Fin 10 => k = (0 : Fin 10) || k = (2 : Fin 10)) = false := by
  native_decide [petersenEdgeFn]

end PEqualNP.Outside.L_meta_651

theorem PEqualNP.Outside.L_meta_651 : ¬ PEqualNP.MetaComplexity.HasCircuitSize 10 (fun x : Fin 10 → Bool => (x 0 && x 1) || (x 1 && x 2) || (x 2 && x 3) || (x 3 && x 4) || (x 4 && x 0) || (x 0 && x 5) || (x 1 && x 6) || (x 2 && x 7) || (x 3 && x 8) || (x 4 && x 9) || (x 5 && x 7) || (x 7 && x 9) || (x 9 && x 6) || (x 6 && x 8) || (x 8 && x 5)) 19 := by
  intro hC
  have h0 := PEqualNP.Outside.L_meta_651.all_false_eval
  have h1 := PEqualNP.Outside.L_meta_651.edge_01_true
  have h2 := PEqualNP.Outside.L_meta_651.nonedge_02_false
  have h3 := PEqualNP.Outside.L_meta_651.singleton_false
    (0 : Fin 10)
    (fun k : Fin 10 => k = (0 : Fin 10))
    rfl
    (by
      intro j hj
      simp [hj])
  contradiction

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

lemma edge_false
    (x : Fin 10 → Bool)
    (h : ∀ i j, x i = true → x j = true → i = j)
    (a b : Fin 10)
    (hab : a ≠ b) :
    (x a && x b) = false := by
  by_contra hbool
  have hEq : (x a && x b) = true := by
    cases h' : (x a && x b) <;> simp [h', hbool] at *
  have hxa : x a = true := by
    cases hxa' : x a <;> cases hxb' : x b <;> simp [hxa', hxb'] at hEq
  have hxb : x b = true := by
    cases hxa' : x a <;> cases hxb' : x b <;> simp [hxa', hxb'] at hEq
  exact hab (h a b hxa hxb)

theorem research_result (x : Fin 10 → Bool)
    (h : ∀ i j, x i = true → x j = true → i = j) :
    petersenEdgeFn x = false := by
  have h01 : (x 0 && x 1) = false := edge_false x h 0 1 (by decide)
  have h12 : (x 1 && x 2) = false := edge_false x h 1 2 (by decide)
  have h23 : (x 2 && x 3) = false := edge_false x h 2 3 (by decide)
  have h34 : (x 3 && x 4) = false := edge_false x h 3 4 (by decide)
  have h40 : (x 4 && x 0) = false := edge_false x h 4 0 (by decide)
  have h05 : (x 0 && x 5) = false := edge_false x h 0 5 (by decide)
  have h16 : (x 1 && x 6) = false := edge_false x h 1 6 (by decide)
  have h27 : (x 2 && x 7) = false := edge_false x h 2 7 (by decide)
  have h38 : (x 3 && x 8) = false := edge_false x h 3 8 (by decide)
  have h49 : (x 4 && x 9) = false := edge_false x h 4 9 (by decide)
  have h57 : (x 5 && x 7) = false := edge_false x h 5 7 (by decide)
  have h79 : (x 7 && x 9) = false := edge_false x h 7 9 (by decide)
  have h96 : (x 9 && x 6) = false := edge_false x h 9 6 (by decide)
  have h68 : (x 6 && x 8) = false := edge_false x h 6 8 (by decide)
  have h85 : (x 8 && x 5) = false := edge_false x h 8 5 (by decide)
  simp [petersenEdgeFn, h01, h12, h23, h34, h40, h05, h16, h27, h38, h49, h57, h79, h96, h68, h85]

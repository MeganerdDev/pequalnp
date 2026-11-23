import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (xs ys : List Bool),
      xs.length = ys.length →
      popTrace xs.length xs = popTrace ys.length ys →
      xs = ys := by
  intro xs
  induction xs with
  | nil =>
      intro ys hlen htrace
      cases ys with
      | nil =>
          rfl
      | cons y ys =>
          simp at hlen
  | cons x xs ih =>
      intro ys hlen htrace
      cases ys with
      | nil =>
          simp at hlen
      | cons y ys =>
          simp at hlen
          have hlenTail : xs.length = ys.length := hlen
          have htrace' : some x :: popTrace xs.length xs = some y :: popTrace ys.length ys := by
            simpa [popTrace] using htrace
          have hhead : some x = some y := by
            simpa using congrArg List.head? htrace'
          have hxy : x = y := by
            injection hhead with hxy
            exact hxy
          have htail : popTrace xs.length xs = popTrace ys.length ys := by
            simpa using congrArg List.tail? htrace'
          have hrest : xs = ys := ih ys hlenTail htail
          simp [hxy, hrest]

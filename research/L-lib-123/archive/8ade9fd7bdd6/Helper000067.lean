import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (b1 b2 b3 c1 c2 c3 : Bool),
      (∀ k ≤ 3, popTrace k [b1, b2, b3] = popTrace k [c1, c2, c3]) →
      [b1, b2, b3] = [c1, c2, c3] := by
  intro b1 b2 b3 c1 c2 c3 h
  have h3 := h 3 (by decide)
  dsimp [popTrace] at h3
  cases h3
  rfl

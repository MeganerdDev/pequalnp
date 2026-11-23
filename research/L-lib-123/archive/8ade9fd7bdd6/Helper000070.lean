import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (b1 b2 c1 c2 : Bool),
      (∀ k ≤ 2, popTrace k [b1, b2] = popTrace k [c1, c2]) →
      [b1, b2] = [c1, c2] := by
  intro b1 b2 c1 c2 h
  have h2 := h 2 (by decide)
  dsimp [popTrace] at h2
  cases h2
  rfl

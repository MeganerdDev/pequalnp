import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ b1 b2 b3 c1 c2 c3,
      (∀ k ≤ 3, popTrace k [b1, b2, b3] = popTrace k [c1, c2, c3]) →
      [b1, b2, b3] = [c1, c2, c3] := by
  intro b1 b2 b3 c1 c2 c3 h
  have h1 := h 1 (by decide)
  have h2 := h 2 (by decide)
  have h3 := h 3 (by decide)
  dsimp [popTrace] at h1 h2 h3
  injection h1 with hb1
  injection h2 with _ hb2
  injection h3 with _ _ hb3
  subst hb1
  subst hb2
  subst hb3
  rfl

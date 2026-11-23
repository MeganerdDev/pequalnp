import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (b1 b2 c1 c2 : Bool),
      (∀ k ≤ 2, popTrace k [b1, b2] = popTrace k [c1, c2]) →
      b1 = c1 ∧ b2 = c2 := by
  intro b1 b2 c1 c2 h
  have h2 := h 2 (by decide)
  dsimp [popTrace] at h2
  injection h2 with hhead htail
  injection hhead with hb1
  injection htail with hmid
  injection hmid with hb2
  exact And.intro hb1 hb2

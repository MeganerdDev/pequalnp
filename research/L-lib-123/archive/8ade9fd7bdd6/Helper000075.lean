import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (b1 b2 b3 b4 c1 c2 c3 c4 : Bool),
      (∀ k ≤ 4, popTrace k [b1, b2, b3, b4] = popTrace k [c1, c2, c3, c4]) →
      b1 = c1 ∧ b2 = c2 ∧ b3 = c3 ∧ b4 = c4 := by
  intro b1 b2 b3 b4 c1 c2 c3 c4 h
  have h4 := h 4 (by decide)
  dsimp [popTrace] at h4
  injection h4 with hhead htail
  injection hhead with hb1
  injection htail with hmid1 htail1
  injection hmid1 with hb2
  injection htail1 with hmid2 htail2
  injection hmid2 with hb3
  injection htail2 with hmid3
  injection hmid3 with hb4
  exact And.intro hb1 (And.intro hb2 (And.intro hb3 hb4))

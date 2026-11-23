import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (b1 b2 b3 c1 c2 c3 : Bool),
      (∀ k ≤ 3, popTrace k [b1, b2, b3] = popTrace k [c1, c2, c3]) →
      b1 = c1 ∧ b2 = c2 ∧ b3 = c3 := by
  intro b1 b2 b3 c1 c2 c3 h
  have h3 := h 3 (by decide)
  dsimp [popTrace] at h3
  injection h3 with hhead htail
  injection hhead with hb1
  injection htail with hmid1
  injection hmid1 with hhead2 htail2
  injection hhead2 with hb2
  injection htail2 with hmid2
  injection hmid2 with hhead3 htail3
  injection hhead3 with hb3
  exact And.intro hb1 (And.intro hb2 hb3)

import PEqualNP.Defs

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

theorem research_result :
    ∀ (s t : List Bool),
      s.length = t.length →
      (∀ k ≤ s.length, popTrace k s = popTrace k t) →
      s = t := by
  intro s
  induction s with
  | nil =>
      intro t hlen htrace
      cases t with
      | nil => rfl
      | cons b t =>
          simp at hlen
  | cons a s ih =>
      intro t hlen htrace
      cases t with
      | nil =>
          simp at hlen
      | cons b t =>
          have h1 := htrace 1 (by simp)
          dsimp [popTrace] at h1
          injection h1 with hab
          subst hab
          have hlen_tail : s.length = t.length := by
            simp at hlen
            exact hlen
          have htrace_tail : ∀ k ≤ s.length, popTrace k s = popTrace k t := by
            intro k hk
            have hsucc := htrace (k + 1) (by simpa [Nat.add_comm, Nat.add_left_comm, Nat.add_assoc] using Nat.succ_le_succ hk)
            cases k with
            | zero =>
                rfl
            | succ k' =>
                dsimp [popTrace] at hsucc
                injection hsucc with htail
                exact htail
          have hs : s = t := ih t hlen_tail htrace_tail
          subst hs
          rfl

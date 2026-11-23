import PEqualNP.Defs


def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | Nat.succ n, [] => none :: popTrace n []
  | Nat.succ n, a :: s => some a :: popTrace n s

lemma popTrace_of_take_eq : ∀ {α} (k : Nat) (s t : List α),
    List.take k s = List.take k t → popTrace k s = popTrace k t
  | α, 0, s, t, h => by
      rfl
  | α, Nat.succ k, [], [], h => by
      rfl
  | α, Nat.succ k, [], b :: t, h => by
      cases h
  | α, Nat.succ k, a :: s, [], h => by
      cases h
  | α, Nat.succ k, a :: s, b :: t, h => by
      cases h
      have hs : popTrace k s = popTrace k t := popTrace_of_take_eq k s t rfl
      simp [popTrace, hs]

theorem research_result : ∀ {α} (k : Nat) (s t : List α),
    s.length = t.length →
    List.take k s = List.take k t →
    popTrace k s = popTrace k t := by
  intro α k s t hlen htake
  exact popTrace_of_take_eq k s t htake

example :
    popTrace 2 ([true, false, true] : List Bool) =
      popTrace 2 ([true, false, false] : List Bool) := by
  rfl

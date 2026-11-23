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
      simpa using h
  | α, Nat.succ k, a :: s, [], h => by
      simpa using h
  | α, Nat.succ k, a :: s, b :: t, h => by
      have hab_htail : a = b ∧ List.take k s = List.take k t := by
        simpa using h
      have htail : List.take k s = List.take k t := hab_htail.2
      have hs : popTrace k s = popTrace k t := popTrace_of_take_eq k s t htail
      cases hab_htail with
      | intro hab htail =>
          cases hab
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

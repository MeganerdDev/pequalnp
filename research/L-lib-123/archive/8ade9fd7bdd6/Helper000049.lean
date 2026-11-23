import PEqualNP.Defs


def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | n + 1, [] => none :: popTrace n []
  | n + 1, a :: s => some a :: popTrace n s

lemma popTrace_of_take_eq : ∀ {α} (k : Nat) (s t : List α),
    List.take k s = List.take k t → popTrace k s = popTrace k t
  | α, 0, s, t, _ => by
      simp [popTrace]
  | α, k + 1, [], [], _ => by
      simp [popTrace]
  | α, k + 1, [], b :: t, h => by
      simp at h
  | α, k + 1, a :: s, [], h => by
      simp at h
  | α, k + 1, a :: s, b :: t, h => by
      simp at h
      cases h with
      | intro hab htake =>
          subst hab
          simp [popTrace, popTrace_of_take_eq k s t htake]

theorem research_result : ∀ {α} (k : Nat) (s t : List α),
    s.length = t.length →
    List.take k s = List.take k t →
    popTrace k s = popTrace k t := by
  intro α k s t _ htake
  exact popTrace_of_take_eq k s t htake

example :
    popTrace 2 ([true, false, true] : List Bool) =
      popTrace 2 ([true, false, false] : List Bool) := by
  apply research_result 2
  · simp
  · simp

import PEqualNP.Defs

open List

def popTrace : Nat → List α → List (Option α)
  | 0, _ => []
  | _ + 1, [] => none :: popTrace _ []
  | _ + 1, a :: s => some a :: popTrace _ s

lemma popTrace_eq_map_getElem? (k : Nat) (s : List α) :
    popTrace k s = (List.range k).map (fun i => s.get? i) := by
  induction k generalizing s with
  | zero =>
      simp [popTrace]
  | succ k ih =>
      cases s with
      | nil =>
          simp [popTrace, ih]
      | cons a s =>
          simp [popTrace, ih, List.range_succ, Nat.add_comm, Nat.add_left_comm, Nat.add_assoc]

lemma get?_eq_get?_of_take_eq {k i : Nat} {s t : List α}
    (hi : i < k) (h : List.take k s = List.take k t) :
    s.get? i = t.get? i := by
  have hget := congrArg (fun u => u.get? i) h
  have hs : (List.take k s).get? i = s.get? i := by
    simpa [List.getElem?_take, hi, if_pos hi]
  have ht : (List.take k t).get? i = t.get? i := by
    simpa [List.getElem?_take, hi, if_pos hi]
  exact hs.trans (hget.trans ht.symm)

lemma map_get?_take_eq {k : Nat} {s t : List α}
    (h : List.take k s = List.take k t) :
    (List.range k).map (fun i => s.get? i) = (List.range k).map (fun i => t.get? i) := by
  refine List.ext fun i => ?_
  simp only [List.getElem?_map, List.length_range]
  split
  · rename_i hi
    simp only [List.getElem?_range, hi, Option.pure_def]
    exact get?_eq_get?_of_take_eq hi h
  · rfl

theorem research_result : ∀ {α} (k : Nat) (s t : List α),
    s.length = t.length →
    List.take k s = List.take k t →
    popTrace k s = popTrace k t := by
  intro α k s t hlen htake
  rw [popTrace_eq_map_getElem?, popTrace_eq_map_getElem?]
  exact map_get?_take_eq htake

example :
    popTrace 2 ([true, false, true] : List Bool) =
      popTrace 2 ([true, false, false] : List Bool) := by
  apply research_result 2
  · simp
  · simp

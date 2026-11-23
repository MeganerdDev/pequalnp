#!/usr/bin/env python3
"""Exhaustive toy-stack audit for boundary summaries.

This script checks two claims for stacks of fixed bit height n:
1. The full family of k-pop traces for k=1..n is injective.
2. Any summary using fewer than 2^n codes must merge two distinct stacks, and
   therefore cannot force correctness for all future pop challenges, because
   some merged pair has a different pop-trace family.

It also prints an explicit counterexample for the natural compressed summary
(height, top), which at fixed height reduces to just the top bit.
"""

from __future__ import annotations

import itertools
import sys
from collections import defaultdict
from typing import Dict, Iterable, Iterator, List, Sequence, Tuple

Bit = int
Stack = Tuple[Bit, ...]  # top at index 0
Trace = Tuple[int | None, ...]
Summary = Tuple[int, ...]


def all_stacks(n: int) -> List[Stack]:
    return [tuple(bits) for bits in itertools.product((0, 1), repeat=n)]


def pop_trace(k: int, stack: Sequence[Bit]) -> Trace:
    out: List[int | None] = []
    for i in range(k):
        out.append(stack[i] if i < len(stack) else None)
    return tuple(out)



def full_trace_family(stack: Sequence[Bit], n: int) -> Tuple[Trace, ...]:
    return tuple(pop_trace(k, stack) for k in range(1, n + 1))



def natural_summary_height_top(stack: Sequence[Bit]) -> Tuple[int, int | None]:
    return (len(stack), stack[0] if stack else None)



def grouped_by_summary(stacks: Iterable[Stack], summary_fn) -> Dict[object, List[Stack]]:
    groups: Dict[object, List[Stack]] = defaultdict(list)
    for stack in stacks:
        groups[summary_fn(stack)].append(stack)
    return dict(groups)



def find_conflicting_pair_in_groups(groups: Dict[object, List[Stack]], n: int):
    for summary, members in groups.items():
        by_trace: Dict[Tuple[Trace, ...], Stack] = {}
        for stack in members:
            trace_family = full_trace_family(stack, n)
            if trace_family not in by_trace:
                by_trace[trace_family] = stack
        if len(by_trace) >= 2:
            reps = list(by_trace.items())
            (trace1, s1), (trace2, s2) = reps[0], reps[1]
            return summary, s1, s2, trace1, trace2
    return None



def restricted_growth_strings(length: int, max_label: int) -> Iterator[Summary]:
    """Generate all restricted growth strings of given length.

    These canonically enumerate set partitions of {0, ..., length-1} whose
    labels are in {0, ..., max_label-1}. Every prefix introduces a new label at
    most one above the current maximum.
    """

    arr = [0] * length

    def rec(i: int, used: int) -> Iterator[Summary]:
        if i == length:
            yield tuple(arr)
            return
        limit = min(used + 1, max_label)
        for x in range(limit):
            arr[i] = x
            new_used = used + (1 if x == used else 0)
            yield from rec(i + 1, new_used)

    if length == 0:
        yield tuple()
    else:
        yield from rec(1, 1)



def partition_from_rgs(items: Sequence[Stack], rgs: Summary) -> Dict[int, List[Stack]]:
    groups: Dict[int, List[Stack]] = defaultdict(list)
    for item, label in zip(items, rgs):
        groups[label].append(item)
    return dict(groups)



def enumerate_bad_partitions(n: int):
    stacks = all_stacks(n)
    total = 0
    bad = 0
    witness = None
    m = len(stacks)
    for class_bound in range(1, m):
        for rgs in restricted_growth_strings(m, class_bound):
            groups = partition_from_rgs(stacks, rgs)
            total += 1
            conflict = find_conflicting_pair_in_groups(groups, n)
            if conflict is None:
                bad += 1
                witness = groups
                break
        if witness is not None:
            break
    return total, bad, witness



def first_k_where_traces_differ(s1: Stack, s2: Stack, n: int):
    for k in range(1, n + 1):
        t1 = pop_trace(k, s1)
        t2 = pop_trace(k, s2)
        if t1 != t2:
            return k, t1, t2
    return None



def check_injectivity(n: int):
    stacks = all_stacks(n)
    seen: Dict[Tuple[Trace, ...], Stack] = {}
    for stack in stacks:
        family = full_trace_family(stack, n)
        prev = seen.get(family)
        if prev is not None and prev != stack:
            return False, prev, stack, family
        seen[family] = stack
    return True, len(seen)



def main() -> int:
    failures: List[str] = []

    print("Toy stack boundary audit")
    print("=" * 60)

    # Explicit natural compressed summary counterexample.
    s_honest = (1, 0)
    s_claimed = (1, 1)
    summary_honest = natural_summary_height_top(s_honest)
    summary_claimed = natural_summary_height_top(s_claimed)
    print("Explicit compressed-summary counterexample:")
    print(f"  honest stack   = {s_honest}, summary(height, top) = {summary_honest}")
    print(f"  cheating stack = {s_claimed}, summary(height, top) = {summary_claimed}")
    diff = first_k_where_traces_differ(s_honest, s_claimed, 2)
    print(f"  first differing pop challenge = k={diff[0]}, traces {diff[1]} vs {diff[2]}")
    if summary_honest != summary_claimed:
        failures.append("Expected the (height, top) summaries to collide for the explicit witness.")
    if diff is None:
        failures.append("Expected the explicit compressed-summary witness to differ on some pop trace.")

    print("\nInjectivity of the full family of pop traces:")
    for n in (1, 2, 3, 4):
        ok, a, b, c = None, None, None, None
        result = check_injectivity(n)
        if result[0]:
            _, distinct_codes = result
            print(f"  n={n}: injective; {distinct_codes} distinct trace families for {2**n} stacks")
            if distinct_codes != 2**n:
                failures.append(f"Injective check for n={n} produced {distinct_codes} codes instead of {2**n}.")
        else:
            _, s1, s2, family = result
            print(f"  n={n}: NOT injective; collision {s1} and {s2} -> {family}")
            failures.append(f"Full trace family should be injective for n={n}, but {s1} and {s2} collided.")

    print("\nExhaustive partition audit for n=3:")
    total, bad, witness = enumerate_bad_partitions(3)
    print(f"  checked {total} partitions into fewer than 8 classes")
    print(f"  partitions with no conflicting colliding pair = {bad}")
    if witness is None:
        print("  result: every partition with fewer than 8 summary classes has a conflicting colliding pair")
    else:
        print(f"  unexpected witness partition without conflict: {witness}")
        failures.append("Found a partition with fewer than 2^n classes but no conflicting colliding pair.")

    print("\nOne concrete partition witness from the natural summary at n=3:")
    stacks3 = all_stacks(3)
    groups3 = grouped_by_summary(stacks3, natural_summary_height_top)
    conflict = find_conflicting_pair_in_groups(groups3, 3)
    if conflict is None:
        failures.append("Expected a conflicting pair for natural summary (height, top) at n=3.")
    else:
        summary, s1, s2, trace1, trace2 = conflict
        kd = first_k_where_traces_differ(s1, s2, 3)
        print(f"  shared summary = {summary}")
        print(f"  colliding stacks = {s1} and {s2}")
        print(f"  full trace families:\n    {trace1}\n    {trace2}")
        print(f"  first differing k = {kd[0]}, traces {kd[1]} vs {kd[2]}")

    if failures:
        print("\nFAILURES DETECTED:")
        for msg in failures:
            print(f"  - {msg}")
        return 1

    print("\nAll checks passed.")
    print("Conclusion: in this toy model, any summary that guarantees correctness of all future pop")
    print("challenges up to depth n must distinguish all 2^n boundary stacks; the full family of")
    print("pop traces is injective, while compressed summaries like (height, top) are not sound.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

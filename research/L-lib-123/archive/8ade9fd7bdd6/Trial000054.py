#!/usr/bin/env python3
"""Brute-force audit of pre-challenge stack-cell disclosures.

This script studies the toy boundary-stack example from stack-boundary.md.
For each stack height n, the honest boundary stack is
    [1, 0, 0, ..., 0]
with index 0 the top of stack.

Segment B falsely claims two pops both return 1, so a cheating stack must have
first two cells [1, 1].

The verifier checks only:
- stack height,
- top cell,
- k additional disclosed stack cells chosen before the challenge.

For each n and k, we enumerate all disclosure subsets of size k and determine
whether every such subset blocks cheating, i.e. whether there exists no binary
stack of length n that:
- differs from the honest stack,
- matches the honest height and top,
- matches all disclosed cells,
- yields first two pops [1, 1].

We compute the minimum k that blocks all cheating subsets, and cross-check the
result with an independent oracle.
"""

from __future__ import annotations

import itertools
import math
import sys
from typing import Iterable, List, Sequence, Tuple


Stack = Tuple[int, ...]
Subset = Tuple[int, ...]


def require(condition: bool, message: str, failures: List[str]) -> None:
    if not condition:
        failures.append(message)


def honest_stack(n: int) -> Stack:
    if n < 2:
        raise ValueError("This experiment requires n >= 2.")
    return (1, 0) + (0,) * (n - 2)


def all_stacks(n: int) -> Iterable[Stack]:
    return itertools.product((0, 1), repeat=n)


def pops2(stack: Sequence[int]) -> Tuple[int, int]:
    return (stack[0], stack[1])


def matches_checked_data(candidate: Sequence[int], honest: Sequence[int], subset: Sequence[int]) -> bool:
    if len(candidate) != len(honest):
        return False
    if candidate[0] != honest[0]:
        return False
    return all(candidate[i] == honest[i] for i in subset)


def cheating_witnesses(n: int, subset: Sequence[int]) -> List[Stack]:
    honest = honest_stack(n)
    out: List[Stack] = []
    for stack in all_stacks(n):
        if stack == honest:
            continue
        if pops2(stack) != (1, 1):
            continue
        if not matches_checked_data(stack, honest, subset):
            continue
        out.append(stack)
    return out


def subset_blocks_cheating(n: int, subset: Sequence[int]) -> bool:
    return not cheating_witnesses(n, subset)


def min_k_by_search(n: int) -> Tuple[int, List[Tuple[int, int]]]:
    profile: List[Tuple[int, int]] = []
    for k in range(0, n + 1):
        blocked_count = 0
        total = math.comb(n, k)
        for subset in itertools.combinations(range(n), k):
            if subset_blocks_cheating(n, subset):
                blocked_count += 1
        profile.append((blocked_count, total))
        if blocked_count == total:
            return k, profile
    raise AssertionError("Some k <= n should block cheating, at worst by disclosing all cells.")


# Independent oracle: reason directly from the forced second cell.
def min_k_oracle(n: int) -> int:
    # Honest top already reveals index 0 = 1. A cheating stack with pops [1,1]
    # differs exactly by needing index 1 = 1 instead of honest index 1 = 0,
    # while arbitrary deeper cells do not matter to the first two pops.
    # Therefore every subset must include index 1 to block cheating. The minimum
    # k that guarantees this for all size-k subsets of {0,...,n-1} is k = n:
    # for any k < n, there exists a size-k subset omitting index 1.
    if n < 2:
        raise ValueError("This experiment requires n >= 2.")
    return n


def demonstrate_counterexample(n: int, k: int) -> Tuple[Subset, Stack] | None:
    for subset in itertools.combinations(range(n), k):
        witnesses = cheating_witnesses(n, subset)
        if witnesses:
            return subset, witnesses[0]
    return None


def main() -> int:
    failures: List[str] = []
    ns = list(range(2, 9))

    print("BOUNDARY STACK DISCLOSURE AUDIT")
    print("honest stack format: top-first tuple, honest(n) = (1, 0, 0, ..., 0)")
    print("false transcript constraint: first two pops must be (1, 1)")
    print()

    for n in ns:
        honest = honest_stack(n)
        min_k, profile = min_k_by_search(n)
        oracle_k = min_k_oracle(n)
        require(min_k == oracle_k, f"n={n}: search found min_k={min_k}, oracle expected {oracle_k}", failures)

        print(f"n={n}")
        print(f"  honest stack: {honest}")
        for k, (blocked_count, total) in enumerate(profile):
            status = "blocks all" if blocked_count == total else "not enough"
            print(f"  k={k}: blocked subsets {blocked_count}/{total} -> {status}")
        print(f"  minimum k blocking all disclosure sets: {min_k}")

        if min_k > 0:
            witness_info = demonstrate_counterexample(n, min_k - 1)
            require(witness_info is not None, f"n={n}: expected counterexample at k={min_k - 1}", failures)
            if witness_info is not None:
                subset, witness = witness_info
                print(f"  sample surviving disclosure set at k={min_k - 1}: {subset}")
                print(f"  sample cheating stack: {witness}")
                require(1 not in subset, f"n={n}: expected sample subset to omit buried index 1", failures)
                require(matches_checked_data(witness, honest, subset), f"n={n}: witness does not match checked data", failures)
                require(pops2(witness) == (1, 1), f"n={n}: witness does not realize false transcript", failures)
        print()

    # Direct substantive assertions about the pattern.
    for n in ns:
        min_k, _ = min_k_by_search(n)
        require(min_k == n, f"n={n}: expected full disclosure k=n to be necessary in this toy model", failures)
        if n > 2:
            require(min_k > math.ceil(math.log2(n)), f"n={n}: unexpectedly tiny sublinear k sufficed", failures)
            require(min_k > n // 2, f"n={n}: unexpectedly proper sublinear k sufficed", failures)

    print("SUMMARY")
    print("  For every tested n in 2..8, the minimum k that rules out cheating for ALL size-k disclosure sets is k=n.")
    print("  Reason: any pre-challenge disclosure family that can omit buried index 1 leaves a cheating stack")
    print("  with second cell flipped to 1 while preserving height, top, and all disclosed cells.")
    print("  This supports the report's linear-information concern in the toy model.")

    if failures:
        print()
        print("CHECK FAILURES DETECTED:")
        for msg in failures:
            print(f"- {msg}")
        return 1

    print()
    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

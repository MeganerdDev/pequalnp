#!/usr/bin/env python3
"""Independent falsifiable audit of the stack-boundary example."""

from itertools import product
import sys


def push(stack, bit):
    return [bit] + list(stack)


def pop(stack):
    if not stack:
        return None, []
    return stack[0], stack[1:]


def run_ops(initial_stack, ops):
    stack = list(initial_stack)
    transcript = []
    for op in ops:
        kind = op[0]
        if kind == "push":
            stack = push(stack, op[1])
        elif kind == "pop":
            value, stack = pop(stack)
            transcript.append(value)
        else:
            raise ValueError(f"unknown op: {op}")
    return stack, transcript


def summary(stack):
    return len(stack), (stack[0] if stack else None)


def stacks_matching_pop_transcript(max_height, claimed_pops):
    matches = []
    for h in range(max_height + 1):
        for bits in product([0, 1], repeat=h):
            stack = list(bits)
            _, transcript = run_ops(stack, [("pop",), ("pop",)])
            if transcript == claimed_pops:
                matches.append(stack)
    return matches


def require(cond, msg, failures):
    if not cond:
        failures.append(msg)


def main():
    failures = []

    honest_boundary, honest_transcript_a = run_ops([], [("push", 0), ("push", 1)])
    require(honest_transcript_a == [], "A should produce no pop transcript.", failures)
    require(honest_boundary == [1, 0], f"Expected honest boundary [1, 0], got {honest_boundary}", failures)

    honest_after_b, honest_b_pops = run_ops(honest_boundary, [("pop",), ("pop",)])
    require(honest_b_pops == [1, 0], f"Expected honest B pops [1, 0], got {honest_b_pops}", failures)
    require(honest_b_pops != [1, 1], "The claimed false transcript unexpectedly matched honest execution.", failures)

    boundary_summary = summary(honest_boundary)
    claimed_transcript = [1, 1]

    witness_same_summary_diff_full = None
    search_space = []
    for h in range(0, 5):
        for bits in product([0, 1], repeat=h):
            stack = list(bits)
            search_space.append(stack)
            if stack != honest_boundary and summary(stack) == boundary_summary:
                witness_same_summary_diff_full = stack
                break
        if witness_same_summary_diff_full is not None:
            break

    require(witness_same_summary_diff_full is not None,
            "Failed to find a stack with same (height, top) as honest boundary but different full contents.",
            failures)

    consistent_false_boundary = None
    consistent_false_boundaries = []
    for stack in search_space:
        _, pops = run_ops(stack, [("pop",), ("pop",)])
        if pops == claimed_transcript:
            consistent_false_boundaries.append(stack)
            if summary(stack) == boundary_summary and stack != honest_boundary and consistent_false_boundary is None:
                consistent_false_boundary = stack

    require(consistent_false_boundary is not None,
            "Failed to find a stack that both matches honest (height, top) and supports false transcript [1,1].",
            failures)

    honest_bits_to_bind = len(honest_boundary)
    sequential_checks_one_path = 5
    unresolved_failure_point = (
        "Binding the full boundary stack catches the buried-bit error here, "
        "but scales linearly with boundary height and so may be too expensive "
        "for the intended speedup."
    )

    print("STACK-BOUNDARY AUDIT")
    print(f"honest boundary stack after A: {honest_boundary}")
    print(f"honest boundary (height, top): {boundary_summary}")
    print(f"honest B pop transcript from true boundary: {honest_b_pops}")
    print(f"claimed false B transcript: {claimed_transcript}")
    print(f"witness with same (height, top) but different full stack: {witness_same_summary_diff_full}")
    print(f"witness also supporting claimed false transcript: {consistent_false_boundary}")
    print(f"all searched false-transcript boundary stacks up to height 4: {consistent_false_boundaries}")
    print(f"content bits needed to bind entire honest boundary stack: {honest_bits_to_bind}")
    print(f"sequential verification-step count for one revealed challenge path: {sequential_checks_one_path}")
    print(f"first unresolved failure point: {unresolved_failure_point}")

    if failures:
        print("CHECK FAILURES DETECTED:")
        for item in failures:
            print(f"- {item}")
        return 1

    print("All required checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

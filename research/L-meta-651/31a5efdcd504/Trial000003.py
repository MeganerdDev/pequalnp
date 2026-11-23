#!/usr/bin/env python3
import itertools
import sys
from typing import Iterable, List, Sequence, Tuple

EDGES: List[Tuple[int, int]] = [
    (0, 1),
    (1, 2),
    (2, 3),
    (3, 4),
    (4, 0),
    (0, 5),
    (1, 6),
    (2, 7),
    (3, 8),
    (4, 9),
    (5, 7),
    (7, 9),
    (9, 6),
    (6, 8),
    (8, 5),
]

N = 10
EDGE_SET = {tuple(sorted(e)) for e in EDGES}


def petersen_edge_function(bits: Sequence[bool]) -> bool:
    if len(bits) != N:
        raise ValueError(f"expected {N} bits, got {len(bits)}")
    x = bits
    return (
        (x[0] and x[1]) or
        (x[1] and x[2]) or
        (x[2] and x[3]) or
        (x[3] and x[4]) or
        (x[4] and x[0]) or
        (x[0] and x[5]) or
        (x[1] and x[6]) or
        (x[2] and x[7]) or
        (x[3] and x[8]) or
        (x[4] and x[9]) or
        (x[5] and x[7]) or
        (x[7] and x[9]) or
        (x[9] and x[6]) or
        (x[6] and x[8]) or
        (x[8] and x[5])
    )


def assignment_with_true_indices(indices: Iterable[int]) -> Tuple[bool, ...]:
    s = set(indices)
    return tuple(i in s for i in range(N))


def pair_oracle(bits: Sequence[bool]) -> bool:
    true_vertices = [i for i, b in enumerate(bits) if b]
    return len(true_vertices) == 2 and tuple(sorted(true_vertices)) in EDGE_SET


def fmt_bits(bits: Sequence[bool]) -> str:
    return ''.join('1' if b else '0' for b in bits)


def main() -> int:
    notes = []
    failures = []

    notes.append("Objective: verify a concrete specification fragment for the 10-input Petersen edge function.")
    notes.append(f"Edges ({len(EDGES)} total): {EDGES}")

    # (1) Hamming weight 0 and 1 inputs should map to False.
    checked_weight_le_1 = []
    for true_set in [tuple()] + [(i,) for i in range(N)]:
        bits = assignment_with_true_indices(true_set)
        actual = petersen_edge_function(bits)
        checked_weight_le_1.append((true_set, actual, fmt_bits(bits)))
        if actual is not False:
            failures.append(
                f"Expected False on weight-{len(true_set)} input {true_set} ({fmt_bits(bits)}), got {actual}"
            )

    # (2) Each listed edge with exactly its endpoints true should map to True.
    edge_results = []
    for edge in EDGES:
        bits = assignment_with_true_indices(edge)
        actual = petersen_edge_function(bits)
        oracle = pair_oracle(bits)
        edge_results.append((edge, actual, oracle, fmt_bits(bits)))
        if oracle is not True:
            failures.append(f"Internal oracle error: listed edge {edge} was not recognized as an edge")
        if actual is not True:
            failures.append(
                f"Expected True on edge input {edge} ({fmt_bits(bits)}), got {actual}"
            )

    # (3) At least one concrete non-edge pair should map to False.
    non_edge = (0, 2)
    bits = assignment_with_true_indices(non_edge)
    non_edge_actual = petersen_edge_function(bits)
    non_edge_oracle = pair_oracle(bits)
    if non_edge_oracle is not False:
        failures.append(f"Chosen witness pair {non_edge} is unexpectedly in the edge oracle")
    if non_edge_actual is not False:
        failures.append(
            f"Expected False on non-edge input {non_edge} ({fmt_bits(bits)}), got {non_edge_actual}"
        )

    # Strengthen slightly: all 45 two-true assignments agree with the graph-edge oracle.
    all_pair_results = []
    for i, j in itertools.combinations(range(N), 2):
        bits = assignment_with_true_indices((i, j))
        actual = petersen_edge_function(bits)
        oracle = pair_oracle(bits)
        all_pair_results.append(((i, j), actual, oracle))
        if actual != oracle:
            failures.append(
                f"Two-true mismatch on pair {(i, j)} ({fmt_bits(bits)}): function={actual}, oracle={oracle}"
            )

    print("Petersen edge function audit")
    print(f"Checked {len(checked_weight_le_1)} inputs of Hamming weight 0 or 1.")
    for true_set, actual, bitstr in checked_weight_le_1:
        print(f"  weight={len(true_set)} true_set={true_set} bits={bitstr} -> {actual}")

    print(f"Checked {len(edge_results)} listed edge inputs.")
    for edge, actual, oracle, bitstr in edge_results:
        print(f"  edge={edge} bits={bitstr} -> function={actual}, oracle={oracle}")

    print(f"Concrete non-edge witness: pair={non_edge} bits={fmt_bits(bits)} -> function={non_edge_actual}, oracle={non_edge_oracle}")

    pair_matches = sum(1 for _, actual, oracle in all_pair_results if actual == oracle)
    print(f"All two-true assignments checked: {pair_matches}/{len(all_pair_results)} matched the edge oracle.")

    if failures:
        print("FAILURES DETECTED:")
        for msg in failures:
            print("  -", msg)
        status = 1
    else:
        print("All required checks succeeded.")
        status = 0

    notes.append(f"Checked {len(checked_weight_le_1)} weight<=1 inputs, {len(edge_results)} listed edges, and {len(all_pair_results)} two-true pairs.")
    notes.append("Result: PASS" if status == 0 else "Result: FAIL")

    with open("notes.md", "a", encoding="utf-8") as fh:
        fh.write("\n## Trial000003\n")
        for line in notes:
            fh.write(f"- {line}\n")
        if failures:
            fh.write("- Failures:\n")
            for msg in failures:
                fh.write(f"  - {msg}\n")

    return status


if __name__ == "__main__":
    sys.exit(main())

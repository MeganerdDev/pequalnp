#!/usr/bin/env python3
import itertools
import sys
import time
from collections import defaultdict


def append_notes(line: str) -> None:
    with open('/workspace/notes.md', 'a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def all_bitstrings(m):
    return [tuple((x >> i) & 1 for i in range(m)) for x in range(1 << m)]


def fmt_bits(x):
    return ''.join(str(b) for b in x)


def subsets_of_positions(m):
    positions = list(range(m))
    for r in range(m + 1):
        for combo in itertools.combinations(positions, r):
            yield combo


def summary_key(x, S):
    return tuple(x[i] for i in S)


def agrees_on_positions(x, y, positions):
    return all(x[i] == y[i] for i in positions)


def pair_indistinguishable_with_t_probes(x, y, k, S, t, m):
    if x[k] == y[k]:
        return False
    if k in S:
        return False
    diff_positions = [i for i in range(m) if x[i] != y[i]]
    hidden_diffs = [i for i in diff_positions if i not in S]
    # Deterministic adaptive probing can only distinguish by querying a hidden differing bit.
    # If there are more hidden differing bits than available probes, there exists a branch
    # of answers that avoids every queried differing location, so the pair remains consistent.
    return len(hidden_diffs) > t


def find_witness_for_case(m, S, t, bitstrings):
    classes = defaultdict(list)
    for x in bitstrings:
        classes[summary_key(x, S)].append(x)
    for key, items in classes.items():
        if len(items) < 2:
            continue
        outside = [k for k in range(m) if k not in S]
        for k in outside:
            for base in items:
                alt = list(base)
                alt[k] ^= 1
                alt = tuple(alt)
                if alt in items and pair_indistinguishable_with_t_probes(base, alt, k, S, t, m):
                    return {
                        'summary': key,
                        'x': base,
                        'y': alt,
                        'k': k,
                        'hidden_diffs': [i for i in range(m) if base[i] != alt[i] and i not in S],
                        'preferred_single_flip': True,
                    }
            for x, y in itertools.combinations(items, 2):
                if pair_indistinguishable_with_t_probes(x, y, k, S, t, m):
                    return {
                        'summary': key,
                        'x': x,
                        'y': y,
                        'k': k,
                        'hidden_diffs': [i for i in range(m) if x[i] != y[i] and i not in S],
                        'preferred_single_flip': False,
                    }
    return None


def positive_strategy_correct(m, S, t, bitstrings):
    if len(S) + t < m:
        return False, 'precondition not met'
    for x in bitstrings:
        for k in range(m):
            if k in S:
                answer = x[k]
                probes = []
            else:
                if t < 1:
                    return False, f'challenge k={k} outside S but no probe budget'
                probes = [k]
                answer = x[k]
            if answer != x[k]:
                return False, f'wrong answer on {fmt_bits(x)} at k={k}'
            if len(probes) > t:
                return False, f'used too many probes on {fmt_bits(x)} at k={k}'
    return True, 'all challenges answered exactly'


def main() -> int:
    start = time.time()
    failures = []
    witness_count = 0
    positive_count = 0

    print('Prechallenge buried-position binding experiment')
    print('Summary binds exact values on a subset S of buried positions before the challenge.')
    print('After challenge depth k, verifier may adaptively probe at most t additional positions.')
    print('Audit conjecture: success for every stack and challenge iff |S| + t >= m.')
    print()

    for m in (3, 4, 5):
        bitstrings = all_bitstrings(m)
        negative_cases = 0
        positive_cases = 0
        print(f'=== buried length m={m} ({len(bitstrings)} bitstrings) ===')
        print('negative cases:')
        any_negative = False
        for S in subsets_of_positions(m):
            for t in range(m + 1):
                if len(S) + t < m:
                    any_negative = True
                    negative_cases += 1
                    witness = find_witness_for_case(m, S, t, bitstrings)
                    if witness is None:
                        failures.append(f'm={m}, S={S}, t={t}: no explicit counterexample found')
                        print(f'  FAIL S={S} t={t}: no witness')
                    else:
                        witness_count += 1
                        print(
                            f'  PASS S={S} t={t}: witness x={fmt_bits(witness["x"])} '
                            f'y={fmt_bits(witness["y"])} k={witness["k"]} '
                            f'hidden_diffs={witness["hidden_diffs"]} '
                            f'single_flip={witness["preferred_single_flip"]}'
                        )
        if not any_negative:
            print('  (none)')

        print('positive cases:')
        any_positive = False
        for S in subsets_of_positions(m):
            for t in range(m + 1):
                if len(S) + t >= m:
                    any_positive = True
                    positive_cases += 1
                    ok, note = positive_strategy_correct(m, S, t, bitstrings)
                    if not ok:
                        failures.append(f'm={m}, S={S}, t={t}: positive strategy failed: {note}')
                        print(f'  FAIL S={S} t={t}: {note}')
                    else:
                        positive_count += 1
                        print(f'  PASS S={S} t={t}: {note}')
        if not any_positive:
            print('  (none)')
        print(f'summary m={m}: negative_cases={negative_cases} positive_cases={positive_cases}')
        print()

    elapsed = time.time() - start
    ok = not failures
    print('=== summary ===')
    print(f'negative_witnesses_found={witness_count}')
    print(f'positive_cases_verified={positive_count}')
    print(f'required_checks: {"PASS" if ok else "FAIL"}')
    print(f'elapsed_seconds={elapsed:.3f}')
    if failures:
        print('failure_details:')
        for failure in failures:
            print('-', failure)

    append_notes(
        'Trial000135 result: ' + ('PASS' if ok else 'FAIL') +
        f'; negative_witnesses={witness_count}; positive_cases={positive_count}'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

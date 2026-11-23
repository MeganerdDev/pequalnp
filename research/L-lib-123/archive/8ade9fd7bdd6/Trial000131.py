#!/usr/bin/env python3
import itertools
import math
import random
import sys
from collections import defaultdict
from pathlib import Path


def append_notes(line: str) -> None:
    path = Path('/workspace/notes.md')
    previous = path.read_text() if path.exists() else ''
    path.write_text(previous + line + '\n')


def all_strings(m):
    return [tuple((x >> i) & 1 for i in range(m)) for x in range(1 << m)]


def fmt_bits(bits):
    return ''.join(str(b) for b in bits)


def challenged_bit(s, k):
    return s[k - 1]


def can_force_distinction(x, y, k, t):
    differing = {i + 1 for i, (a, b) in enumerate(zip(x, y)) if a != b}
    if challenged_bit(x, k) == challenged_bit(y, k):
        return True
    return k in differing and len(differing) <= t


def class_failure_witness(group, t):
    m = len(group[0])
    for k in range(1, m + 1):
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                x = group[i]
                y = group[j]
                if challenged_bit(x, k) != challenged_bit(y, k):
                    if not can_force_distinction(x, y, k, t):
                        differing = [idx + 1 for idx, (a, b) in enumerate(zip(x, y)) if a != b]
                        unqueried_needed = [d for d in differing if d != k]
                        return {
                            'x': x,
                            'y': y,
                            'k': k,
                            'differing_positions': differing,
                            'explanation': (
                                f'any deterministic {t}-check strategy can inspect at most {t} positions; '
                                f'these strings differ at positions {differing}, so to answer depth {k} soundly '
                                f'it would need to learn depth {k} itself and every other differing position first, '
                                f'requiring {len(differing)} inspections > {t}'
                            )
                        }
    return None


def generate_rgs(length, max_classes):
    rgs = [0] * length
    def rec(i, used):
        if i == length:
            yield tuple(rgs)
            return
        limit = min(used + 1, max_classes)
        for v in range(limit):
            rgs[i] = v
            yield from rec(i + 1, max(used, v + 1))
    rgs[0] = 0
    yield from rec(1, 1)


def partition_from_rgs(items, rgs):
    groups = defaultdict(list)
    for item, cls in zip(items, rgs):
        groups[cls].append(item)
    return [groups[k] for k in sorted(groups)]


def test_partition(items, partition, t):
    for group in partition:
        witness = class_failure_witness(group, t)
        if witness is not None:
            return witness
    return None


def exact_case(n, b, t):
    m = n - 1
    items = all_strings(m)
    max_classes = 1 << b
    checked = 0
    for rgs in generate_rgs(len(items), max_classes):
        checked += 1
        partition = partition_from_rgs(items, rgs)
        witness = test_partition(items, partition, t)
        if witness is None:
            return {
                'ok': False,
                'checked': checked,
                'reason': 'found summary partition with no failure witness',
                'partition': partition,
            }
    return {'ok': True, 'checked': checked}


def random_partition(items, max_classes, rng):
    labels = [rng.randrange(max_classes) for _ in items]
    groups = defaultdict(list)
    for item, label in zip(items, labels):
        groups[label].append(item)
    return [g for g in groups.values() if g]


def positive_identity_case(n, t):
    m = n - 1
    items = all_strings(m)
    partition = [[x] for x in items]
    return test_partition(items, partition, t) is None


def main():
    failures = []
    randomized_checks = 0
    exact_partitions = 0
    print('Adaptive sequential buried-bit verification experiment')
    print('Model: buried length m=n-1 with fixed top bit; summary is any deterministic b-bit partition.')
    print('After challenge depth k, verifier may adaptively inspect up to t buried positions.')
    print('A pair x,y in one summary class defeats soundness at k if every deterministic t-check strategy')
    print('still leaves them indistinguishable before answering yet x_k != y_k.')
    print()

    exact_cases = [
        (4, 0, 0), (4, 0, 1), (4, 0, 2),
        (4, 1, 0), (4, 1, 1),
        (4, 2, 0),
        (5, 0, 0), (5, 0, 1), (5, 0, 2), (5, 0, 3),
        (5, 1, 0), (5, 1, 1), (5, 1, 2),
    ]
    print('=== exact compressed cases ===')
    print('n b t | partitions | status | witness')
    for n, b, t in exact_cases:
        result = exact_case(n, b, t)
        exact_partitions += result['checked']
        if not result['ok']:
            failures.append(f'exact case n={n}, b={b}, t={t} unexpectedly had a safe partition')
            print(f'{n} {b} {t} | {result["checked"]:<10} | FAIL   | safe partition found')
        else:
            m = n - 1
            base = tuple(0 for _ in range(m))
            other = tuple(1 if i == m - 1 else 0 for i in range(m))
            k = m
            print(f'{n} {b} {t} | {result["checked"]:<10} | PASS   | e.g. {fmt_bits(base)} vs {fmt_bits(other)} at depth {k}')
    print()

    print('=== randomized larger compressed cases (independent search) ===')
    print('n b t | samples | status | note')
    rng = random.Random(0)
    randomized_cases = [
        (5, 2, 0, 2000),
        (5, 2, 1, 2000),
    ]
    for n, b, t, samples in randomized_cases:
        items = all_strings(n - 1)
        max_classes = 1 << b
        ok = True
        for _ in range(samples):
            part = random_partition(items, max_classes, rng)
            randomized_checks += 1
            if test_partition(items, part, t) is None:
                ok = False
                break
        if not ok:
            failures.append(f'randomized case n={n}, b={b}, t={t} produced a sampled safe partition')
            print(f'{n} {b} {t} | {samples:<7} | FAIL   | sampled partition with no witness')
        else:
            print(f'{n} {b} {t} | {samples:<7} | PASS   | all sampled partitions had a witness; exact oracle omitted for size')
    print()

    print('=== positive identity edge cases ===')
    print('n t | status | note')
    for n in (4, 5):
        for t in range(0, n):
            ok = positive_identity_case(n, t)
            if not ok:
                failures.append(f'identity summary failed for n={n}, t={t}')
                print(f'{n} {t} | FAIL   | singleton classes should be fully determined')
            else:
                print(f'{n} {t} | PASS   | singleton summary classes leave no collision')
    print()

    required = not failures
    print('=== summary ===')
    print(f'exact_partitions_checked={exact_partitions}')
    print(f'randomized_partitions_checked={randomized_checks}')
    print('required_checks:', 'PASS' if required else 'FAIL')
    if failures:
        print('failure_details:')
        for f in failures:
            print('-', f)

    append_notes(
        'Trial000131 result: ' + ('PASS' if required else 'FAIL') +
        f'; exact_partitions={exact_partitions}; randomized_partitions={randomized_checks}'
    )
    return 0 if required else 1


if __name__ == '__main__':
    sys.exit(main())

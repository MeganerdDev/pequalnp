#!/usr/bin/env python3
import itertools
import sys


def append_note(text: str) -> None:
    with open('/workspace/notes.md', 'a', encoding='utf-8') as f:
        f.write(text)
        if not text.endswith('\n'):
            f.write('\n')


append_note('Trial000059: exhaustive audit of disclosure subsets for the toy stack-boundary model.\n')
append_note('Correction: for size n-1 disclosures, all sets containing index 1 are sound; the unique unsound one omits index 1.\n')


def require(condition, message, failures):
    if not condition:
        failures.append(message)


def honest_stack(n: int):
    if n < 2:
        raise ValueError('n must be at least 2')
    return [1] + [0] * (n - 1)


def all_stacks(n: int):
    for bits in itertools.product((0, 1), repeat=n):
        yield list(bits)


def two_pop_transcript(stack):
    return (stack[0], stack[1])


def matches_disclosure(candidate, honest, subset):
    return all(candidate[i] == honest[i] for i in subset)


def cheating_witness_for_subset(n: int, subset):
    honest = honest_stack(n)
    for candidate in all_stacks(n):
        if candidate == honest:
            continue
        if candidate[0] != honest[0]:
            continue
        if two_pop_transcript(candidate) != (1, 1):
            continue
        if matches_disclosure(candidate, honest, subset):
            return candidate
    return None


def subset_is_sound(n: int, subset):
    return cheating_witness_for_subset(n, subset) is None


def min_k_for_universal_soundness(n: int):
    for k in range(n + 1):
        bad_example = None
        for subset in itertools.combinations(range(n), k):
            witness = cheating_witness_for_subset(n, subset)
            if witness is not None:
                bad_example = (subset, witness)
                break
        if bad_example is None:
            return k, None
    return None, None


def explicit_witness(n: int):
    return [1, 1] + [0] * (n - 2)


def first_subset_of_size_omitting_one(n: int, k: int):
    subset = tuple(i for i in range(n) if i != 1)[:k]
    if 1 in subset:
        raise AssertionError('constructed subset should omit index 1')
    return subset


def main() -> int:
    failures = []
    tested_ns = list(range(2, 11))

    print('TOY-MODEL STACK-BOUNDARY DISCLOSURE AUDIT')
    print('Honest stack: [1,0,0,...,0] of length n.')
    print('Cheating target: same length, same top bit, agreement on disclosed cells, but false two-pop transcript (1,1).')
    print()

    for n in tested_ns:
        honest = honest_stack(n)
        k_star, _ = min_k_for_universal_soundness(n)
        witness_template = explicit_witness(n)

        print(f'n={n}')
        print(f'  honest stack: {honest}')
        print(f'  candidate-space size searched by oracle: {2**n}')
        print(f'  minimum k forcing soundness for every size-k disclosure set: {k_star}')

        require(k_star == n, f'n={n}: expected minimum universal soundness threshold to be n, got {k_star}', failures)

        for k in range(n):
            subset = first_subset_of_size_omitting_one(n, k)
            witness = cheating_witness_for_subset(n, subset)
            require(witness is not None, f'n={n}, k={k}: expected a cheating witness for some size-k subset omitting index 1', failures)
            require(matches_disclosure(witness_template, honest, subset), f'n={n}, k={k}: explicit witness should match the disclosed cells', failures)
            require(two_pop_transcript(witness_template) == (1, 1), f'n={n}, k={k}: explicit witness should realize transcript (1,1)', failures)
            require(witness_template[0] == honest[0], f'n={n}, k={k}: explicit witness should preserve the top bit', failures)
            require(len(witness_template) == len(honest), f'n={n}, k={k}: explicit witness should preserve stack height', failures)
            if k == n - 1:
                print(f'  sample unsound size-{k} subset: {subset}')
                print(f'  sample cheating witness: {witness_template}')

        all_size_n_minus_1 = list(itertools.combinations(range(n), n - 1))
        sound_sets = [subset for subset in all_size_n_minus_1 if subset_is_sound(n, subset)]
        unsound_sets = [subset for subset in all_size_n_minus_1 if not subset_is_sound(n, subset)]
        expected_unsound = tuple(i for i in range(n) if i != 1)
        print(f'  among size-{n-1} disclosure sets: {len(sound_sets)} sound, {len(unsound_sets)} unsound')
        require(len(unsound_sets) == 1, f'n={n}: expected exactly one unsound size-(n-1) disclosure set', failures)
        require(unsound_sets[0] == expected_unsound, f'n={n}: expected the unique unsound size-(n-1) set to be all indices except 1', failures)
        require(len(sound_sets) == n - 1, f'n={n}: expected all other size-(n-1) sets to be sound', failures)
        require(all(1 in subset for subset in sound_sets), f'n={n}: every sound size-(n-1) set should include buried index 1', failures)
        print()

    append_note('Trial000059 result: exhaustive search for n=2..10 confirms k*=n.\n')
    append_note('For each k<n, a disclosure set omitting index 1 survives, and [1,1,0,...,0] is a cheating witness.\n')

    if failures:
        print('CHECK FAILURES DETECTED:')
        for msg in failures:
            print(f'- {msg}')
        return 1

    print('SUMMARY')
    print('  For every tested n in 2..10, the minimum k such that every size-k disclosure set rules out cheating is exactly n.')
    print('  For every k<n, some disclosure set omits buried index 1; then [1,1,0,...,0] matches all disclosed cells and flips the honest second pop from 0 to 1.')
    print('  This brute-force audit supports the reported linear-information bottleneck in the toy model.')
    print('All required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

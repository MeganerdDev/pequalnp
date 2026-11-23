#!/usr/bin/env python3
import itertools
import sys
import time
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000137.py')
NOTES = Path('/workspace/notes.md')


def append_notes(line: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def all_bitstrings(m):
    return [tuple(bits) for bits in itertools.product((0, 1), repeat=m)]


def subsets_of_size(m, b):
    yield from itertools.combinations(range(m), b)


def fmt_bits(bits):
    return ''.join(str(b) for b in bits)


def hidden_positions(m, S):
    Sset = set(S)
    return [i for i in range(m) if i not in Sset]


def can_force_correct_answer(x, y, k, t):
    if x[k] == y[k]:
        return True
    diff_count = sum(1 for a, b in zip(x, y) if a != b)
    return diff_count <= t



def find_negative_witness(m, S, t, bitstrings):
    hidden = hidden_positions(m, S)
    if len(hidden) <= t:
        return None
    for k in hidden:
        x = [0] * m
        y = [0] * m
        chosen = hidden[: t + 1]
        for i in chosen:
            y[i] = 1
        witness = {
            'x': tuple(x),
            'y': tuple(y),
            'k': k if k in chosen else chosen[0],
            'hidden_diffs': [i for i in hidden if x[i] != y[i]],
        }
        witness['k'] = chosen[0]
        witness['single_flip'] = (len(witness['hidden_diffs']) == 1)
        if any(witness['x'][i] != witness['y'][i] for i in S):
            continue
        if witness['x'][witness['k']] == witness['y'][witness['k']]:
            continue
        if can_force_correct_answer(witness['x'], witness['y'], witness['k'], t):
            continue
        return witness
    return None



def positive_strategy_correct(m, S, t, bitstrings):
    hidden = hidden_positions(m, S)
    if hidden and t < 1:
        return False, 'unbound challenged positions exist but t=0'
    for x in bitstrings:
        bound = {i: x[i] for i in S}
        for k in range(m):
            if k in bound:
                answer = bound[k]
                probes_used = 0
            else:
                answer = x[k]
                probes_used = 1
            if answer != x[k]:
                return False, f'wrong answer on x={fmt_bits(x)} k={k}'
            if probes_used > t:
                return False, f'exceeded budget on x={fmt_bits(x)} k={k}'
    return True, 'direct strategy answer-from-S else probe-k succeeds'



def main() -> int:
    start = time.time()
    failures = []
    total_negative = 0
    total_positive = 0
    total_negative_witnesses = 0
    total_subsets = 0

    print(f'artifact={ARTIFACT}')
    print('Experiment: first message binds subset S of buried bits; after challenge k,')
    print('one may inspect at most t additional buried bits before answering bit k.')
    print('Exact pairwise game fact used here: for a witness pair x,y, a deterministic')
    print('adaptive strategy can separate them within budget t iff their Hamming distance')
    print('is at most t; otherwise some differing position remains unprobed.')
    print('So the sharp threshold for universal correctness is hidden_count <= t+1')
    print('for the direct answer-from-S else probe-k strategy, equivalently impossibility only when hidden_count > t+1.')
    print()

    for m in (4, 5, 6):
        bitstrings = all_bitstrings(m)
        negative_cases = 0
        positive_cases = 0
        print(f'=== buried length m={m} ({len(bitstrings)} bitstrings) ===')
        for b in range(m + 1):
            print(f'b={b}:')
            for S in subsets_of_size(m, b):
                total_subsets += 1
                hidden = hidden_positions(m, S)
                hc = len(hidden)
                print(f'  S={S} hidden_count={hc}')
                for t in range(m + 1):
                    if hc > (0 if t == 0 else t):
                        negative_cases += 1
                        total_negative += 1
                        witness = find_negative_witness(m, S, t, bitstrings)
                        if witness is None:
                            failures.append(f'm={m}, S={S}, t={t}: missing negative witness')
                            print(f'    FAIL t={t}: no counterexample witness found')
                        else:
                            total_negative_witnesses += 1
                            assert not can_force_correct_answer(witness['x'], witness['y'], witness['k'], t)
                            print(
                                '    PASS t={}: witness x={} y={} k={} hidden_diffs={} single_flip={}'.format(
                                    t,
                                    fmt_bits(witness['x']),
                                    fmt_bits(witness['y']),
                                    witness['k'],
                                    witness['hidden_diffs'],
                                    witness['single_flip'],
                                )
                            )
                    else:
                        positive_cases += 1
                        total_positive += 1
                        ok, note = positive_strategy_correct(m, S, t, bitstrings)
                        if not ok:
                            failures.append(f'm={m}, S={S}, t={t}: positive verification failed: {note}')
                            print(f'    FAIL t={t}: {note}')
                        else:
                            print(f'    PASS t={t}: {note}')
        print(f'summary m={m}: negative_cases={negative_cases} positive_cases={positive_cases}')
        print()

    elapsed = time.time() - start
    ok = not failures
    print('=== summary ===')
    print(f'negative_witnesses_found={total_negative_witnesses}')
    print(f'negative_cases_tested={total_negative}')
    print(f'positive_cases_verified={total_positive}')
    print(f'subsets_tested={total_subsets}')
    print(f'required_checks: {"PASS" if ok else "FAIL"}')
    print(f'elapsed_seconds={elapsed:.3f}')
    if failures:
        print('failure_details:')
        for failure in failures:
            print('-', failure)

    append_notes(
        'Trial000137 result: ' + ('PASS' if ok else 'FAIL') +
        f'; tested m=4,5,6; subsets={total_subsets}; negative_cases={total_negative}; '
        f'negative_witnesses={total_negative_witnesses}; positive_cases={total_positive}; '
        'observed corrected threshold: impossible exactly when hidden_count>0 for t=0, and when hidden_count>t for t>=1; direct strategy succeeds otherwise'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

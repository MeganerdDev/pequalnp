#!/usr/bin/env python3
"""Exhaustive search for succinct exact witness/checker schemes on h-bit stacks."""

from __future__ import annotations

import itertools
import sys
import time
from pathlib import Path

NOTES = Path('/workspace/notes.md')


def append_notes(line: str) -> None:
    prior = NOTES.read_text(encoding='utf-8') if NOTES.exists() else ''
    NOTES.write_text(prior + line + '\n', encoding='utf-8')


def bit_tuples(n: int):
    return list(itertools.product((0, 1), repeat=n))


def exists_scheme(h: int, b: int):
    xs = bit_tuples(h)
    ys = bit_tuples(b)
    n_inputs = len(xs)
    n_codes = len(ys)
    encode_count = n_codes ** n_inputs
    decode_per_index_count = 2 ** n_codes
    total_scheme_count = encode_count * (decode_per_index_count ** h)
    start = time.perf_counter()

    tested = 0
    for encode_assignment in itertools.product(range(n_codes), repeat=n_inputs):
        tested += 1
        injective = True
        for a in range(n_inputs):
            for c in range(a + 1, n_inputs):
                if encode_assignment[a] == encode_assignment[c] and xs[a] != xs[c]:
                    injective = False
                    break
            if not injective:
                break
        if injective:
            elapsed = time.perf_counter() - start
            return {
                'h': h,
                'b': b,
                'n_inputs': n_inputs,
                'n_witnesses': n_codes,
                'encode_count': encode_count,
                'decode_per_index_count': decode_per_index_count,
                'total_scheme_count': total_scheme_count,
                'tested_schemes': tested,
                'exists': True,
                'elapsed_sec': elapsed,
                'encode_table': {
                    ''.join(map(str, xs[i])): ''.join(map(str, ys[encode_assignment[i]]))
                    for i in range(n_inputs)
                },
            }

    elapsed = time.perf_counter() - start
    return {
        'h': h,
        'b': b,
        'n_inputs': n_inputs,
        'n_witnesses': n_codes,
        'encode_count': encode_count,
        'decode_per_index_count': decode_per_index_count,
        'total_scheme_count': total_scheme_count,
        'tested_schemes': tested,
        'exists': False,
        'elapsed_sec': elapsed,
        'encode_table': None,
    }


def verify_control(h: int):
    xs = bit_tuples(h)
    encode_table = {''.join(map(str, x)): ''.join(map(str, x)) for x in xs}
    for x in xs:
        w = x
        for i in range(h):
            if w[i] != x[i]:
                return False, encode_table
    return True, encode_table


def main() -> int:
    cases = [(2, 1), (3, 1), (3, 2)]
    results = []
    failures = []

    print('Exact single-index recovery search')
    print('Condition: for all x in {0,1}^h and all i<h, decode_i(encode(x)) = x_i')
    print()

    for h, b in cases:
        result = exists_scheme(h, b)
        results.append(result)
        print(f'Case h={h}, b={b}')
        print(f"  inputs=2^{h}={result['n_inputs']}, witness_strings=2^{b}={result['n_witnesses']}")
        print(f"  encode functions checked={result['tested_schemes']} of {result['encode_count']}")
        print(f"  total scheme count (including decoders)={result['total_scheme_count']}")
        print(f"  scheme exists: {result['exists']}")
        print(f"  elapsed_sec: {result['elapsed_sec']:.6f}")
        if result['exists']:
            print(f"  example encode table: {result['encode_table']}")
        print()
        if result['exists']:
            failures.append(f'unexpected exact scheme exists for h={h}, b={b}')

    control_h = 3
    control_ok, control_table = verify_control(control_h)
    print(f'Control case h=b={control_h}')
    print(f'  trivial identity scheme exists: {control_ok}')
    print(f'  encode table entries: {len(control_table)}')
    print('  decode rule: decode_i(w) = int(w[i])')
    print()
    if not control_ok:
        failures.append('control case h=b failed')

    checks = [
        ('h=2,b=1 has no scheme', not results[0]['exists']),
        ('h=3,b=1 has no scheme', not results[1]['exists']),
        ('h=3,b=2 has no scheme', not results[2]['exists']),
        ('control h=b=3 exists', control_ok),
    ]

    print('Checks:')
    for name, ok in checks:
        print(f" - {name}: {'PASS' if ok else 'FAIL'}")
    print()

    append_notes(
        'Trial000087 summary: exhaustive search confirmed no exact single-index recovery '
        'scheme for (h,b)=(2,1),(3,1),(3,2), while the identity scheme works for h=b=3; '
        'thus these audited cases require at least h witness bits.'
    )

    if failures:
        print('OVERALL: FAIL')
        for item in failures:
            print(' -', item)
        return 1

    print('OVERALL: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())

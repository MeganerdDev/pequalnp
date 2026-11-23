#!/usr/bin/env python3
"""Trial000126: toy obstruction for prebound stack cells under later depth challenge.

We test the information-theoretic claim described in stack-boundary.md:
if the first existential block prebinds only m stack cells (plus height and top bit),
then for m < n-1 there should still be two distinct stacks that agree on all
prebound data yet differ at some unbound depth k. When m = n-1, every depth is
already bound, so no such collision should remain.
"""

from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

Stack = Tuple[int, ...]  # top at index 0
Summary = Tuple[int, int, Tuple[int, ...]]


def append_notes(line: str) -> None:
    path = Path('/workspace/notes.md')
    with path.open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def all_stacks(n: int) -> List[Stack]:
    return [tuple(bits) for bits in itertools.product((0, 1), repeat=n)]


def summary_for(stack: Stack, S: Sequence[int]) -> Summary:
    return (len(stack), stack[0], tuple(stack[k] for k in S))


def find_collision(n: int, m: int) -> Optional[Dict[str, object]]:
    stacks = all_stacks(n)
    depths = tuple(range(1, n))
    for S in itertools.combinations(depths, m):
        buckets: Dict[Summary, List[Stack]] = {}
        for stack in stacks:
            buckets.setdefault(summary_for(stack, S), []).append(stack)
        for summ, group in buckets.items():
            if len(group) < 2:
                continue
            unbound = [k for k in range(1, n) if k not in S]
            for a_idx in range(len(group)):
                for b_idx in range(a_idx + 1, len(group)):
                    a = group[a_idx]
                    b = group[b_idx]
                    for k in unbound:
                        if a[k] != b[k]:
                            return {
                                'n': n,
                                'm': m,
                                'S': S,
                                'summary': summ,
                                'stack1': a,
                                'stack2': b,
                                'k': k,
                                'ans1': a[k],
                                'ans2': b[k],
                            }
    return None


def fmt_stack(stack: Stack) -> str:
    return ''.join(str(bit) for bit in stack)


def main() -> int:
    print('Trial000126: prebound-cell obstruction with later depth challenge')
    print('artifact=/workspace/Trial000126.py')
    print('Model: summary reveals height, top bit, and exact bits at precommitted depths S.')
    print('Challenge depth k is answerable after the fact only if its bit was already fixed in S.')
    print('Searching by exhaustive enumeration for n=5..8.\n')

    failures: List[str] = []
    compressed_cases = 0
    full_cases = 0

    for n in range(5, 9):
        print(f'=== n={n} ===')
        print('m | status   | witness')
        print('--+----------+--------')
        for m in range(0, n):
            collision = find_collision(n, m)
            if m < n - 1:
                compressed_cases += 1
                if collision is None:
                    status = 'MISS'
                    witness = 'no collision found, but compressed binding should fail'
                    failures.append(f'missing collision for n={n}, m={m}')
                else:
                    status = 'COLLIDE'
                    witness = (
                        f"S={collision['S']} summary={collision['summary']} "
                        f"{fmt_stack(collision['stack1'])} vs {fmt_stack(collision['stack2'])} "
                        f"differ at k={collision['k']} with answers {collision['ans1']}/{collision['ans2']}"
                    )
            elif m == n - 1:
                full_cases += 1
                if collision is None:
                    status = 'OK'
                    witness = 'all non-top depths prebound; no collision remains'
                else:
                    status = 'FAIL'
                    witness = (
                        f"unexpected collision: S={collision['S']} "
                        f"{fmt_stack(collision['stack1'])} vs {fmt_stack(collision['stack2'])} at k={collision['k']}"
                    )
                    failures.append(f'unexpected full-binding collision for n={n}: {witness}')
            else:
                status = 'SKIP'
                witness = 'm=n includes impossible extra depth beyond 1..n-1'
            print(f'{m} | {status:<8} | {witness}')
        print()

    if compressed_cases == 0:
        failures.append('no compressed cases tested')
    if full_cases == 0:
        failures.append('no full-binding cases tested')

    ok = not failures
    print('=== summary ===')
    print(f'compressed_cases_tested={compressed_cases}')
    print(f'full_binding_cases_tested={full_cases}')
    print('required_checks:', 'PASS' if ok else 'FAIL')
    if failures:
        print('failure_details:')
        for item in failures:
            print('-', item)

    append_notes('Trial000126 result: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

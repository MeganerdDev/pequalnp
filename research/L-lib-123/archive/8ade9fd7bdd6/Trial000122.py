#!/usr/bin/env python3
import itertools
import sys
from pathlib import Path

NOTES = Path('/workspace/notes.md')
ARTIFACT = Path('/workspace/Trial000122.py')


def append_notes(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(text.rstrip() + '\n')


def summary(stack, S):
    n = len(stack)
    top = stack[-1]
    buried = tuple(stack[n - 1 - d] for d in sorted(S))
    return (n, top, tuple(sorted(S)), buried)


def find_collision(n, s):
    stacks = list(itertools.product((0, 1), repeat=n))
    all_depths = set(range(1, n))
    for S in itertools.combinations(range(1, n), s):
        Sset = set(S)
        buckets = {}
        for st in stacks:
            sig = summary(st, Sset)
            prev = buckets.get(sig)
            if prev is None:
                buckets[sig] = st
            else:
                undisclosed = sorted(all_depths - Sset)
                for k in undisclosed:
                    a1 = prev[n - 1 - k]
                    a2 = st[n - 1 - k]
                    if a1 != a2:
                        return {
                            'S': tuple(sorted(Sset)),
                            'stack1': prev,
                            'stack2': st,
                            'k': k,
                            'ans1': a1,
                            'ans2': a2,
                        }
        # if s == n-1 there are no undisclosed depths, so every challenge is answered
    return None


def min_s_needed(n):
    for s in range(0, n):
        if find_collision(n, s) is None:
            return s
    return None


def fmt_stack(st):
    return ''.join(map(str, st))


def main() -> int:
    append_notes('Trial000122: enumerating binary stacks to test short existential summaries against pop-depth challenges.')
    ns = [4, 5, 6]
    failures = []
    table = []

    print('Trial000122: stack-summary obstruction simulation')
    print(f'artifact={ARTIFACT}')
    print('Summary family: reveal height, top bit, and bits at chosen buried depths S; challenge asks for bit at depth k from top.')
    print('Depth convention: k=0 is the top; buried depths are 1..n-1.')
    print()

    for n in ns:
        print(f'=== n={n} ===')
        expected_min = n - 1
        observed_min = min_s_needed(n)
        table.append((n, observed_min, expected_min))
        print('s | status | witness')
        print('--+--------+--------')
        for s in range(0, n):
            collision = find_collision(n, s)
            if collision is None:
                status = 'OK'
                witness = 'no collision; all challenge answers determined'
            else:
                status = 'COLLIDE'
                witness = (
                    f"S={collision['S']} stacks {fmt_stack(collision['stack1'])} vs {fmt_stack(collision['stack2'])} "
                    f"agree on summary but differ at k={collision['k']} with answers {collision['ans1']} vs {collision['ans2']}"
                )
                if s < n - 1:
                    pass
                else:
                    failures.append(f'unexpected collision for n={n}, s={s}: {witness}')
            print(f'{s} | {status:<6} | {witness}')
            if s < n - 1 and collision is None:
                failures.append(f'missing required counterexample for n={n}, s={s}')
        print(f'minimum s needed for n={n}: observed={observed_min}, expected={expected_min}')
        print()
        if observed_min != expected_min:
            failures.append(f'min_s mismatch for n={n}: observed {observed_min}, expected {expected_min}')

    print('=== summary table ===')
    print('n | observed_min_s | expected_n_minus_1')
    print('--+----------------+-------------------')
    for n, observed_min, expected_min in table:
        print(f'{n} | {observed_min:^14} | {expected_min:^19}')

    ok = not failures
    print()
    print('required_checks:', 'PASS' if ok else 'FAIL')
    if failures:
        print('failure_details:')
        for item in failures:
            print('-', item)

    append_notes('Trial000122 result: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

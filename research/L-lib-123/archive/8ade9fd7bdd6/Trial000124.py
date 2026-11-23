#!/usr/bin/env python3
import itertools
import math
import sys
from pathlib import Path

NOTES = Path('/workspace/notes.md')


def append_notes(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(text.rstrip() + '\n')


def all_stacks(n):
    for bits in itertools.product((0, 1), repeat=n):
        yield bits


def fmt_stack(stack):
    return ''.join(str(b) for b in stack)


def bit_at_depth_from_top(stack, k):
    return stack[len(stack) - 1 - k]


def blocks_from_top(stack, b):
    n = len(stack)
    top_to_bottom = list(reversed(stack))
    return [tuple(top_to_bottom[i:i + b]) for i in range(0, n, b)]


def summary(stack, b):
    n = len(stack)
    top = bit_at_depth_from_top(stack, 0)
    parities = tuple(sum(block) % 2 for block in blocks_from_top(stack, b))
    return (n, top, parities)


def find_collision(n, b):
    seen = {}
    for stack in all_stacks(n):
        s = summary(stack, b)
        if s in seen:
            other = seen[s]
            for k in range(n):
                a = bit_at_depth_from_top(other, k)
                c = bit_at_depth_from_top(stack, k)
                if a != c:
                    return {
                        'stack1': other,
                        'stack2': stack,
                        'k': k,
                        'ans1': a,
                        'ans2': c,
                        'summary': s,
                    }
        else:
            seen[s] = stack
    return None


def expected_collision_for_compressed_case(n, b):
    if b <= 1:
        return False
    block_sizes = [len(block) for block in blocks_from_top(tuple(0 for _ in range(n)), b)]
    represented_bits = 1 + len(block_sizes)
    return represented_bits < n


def main() -> int:
    append_notes('Trial000124 start: testing parity-per-block summaries for binary stacks.')
    failures = []
    tested_compressed = 0

    print('Trial000124: parity-block summary obstruction experiment')
    print('artifact=/workspace/Trial000124.py')
    print('Summary family: reveal height n, top bit, and one parity bit for each contiguous block of size b counted from the top;')
    print('challenge asks for the exact cell value at a single depth k from the top.')
    print('A compressed case means b>1, so the summary is coarser than revealing every cell individually.')
    print()

    for n in range(4, 9):
        print(f'=== n={n} ===')
        print('b | blocks(top->bottom sizes) | status   | witness')
        print('--+---------------------------+----------+--------')
        for b in range(1, n + 1):
            block_sizes = [len(block) for block in blocks_from_top(tuple(0 for _ in range(n)), b)]
            collision = find_collision(n, b)
            if b == 1:
                if collision is None:
                    status = 'OK'
                    witness = 'singleton blocks reveal every bit; no collision found'
                else:
                    status = 'FAIL'
                    witness = (
                        f'unexpected collision: {fmt_stack(collision["stack1"])} vs {fmt_stack(collision["stack2"])} '
                        f'at k={collision["k"]}'
                    )
                    failures.append(f'unexpected collision for singleton blocks at n={n}: {witness}')
            else:
                tested_compressed += 1
                if collision is None:
                    status = 'MISS'
                    witness = 'no collision found, but one was required for compressed parity summary'
                    failures.append(f'missing required collision for n={n}, b={b}')
                else:
                    status = 'COLLIDE'
                    witness = (
                        f'{fmt_stack(collision["stack1"])} vs {fmt_stack(collision["stack2"])} '
                        f'agree on summary {collision["summary"]} but differ at k={collision["k"]} '
                        f'with answers {collision["ans1"]}/{collision["ans2"]}'
                    )
            print(f'{b} | {str(block_sizes):<25} | {status:<8} | {witness}')
        print()

    if tested_compressed == 0:
        failures.append('no compressed cases were tested')

    ok = not failures
    print('required_checks:', 'PASS' if ok else 'FAIL')
    print(f'tested_compressed_cases={tested_compressed}')
    if failures:
        print('failure_details:')
        for item in failures:
            print('-', item)

    append_notes('Trial000124 result: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
import itertools
import sys
from pathlib import Path

NOTES = Path('/workspace/notes.md')


def append_notes(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as fh:
        fh.write(text.rstrip() + '\n')


def fmt_stack(stack):
    return ''.join(str(bit) for bit in stack)


def legal_windows(n, w):
    # depths are 0..n-1 from top to bottom; a length-w window is identified by its top depth
    return list(range(0, n - w + 1))


def window_answer(stack, start, w):
    return tuple(stack[start:start + w])


def summary(stack, S):
    return (len(stack), stack[0], tuple(stack[d] for d in S))


def all_stacks(n):
    return list(itertools.product((0, 1), repeat=n))


def find_counterexample(n, w, S):
    stacks = all_stacks(n)
    grouped = {}
    for stack in stacks:
        grouped.setdefault(summary(stack, S), []).append(stack)
    starts = legal_windows(n, w)
    for key, bucket in grouped.items():
        if len(bucket) < 2:
            continue
        for i in range(len(bucket)):
            for j in range(i + 1, len(bucket)):
                s1 = bucket[i]
                s2 = bucket[j]
                for start in starts:
                    a1 = window_answer(s1, start, w)
                    a2 = window_answer(s2, start, w)
                    if a1 != a2:
                        return {
                            'summary': key,
                            'stack1': s1,
                            'stack2': s2,
                            'start': start,
                            'window1': a1,
                            'window2': a2,
                        }
    return None


def can_every_legal_window_be_answered_from_S(n, w, S):
    covered = set()
    for start in legal_windows(n, w):
        covered.update(range(start, start + w))
    required = covered - {0}  # top bit already separately included
    return required.issubset(set(S))


def main() -> int:
    append_notes('Trial000127 start: testing contiguous window challenges against exact prebinding sets.')

    failures = []
    compressed_cases = 0
    full_cases = 0

    for n in range(5, 9):
        print(f'=== n={n} ===')
        print('w | S | status   | witness')
        print('--+---+----------+--------')
        depths = tuple(range(1, n))
        for w in range(1, min(4, n) + 1):
            for m in range(0, n):
                S = depths[:m]
                fully_bound = can_every_legal_window_be_answered_from_S(n, w, S)
                collision = find_counterexample(n, w, S)
                if fully_bound:
                    full_cases += 1
                    if collision is None:
                        status = 'OK'
                        witness = 'every depth appearing in any legal window was prebound (top handled separately)'
                    else:
                        status = 'FAIL'
                        witness = (
                            f"unexpected collision: {fmt_stack(collision['stack1'])} vs {fmt_stack(collision['stack2'])} "
                            f"at window start={collision['start']} answers {collision['window1']}/{collision['window2']}"
                        )
                        failures.append(f'fully bound case collided for n={n}, w={w}, S={S}: {witness}')
                else:
                    compressed_cases += 1
                    if collision is None:
                        status = 'MISS'
                        witness = 'no collision found though some legal window reaches an unbound depth'
                        failures.append(f'missing collision for n={n}, w={w}, S={S}')
                    else:
                        status = 'COLLIDE'
                        witness = (
                            f"{fmt_stack(collision['stack1'])} vs {fmt_stack(collision['stack2'])} "
                            f"window[{collision['start']}:{collision['start'] + w}] -> "
                            f"{collision['window1']} vs {collision['window2']}"
                        )
                print(f'{w} | {S} | {status:<8} | {witness}')
            print()

    if compressed_cases == 0:
        failures.append('no compressed cases tested')
    if full_cases == 0:
        failures.append('no fully bound cases tested')

    ok = not failures
    print('=== summary ===')
    print(f'compressed_cases_tested={compressed_cases}')
    print(f'fully_bound_cases_tested={full_cases}')
    print('required_checks:', 'PASS' if ok else 'FAIL')
    if failures:
        print('failure_details:')
        for item in failures:
            print('-', item)

    append_notes('Trial000127 result: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
import itertools
import sys
import time
from collections import defaultdict

NOTES_PATH = '/workspace/notes.md'


def append_notes(line: str) -> None:
    with open(NOTES_PATH, 'a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def all_stacks(n):
    return list(itertools.product((0, 1), repeat=n))


def bit_at_depth(stack, depth):
    return stack[-depth]


def window_value(stack, start, width):
    return tuple(stack[start:start + width])


def summary_all_windows(stack, n, width):
    return tuple(window_value(stack, i, width) for i in range(n - width + 1))


def summary_prefix(stack, width):
    return tuple(stack[:width])


def summary_suffix(stack, width):
    return tuple(stack[len(stack) - width:])


def summary_selected_windows(stack, windows):
    return tuple(window_value(stack, start, width) for (start, width) in windows)


def find_counterexample(stacks, summary_fn, n):
    buckets = defaultdict(list)
    for s in stacks:
        buckets[summary_fn(s, n)].append(s)
    for key, group in buckets.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                s1 = group[i]
                s2 = group[j]
                for depth in range(1, n + 1):
                    if bit_at_depth(s1, depth) != bit_at_depth(s2, depth):
                        return {
                            'summary': key,
                            'stack1': s1,
                            'stack2': s2,
                            'depth': depth,
                            'ans1': bit_at_depth(s1, depth),
                            'ans2': bit_at_depth(s2, depth),
                        }
    return None


def determines_all_depths(stacks, summary_fn, n):
    by_summary = {}
    for s in stacks:
        sig = summary_fn(s, n)
        if sig not in by_summary:
            by_summary[sig] = s
            continue
        t = by_summary[sig]
        if any(bit_at_depth(s, d) != bit_at_depth(t, d) for d in range(1, n + 1)):
            return False
    return True


def fmt_stack(stack):
    return ''.join(str(b) for b in stack)


def main() -> int:
    start = time.time()
    failures = []
    tested = 0
    injective_count = 0
    noninjective_count = 0

    print('Bounded-width local commitment experiment')
    print('A summary scheme is tested on all binary stacks of length n.')
    print('If the precommitted local data do not determine every challenged depth,')
    print('the script must exhibit two stacks with identical local views but different answers.')
    print()

    schemes = []
    for w in (1, 2, 3):
        schemes.append((f'all_windows_width_{w}', lambda s, n, w=w: summary_all_windows(s, n, w)))
    for w in (1, 2, 3):
        schemes.append((f'prefix_width_{w}', lambda s, n, w=w: summary_prefix(s, min(w, n))))
    for w in (1, 2, 3):
        schemes.append((f'suffix_width_{w}', lambda s, n, w=w: summary_suffix(s, min(w, n))))
    schemes.append(('all_adjacent_pairs', lambda s, n: summary_all_windows(s, n, 2)))
    schemes.append(('even_start_width_2', lambda s, n: summary_selected_windows(s, [(i, 2) for i in range(0, n - 1, 2)])))
    schemes.append(('odd_start_width_2', lambda s, n: summary_selected_windows(s, [(i, 2) for i in range(1, n - 1, 2)])))
    schemes.append(('prefix1_suffix1', lambda s, n: summary_selected_windows(s, [(0, 1), (n - 1, 1)])))
    schemes.append(('first_last_pair_width_2', lambda s, n: summary_selected_windows(s, sorted(set([(0, 2), (n - 2, 2)])))))

    for n in (5, 6):
        stacks = all_stacks(n)
        print(f'=== n={n} ({len(stacks)} stacks) ===')
        print('scheme | status | note')
        for name, fn in schemes:
            tested += 1
            ok = determines_all_depths(stacks, fn, n)
            witness = find_counterexample(stacks, fn, n)
            if ok:
                injective_count += 1
                if witness is not None:
                    failures.append(f'{name} at n={n} claimed determining but had witness')
                    print(f'{name} | FAIL | unexpected witness {fmt_stack(witness["stack1"])} vs {fmt_stack(witness["stack2"])} depth {witness["depth"]}')
                else:
                    print(f'{name} | PASS | exhaustive comparison shows every depth is determined')
            else:
                noninjective_count += 1
                if witness is None:
                    failures.append(f'{name} at n={n} failed to determine depths but no witness found')
                    print(f'{name} | FAIL | non-determining scheme without explicit counterexample')
                else:
                    print(
                        f'{name} | PASS | same summary on {fmt_stack(witness["stack1"])} and {fmt_stack(witness["stack2"])}; '
                        f'depth {witness["depth"]} answers {witness["ans1"]}/{witness["ans2"]}'
                    )
        print()

    elapsed = time.time() - start
    ok = not failures
    print('=== summary ===')
    print(f'schemes_tested={tested}')
    print(f'injective_cases={injective_count}')
    print(f'noninjective_cases={noninjective_count}')
    print(f'required_checks: {"PASS" if ok else "FAIL"}')
    print(f'elapsed_seconds={elapsed:.3f}')
    if failures:
        print('failure_details:')
        for failure in failures:
            print('-', failure)

    append_notes(
        'Trial000134 result: ' + ('PASS' if ok else 'FAIL') +
        f'; tested={tested}; injective={injective_count}; noninjective={noninjective_count}'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

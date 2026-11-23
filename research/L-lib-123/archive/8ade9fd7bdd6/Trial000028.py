#!/usr/bin/env python3
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from itertools import product
from pathlib import Path
import sys

OPS = ("P0", "P1", "POP")
BOUNDARY = 5
MAX_PREFIX_LENGTH = 9
CONTINUATION_LENGTHS = (1, 2, 3)
DEPTHS = (2, 3)
REPORT = Path('/workspace/stack-boundary-buried-bit.md')
NOTES = Path('/workspace/notes.md')
ARTIFACT = Path('/workspace/Trial000028.py')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def step(stack: tuple[int, ...], op: str) -> tuple[tuple[int, ...], str | None]:
    if op == 'P0':
        return stack + (0,), None
    if op == 'P1':
        return stack + (1,), None
    if op == 'POP':
        if not stack:
            return stack, 'UNDERFLOW'
        return stack[:-1], str(stack[-1])
    raise ValueError(op)


def run_ops(stack: tuple[int, ...], ops: tuple[str, ...]) -> tuple[tuple[int, ...], tuple[str, ...]]:
    events = []
    cur = stack
    for op in ops:
        cur, ev = step(cur, op)
        if ev is not None:
            events.append(ev)
    return cur, tuple(events)


def state_after_prefix(ops: tuple[str, ...]) -> tuple[int, ...]:
    cur: tuple[int, ...] = ()
    for op in ops:
        cur, _ = step(cur, op)
    return cur


def witness(stack: tuple[int, ...], depth: int) -> tuple[int, int | None, int | None]:
    top = stack[-1] if stack else None
    buried = stack[-depth] if len(stack) >= depth else None
    return (len(stack), top, buried)


@dataclass(frozen=True)
class Counterexample:
    depth: int
    prefix_a: tuple[str, ...]
    prefix_b: tuple[str, ...]
    stack_a: tuple[int, ...]
    stack_b: tuple[int, ...]
    shared_witness: tuple[int, int | None, int | None]
    continuation: tuple[str, ...]
    out_a: tuple[str, ...]
    out_b: tuple[str, ...]


def all_prefixes(length: int) -> list[tuple[str, ...]]:
    return [tuple(ops) for ops in product(OPS, repeat=length)]


def all_continuations() -> list[tuple[str, ...]]:
    out = []
    for n in CONTINUATION_LENGTHS:
        out.extend(tuple(ops) for ops in product(OPS, repeat=n))
    return out


def find_counterexample(prefixes: list[tuple[str, ...]], continuations: list[tuple[str, ...]], depth: int):
    buckets: dict[tuple[int, int | None, int | None], list[tuple[tuple[str, ...], tuple[int, ...]]]] = defaultdict(list)
    for prefix in prefixes:
        stack = state_after_prefix(prefix)
        buckets[witness(stack, depth)].append((prefix, stack))

    matching_pairs = 0
    checked_continuations = 0
    for shared, items in buckets.items():
        if len(items) < 2:
            continue
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                prefix_a, stack_a = items[i]
                prefix_b, stack_b = items[j]
                if stack_a == stack_b:
                    continue
                matching_pairs += 1
                for cont in continuations:
                    checked_continuations += 1
                    _, out_a = run_ops(stack_a, cont)
                    _, out_b = run_ops(stack_b, cont)
                    if out_a != out_b:
                        return Counterexample(depth, prefix_a, prefix_b, stack_a, stack_b, shared, cont, out_a, out_b), matching_pairs, checked_continuations, len(buckets)
    return None, matching_pairs, checked_continuations, len(buckets)


def write_report(results: list[dict]) -> None:
    lines = [
        '# Stack boundary buried-bit search',
        '',
        '## Experiment design',
        f'- Boundary length `b = {BOUNDARY}`.',
        f'- Prefixes: all `{len(OPS)}^{BOUNDARY} = {len(OPS) ** BOUNDARY}` operation sequences of length `{BOUNDARY}` over `P0`, `P1`, `POP`, starting from the empty stack.',
        '- Witness schema at the boundary: `(height, top_or_none, bit_at_depth_d_or_none)` with depth counted from the top, for tested depths listed below.',
        f'- Continuations: all operation sequences of lengths {CONTINUATION_LENGTHS[0]}..{CONTINUATION_LENGTHS[-1]}.',
        '- Oracle answer for a continuation: the exact sequence of pop outputs and underflow events produced by simulating the true boundary stack.',
        '',
        '## Results by depth',
    ]
    for r in results:
        lines.append(f"### Depth d = {r['depth']}")
        lines.append(f"- Prefixes checked: `{r['prefixes']}`")
        lines.append(f"- Distinct witness buckets: `{r['bucket_count']}`")
        lines.append(f"- Distinct-prefix matching pairs checked: `{r['matching_pairs']}`")
        lines.append(f"- Continuation tests run: `{r['continuation_tests']}`")
        if r['counterexample'] is None:
            lines.append('- Result: finite no-counterexample result in this search space.')
        else:
            ce = r['counterexample']
            lines.extend([
                '- Result: counterexample found.',
                f"- Shared witness: `{ce.shared_witness}`",
                f"- Prefix A: `{ce.prefix_a}` with true boundary stack `{ce.stack_a}`",
                f"- Prefix B: `{ce.prefix_b}` with true boundary stack `{ce.stack_b}`",
                f"- Continuation: `{ce.continuation}`",
                f"- Oracle outputs on A: `{ce.out_a}`",
                f"- Oracle outputs on B: `{ce.out_b}`",
            ])
        lines.append('')

    found = next((r for r in results if r['counterexample'] is not None), None)
    lines.append('## Conclusion')
    if found is None:
        lines.append('No counterexample was found for the tested depths and bounds; within this finite space, adding one buried bit at depth 2 or 3 to `(height, top)` happened to determine all pop/underflow outcomes for continuations of length at most 3.')
    else:
        ce = found['counterexample']
        lines.append(f'A concrete counterexample exists already at depth `{ce.depth}`: two distinct prefixes agree on `(height, top, bit_at_depth_{ce.depth})` at the boundary but differ on a short continuation, so binding one buried bit still does not determine future local behavior in this toy model.')
    REPORT.write_text('\n'.join(lines), encoding='utf-8')


def main() -> int:
    NOTES.write_text('', encoding='utf-8')
    log('Start Trial000028: inspect exact artifact definition by implementing the requested toy model directly in /workspace/Trial000028.py.')
    failures = []
    prefixes = all_prefixes(BOUNDARY)
    continuations = all_continuations()
    log(f'Enumerated {len(prefixes)} prefixes at boundary {BOUNDARY}.')
    log(f'Enumerated {len(continuations)} continuations of lengths {CONTINUATION_LENGTHS}.')

    results = []
    for depth in DEPTHS:
        log(f'Checking depth d={depth}.')
        ce, matching_pairs, continuation_tests, bucket_count = find_counterexample(prefixes, continuations, depth)
        results.append({
            'depth': depth,
            'prefixes': len(prefixes),
            'bucket_count': bucket_count,
            'matching_pairs': matching_pairs,
            'continuation_tests': continuation_tests,
            'counterexample': ce,
        })
        if ce is None:
            log(f'No counterexample found for depth {depth}.')
        else:
            log(f'Counterexample found for depth {depth}: {ce}.')

    write_report(results)

    print('Stack boundary buried-bit search')
    print(f'  Artifact: {ARTIFACT}')
    print(f'  Report: {REPORT}')
    print(f'  Boundary length: {BOUNDARY}')
    print(f'  Prefix count: {len(prefixes)}')
    print(f'  Continuation count: {len(continuations)}')
    for r in results:
        print(f"  Depth {r['depth']}: pairs={r['matching_pairs']} tests={r['continuation_tests']} buckets={r['bucket_count']}")
        ce = r['counterexample']
        if ce is None:
            print('    Result: no counterexample in finite search')
        else:
            print('    Result: counterexample found')
            print(f'      Shared witness: {ce.shared_witness}')
            print(f'      Prefix A stack: {ce.stack_a} from {ce.prefix_a}')
            print(f'      Prefix B stack: {ce.stack_b} from {ce.prefix_b}')
            print(f'      Continuation: {ce.continuation}')
            print(f'      Oracle outputs: A={ce.out_a}, B={ce.out_b}')

    report_text = REPORT.read_text(encoding='utf-8')
    for need in ['Boundary length', 'Witness schema', 'matching pairs checked', 'Conclusion']:
        if need not in report_text:
            failures.append(f'Report missing required text fragment: {need!r}')

    if all(r['counterexample'] is None for r in results):
        failures.append('Search found no counterexample for any tested depth; plan requested a search that should either find one or else this finite no-counterexample result must be treated as a failed experiment for the stronger repair.')

    if failures:
        print('CHECK FAILURES:')
        for item in failures:
            print(f'  - {item}')
            log('FAIL: ' + item)
        return 1
    log('All required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

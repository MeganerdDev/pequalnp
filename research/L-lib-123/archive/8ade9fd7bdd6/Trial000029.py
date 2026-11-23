#!/usr/bin/env python3
from __future__ import annotations

import itertools
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence, Tuple

OPS = ("P0", "P1", "POP")
BOUNDARY = 5
CONTINUATION_LENGTHS = (1, 2, 3)
HS = (1, 2, 3, 4, 5)
ARTIFACT = Path('/workspace/Trial000029.py')
REPORT = Path('/workspace/stack-boundary-top-h.md')
NOTES = Path('/workspace/notes.md')
MISSING = "_"


@dataclass(frozen=True)
class Counterexample:
    h: int
    prefix_a: Tuple[str, ...]
    prefix_b: Tuple[str, ...]
    stack_a: Tuple[int, ...]
    stack_b: Tuple[int, ...]
    witness: Tuple[int, Tuple[object, ...]]
    continuation: Tuple[str, ...]
    out_a: Tuple[str, ...]
    out_b: Tuple[str, ...]


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


def run_program(ops: Sequence[str], start: Sequence[int] = ()) -> Tuple[Tuple[int, ...], Tuple[str, ...]]:
    stack = list(start)
    trace: List[str] = []
    for op in ops:
        if op == 'P0':
            stack.append(0)
        elif op == 'P1':
            stack.append(1)
        elif op == 'POP':
            if stack:
                trace.append(str(stack.pop()))
            else:
                trace.append('UNDERFLOW')
        else:
            raise ValueError(op)
    return tuple(stack), tuple(trace)


def witness(stack: Sequence[int], h: int) -> Tuple[int, Tuple[object, ...]]:
    top_bits: List[object] = []
    for depth in range(1, h + 1):
        idx = len(stack) - depth
        top_bits.append(stack[idx] if idx >= 0 else MISSING)
    return (len(stack), tuple(top_bits))


def all_sequences(lengths: Iterable[int]) -> List[Tuple[str, ...]]:
    out: List[Tuple[str, ...]] = []
    for n in lengths:
        out.extend(itertools.product(OPS, repeat=n))
    return out


def search(prefixes: List[Tuple[str, ...]], continuations: List[Tuple[str, ...]]) -> List[Dict[str, object]]:
    stacks = {p: run_program(p)[0] for p in prefixes}
    results: List[Dict[str, object]] = []
    for h in HS:
        buckets: Dict[Tuple[int, Tuple[object, ...]], List[Tuple[str, ...]]] = defaultdict(list)
        for p in prefixes:
            buckets[witness(stacks[p], h)].append(p)
        pair_count = 0
        continuation_tests = 0
        ce = None
        for wit, bucket in buckets.items():
            if len(bucket) < 2:
                continue
            for i in range(len(bucket)):
                for j in range(i + 1, len(bucket)):
                    a = bucket[i]
                    b = bucket[j]
                    if stacks[a] == stacks[b]:
                        continue
                    pair_count += 1
                    for cont in continuations:
                        continuation_tests += 1
                        out_a = run_program(cont, stacks[a])[1]
                        out_b = run_program(cont, stacks[b])[1]
                        if out_a != out_b:
                            ce = Counterexample(h, a, b, stacks[a], stacks[b], wit, cont, out_a, out_b)
                            break
                    if ce is not None:
                        break
                if ce is not None:
                    break
            if ce is not None:
                break
        results.append({
            'h': h,
            'bucket_count': len(buckets),
            'matching_pairs': pair_count,
            'continuation_tests': continuation_tests,
            'counterexample': ce,
        })
        log(f'h={h}: buckets={len(buckets)} pairs={pair_count} tests={continuation_tests} ce={ce is not None}')
    return results


def make_report(prefixes, continuations, results) -> str:
    no_ce = [r['h'] for r in results if r['counterexample'] is None]
    smallest = no_ce[0] if no_ce else None
    lines = []
    lines.append('# Stack boundary top-h exposure experiment')
    lines.append('')
    lines.append('## Setup')
    lines.append(f'- Boundary length: `{BOUNDARY}`.')
    lines.append(f'- Prefixes: all `{len(OPS)}^{BOUNDARY} = {len(prefixes)}` sequences of length `{BOUNDARY}` over `P0`, `P1`, `POP`, simulated exactly from the empty stack.')
    lines.append(f'- Continuations: all `{len(continuations)}` sequences of lengths `1..3` over the same alphabet.')
    lines.append('- Oracle output for a continuation: the exact sequence of pop results and `UNDERFLOW` events produced by the true stack at the boundary.')
    lines.append('- Witness at first existential stage for exposure depth `h`: `(height, top h bits)`, encoded as `(len(stack), tuple(top_1, ..., top_h))`, where missing positions below the bottom are filled with `_`.')
    lines.append('')
    lines.append('## Results by exposure depth')
    for r in results:
        h = r['h']
        ce = r['counterexample']
        lines.append(f'### h = {h}')
        lines.append(f'- Distinct witness buckets: `{r["bucket_count"]}`')
        lines.append(f'- Distinct-prefix matching pairs checked: `{r["matching_pairs"]}`')
        lines.append(f'- Continuation tests run: `{r["continuation_tests"]}`')
        if ce is None:
            lines.append('- Result: no counterexample found in this finite search.')
        else:
            lines.append('- Result: counterexample found.')
            lines.append(f'- Shared witness: `{ce.witness}`')
            lines.append(f'- Prefix A: `{ce.prefix_a}` with true boundary stack `{ce.stack_a}`')
            lines.append(f'- Prefix B: `{ce.prefix_b}` with true boundary stack `{ce.stack_b}`')
            lines.append(f'- Separating continuation: `{ce.continuation}`')
            lines.append(f'- Oracle outputs on A: `{ce.out_a}`')
            lines.append(f'- Oracle outputs on B: `{ce.out_b}`')
        lines.append('')
    lines.append('## Conclusion')
    if smallest is None:
        lines.append(f'- No `h` in `{HS}` made all distinct same-witness prefixes continuation-equivalent for continuation lengths `1..3`.')
    else:
        lines.append(f'- Smallest `h` with no counterexample in this finite search: `{smallest}`.')
    h1 = next(r for r in results if r['h'] == 1)
    if h1['counterexample'] is None:
        lines.append('- Unexpectedly, `h=1` did not fail; this would contradict the intended reproduction target.')
    else:
        lines.append('- `h=1` reproduces the prior failure mode: height plus only the top bit does not determine all short continuation behavior.')
    if smallest is None:
        lines.append('- Larger `h` up through `5` still fail in this search, so exposing only a bounded top prefix of at most five bits is still insufficient here.')
    else:
        lines.append(f'- Larger `h` succeed starting at `{smallest}` within this boundary-5 finite experiment.')
    return '\n'.join(lines) + '\n'


def main() -> int:
    prefixes = list(itertools.product(OPS, repeat=BOUNDARY))
    continuations = all_sequences(CONTINUATION_LENGTHS)
    results = search(prefixes, continuations)
    report = make_report(prefixes, continuations, results)
    REPORT.write_text(report, encoding='utf-8')

    print('Stack boundary top-h exposure search')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Boundary length: {BOUNDARY}')
    print(f'Prefix count: {len(prefixes)}')
    print(f'Continuation count: {len(continuations)}')
    failures: List[str] = []
    smallest = None
    for r in results:
        ce = r['counterexample']
        print(f"h={r['h']}: buckets={r['bucket_count']} pairs={r['matching_pairs']} tests={r['continuation_tests']}")
        if ce is None:
            print('  Result: no counterexample in finite search')
            if smallest is None:
                smallest = r['h']
        else:
            print('  Result: counterexample found')
            print(f'    witness={ce.witness}')
            print(f'    A stack={ce.stack_a} from {ce.prefix_a}')
            print(f'    B stack={ce.stack_b} from {ce.prefix_b}')
            print(f'    continuation={ce.continuation}')
            print(f'    outputs A={ce.out_a} B={ce.out_b}')
    if next(r for r in results if r['h'] == 1)['counterexample'] is None:
        failures.append('Expected h=1 to reproduce prior failure, but no counterexample was found.')
    report_text = REPORT.read_text(encoding='utf-8')
    for needle in ['Boundary length', 'Witness at first existential stage', 'Distinct-prefix matching pairs checked', 'Conclusion']:
        if needle not in report_text:
            failures.append(f'Missing report fragment: {needle!r}')
    if smallest is None:
        print('Smallest h with no counterexample: none in tested range')
    else:
        print(f'Smallest h with no counterexample: {smallest}')
    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1
    log('All required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

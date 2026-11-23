#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

ARTIFACT = Path('/workspace/Trial000036.py')
NOTES = Path('/workspace/notes.md')
REPORT1 = Path('/workspace/stack-boundary.md')
REPORT2 = Path('/workspace/stack-boundary-extended.md')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def all_stacks(max_height: int) -> List[Tuple[int, ...]]:
    out: List[Tuple[int, ...]] = []
    for h in range(max_height + 1):
        for bits in product((0, 1), repeat=h):
            out.append(tuple(bits))
    return out


def pop_trace(stack: Sequence[int], k: int) -> Tuple[str, ...]:
    s = list(stack)
    trace: List[str] = []
    for _ in range(k):
        if s:
            trace.append(str(s.pop()))
        else:
            trace.append('U')
    return tuple(trace)


def top_bits_with_padding(stack: Sequence[int], n: int) -> Tuple[int, ...]:
    s = list(stack)
    vals: List[int] = []
    for i in range(n):
        idx = len(s) - 1 - i
        vals.append(s[idx] if idx >= 0 else 0)
    return tuple(vals)


def witness_top1(stack: Sequence[int]) -> Tuple[int, int]:
    return (len(stack), top_bits_with_padding(stack, 1)[0])


def witness_top2(stack: Sequence[int]) -> Tuple[int, int, int]:
    t = top_bits_with_padding(stack, 2)
    return (len(stack), t[0], t[1])


def witness_top3(stack: Sequence[int]) -> Tuple[int, int, int, int]:
    t = top_bits_with_padding(stack, 3)
    return (len(stack), t[0], t[1], t[2])


@dataclass
class Counterexample:
    witness: Tuple[int, ...]
    a: Tuple[int, ...]
    b: Tuple[int, ...]
    k: int
    trace_a: Tuple[str, ...]
    trace_b: Tuple[str, ...]


@dataclass
class SearchResult:
    same_pairs: int
    tested: int
    per_length: Dict[int, Optional[Counterexample]]
    first_any: Optional[Counterexample]



def find_counterexamples(
    stacks: Sequence[Tuple[int, ...]],
    witness_fn: Callable[[Sequence[int]], Tuple[int, ...]],
    lengths: Iterable[int],
) -> SearchResult:
    lengths = list(lengths)
    per_length: Dict[int, Optional[Counterexample]] = {k: None for k in lengths}
    same_pairs = 0
    tested = 0
    first_any: Optional[Counterexample] = None
    by_w: Dict[Tuple[int, ...], List[Tuple[int, ...]]] = {}
    for s in stacks:
        by_w.setdefault(witness_fn(s), []).append(s)
    for w, group in by_w.items():
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                same_pairs += 1
                for k in lengths:
                    tested += 1
                    ta = pop_trace(a, k)
                    tb = pop_trace(b, k)
                    if ta != tb:
                        ce = Counterexample(w, a, b, k, ta, tb)
                        if per_length[k] is None:
                            per_length[k] = ce
                        if first_any is None or k < first_any.k:
                            first_any = ce
    return SearchResult(same_pairs=same_pairs, tested=tested, per_length=per_length, first_any=first_any)



def fmt_stack(stack: Sequence[int]) -> str:
    return '[' + ', '.join(str(x) for x in stack) + ']'



def fmt_ce(ce: Optional[Counterexample]) -> str:
    if ce is None:
        return 'none'
    return (
        f'witness={ce.witness}, a={fmt_stack(ce.a)}, b={fmt_stack(ce.b)}, '
        f'k={ce.k}, trace_a={ce.trace_a}, trace_b={ce.trace_b}'
    )



def generate_report1(top1: SearchResult, top2: SearchResult) -> str:
    honest = [0, 1]
    claimed = [1, 1]
    lines = [
        '# Stack boundary report',
        '',
        '## Honest boundary',
        'Start from the empty stack `[]`.',
        'Segment A pushes `0` and then `1`, so the honest boundary stack is `[0, 1]` with top bit `1` and buried bit `0`.',
        'If we now execute two POP operations, the exact honest trace is `(1, 0)`.',
        '',
        '## Claimed boundary',
        'For Segment B to justify two successive pops both returning `1`, the boundary would need to behave like the stack `[1, 1]`.',
        'That claimed stack gives POP trace `(1, 1)`.',
        'So the claim requires a different buried bit than the honest run provides.',
        '',
        '## Why height+top fails',
        'Checking only `top1 = (height, top)` misses the buried-bit mismatch.',
        'The honest stack `[0, 1]` and the claimed-style stack `[1, 1]` both have height `2` and top bit `1`, so `top1` cannot distinguish them at the boundary.',
        'But a second POP exposes the buried bit: the exact traces are `(1, 0)` versus `(1, 1)`.',
        f'Concrete oracle witness: {fmt_ce(top1.per_length[2] or top1.first_any)}.',
        '',
        '## One repair proposal',
        'A direct repair is to expose `top2 = (height, top two bits with padding)` before the universal challenge.',
        'For the boundary `[0, 1]`, this witness is `(2, 1, 0)`, which binds the buried bit as well as the top bit.',
        'This uses exactly 3 disclosed fields: one height value and two stack-bit values.',
        'To check one POP-only challenge of length 2, the verifier simulates two sequential POP steps and compares the returned trace to the witness-implied behavior.',
        'In this finite search, that repair succeeds for all stacks of height up to 4 against one- and two-POP continuations.',
        '',
        '## First unresolved question',
        'Does `top2` remain sufficient for longer POP-only continuations, or does a third exposed bit become necessary?',
        'The length-2 search says: no counterexample exists for `top2` under one- or two-POP continuations among all bit-stacks of height up to 4.',
        'The next step is to extend the exhaustive search to length 3 and test whether `top3` repairs the first new failure of `top2`.',
        '',
        '## Oracle summary',
        f'top1 same-witness pairs checked: {top1.same_pairs}; continuation tests: {top1.tested}.',
        f'top1 first counterexample within lengths <=2: {fmt_ce(top1.first_any)}.',
        f'top2 same-witness pairs checked: {top2.same_pairs}; continuation tests: {top2.tested}.',
        f'top2 first counterexample within lengths <=2: {fmt_ce(top2.first_any)}.',
    ]
    return '\n'.join(lines) + '\n'



def generate_report2(top2: SearchResult, top3: SearchResult, total_stacks: int) -> str:
    lines = [
        '# Stack boundary extended report',
        '',
        '## Question',
        'Continue the first unresolved question from `/workspace/stack-boundary.md`: find the first POP-only continuation length `k` at which exposing `top2 = (height, top two bits with padding)` fails, and test whether `top3 = (height, top three bits with padding)` repairs all counterexamples up to that same bound.',
        '',
        '## Method',
        f'Exhaustively enumerate all bit-stacks of heights 0 through 6. This yields {total_stacks} stacks total.',
        'For each witness scheme, compare every distinct pair of stacks with the same witness and compute the exact POP/underflow trace for continuations of lengths 1, 2, and 3. A counterexample is a same-witness pair whose traces differ for some tested length.',
        '',
        '## top2 results',
        f'Same-witness pairs checked: {top2.same_pairs}. Continuation tests: {top2.tested}.',
        f'Length 1 counterexample: {fmt_ce(top2.per_length[1])}.',
        f'Length 2 counterexample: {fmt_ce(top2.per_length[2])}.',
        f'Length 3 counterexample: {fmt_ce(top2.per_length[3])}.',
        'Confirmed again: `top2` has no distinguishing counterexample for POP-only lengths <= 2 in the searched range.' if top2.per_length[1] is None and top2.per_length[2] is None else 'Unexpectedly, `top2` already fails by length <= 2.',
        '',
        '## top3 results',
        f'Same-witness pairs checked: {top3.same_pairs}. Continuation tests: {top3.tested}.',
        f'Length 1 counterexample: {fmt_ce(top3.per_length[1])}.',
        f'Length 2 counterexample: {fmt_ce(top3.per_length[2])}.',
        f'Length 3 counterexample: {fmt_ce(top3.per_length[3])}.',
        'Yes: top3 removes all counterexamples for k<=3 in the searched range.' if top3.first_any is None else f'No: top3 still has a counterexample within k<=3: {fmt_ce(top3.first_any)}.',
        '',
        '## Earliest failure',
        f'The first top2 failure in the searched range occurs at k=3: {fmt_ce(top2.first_any)}' if top2.first_any is not None else 'No top2 failure exists for lengths <=3 in the searched range.',
    ]
    return '\n'.join(lines) + '\n'



def require_sections(text: str, sections: Sequence[str], failures: List[str], label: str) -> None:
    for sec in sections:
        if f'## {sec}' not in text:
            failures.append(f'{label} missing section: {sec}')



def main() -> int:
    NOTES.write_text('Starting Trial000036 stack-boundary reconstruction and verification.\n', encoding='utf-8')
    log('Generating independent oracle results.')

    stacks4 = all_stacks(4)
    stacks6 = all_stacks(6)
    top1 = find_counterexamples(stacks4, witness_top1, [1, 2])
    top2_small = find_counterexamples(stacks4, witness_top2, [1, 2])
    top2_big = find_counterexamples(stacks6, witness_top2, [1, 2, 3])
    top3_big = find_counterexamples(stacks6, witness_top3, [1, 2, 3])

    report1 = generate_report1(top1, top2_small)
    REPORT1.write_text(report1, encoding='utf-8')
    report2 = generate_report2(top2_big, top3_big, len(stacks6))
    REPORT2.write_text(report2, encoding='utf-8')
    log('Reports written.')

    failures: List[str] = []

    require_sections(report1, ['Honest boundary', 'Claimed boundary', 'Why height+top fails', 'One repair proposal', 'First unresolved question'], failures, 'stack-boundary.md')
    require_sections(report2, ['Question', 'Method', 'top2 results', 'top3 results', 'Earliest failure'], failures, 'stack-boundary-extended.md')

    honest_phrase = 'the honest boundary stack is `[0, 1]`'
    claimed_phrase = 'the stack `[1, 1]`'
    mismatch_phrase = 'Checking only `top1 = (height, top)` misses the buried-bit mismatch.'
    for phrase in [honest_phrase, claimed_phrase, mismatch_phrase]:
        if phrase not in report1:
            failures.append(f'stack-boundary.md missing required textual claim: {phrase}')

    if top1.first_any is None or top1.first_any.k > 2:
        failures.append('Oracle did not find the required top1 counterexample by length 2.')
    if top2_small.per_length[1] is not None or top2_small.per_length[2] is not None:
        failures.append('Oracle found an unexpected top2 counterexample at length <=2 for height <=4.')
    if not (top2_big.per_length[1] is None and top2_big.per_length[2] is None and top2_big.per_length[3] is not None and top2_big.first_any is not None and top2_big.first_any.k == 3):
        failures.append('Oracle did not verify that top2 first fails at length 3 in height <=6 search.')
    if top3_big.first_any is not None:
        failures.append('Oracle found an unexpected top3 counterexample at length <=3 for height <=6.')

    expected_strings = [
        'no counterexample exists for `top2` under one- or two-POP continuations',
        'Confirmed again: `top2` has no distinguishing counterexample for POP-only lengths <= 2 in the searched range.',
        'Yes: top3 removes all counterexamples for k<=3 in the searched range.',
        'The first top2 failure in the searched range occurs at k=3:',
    ]
    combined = report1 + '\n' + report2
    for s in expected_strings:
        if s not in combined:
            failures.append(f'Missing expected conclusion text: {s}')

    print('Stack boundary reconstruction experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report 1: {REPORT1}')
    print(f'Report 2: {REPORT2}')
    print(f'Stacks up to height 4: {len(stacks4)}')
    print(f'Stacks up to height 6: {len(stacks6)}')
    print(f'top1 earliest counterexample: {fmt_ce(top1.first_any)}')
    print(f'top2 (<=4, len<=2) earliest counterexample: {fmt_ce(top2_small.first_any)}')
    print(f'top2 (<=6, len<=3) earliest counterexample: {fmt_ce(top2_big.first_any)}')
    print(f'top3 (<=6, len<=3) earliest counterexample: {fmt_ce(top3_big.first_any)}')

    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1

    print('All checks passed.')
    log('All checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

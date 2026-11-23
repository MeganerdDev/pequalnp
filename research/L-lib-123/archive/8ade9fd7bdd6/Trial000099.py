#!/usr/bin/env python3
from __future__ import annotations

import itertools
import sys
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Sequence, Tuple

NOTES = Path('/workspace/notes.md')
REPORT = Path('/workspace/stack-boundary.md')


class CheckFailure(Exception):
    pass


Bit = int
Stack = Tuple[Bit, ...]  # bottom..top
Transcript = Tuple[Bit, ...]
Summary = Tuple[object, ...]


def append_notes(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as fh:
        fh.write(text.rstrip() + '\n')


def all_bit_stacks(depth: int) -> List[Stack]:
    return [tuple(bits) for bits in itertools.product((0, 1), repeat=depth)]


def pop_transcript(stack: Stack, count: int) -> Transcript:
    if len(stack) < count:
        raise ValueError('underflow')
    working = list(stack)
    out: List[Bit] = []
    for _ in range(count):
        out.append(working.pop())
    return tuple(out)


def summary_height_top(stack: Stack) -> Summary:
    return (len(stack), stack[-1] if stack else None)


def summary_height_top_second(stack: Stack) -> Summary:
    top = stack[-1] if len(stack) >= 1 else None
    second = stack[-2] if len(stack) >= 2 else None
    return (len(stack), top, second)


def collisions(depth: int, pops: int, summary_fn: Callable[[Stack], Summary]) -> Dict[Summary, List[Tuple[Stack, Transcript]]]:
    buckets: Dict[Summary, List[Tuple[Stack, Transcript]]] = {}
    for stack in all_bit_stacks(depth):
        s = summary_fn(stack)
        t = pop_transcript(stack, pops)
        buckets.setdefault(s, []).append((stack, t))
    bad: Dict[Summary, List[Tuple[Stack, Transcript]]] = {}
    for key, items in buckets.items():
        transcripts = {transcript for _, transcript in items}
        if len(transcripts) > 1:
            bad[key] = items
    return bad


def find_example(cmap: Dict[Summary, List[Tuple[Stack, Transcript]]]) -> Tuple[Summary, Tuple[Stack, Transcript], Tuple[Stack, Transcript]]:
    for key, items in cmap.items():
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if items[i][1] != items[j][1]:
                    return key, items[i], items[j]
    raise CheckFailure('expected a collision example, found none')


def write_report(depth2_ht_example, depth3_ht2_example) -> None:
    key2, ex2a, ex2b = depth2_ht_example
    key3, ex3a, ex3b = depth3_ht2_example
    report = f'''# Stack-boundary finite obstruction audit

This note continues from the first unresolved question in the previous stack-boundary report by brute-force enumeration.

## Model
- A stack is a bit-vector written bottom-to-top, e.g. `[0, 1]` means bottom `0`, top `1`.
- A `k`-pop transcript is the sequence of return values from `k` honest successive pops.
- Candidate summary schemes expose only some boundary information before challenge.

## Depth 2: one-pop-visible summary is too weak
Enumerate all depth-2 stacks and their honest two-pop transcripts.

- Summary `(height, top)` collision key: `{key2}`
- First stack/transcript: `{list(ex2a[0])} -> {ex2a[1]}`
- Second stack/transcript: `{list(ex2b[0])} -> {ex2b[1]}`

These stacks have the same exposed summary `(height, top)` but different full two-pop transcripts, so `(height, top)` cannot certify both pops.

## Depth 2: exposing both boundary cells removes collisions
Brute force over all depth-2 stacks shows summary `(height, top, second)` is injective on the full two-pop transcript relation. Since depth is exactly 2, this is equivalent to binding all boundary cells.

## Depth 3: exposing only the top two cells is still too weak
Enumerate all depth-3 stacks and their honest three-pop transcripts.

- Summary `(height, top, second)` collision key: `{key3}`
- First stack/transcript: `{list(ex3a[0])} -> {ex3a[1]}`
- Second stack/transcript: `{list(ex3b[0])} -> {ex3b[1]}`

These stacks agree on the top two exposed cells but differ on the buried third cell, and that buried bit reappears on the third challenged pop. Therefore binding only one existentially buried bit beyond the visible top does not scale to three consecutive pops.

## Exact finite obstruction for the next invariant
A natural strengthening works at challenge depth 2 only if it binds both cells of the depth-2 boundary exactly. At challenge depth 3, any summary exposing only the top two cells still admits collisions coming from the third buried bit.
'''
    REPORT.write_text(report, encoding='utf-8')


def main() -> int:
    append_notes('- Round 99: enumerating depth-2 and depth-3 stack summaries versus full pop transcripts.')

    depth2_ht = collisions(depth=2, pops=2, summary_fn=summary_height_top)
    if not depth2_ht:
        raise CheckFailure('depth-2 (height, top) should have a collision')

    depth2_hts = collisions(depth=2, pops=2, summary_fn=summary_height_top_second)
    if depth2_hts:
        raise CheckFailure(f'depth-2 (height, top, second) should remove collisions, found {depth2_hts}')

    depth3_ht2 = collisions(depth=3, pops=3, summary_fn=summary_height_top_second)
    if not depth3_ht2:
        raise CheckFailure('depth-3 (height, top, second) should still have a collision')

    ex2 = find_example(depth2_ht)
    ex3 = find_example(depth3_ht2)

    write_report(ex2, ex3)
    append_notes('- Verified: depth-2 needs both boundary cells for two pops; depth-3 top-two-cell summary still collides on third pop.')

    print('STACK BOUNDARY ENUMERATION RESULTS')
    print(f'depth2_stack_count={len(all_bit_stacks(2))}')
    print(f'depth3_stack_count={len(all_bit_stacks(3))}')
    print(f'depth2_height_top_collision_count={len(depth2_ht)}')
    print(f'depth2_height_top_second_collision_count={len(depth2_hts)}')
    print(f'depth3_height_top_second_collision_count={len(depth3_ht2)}')
    print(f'depth2_example_summary={ex2[0]}')
    print(f'depth2_example_a_stack={list(ex2[1][0])} transcript={ex2[1][1]}')
    print(f'depth2_example_b_stack={list(ex2[2][0])} transcript={ex2[2][1]}')
    print(f'depth3_example_summary={ex3[0]}')
    print(f'depth3_example_a_stack={list(ex3[1][0])} transcript={ex3[1][1]}')
    print(f'depth3_example_b_stack={list(ex3[2][0])} transcript={ex3[2][1]}')
    print(f'report_written={REPORT}')
    print('ALL CHECKS PASSED')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except CheckFailure as exc:
        print(f'CHECK FAILURE: {exc}', file=sys.stderr)
        raise SystemExit(1)

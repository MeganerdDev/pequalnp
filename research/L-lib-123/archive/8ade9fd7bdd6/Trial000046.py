#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import itertools
import re
import sys

ROOT = Path('/workspace')
ARTIFACT = ROOT / 'Trial000046.py'
REPORT = ROOT / 'stack-boundary.md'
NOTES = ROOT / 'notes.md'


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def push(stack: list[int], bit: int) -> None:
    stack.insert(0, bit)


def pop(stack: list[int]):
    if not stack:
        return None
    return stack.pop(0)


def simulate_pushes(bits: list[int]) -> list[int]:
    stack: list[int] = []
    for b in bits:
        push(stack, b)
    return stack


def pop_trace(stack: list[int], n: int) -> tuple:
    s = list(stack)
    out = []
    for _ in range(n):
        out.append(pop(s))
    return tuple(out)


@dataclass(frozen=True)
class Counterexample:
    a: tuple[int, ...]
    b: tuple[int, ...]
    summary: tuple[int, int | None]
    trace_a: tuple
    trace_b: tuple


def enumerate_stacks(max_height: int) -> list[tuple[int, ...]]:
    stacks = [tuple()]
    for h in range(1, max_height + 1):
        stacks.extend(itertools.product((0, 1), repeat=h))
    return stacks


def summary_height_top(stack: tuple[int, ...]) -> tuple[int, int | None]:
    return (len(stack), stack[0] if stack else None)


def find_same_height_top_different_two_pop(stacks: list[tuple[int, ...]]) -> Counterexample | None:
    by_summary: dict[tuple[int, int | None], list[tuple[int, ...]]] = {}
    for s in stacks:
        by_summary.setdefault(summary_height_top(s), []).append(s)
    for summ, group in by_summary.items():
        for i, a in enumerate(group):
            ta = pop_trace(list(a), 2)
            for b in group[i + 1:]:
                tb = pop_trace(list(b), 2)
                if ta != tb:
                    return Counterexample(a=a, b=b, summary=summ, trace_a=ta, trace_b=tb)
    return None


def build_report(boundary_stack: list[int], honest_trace: tuple, claimed_trace: tuple, cex: Counterexample) -> str:
    return f"""# Stack boundary note

We use the **top-first** convention for stacks: the first list entry is the current top.
Start from the empty stack `[]`.

## Toy example
Segment A is honest and pushes `0`, then `1`.
Under the top-first convention this gives the boundary stack `{boundary_stack}`.
Concretely: after push `0` the stack is `[0]`, and after push `1` the stack is `[1, 0]`.

Now suppose Segment B dishonestly claims that two successive pops both return `1`.
Its claimed two-pop trace is `{claimed_trace}`.
The honest two-pop trace from the actual boundary stack is `{honest_trace}`.
So the first pop agrees, but the second pop exposes the buried-bit error: the true second return is `0`, not `1`.

## Why checking only height and top can miss the error
Checking only the pair `(height, top)` is too weak in larger examples.
Two different stacks can share the same `(height, top)` summary while differing below the top cell, and then a two-pop challenge can distinguish them.

One explicit counterexample is:
- stack A = `{list(cex.a)}`
- stack B = `{list(cex.b)}`
- both have summary `(height, top) = {cex.summary}`
- two-pop trace of stack A = `{cex.trace_a}`
- two-pop trace of stack B = `{cex.trace_b}`

Thus height-and-top-only checking can accept both boundary descriptions even though they imply different answers to the second pop.
That is exactly the kind of buried-bit problem seen in the toy story: the top bit matches, but the next bit down matters on the second pop.

## One first-existential-block binding scheme
A simple proposal is: in the first existential block, provide
1. the boundary height, and
2. the top two boundary bits.

Then the universal challenge chooses whether to check:
- a one-pop continuation, or
- a two-pop continuation.

For this specific two-pop toy setting, the guessed data are:
- `1` height value, and
- `2` guessed boundary bits,
so the scheme binds **2 boundary bits** beyond the height field.

To verify one challenge sequentially:
1. read the claimed height and top two bits,
2. simulate Segment A up to the boundary,
3. compare the simulated boundary height with the claimed height,
4. compare the simulated top bit with the claimed top bit,
5. if the challenge is for two pops, also compare the simulated second bit / second pop result with the claimed second bit,
6. simulate the requested one-pop or two-pop continuation and compare with Segment B's claimed answers.

So this proposal uses **6 sequential verification steps** as listed above for one challenged branch.
For the toy example itself, it suffices: the second committed boundary bit distinguishes honest `[1, 0]` from the dishonest story that would need second pop `1`.

## Exact limitation of the proposal
This proposal only binds enough information for challenges that inspect at most two pops across the boundary.
If later continuations may perform three or more pops before any compensating push, then committing only the top two bits is not enough: two stacks can agree on height and top two bits yet differ on the third pop.
So the scheme does **not** cover all possible longer continuations; it fails exactly when the universal challenge can force inspection deeper than the committed prefix.
"""


def validate_report_text(report: str, cex: Counterexample) -> list[str]:
    failures: list[str] = []
    required_snippets = [
        'boundary stack `[1, 0]`',
        'claimed two-pop trace is `(1, 1)`',
        'honest two-pop trace from the actual boundary stack is `(1, 0)`',
        'binds **2 boundary bits** beyond the height field',
        'uses **6 sequential verification steps**',
        'three or more pops',
    ]
    for snippet in required_snippets:
        if snippet not in report:
            failures.append(f'missing report snippet: {snippet}')
    if str(cex.summary) not in report:
        failures.append('counterexample summary missing from report')
    if str(cex.trace_a) not in report or str(cex.trace_b) not in report:
        failures.append('counterexample traces missing from report')
    numbered = re.findall(r'^([1-6])\. ', report, flags=re.M)
    if len(numbered) < 6:
        failures.append('expected six numbered sequential verification steps')
    return failures


def main() -> int:
    NOTES.write_text('Trial000046 start\n', encoding='utf-8')
    log('Inspecting exact stack definition by direct simulation.')

    boundary_stack = simulate_pushes([0, 1])
    honest_trace = pop_trace(boundary_stack, 2)
    claimed_trace = (1, 1)

    stacks = enumerate_stacks(5)
    cex = find_same_height_top_different_two_pop(stacks)
    if cex is None:
        print('CHECK FAILURES: no same-(height, top) counterexample found')
        log('FAIL: no same-(height, top) counterexample found')
        return 1

    report = build_report(boundary_stack, honest_trace, claimed_trace, cex)
    REPORT.write_text(report, encoding='utf-8')
    log('Wrote stack-boundary.md and now validating concrete claims.')

    failures: list[str] = []
    if boundary_stack != [1, 0]:
        failures.append(f'expected boundary stack [1, 0], got {boundary_stack}')
    if honest_trace != (1, 0):
        failures.append(f'expected honest trace (1, 0), got {honest_trace}')
    if claimed_trace != (1, 1):
        failures.append(f'expected claimed trace (1, 1), got {claimed_trace}')
    if cex.summary != summary_height_top(cex.a) or cex.summary != summary_height_top(cex.b):
        failures.append('counterexample summary inconsistent with stacks')
    if cex.trace_a == cex.trace_b:
        failures.append('counterexample does not actually differ on two-pop traces')
    failures.extend(validate_report_text(report, cex))

    print('Stack boundary experiment')
    print(f'Boundary stack after pushes 0 then 1: {boundary_stack}')
    print(f'Honest two-pop trace: {honest_trace}')
    print(f'Dishonest claimed two-pop trace: {claimed_trace}')
    print('Counterexample to checking only (height, top):')
    print(f'  stack A = {list(cex.a)}')
    print(f'  stack B = {list(cex.b)}')
    print(f'  shared summary = {cex.summary}')
    print(f'  two-pop trace A = {cex.trace_a}')
    print(f'  two-pop trace B = {cex.trace_b}')
    print(f'Report written to: {REPORT}')

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

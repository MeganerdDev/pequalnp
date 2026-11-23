#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

NOTES = Path('/workspace/notes.md')
REPORT = Path('/workspace/stack-boundary.md')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


class StackError(Exception):
    pass


@dataclass(frozen=True)
class PopTrace:
    outputs: tuple[int, ...]
    final_stack: tuple[int, ...]


def push(stack: tuple[int, ...], bit: int) -> tuple[int, ...]:
    if bit not in (0, 1):
        raise ValueError(f'bit must be 0 or 1, got {bit!r}')
    return stack + (bit,)


def pop(stack: tuple[int, ...]) -> tuple[int, tuple[int, ...]]:
    if not stack:
        raise StackError('pop from empty stack')
    return stack[-1], stack[:-1]


def run_segment_a() -> tuple[int, ...]:
    stack: tuple[int, ...] = ()
    stack = push(stack, 0)
    stack = push(stack, 1)
    return stack


def pop_twice(stack: tuple[int, ...]) -> PopTrace:
    out1, stack1 = pop(stack)
    out2, stack2 = pop(stack1)
    return PopTrace((out1, out2), stack2)


def summary_height_top(stack: tuple[int, ...]) -> tuple[int, int | None]:
    return (len(stack), stack[-1] if stack else None)


def summary_with_buried_bit(stack: tuple[int, ...]) -> tuple[int, int | None, int | None]:
    buried = stack[-2] if len(stack) >= 2 else None
    return (len(stack), stack[-1] if stack else None, buried)


def verifier_steps_for_one_challenge() -> int:
    # Toy challenge: verify that the guessed buried bit and observed top bit
    # produce the claimed two-pop transcript for Segment B.
    # Sequential checks counted explicitly:
    # 1. read top bit
    # 2. compare first claimed pop to top
    # 3. read guessed buried bit
    # 4. compare second claimed pop to guessed buried bit
    return 4


def build_report(honest: tuple[int, ...], counterfeit: tuple[int, ...], honest_trace: PopTrace, counterfeit_trace: PopTrace) -> str:
    h_ht = summary_height_top(honest)
    c_ht = summary_height_top(counterfeit)
    h_strong = summary_with_buried_bit(honest)
    c_strong = summary_with_buried_bit(counterfeit)
    guessed_bits = 1
    steps = verifier_steps_for_one_challenge()
    lines = [
        '# Stack boundary toy experiment',
        '',
        'Convention: stack top is at the end of the list/tuple.',
        '',
        '## Honest execution',
        '',
        f'- Start from empty stack: `[]`.',
        f'- Segment A = push 0, push 1, so the honest boundary stack is `{list(honest)}`.',
        f'- Honest summary `(height, top)` is `{h_ht}`.',
        f'- Stronger summary `(height, top, buried_bit)` is `{h_strong}`.',
        f'- Running Segment B honestly from `{list(honest)}` gives pop trace `{list(honest_trace.outputs)}` and final stack `{list(honest_trace.final_stack)}`.',
        '',
        '## Claimed Segment B and why the shallow summary fails',
        '',
        '- Claimed Segment B says `pop -> 1, pop -> 1`.',
        f'- But from the honest boundary stack `{list(honest)}`, the actual two pops are `{list(honest_trace.outputs)}`, so the second claimed `1` is false.',
        f'- A counterfeit boundary stack `{list(counterfeit)}` has the same `(height, top)` summary `{c_ht}` as the honest boundary stack.',
        f'- Its stronger summary is `{c_strong}`, which differs from the honest stronger summary `{h_strong}` only in the buried bit.',
        f'- Running two pops from the counterfeit stack gives `{list(counterfeit_trace.outputs)}`.',
        '- Therefore `(height, top)` alone cannot distinguish the honest boundary `[0, 1]` from the counterfeit boundary `[1, 1]`, even though one yields pops `[1, 0]` and the other yields `[1, 1]`.',
        '',
        '## One proposed first existential block',
        '',
        '- Proposal: in the first existential block, the prover explicitly guesses the buried bit just under the top at the A/B boundary.',
        '- On this toy instance that is exactly **1 guessed bit**.',
        '- After that, a universal challenge may ask to check Segment B locally: compare the first claimed pop to the top bit and the second claimed pop to the guessed buried bit.',
        f'- For this toy check, that needs exactly **{steps} sequential verifier steps** under the explicit counting used by the script.',
        '- With the honest boundary `[0, 1]`, the only correct buried-bit guess is `0`, so the claimed trace `[1, 1]` is rejected on the second comparison.',
        '- With the counterfeit boundary `[1, 1]`, the guessed buried bit `1` makes the claimed trace `[1, 1]` pass; this shows the stronger summary really does bind the missing buried information on the toy instance.',
        '',
        '## Where the proposal fails or remains unresolved',
        '',
        '- It succeeds on this toy instance because there is only one hidden bit below the top that matters for two pops.',
        '- The unresolved point is scaling: for longer computations or deeper stacks, binding enough buried information before a later universal challenge may require many guessed bits, and it is not shown here how to do that without exceeding the intended three-round structure.',
        '- So the toy repair works locally, but this experiment does **not** establish a scalable three-round method.',
        '',
        '## Bottom line',
        '',
        '- Honest boundary after Segment A: `[0, 1]`.',
        '- Actual pops from that boundary: `[1, 0]`.',
        '- Claimed pops: `[1, 1]`.',
        '- Shallow summary collision: both honest `[0, 1]` and counterfeit `[1, 1]` have `(height, top) = (2, 1)`.',
        '- Stronger summary distinguishes them by the buried bit.',
    ]
    return '\n'.join(lines) + '\n'


def main() -> int:
    NOTES.write_text('Trial000018 started.\n', encoding='utf-8')
    log('Simulating Segment A and Segment B on a toy stack with top at end.')

    honest = run_segment_a()
    counterfeit = (1, 1)
    honest_trace = pop_twice(honest)
    counterfeit_trace = pop_twice(counterfeit)

    print('Measured results:')
    print(f'  honest boundary stack: {list(honest)}')
    print(f'  counterfeit boundary stack: {list(counterfeit)}')
    print(f'  honest (height, top): {summary_height_top(honest)}')
    print(f'  counterfeit (height, top): {summary_height_top(counterfeit)}')
    print(f'  honest stronger summary: {summary_with_buried_bit(honest)}')
    print(f'  counterfeit stronger summary: {summary_with_buried_bit(counterfeit)}')
    print(f'  honest two-pop trace: {list(honest_trace.outputs)}')
    print(f'  counterfeit two-pop trace: {list(counterfeit_trace.outputs)}')
    print(f'  guessed bits in proposed existential block: 1')
    print(f'  sequential verifier steps for one toy challenge: {verifier_steps_for_one_challenge()}')

    failures: list[str] = []
    if honest != (0, 1):
        failures.append(f'Expected honest boundary (0, 1), got {honest!r}')
    if honest_trace.outputs != (1, 0):
        failures.append(f'Expected honest pop trace (1, 0), got {honest_trace.outputs!r}')
    if summary_height_top(honest) != (2, 1):
        failures.append('Honest shallow summary should be (2, 1).')
    if summary_height_top(counterfeit) != (2, 1):
        failures.append('Counterfeit shallow summary should be (2, 1).')
    if summary_with_buried_bit(honest) == summary_with_buried_bit(counterfeit):
        failures.append('Stronger summaries should differ on the buried bit.')
    if counterfeit_trace.outputs != (1, 1):
        failures.append(f'Expected counterfeit pop trace (1, 1), got {counterfeit_trace.outputs!r}')

    report = build_report(honest, counterfeit, honest_trace, counterfeit_trace)
    REPORT.write_text(report, encoding='utf-8')
    log('Wrote stack-boundary.md with honest/counterfeit comparison and scaling caveat.')

    report_text = REPORT.read_text(encoding='utf-8')
    required_phrases = [
        'Honest boundary after Segment A',
        'Actual pops from that boundary',
        'Claimed pops',
        '1 guessed bit',
        'sequential verifier steps',
        'three-round structure',
        'unresolved point is scaling',
    ]
    for phrase in required_phrases:
        if phrase not in report_text:
            failures.append(f'Markdown report missing required phrase: {phrase!r}')

    if failures:
        print('\nFAILURES:')
        for item in failures:
            print(f'  - {item}')
            log(f'FAIL: {item}')
        return 1

    log('All checks passed.')
    print('\nAll checks passed.')
    print(f'Report written to: {REPORT}')
    return 0


if __name__ == '__main__':
    sys.exit(main())

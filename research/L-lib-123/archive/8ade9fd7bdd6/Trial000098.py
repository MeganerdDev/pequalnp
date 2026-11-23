#!/usr/bin/env python3
"""Self-contained test for the stack-boundary obstruction example.

This script independently models a deterministic bit stack, checks the exact
example from the assignment, emits a short report file in /workspace, and exits
nonzero if any required property fails.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

NOTES = Path('/workspace/notes.md')
REPORT = Path('/workspace/stack-boundary.md')


def append_notes(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(text)
        if not text.endswith('\n'):
            f.write('\n')


@dataclass
class BitStack:
    data: list[int]

    def __init__(self) -> None:
        self.data = []

    def push(self, bit: int) -> None:
        if bit not in (0, 1):
            raise ValueError(f'bit must be 0 or 1, got {bit!r}')
        self.data.append(bit)

    def pop(self) -> int:
        if not self.data:
            raise IndexError('pop from empty stack')
        return self.data.pop()

    def snapshot(self) -> list[int]:
        return list(self.data)

    def height(self) -> int:
        return len(self.data)

    def top(self):
        return self.data[-1] if self.data else None


class CheckFailure(AssertionError):
    pass


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailure(msg)


def summarize_boundary(stack: BitStack) -> tuple[int, int | None]:
    return (stack.height(), stack.top())


def main() -> int:
    append_notes('# Round 98\n')
    append_notes('- Building executable stack-boundary audit as Trial000098.py.')

    # Honest Segment A and Segment B.
    stack = BitStack()
    require(stack.snapshot() == [], 'stack should start empty')
    stack.push(0)
    stack.push(1)
    boundary_stack = stack.snapshot()
    boundary_summary = summarize_boundary(stack)

    honest_first = stack.pop()
    state_after_first_pop = stack.snapshot()
    honest_second = stack.pop()
    final_stack = stack.snapshot()
    final_summary = summarize_boundary(stack)
    honest_transcript = (honest_first, honest_second)
    forged_transcript = (1, 1)

    # Required exact facts.
    require(boundary_stack == [0, 1], f'boundary stack mismatch: {boundary_stack!r}')
    require(boundary_summary == (2, 1), f'boundary summary mismatch: {boundary_summary!r}')
    require(honest_transcript == (1, 0), f'honest pop transcript mismatch: {honest_transcript!r}')
    require(honest_first == forged_transcript[0], 'forged first pop should match honest first pop')
    require(honest_second != forged_transcript[1], 'forged second pop should disagree with honest second pop')
    require(state_after_first_pop == [0], f'residual stack after one honest pop should be [0], got {state_after_first_pop!r}')
    require(final_stack == [], f'final stack should be empty, got {final_stack!r}')
    require(final_summary == (0, None), f'final summary mismatch: {final_summary!r}')

    # Concrete demonstration of the too-weak summary issue.
    # If a verifier only checks boundary summaries before Segment B and after Segment B,
    # then both the honest and forged two-pop claims are compatible with the same summaries:
    # start (height 2, top 1), end (height 0, top None). The buried bit is not represented.
    observed_before = boundary_summary
    observed_after = final_summary
    honest_observation = (observed_before, observed_after)
    forged_observation = (observed_before, observed_after)
    require(honest_observation == forged_observation,
            'height/top-only observations should coincide for honest and forged stories here')

    witness_bits = 1  # one buried bit, namely the lower cell 0 beneath top 1
    seq_steps_one_challenge = 4  # reveal witness bit, check boundary top, check first pop, check residual/top for second pop

    report = f"""# Stack boundary micro-analysis

## Example setup
Start from the empty stack `[]`.

Segment A pushes `0`, then pushes `1`.
So the honest boundary stack is `{boundary_stack}` with top `{boundary_summary[1]}` and height `{boundary_summary[0]}`.

## Honest versus claimed Segment B
Segment B claims that two successive pops both return `1`.

Honest execution on boundary stack `{boundary_stack}`:
1. First pop returns `{honest_first}` and leaves residual stack `{state_after_first_pop}`.
2. Second pop therefore must return `{honest_second}` and leaves final stack `{final_stack}`.

Claimed execution:
1. First claimed pop returns `1`.
2. Second claimed pop also returns `1`.

The first claimed pop is consistent with the honest stack because the top at the boundary is `1`.
The second claimed pop is inconsistent: after one honest pop the residual stack is `{state_after_first_pop}`, whose top is `0`, so the second honest pop must be `0`, not `1`.

## Why checking only boundary height and top misses the buried-bit error
If a verifier records only `(height, top)` at the start and end of Segment B, then it sees:
- before Segment B: `{observed_before}`
- after two pops: `{observed_after}`

Those summaries are identical whether the internal pop transcript is the honest `{honest_transcript}` or the forged `{forged_transcript}`. Once the stack is emptied, the buried bit is no longer visible in the final summary. Therefore a boundary check that tracks only height and current top is too weak: it cannot certify the second pop value.

## One first-existential binding scheme for the buried bit
A minimal proposal is for the first existential block to bind the one buried bit present at the boundary: namely the lower cell `0` under the visible top `1`.

- Witness bits required in this example: `{witness_bits}` bit.
- Proposed witness: the prover commits to the buried bit value before any universal challenge.
- Sequential verification steps for one challenged pop sequence:
  1. Read the committed buried bit witness.
  2. Check the visible boundary summary `(height=2, top=1)`.
  3. Verify the first challenged pop is `1`, matching the visible top.
  4. Update to the residual stack using the witness; then verify the second challenged pop equals the committed buried bit, here `0`.

On this concrete forged claim `(1,1)`, the scheme fails exactly at step 4: the committed buried bit is `0`, so the claimed second pop `1` is rejected.

## Executable check results
- boundary stack: {boundary_stack}
- boundary summary (height, top): {boundary_summary}
- honest two-pop transcript: {honest_transcript}
- forged two-pop transcript: {forged_transcript}
- final summary after two honest pops: {final_summary}
- height/top-only observation collision: {honest_observation == forged_observation}
"""
    REPORT.write_text(report, encoding='utf-8')
    append_notes('- Wrote stack-boundary.md and verified the boundary-obstruction facts by execution.')

    print('STACK BOUNDARY TEST RESULTS')
    print(f'boundary_stack={boundary_stack}')
    print(f'boundary_summary(height, top)={boundary_summary}')
    print(f'honest_transcript={honest_transcript}')
    print(f'forged_transcript={forged_transcript}')
    print(f'state_after_first_pop={state_after_first_pop}')
    print(f'final_summary={final_summary}')
    print(f'height_top_only_collision={honest_observation == forged_observation}')
    print(f'witness_bits_example={witness_bits}')
    print(f'seq_steps_one_challenge={seq_steps_one_challenge}')
    print(f'report_written={REPORT}')
    print('ALL CHECKS PASSED')
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except CheckFailure as exc:
        print(f'CHECK FAILURE: {exc}', file=sys.stderr)
        raise SystemExit(1)

#!/usr/bin/env python3
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import itertools
import sys

ARTIFACT_MD = Path('/workspace/stack-boundary.md')
NOTES_MD = Path('/workspace/notes.md')


def append_notes(text: str) -> None:
    with NOTES_MD.open('a', encoding='utf-8') as f:
        f.write(text)
        if not text.endswith('\n'):
            f.write('\n')


def pop_trace(num_pops: int, stack: list[int]) -> list[int | None]:
    s = list(stack)
    out: list[int | None] = []
    for _ in range(num_pops):
        if s:
            out.append(s.pop(0))
        else:
            out.append(None)
    return out


def summary_height_top(stack: list[int]) -> tuple[int, int | None]:
    return (len(stack), stack[0] if stack else None)


@dataclass(frozen=True)
class SchemeReport:
    witness_bits: int
    sequential_steps_for_one_challenge: int
    description: str


def write_report() -> SchemeReport:
    scheme = SchemeReport(
        witness_bits=2,
        sequential_steps_for_one_challenge=2,
        description=(
            'First existential block guesses both boundary bits (x_top, x_next). '
            'Then the verifier chooses i in {0,1}. To check challenge i, the verifier '
            'simulates exactly i+1 pops from the guessed boundary and compares the claimed '
            'ith pop result with the simulation.'
        ),
    )
    report = f"""# Stack-boundary toy counterexample

We start from the empty stack `[]`.

## Honest Segment A

Segment A pushes `0`, then pushes `1`.
With the convention that the **leftmost element is the top of the stack**, the boundary stack is:

| Step | Operation | Stack |
|---|---|---|
| 0 | start | `[]` |
| 1 | push 0 | `[0]` |
| 2 | push 1 | `[1,0]` |

So the honest boundary stack is **`[1,0]`**.
It has height `2`, top symbol `1`, and two-pop transcript `{pop_trace(2, [1,0])}`.

## Fraudulent Segment B claim

Segment B claims that two successive pops both return `1`.
That means its claimed two-pop transcript is:

| Pop number | Claimed return |
|---|---|
| 1 | `1` |
| 2 | `1` |

A stack consistent with that claimed transcript is **`[1,1]`**, whose two-pop transcript is `{pop_trace(2, [1,1])}`.

## Why checking only height and top misses the error

A checker that inspects only the boundary summary `(height, top)` sees:

| Stack | Height | Top | Two-pop transcript |
|---|---:|---:|---|
| honest `[1,0]` | `2` | `1` | `{pop_trace(2, [1,0])}` |
| forged `[1,1]` | `2` | `1` | `{pop_trace(2, [1,1])}` |

Both stacks have the same summary `(2,1)`, so any checker restricted to height and top **accepts both**.
But the buried bit differs: the next symbol is `0` in the honest stack and `1` in the forged stack. That hidden bit is exactly what changes the second pop.

## One concrete first-existential-block scheme

A natural repair is to let the first existential block guess **both boundary bits** `(x_top, x_next)` before the universal challenge.
Then the verifier chooses `i ∈ {{0,1}}` and asks for the `i`th pop result.
The verifier simulates exactly `i+1` pops from the guessed boundary and checks that the returned symbol matches the simulation.

- Witness bits guessed in the first existential block: **{scheme.witness_bits}**
- Sequential verification steps for one challenge: **{scheme.sequential_steps_for_one_challenge}** pop-simulation steps in the worst case
  - if `i = 0`: 1 simulated pop
  - if `i = 1`: 2 simulated pops

Because the witness fixes both bits, the verifier can answer both possible challenges consistently from one committed boundary.
On this 2-bit toy model, that eliminates the collision between `[1,0]` and `[1,1]`.

## Limits / possible failure relative to the intended FP3 structure

This proposal works only because the boundary here has exactly two relevant bits.
For a longer real stack boundary, binding all buried symbols may require many guessed bits, potentially destroying any hoped-for speedup.
So the unresolved question is not whether the two-bit repair works here—it does—but whether an FP3 protocol can bind enough of a long deterministic computation **without** essentially guessing the whole relevant boundary.
"""
    ARTIFACT_MD.write_text(report, encoding='utf-8')
    return scheme


def main() -> int:
    append_notes('Round 71: generating Trial000071.py and stack-boundary.md; verifying the exact toy counterexample by brute force.')
    scheme = write_report()

    stacks = [list(bits) for bits in itertools.product([0, 1], repeat=2)]
    transcripts = {tuple(s): tuple(pop_trace(2, s)) for s in stacks}
    groups: dict[tuple[int, int | None], list[list[int]]] = {}
    for s in stacks:
        groups.setdefault(summary_height_top(s), []).append(s)

    append_notes(f'Enumerated stacks: {stacks}')
    append_notes(f'Groups by (height, top): {groups}')
    append_notes(f'Two-pop transcripts: {transcripts}')

    failures: list[str] = []

    collision_group = groups.get((2, 1), [])
    if [1, 0] not in collision_group or [1, 1] not in collision_group:
        failures.append('Expected collision group (2,1) to contain both [1,0] and [1,1].')

    if summary_height_top([1, 0]) != summary_height_top([1, 1]):
        failures.append('Expected [1,0] and [1,1] to have the same (height, top) summary.')

    if pop_trace(2, [1, 0]) == pop_trace(2, [1, 1]):
        failures.append('Expected [1,0] and [1,1] to have different two-pop transcripts.')

    any_collision = any(len(v) > 1 for v in groups.values())
    if not any_collision:
        failures.append('No collision found for summary (height, top), contradicting the report.')

    encoding = {(len(s), s[0], s[1]): tuple(s) for s in stacks}
    if len(encoding) != len(stacks):
        failures.append('Augmenting with both bits was not injective on 2-bit stacks.')

    full_guess_transcripts = {tuple(s): tuple(pop_trace(2, s)) for s in stacks}
    if len(set(full_guess_transcripts.values())) != len(stacks):
        failures.append('Even full 2-bit guessing did not distinguish all 2-bit stacks under popTrace 2.')

    print('Wrote report:', ARTIFACT_MD)
    print('Witness bits in guessed-two-bits scheme:', scheme.witness_bits)
    print('Worst-case sequential verification steps for one challenge:', scheme.sequential_steps_for_one_challenge)
    print('\nStacks grouped by (height, top):')
    for key in sorted(groups):
        print(f'  {key}: {groups[key]}')
    print('\nTwo-pop transcripts:')
    for s in stacks:
        print(f'  {s} -> {pop_trace(2, s)}')
    print('\nSpecific comparison:')
    print('  summary([1,0]) =', summary_height_top([1, 0]))
    print('  summary([1,1]) =', summary_height_top([1, 1]))
    print('  popTrace(2, [1,0]) =', pop_trace(2, [1, 0]))
    print('  popTrace(2, [1,1]) =', pop_trace(2, [1, 1]))
    print('  injective encoding with both guessed bits:', len(encoding) == len(stacks))

    if failures:
        print('\nFAILURES DETECTED:')
        for msg in failures:
            print(' -', msg)
        return 1

    print('\nAll required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

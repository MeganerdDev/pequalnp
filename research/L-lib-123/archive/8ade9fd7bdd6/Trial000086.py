#!/usr/bin/env python3
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


@dataclass(frozen=True)
class Push:
    bit: int


@dataclass(frozen=True)
class PopClaim:
    claimed: int


Stack = list[int]


def push(stack: Stack, bit: int) -> Stack:
    assert bit in (0, 1)
    return [bit] + list(stack)


def pop_semantic(stack: Stack) -> tuple[int | None, Stack]:
    if not stack:
        return None, []
    return stack[0], stack[1:]


def run_segment_a(start: Stack) -> Stack:
    s = list(start)
    s = push(s, 0)
    s = push(s, 1)
    return s


def run_claimed_b(boundary: Stack, claims: list[PopClaim]) -> list[int | None]:
    # Claimed outputs only; ignores semantics, representing the false transcript.
    return [c.claimed for c in claims]


def run_semantic_b(boundary: Stack, steps: list[PopClaim]) -> tuple[list[int | None], Stack]:
    s = list(boundary)
    outs: list[int | None] = []
    for _ in steps:
        out, s = pop_semantic(s)
        outs.append(out)
    return outs, s


def bits_required_full_boundary(h: int) -> int:
    if h < 0:
        raise ValueError('height must be nonnegative')
    return h


def sequential_steps_one_challenge() -> int:
    # Minimal explicit proposal: verifier chooses one challenged position i in [0,h-1];
    # prover reveals that bit and the verifier compares it to the earlier existential witness.
    # We count only the online sequential checking steps after the challenge is chosen.
    return 2  # read challenged bit, compare/equality-check


def make_report(honest_boundary: Stack, forged_boundary: Stack, claims: list[int], honest_pops: list[int | None], forged_semantic_pops: list[int | None]) -> str:
    h = len(honest_boundary)
    witness_bits = bits_required_full_boundary(h)
    challenge_steps = sequential_steps_one_challenge()
    return f"""# Stack boundary counterexample

Start from the empty stack `[]`, with the top shown first.

- Segment A: `push 0`, then `push 1`.
- Segment B claims: `pop -> 1`, then `pop -> 1`.

## Honest execution of A

From `[]`:

1. After `push 0`: `[0]`
2. After `push 1`: `{honest_boundary}`

So the honest boundary stack after A is `{honest_boundary}`.
Its height is `{len(honest_boundary)}` and its top bit is `{honest_boundary[0]}`.

## Forged boundary stack used by the false B-claim

Take the alternative boundary stack `{forged_boundary}`.
It has the same height `{len(forged_boundary)}` and the same top bit `{forged_boundary[0]}` as the honest boundary stack,
but its buried bit differs: honest buried bit = `{honest_boundary[1]}`, forged buried bit = `{forged_boundary[1]}`.

This is the concrete buried-bit error: checking only height and top cannot distinguish
`{honest_boundary}` from `{forged_boundary}`.

## What B outputs

The claimed B transcript says the two pops return `{claims}`.

- If one follows the false transcript from the forged boundary `{forged_boundary}`, the two pop outputs are `{forged_semantic_pops}`.
- Under the honest semantics from the real boundary `{honest_boundary}`, the two pop outputs are `{honest_pops}`.

Therefore a boundary check that looks only at height and top misses the error in the second bit.
The first pop is compatible with both boundaries, but the second pop exposes the mismatch.

## One explicit first-existential binding proposal

Proposal: in the first existential block, send the full boundary stack bits explicitly.
For a boundary stack of height `h`, this witness uses exactly `h` bits for the stack contents
(or `h + O(log h)` bits if one also transmits the height separately; here the height is already being tracked,
so the content-only cost is `{witness_bits}` bits when `h = {h}`).

Then the universal challenge chooses one position `i` with `0 <= i < h`.
To check one challenge sequentially:

1. read the challenged position `i`;
2. read/recover the claimed bit at position `i` from the witness;
3. compare it with the bit demanded by the challenged local simulation.

If the witness is stored as raw boundary bits, the online check for one chosen position is `{challenge_steps}` core steps
(read the challenged bit and compare), plus any indexing/addressing overhead if the representation is not random-access.

## Where this proposal fails

This proposal binds the buried bit honestly, but it does so by sending the entire boundary stack.
That costs `h` witness bits, which scales with the whole boundary size rather than compressing it.
So it does not by itself deliver the kind of sublinear or exponent-saving summary one would need for the larger FP3 plan.
The precise failure point is compression: the proposal gives correctness against a single buried-bit challenge,
but no nontrivial succinctness.
"""


def main() -> int:
    append_notes('Trial000086: constructing stack-boundary counterexample and verified markdown report.')

    claims_steps = [PopClaim(1), PopClaim(1)]
    claims = [c.claimed for c in claims_steps]

    honest_boundary = run_segment_a([])
    forged_boundary = [1, 1]

    honest_pops, honest_final = run_semantic_b(honest_boundary, claims_steps)
    forged_semantic_pops, forged_final = run_semantic_b(forged_boundary, claims_steps)
    claimed_outputs = run_claimed_b(forged_boundary, claims_steps)

    checks: list[tuple[str, bool]] = []
    checks.append(('after A honest stack is [1,0]', honest_boundary == [1, 0]))
    checks.append(('honest height is 2', len(honest_boundary) == 2))
    checks.append(('honest top is 1', honest_boundary[0] == 1))
    checks.append(('forged boundary is [1,1]', forged_boundary == [1, 1]))
    checks.append(('forged has same height as honest', len(forged_boundary) == len(honest_boundary)))
    checks.append(('forged has same top as honest', forged_boundary[0] == honest_boundary[0]))
    checks.append(('buried bit differs', forged_boundary[1] != honest_boundary[1]))
    checks.append(('claimed B outputs are [1,1]', claimed_outputs == [1, 1]))
    checks.append(('forged semantics give [1,1]', forged_semantic_pops == [1, 1]))
    checks.append(('honest semantics give [1,0]', honest_pops == [1, 0]))
    checks.append(('counterexample distinguishes claimed from honest on second pop', claimed_outputs != honest_pops))
    checks.append(('full-boundary witness bits at h=2 equals 2', bits_required_full_boundary(2) == 2))
    checks.append(('one-challenge sequential step count equals 2', sequential_steps_one_challenge() == 2))

    report = make_report(honest_boundary, forged_boundary, claimed_outputs, honest_pops, forged_semantic_pops)
    REPORT.write_text(report, encoding='utf-8')

    print('Generated report:', REPORT)
    print('Honest boundary after A:', honest_boundary)
    print('Forged boundary:', forged_boundary)
    print('Claimed pop outputs:', claimed_outputs)
    print('Honest semantic pop outputs from honest boundary:', honest_pops)
    print('Semantic pop outputs from forged boundary:', forged_semantic_pops)
    print('Honest final stack after B:', honest_final)
    print('Forged final stack after B:', forged_final)
    print('Witness bits for full boundary, h=2:', bits_required_full_boundary(2))
    print('Sequential check cost for one challenged position:', sequential_steps_one_challenge())
    print('\nCheck results:')

    failed = []
    for name, ok in checks:
        print(f' - {name}: {"PASS" if ok else "FAIL"}')
        if not ok:
            failed.append(name)

    append_notes('Trial000086 checks complete. failures=' + repr(failed))

    if failed:
        print('\nOVERALL: FAIL')
        return 1
    print('\nOVERALL: PASS')
    return 0


if __name__ == '__main__':
    sys.exit(main())

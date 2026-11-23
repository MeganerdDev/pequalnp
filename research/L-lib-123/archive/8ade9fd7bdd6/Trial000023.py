from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

NOTES = Path('/workspace/notes.md')
REPORT = Path('/workspace/stack-boundary.md')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


@dataclass(frozen=True)
class BoundaryView:
    height: int
    top: int | None


class SemanticError(Exception):
    pass


def push(stack: list[int], bit: int) -> list[int]:
    if bit not in (0, 1):
        raise ValueError(f'invalid bit {bit}')
    return stack + [bit]


def pop(stack: list[int]) -> tuple[int, list[int]]:
    if not stack:
        raise SemanticError('pop from empty stack')
    return stack[-1], stack[:-1]


def boundary_view(stack: list[int]) -> BoundaryView:
    return BoundaryView(len(stack), stack[-1] if stack else None)


def simulate_segment_a() -> list[int]:
    stack: list[int] = []
    stack = push(stack, 0)
    stack = push(stack, 1)
    return stack


def simulate_claimed_segment_b(start_stack: list[int]) -> dict:
    first_value, after_first = pop(start_stack)
    result = {
        'start': start_stack,
        'first_pop_value': first_value,
        'after_first': after_first,
    }
    try:
        second_value, after_second = pop(after_first)
        result['second_pop_value'] = second_value
        result['after_second'] = after_second
    except SemanticError as e:
        result['second_pop_error'] = str(e)
    return result


def simulate_honest_two_pops(start_stack: list[int]) -> tuple[int, int, list[int]]:
    v1, s1 = pop(start_stack)
    v2, s2 = pop(s1)
    return v1, v2, s2


def write_report(honest_boundary: list[int], alt_boundary: list[int], claimed: dict) -> None:
    witness_bits = 1
    sequential_steps = [
        'Read the one-bit witness b that claims the buried bit directly under the top at the boundary.',
        'Issue a universal challenge asking for the local transition transcript for Segment A from empty stack to the boundary.',
        'Deterministically simulate Segment A: push 0, then push 1.',
        'Extract the boundary stack from the simulation and compare its second-from-top bit with b.',
        'If they differ, reject before even considering Segment B; if they agree, continue to any later challenged check.'
    ]
    lines = [
        '# Stack boundary audit',
        '',
        'Toy example fixed by the operator:',
        '- Start from empty stack `[]`.',
        '- Segment A performs `push 0; push 1`.',
        '- Segment B claims two successive pops both return `1`.',
        '',
        '## Honest boundary after Segment A',
        f'- Simulating Segment A gives boundary stack `{honest_boundary}` (bottom to top).',
        '- So the buried bit is `0` and the top bit is `1`.',
        '',
        '## Claimed Segment B versus honest semantics',
        f"- First pop from `{honest_boundary}` honestly returns `{claimed['first_pop_value']}` and leaves `{claimed['after_first']}`.",
        '- Therefore the first claimed pop returning `1` is compatible with honest semantics.',
        f"- The next honest pop from `{claimed['after_first']}` returns `{claimed.get('second_pop_value')}`, not `1`.",
        '- So the claim `pop -> 1; pop -> 1` fails exactly on the second pop.',
        '',
        '## Why checking only boundary height and top is insufficient',
        f'- Honest boundary stack: `{honest_boundary}` has view `(height={len(honest_boundary)}, top={honest_boundary[-1]})`.',
        f'- Alternate stack: `{alt_boundary}` has the same view `(height={len(alt_boundary)}, top={alt_boundary[-1]})`.',
        '- A verifier that inspects only height and top sees no difference between these two boundary states.',
        '- But the buried bit differs: honest stack has buried bit `0`, alternate stack has buried bit `1`.',
        '- Segment B depends on that buried bit after the first pop, so height+top alone misses the error source.',
        '',
        '## One explicit witness-binding proposal',
        '- Proposal: the first existential block sends one extra witness bit `b` intended to equal the buried bit at the boundary.',
        f'- Bits required for this proposal in the toy example: `{witness_bits}` extra bit.',
        '- Purpose: bind the information that height and top fail to reveal before a universal challenge chooses what local check to audit.',
        '',
        '## Sequential steps to check one challenge',
    ]
    for i, step in enumerate(sequential_steps, start=1):
        lines.append(f'{i}. {step}')
    lines += [
        '',
        '## Status of the proposal',
        '- For this toy example, the proposal succeeds only as a local fix because Segment A is fully known and deterministic, so the verifier can recompute the buried bit and compare it with the witness bit.',
        '- First unresolved technical question for the open theorem: in a long computation with many possible challenge locations, what compact first-round witness can bind the relevant buried symbol for every potential boundary simultaneously without expanding to essentially the whole stack history?',
        '- This is exactly where the toy repair stops scaling: one explicit bit works for one predetermined boundary, but no checked mechanism here compresses all such buried-state commitments into a three-round protocol with sublinear verification overhead.'
    ]
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')



def main() -> int:
    NOTES.write_text('', encoding='utf-8')
    log('Trial000023: begin stack-boundary experiment.')

    failures: list[str] = []

    honest_boundary = simulate_segment_a()
    log(f'Computed Segment A boundary: {honest_boundary}')
    if honest_boundary != [0, 1]:
        failures.append(f'Expected honest boundary [0, 1], got {honest_boundary}')

    claimed = simulate_claimed_segment_b(honest_boundary)
    log(f'Claimed Segment B audit: {claimed}')

    if claimed['first_pop_value'] != 1:
        failures.append(f"Expected first pop to return 1, got {claimed['first_pop_value']}")

    honest_first, honest_second, final_stack = simulate_honest_two_pops(honest_boundary)
    if honest_second != 0:
        failures.append(f'Expected second honest pop to return 0, got {honest_second}')
    if honest_first != 1:
        failures.append(f'Expected first honest pop to return 1, got {honest_first}')
    if final_stack != []:
        failures.append(f'Expected final stack after two honest pops to be [], got {final_stack}')

    alt_boundary = [1, 1]
    honest_view = boundary_view(honest_boundary)
    alt_view = boundary_view(alt_boundary)
    log(f'Boundary views honest={honest_view}, alternate={alt_view}')
    if honest_view != alt_view:
        failures.append('Expected alternate stack to match honest stack on height and top only')
    if honest_boundary[0] == alt_boundary[0]:
        failures.append('Expected alternate stack to differ in buried bit')

    write_report(honest_boundary, alt_boundary, claimed)
    log('Wrote /workspace/stack-boundary.md')

    print('Stack boundary experiment results')
    print(f'  Honest Segment A boundary: {honest_boundary}')
    print(f'  Honest two pops return: first={honest_first}, second={honest_second}, final={final_stack}')
    print(f'  Boundary view honest: height={honest_view.height}, top={honest_view.top}')
    print(f'  Boundary view alternate: height={alt_view.height}, top={alt_view.top}')
    print(f'  Report written to: {REPORT}')

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

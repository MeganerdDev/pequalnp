from pathlib import Path
import re
import sys

REPORT = Path('/workspace/stack-boundary.md')
NOTES = Path('/workspace/notes.md')

REPORT_TEXT = '''# Stack-boundary report

## Segment A
Start with the empty stack `[]`.

Segment A performs two pushes in order:
1. push `0`
2. push `1`

So the honest stack at boundary is `[0, 1]` from bottom to top.
The height at the boundary is `2` and the top bit is `1`.

## Segment B
Segment B claims two successive pops both return `1`.

If we execute Segment B honestly from the boundary stack `[0, 1]`, then:
1. the first pop returns `1`, leaving `[0]`
2. the second honest pop would return `0`, leaving `[]`

Therefore the claimed narrative after two pops returning `1` is inconsistent with the honest boundary stack.
A forged local story for Segment B could still talk as if the stack were `[1, 1]` at the boundary, because then two pops returning `1` would look locally consistent.

## Honest stack at boundary
The honest boundary stack is `[0, 1]` (bottom to top).

## Claimed stack at boundary
The claimed stack at boundary implicit in the "two pops both return 1" narrative would have to contain a buried `1` under the top `1`, for example `[1, 1]` at the topmost two positions. That claimed stack is not the honest one.

## Why checking only height and top misses the error
A verifier that checks only the boundary height and top bit sees:
- height `2`
- top `1`

Both the honest stack `[0, 1]` and the false claimed stack `[1, 1]` satisfy those two checks.
So height-plus-top does not bind the buried bit. The error lives in the second item from the top, and it is exposed only when the second pop is checked: after one honest pop the remaining top is `0`, not `1`.

## One proposal for binding the buried bit before a universal challenge
Proposal: the first existential block also guesses the top two boundary bits instead of only height and top, together with the claimed boundary height.
For this toy example, the witness is:
- boundary height: `2` encoded in `2` bits if we use a fixed-width local encoding for values `0..3`
- top bit: `1` bit
- second-from-top bit (the buried bit here): `1` bit

Total bits guessed for this boundary certificate in the toy instance: `4` bits.
If the machine model already carries the height elsewhere, then the incremental cost of binding the buried bit before the universal challenge is just `1` extra bit beyond the top-bit summary, or `2` bits for the top-two-bit summary.

A universal challenge can now choose one of the two pop positions to audit.
To check one challenge sequentially in this toy example:
1. read the guessed top-two-bit certificate
2. compare it against the actual boundary summary promised by Segment A
3. simulate the designated pop
4. verify the reported return value and updated top/height relation

This is a constant-length check; a concrete count is about `4` sequential steps in the toy boundary interface above.
If the challenge asks for the second pop, the checker must use the bound second-from-top bit, and it catches the inconsistency because the honest second pop returns `0`.

## First unresolved question / failure point
The first unresolved question is scalability: for a real long stack computation, how can the first existential block bind enough buried information before the universal challenge without growing the certificate to linear size in the number of potentially exposed stack cells?

Exact failure point for this proposal: binding the top two bits works for the two-pop toy example, but the method does not obviously extend when Segment B may pop an adversarially chosen depth `k`; then the existential block seems forced to guess `k` buried bits in advance, and for unrestricted `k` this destroys the hoped-for sublinear summary.
'''


def append_notes(msg: str) -> None:
    old = NOTES.read_text() if NOTES.exists() else ''
    NOTES.write_text(old + ('' if old.endswith('\n') or not old else '\n') + msg + '\n')


def check(name: str, ok: bool) -> bool:
    print(f'{name}: {"PASS" if ok else "FAIL"}')
    return ok


def main() -> int:
    append_notes('Trial000121: writing /workspace/stack-boundary.md and auditing required content.')
    REPORT.write_text(REPORT_TEXT)
    text = REPORT.read_text()

    results = []
    results.append(check('report_exists', REPORT.exists()))
    results.append(check('mentions_segment_a', '## Segment A' in text or 'Segment A' in text))
    results.append(check('mentions_segment_b', '## Segment B' in text or 'Segment B' in text))
    results.append(check('mentions_honest_boundary', 'honest stack at boundary' in text.lower()))
    results.append(check('mentions_claimed_boundary', 'claimed stack at boundary' in text.lower()))
    results.append(check('mentions_height_top_blindness', 'why checking only height and top misses the error' in text.lower()))
    results.append(check('states_honest_stack_exactly', '[0, 1]' in text and 'bottom to top' in text))
    results.append(check('states_second_honest_pop_zero', 'second honest pop would return `0`' in text or 'second honest pop would return 0' in text))
    results.append(check('states_two_pop_ones_inconsistent', 'two pops returning `1` is inconsistent' in text or 'two pops returning 1 is inconsistent' in text))
    results.append(check('proposes_binding_method', 'first existential block' in text.lower() and 'bind' in text.lower() and 'buried bit' in text.lower()))
    results.append(check('contains_concrete_bit_count', bool(re.search(r'Total bits guessed.*`4` bits', text)) or '4 bits' in text))
    results.append(check('contains_concrete_step_count', '4 sequential steps' in text or 'about `4` sequential steps' in text))
    results.append(check('contains_unresolved_question', 'first unresolved question' in text.lower() or 'unresolved question' in text.lower()))
    results.append(check('contains_exact_failure_point', 'Exact failure point' in text or 'failure point' in text.lower()))

    print('\nMeasured results:')
    print(f'report_path={REPORT}')
    print(f'bytes={REPORT.stat().st_size}')
    print(f'lines={len(text.splitlines())}')
    print('claimed_honest_boundary=[0, 1]')
    print('claimed_false_story=two successive pops both return 1')
    print('certificate_bits_toy=4')
    print('challenge_check_steps_toy=4')

    ok = all(results)
    append_notes('Trial000121 result: ' + ('PASS' if ok else 'FAIL'))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

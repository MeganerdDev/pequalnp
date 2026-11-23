from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import re

ARTIFACT = Path('/workspace/Trial000040.py')
REPORT = Path('/workspace/stack-boundary.md')
NOTES = Path('/workspace/notes.md')

REQUIRED_SECTIONS = [
    'Honest boundary',
    'Claimed boundary',
    'Why height+top fails',
    'One repair proposal',
    'Bit count and sequential check cost',
    'First unresolved question',
]


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


class CheckFailure(Exception):
    pass


def push(stack: list[int], bit: int) -> list[int]:
    return stack + [bit]


def pop(stack: list[int]) -> tuple[int | None, list[int]]:
    if not stack:
        return None, []
    return stack[-1], stack[:-1]


def run_ops(start: list[int], ops: list[tuple[str, int | None]]) -> tuple[list[int], list[int | None]]:
    stack = list(start)
    outs: list[int | None] = []
    for op, arg in ops:
        if op == 'push':
            assert arg in (0, 1)
            stack = push(stack, int(arg))
        elif op == 'pop':
            out, stack = pop(stack)
            outs.append(out)
        else:
            raise ValueError(op)
    return stack, outs


def top_bit(stack: list[int]) -> int | None:
    return stack[-1] if stack else None


def all_stacks(max_height: int) -> list[list[int]]:
    out: list[list[int]] = [[]]
    for h in range(1, max_height + 1):
        for bits in product([0, 1], repeat=h):
            out.append(list(bits))
    return out


def witness_height_top(stack: list[int]) -> tuple[int, int | None]:
    return (len(stack), top_bit(stack))


def pop_trace(stack: list[int], k: int) -> tuple[int | None, ...]:
    s = list(stack)
    ans: list[int | None] = []
    for _ in range(k):
        b, s = pop(s)
        ans.append(b)
    return tuple(ans)


@dataclass
class Counterexample:
    witness: tuple[int, int | None]
    a: list[int]
    b: list[int]
    k: int
    trace_a: tuple[int | None, ...]
    trace_b: tuple[int | None, ...]


def find_counterexample(max_height: int, challenge_len: int) -> Counterexample | None:
    stacks = all_stacks(max_height)
    groups: dict[tuple[int, int | None], list[list[int]]] = {}
    for s in stacks:
        groups.setdefault(witness_height_top(s), []).append(s)
    for w in sorted(groups, key=lambda x: (x[0], -1 if x[1] is None else x[1])):
        group = groups[w]
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                ta, tb = pop_trace(a, challenge_len), pop_trace(b, challenge_len)
                if ta != tb:
                    return Counterexample(w, a, b, challenge_len, ta, tb)
    return None


def expect(cond: bool, msg: str) -> None:
    if not cond:
        raise CheckFailure(msg)


def build_report() -> str:
    ops_a = [('push', 0), ('push', 1)]
    honest_boundary, _ = run_ops([], ops_a)
    claimed_pop_ops = [('pop', None), ('pop', None)]
    _, honest_pop_trace = run_ops(honest_boundary, claimed_pop_ops)

    expect(honest_boundary == [0, 1], f'honest boundary mismatch: {honest_boundary}')
    expect(honest_pop_trace == [1, 0], f'honest pop trace mismatch: {honest_pop_trace}')

    claimed_boundary_example = [1, 1]
    _, claimed_pop_trace = run_ops(claimed_boundary_example, claimed_pop_ops)
    expect(claimed_pop_trace == [1, 1], f'claimed witness stack does not realize [1,1]: {claimed_pop_trace}')
    expect(witness_height_top(honest_boundary) == witness_height_top(claimed_boundary_example), 'height+top should match between honest and claimed witness stack')

    cex = find_counterexample(4, 2)
    expect(cex is not None, 'expected a height+top counterexample up to height 4 for length-2 pops')
    assert cex is not None
    expect(cex.trace_a != cex.trace_b, 'counterexample traces should differ')
    expect(witness_height_top(cex.a) == witness_height_top(cex.b), 'counterexample witness mismatch')

    report = []
    report.append('# Stack boundary audit')
    report.append('')
    report.append('## Honest boundary')
    report.append('Start from the empty stack `[]`. Segment A pushes `0` and then pushes `1`.')
    report.append(f'- Oracle result: the honest boundary stack is `{honest_boundary}` with top `{top_bit(honest_boundary)}` and height `{len(honest_boundary)}`.')
    report.append(f'- Oracle continuation under two successive pops: `{honest_pop_trace[0]}` then `{honest_pop_trace[1]}`.')
    report.append('- Therefore, after pushes 0 then 1 the honest boundary stack is `[0, 1]` with top 1 and height 2, and the second pop from the honest stack returns 0.')
    report.append('')
    report.append('## Claimed boundary')
    report.append('Segment B falsely claims that two successive pops both return `1`.')
    report.append('- A boundary stack that really would support that claim is `[1, 1]`.')
    report.append(f'- Oracle check on `[1, 1]`: two successive pops return `{claimed_pop_trace[0]}` then `{claimed_pop_trace[1]}`.')
    report.append(f'- This stack has the same height and top summary as the honest stack: witness `{witness_height_top(claimed_boundary_example)}`.')
    report.append('- So the claimed transcript for two pops both returning 1 requires a different boundary behavior because the second pop from the honest stack returns 0.')
    report.append('')
    report.append('## Why height+top fails')
    report.append('Checking only `(height, top)` cannot distinguish the honest boundary `[0, 1]` from the dishonest alternative `[1, 1]`: both have height `2` and top `1`.')
    report.append('The mismatch is a buried bit: the second-from-top bit is `0` in the honest stack but `1` in the claimed stack.')
    report.append(f'- Exhaustive oracle search over all bit-stacks of height up to 4 found a concrete counterexample with shared witness `{cex.witness}`.')
    report.append(f'- Concrete pair: `a = {cex.a}` and `b = {cex.b}`.')
    report.append(f'- Two-pop traces: from `a` the oracle returns `{list(cex.trace_a)}`, while from `b` it returns `{list(cex.trace_b)}`.')
    report.append('- This mechanically demonstrates that height+top misses buried-bit errors even for a POP-only continuation of length 2.')
    report.append('')
    report.append('## One repair proposal')
    report.append('One explicit repair proposal is: before the universal challenge, the first existential block binds the top two bits together with the height.')
    report.append('For example, use a witness of the form `(height, top1, top2)` where `top2` is padded with a sentinel when the stack height is below 2, or equivalently bind the entire length-2 top suffix plus the height.')
    report.append('For the concrete boundary above, that witness distinguishes `[0, 1]` from `[1, 1]` because their top-two-bit views are different: `[0, 1]` versus `[1, 1]`.')
    report.append('This binds the buried bit needed to answer a length-2 POP-only challenge correctly.')
    report.append('')
    report.append('## Bit count and sequential check cost')
    report.append('If the verifier may issue a POP-only challenge of length `k`, the direct suffix-binding version of the proposal stores the top `k` bits, with padding for short stacks, plus enough bits to encode the height.')
    report.append('- Witness-bit count as a function of `k`: `k` payload bits for the bound suffix, plus the height field (for stacks bounded by height `H`, this is `ceil(log2(H+1))` bits, or one may leave height as an external arithmetic parameter and still need the `k` suffix bits).')
    report.append('- For the specific proposal requested here, binding at least the top two bits uses 2 payload bits, plus the height field.')
    report.append('- Sequential verification cost for one length-2 challenge: 2 pop-check steps, because the verifier must compare the first claimed pop to the bound top bit and the second claimed pop to the next bound bit in order.')
    report.append('More generally, checking one length-`k` POP-only challenge against this bound suffix takes `k` sequential pop-check steps.')
    report.append('')
    report.append('## First unresolved question')
    report.append('The direct suffix-binding repair scales linearly with challenge length: to survive arbitrary length-`k` POP-only challenges, it appears to need `k` explicitly bound bits and `k` sequential comparison steps.')
    report.append('The first unresolved question is whether there exists any sound three-round binding scheme that commits to enough buried stack information to answer long adaptive pop challenges while using asymptotically fewer than `k` bound bits or fewer than `k` sequential checks, without reintroducing the same buried-bit failure at a deeper level.')
    return '\n'.join(report) + '\n'


def verify_report(text: str) -> None:
    for sec in REQUIRED_SECTIONS:
        expect(f'## {sec}' in text, f'missing required section: {sec}')

    required_phrases = [
        'the honest boundary stack is `[0, 1]` with top `1` and height `2`',
        'the second pop from the honest stack returns 0',
        'two successive pops both return `1`',
        'height `2` and top `1`',
        '2 pop-check steps',
    ]
    for phrase in required_phrases:
        expect(phrase in text, f'missing required phrase: {phrase}')

    honest_match = re.search(r'honest boundary stack is `([^`]+)` with top `([^`]+)` and height `([^`]+)`', text)
    expect(honest_match is not None, 'could not parse honest boundary line')
    stack_text, top_text, height_text = honest_match.groups()
    expect(stack_text == '[0, 1]' and top_text == '1' and height_text == '2', 'honest boundary textual claim disagrees with oracle')

    pair_match = re.search(r'Concrete pair: `a = (\[[^`]+\])` and `b = (\[[^`]+\])`\.', text)
    expect(pair_match is not None, 'could not parse concrete pair line')
    a = eval(pair_match.group(1), {}, {})
    b = eval(pair_match.group(2), {}, {})
    expect(witness_height_top(a) == witness_height_top(b), 'parsed counterexample pair does not share witness')
    expect(pop_trace(a, 2) != pop_trace(b, 2), 'parsed counterexample pair does not differ on length-2 pop trace')


def main() -> int:
    NOTES.write_text('Trial000040 starting\n', encoding='utf-8')
    log('Building stack-boundary.md from explicit stack semantics oracle.')
    text = build_report()
    REPORT.write_text(text, encoding='utf-8')
    verify_report(text)
    cex = find_counterexample(4, 2)
    assert cex is not None
    print('Stack boundary audit experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print('Honest boundary stack:', [0, 1])
    print('Honest two-pop trace:', list(pop_trace([0, 1], 2)))
    print('Height+top witness for honest and claimed [1,1]:', witness_height_top([0, 1]))
    print('Exhaustive counterexample up to height 4:', f'witness={cex.witness}, a={cex.a}, b={cex.b}, trace_a={list(cex.trace_a)}, trace_b={list(cex.trace_b)}')
    print('All checks passed.')
    log('All checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

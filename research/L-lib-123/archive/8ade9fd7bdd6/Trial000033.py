#!/usr/bin/env python3
from __future__ import annotations

import itertools
import os
import sys
from pathlib import Path

WORKSPACE = Path('/workspace')
ARTIFACT = WORKSPACE / 'Trial000033.py'
REPORT = WORKSPACE / 'stack-boundary.md'
NOTES = WORKSPACE / 'notes.md'


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def push(stack, bit):
    return stack + (bit,)


def pop_trace(stack, steps):
    s = list(stack)
    out = []
    for _ in range(steps):
        if s:
            out.append(str(s.pop()))
        else:
            out.append('UNDERFLOW')
    return tuple(out), tuple(s)


def witness_top1(stack):
    top = stack[-1] if stack else None
    return (len(stack), top)


def witness_top2(stack):
    if len(stack) >= 2:
        bits = (stack[-1], stack[-2])
    elif len(stack) == 1:
        bits = (stack[-1], None)
    else:
        bits = (None, None)
    return (len(stack), bits)


def all_stacks(max_height=4):
    stacks = [tuple()]
    for h in range(1, max_height + 1):
        for bits in itertools.product((0, 1), repeat=h):
            stacks.append(bits)
    return stacks


def find_counterexample(stacks, witness_fn, max_steps=2):
    buckets = {}
    for st in stacks:
        buckets.setdefault(witness_fn(st), []).append(st)
    tested_pairs = 0
    tested_conts = 0
    first = None
    any_same_witness_pairs = 0
    for witness, items in buckets.items():
        if len(items) < 2:
            continue
        for a, b in itertools.combinations(items, 2):
            any_same_witness_pairs += 1
            tested_pairs += 1
            for steps in range(1, max_steps + 1):
                tested_conts += 1
                ta, _ = pop_trace(a, steps)
                tb, _ = pop_trace(b, steps)
                if ta != tb and first is None:
                    first = {
                        'witness': witness,
                        'a': a,
                        'b': b,
                        'steps': steps,
                        'trace_a': ta,
                        'trace_b': tb,
                    }
    return {
        'counterexample': first,
        'tested_pairs': tested_pairs,
        'tested_conts': tested_conts,
        'same_witness_pairs': any_same_witness_pairs,
    }


def write_report(top1_result, top2_result):
    honest = (0, 1)
    claimed = (1, 1)
    lines = []
    lines.append('# Stack boundary report')
    lines.append('')
    lines.append('## Honest boundary')
    lines.append('Start from the empty stack `[]`. Segment A does `push 0; push 1`.')
    lines.append(f'The honest boundary stack is `{list(honest)}` (bottom-to-top), so height = 2 and top = 1.')
    lines.append('If we now pop twice honestly, the returns are `1` then `0`.')
    lines.append('')
    lines.append('## Claimed boundary')
    lines.append('For Segment B to justify the claim that two successive pops both return `1`, the boundary would need buried contents consistent with top two bits `(1, 1)`.')
    lines.append(f'One concrete claimed boundary stack is `{list(claimed)}` (bottom-to-top).')
    lines.append('From that claimed stack, two pops return `1` then `1`.')
    lines.append('')
    lines.append('## Why height+top fails')
    lines.append(f'Both the honest stack `{list(honest)}` and the claimed stack `{list(claimed)}` have the same `(height, top)` witness: `{witness_top1(honest)}`.')
    lines.append('The buried bit mismatch is concrete: the honest bottom/buried bit is `0`, while the claimed buried bit is `1`.')
    lines.append('A verifier that checks only height and top cannot see that mismatch, so one pop looks fine but the second pop can expose the hidden error.')
    lines.append('The exhaustive oracle search below confirms a distinguishing counterexample for `top1 = (height, top)` within two POP steps.')
    lines.append('')
    lines.append('## One repair proposal')
    lines.append('Repair proposal: let the first existential block reveal not only the height and top bit, but also the next buried bit before the universal challenge.')
    lines.append('In this toy binary stack model, that exposes exactly 3 witness bits/information units for a height-2 boundary:')
    lines.append('1. the height (value `2` here),')
    lines.append('2. the top bit,')
    lines.append('3. the second-from-top / buried bit.')
    lines.append('To check one challenge consisting of up to two POP operations, the verifier needs exactly 2 sequential simulation steps: execute POP once, then POP a second time, comparing the observed outputs against the bound top-two-bit witness.')
    lines.append('For the specific Segment A / Segment B dispute, this repair succeeds because the second exposed bit distinguishes honest `[0, 1]` from claimed `[1, 1]` immediately.')
    lines.append('More generally, this proposal fails beyond two-step POP challenges: stacks with the same `(height, top two bits)` can still disagree deeper down, so a third POP may distinguish them. That exact failure point is beyond the present two-step check and is the first unresolved question.')
    lines.append('')
    lines.append('## First unresolved question')
    lines.append('Does exposing `(height, top two bits)` eliminate all counterexamples for continuations of length at most 2, and where does it first fail?')
    lines.append(f'Oracle result for `top1=(height, top)`: same-witness pairs={top1_result["same_witness_pairs"]}, tested continuations={top1_result["tested_conts"]}.')
    ce1 = top1_result['counterexample']
    lines.append(f'Counterexample for `top1`: stacks {list(ce1["a"])} and {list(ce1["b"])} share witness {ce1["witness"]}, but {ce1["steps"]} POP steps produce traces {ce1["trace_a"]} and {ce1["trace_b"]}.')
    lines.append(f'Oracle result for `top2=(height, top two bits with padding)`: same-witness pairs={top2_result["same_witness_pairs"]}, tested continuations={top2_result["tested_conts"]}.')
    if top2_result['counterexample'] is None:
        lines.append('No counterexample exists for `top2` under one- or two-POP continuations in the exhaustive search over all stacks of height up to 4.')
    else:
        ce2 = top2_result['counterexample']
        lines.append(f'Counterexample for `top2`: stacks {list(ce2["a"])} and {list(ce2["b"])} share witness {ce2["witness"]}, but {ce2["steps"]} POP steps produce traces {ce2["trace_a"]} and {ce2["trace_b"]}.')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main() -> int:
    log('Starting Trial000033 stack-boundary experiment.')
    stacks = all_stacks(4)
    top1_result = find_counterexample(stacks, witness_top1, 2)
    top2_result = find_counterexample(stacks, witness_top2, 2)
    write_report(top1_result, top2_result)

    text = REPORT.read_text(encoding='utf-8')
    failures = []
    required_sections = [
        '## Honest boundary',
        '## Claimed boundary',
        '## Why height+top fails',
        '## One repair proposal',
        '## First unresolved question',
    ]
    for sec in required_sections:
        if sec not in text:
            failures.append(f'missing markdown section: {sec}')
    for needle in [
        'The honest boundary stack is `[0, 1]`',
        'One concrete claimed boundary stack is `[1, 1]`',
        'The buried bit mismatch is concrete: the honest bottom/buried bit is `0`, while the claimed buried bit is `1`.',
    ]:
        if needle not in text:
            failures.append(f'missing required sentence/content: {needle}')

    if top1_result['counterexample'] is None:
        failures.append('expected a distinguishing counterexample for top1 under length <= 2, but none was found')
    else:
        ce1 = top1_result['counterexample']
        expected_pair = {tuple((0, 1)), tuple((1, 1))}
        if ce1['steps'] > 2:
            failures.append('top1 counterexample used too many POP steps')
        focused_trace_a, _ = pop_trace((0, 1), 2)
        focused_trace_b, _ = pop_trace((1, 1), 2)
        if focused_trace_a == focused_trace_b:
            failures.append('focused boundary pair [0,1] vs [1,1] was not distinguished by two POPs')
        if {ce1['a'], ce1['b']} != expected_pair:
            log(f'Note: first top1 counterexample differs from focused boundary pair: {ce1}')

    if top2_result['counterexample'] is not None:
        failures.append(f'expected no top2 counterexample under length <= 2, found {top2_result["counterexample"]}')

    if 'No counterexample exists for `top2` under one- or two-POP continuations' not in text:
        failures.append('markdown does not state the top2 oracle result clearly')

    print('Stack boundary experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Total stacks checked: {len(stacks)}')
    print(f'top1 same-witness pairs: {top1_result["same_witness_pairs"]}, continuation tests: {top1_result["tested_conts"]}')
    print(f'top2 same-witness pairs: {top2_result["same_witness_pairs"]}, continuation tests: {top2_result["tested_conts"]}')
    print(f'top1 counterexample: {top1_result["counterexample"]}')
    print(f'top2 counterexample: {top2_result["counterexample"]}')

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

#!/usr/bin/env python3
from __future__ import annotations

import itertools
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000035.py')
REPORT = Path('/workspace/stack-boundary-extended.md')
NOTES = Path('/workspace/notes.md')
PRIOR = Path('/workspace/stack-boundary.md')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def all_stacks(max_height: int):
    for h in range(max_height + 1):
        for bits in itertools.product((0, 1), repeat=h):
            yield bits


def pop_trace(stack, k: int):
    s = list(stack)
    out = []
    for _ in range(k):
        if s:
            out.append(str(s.pop()))
        else:
            out.append('U')
    return tuple(out)


def top_bits_with_padding(stack, t: int):
    s = list(stack)
    bits = []
    for i in range(t):
        idx = len(s) - 1 - i
        bits.append(s[idx] if idx >= 0 else 'P')
    return tuple(bits)


def witness_top2(stack):
    return (len(stack),) + top_bits_with_padding(stack, 2)


def witness_top3(stack):
    return (len(stack),) + top_bits_with_padding(stack, 3)


def search(stacks, witness_fn, lengths):
    groups = {}
    for st in stacks:
        groups.setdefault(witness_fn(st), []).append(st)
    same_pairs = 0
    tested = 0
    per_length = {k: None for k in lengths}
    first_any = None
    for wit, group in groups.items():
        if len(group) < 2:
            continue
        for i in range(len(group)):
            for j in range(i + 1, len(group)):
                a, b = group[i], group[j]
                same_pairs += 1
                for k in lengths:
                    tested += 1
                    ta = pop_trace(a, k)
                    tb = pop_trace(b, k)
                    if ta != tb:
                        ce = {
                            'witness': wit,
                            'a': a,
                            'b': b,
                            'k': k,
                            'trace_a': ta,
                            'trace_b': tb,
                        }
                        if per_length[k] is None:
                            per_length[k] = ce
                        if first_any is None or k < first_any['k']:
                            first_any = ce
    return {
        'same_pairs': same_pairs,
        'tested': tested,
        'per_length': per_length,
        'first_any': first_any,
    }


def fmt_stack(st):
    return '[' + ', '.join(str(x) for x in st) + ']'


def fmt_ce(ce):
    if ce is None:
        return 'none'
    return (
        f"witness={ce['witness']}, a={fmt_stack(ce['a'])}, b={fmt_stack(ce['b'])}, "
        f"k={ce['k']}, trace_a={ce['trace_a']}, trace_b={ce['trace_b']}"
    )


def main() -> int:
    NOTES.write_text('', encoding='utf-8')
    log('Starting Trial000035 stack-boundary extension experiment.')
    failures = []

    if not PRIOR.exists():
        failures.append('Missing prior report /workspace/stack-boundary.md')
        prior_text = ''
    else:
        prior_text = PRIOR.read_text(encoding='utf-8')
        log('Loaded prior stack-boundary.md for verification.')

    required_prior = [
        'First unresolved question',
        'No counterexample exists for `top2` under one- or two-POP continuations',
    ]
    for needle in required_prior:
        if needle not in prior_text:
            failures.append(f'Prior report missing expected text: {needle}')

    max_height = 6
    stacks = list(all_stacks(max_height))
    log(f'Enumerated {len(stacks)} stacks up to height {max_height}.')

    top2 = search(stacks, witness_top2, [1, 2, 3])
    top3 = search(stacks, witness_top3, [1, 2, 3])
    log(f"top2 earliest counterexample: {fmt_ce(top2['first_any'])}")
    log(f"top3 earliest counterexample: {fmt_ce(top3['first_any'])}")

    if top2['per_length'][1] is not None or top2['per_length'][2] is not None:
        failures.append('Oracle contradicts prior claim: top2 has a counterexample for k<=2.')
    if top2['per_length'][3] is None:
        earliest_text = 'No top2 counterexample exists for length 3 within height <= 6.'
    else:
        earliest_text = (
            'The first top2 failure in the searched range occurs at k=3: '
            + fmt_ce(top2['per_length'][3])
        )
    if top3['per_length'][1] is not None or top3['per_length'][2] is not None or top3['per_length'][3] is not None:
        top3_text = 'No: top3 still has a counterexample within k<=3: ' + fmt_ce(top3['first_any'])
    else:
        top3_text = 'Yes: top3 removes all counterexamples for k<=3 in the searched range.'

    lines = []
    lines.append('# Stack boundary extended report')
    lines.append('')
    lines.append('## Question')
    lines.append('Continue the first unresolved question from `/workspace/stack-boundary.md`: find the first POP-only continuation length `k` at which exposing `top2 = (height, top two bits with padding)` fails, and test whether `top3 = (height, top three bits with padding)` repairs all counterexamples up to that same bound.')
    lines.append('')
    lines.append('## Method')
    lines.append(f'Exhaustively enumerate all bit-stacks of heights 0 through {max_height}. This yields {len(stacks)} stacks total. For each witness scheme, compare every distinct pair of stacks with the same witness and compute the exact POP/underflow trace for continuations of lengths 1, 2, and 3. A counterexample is a same-witness pair whose traces differ for some tested length.')
    lines.append('')
    lines.append('## top2 results')
    lines.append(f"Same-witness pairs checked: {top2['same_pairs']}. Continuation tests: {top2['tested']}.")
    lines.append(f"Length 1 counterexample: {fmt_ce(top2['per_length'][1])}.")
    lines.append(f"Length 2 counterexample: {fmt_ce(top2['per_length'][2])}.")
    lines.append(f"Length 3 counterexample: {fmt_ce(top2['per_length'][3])}.")
    if top2['per_length'][1] is None and top2['per_length'][2] is None:
        lines.append('Confirmed again: `top2` has no distinguishing counterexample for POP-only lengths <= 2 in the searched range.')
    else:
        lines.append('Unexpectedly, `top2` already fails for a POP-only length <= 2 in the searched range.')
    lines.append('')
    lines.append('## top3 results')
    lines.append(f"Same-witness pairs checked: {top3['same_pairs']}. Continuation tests: {top3['tested']}.")
    lines.append(f"Length 1 counterexample: {fmt_ce(top3['per_length'][1])}.")
    lines.append(f"Length 2 counterexample: {fmt_ce(top3['per_length'][2])}.")
    lines.append(f"Length 3 counterexample: {fmt_ce(top3['per_length'][3])}.")
    lines.append(top3_text)
    lines.append('')
    lines.append('## Earliest failure')
    lines.append(earliest_text)
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    text = REPORT.read_text(encoding='utf-8')
    for sec in ['Question', 'Method', 'top2 results', 'top3 results', 'Earliest failure']:
        if f'## {sec}' not in text:
            failures.append(f'Missing report section: {sec}')

    if top2['per_length'][1] is None and top2['per_length'][2] is None:
        req = 'Confirmed again: `top2` has no distinguishing counterexample for POP-only lengths <= 2 in the searched range.'
        if req not in text:
            failures.append('Report does not clearly confirm top2 for lengths <=2.')
    if top2['per_length'][3] is None:
        req = 'No top2 counterexample exists for length 3 within height <= 6.'
    else:
        req = 'The first top2 failure in the searched range occurs at k=3:'
    if req not in text:
        failures.append('Report does not state the top2 length-3 outcome correctly.')
    if top3['first_any'] is None:
        req = 'Yes: top3 removes all counterexamples for k<=3 in the searched range.'
    else:
        req = 'No: top3 still has a counterexample within k<=3:'
    if req not in text:
        failures.append('Report does not state the top3 outcome correctly.')

    print('Stack boundary extended experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Total stacks checked: {len(stacks)}')
    print(f"top2 same-witness pairs: {top2['same_pairs']}, continuation tests: {top2['tested']}")
    print(f"top2 earliest counterexample: {fmt_ce(top2['first_any'])}")
    print(f"top3 same-witness pairs: {top3['same_pairs']}, continuation tests: {top3['tested']}")
    print(f"top3 earliest counterexample: {fmt_ce(top3['first_any'])}")

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

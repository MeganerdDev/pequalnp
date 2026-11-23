#!/usr/bin/env python3
import json
import sys
from pathlib import Path


NOTES = Path('/workspace/notes.md')


def pop_result(stack, depth):
    if depth <= 0:
        raise ValueError('depth must be positive')
    if len(stack) < depth:
        return None
    return stack[-depth]


def summarize_stack(stack):
    return {
        'stack': list(stack),
        'height': len(stack),
        'top': stack[-1] if stack else None,
        'depth2_bit': pop_result(stack, 2),
        'first_pop': pop_result(stack, 1),
        'second_pop': pop_result(stack, 2),
        'third_pop': pop_result(stack, 3),
    }


def append_notes(lines):
    prior = ''
    if NOTES.exists():
        prior = NOTES.read_text(encoding='utf-8')
        if prior and not prior.endswith('\n'):
            prior += '\n'
    NOTES.write_text(prior + ''.join(line + '\n' for line in lines), encoding='utf-8')


def main():
    honest = [1, 0, 1]
    cheating = [0, 0, 1]

    honest_summary = summarize_stack(honest)
    cheating_summary = summarize_stack(cheating)

    checks = {
        'same_height': honest_summary['height'] == cheating_summary['height'],
        'same_top': honest_summary['top'] == cheating_summary['top'],
        'same_depth2': honest_summary['depth2_bit'] == cheating_summary['depth2_bit'],
        'same_bound_summary': (
            honest_summary['height'],
            honest_summary['top'],
            honest_summary['depth2_bit'],
        ) == (
            cheating_summary['height'],
            cheating_summary['top'],
            cheating_summary['depth2_bit'],
        ),
        'different_third_pop': honest_summary['third_pop'] != cheating_summary['third_pop'],
    }

    expected = {
        'honest_first_pop_is_1': honest_summary['first_pop'] == 1,
        'cheating_first_pop_is_1': cheating_summary['first_pop'] == 1,
        'honest_second_pop_is_0': honest_summary['second_pop'] == 0,
        'cheating_second_pop_is_0': cheating_summary['second_pop'] == 0,
        'honest_third_pop_is_1': honest_summary['third_pop'] == 1,
        'cheating_third_pop_is_0': cheating_summary['third_pop'] == 0,
    }

    result = {
        'objective': 'Even binding (height, top, depth-2 bit) does not authenticate arbitrary deeper stack contents.',
        'honest': honest_summary,
        'cheating': cheating_summary,
        'same_height': checks['same_height'],
        'same_top': checks['same_top'],
        'same_depth2': checks['same_depth2'],
        'same_bound_summary': checks['same_bound_summary'],
        'different_third_pop': checks['different_third_pop'],
        'checks': checks,
        'expected': expected,
        'pass': all(checks.values()) and all(expected.values()),
    }

    append_notes([
        'Trial000013: tested stronger toy impossibility claim with bound summary (height, top, depth2).',
        f'Honest stack: {honest}',
        f'Cheating stack: {cheating}',
        'Goal: stacks agree on the three bound fields but differ on third pop.',
        json.dumps(result, sort_keys=True),
    ])

    print(json.dumps(result, indent=2))
    if result['pass']:
        return 0
    print('FAIL: stronger toy counterexample checks did not all hold.', file=sys.stderr)
    return 1


if __name__ == '__main__':
    raise SystemExit(main())

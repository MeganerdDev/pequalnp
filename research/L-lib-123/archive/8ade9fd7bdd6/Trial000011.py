#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPORT = Path('/workspace/stack-boundary.md')


def has_pair(text: str, a: str, b: str) -> bool:
    return a in text and b in text


def main() -> int:
    checks: dict[str, bool] = {}
    details: dict[str, object] = {}

    checks['exists'] = REPORT.is_file()
    if not checks['exists']:
        summary = {
            'report': str(REPORT),
            'checks': checks,
            'details': {'error': 'report missing'},
        }
        print(json.dumps(summary, indent=2))
        return 1

    text = REPORT.read_text(encoding='utf-8')
    lower = text.lower()

    phrases = {
        'empty stack': 'empty stack' in lower,
        'pushes 0': 'pushes 0' in lower,
        'pushes 1': 'pushes 1' in lower,
        'two successive pops both return 1': 'two successive pops both return 1' in lower,
    }
    checks['specified_example_phrases'] = all(phrases.values())
    details['specified_example_phrases'] = phrases

    honest_claimed = (
        'honest boundary stack' in lower
        and 'claimed boundary stack' in lower
        and 'honest' in lower
        and 'claimed' in lower
    )
    checks['honest_vs_claimed_boundary'] = honest_claimed

    checks['height_and_top_explained'] = (
        'height' in lower and 'top' in lower and ('misses the error' in lower or 'insufficient' in lower)
    )

    checks['existential_binding_proposal'] = (
        'existential' in lower and 'buried bit' in lower and 'universal challenge' in lower
    )

    checks['bit_count_and_sequential_steps'] = (
        'bits' in lower and 'sequential steps' in lower and bool(re.search(r'\b[0-9]+\s+bits\b', lower))
    )

    checks['unresolved_question_phrase'] = 'unresolved question' in lower

    summary = {
        'report': str(REPORT),
        'checks': checks,
        'details': details,
    }
    print(json.dumps(summary, indent=2))
    return 0 if all(checks.values()) else 1


if __name__ == '__main__':
    raise SystemExit(main())

#!/usr/bin/env python3
import re
import sys
from pathlib import Path

NOTES = Path('/workspace/notes.md')
ARTIFACT = Path('/workspace/Trial000108.py')
TARGET = Path('/workspace/stack-boundary.md')


def append_note(text: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(text.rstrip() + '\n')


def normalize(text: str) -> str:
    text = text.lower().replace('`', ' ')
    text = re.sub(r'[^a-z0-9()_,+\-\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def contains_all(text: str, groups):
    return all(any(token in text for token in group) for group in groups)


def find_lines(raw: str, needles, limit: int = 4):
    hits = []
    for line in raw.splitlines():
        low = line.lower()
        if any(n in low for n in needles):
            hits.append(line.strip())
    return hits[:limit]


def feature_checks(raw: str):
    norm = normalize(raw)
    seq_lines = [line.strip() for line in raw.splitlines() if re.match(r'\s*\d+\.', line)]
    return [
        (
            'honest stack at boundary',
            contains_all(norm, [
                ['honest stack', 'actual stack', 'true stack', 'produced stack'],
                ['boundary'],
            ]),
            find_lines(raw, ['honest stack', 'actual stack', 'true stack', 'produced stack', 'boundary'])
        ),
        (
            'claimed stack at boundary',
            contains_all(norm, [
                ['claimed execution', 'claimed stack', 'segment b falsely claims', 'claimed transcript'],
                ['boundary', 'a/b boundary'],
            ]),
            find_lines(raw, ['claimed execution', 'claimed stack', 'segment b falsely claims', 'claimed transcript', 'boundary'])
        ),
        (
            'height and top alone miss the error',
            contains_all(norm, [
                ['height and top', 'only height and top', 'checking only height and top'],
                ['misses the error', 'misses the mismatch', 'does not determine', 'cannot detect', 'fails to detect'],
            ]),
            find_lines(raw, ['height and top', 'only height and top', 'does not determine', 'misses', 'detect'])
        ),
        (
            'proposal binds buried bit before universal challenge',
            contains_all(norm, [
                ['bind the buried bit', 'binding the buried bit', 'buried information', 'hidden cell'],
                ['before a universal challenge', 'before the universal challenge', 'universal challenge'],
            ]),
            find_lines(raw, ['buried bit', 'buried information', 'hidden cell', 'universal challenge'])
        ),
        (
            'explicit bit count',
            contains_all(norm, [[
                'bit count', 'bits required', 'extra cost', '2 bits', '1 bit'
            ]]),
            find_lines(raw, ['bit count', 'bits required', 'extra cost', '2 bits', '1 bit'])
        ),
        (
            'explicit sequential check steps',
            len(seq_lines) >= 3 and ('check one challenge' in norm or 'verifier checking one challenge would' in norm),
            seq_lines[:6]
        ),
        (
            'explicit failure point or unresolved question',
            contains_all(norm, [[
                'where the proposal fails', 'unresolved issue', 'unresolved question', 'proposal currently fails'
            ]]),
            find_lines(raw, ['where the proposal fails', 'unresolved issue', 'unresolved question', 'proposal currently fails'])
        ),
        (
            'secondary: report notes bounded toy fix only',
            any(phrase in norm for phrase in [
                'works only for a fixed tiny lookahead',
                'not an unbounded stack suffix',
                'arbitrary length challenge',
                'constant size first existential block does not determine all deeper cells',
            ]),
            find_lines(raw, ['lookahead', 'unbounded stack suffix', 'arbitrary length challenge', 'deeper cells'])
        ),
    ]


def main() -> int:
    append_note('Trial000108: created synonym-tolerant audit for /workspace/stack-boundary.md and executing it.')
    print('Trial000108 stack-boundary audit')
    print(f'Artifact path: {ARTIFACT}')
    print(f'Target path:   {TARGET}')
    if not TARGET.exists():
        print('FAIL target file missing')
        append_note('Target markdown missing; exit 1.')
        return 1
    raw = TARGET.read_text(encoding='utf-8')
    checks = feature_checks(raw)
    print(f'Measured bytes: {len(raw.encode("utf-8"))}')
    print(f'Measured lines: {len(raw.splitlines())}')
    print()
    overall = True
    for name, ok, evidence in checks:
        print(('PASS ' if ok else 'FAIL ') + name)
        for item in evidence or ['<none found>']:
            print(f'  evidence: {item}')
        overall = overall and ok
    print()
    if overall:
        print('OVERALL PASS')
        append_note('Audit passed: all required report features detected.')
        return 0
    print('OVERALL FAIL')
    append_note('Audit failed: one or more features missing.')
    return 1


if __name__ == '__main__':
    sys.exit(main())

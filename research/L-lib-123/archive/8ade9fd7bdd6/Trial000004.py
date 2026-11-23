#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

ROOT_CANDIDATES = [Path('/workspace/repo'), Path('/workspace/reference'), Path('/workspace')]
TOKENS = ['FP3', 'L_lib_123', 'L_lib_122', 'SigmaV 3', 'DTIMEO']
WITNESS_PATTERNS = [
    re.compile(r'\btheorem\b[^\n]*\bFP3\b', re.IGNORECASE),
    re.compile(r'\baxiom\b[^\n]*\bFP3\b', re.IGNORECASE),
    re.compile(r'\bexample\b[^\n]*\bFP3\b', re.IGNORECASE),
    re.compile(r'∃\s*p\s*q[^\n]*FP3'),
    re.compile(r'exists\s+p\s+q[^\n]*FP3', re.IGNORECASE),
    re.compile(r'\bFP3\s+\d+\s+\d+'),
]
STRONGER_PATTERNS = [
    re.compile(r'∀\s*L[^\n]*DTIMEO[^\n]*SigmaV\s*3'),
    re.compile(r'\bSigmaV\s*3\b[^\n]*DTIMEO|\bDTIMEO\b[^\n]*\bSigmaV\s*3\b'),
]


def choose_root():
    for c in ROOT_CANDIDATES:
        if c.exists():
            return c
    return Path('/workspace')


def find_lean_files(root: Path):
    return sorted(p for p in root.rglob('*.lean') if p.is_file())


def scan_tokens(files):
    hits = {t: [] for t in TOKENS}
    witness_like = []
    stronger_like = []
    for path in files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for t in TOKENS:
                if t in line:
                    hits[t].append({'file': str(path), 'line_no': i, 'line': line.rstrip()})
            if any(p.search(line) for p in WITNESS_PATTERNS):
                witness_like.append({'file': str(path), 'line_no': i, 'line': line.rstrip()})
            if any(p.search(line) for p in STRONGER_PATTERNS):
                stronger_like.append({'file': str(path), 'line_no': i, 'line': line.rstrip()})
    return hits, witness_like, stronger_like


def check_stack_boundary(root: Path):
    candidates = [Path('/workspace/stack-boundary.md'), root / 'stack-boundary.md']
    seen = []
    for p in candidates:
        if p.exists() and p not in seen:
            seen.append(p)
    if not seen:
        return {'exists': False, 'path': None, 'contains_phrase': False, 'ends_with_phrase_context': False}
    p = seen[0]
    text = p.read_text(encoding='utf-8', errors='replace')
    contains = 'unresolved question' in text.lower()
    tail = '\n'.join(text.strip().splitlines()[-6:]).lower() if text.strip() else ''
    tail_ok = 'unresolved question' in tail
    return {'exists': True, 'path': str(p), 'contains_phrase': contains, 'ends_with_phrase_context': tail_ok}


def main():
    root = choose_root()
    files = find_lean_files(root)
    hits, witness_like, stronger_like = scan_tokens(files)
    stack = check_stack_boundary(root)

    print(f'Scanned root: {root}')
    print(f'Lean files scanned: {len(files)}')
    print('\nToken matches:')
    for t in TOKENS:
        print(f'== {t} ({len(hits[t])} matches) ==')
        for item in hits[t]:
            print(f"{item['file']}:{item['line_no']}: {item['line']}")
    print('\nWitness-like matches involving FP3/existence:')
    if witness_like:
        for item in witness_like:
            print(f"{item['file']}:{item['line_no']}: {item['line']}")
    else:
        print('ZERO MATCHES')
    print('\nPotential stronger reusable lines mentioning DTIMEO/SigmaV 3:')
    if stronger_like:
        for item in stronger_like:
            print(f"{item['file']}:{item['line_no']}: {item['line']}")
    else:
        print('ZERO MATCHES')
    print('\nstack-boundary.md status:')
    print(json.dumps(stack, indent=2))

    direct_witness = [x for x in witness_like if '∃' in x['line'] or 'exists' in x['line'].lower() or re.search(r'\bFP3\s+\d+\s+\d+', x['line'])]
    conclusion = {
        'root': str(root),
        'lean_files_scanned': len(files),
        'token_match_counts': {t: len(hits[t]) for t in TOKENS},
        'witness_like_count': len(witness_like),
        'direct_witness_count': len(direct_witness),
        'stronger_like_count': len(stronger_like),
        'stack_boundary_ok': bool(stack['exists'] and stack['contains_phrase']),
        'falsifiable_conclusion': (
            'No existing repository lemma text providing a direct existential FP3 witness was found; '
            'candidate strategy "solve by existing repository lemma" is textually blocked.'
            if len(direct_witness) == 0 else
            'At least one direct witness-like FP3 line was found; inspect reported lines.'
        ),
    }
    print('\nConclusion JSON:')
    print(json.dumps(conclusion, indent=2))

    failures = []
    if len(files) == 0:
        failures.append('No Lean files were scanned.')
    if not stack['exists']:
        failures.append('stack-boundary.md does not exist.')
    if not stack['contains_phrase']:
        failures.append('stack-boundary.md does not contain the phrase "unresolved question".')
    # Main falsifiable repository-audit check: zero direct witness-style theorem lines found.
    if len(direct_witness) != 0:
        failures.append(f'Expected zero direct FP3 witness-style matches, found {len(direct_witness)}.')

    print('\nFailures:')
    if failures:
        for f in failures:
            print('-', f)
        return 1
    print('None')
    return 0

if __name__ == '__main__':
    sys.exit(main())

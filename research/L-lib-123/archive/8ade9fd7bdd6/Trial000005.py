#!/usr/bin/env python3
import json
import os
import re
import sys
from pathlib import Path

CANDIDATE_ROOTS = [Path('/project'), Path('/workspace/reference'), Path('/workspace')]
TOKENS = ['FP3', 'L_lib_123', 'L_lib_122', 'SigmaV 3', 'DTIMEO']
WITNESS_PATTERNS = [
    re.compile(r'theorem\s+.*FP3'),
    re.compile(r'axiom\s+.*FP3'),
    re.compile(r'\bexample\b.*FP3'),
    re.compile(r'∃\s*p\s*q.*FP3'),
    re.compile(r'exists.*FP3', re.IGNORECASE),
]
DIRECT_PATTERNS = [
    re.compile(r'∃\s*p\s*q\s*:.*FP3'),
    re.compile(r'\bexists\b.*\bFP3\b', re.IGNORECASE),
    re.compile(r'\bFP3\s+\d+\s+\d+\b'),
]

def discover_root():
    findings = []
    for root in CANDIDATE_ROOTS:
        score = 0
        lake = list(root.rglob('lakefile.lean')) if root.exists() else []
        peq = list(root.rglob('PEqualNP')) if root.exists() else []
        lean_files = list(root.rglob('*.lean')) if root.exists() else []
        score += 100 * len(lake)
        score += 10 * sum(1 for p in peq if p.is_dir())
        score += len(lean_files)
        findings.append({
            'root': str(root),
            'exists': root.exists(),
            'lakefiles': [str(p) for p in lake[:10]],
            'peq_dirs': [str(p) for p in peq[:10]],
            'lean_file_count': len(lean_files),
            'score': score,
        })
    best = max(findings, key=lambda x: x['score'])
    return Path(best['root']), findings

def gather_lean_files(root: Path):
    files = []
    for p in root.rglob('*.lean'):
        if any(part in {'.lake', '.git', '__pycache__'} for part in p.parts):
            continue
        files.append(p)
    return sorted(files)

def scan_files(files):
    hits = {t: [] for t in TOKENS}
    witness_like = []
    direct = []
    stronger = []
    for path in files:
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            witness_like.append({'file': str(path), 'line_no': 0, 'line': f'<read error: {e}>'})
            continue
        for i, line in enumerate(text.splitlines(), start=1):
            for token in TOKENS:
                if token in line:
                    hits[token].append({'file': str(path), 'line_no': i, 'line': line.strip()})
            if 'FP3' in line and any(p.search(line) for p in WITNESS_PATTERNS):
                witness_like.append({'file': str(path), 'line_no': i, 'line': line.strip()})
            if 'FP3' in line and any(p.search(line) for p in DIRECT_PATTERNS):
                direct.append({'file': str(path), 'line_no': i, 'line': line.strip()})
            if ('SigmaV 3' in line or 'DTIMEO' in line or 'FP3' in line) and any(k in line for k in ['theorem', 'lemma', 'axiom', ':=']):
                stronger.append({'file': str(path), 'line_no': i, 'line': line.strip()})
    return hits, witness_like, direct, stronger

def find_stack_boundary(search_roots):
    candidates = []
    for root in search_roots:
        if root.exists():
            candidates.extend(root.rglob('stack-boundary.md'))
    seen = set()
    uniq = []
    for p in candidates:
        s = str(p)
        if s not in seen:
            seen.add(s)
            uniq.append(p)
    if not uniq:
        return {'exists': False, 'path': None, 'contains_phrase': False, 'context': None}
    best = uniq[0]
    text = best.read_text(encoding='utf-8', errors='replace')
    phrase = 'unresolved question'
    idx = text.lower().find(phrase)
    context = text[max(0, idx-80):idx+len(phrase)+80] if idx >= 0 else None
    return {'exists': True, 'path': str(best), 'contains_phrase': idx >= 0, 'context': context}

def print_matches(title, rows, limit=50):
    print(title)
    if not rows:
        print('ZERO MATCHES')
        return
    for row in rows[:limit]:
        print(f"{row['file']}:{row['line_no']}: {row['line']}")
    if len(rows) > limit:
        print(f'... truncated {len(rows)-limit} additional matches')

def main():
    chosen_root, findings = discover_root()
    files = gather_lean_files(chosen_root)
    hits, witness_like, direct, stronger = scan_files(files)
    stack = find_stack_boundary([Path('/workspace'), chosen_root])

    print('Discovery:')
    print(json.dumps({'chosen_root': str(chosen_root), 'candidates': findings}, indent=2))
    print(f'Lean files scanned in chosen root: {len(files)}')

    for token in TOKENS:
        print_matches(f'\n== {token} ({len(hits[token])} matches) ==', hits[token])

    print_matches('\nWitness-like matches involving FP3/existence:', witness_like)
    print_matches('\nDirect witness-style matches:', direct)
    print_matches('\nPotential stronger reusable lines:', stronger)

    print('\nstack-boundary.md status:')
    print(json.dumps(stack, indent=2))

    direct_witness_found = len(direct) > 0
    summary = {
        'chosen_root': str(chosen_root),
        'lean_files_scanned': len(files),
        'stack_boundary_ok': bool(stack['exists'] and stack['contains_phrase']),
        'direct_witness_found': direct_witness_found,
        'token_match_counts': {t: len(hits[t]) for t in TOKENS},
        'witness_like_count': len(witness_like),
        'direct_witness_count': len(direct),
    }
    print('\nSummary JSON:')
    print(json.dumps(summary, indent=2))

    failures = []
    if len(files) == 0:
        failures.append('No Lean files found in chosen root.')
    if not stack['exists']:
        failures.append('stack-boundary.md not found under /workspace or chosen root.')
    if not stack['contains_phrase']:
        failures.append('stack-boundary.md missing phrase "unresolved question".')

    print('\nFailures:')
    if failures:
        for f in failures:
            print('-', f)
        return 1
    print('None')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())

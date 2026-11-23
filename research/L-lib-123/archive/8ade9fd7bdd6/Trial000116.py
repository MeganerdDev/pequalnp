#!/usr/bin/env python3
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000116.py')
NOTES = Path('/workspace/notes.md')
ROOTS = [Path('/workspace'), Path('/')]
TARGET_NAMES = {'Defs.lean', 'L_lib_123.lean'}
PATH_TOKEN = 'PEqualNP'
MAX_PATH_HITS = 200
MAX_CONTEXTS_PER_FILE = 20
CONTEXT_RADIUS = 2
MAX_FILE_BYTES = 2_000_000
CLASSIFICATIONS = {
    'fp3_definition_found',
    'fp3_mentions_without_definition',
    'repo_found_but_no_fp3',
    'repo_not_found',
}


def append_note(line: str) -> None:
    try:
        with NOTES.open('a', encoding='utf-8') as f:
            f.write(line.rstrip() + '\n')
    except Exception:
        pass


def safe_read_text(path: Path):
    try:
        if path.stat().st_size > MAX_FILE_BYTES:
            return None, f'skipped_large_file>{MAX_FILE_BYTES}'
        return path.read_text(encoding='utf-8', errors='replace'), None
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def walk_roots(roots):
    exact_matches = {name: [] for name in TARGET_NAMES}
    pequalnp_paths = []
    lean_files = []
    walk_errors = []
    seen_dirs = set()
    for root in roots:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, onerror=None):
            if dirpath in seen_dirs:
                continue
            seen_dirs.add(dirpath)
            # prune some proc/sys noise
            if dirpath.startswith('/proc') or dirpath.startswith('/sys/devices'):
                dirnames[:] = []
            for fn in filenames:
                full = Path(dirpath) / fn
                if fn in TARGET_NAMES:
                    exact_matches[fn].append(str(full))
                if PATH_TOKEN in str(full):
                    if len(pequalnp_paths) < MAX_PATH_HITS:
                        pequalnp_paths.append(str(full))
                if full.suffix == '.lean':
                    lean_files.append(full)
    return exact_matches, pequalnp_paths, lean_files, walk_errors


def collect_context(lines, idx):
    start = max(0, idx - CONTEXT_RADIUS)
    end = min(len(lines), idx + CONTEXT_RADIUS + 1)
    out = []
    for i in range(start, end):
        out.append(f'{i+1}: {lines[i]}')
    return '\n'.join(out)


def scan_lean_files(lean_files):
    contexts = []
    theorem_hits = []
    fp3_line_hits = []
    definition_hits = []
    mention_files = set()
    read_errors = []
    definition_re = re.compile(r'\b(?:def|abbrev)\s+FP3\b')
    theorem_re = re.compile(r'\b(?:theorem|lemma)\b.*\b(?:Library\.)?FP3\b')
    fp3_12_re = re.compile(r'\bFP3\s+1\s+2\b')
    for path in lean_files:
        text, err = safe_read_text(path)
        if err:
            read_errors.append((str(path), err))
            continue
        if 'FP3' not in text:
            continue
        mention_files.add(str(path))
        lines = text.splitlines()
        per_file = 0
        for i, line in enumerate(lines):
            interesting = False
            label = None
            if definition_re.search(line):
                definition_hits.append((str(path), i + 1, line.strip()))
                interesting = True
                label = 'definition'
            elif theorem_re.search(line):
                theorem_hits.append((str(path), i + 1, line.strip()))
                interesting = True
                label = 'theorem_or_lemma'
            elif fp3_12_re.search(line):
                fp3_line_hits.append((str(path), i + 1, line.strip()))
                interesting = True
                label = 'fp3_1_2'
            elif 'Library.FP3' in line:
                interesting = True
                label = 'library_fp3_mention'
            if interesting and per_file < MAX_CONTEXTS_PER_FILE:
                contexts.append((str(path), label, collect_context(lines, i)))
                per_file += 1
    return {
        'contexts': contexts,
        'theorem_hits': theorem_hits,
        'fp3_line_hits': fp3_line_hits,
        'definition_hits': definition_hits,
        'mention_files': sorted(mention_files),
        'read_errors': read_errors,
    }


def classify(exact_matches, pequalnp_paths, scan):
    repo_found = bool(pequalnp_paths or exact_matches['Defs.lean'] or exact_matches['L_lib_123.lean'])
    has_def = bool(scan['definition_hits'])
    has_mentions = bool(scan['mention_files'])
    if has_def:
        return 'fp3_definition_found'
    if has_mentions:
        return 'fp3_mentions_without_definition'
    if repo_found:
        return 'repo_found_but_no_fp3'
    return 'repo_not_found'


def main() -> int:
    append_note('Trial000116: starting filesystem source-text audit for FP3/PEqualNP artifacts.')
    exact_matches, pequalnp_paths, lean_files, walk_errors = walk_roots(ROOTS)
    scan = scan_lean_files(lean_files)
    classification = classify(exact_matches, pequalnp_paths, scan)

    print('Trial000116 independent source-text FP3 audit')
    print(f'artifact: {ARTIFACT}')
    print(f'roots_scanned: {", ".join(str(r) for r in ROOTS)}')
    print(f'lean_file_count: {len(lean_files)}')
    print('')

    for name in sorted(TARGET_NAMES):
        vals = sorted(set(exact_matches[name]))
        print(f'exact_path_matches[{name}]:')
        print('\n'.join(vals) if vals else '<none>')
        print('')

    print(f'paths_containing_{PATH_TOKEN} (up to {MAX_PATH_HITS}):')
    print('\n'.join(sorted(set(pequalnp_paths))) if pequalnp_paths else '<none>')
    print('')

    print('lean_files_with_any_FP3:')
    print('\n'.join(scan['mention_files']) if scan['mention_files'] else '<none>')
    print('')

    print('context_hits:')
    if scan['contexts']:
        for path, label, ctx in scan['contexts']:
            print(f'--- {path} [{label}] ---')
            print(ctx)
    else:
        print('<none>')
    print('')

    print('definition_hits:')
    if scan['definition_hits']:
        for p, ln, line in scan['definition_hits']:
            print(f'{p}:{ln}: {line}')
    else:
        print('<none>')
    print('')

    print('theorem_or_lemma_hits:')
    if scan['theorem_hits']:
        for p, ln, line in scan['theorem_hits']:
            print(f'{p}:{ln}: {line}')
    else:
        print('<none>')
    print('')

    print('fp3_1_2_hits:')
    if scan['fp3_line_hits']:
        for p, ln, line in scan['fp3_line_hits']:
            print(f'{p}:{ln}: {line}')
    else:
        print('<none>')
    print('')

    checks = [
        ('classification_valid', classification in CLASSIFICATIONS),
        ('reported_exact_matches', True),
        ('reported_pequalnp_paths', True),
        ('reported_contexts', True),
    ]
    for name, ok in checks:
        print(f'check {name}: {"PASS" if ok else "FAIL"}')
    print(f'classification: {classification}')

    append_note(
        f'Trial000116 classification={classification}, lean_files={len(lean_files)}, '
        f'pequalnp_paths={len(set(pequalnp_paths))}, fp3_files={len(scan["mention_files"])}, '
        f'definition_hits={len(scan["definition_hits"])}, theorem_hits={len(scan["theorem_hits"])}, '
        f'fp3_1_2_hits={len(scan["fp3_line_hits"])}'
    )
    return 0 if classification in CLASSIFICATIONS else 1


if __name__ == '__main__':
    sys.exit(main())

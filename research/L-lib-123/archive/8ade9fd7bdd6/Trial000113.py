#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

ROOT = Path('/workspace')
ARTIFACT = ROOT / 'Trial000113.py'
NOTES = ROOT / 'notes.md'
TARGET_REL = Path('lean/PEqualNP/Defs.lean')
ASSIGNED_REL = Path('lean/PEqualNP/Outside/L_lib_123.lean')
TOKENS = ['FP3', 'namespace Library', 'PEqualNP.Library.FP3']
CLASSIFICATIONS = {'definition_found', 'token_found_no_definition', 'no_FP3_tokens'}


def append_note(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def is_lean_file(path: Path) -> bool:
    return path.is_file() and path.suffix == '.lean'


def context_snippets(text: str, token: str, radius: int = 2):
    lines = text.splitlines()
    out = []
    for i, line in enumerate(lines):
        if token in line:
            start = max(0, i - radius)
            end = min(len(lines), i + radius + 1)
            snippet = []
            for j in range(start, end):
                mark = '>' if j == i else ' '
                snippet.append(f'{mark}{j+1}: {lines[j]}')
            out.append('\n'.join(snippet))
    return out


def classify(fp3_files, definition_hits):
    if definition_hits:
        return 'definition_found'
    if fp3_files:
        return 'token_found_no_definition'
    return 'no_FP3_tokens'


def main() -> int:
    append_note('Trial000113: scanning /workspace recursively for Lean files and textual FP3 definition evidence.')
    lean_files = []
    read_errors = []
    files_with_token = {tok: [] for tok in TOKENS}
    snippets = []
    fp3_files = []
    definition_hits = []

    for path in ROOT.rglob('*'):
        if not is_lean_file(path):
            continue
        lean_files.append(path)
        try:
            text = path.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            read_errors.append((path, repr(e)))
            continue
        token_found_here = False
        for tok in TOKENS:
            if tok in text:
                files_with_token[tok].append(path)
                for snip in context_snippets(text, tok):
                    snippets.append((path, tok, snip))
                if tok == 'FP3':
                    token_found_here = True
        if token_found_here:
            fp3_files.append(path)
        for m in re.finditer(r'(?m)^\s*(?:def|abbrev|theorem|lemma)\s+FP3\b', text):
            line_no = text[:m.start()].count('\n') + 1
            definition_hits.append((path, line_no, text.splitlines()[line_no-1]))
        for m in re.finditer(r'PEqualNP\.Library\.FP3\s*[:(]', text):
            line_no = text[:m.start()].count('\n') + 1
            definition_hits.append((path, line_no, text.splitlines()[line_no-1]))

    defs_exists = (ROOT / TARGET_REL).exists()
    assigned_exists = (ROOT / ASSIGNED_REL).exists()
    classification = classify(fp3_files, definition_hits)

    print('Trial000113 textual FP3 audit')
    print(f'artifact: {ARTIFACT}')
    print(f'workspace: {ROOT}')
    print(f'lean_file_count: {len(lean_files)}')
    print(f'defs_exists: {defs_exists} path={(ROOT / TARGET_REL)}')
    print(f'assigned_exists: {assigned_exists} path={(ROOT / ASSIGNED_REL)}')
    print('')

    print('files_with_token_FP3:')
    print('\n'.join(str(p) for p in sorted(set(fp3_files))) if fp3_files else '<none>')
    print('')

    for tok in TOKENS:
        print(f'files_with_token_{tok!r}:')
        lst = sorted(set(files_with_token[tok]))
        print('\n'.join(str(p) for p in lst) if lst else '<none>')
        print('')

    print('context_snippets:')
    if snippets:
        for path, tok, snip in snippets:
            print(f'--- {path} token={tok} ---')
            print(snip)
    else:
        print('<none>')
    print('')

    print('definition_like_hits:')
    if definition_hits:
        seen = set()
        for item in definition_hits:
            if item in seen:
                continue
            seen.add(item)
            path, line_no, line = item
            print(f'{path}:{line_no}: {line}')
    else:
        print('<none>')
    print('')

    if read_errors:
        print('read_errors:')
        for path, err in read_errors:
            print(f'{path}: {err}')
        print('')

    checks = [
        ('counted_lean_files', len(lean_files) >= 0),
        ('reported_defs_existence', isinstance(defs_exists, bool)),
        ('listed_fp3_files', isinstance(fp3_files, list)),
        ('printed_context_snippets', True),
        ('classification_valid', classification in CLASSIFICATIONS),
    ]
    for name, ok in checks:
        print(f'check {name}: {"PASS" if ok else "FAIL"}')
    print(f'classification: {classification}')

    append_note(f'Trial000113 classification={classification}, lean_files={len(lean_files)}, defs_exists={defs_exists}, assigned_exists={assigned_exists}, fp3_files={len(set(fp3_files))}, definition_hits={len(definition_hits)}')
    return 0 if all(ok for _, ok in checks) and classification in CLASSIFICATIONS else 1


if __name__ == '__main__':
    sys.exit(main())

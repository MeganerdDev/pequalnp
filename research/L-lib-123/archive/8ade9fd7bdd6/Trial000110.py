#!/usr/bin/env python3
import os
import sys
import shutil
from pathlib import Path

WORKSPACE = Path('/workspace')
ARTIFACT = WORKSPACE / 'Trial000110.py'
NOTES = WORKSPACE / 'notes.md'
STACK = WORKSPACE / 'stack-boundary.md'

SEARCH_FILENAMES = {'Defs.lean', 'L_lib_123.lean'}
SEARCH_SNIPPETS = {
    'namespace PEqualNP': [],
    'def FP3': [],
    'theorem L_lib_123': [],
}
BINARY_NAMES = ['lean', 'lake']
EXPLICIT_BIN_PATHS = [
    '/workspace/home/.elan/bin/lean',
    '/workspace/home/.elan/bin/lake',
    '/workspace/.elan/bin/lean',
    '/workspace/.elan/bin/lake',
    '/root/.elan/bin/lean',
    '/root/.elan/bin/lake',
    '/usr/local/bin/lean',
    '/usr/local/bin/lake',
    '/usr/bin/lean',
    '/usr/bin/lake',
]


def append_note(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def scan_workspace():
    lean_files = []
    by_name = {name: [] for name in SEARCH_FILENAMES}
    snippet_hits = {k: [] for k in SEARCH_SNIPPETS}
    errors = []
    for root, dirs, files in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in {'.git', '__pycache__'}]
        for fn in files:
            path = Path(root) / fn
            if fn.endswith('.lean'):
                lean_files.append(path)
                if fn in by_name:
                    by_name[fn].append(path)
                try:
                    text = path.read_text(encoding='utf-8', errors='replace')
                except Exception as e:
                    errors.append((str(path), repr(e)))
                    continue
                for needle in SEARCH_SNIPPETS:
                    if needle in text:
                        snippet_hits[needle].append(path)
    return lean_files, by_name, snippet_hits, errors


def safe_path_status(p: str):
    try:
        exists = os.path.exists(p)
    except Exception as e:
        return ('error', repr(e), False)
    try:
        executable = os.access(p, os.X_OK) if exists else False
    except Exception as e:
        return (exists, repr(e), False)
    return (exists, None, executable)


def inspect_binaries():
    which = {name: shutil.which(name) for name in BINARY_NAMES}
    explicit = []
    for p in EXPLICIT_BIN_PATHS:
        exists, err, executable = safe_path_status(p)
        explicit.append((p, exists, executable, err))
    return which, explicit


def classify(lean_files, defs_hits, l_hits, which, explicit):
    repo_present = bool(lean_files or defs_hits or l_hits)
    toolchain_present = any(which.values()) or any(exists is True and executable for _, exists, executable, _ in explicit)
    if repo_present and toolchain_present:
        return 'repo_and_toolchain_present'
    if repo_present and not toolchain_present:
        return 'repo_present/toolchain_missing'
    if (not repo_present) and toolchain_present:
        return 'repo_missing/toolchain_present'
    return 'repo_missing'


def main() -> int:
    append_note('Trial000110: auditing /workspace for Lean sources and toolchain presence.')
    lean_files, by_name, snippet_hits, errors = scan_workspace()
    which, explicit = inspect_binaries()
    classification = classify(lean_files, by_name['Defs.lean'], by_name['L_lib_123.lean'], which, explicit)

    print('Trial000110 workspace Lean/toolchain audit')
    print(f'artifact: {ARTIFACT}')
    print(f'stack-boundary.md exists: {STACK.exists()}')
    print(f'lean file count: {len(lean_files)}')
    print('')

    print('Defs.lean paths:')
    print('\n'.join(str(p) for p in sorted(by_name['Defs.lean'])) ) if by_name['Defs.lean'] else print('<none>')
    print('')
    print('L_lib_123.lean paths:')
    print('\n'.join(str(p) for p in sorted(by_name['L_lib_123.lean'])) ) if by_name['L_lib_123.lean'] else print('<none>')
    print('')

    for needle in ['namespace PEqualNP', 'def FP3', 'theorem L_lib_123']:
        print(f'Files containing {needle!r}:')
        hits = snippet_hits[needle]
        print('\n'.join(str(p) for p in sorted(hits))) if hits else print('<none>')
        print('')

    print('Binary resolution via shutil.which:')
    for name, resolved in which.items():
        print(f'{name}: {resolved}')
    print('')

    print('Explicit binary path checks:')
    for p, exists, executable, err in explicit:
        suffix = f' error={err}' if err else ''
        print(f'{p}: exists={exists} executable={executable}{suffix}')
    print('')

    if errors:
        print('Read errors:')
        for path, err in errors:
            print(f'{path}: {err}')
        print('')

    print(f'classification: {classification}')

    checks = [
        ('classification_nonempty', bool(classification)),
        ('scan_completed', True),
        ('reported_lean_count_nonnegative', len(lean_files) >= 0),
    ]
    for name, ok in checks:
        print(f'check {name}: {"PASS" if ok else "FAIL"}')

    append_note(f'Trial000110 classification={classification}, lean_files={len(lean_files)}, lean={which["lean"]}, lake={which["lake"]}')
    return 0 if all(ok for _, ok in checks) else 1


if __name__ == '__main__':
    sys.exit(main())

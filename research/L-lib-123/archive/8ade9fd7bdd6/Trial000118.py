#!/usr/bin/env python3
import hashlib
import os
import sys
from collections import defaultdict
from pathlib import Path

ROOTS = [Path('/workspace'), Path('/'), Path('/tmp'), Path('/home')]
TARGET_BASENAMES = ['L_lib_123.lean', 'Defs.lean', 'stack-boundary.md']
TARGET_SUFFIXES = [
    'lean/PEqualNP/Outside/L_lib_123.lean',
    'PEqualNP/Defs.lean',
]
CLASSIFICATIONS = {'targets_visible', 'repo_visible_targets_missing', 'repo_not_visible'}
MAX_HITS_PER_GROUP = 20
MAX_LEAN_PER_ROOT = 20
MAX_FIRST_LINES = 5


def append_note(msg: str) -> None:
    with open('/workspace/notes.md', 'a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def first_lines(path: Path, n: int = MAX_FIRST_LINES):
    lines = []
    with open(path, 'r', encoding='utf-8', errors='replace') as f:
        for _ in range(n):
            line = f.readline()
            if not line:
                break
            lines.append(line.rstrip('\n'))
    return lines


def scan_root(root: Path):
    result = {
        'readable': False,
        'lean_files': [],
        'basename_hits': defaultdict(list),
        'suffix_hits': defaultdict(list),
        'errors': [],
    }
    seen_dirs = set()
    seen_files = set()
    stack = [root]
    while stack:
        cur = stack.pop()
        try:
            st = cur.stat(follow_symlinks=True)
        except Exception as e:
            result['errors'].append((str(cur), f'stat_failed: {e}'))
            continue
        dir_key = (st.st_dev, st.st_ino)
        if dir_key in seen_dirs:
            continue
        seen_dirs.add(dir_key)
        try:
            entries = list(cur.iterdir())
            result['readable'] = True
        except Exception as e:
            result['errors'].append((str(cur), f'iterdir_failed: {e}'))
            continue
        for entry in entries:
            try:
                if entry.is_dir():
                    stack.append(entry)
                    continue
                if not entry.is_file():
                    continue
                fst = entry.stat(follow_symlinks=True)
                fkey = (fst.st_dev, fst.st_ino)
                if fkey in seen_files:
                    continue
                seen_files.add(fkey)
                abs_path = str(entry.resolve())
                name = entry.name
                if name in TARGET_BASENAMES:
                    result['basename_hits'][name].append(abs_path)
                norm = abs_path.replace('\\', '/')
                for suf in TARGET_SUFFIXES:
                    if norm.endswith(suf):
                        result['suffix_hits'][suf].append(abs_path)
                if entry.suffix == '.lean':
                    result['lean_files'].append(abs_path)
            except Exception as e:
                result['errors'].append((str(entry), f'entry_failed: {e}'))
    return result


def report_file(path_str: str):
    p = Path(path_str)
    size = p.stat().st_size
    sha = file_sha256(p)
    lines = first_lines(p)
    print(f'path: {path_str}')
    print(f'  size: {size}')
    print(f'  sha256: {sha}')
    print('  first_5_lines:')
    if lines:
        for line in lines:
            print(f'    {line}')
    else:
        print('    <empty>')


def main() -> int:
    append_note('Trial000118: starting symlink-aware filesystem audit for requested targets and lean source counts.')
    per_root = {}
    all_lean = set()
    all_target_hits = set()
    for root in ROOTS:
        per_root[str(root)] = scan_root(root)
        all_lean.update(per_root[str(root)]['lean_files'])
        for name in TARGET_BASENAMES:
            all_target_hits.update(per_root[str(root)]['basename_hits'].get(name, []))
        for suf in TARGET_SUFFIXES:
            all_target_hits.update(per_root[str(root)]['suffix_hits'].get(suf, []))

    repo_visible = any(per_root[str(root)]['lean_files'] for root in ROOTS)
    targets_visible = bool(all_target_hits)
    if targets_visible:
        classification = 'targets_visible'
    elif repo_visible:
        classification = 'repo_visible_targets_missing'
    else:
        classification = 'repo_not_visible'

    print('Trial000118 symlink-aware filesystem audit')
    print('artifact: /workspace/Trial000118.py')
    print('roots_scanned: ' + ', '.join(str(r) for r in ROOTS))
    print('')

    for root in ROOTS:
        info = per_root[str(root)]
        lean_sorted = sorted(set(info['lean_files']))
        print(f'root: {root}')
        print(f'  readable: {info["readable"]}')
        print(f'  lean_file_count: {len(lean_sorted)}')
        print(f'  sample_lean_files_up_to_{MAX_LEAN_PER_ROOT}:')
        if lean_sorted:
            for p in lean_sorted[:MAX_LEAN_PER_ROOT]:
                print(f'    {p}')
        else:
            print('    <none>')
        print('')

    for name in TARGET_BASENAMES:
        hits = sorted(set(p for info in per_root.values() for p in info['basename_hits'].get(name, [])))
        print(f'exact_basename_hits[{name}]:')
        if hits:
            for p in hits[:MAX_HITS_PER_GROUP]:
                report_file(p)
        else:
            print('<none>')
        print('')

    for suf in TARGET_SUFFIXES:
        hits = sorted(set(p for info in per_root.values() for p in info['suffix_hits'].get(suf, [])))
        print(f'suffix_hits[{suf}]:')
        if hits:
            for p in hits[:MAX_HITS_PER_GROUP]:
                report_file(p)
        else:
            print('<none>')
        print('')

    print(f'total_unique_lean_files: {len(all_lean)}')
    print(f'total_unique_target_hits: {len(all_target_hits)}')
    print(f'classification: {classification}')

    valid = classification in CLASSIFICATIONS
    print(f'check classification_valid: {"PASS" if valid else "FAIL"}')

    append_note(
        f'Trial000118 classification={classification}, total_unique_lean_files={len(all_lean)}, '
        f'total_unique_target_hits={len(all_target_hits)}'
    )
    return 0 if valid else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
import ast
import hashlib
import os
import re
import stat
import sys
from collections import defaultdict
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000119.py')
NOTES = Path('/workspace/notes.md')
ROOTS = [Path('/workspace'), Path('/root'), Path('/home'), Path('/tmp'), Path('/proc')]
TARGET_BASENAMES = {'L_lib_123.lean', 'Defs.lean', 'stack-boundary.md'}
TEXT_TOKENS = ['PEqualNP', 'FP3', 'lean_files=1177', 'classification=targets_visible']
PRIOR_ARTIFACTS = [Path('/workspace/Trial000116.py'), Path('/workspace/Trial000118.py')]
CLASSIFICATIONS = {
    'environment_consistent_repo_visible',
    'environment_consistent_repo_absent',
    'environment_inconsistent_artifacts',
}
MAX_TOP = 20
MAX_HITS = 200
MAX_WALK_DIRS = 5000
MAX_WALK_FILES = 50000
MAX_READ = 200000


def append_note(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def safe_listdir(path: Path):
    try:
        entries = sorted(os.listdir(path))
        return True, entries, None
    except Exception as e:
        return False, [], f'{type(e).__name__}: {e}'


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8', 'replace')).hexdigest()


def inspect_root(root: Path):
    info = {
        'exists': root.exists(),
        'readable': os.access(root, os.R_OK | os.X_OK),
        'top_entries': [],
        'top_error': None,
        'lean_count': 0,
        'basename_hits': defaultdict(list),
        'token_hits': defaultdict(list),
        'walk_dirs': 0,
        'walk_files': 0,
        'walk_error': None,
    }
    ok, entries, err = safe_listdir(root)
    if ok:
        info['top_entries'] = entries[:MAX_TOP]
    else:
        info['top_error'] = err
    if not info['exists'] or not info['readable']:
        return info

    visited = set()
    try:
        for dirpath, dirnames, filenames in os.walk(root, topdown=True, followlinks=False):
            info['walk_dirs'] += 1
            if info['walk_dirs'] > MAX_WALK_DIRS or info['walk_files'] > MAX_WALK_FILES:
                dirnames[:] = []
                break
            try:
                st = os.stat(dirpath, follow_symlinks=False)
                key = (st.st_dev, st.st_ino)
                if key in visited:
                    dirnames[:] = []
                    continue
                visited.add(key)
            except Exception:
                pass
            pruned = []
            for d in dirnames:
                full = os.path.join(dirpath, d)
                if full.startswith('/proc/'):
                    pruned.append(d)
                elif d in {'.git', '__pycache__'}:
                    pruned.append(d)
            if pruned:
                dirnames[:] = [d for d in dirnames if d not in pruned]
            for name in filenames:
                info['walk_files'] += 1
                if info['walk_files'] > MAX_WALK_FILES:
                    break
                full = os.path.join(dirpath, name)
                if name.endswith('.lean'):
                    info['lean_count'] += 1
                if name in TARGET_BASENAMES:
                    info['basename_hits'][name].append(full)
                if name.endswith(('.py', '.lean', '.md', '.txt')) or name in TARGET_BASENAMES:
                    try:
                        with open(full, 'r', encoding='utf-8', errors='replace') as f:
                            text = f.read(MAX_READ)
                        for tok in TEXT_TOKENS:
                            if tok in text:
                                info['token_hits'][tok].append(full)
                    except Exception:
                        pass
            if info['walk_files'] > MAX_WALK_FILES:
                break
    except Exception as e:
        info['walk_error'] = f'{type(e).__name__}: {e}'
    return info


def inspect_prior_script(path: Path):
    result = {
        'exists': path.exists(),
        'size': None,
        'sha256': None,
        'contains_suspicious_strings': [],
        'computes_via_os_walk': False,
        'contains_literal_assignment': False,
        'classification_literals': [],
        'preview': [],
    }
    if not path.exists():
        return result
    text = path.read_text(encoding='utf-8', errors='replace')
    result['size'] = len(text)
    result['sha256'] = sha256_text(text)
    result['preview'] = text.splitlines()[:10]
    suspicious = ['lean_files=1177', 'classification=targets_visible', 'classification=repo_present/toolchain_missing']
    result['contains_suspicious_strings'] = [s for s in suspicious if s in text]
    result['computes_via_os_walk'] = ('os.walk' in text) or ('Path.rglob' in text)
    result['contains_literal_assignment'] = bool(re.search(r'lean_files\s*=\s*1177', text)) or bool(re.search(r'classification\s*=\s*[\'\"]targets_visible[\'\"]', text))
    result['classification_literals'] = sorted(set(re.findall(r'[\'\"](targets_visible|repo_not_visible|fp3_definition_found|repo_not_found|repo_visible_targets_missing)[\'\"]', text)))
    return result


def main() -> int:
    append_note('Trial000119: starting independent environment audit and prior-artifact source inspection.')
    print('Trial000119 independent environment audit')
    print(f'artifact: {ARTIFACT}')
    print(f'cwd: {os.getcwd()}')
    print(f'uid: {os.getuid()} euid: {os.geteuid()} gid: {os.getgid()}')
    for key in ['HOME', 'PWD', 'USER', 'LOGNAME', 'PYTHONPATH', 'PATH']:
        print(f'env[{key}]={os.environ.get(key)}')
    print('')

    root_listing_ok, root_listing, root_err = safe_listdir(Path('/'))
    print('listdir[/]:')
    if root_listing_ok:
        for x in root_listing[:MAX_TOP]:
            print(f'  {x}')
    else:
        print(f'  <error: {root_err}>')
    print('')

    mount_ok, mount_entries, mount_err = safe_listdir(Path('/proc'))
    print('listdir[/proc]:')
    if mount_ok:
        for x in mount_entries[:MAX_TOP]:
            print(f'  {x}')
    else:
        print(f'  <error: {mount_err}>')
    print('')

    per_root = {str(r): inspect_root(r) for r in ROOTS}
    total_lean = sum(info['lean_count'] for info in per_root.values())
    all_target_hits = sorted({p for info in per_root.values() for hits in info['basename_hits'].values() for p in hits})

    for root in ROOTS:
        info = per_root[str(root)]
        print(f'root: {root}')
        print(f'  exists: {info["exists"]}')
        print(f'  readable: {info["readable"]}')
        print(f'  walk_dirs: {info["walk_dirs"]}')
        print(f'  walk_files: {info["walk_files"]}')
        print(f'  lean_count: {info["lean_count"]}')
        print('  top_entries:')
        if info['top_entries']:
            for x in info['top_entries']:
                print(f'    {x}')
        elif info['top_error']:
            print(f'    <error: {info["top_error"]}>')
        else:
            print('    <none>')
        if info['walk_error']:
            print(f'  walk_error: {info["walk_error"]}')
        print('')

    for name in sorted(TARGET_BASENAMES):
        print(f'exact_hits[{name}]:')
        hits = []
        for info in per_root.values():
            hits.extend(info['basename_hits'].get(name, []))
        hits = sorted(set(hits))
        if hits:
            for p in hits[:MAX_HITS]:
                print(f'  {p}')
        else:
            print('  <none>')
        print('')

    for tok in TEXT_TOKENS:
        print(f'token_hits[{tok}]:')
        hits = []
        for info in per_root.values():
            hits.extend(info['token_hits'].get(tok, []))
        hits = sorted(set(hits))
        if hits:
            for p in hits[:MAX_HITS]:
                print(f'  {p}')
        else:
            print('  <none>')
        print('')

    suspicious_prior = False
    for path in PRIOR_ARTIFACTS:
        meta = inspect_prior_script(path)
        print(f'prior_artifact: {path}')
        print(f'  exists: {meta["exists"]}')
        if meta['exists']:
            print(f'  size: {meta["size"]}')
            print(f'  sha256: {meta["sha256"]}')
            print(f'  computes_via_os_walk: {meta["computes_via_os_walk"]}')
            print(f'  contains_literal_assignment: {meta["contains_literal_assignment"]}')
            print(f'  contains_suspicious_strings: {meta["contains_suspicious_strings"]}')
            print(f'  classification_literals: {meta["classification_literals"]}')
            if meta['contains_suspicious_strings']:
                suspicious_prior = True
            print('  preview:')
            for line in meta['preview']:
                print(f'    {line}')
        print('')

    repo_visible_now = total_lean > 0 or any(all_target_hits)
    if not repo_visible_now and suspicious_prior:
        classification = 'environment_inconsistent_artifacts'
    elif repo_visible_now:
        classification = 'environment_consistent_repo_visible'
    else:
        classification = 'environment_consistent_repo_absent'

    print(f'total_lean_files_counted: {total_lean}')
    print(f'total_exact_target_hits: {len(all_target_hits)}')
    print(f'classification: {classification}')
    valid = classification in CLASSIFICATIONS
    print(f'check classification_valid: {"PASS" if valid else "FAIL"}')
    append_note(f'Trial000119 classification={classification}, total_lean={total_lean}, suspicious_prior={suspicious_prior}, target_hits={len(all_target_hits)}')
    return 0 if valid else 1


if __name__ == '__main__':
    sys.exit(main())

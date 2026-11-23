#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from collections import defaultdict

ARTIFACT = Path('/workspace/Trial000114.py')
NOTES = Path('/workspace/notes.md')
ROOTS = [Path('/workspace'), Path('/'), Path('/root'), Path('/tmp')]
TARGET_NAMES = {'Defs.lean', 'L_lib_123.lean', 'stack-boundary.md'}
PATH_TOKEN = 'PEqualNP'
CONTENT_TOKENS = ['def FP3', 'abbrev FP3', 'PEqualNP.Library.FP3']
CLASSIFICATIONS = {
    'repo_visible_under_workspace',
    'repo_visible_outside_workspace',
    'no_repo_visible',
    'evidence_conflict',
}
MAX_PATH_HITS = 50
MAX_CONTEXT_HITS = 40
CONTEXT_RADIUS = 2
SKIP_DIR_NAMES = {'proc', 'sys', 'dev', 'run'}


def append_note(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def scan_root(root: Path):
    result = {
        'root': str(root),
        'readable': False,
        'lean_files': [],
        'name_matches': defaultdict(list),
        'pequalnp_paths': [],
        'candidate_sources': set(),
        'read_errors': [],
    }
    try:
        if not root.exists():
            return result
        list(root.iterdir())
        result['readable'] = True
    except Exception as e:
        result['read_errors'].append((str(root), f'root_unreadable: {e}'))
        return result

    stack = [root]
    seen = set()
    while stack:
        cur = stack.pop()
        try:
            st = cur.stat(follow_symlinks=False)
        except Exception as e:
            result['read_errors'].append((str(cur), f'stat_failed: {e}'))
            continue
        key = (st.st_dev, st.st_ino)
        if key in seen:
            continue
        seen.add(key)

        try:
            is_dir = os.path.isdir(cur)
        except Exception as e:
            result['read_errors'].append((str(cur), f'isdir_failed: {e}'))
            continue

        if is_dir:
            if str(root) == '/' and cur != root and cur.parent == root and cur.name in SKIP_DIR_NAMES:
                continue
            try:
                for child in cur.iterdir():
                    stack.append(child)
            except Exception as e:
                result['read_errors'].append((str(cur), f'iterdir_failed: {e}'))
            continue

        name = cur.name
        if name in TARGET_NAMES:
            result['name_matches'][name].append(str(cur))
            if name.endswith('.lean'):
                result['candidate_sources'].add(str(cur))
        if cur.suffix == '.lean':
            result['lean_files'].append(str(cur))
            result['candidate_sources'].add(str(cur))
        cur_str = str(cur)
        if PATH_TOKEN in cur_str and len(result['pequalnp_paths']) < MAX_PATH_HITS:
            result['pequalnp_paths'].append(cur_str)
            if cur.suffix == '.lean':
                result['candidate_sources'].add(cur_str)
    return result


def search_contents(paths):
    hits = []
    unreadable = []
    for p in sorted(set(paths)):
        try:
            text = Path(p).read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            unreadable.append((p, str(e)))
            continue
        lines = text.splitlines()
        for i, line in enumerate(lines, start=1):
            for tok in CONTENT_TOKENS:
                if tok in line:
                    lo = max(1, i - CONTEXT_RADIUS)
                    hi = min(len(lines), i + CONTEXT_RADIUS)
                    snippet = '\n'.join(f'{j}: {lines[j-1]}' for j in range(lo, hi + 1))
                    hits.append((p, tok, i, snippet))
                    if len(hits) >= MAX_CONTEXT_HITS:
                        return hits, unreadable
    return hits, unreadable


def classify(per_root, content_hits):
    workspace_lean = len(per_root['/workspace']['lean_files'])
    outside_lean = sum(len(v['lean_files']) for k, v in per_root.items() if k != '/workspace')
    any_readable = any(v['readable'] for v in per_root.values())
    any_name_match = any(any(v['name_matches'][nm] for nm in TARGET_NAMES) for v in per_root.values())
    any_path_hits = any(v['pequalnp_paths'] for v in per_root.values())
    content_paths = {h[0] for h in content_hits}

    if (workspace_lean > 0 and not per_root['/workspace']['readable']) or ((any_name_match or any_path_hits or content_paths) and not any_readable):
        return 'evidence_conflict'
    if workspace_lean > 0 or any(p.startswith('/workspace/') or p == '/workspace' for p in content_paths):
        return 'repo_visible_under_workspace'
    if outside_lean > 0 or any_name_match or any_path_hits or content_paths:
        return 'repo_visible_outside_workspace'
    if any_readable:
        return 'no_repo_visible'
    return 'evidence_conflict'


def main():
    append_note('Trial000114: starting independent filesystem census across /workspace, /, /root, /tmp.')
    per_root = {}
    for root in ROOTS:
        per_root[str(root)] = scan_root(root)

    all_candidate_sources = set()
    all_name_matches = defaultdict(list)
    all_pequalnp = []
    read_errors = []
    for info in per_root.values():
        all_candidate_sources.update(info['candidate_sources'])
        for k, vals in info['name_matches'].items():
            all_name_matches[k].extend(vals)
        all_pequalnp.extend(info['pequalnp_paths'])
        read_errors.extend(info['read_errors'])

    content_hits, unreadable_sources = search_contents(all_candidate_sources)
    classification = classify(per_root, content_hits)

    print('Trial000114 independent workspace census')
    print(f'artifact: {ARTIFACT}')
    print('')
    for root in [str(r) for r in ROOTS]:
        info = per_root[root]
        print(f'root: {root}')
        print(f'  readable: {info["readable"]}')
        print(f'  lean_file_count: {len(info["lean_files"])}')
        print('')

    for name in sorted(TARGET_NAMES):
        matches = sorted(set(all_name_matches[name]))
        print(f'exact_name_matches[{name}]:')
        print('\n'.join(matches) if matches else '<none>')
        print('')

    print(f'paths_containing_{PATH_TOKEN} (up to {MAX_PATH_HITS}):')
    uniq_pequalnp = []
    seen = set()
    for p in all_pequalnp:
        if p not in seen:
            seen.add(p)
            uniq_pequalnp.append(p)
    print('\n'.join(uniq_pequalnp[:MAX_PATH_HITS]) if uniq_pequalnp else '<none>')
    print('')

    print('content_hits_for_FP3_tokens:')
    if content_hits:
        for p, tok, line_no, snippet in content_hits:
            print(f'--- {p} :: {tok} @ line {line_no} ---')
            print(snippet)
    else:
        print('<none>')
    print('')

    if read_errors or unreadable_sources:
        print('read_errors:')
        for p, err in read_errors[:100]:
            print(f'{p}: {err}')
        for p, err in unreadable_sources[:100]:
            print(f'{p}: content_read_failed: {err}')
        print('')

    valid_classification = classification in CLASSIFICATIONS
    print(f'classification: {classification}')
    print(f'check classification_valid: {"PASS" if valid_classification else "FAIL"}')

    append_note(
        f'Trial000114 classification={classification}, '
        f'workspace_lean={len(per_root["/workspace"]["lean_files"])}, '
        f'root_lean={len(per_root["/"]["lean_files"])}, '
        f'root_hits={len(uniq_pequalnp)}, content_hits={len(content_hits)}'
    )
    return 0 if valid_classification else 1


if __name__ == '__main__':
    sys.exit(main())

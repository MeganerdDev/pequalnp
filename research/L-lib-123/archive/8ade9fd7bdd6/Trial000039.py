#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ARTIFACT = Path('/workspace/Trial000039.py')
REPORT = Path('/workspace/fp3-live-audit.md')
NOTES = Path('/workspace/notes.md')
TARGET_REL = Path('PEqualNP/Defs.lean')
HELPER = Path('/workspace/Helper000038.lean')
REQUIRED_SECTIONS = [
    'Definition of FP3',
    'All FP3 mentions',
    'Exact instance mentions',
    'Potential bridge declarations',
    'Verbatim unfolding audit',
]
BRIDGE_TOKENS = [
    'SigmaV 3', 'DTIMEO', 'mono', 'monot', 'subset', 'example', 'instance', 'theorem', 'lemma'
]
DECL_PREFIXES = ('def ', 'abbrev ', 'theorem ', 'lemma ', 'example ', 'instance ', 'axiom ', 'opaque ', 'structure ', 'class ', 'inductive ')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def candidate_roots() -> List[Path]:
    bases = [Path('/workspace'), Path('/workspace/repo'), Path('/workspace/reference'), Path('/workspace/project'), Path('/project')]
    out: List[Path] = []
    for b in bases:
        if b.exists():
            out.append(b)
    return out


def find_repo_root() -> Optional[Path]:
    for base in candidate_roots():
        direct = base / TARGET_REL
        if direct.exists():
            return base
        for p in base.rglob('Defs.lean'):
            try:
                rel = p.relative_to(base)
            except ValueError:
                continue
            if rel.parts[-2:] == ('PEqualNP', 'Defs.lean'):
                return p.parent.parent
    return None


def iter_text_files(root: Path):
    for path in root.rglob('*'):
        if not path.is_file():
            continue
        if any(part.startswith('.git') or part == '.lake' or part == '__pycache__' for part in path.parts):
            continue
        if path.suffix.lower() not in {'.lean', '.md', '.txt', '.py', '.json', '.yaml', '.yml', '.toml'}:
            continue
        yield path


def safe_read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding='utf-8')
    except Exception:
        return None


def line_is_decl(line: str) -> bool:
    s = line.strip()
    return any(s.startswith(p) for p in DECL_PREFIXES)


def extract_helper_rhs() -> Optional[str]:
    text = safe_read(HELPER)
    if not text:
        return None
    m = re.search(r'PEqualNP\.Library\.FP3\s+1\s+2\s*[↔<>=-]+\s*(.*?)\n\s*:=\s*by', text, re.S)
    if m:
        return ' '.join(m.group(1).split())
    m = re.search(r'PEqualNP\.Library\.FP3\s+1\s+2\s*↔\s*(.*?)\n\s*:=\s*by', text, re.S)
    if m:
        return ' '.join(m.group(1).split())
    return None


def main() -> int:
    NOTES.write_text('Trial000039 starting\n', encoding='utf-8')
    failures: List[str] = []
    root = find_repo_root()
    log(f'Repository root probe result: {root}')
    if root is None:
        print('CHECK FAILURES:')
        print('- Could not locate repository root containing PEqualNP/Defs.lean')
        return 1

    fp3_decl: Optional[Tuple[str, int, str]] = None
    fp3_context = ''
    fp3_mentions: List[Tuple[str, int, str]] = []
    exact_mentions: List[Tuple[str, int, str]] = []
    bridge_lines: List[Tuple[str, int, str]] = []
    scanned_files = 0

    helper_rhs = extract_helper_rhs()
    log(f'Extracted helper RHS present: {helper_rhs is not None}')

    for path in iter_text_files(root):
        text = safe_read(path)
        if text is None:
            continue
        scanned_files += 1
        lines = text.splitlines()
        for idx, line in enumerate(lines, start=1):
            if 'FP3' in line:
                fp3_mentions.append((str(path), idx, line.rstrip()))
                if re.search(r'\b(def|abbrev|theorem|lemma|example|instance|axiom|opaque)\b.*\bFP3\b', line):
                    if fp3_decl is None and re.search(r'\b(def|abbrev)\b.*\bFP3\b', line):
                        fp3_decl = (str(path), idx, line.rstrip())
                        start = max(0, idx - 11)
                        end = min(len(lines), idx + 10)
                        fp3_context = '\n'.join(f'{j+1}: {lines[j]}' for j in range(start, end))
            if 'FP3 1 2' in line:
                exact_mentions.append((str(path), idx, line.rstrip()))
            if any(tok in line for tok in BRIDGE_TOKENS) and (('FP3' in line) or line_is_decl(line)):
                bridge_lines.append((str(path), idx, line.rstrip()))

    if fp3_decl is None:
        for path in iter_text_files(root):
            text = safe_read(path)
            if text is None:
                continue
            lines = text.splitlines()
            for idx, line in enumerate(lines, start=1):
                if re.search(r'\b(def|abbrev)\b\s+FP3\b', line):
                    fp3_decl = (str(path), idx, line.rstrip())
                    start = max(0, idx - 11)
                    end = min(len(lines), idx + 10)
                    fp3_context = '\n'.join(f'{j+1}: {lines[j]}' for j in range(start, end))
                    break
            if fp3_decl is not None:
                break

    if fp3_decl is None:
        failures.append('No FP3 declaration found.')

    verbatim_hits: List[Tuple[str, int, str]] = []
    if helper_rhs:
        needle = helper_rhs
        for path in iter_text_files(root):
            text = safe_read(path)
            if text is None:
                continue
            norm = ' '.join(text.split())
            if needle in norm:
                for idx, line in enumerate(text.splitlines(), start=1):
                    if 'SigmaV 3' in line or 'DTIMEO' in line or 'FP3 1 2' in line:
                        verbatim_hits.append((str(path), idx, line.rstrip()))
                        break

    report: List[str] = []
    report.append('# FP3 live audit')
    report.append('')
    report.append(f'- Root scanned: `{root}`')
    report.append(f'- Files scanned: {scanned_files}')
    report.append('')
    report.append('## Definition of FP3')
    if fp3_decl:
        report.append(f'- Declaration: `{fp3_decl[0]}:{fp3_decl[1]}`')
        report.append(f'- Source line: `{fp3_decl[2]}`')
        report.append('')
        report.append('```lean')
        report.append(fp3_context)
        report.append('```')
    else:
        report.append('- No FP3 declaration found.')
    report.append('')
    report.append('## All FP3 mentions')
    report.extend([f'- `{p}:{n}` — `{l}`' for p, n, l in fp3_mentions] or ['- None'])
    report.append('')
    report.append('## Exact instance mentions')
    report.extend([f'- `{p}:{n}` — `{l}`' for p, n, l in exact_mentions] or ['- None'])
    report.append('')
    report.append('## Potential bridge declarations')
    report.extend([f'- `{p}:{n}` — `{l}`' for p, n, l in bridge_lines] or ['- None'])
    report.append('')
    report.append('## Verbatim unfolding audit')
    report.append(f'- Helper file present: {HELPER.exists()}')
    report.append(f'- Extracted RHS from Helper000038.lean: `{helper_rhs}`' if helper_rhs else '- Could not extract RHS from Helper000038.lean')
    report.append(f'- Verbatim normalized RHS occurs in scanned repository: {bool(verbatim_hits)}')
    report.extend([f'- Candidate hit `{p}:{n}` — `{l}`' for p, n, l in verbatim_hits] or ['- No verbatim match found in scanned tree.'])
    report.append('')
    report.append('Conclusion: this audit inventories existing textual support lines for `FP3` and the exact instance `FP3 1 2`.')
    REPORT.write_text('\n'.join(report), encoding='utf-8')

    text = REPORT.read_text(encoding='utf-8')
    for sec in REQUIRED_SECTIONS:
        if f'## {sec}' not in text:
            failures.append(f'Missing required report section: {sec}')
    if fp3_decl and len(fp3_context.splitlines()) < 20:
        failures.append('Extracted FP3 context has fewer than 20 lines.')

    print('FP3 live audit experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Root: {root}')
    print(f'Files scanned: {scanned_files}')
    print(f'FP3 declaration: {fp3_decl[0]}:{fp3_decl[1]}' if fp3_decl else 'FP3 declaration: none')
    print(f'FP3 mention count: {len(fp3_mentions)}')
    print(f'Exact `FP3 1 2` count: {len(exact_mentions)}')
    print(f'Potential bridge declaration count: {len(bridge_lines)}')
    print(f'Verbatim unfolding hits: {len(verbatim_hits)}')

    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1
    print('All checks passed.')
    log('All checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

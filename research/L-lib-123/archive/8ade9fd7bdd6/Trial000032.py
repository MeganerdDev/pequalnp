#!/usr/bin/env python3
from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict

CANDIDATES = [Path('/project/PEqualNP'), Path('/workspace/repo/PEqualNP'), Path('/workspace/PEqualNP'), Path('/workspace/reference/lean/PEqualNP')]
ROOT = next((p for p in CANDIDATES if p.exists()), CANDIDATES[0])
OUT = Path('/workspace/fp3-definition-audit.md')
NOTES = Path('/workspace/notes.md')
TARGET = 'FP3'
SEARCH_TERMS = ['FP3 1 2', 'SigmaV 3', 'DTIMEO']
GUESSED = 'K * 2 ^ m + K'
ALT_GUESSED = 'K * 2 ^ (1 * m) + K'


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


def read_lines(path: Path) -> List[str]:
    return path.read_text(encoding='utf-8', errors='replace').splitlines()


def collect_files(root: Path) -> List[Path]:
    return sorted(p for p in root.rglob('*.lean') if p.is_file())


def snippet(lines: List[str], idx: int, radius: int = 6) -> str:
    start = max(0, idx - radius)
    end = min(len(lines), idx + radius + 1)
    out = []
    for i in range(start, end):
        mark = '>>' if i == idx else '  '
        out.append(f'{mark} {i+1}: {lines[i]}')
    return '\n'.join(out)


def find_definition(files: List[Path]) -> Tuple[Path, int, List[str]]:
    patterns = [
        re.compile(r'\bdef\s+FP3\b'),
        re.compile(r'\babbrev\s+FP3\b'),
        re.compile(r'\btheorem\s+FP3\b'),
        re.compile(r'\blemma\s+FP3\b'),
    ]
    for path in files:
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if any(p.search(line) for p in patterns):
                return path, i, lines
    raise FileNotFoundError('Could not find definition/declaration site for FP3')


def extract_decl(lines: List[str], idx: int) -> str:
    buf = []
    started = False
    for j in range(idx, len(lines)):
        line = lines[j]
        if not started:
            started = True
        buf.append(line)
        if ':=' in line or line.strip().endswith('where'):
            if ':=' in line:
                break
    return '\n'.join(buf)


def extract_rhs(lines: List[str], idx: int) -> str:
    joined = []
    found = False
    first = None
    for j in range(idx, min(len(lines), idx + 25)):
        line = lines[j]
        if not found and ':=' in line:
            first = line.split(':=', 1)[1]
            joined.append(first)
            found = True
            continue
        if found:
            s = line.strip()
            if s.startswith('--'):
                continue
            if re.match(r'^(/--|def|abbrev|theorem|lemma|example|instance|structure|class)\b', s):
                break
            joined.append(line)
    text = ' '.join(part.strip() for part in joined).strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def find_mentions(files: List[Path], needle_re: re.Pattern[str]) -> List[Tuple[Path, int, str]]:
    hits = []
    for path in files:
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if needle_re.search(line):
                hits.append((path, i, line.rstrip()))
    return hits


def theoremish_mentions(files: List[Path]) -> List[Tuple[Path, int, str]]:
    hits = []
    pat = re.compile(r'\b(theorem|lemma)\b.*\bFP3\b|\bFP3\b.*\b(theorem|lemma)\b')
    for path in files:
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if pat.search(line):
                hits.append((path, i, line.rstrip()))
    return hits


def main() -> int:
    log('Starting FP3 audit script.')
    if not ROOT.exists():
        print(f'Missing repository root: {ROOT}')
        return 2
    files = collect_files(ROOT)
    print(f'Scanning {len(files)} Lean files under {ROOT}')
    log(f'Lean files found: {len(files)}')

    def_path, def_idx, def_lines = find_definition(files)
    decl = extract_decl(def_lines, def_idx)
    rhs = extract_rhs(def_lines, def_idx)
    def_snip = snippet(def_lines, def_idx)
    print(f'Found FP3 declaration at {def_path}:{def_idx+1}')
    print(f'Normalized RHS: {rhs}')
    log(f'FP3 declaration at {def_path}:{def_idx+1}')
    log(f'RHS: {rhs}')

    theorem_hits = theoremish_mentions(files)
    fp3_hits = find_mentions(files, re.compile(r'\bFP3\b'))
    term_hits: Dict[str, List[Tuple[Path, int, str]]] = {
        term: find_mentions(files, re.compile(re.escape(term))) for term in SEARCH_TERMS
    }

    guessed_literal = False
    guessed_locations: List[Tuple[Path, int, str]] = []
    for path in files:
        lines = read_lines(path)
        for i, line in enumerate(lines):
            if GUESSED in line or ALT_GUESSED in line:
                guessed_literal = True
                guessed_locations.append((path, i, line.rstrip()))

    sections = []
    sections.append('# FP3 definition audit')
    sections.append('')
    sections.append('## 1. Definition site for `FP3`')
    sections.append(f'- File: `{def_path}`')
    sections.append(f'- Line: {def_idx + 1}')
    sections.append('')
    sections.append('```lean')
    sections.append(def_snip)
    sections.append('```')
    sections.append('')
    sections.append('## 2. Normalized RHS recovered by the script')
    sections.append('')
    sections.append('```text')
    sections.append(rhs or '<empty>')
    sections.append('```')
    sections.append('')
    sections.append('## 3. Check for the previous guessed formula')
    sections.append(f'- Literal `{GUESSED}` appears anywhere: {"yes" if guessed_literal else "no"}')
    sections.append(f'- Alternate literal `{ALT_GUESSED}` appears anywhere: {"yes" if guessed_literal else "no"}')
    if guessed_locations:
        sections.append('')
        sections.append('Matching locations:')
        for path, i, line in guessed_locations[:20]:
            sections.append(f'- `{path}:{i+1}`: `{line}`')
    else:
        sections.append('')
        sections.append('No literal occurrence of the guessed formula was found in scanned Lean sources.')
    sections.append('')
    sections.append('## 4. Existing lemmas/theorems that could rewrite or specialize `FP3`')
    if theorem_hits:
        for path, i, line in theorem_hits[:50]:
            sections.append(f'- `{path}:{i+1}`: `{line}`')
    else:
        sections.append('- No theorem/lemma lines mentioning `FP3` were found by the simple line-based search.')
    sections.append('')
    sections.append('## Supplemental search results')
    sections.append('')
    sections.append(f'- Total `FP3` line hits: {len(fp3_hits)}')
    for term in SEARCH_TERMS:
        hits = term_hits[term]
        sections.append(f'- Exact string `{term}` hits: {len(hits)}')
        for path, i, line in hits[:20]:
            sections.append(f'  - `{path}:{i+1}`: `{line}`')
    sections.append('')
    sections.append('## Preliminary conclusion')
    sections.append(f'- The scanned declaration site suggests `FP3 1 2` unfolds to: `{rhs}`')
    sections.append(f'- Exact string `FP3 1 2` present elsewhere: {"yes" if term_hits["FP3 1 2"] else "no"}')
    sections.append(f'- Exact string `SigmaV 3` present elsewhere: {"yes" if term_hits["SigmaV 3"] else "no"}')
    sections.append(f'- Exact string `DTIMEO` present elsewhere: {"yes" if term_hits["DTIMEO"] else "no"}')

    OUT.write_text('\n'.join(sections) + '\n', encoding='utf-8')
    print(f'Wrote report to {OUT}')

    report_text = OUT.read_text(encoding='utf-8')
    failures = []
    for required in [
        '## 1. Definition site for `FP3`',
        '## 2. Normalized RHS recovered by the script',
        '## 3. Check for the previous guessed formula',
        '## 4. Existing lemmas/theorems that could rewrite or specialize `FP3`',
    ]:
        if required not in report_text:
            failures.append(f'Missing required report section: {required}')
    if not rhs:
        failures.append('Failed to recover a nonempty normalized RHS for FP3.')
    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1

    print('Search term hit counts:')
    for term in SEARCH_TERMS:
        print(f'  {term!r}: {len(term_hits[term])}')
    print(f'FP3 theorem/lemma line hits: {len(theorem_hits)}')
    print(f'Guessed formula literal found: {guessed_literal}')
    print('All required checks passed.')
    log('All required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

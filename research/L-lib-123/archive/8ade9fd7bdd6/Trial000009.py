#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Iterable

BASE = Path('/workspace')
DEFS_SUFFIX = 'PEqualNP/Defs.lean'
OUTSIDE_SUFFIX = 'PEqualNP/Outside/L_lib_123.lean'

WITNESS_PATTERNS = [
    ("exists_pq_nat_fp3", re.compile(r'∃\s*p\s*q\s*:\s*ℕ.*FP3|exists\s+p\s+q\s*,.*FP3', re.IGNORECASE)),
    ("theorem_exists_fp3", re.compile(r'theorem\b.*[:].*(∃|exists).*FP3', re.IGNORECASE)),
    ("example_fp3", re.compile(r'example\b.*FP3', re.IGNORECASE)),
    ("axiom_fp3", re.compile(r'axiom\b.*FP3', re.IGNORECASE)),
    ("concrete_fp3_nums", re.compile(r'\bFP3\s+\d+\s+\d+\b')),
]
L122_DECL = re.compile(r'^\s*theorem\s+PEqualNP\.Library\.L122\b')
IMPORT_RE = re.compile(r'^\s*import\s+(.+?)\s*$')


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding='utf-8')
    except UnicodeDecodeError:
        return path.read_text(encoding='utf-8', errors='replace')


def all_lean_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob('*.lean') if p.is_file())


def find_suffix(base: Path, suffix: str) -> list[Path]:
    return sorted(
        p for p in base.rglob(Path(suffix).name)
        if p.is_file() and p.as_posix().endswith(suffix)
    )


def choose_tree(base: Path) -> tuple[Path | None, list[Path], list[dict]]:
    defs_candidates = find_suffix(base, DEFS_SUFFIX)
    reports = []
    best_root = None
    best_files: list[Path] = []
    best_score = (-1, -1)
    for defs in defs_candidates:
        root = defs.parent.parent
        files = all_lean_files(root)
        score = (len(files), -len(str(root)))
        reports.append({'defs': str(defs), 'root': str(root), 'lean_files': len(files)})
        if score > best_score:
            best_score = score
            best_root = root
            best_files = files
    return best_root, best_files, reports


def parse_imports(path: Path | None) -> list[str] | None:
    if path is None:
        return None
    imports = []
    for line in safe_read(path).splitlines():
        m = IMPORT_RE.match(line)
        if m:
            imports.append(m.group(1).strip())
    return imports


def rel_or_abs(path: Path, base: Path) -> str:
    try:
        return str(path.relative_to(base))
    except ValueError:
        return str(path)


def scan_files(files: Iterable[Path], base: Path) -> tuple[list[dict], str | None]:
    witness_lines = []
    l122_path = None
    for path in files:
        for lineno, line in enumerate(safe_read(path).splitlines(), start=1):
            if l122_path is None and L122_DECL.search(line):
                l122_path = rel_or_abs(path, base)
            for name, pat in WITNESS_PATTERNS:
                if pat.search(line):
                    witness_lines.append({
                        'pattern': name,
                        'path': rel_or_abs(path, base),
                        'line_number': lineno,
                        'line': line.strip(),
                    })
    return witness_lines, l122_path


def main() -> int:
    root, files, reports = choose_tree(BASE)
    exact_outside = find_suffix(BASE, OUTSIDE_SUFFIX)
    loose_outside = sorted(p for p in BASE.rglob('L_lib_123.lean') if p.is_file())
    outside_path = exact_outside[0] if exact_outside else (loose_outside[0] if loose_outside else None)
    outside_imports = parse_imports(outside_path)

    witness_lines: list[dict] = []
    l122_path = None
    if root is not None:
        witness_lines, l122_path = scan_files(files, root)

    result = {
        'tree_discovery': {
            'searched_base': str(BASE),
            'defs_candidates': reports,
            'chosen_root': str(root) if root else None,
            'lean_file_count': len(files),
        },
        'outside_file': str(outside_path) if outside_path else None,
        'outside_file_exact_match': bool(exact_outside),
        'outside_file_candidates': [str(p) for p in loose_outside[:10]],
        'direct_witness_found': bool(witness_lines),
        'witness_lines': witness_lines,
        'l122_path': l122_path,
        'outside_allowed_imports': outside_imports,
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if root is None or not files:
        print('\nFAILURES:')
        print('- No Lean tree found via PEqualNP/Defs.lean under /workspace.')
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

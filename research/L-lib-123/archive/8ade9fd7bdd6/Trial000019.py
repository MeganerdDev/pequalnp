#!/usr/bin/env python3
import re
import sys
from pathlib import Path
from typing import List, Tuple, Dict, Optional

ROOT_CANDIDATES = [
    Path('/project/PEqualNP'),
    Path('/workspace/repo/PEqualNP'),
    Path('/workspace/reference/lean/PEqualNP'),
]
NOTES = Path('/workspace/notes.md')
STACK_REPORT = Path('/workspace/stack-boundary.md')

CURRENT_CANDIDATE = '''import PEqualNP.Defs

theorem PEqualNP.Outside.L_lib_123 : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ PEqualNP.Library.FP3 p q := by
  refine ⟨1, 2, by decide, by decide, ?_⟩
'''
PRIOR_UNSOLVED = '⊢ Library.FP3 1 2'


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def find_root() -> Path:
    for cand in ROOT_CANDIDATES:
        if cand.exists():
            return cand
    raise FileNotFoundError('Missing repository root; checked: ' + ', '.join(str(p) for p in ROOT_CANDIDATES))


def theorem_name_from_line(line: str) -> Optional[str]:
    m = re.search(r'\b(?:theorem|lemma|example)\s+([^\s:(\[]+)', line)
    return m.group(1) if m else None


def scan(root: Path) -> Dict[str, object]:
    lean_files = sorted(root.rglob('*.lean'))
    hits: List[Tuple[Path, int, str]] = []
    defs: List[Tuple[Path, int, str]] = []
    theorem_mentions: List[Tuple[Path, int, str, str]] = []
    all_lines: Dict[Path, List[str]] = {}
    fp3_re = re.compile(r'\bFP3\b')
    def_re = re.compile(r'\bdef\s+FP3\b|\babbrev\s+FP3\b|\btheorem\s+FP3\b|\blemma\s+FP3\b|\bopaque\s+FP3\b|\baxiom\s+FP3\b|\bconstant\s+FP3\b')
    thm_kw_re = re.compile(r'\b(theorem|lemma|example)\b')

    for path in lean_files:
        text = path.read_text(encoding='utf-8', errors='replace')
        lines = text.splitlines()
        all_lines[path] = lines
        for i, line in enumerate(lines, 1):
            if fp3_re.search(line):
                rel = path.relative_to(root.parent)
                hits.append((rel, i, line.rstrip()))
                if def_re.search(line):
                    defs.append((rel, i, line.rstrip()))
                if thm_kw_re.search(line):
                    name = theorem_name_from_line(line) or '<anonymous>'
                    theorem_mentions.append((rel, i, name, line.rstrip()))
    return {'lean_files': lean_files, 'hits': hits, 'defs': defs, 'theorem_mentions': theorem_mentions, 'all_lines': all_lines}


def get_context(root: Path, all_lines: Dict[Path, List[str]], rel_path: Path, line_no: int, radius: int = 3) -> str:
    full = root.parent / rel_path
    lines = all_lines[full]
    start = max(1, line_no - radius)
    end = min(len(lines), line_no + radius)
    return '\n'.join(f'{">" if n == line_no else " "} {n:4d}: {lines[n-1]}' for n in range(start, end + 1))


def classify(data: Dict[str, object]) -> str:
    defs = data['defs']
    theorem_mentions = data['theorem_mentions']
    if not defs:
        return 'FP3 only appears as an opaque constant/axiom'
    def_text = ' '.join(line for _, _, line in defs)
    if any(k in def_text for k in ['axiom FP3', 'constant FP3', 'opaque FP3']):
        return 'FP3 only appears as an opaque constant/axiom'
    if any(re.search(r'\bFP3\s+1\s+2\b', line) for _, _, _, line in theorem_mentions):
        return 'definition found with obvious constructor path for FP3 1 2'
    return 'definition found but no evident introduction lemma for FP3 1 2'


def main() -> int:
    NOTES.write_text('Trial000019 started.\n', encoding='utf-8')
    log('Objective: audit Lean definitions mentioning FP3 and classify the blocker Library.FP3 1 2.')
    failures: List[str] = []

    root = find_root()
    data = scan(root)
    hits = data['hits']
    defs = data['defs']
    theorem_mentions = data['theorem_mentions']
    all_lines = data['all_lines']

    if not defs:
        failures.append(f'No FP3 definition-like site found under {root}.')

    namespace_consistent = ('Library.FP3 1 2' in PRIOR_UNSOLVED) and ('PEqualNP.Library.FP3' in CURRENT_CANDIDATE)
    if not namespace_consistent:
        failures.append('Namespace consistency check failed for current candidate vs unsolved goal.')

    classification = classify(data)
    exact_fp3_12_mentions = [item for item in theorem_mentions if re.search(r'\bFP3\s+1\s+2\b', item[3])]

    print('FP3 search audit')
    print(f'Repository root: {root}')
    print(f'Lean files scanned: {len(data["lean_files"])}')
    print(f'Total FP3 hits: {len(hits)}')
    print(f'Definition-like hits: {len(defs)}')
    print(f'Theorem/lemma/example mentions: {len(theorem_mentions)}')
    print(f'Classification: {classification}')
    print(f'Namespace consistency: {namespace_consistent}')

    print('\nDefinition contexts:')
    for rel, line_no, _ in defs[:10]:
        print(f'-- {rel}:{line_no}')
        print(get_context(root, all_lines, rel, line_no))

    print('\nTheorem/lemma/example mentions of FP3:')
    for rel, line_no, name, line in theorem_mentions[:20]:
        print(f'- {rel}:{line_no}: {name}: {line}')

    print(f'\nExact theorem/example mentions of `FP3 1 2`: {len(exact_fp3_12_mentions)}')
    for rel, line_no, name, line in exact_fp3_12_mentions:
        print(f'  * {rel}:{line_no}: {name}: {line}')

    quoted_next = exact_fp3_12_mentions[0][3] if exact_fp3_12_mentions else 'none'
    print(f'Quoted theorem for next Lean candidate: {quoted_next}')

    log(f'Using repository root: {root}')
    log(f'Scanned {len(data["lean_files"])} Lean files; found {len(hits)} FP3 hits and {len(defs)} definition-like hits.')
    log(f'Classification: {classification}')
    log(f'Namespace consistency with blocker: {namespace_consistent}')
    if defs:
        rel, line_no, _ = defs[0]
        log(f'Primary definition site: {rel}:{line_no}')
    if exact_fp3_12_mentions:
        log(f'Exact FP3 1 2 theorem/example mention: {exact_fp3_12_mentions[0][0]}:{exact_fp3_12_mentions[0][1]}')
    else:
        log('No theorem/example line mentions FP3 1 2 exactly.')
    if STACK_REPORT.exists():
        log('Verified prior artifact exists: stack-boundary.md')

    if failures:
        print('\nFAILURES:')
        for item in failures:
            print(f'  - {item}')
            log(f'FAIL: {item}')
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())

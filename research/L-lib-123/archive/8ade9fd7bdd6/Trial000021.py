#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT_CANDIDATES = [Path('/project'), Path('/workspace')]
NOTES = Path('/workspace/notes.md')
EXPECTED_SNIPPETS = [
    'def FP3 (p q : ℕ) : Prop :=',
    '∀ L ∈ DTIMEO (fun m => 2 ^ (q * m))',
    '∃ K : ℕ, 1 ≤ K ∧ L ∈ SigmaV 3 (fun m => K * 2 ^ (p * m) + K)',
]
DECL_RE = re.compile(r'^\s*(theorem|lemma|example|axiom)\s+([^:\s(]+)?[^\n]*\bFP3\b')
EXACT_RE = re.compile(r'\bFP3\s+1\s+2\b')
WORD_RE = re.compile(r'\bFP3\b')


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as fh:
        fh.write(msg + '\n')


def candidate_roots():
    seen = set()
    for base in ROOT_CANDIDATES:
        if not base.exists():
            continue
        for path in [base] + sorted([p for p in base.rglob('*') if p.is_dir()]):
            rp = path.resolve()
            if rp not in seen:
                seen.add(rp)
                yield path


def find_repo_root():
    matches = []
    for d in candidate_roots():
        if (d / 'PEqualNP' / 'Defs.lean').exists() or (d / 'PEqualNP' / 'Defs').exists():
            matches.append(d)
    if not matches:
        raise FileNotFoundError('No repo root found containing PEqualNP/Defs.lean or PEqualNP/Defs')
    matches.sort(key=lambda p: (len(p.parts), str(p)))
    return matches[0], matches


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def gather(root: Path):
    peq = root / 'PEqualNP'
    files = sorted(peq.rglob('*.lean'))
    if not files:
        raise FileNotFoundError(f'No Lean files under {peq}')
    hits = []
    decls = []
    exacts = []
    defs = []
    for f in files:
        text = read_text(f)
        lines = text.splitlines()
        rel = f.relative_to(root)
        for i, line in enumerate(lines, 1):
            if WORD_RE.search(line):
                hits.append((str(rel), i, line.strip()))
            if line.lstrip().startswith('def FP3 '):
                defs.append((str(rel), i, line.rstrip()))
            m = DECL_RE.search(line)
            if m:
                decls.append((str(rel), i, m.group(1), m.group(2) or '', line.rstrip()))
            if EXACT_RE.search(line):
                exacts.append((str(rel), i, line.rstrip()))
    return files, hits, decls, exacts, defs


def verify_definition(root: Path, defs):
    if not defs:
        return False, 'no def FP3 line found'
    rel, line_no, _ = defs[0]
    text = read_text(root / rel)
    ok = all(snippet in text for snippet in EXPECTED_SNIPPETS)
    return ok, f'{rel}:{line_no}'


def classify(defs, decls, exacts):
    if any(kind in {'theorem', 'lemma', 'axiom', 'example'} for _, _, kind, _, line in decls if EXACT_RE.search(line)):
        return 'exact theorem for FP3 1 2 found'
    transfer_words = ('mono', 'monot', 'transfer', 'lift', 'weaken', 'strengthen', 'subset', 'include', 'imp')
    if any(any(w in (name + ' ' + line).lower() for w in transfer_words) for _, _, _, name, line in decls):
        return 'transfer/monotonic lemmas found but no exact theorem'
    return 'only definition/unfolding found'


def main():
    failures = []
    try:
        root, all_roots = find_repo_root()
    except Exception as e:
        print(f'FAIL: {e}')
        log(f'FAIL finding root: {e}')
        return 1

    files, hits, decls, exacts, defs = gather(root)
    def_ok, def_site = verify_definition(root, defs)
    if not defs:
        failures.append('No definition site for FP3 found')
    if not def_ok:
        failures.append('Defining occurrence did not match recorded unfolding oracle')

    classification = classify(defs, decls, exacts)
    exact_decl_lines = [(rel, ln, kind, name, line) for rel, ln, kind, name, line in decls if EXACT_RE.search(line)]

    print(f'Repository root: {root}')
    print('All candidate roots found:')
    for r in all_roots:
        print(f'  - {r}')
    print(f'Lean files scanned: {len(files)}')
    print(f'FP3 hits: {len(hits)}')
    print(f'Declaration lines mentioning FP3: {len(decls)}')
    print(f'Exact textual mentions of FP3 1 2: {len(exacts)}')
    print(f'Definition site oracle match: {def_ok} ({def_site})')
    print(f'Classification: {classification}')

    print('\nDefinition sites:')
    for rel, ln, line in defs[:10]:
        print(f'  {rel}:{ln}: {line}')

    print('\nDeclarations mentioning FP3:')
    for rel, ln, kind, name, line in decls[:20]:
        print(f'  {rel}:{ln}: {kind} {name}: {line}')

    print('\nExact textual mentions of FP3 1 2:')
    for rel, ln, line in exacts[:20]:
        print(f'  {rel}:{ln}: {line}')

    quoted = exact_decl_lines[0][4] if exact_decl_lines else 'none'
    print(f'Quoted theorem for next Lean candidate: {quoted}')

    log(f'Using root {root}')
    log(f'Roots found: {", ".join(str(r) for r in all_roots)}')
    log(f'Scanned {len(files)} Lean files; {len(hits)} FP3 hits; {len(decls)} decl mentions; {len(exacts)} exact textual mentions.')
    log(f'Definition oracle match: {def_ok} at {def_site}')
    log(f'Classification: {classification}')
    log(f'Quoted theorem line: {quoted}')

    if failures:
        print('\nFAILURES:')
        for f in failures:
            print(f'  - {f}')
            log(f'FAIL: {f}')
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())

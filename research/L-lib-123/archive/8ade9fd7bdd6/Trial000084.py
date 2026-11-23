#!/usr/bin/env python3
import re
import sys
from pathlib import Path

SEARCH_ROOTS = [Path('/workspace/repo'), Path('/workspace/reference'), Path('/workspace')]
PRIMARY_FILES = [
    Path('lean/PEqualNP/Defs.lean'),
    Path('lean/PEqualNP/Defs/TimeAlt.lean'),
]
DECL_RE = re.compile(r'^(?:@[\[\]A-Za-z0-9_., ]+\s*)?(?:noncomputable\s+)?(?:opaque|abbrev|def|theorem)\s+FP3\b')
HYPOTHESIS_TOKENS = ['DTIMEO', 'SigmaV 3', '2 ^ (2 * m)', '2 ^ (1 * m)']


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def candidate_files():
    seen = set()
    searched = []
    for root in SEARCH_ROOTS:
        for rel in PRIMARY_FILES:
            p = root / rel
            searched.append(str(p))
            if p.exists() and p not in seen:
                seen.add(p)
                yield p, searched
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob('*.lean'):
            sp = str(p)
            if sp not in searched:
                searched.append(sp)
            if p in seen:
                continue
            try:
                txt = read_text(p)
            except Exception:
                continue
            if 'FP3' in txt:
                seen.add(p)
                yield p, searched


def extract_decl_lines(lines):
    idx = None
    for i, line in enumerate(lines):
        if DECL_RE.match(line.strip()):
            idx = i
            break
    if idx is None:
        return None, None
    start = max(0, idx - 5)
    end = min(len(lines), idx + 30)
    return idx, lines[start:end]


def main():
    target = None
    searched = []
    snippet = None
    for p, searched in candidate_files():
        lines = read_text(p).splitlines()
        idx, block = extract_decl_lines(lines)
        if idx is not None:
            target = p
            snippet = '\n'.join(block)
            break

    print('Searched paths/files:')
    for s in searched:
        print(' -', s)
    if target is None:
        print('ERROR: could not locate declaration line for FP3 in searched Lean files')
        return 2

    print(f'\nUsing file: {target}')
    print('\nExtracted snippet around FP3 declaration:')
    print('--- SNIPPET START ---')
    print(snippet)
    print('--- SNIPPET END ---')

    found = {tok: (tok in snippet) for tok in HYPOTHESIS_TOKENS}
    hypothesis_confirmed = all(found.values())
    opaque_or_aliased = (':=' not in snippet) or snippet.lstrip().startswith('opaque ')

    print('\nToken checks against hypothesized unfolded shape:')
    for tok, ok in found.items():
        print(f' - {tok!r}: {ok}')
    print(f'\nHypothesis confirmed: {hypothesis_confirmed}')
    print(f'Opaque or alias-like declaration: {opaque_or_aliased}')

    if hypothesis_confirmed:
        print('VERDICT: snippet syntactically matches the hypothesized shape.')
    else:
        missing = [tok for tok, ok in found.items() if not ok]
        print('VERDICT: counterexample to the hypothesis; actual declaration snippet does not match.')
        if missing:
            print('Missing tokens:', ', '.join(repr(x) for x in missing))
    return 0


if __name__ == '__main__':
    sys.exit(main())

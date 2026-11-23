#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000037.py')
REPORT = Path('/workspace/fp3-live-audit.md')
NOTES = Path('/workspace/notes.md')
CANDIDATE_ROOTS = [Path('/project/PEqualNP'), Path('/workspace/reference/lean/PEqualNP')]
REQUIRED_SECTIONS = [
    'Definition of FP3',
    'All FP3 mentions',
    'Potential bridge declarations',
    'Literal occurrence audit',
]
DECL_PREFIXES = ('theorem', 'lemma', 'def', 'abbrev', 'instance', 'example', 'opaque', 'axiom', 'class', 'structure')
BRIDGE_TOKENS = ['SigmaV 3', 'DTIMEO', 'collapse', 'rootUp', 'mono', 'monot', 'subset', 'instance', 'example', '1 2', '2 1']
LITERALS = ['theorem research_result', 'FP3 1 2', 'K * 2 ^']


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def choose_root() -> Path | None:
    for root in CANDIDATE_ROOTS:
        if root.exists():
            return root
    return None


def iter_files(root: Path):
    for p in sorted(root.rglob('*')):
        if p.is_file() and p.suffix in {'.lean', '.md', '.txt'}:
            yield p


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


def declaration_lines(text: str):
    out = []
    for i, line in enumerate(text.splitlines(), start=1):
        s = line.strip()
        if s.startswith(DECL_PREFIXES):
            out.append((i, line.rstrip('\n')))
    return out


def main() -> int:
    root = choose_root()
    log('Trial000037 start: auditing live project tree for FP3 facts.')
    failures = []
    if root is None:
        print('Missing repository root candidates: ' + ', '.join(str(p) for p in CANDIDATE_ROOTS))
        log('FAIL missing repository root candidates')
        return 1
    log(f'Using root: {root}')

    fp3_decl = None
    fp3_context = ''
    fp3_mentions = []
    bridge_lines = []
    literal_hits = {lit: [] for lit in LITERALS}
    scanned_files = 0

    for path in iter_files(root):
        scanned_files += 1
        text = read_text(path)
        lines = text.splitlines()

        for lit in LITERALS:
            if lit in text:
                for i, line in enumerate(lines, start=1):
                    if lit in line:
                        literal_hits[lit].append((path, i, line.strip()))

        decls = declaration_lines(text)
        for i, line in decls:
            if 'FP3' in line:
                fp3_mentions.append((path, i, line.strip()))
                if fp3_decl is None and re.search(r'\b(def|abbrev|theorem|lemma|opaque|axiom)\b.*\bFP3\b', line):
                    start = max(1, i - 10)
                    end = min(len(lines), i + 10)
                    snippet = [f'{j:4d}: {lines[j-1]}' for j in range(start, end + 1)]
                    fp3_decl = (path, i, line.strip())
                    fp3_context = '\n'.join(snippet)
            if any(tok in line for tok in BRIDGE_TOKENS):
                bridge_lines.append((path, i, line.strip()))

    if fp3_decl is None:
        failures.append('No FP3 declaration found in live project tree.')

    report_lines = [
        '# FP3 live audit',
        '',
        f'Scanned root: `{root}`',
        f'Files scanned: {scanned_files}',
        '',
        '## Definition of FP3',
    ]
    if fp3_decl is None:
        report_lines.append('No declaration found.')
    else:
        path, line_no, decl = fp3_decl
        report_lines.extend([
            f'- Path: `{path}`',
            f'- Line: {line_no}',
            f'- Declaration: `{decl}`',
            '',
            '```lean',
            fp3_context,
            '```',
        ])
    report_lines.extend(['', '## All FP3 mentions'])
    report_lines.extend(
        [f'- `{path}:{line_no}` — `{line}`' for path, line_no, line in fp3_mentions] or ['- None']
    )
    report_lines.extend(['', '## Potential bridge declarations'])
    report_lines.extend(
        [f'- `{path}:{line_no}` — `{line}`' for path, line_no, line in bridge_lines] or ['- None']
    )
    report_lines.extend(['', '## Literal occurrence audit'])
    for lit in LITERALS:
        hits = literal_hits[lit]
        report_lines.append(f'### `{lit}`')
        report_lines.append(f'Count: {len(hits)}')
        report_lines.extend([f'- `{path}:{line_no}` — `{line}`' for path, line_no, line in hits] or ['- No occurrences found.'])
        report_lines.append('')

    REPORT.write_text('\n'.join(report_lines), encoding='utf-8')
    log(f'Wrote report to {REPORT}')

    report_text = REPORT.read_text(encoding='utf-8')
    for sec in REQUIRED_SECTIONS:
        if f'## {sec}' not in report_text:
            failures.append(f'Missing required report section: {sec}')
    if fp3_decl is not None and len(fp3_context.splitlines()) < 20:
        failures.append('FP3 surrounding source snippet has fewer than 20 lines.')

    print('FP3 live audit experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Root: {root}')
    print(f'Files scanned: {scanned_files}')
    print(f'FP3 declaration: {fp3_decl[0]}:{fp3_decl[1]} :: {fp3_decl[2]}' if fp3_decl else 'FP3 declaration: none')
    print(f'FP3 mention count: {len(fp3_mentions)}')
    print(f'Potential bridge declaration count: {len(bridge_lines)}')
    for lit in LITERALS:
        print(f'Literal {lit!r} count: {len(literal_hits[lit])}')

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

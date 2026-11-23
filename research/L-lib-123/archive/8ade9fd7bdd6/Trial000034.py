#!/usr/bin/env python3
import os
import re
import sys
import time
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000034.py')
REPORT = Path('/workspace/fp3-bridge-audit.md')
NOTES = Path('/workspace/notes.md')
ROOT = Path('/workspace/reference/lean/PEqualNP')

REQUIRED_SECTIONS = [
    '## Definition of FP3',
    '## Nearby definitions',
    '## Declarations mentioning FP3',
    '## Potential bridge lemmas',
    '## Negative findings',
]

DECL_TOKENS = ('theorem ', 'lemma ', 'def ', 'abbrev ', 'noncomputable def ')
BRIDGE_TOKENS = ['subset', 'mono', 'absorb', 'congr', 'rootUp', 'u / v', 'rational exponent']
SEARCH_NEEDLES = ['FP3', 'SigmaV 3', 'DTIMEO', 'rootUp', 'collapse']
FALSE_FRAGMENTS = ['K * 2 ^ m + K', 'FP3 1 2']


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def lean_files(root: Path):
    return sorted(root.rglob('*.lean'))


def read_lines(path: Path):
    return path.read_text(encoding='utf-8', errors='replace').splitlines()


def find_fp3_definition(files):
    patterns = [
        re.compile(r'\b(?:def|abbrev)\s+FP3\b'),
        re.compile(r'\b(?:def|abbrev)\s+Library\.FP3\b'),
    ]
    for path in files:
        lines = read_lines(path)
        for idx, line in enumerate(lines):
            if any(p.search(line) for p in patterns):
                return path, idx, lines
    return None


def collect_declaration_lines(files):
    hits = []
    bridge = []
    for path in files:
        lines = read_lines(path)
        for idx, line in enumerate(lines):
            text = line.strip()
            if any(tok in text for tok in DECL_TOKENS) and ('FP3' in text or 'collapse' in text):
                hits.append((path, idx + 1, text))
            if any(tok in text for tok in DECL_TOKENS) and any(bt in text for bt in BRIDGE_TOKENS):
                bridge.append((path, idx + 1, text))
    return hits, bridge


def count_exact_fragments(files, fragments):
    counts = {frag: 0 for frag in fragments}
    locations = {frag: [] for frag in fragments}
    for path in files:
        text = path.read_text(encoding='utf-8', errors='replace')
        for frag in fragments:
            c = text.count(frag)
            if c:
                counts[frag] += c
                locations[frag].append(str(path))
    return counts, locations


def count_search_mentions(files, needles):
    result = {n: [] for n in needles}
    for path in files:
        lines = read_lines(path)
        for idx, line in enumerate(lines, start=1):
            for n in needles:
                if n in line:
                    result[n].append((path, idx, line.rstrip()))
    return result


def extract_nearby(lines, idx, radius=10):
    start = max(0, idx - radius)
    end = min(len(lines), idx + radius + 1)
    return start, end, lines[start:end]


def main() -> int:
    start = time.time()
    NOTES.write_text('Starting Trial000034 FP3 bridge audit.\n', encoding='utf-8')

    failures = []
    if not ROOT.exists():
        failures.append(f'Missing repository root: {ROOT}')
    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1

    files = lean_files(ROOT)
    log(f'Lean files found under root: {len(files)}')

    fp3_info = find_fp3_definition(files)
    if fp3_info is None:
        failures.append('No FP3 definition found.')
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1

    fp3_path, fp3_idx, fp3_lines = fp3_info
    log(f'FP3 definition at {fp3_path}:{fp3_idx + 1}')
    start_i, end_i, snippet = extract_nearby(fp3_lines, fp3_idx, radius=10)
    if len(snippet) < 15:
        failures.append('FP3 surrounding snippet shorter than required 15 lines.')

    decl_hits, bridge_hits = collect_declaration_lines(files)
    search_mentions = count_search_mentions(files, SEARCH_NEEDLES)
    frag_counts, frag_locations = count_exact_fragments(files, FALSE_FRAGMENTS)

    negative_points = []
    if not any('rootUp' in line for _, _, line in decl_hits if 'FP3' in line):
        negative_points.append('No declaration line simultaneously mentions `FP3` and `rootUp`.')
    if not any(('mono' in line or 'subset' in line or 'congr' in line or 'absorb' in line) and 'FP3' in line for _, _, line in decl_hits):
        negative_points.append('No declaration line indicates an explicit monotonicity/congruence/subset lemma for `FP3`.')
    if frag_counts['FP3 1 2'] == 0:
        negative_points.append('Literal `FP3 1 2` does not occur anywhere in the scanned Lean tree.')
    if frag_counts['K * 2 ^ m + K'] == 0:
        negative_points.append('Literal `K * 2 ^ m + K` does not occur anywhere in the scanned Lean tree.')

    lines = []
    lines.append('# FP3 Bridge Audit')
    lines.append('')
    lines.append(f'- Root scanned: `{ROOT}`')
    lines.append(f'- Lean files scanned: {len(files)}')
    lines.append(f'- Runtime seconds: {time.time() - start:.3f}')
    lines.append('')

    lines.append('## Definition of FP3')
    lines.append('')
    lines.append(f'- Definition file: `{fp3_path}`')
    lines.append(f'- Definition line: {fp3_idx + 1}')
    lines.append('- Surrounding source snippet:')
    lines.append('```lean')
    for j, s in enumerate(snippet, start=start_i + 1):
        lines.append(f'{j:4d}: {s}')
    lines.append('```')
    lines.append('')

    lines.append('## Nearby definitions')
    lines.append('')
    nearby = []
    for off in range(max(0, fp3_idx - 20), min(len(fp3_lines), fp3_idx + 30)):
        text = fp3_lines[off].strip()
        if any(tok in text for tok in ('def ', 'abbrev ', 'theorem ', 'lemma ', 'noncomputable def ')):
            nearby.append((off + 1, fp3_lines[off]))
    for ln, txt in nearby:
        lines.append(f'- `{fp3_path}:{ln}`: `{txt}`')
    lines.append('')

    lines.append('## Declarations mentioning FP3')
    lines.append('')
    if decl_hits:
        for path, ln, txt in decl_hits:
            lines.append(f'- `{path}:{ln}`: `{txt}`')
    else:
        lines.append('- None found.')
    lines.append('')
    lines.append('Search mention counts:')
    for needle in SEARCH_NEEDLES:
        lines.append(f'- `{needle}`: {len(search_mentions[needle])} line hits')
    lines.append('')

    lines.append('## Potential bridge lemmas')
    lines.append('')
    if bridge_hits:
        for path, ln, txt in bridge_hits:
            lines.append(f'- `{path}:{ln}`: `{txt}`')
    else:
        lines.append('- No declaration lines with the configured bridge tokens were found.')
    lines.append('')
    lines.append('Literal fragment counts:')
    for frag in FALSE_FRAGMENTS:
        lines.append(f'- `{frag}`: {frag_counts[frag]} exact matches')
    lines.append('')

    lines.append('## Negative findings')
    lines.append('')
    for item in negative_points:
        lines.append(f'- {item}')
    if not negative_points:
        lines.append('- None.')
    lines.append('')
    lines.append('Explicit literal-occurrence verdicts:')
    for frag in FALSE_FRAGMENTS:
        verdict = 'occurs' if frag_counts[frag] else 'does not occur'
        lines.append(f'- `{frag}` {verdict} anywhere in the scanned Lean tree.')

    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    report_text = REPORT.read_text(encoding='utf-8')
    for section in REQUIRED_SECTIONS:
        if section not in report_text:
            failures.append(f'Missing required section: {section}')
    if 'Definition file:' not in report_text or 'Definition line:' not in report_text:
        failures.append('Report omitted precise FP3 file/line.')
    if report_text.count('```lean') < 1:
        failures.append('Report omitted Lean source snippet.')
    if len(snippet) < 15:
        failures.append('Report snippet requirement not met.')
    if 'Literal fragment counts:' not in report_text:
        failures.append('Report omitted literal fragment counts.')
    if 'Search mention counts:' not in report_text:
        failures.append('Report omitted search mention counts.')

    print('FP3 bridge audit')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Lean files scanned: {len(files)}')
    print(f'FP3 definition: {fp3_path}:{fp3_idx + 1}')
    print(f'Declaration hits (FP3/collapse): {len(decl_hits)}')
    print(f'Potential bridge declaration hits: {len(bridge_hits)}')
    for frag in FALSE_FRAGMENTS:
        print(f'Exact matches for {frag!r}: {frag_counts[frag]}')

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

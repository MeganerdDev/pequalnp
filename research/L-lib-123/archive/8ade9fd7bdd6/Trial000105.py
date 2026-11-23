#!/usr/bin/env python3
import os
import re
import sys
from pathlib import Path

ROOT = Path('/workspace')
TARGET_THEOREM_REL = Path('lean/PEqualNP/Outside/L_lib_123.lean')
ASSIGNMENT_CANDIDATE = r'''import PEqualNP.Defs

theorem L_lib_123 : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ PEqualNP.Library.FP3 p q := by
  refine ⟨1, 2, ?_, ?_, ?_⟩
  · decide
  · decide
  · unfold PEqualNP.Library.FP3
'''


def fail(msg: str) -> int:
    print(f'FAIL: {msg}', file=sys.stderr)
    return 1


def read_text(path: Path) -> str:
    return path.read_text(encoding='utf-8', errors='replace')


BLOCK_COMMENT_RE = re.compile(r'/-.*?-/', re.S)
LINE_COMMENT_RE = re.compile(r'--.*?$' , re.M)


def strip_comments(text: str) -> str:
    text = BLOCK_COMMENT_RE.sub('', text)
    text = LINE_COMMENT_RE.sub('', text)
    return text


def find_fp3_candidates(root: Path):
    hits = []
    for path in root.rglob('TimeAlt.lean'):
        try:
            text = read_text(path)
        except Exception:
            continue
        if 'def FP3' in text:
            hits.append(path)
    return sorted(hits)


def choose_theorem_path(root: Path) -> Path | None:
    exact = []
    fallback = []
    for path in root.rglob('L_lib_123.lean'):
        rel = None
        try:
            rel = path.relative_to(root)
        except Exception:
            pass
        text = ''
        try:
            text = read_text(path)
        except Exception:
            continue
        if 'theorem L_lib_123' not in text:
            continue
        fallback.append(path)
        if rel == TARGET_THEOREM_REL:
            exact.append(path)
    if exact:
        return sorted(exact)[0]
    if fallback:
        return sorted(fallback)[0]
    return None


DEF_FP3_RE = re.compile(
    r'(^\s*def\s+FP3\s*\(p\s+q\s*:\s*ℕ\)\s*:\s*Prop\s*:=\s*\n(?:^(?!\s*(?:def|theorem|lemma|example|noncomputable\b|end\b)).*\n?)*)',
    re.M,
)


def extract_fp3_block(text: str) -> str | None:
    m = DEF_FP3_RE.search(text)
    if m:
        return m.group(1).rstrip()
    idx = text.find('def FP3')
    if idx == -1:
        return None
    tail = text[idx:]
    lines = tail.splitlines()
    out = []
    for i, line in enumerate(lines):
        if i > 0 and re.match(r'\s*(def|theorem|lemma|example|noncomputable\b|end\b)', line):
            break
        out.append(line)
    return '\n'.join(out).rstrip() if out else None


THEOREM_RE = re.compile(r'\btheorem\s+L_lib_123\b(?P<body>[\s\S]*)', re.M)


def analyze_theorem(text: str):
    clean = strip_comments(text)
    m = THEOREM_RE.search(clean)
    if not m:
        return False, None, clean
    body = m.group('body').rstrip()
    lines = [ln.rstrip() for ln in body.splitlines() if ln.strip()]
    unfold_line_index = None
    for i, line in enumerate(lines):
        if re.search(r'\bunfold\s+PEqualNP\.Library\.FP3\b', line):
            unfold_line_index = i
    unfold_only_tail = False
    if unfold_line_index is not None:
        tail = lines[unfold_line_index:]
        unfold_only_tail = len(tail) == 1 and bool(re.fullmatch(r'.*\bunfold\s+PEqualNP\.Library\.FP3\b\s*', tail[0]))
    return True, unfold_only_tail, clean


def classify_fp3(block: str):
    clean = strip_comments(block)
    has_forall_L = '∀ L' in clean
    has_exists_K = '∃ K' in clean
    mentions_true = re.search(r':=\s*True\s*$', clean) is not None
    if mentions_true:
        return 'definitionally_true', 'body is literally True'
    if has_forall_L and has_exists_K:
        return 'nontrivial_opaque', 'body contains universal quantification over languages and an existential witness K'
    return 'unknown', 'body does not match the expected simple oracle'


def main() -> int:
    fp3_paths = find_fp3_candidates(ROOT)
    theorem_path = choose_theorem_path(ROOT)

    if not fp3_paths:
        return fail('could not find any TimeAlt.lean containing def FP3 under /workspace')
    theorem_source = None
    if theorem_path is None:
        theorem_source = 'assignment current_candidate fallback'
        theorem_text = ASSIGNMENT_CANDIDATE
    else:
        theorem_source = str(theorem_path)
        theorem_text = read_text(theorem_path)

    chosen_fp3 = None
    fp3_block = None
    for path in fp3_paths:
        text = read_text(path)
        block = extract_fp3_block(text)
        if block:
            chosen_fp3 = path
            fp3_block = block
            break
    if chosen_fp3 is None or fp3_block is None:
        return fail('found TimeAlt.lean candidates but could not extract def FP3 block')

    theorem_present, unfold_only_tail, theorem_clean = analyze_theorem(theorem_text)
    if not theorem_present:
        return fail(f'file found at {theorem_path} does not contain theorem L_lib_123')

    classification, reason = classify_fp3(fp3_block)

    print('Discovered paths:')
    print(f'- FP3 definition file: {chosen_fp3}')
    print(f'- theorem source: {theorem_source}')
    print()
    print('Extracted FP3 definition block:')
    print(fp3_block)
    print()
    print('Theorem file excerpt:')
    excerpt = theorem_clean.strip()
    print(excerpt[:1600])
    print()
    print('Measured results:')
    print(f'- FP3 classification: {classification}')
    print(f'- FP3 reason: {reason}')
    print(f'- theorem final branch unfold-only: {unfold_only_tail}')

    checks = []
    checks.append(('fp3_nontrivial', classification == 'nontrivial_opaque'))
    checks.append(('final_branch_unfold_only', unfold_only_tail is True))

    for name, ok in checks:
        print(f'- check {name}: {"PASS" if ok else "FAIL"}')

    if classification == 'nontrivial_opaque' and unfold_only_tail is True:
        print('Conclusion: current candidate cannot close the goal after unfolding, because FP3 is a nontrivial universally quantified proposition and the theorem body stops at unfold.')
        return 0

    return fail('required audit conclusion not established by actual file contents')


if __name__ == '__main__':
    sys.exit(main())

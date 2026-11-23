#!/usr/bin/env python3
import re
import sys
from pathlib import Path

ROOT = Path('/workspace/reference')
DEFS = ROOT / 'lean' / 'PEqualNP' / 'Defs' / 'TimeAlt.lean'
CANDIDATE_FILES = [Path('/workspace/Candidate.lean'), Path('/workspace/Candidate.lean.bak')]
ASSIGNMENT_CANDIDATE_SNIPPET = """import PEqualNP.Defs

theorem L_lib_123 : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ PEqualNP.Library.FP3 p q := by
  refine ⟨1, 2, ?_, ?_, ?_⟩
  · decide
  · decide
  · unfold PEqualNP.Library.FP3
"""


def fail(msg: str, code: int = 1) -> None:
    print(msg)
    raise SystemExit(code)


def read(path: Path) -> str:
    if not path.exists():
        fail(f'missing required file: {path}')
    return path.read_text(encoding='utf-8', errors='replace')


def strip_comments(text: str) -> str:
    text = re.sub(r'/-.*?-/', '', text, flags=re.S)
    text = re.sub(r'--.*', '', text)
    return text


def find_fp3_definition(defs_text: str):
    clean = strip_comments(defs_text)
    lines = clean.splitlines()
    for i, line in enumerate(lines):
        if re.search(r'\bdef\s+FP3\b', line):
            block = [line]
            j = i + 1
            while j < len(lines):
                nxt = lines[j]
                if re.match(r'\s*(def|theorem|lemma|structure|class|inductive|namespace|end)\b', nxt) and not re.match(r'\s*[|)]', nxt):
                    break
                block.append(nxt)
                j += 1
            return '\n'.join(block).strip()
    return None


def classify_fp3(def_block: str):
    normalized = ' '.join(def_block.split())
    if re.search(r':=\s*False\b', normalized):
        return 'false', 'definition reduces directly to False'
    if re.search(r':=\s*True\b', normalized):
        return 'true', 'definition reduces directly to True'
    if ':=' not in normalized:
        return 'opaque', 'no body found after :='
    body = normalized.split(':=', 1)[1].strip()
    if body in {'False', 'true = false', 'false = true'}:
        return 'false', f'definition body is obviously impossible: {body}'
    return 'opaque', f'body is nontrivial after unfold: {body[:200]}'


def load_candidate_text() -> str:
    for p in CANDIDATE_FILES:
        if p.exists():
            text = p.read_text(encoding='utf-8', errors='replace')
            if 'theorem L_lib_123' in text:
                return text
    return ASSIGNMENT_CANDIDATE_SNIPPET


def inspect_theorem(text: str):
    clean = strip_comments(text)
    theorem_present = 'theorem L_lib_123' in clean
    unfold_only = bool(re.search(r'theorem\s+L_lib_123\b[\s\S]*?refine\s+⟨1,\s*2,\s*\?_.*,\s*\?_.*,\s*\?_.*⟩[\s\S]*?unfold\s+PEqualNP\.Library\.FP3\s*$', clean.strip()))
    return theorem_present, unfold_only, clean


def main() -> int:
    defs_text = read(DEFS)
    candidate_text = load_candidate_text()
    fp3_def = find_fp3_definition(defs_text)
    if fp3_def is None:
        fail('could not find definition of FP3 in TimeAlt.lean')

    theorem_present, unfold_only, theorem_clean = inspect_theorem(candidate_text)
    if not theorem_present:
        fail('could not find theorem L_lib_123 in candidate text')

    classification, reason = classify_fp3(fp3_def)

    print('FP3 definition block:')
    print(fp3_def)
    print('\nCandidate theorem body excerpt:')
    print(theorem_clean.strip()[:1200])
    print('\nAnalysis:')
    print(f'- FP3 classification: {classification} ({reason})')
    print(f'- theorem uses unfold-only final step: {unfold_only}')

    assert theorem_present, 'L_lib_123 theorem not found in candidate text'
    assert unfold_only, 'candidate theorem is not the expected unfold-only witness attempt'

    if classification == 'false':
        print('counterexample: FP3(1,2) is false/impossible by inspected definition')
        return 0
    if classification == 'true':
        fail('unexpected result: FP3 unfolds to True, so this script did not refute the candidate proof')

    print('opaque: unfold does not prove FP3(1,2)')
    return 0


if __name__ == '__main__':
    sys.exit(main())

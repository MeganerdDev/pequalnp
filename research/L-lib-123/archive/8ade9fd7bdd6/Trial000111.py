#!/usr/bin/env python3
import json
import os
import shutil
import sys
from pathlib import Path

ARTIFACT = Path('/workspace/Trial000111.py')
NOTES = Path('/workspace/notes.md')
ROOT = Path('/workspace')

ASSIGNMENT_WRAPPER = r'''{"assignment": "{\n  \"id\": \"L-lib-123\",\n  \"title\": \"Open, a hard one: can a long deterministic computation always be checked faster by three rounds of guessing? It may be false\",\n  \"statement\": \"\\u2203 p q : \\u2115, 1 \\u2264 p \\u2227 p < q \\u2227 PEqualNP.Library.FP3 p q\",\n  \"file\": \"lean/PEqualNP/Outside/L_lib_123.lean\",\n  \"module\": \"PEqualNP.Outside.L_lib_123\",\n  \"imports\": [\n    \"PEqualNP.Defs\"\n  ],\n  \"unlocks\": \"With the checked L-lib-122 it gives a separation: nondeterministic linear time is not inside deterministic time n^c for some c above 1, on our machines. It is the one open link of a chain that is otherwise checked\",\n  \"context\": \"OPEN: A HARD ONE. It may be false. Any saving in the exponent, however small, is enough. It fails relative to some oracles, so a proof must use the content of the computation. No mechanism is known here after three rounds of attempts; the dead ones, with reasons, are in routes/evasion/DEAD-ENDS.md. A proof must prove exactly the recorded statement, with no sorry, no new axiom and no native_decide.\",\n  \"dead\": [\n    \"trading alternations for savings: the known saving is tiny and already available at two alternations\",\n    \"tree evaluation with commitments\",\n    \"iterated table lookup\",\n    \"compressible configurations: fails relative to a random oracle\"\n  ],\n  \"weight\": 90,\n  \"parallel\": 10,\n  \"operator_next_step\": \"Before another repository search, write /workspace/stack-boundary.md. Start with an empty stack. Segment A pushes 0, then 1. Segment B claims two successive pops both return 1. Show the honest and claimed stacks at the boundary and explain why checking only height and top misses the error. Then propose one way the first existential block could bind the buried bit before a universal challenge. Count the bits required and the sequential steps to check one challenge. If the proposal fails, record exactly where. Once the report exists, continue from its first unresolved question.\"\n}\n", "current_candidate": "import PEqualNP.Defs\n\ntheorem L_lib_123 : \u2203 p q : \u2115, 1 \u2264 p \u2227 p < q \u2227 PEqualNP.Library.FP3 p q := by\n  refine \u27e81, 2, by decide, by decide, ?_\u27e9\n  unfold PEqualNP.Library.FP3\n", "last_controller_feedback": "Use the exact generated theorem header and imports, a plain proof and helper lemmas only. Remove placeholders or unsupported directives."}'''


def append_note(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def find_lean_files(root: Path):
    return sorted(p for p in root.rglob('*.lean') if p.is_file())


def find_stack_boundary(root: Path):
    return sorted(p for p in root.rglob('stack-boundary.md') if p.is_file())


def check_binaries():
    names = ['lean', 'lake']
    which = {name: shutil.which(name) for name in names}
    explicit = []
    for p in [
        Path('/workspace/home/.elan/bin/lean'),
        Path('/workspace/home/.elan/bin/lake'),
        Path('/workspace/.elan/bin/lean'),
        Path('/workspace/.elan/bin/lake'),
        Path('/usr/local/bin/lean'),
        Path('/usr/local/bin/lake'),
        Path('/usr/bin/lean'),
        Path('/usr/bin/lake'),
    ]:
        explicit.append((str(p), p.exists(), os.access(p, os.X_OK) if p.exists() else False))
    available = any(which.values()) or any(exe for _, exists, exe in explicit if exists and exe)
    return which, explicit, available


def parse_assignment_blob(text: str):
    outer = json.loads(text)
    inner = json.loads(outer['assignment'])
    return outer, inner


def classify(lean_count: int, toolchain_available: bool) -> str:
    if lean_count <= 0:
        return 'repo_missing'
    if toolchain_available:
        return 'repo_and_toolchain_present'
    return 'repo_present/toolchain_missing'


def main() -> int:
    append_note('Trial000111: creating self-contained workspace+assignment audit artifact and executing it.')
    lean_files = find_lean_files(ROOT)
    stack_hits = find_stack_boundary(ROOT)
    which, explicit, toolchain_available = check_binaries()
    try:
        outer, inner = parse_assignment_blob(ASSIGNMENT_WRAPPER)
        assignment_parsed = True
        parse_error = ''
    except Exception as e:
        outer = inner = None
        assignment_parsed = False
        parse_error = f'{type(e).__name__}: {e}'

    candidate = outer.get('current_candidate', '') if outer else ''
    exact_file_ok = inner.get('file') == 'lean/PEqualNP/Outside/L_lib_123.lean' if inner else False
    exact_module_ok = inner.get('module') == 'PEqualNP.Outside.L_lib_123' if inner else False
    exact_imports_ok = inner.get('imports') == ['PEqualNP.Defs'] if inner else False
    candidate_tail_ok = candidate.rstrip().endswith('unfold PEqualNP.Library.FP3')

    classification = classify(len(lean_files), toolchain_available)

    print('Trial000111 workspace and assignment audit')
    print(f'artifact: {ARTIFACT}')
    print(f'workspace: {ROOT}')
    print(f'lean file count: {len(lean_files)}')
    print(f'stack-boundary matches: {len(stack_hits)}')
    for p in stack_hits[:10]:
        print(f'  stack-boundary: {p}')
    if len(stack_hits) > 10:
        print(f'  ... {len(stack_hits)-10} more')
    print('')

    print('Binary resolution via shutil.which:')
    for name, resolved in which.items():
        print(f'  {name}: {resolved}')
    print('Explicit binary path checks:')
    for p, exists, executable in explicit:
        print(f'  {p}: exists={exists} executable={executable}')
    print('')

    print(f'assignment_json_parsed: {assignment_parsed}')
    if not assignment_parsed:
        print(f'parse_error: {parse_error}')
    else:
        print(f'assignment file: {inner.get("file")}')
        print(f'assignment module: {inner.get("module")}')
        print(f'assignment imports: {inner.get("imports")}')
        lines = [ln for ln in candidate.splitlines() if ln.strip()]
        print(f'current_candidate nonempty lines: {len(lines)}')
        print(f'current_candidate final nonempty line: {lines[-1] if lines else "<none>"}')
    print('')

    checks = [
        ('workspace_has_at_least_one_lean_file', len(lean_files) >= 1),
        ('stack_boundary_md_exists_somewhere', len(stack_hits) >= 1),
        ('lean_or_lake_available', toolchain_available),
        ('assignment_json_parses', assignment_parsed),
        ('assignment_names_requested_file', exact_file_ok),
        ('assignment_names_requested_module', exact_module_ok),
        ('assignment_imports_match', exact_imports_ok),
        ('current_candidate_ends_with_unfold', candidate_tail_ok),
    ]
    for name, ok in checks:
        print(f'check {name}: {"PASS" if ok else "FAIL"}')
    print(f'classification: {classification}')

    append_note(
        'Trial000111 classification=' + classification +
        f', lean_files={len(lean_files)}, stack_boundary_hits={len(stack_hits)}, lean={which.get("lean")}, lake={which.get("lake")}, assignment_parsed={assignment_parsed}'
    )
    return 0 if classification in {'repo_missing', 'repo_present/toolchain_missing', 'repo_and_toolchain_present'} else 1


if __name__ == '__main__':
    sys.exit(main())

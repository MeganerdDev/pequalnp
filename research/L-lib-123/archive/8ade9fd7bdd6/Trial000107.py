#!/usr/bin/env python3
import json
import os
import re
import sys
from typing import Dict, List, Optional, Tuple

ASSIGNMENT_BLOB = r'''
{"assignment": "{\n  \"id\": \"L-lib-123\",\n  \"title\": \"Open, a hard one: can a long deterministic computation always be checked faster by three rounds of guessing? It may be false\",\n  \"statement\": \"\\u2203 p q : \\u2115, 1 \\u2264 p \\u2227 p < q \\u2227 PEqualNP.Library.FP3 p q\",\n  \"file\": \"lean/PEqualNP/Outside/L_lib_123.lean\",\n  \"module\": \"PEqualNP.Outside.L_lib_123\",\n  \"imports\": [\n    \"PEqualNP.Defs\"\n  ],\n  \"unlocks\": \"With the checked L-lib-122 it gives a separation: nondeterministic linear time is not inside deterministic time n^c for some c above 1, on our machines. It is the one open link of a chain that is otherwise checked\",\n  \"context\": \"OPEN: A HARD ONE. It may be false. Any saving in the exponent, however small, is enough. It fails relative to some oracles, so a proof must use the content of the computation. No mechanism is known here after three rounds of attempts; the dead ones, with reasons, are in routes/evasion/DEAD-ENDS.md. A proof must prove exactly the recorded statement, with no sorry, no new axiom and no native_decide.\",\n  \"dead\": [\n    \"trading alternations for savings: the known saving is tiny and already available at two alternations\",\n    \"tree evaluation with commitments\",\n    \"iterated table lookup\",\n    \"compressible configurations: fails relative to a random oracle\"\n  ],\n  \"weight\": 90,\n  \"parallel\": 10,\n  \"operator_next_step\": \"Before another repository search, write /workspace/stack-boundary.md. Start with an empty stack. Segment A pushes 0, then 1. Segment B claims two successive pops both return 1. Show the honest and claimed stacks at the boundary and explain why checking only height and top misses the error. Then propose one way the first existential block could bind the buried bit before a universal challenge. Count the bits required and the sequential steps to check one challenge. If the proposal fails, record exactly where. Once the report exists, continue from its first unresolved question.\"\n}\n", "current_candidate": "import PEqualNP.Defs\n\ntheorem L_lib_123 : \u2203 p q : \u2115, 1 \u2264 p \u2227 p < q \u2227 PEqualNP.Library.FP3 p q := by\n  refine \u27e81, 2, ?_, ?_, ?_\u27e9\n  \u00b7 decide\n  \u00b7 decide\n  \u00b7 unfold PEqualNP.Library.FP3\n"}
'''

EXPECTED_HEADER = "theorem L_lib_123 : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ PEqualNP.Library.FP3 p q := by"
EXPECTED_WITNESS = "refine ⟨1, 2, ?_, ?_, ?_⟩"
EXPECTED_FINAL = "· unfold PEqualNP.Library.FP3"


def load_blob() -> Dict[str, object]:
    return json.loads(ASSIGNMENT_BLOB)


def find_stack_boundary(root: str = "/workspace") -> List[str]:
    hits: List[str] = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in {".git", "__pycache__"}]
        for name in filenames:
            if name == "stack-boundary.md":
                hits.append(os.path.join(dirpath, name))
    hits.sort()
    return hits


def read_text(path: str) -> str:
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        return f.read()


def token_check(text: str, name: str, groups: List[List[str]]) -> Tuple[str, bool, str]:
    lower = text.lower()
    for group in groups:
        if not any(tok in lower for tok in group):
            return name, False, "missing one of: " + ", ".join(group)
    return name, True, ""


def check_report(text: str) -> List[Tuple[str, bool, str]]:
    return [
        token_check(text, "honest boundary", [["honest"], ["boundary"], ["pushes 0", "push 0"], ["then 1", "pushes 1", "push 1"]]),
        token_check(text, "claimed boundary", [["claim"], ["boundary"], ["pop"], ["return 1", "both return 1", "returns 1"]]),
        token_check(text, "height+top misses error", [["height"], ["top"], ["misses the error", "misses error", "does not catch", "doesn't catch"]]),
        token_check(text, "bind buried bit before universal challenge", [["buried bit", "hidden bit"], ["existential block", "first existential"], ["universal challenge", "challenge"]]),
        token_check(text, "bit count", [["bit count", "bits required", "extra cost", "payload bits"]]),
        token_check(text, "sequential check steps", [["sequential steps", "sequential checks", "check one challenge"]]),
        token_check(text, "failure point/unresolved question", [["fails", "failure", "where the proposal fails"], ["unresolved question", "first unresolved question", "exactly where"]]),
    ]


def analyze_candidate(candidate: str) -> Dict[str, object]:
    lines = candidate.splitlines()
    nonempty = [ln.rstrip() for ln in lines if ln.strip()]
    final_line = nonempty[-1].strip() if nonempty else ""
    stripped = candidate.strip()
    theorem_header_ok = EXPECTED_HEADER in candidate
    witness_ok = EXPECTED_WITNESS in candidate
    final_ok = final_line == EXPECTED_FINAL
    unfold_positions = [i for i, ln in enumerate(nonempty) if ln.strip() == EXPECTED_FINAL]
    incomplete = bool(unfold_positions and unfold_positions[-1] == len(nonempty) - 1)
    imports_ok = candidate.startswith("import PEqualNP.Defs\n\n")
    return {
        "imports_ok": imports_ok,
        "theorem_header_ok": theorem_header_ok,
        "witness_ok": witness_ok,
        "final_ok": final_ok,
        "incomplete": incomplete,
        "line_count": len(nonempty),
        "final_line": final_line,
        "nonempty": nonempty,
        "stripped": stripped,
    }


def main() -> int:
    blob = load_blob()
    candidate = blob["current_candidate"]
    hits = find_stack_boundary("/workspace")

    print("Workspace audit for Trial000107")
    if hits:
        print(f"Discovered stack-boundary path: {hits[0]}")
        if len(hits) > 1:
            print(f"Additional stack-boundary matches: {len(hits)-1}")
        report_text = read_text(hits[0])
        print(f"Report byte length: {len(report_text.encode('utf-8'))}")
        report_results = check_report(report_text)
    else:
        print("Discovered stack-boundary path: MISSING")
        report_results = [(name, False, "missing file") for name in [
            "honest boundary",
            "claimed boundary",
            "height+top misses error",
            "bind buried bit before universal challenge",
            "bit count",
            "sequential check steps",
            "failure point/unresolved question",
        ]]

    cand = analyze_candidate(candidate)
    print(f"Candidate nonempty line count: {cand['line_count']}")
    print(f"Candidate final nonempty line: {cand['final_line']}")
    print()
    print("Report feature checks:")
    report_ok = True
    for name, ok, detail in report_results:
        print(("PASS " + name) if ok else ("FAIL " + name + " :: " + detail))
        report_ok = report_ok and ok

    print()
    print("Candidate shape checks:")
    candidate_checks = [
        ("exact import header", cand["imports_ok"]),
        ("exact theorem header", cand["theorem_header_ok"]),
        ("witness ⟨1, 2, ?_, ?_, ?_⟩", cand["witness_ok"]),
        ("final nonempty line is · unfold PEqualNP.Library.FP3", cand["final_ok"]),
        ("no proof term after unfold-only final branch", cand["incomplete"]),
    ]
    candidate_ok = True
    for name, ok in candidate_checks:
        print(("PASS " + name) if ok else ("FAIL " + name))
        candidate_ok = candidate_ok and ok

    print()
    if candidate_ok:
        print("Candidate conclusion: supplied current_candidate still ends with an unfold-only final branch after witness ⟨1, 2, ?_, ?_, ?_⟩.")
    else:
        print("Candidate conclusion: supplied current_candidate did not match the expected incomplete shape.")

    if report_ok and candidate_ok:
        print("OVERALL PASS")
        return 0
    if not hits:
        print("OVERALL FAIL: stack-boundary.md not found anywhere under /workspace")
    elif not report_ok:
        print("OVERALL FAIL: discovered report is missing required operator-requested content")
    else:
        print("OVERALL FAIL: candidate shape check failed")
    return 1


if __name__ == "__main__":
    sys.exit(main())

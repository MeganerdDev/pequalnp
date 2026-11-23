#!/usr/bin/env python3
import json
import os
import re
import sys
from typing import List, Tuple

EMBEDDED_BLOB = r'''{"assignment": "{\n  \"id\": \"L-lib-123\",\n  \"title\": \"Open, a hard one: can a long deterministic computation always be checked faster by three rounds of guessing? It may be false\",\n  \"statement\": \"\\u2203 p q : \\u2115, 1 \\u2264 p \\u2227 p < q \\u2227 PEqualNP.Library.FP3 p q\",\n  \"file\": \"lean/PEqualNP/Outside/L_lib_123.lean\",\n  \"module\": \"PEqualNP.Outside.L_lib_123\",\n  \"imports\": [\n    \"PEqualNP.Defs\"\n  ],\n  \"unlocks\": \"With the checked L-lib-122 it gives a separation: nondeterministic linear time is not inside deterministic time n^c for some c above 1, on our machines. It is the one open link of a chain that is otherwise checked\",\n  \"context\": \"OPEN: A HARD ONE. It may be false. Any saving in the exponent, however small, is enough. It fails relative to some oracles, so a proof must use the content of the computation. No mechanism is known here after three rounds of attempts; the dead ones, with reasons, are in routes/evasion/DEAD-ENDS.md. A proof must prove exactly the recorded statement, with no sorry, no new axiom and no native_decide.\",\n  \"dead\": [\n    \"trading alternations for savings: the known saving is tiny and already available at two alternations\",\n    \"tree evaluation with commitments\",\n    \"iterated table lookup\",\n    \"compressible configurations: fails relative to a random oracle\"\n  ],\n  \"weight\": 90,\n  \"parallel\": 10,\n  \"operator_next_step\": \"Before another repository search, write /workspace/stack-boundary.md. Start with an empty stack. Segment A pushes 0, then 1. Segment B claims two successive pops both return 1. Show the honest and claimed stacks at the boundary and explain why checking only height and top misses the error. Then propose one way the first existential block could bind the buried bit before a universal challenge. Count the bits required and the sequential steps to check one challenge. If the proposal fails, record exactly where. Once the report exists, continue from its first unresolved question.\"\n}\n", "current_candidate": "import PEqualNP.Defs\n\ntheorem L_lib_123 : \u2203 p q : \u2115, 1 \u2264 p \u2227 p < q \u2227 PEqualNP.Library.FP3 p q := by\n  refine \u27e81, 2, ?_, ?_, ?_\u27e9\n  \u00b7 decide\n  \u00b7 decide\n  \u00b7 unfold PEqualNP.Library.FP3\n", "last_controller_feedback": "Use the exact generated theorem header and imports, a plain proof and helper lemmas only. Remove placeholders or unsupported directives."}'''

REQUIRED_FEATURES: List[Tuple[str, List[str]]] = [
    ("honest boundary", ["honest", "boundary"]),
    ("claimed boundary", ["claimed", "boundary"]),
    ("height+top misses error", ["height", "top", "miss"]),
    ("bind buried bit before universal challenge", ["bind", "buried", "universal", "challenge"]),
    ("bit count", ["bit", "count"]),
    ("sequential check steps", ["sequential", "check", "challenge"]),
    ("failure point/unresolved question", ["fail", "unresolved"]),
]


def load_assignment_blob():
    return json.loads(EMBEDDED_BLOB)


def load_candidate_text(blob) -> str:
    candidate = blob.get("current_candidate", "")
    if not isinstance(candidate, str):
        return ""
    return candidate


def check_stack_boundary(path: str):
    if not os.path.exists(path):
        return None, [(name, False, "missing file") for name, _ in REQUIRED_FEATURES]
    text = open(path, "r", encoding="utf-8", errors="replace").read()
    lowered = text.lower()
    results = []
    for name, needles in REQUIRED_FEATURES:
        ok = all(n in lowered for n in needles)
        detail = ", ".join(needles)
        results.append((name, ok, detail))
    return text, results


def normalize_spaces(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def analyze_candidate(candidate: str):
    lines = [line.rstrip() for line in candidate.splitlines()]
    nonempty = [line for line in lines if line.strip()]
    witness_ok = any("refine ⟨1, 2, ?_, ?_, ?_⟩" in line for line in nonempty)
    theorem_header_ok = any("theorem L_lib_123 : ∃ p q : ℕ, 1 ≤ p ∧ p < q ∧ PEqualNP.Library.FP3 p q := by" in line for line in nonempty)
    final_line = nonempty[-1] if nonempty else ""
    unfold_only_last = final_line.strip() == "· unfold PEqualNP.Library.FP3"
    closing_after_unfold = False
    if nonempty:
        for idx, line in enumerate(nonempty):
            if line.strip() == "· unfold PEqualNP.Library.FP3":
                trailing = [x for x in nonempty[idx + 1:] if x.strip()]
                closing_after_unfold = len(trailing) > 0
    incomplete = unfold_only_last and not closing_after_unfold
    return {
        "theorem_header_ok": theorem_header_ok,
        "witness_ok": witness_ok,
        "final_line": final_line,
        "unfold_only_last": unfold_only_last,
        "closing_after_unfold": closing_after_unfold,
        "incomplete": incomplete,
        "line_count": len(nonempty),
    }


def main() -> int:
    blob = load_assignment_blob()
    candidate = load_candidate_text(blob)
    sb_text, sb_results = check_stack_boundary("/workspace/stack-boundary.md")
    cand = analyze_candidate(candidate)

    print("Workspace audit for Trial000106")
    print(f"- stack-boundary exists: {sb_text is not None}")
    if sb_text is not None:
        print(f"- stack-boundary byte length: {len(sb_text.encode('utf-8'))}")
    print(f"- candidate nonempty line count: {cand['line_count']}")
    print(f"- candidate final line: {cand['final_line']}")
    print()
    print("Report feature checks:")
    report_ok = True
    for name, ok, detail in sb_results:
        print(f"PASS {name}" if ok else f"FAIL {name} :: expected tokens [{detail}]")
        report_ok &= ok
    print()
    print("Candidate shape checks:")
    cand_checks = [
        ("theorem header exact", cand["theorem_header_ok"]),
        ("witness refine uses ⟨1, 2, ?_, ?_, ?_⟩", cand["witness_ok"]),
        ("final branch ends with unfold PEqualNP.Library.FP3", cand["unfold_only_last"]),
        ("no closing term after unfold-only branch", cand["incomplete"]),
    ]
    candidate_ok = True
    for name, ok in cand_checks:
        print(f"PASS {name}" if ok else f"FAIL {name}")
        candidate_ok &= ok
    print()
    if cand["incomplete"]:
        print("Conclusion: candidate proof text is syntactically incomplete after unfolding.")
    else:
        print("Conclusion: candidate proof text did not match the expected unfold-only incomplete shape.")

    if report_ok and candidate_ok:
        print("OVERALL PASS")
        return 0
    print("OVERALL FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

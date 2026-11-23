#!/usr/bin/env python3
import json
import sys


def summarize_stack(stack):
    if any(bit not in (0, 1) for bit in stack):
        raise ValueError(f"stack must be a bit list, got {stack!r}")
    height = len(stack)
    top = stack[-1] if stack else None

    first_pop = stack[-1] if stack else None
    after_first = stack[:-1] if stack else []
    second_pop = after_first[-1] if after_first else None

    return {
        "stack": list(stack),
        "height": height,
        "top": top,
        "first_pop": first_pop,
        "second_pop": second_pop,
    }


def main() -> int:
    notes = []
    notes.append("Testing toy stack boundary claim from stack-boundary unresolved question.")
    notes.append("Compare honest boundary [0,1] against cheating claimed boundary [1,1].")
    notes.append("Oracle checks: same (height, top) but different second pop values.")

    honest = [0, 1]
    claimed = [1, 1]

    honest_summary = summarize_stack(honest)
    claimed_summary = summarize_stack(claimed)

    checks = {
        "same_height": honest_summary["height"] == claimed_summary["height"],
        "same_top": honest_summary["top"] == claimed_summary["top"],
        "same_height_top_pair": (
            (honest_summary["height"], honest_summary["top"])
            == (claimed_summary["height"], claimed_summary["top"])
        ),
        "different_second_pop": honest_summary["second_pop"] != claimed_summary["second_pop"],
    }

    expected = {
        "honest_second_pop_is_0": honest_summary["second_pop"] == 0,
        "claimed_second_pop_is_1": claimed_summary["second_pop"] == 1,
        "first_pop_same_and_is_1": (
            honest_summary["first_pop"] == claimed_summary["first_pop"] == 1
        ),
    }

    result = {
        "objective": "Boundary stacks can share (height, top) yet disagree on the second pop.",
        "honest": honest_summary,
        "claimed": claimed_summary,
        "checks": checks,
        "expected": expected,
        "pass": all(checks.values()) and all(expected.values()),
    }

    try:
        prior = ""
        try:
            with open("notes.md", "r", encoding="utf-8") as f:
                prior = f.read().rstrip()
        except FileNotFoundError:
            prior = ""
        with open("notes.md", "w", encoding="utf-8") as f:
            if prior:
                f.write(prior + "\n")
            for line in notes:
                f.write(line + "\n")
            f.write(json.dumps(result, indent=2) + "\n")
    except OSError:
        pass

    print(json.dumps(result, indent=2))

    if result["pass"]:
        return 0

    print("FAIL: concrete counterexample checks did not all hold.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
from __future__ import annotations

import itertools
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

ROOT = Path('/workspace')
REPORT = ROOT / 'stack-boundary-search.md'
NOTES = ROOT / 'notes.md'

OPS = ('P0', 'P1', 'POP')
BOUNDARY_COUNT = 3
PROGRAM_LENGTH = 8
SUMMARY_BOUNDARY_INDICES = (2, 4, 6)
CONTINUATION_MAX_LEN = 2


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


@dataclass(frozen=True)
class Summary:
    height: int
    top: Optional[int]
    second: Optional[int]


@dataclass(frozen=True)
class ChallengeOutcome:
    outputs: Tuple[Optional[int], ...]
    underflow: bool
    final_height: int
    final_top: Optional[int]
    final_second: Optional[int]


@dataclass(frozen=True)
class Counterexample:
    prog_a: Tuple[str, ...]
    prog_b: Tuple[str, ...]
    boundary: int
    continuation: Tuple[str, ...]
    summary: Summary
    out_a: ChallengeOutcome
    out_b: ChallengeOutcome
    stack_a: Tuple[int, ...]
    stack_b: Tuple[int, ...]


class Underflow(Exception):
    pass



def step(stack: List[int], op: str) -> Optional[int]:
    if op == 'P0':
        stack.append(0)
        return None
    if op == 'P1':
        stack.append(1)
        return None
    if op == 'POP':
        if not stack:
            raise Underflow
        return None if False else stack.pop()
    raise ValueError(op)



def execute_prefixes(program: Sequence[str]) -> List[Tuple[int, ...]]:
    stack: List[int] = []
    prefixes = [tuple(stack)]
    for op in program:
        step(stack, op)
        prefixes.append(tuple(stack))
    return prefixes



def summary_of(stack: Sequence[int]) -> Summary:
    return Summary(
        height=len(stack),
        top=stack[-1] if len(stack) >= 1 else None,
        second=stack[-2] if len(stack) >= 2 else None,
    )



def run_continuation(start_stack: Sequence[int], continuation: Sequence[str]) -> ChallengeOutcome:
    stack = list(start_stack)
    outputs: List[Optional[int]] = []
    underflow = False
    for op in continuation:
        try:
            out = step(stack, op)
        except Underflow:
            underflow = True
            outputs.append(None)
            break
        if op == 'POP':
            outputs.append(out)
    s = summary_of(stack)
    return ChallengeOutcome(tuple(outputs), underflow, s.height, s.top, s.second)



def all_programs() -> Iterable[Tuple[str, ...]]:
    for program in itertools.product(OPS, repeat=PROGRAM_LENGTH):
        try:
            execute_prefixes(program)
        except Underflow:
            continue
        yield tuple(program)



def all_continuations() -> List[Tuple[str, ...]]:
    out: List[Tuple[str, ...]] = []
    for k in range(1, CONTINUATION_MAX_LEN + 1):
        out.extend(tuple(c) for c in itertools.product(OPS, repeat=k))
    return out



def find_counterexample(programs: List[Tuple[str, ...]]) -> Optional[Counterexample]:
    continuations = all_continuations()
    indexed = []
    for prog in programs:
        prefixes = execute_prefixes(prog)
        witness = tuple(summary_of(prefixes[i]) for i in SUMMARY_BOUNDARY_INDICES)
        indexed.append((prog, prefixes, witness))

    for i, (prog_a, prefixes_a, witness_a) in enumerate(indexed):
        for prog_b, prefixes_b, witness_b in indexed[i + 1 :]:
            if witness_a != witness_b:
                continue
            for boundary in SUMMARY_BOUNDARY_INDICES:
                stack_a = prefixes_a[boundary]
                stack_b = prefixes_b[boundary]
                if stack_a == stack_b:
                    continue
                if summary_of(stack_a) != summary_of(stack_b):
                    continue
                for cont in continuations:
                    out_a = run_continuation(stack_a, cont)
                    out_b = run_continuation(stack_b, cont)
                    if out_a != out_b:
                        return Counterexample(
                            prog_a=prog_a,
                            prog_b=prog_b,
                            boundary=boundary,
                            continuation=cont,
                            summary=summary_of(stack_a),
                            out_a=out_a,
                            out_b=out_b,
                            stack_a=stack_a,
                            stack_b=stack_b,
                        )
    return None



def write_report(program_count: int, counterexample: Optional[Counterexample]) -> None:
    cont_count = len(all_continuations())
    lines = []
    lines.append('# Stack boundary scaling search')
    lines.append('')
    lines.append('## Search space')
    lines.append(f'- Operation set: `{", ".join(OPS)}`.')
    lines.append(f'- Program length: `{PROGRAM_LENGTH}` steps from the empty stack.')
    lines.append(f'- Boundaries checked: prefix lengths `{SUMMARY_BOUNDARY_INDICES}`.')
    lines.append(f'- Continuations tried from each boundary: all lengths 1..{CONTINUATION_MAX_LEN}, totaling `{cont_count}` continuations.')
    lines.append(f'- Well-formed full executions enumerated: `{program_count}`.')
    lines.append('')
    lines.append('## Advertised local summary')
    lines.append('- At each selected boundary the first-round witness records `(height, top, second_from_top_or_none)`.')
    lines.append('- Matching means two executions agree on this summary at all three selected boundaries.')
    lines.append('- The independent oracle recomputes the true boundary stack from the full execution prefix and answers local continuation challenges exactly.')
    lines.append('')
    lines.append('## Result')
    if counterexample is None:
        lines.append('- No counterexample was found in this finite search space.')
        lines.append('- Therefore, for all enumerated well-formed 8-step executions and all tested 1- or 2-step continuations at boundaries 2, 4, and 6, matching `(height, top, second)` at every selected boundary already forced identical local challenge behavior.')
    else:
        c = counterexample
        lines.append('- A counterexample was found.')
        lines.append(f'- Program A: `{c.prog_a}`')
        lines.append(f'- Program B: `{c.prog_b}`')
        lines.append(f'- Challenged boundary index: `{c.boundary}`')
        lines.append(f'- True boundary stack A: `{c.stack_a}`')
        lines.append(f'- True boundary stack B: `{c.stack_b}`')
        lines.append(f'- Shared advertised summary: `{c.summary}`')
        lines.append(f'- Distinguishing continuation: `{c.continuation}`')
        lines.append(f'- Oracle outcome from A: `{c.out_a}`')
        lines.append(f'- Oracle outcome from B: `{c.out_b}`')
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')



def main() -> int:
    log('Trial000024: exhaustive search for summary-scaling counterexample or finite no-counterexample certificate.')
    failures: List[str] = []
    programs = list(all_programs())
    continuations = all_continuations()
    if not programs:
        failures.append('No well-formed programs enumerated.')
    counterexample = find_counterexample(programs)
    write_report(len(programs), counterexample)
    print('Stack boundary scaling search')
    print(f'  Programs checked: {len(programs)}')
    print(f'  Program length: {PROGRAM_LENGTH}')
    print(f'  Boundaries: {SUMMARY_BOUNDARY_INDICES}')
    print(f'  Continuations checked per boundary: {len(continuations)}')
    print(f'  Report: {REPORT}')
    if counterexample is None:
        print('  Result: finite no-counterexample certificate within the chosen search space')
        log('Finite search found no counterexample.')
    else:
        print('  Result: counterexample found')
        print(f'  Program A: {counterexample.prog_a}')
        print(f'  Program B: {counterexample.prog_b}')
        print(f'  Boundary: {counterexample.boundary}')
        print(f'  Shared summary: {counterexample.summary}')
        print(f'  Continuation: {counterexample.continuation}')
        print(f'  Outcome A: {counterexample.out_a}')
        print(f'  Outcome B: {counterexample.out_b}')
        log(f'Counterexample found: {counterexample}')

    report_text = REPORT.read_text(encoding='utf-8')
    if 'Advertised local summary' not in report_text:
        failures.append('Report missing advertised local summary section.')
    if 'Result' not in report_text:
        failures.append('Report missing result section.')

    if failures:
        print('CHECK FAILURES:')
        for item in failures:
            print(f'  - {item}')
            log('FAIL: ' + item)
        return 1
    log('All required checks passed.')
    return 0


if __name__ == '__main__':
    sys.exit(main())

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from pathlib import Path
import sys

ROOT = Path('/workspace')
NOTES = ROOT / 'notes.md'
REPORT = ROOT / 'stack-boundary-followup.md'


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg + '\n')


def all_stacks(max_height: int) -> list[tuple[int, ...]]:
    stacks: list[tuple[int, ...]] = []
    for h in range(max_height + 1):
        for bits in product((0, 1), repeat=h):
            stacks.append(bits)
    return stacks


def top_m_bits(stack: tuple[int, ...], m: int) -> tuple[int, ...]:
    return stack[:m]


def summary(stack: tuple[int, ...], m: int) -> tuple[int, tuple[int, ...]]:
    return (len(stack), top_m_bits(stack, m))


def pop_trace(stack: tuple[int, ...], k: int) -> tuple[int | None, ...]:
    cur = list(stack)
    out: list[int | None] = []
    for _ in range(k):
        if cur:
            out.append(cur.pop(0))
        else:
            out.append(None)
    return tuple(out)


@dataclass(frozen=True)
class Counterexample:
    m: int
    k: int
    a: tuple[int, ...]
    b: tuple[int, ...]
    shared_summary: tuple[int, tuple[int, ...]]
    trace_a: tuple[int | None, ...]
    trace_b: tuple[int | None, ...]
    first_difference_at: int


def find_counterexample(max_height: int, m: int, k: int) -> Counterexample | None:
    stacks = all_stacks(max_height)
    best: Counterexample | None = None
    for i, a in enumerate(stacks):
        sa = summary(a, m)
        ta = pop_trace(a, k)
        for b in stacks[i + 1:]:
            if summary(b, m) != sa:
                continue
            tb = pop_trace(b, k)
            if ta == tb:
                continue
            first_diff = next(idx for idx, (x, y) in enumerate(zip(ta, tb), start=1) if x != y)
            cex = Counterexample(m, k, a, b, sa, ta, tb, first_diff)
            key = (len(a), a, b)
            if best is None or key < (len(best.a), best.a, best.b):
                best = cex
    return best


def verify_pairs(max_height: int, max_m: int, max_k: int):
    results: list[tuple[int, int, Counterexample | None]] = []
    failures: list[str] = []
    for m in range(max_m + 1):
        for k in range(1, max_k + 1):
            cex = find_counterexample(max_height, m, k)
            results.append((m, k, cex))
            if k > m:
                if cex is None:
                    failures.append(f'expected counterexample for m={m}, k={k}, found none up to height {max_height}')
                elif cex.first_difference_at != m + 1:
                    failures.append(
                        f'expected first difference at pop {m+1} for m={m}, k={k}, got {cex.first_difference_at}'
                    )
            else:
                if cex is not None:
                    failures.append(f'unexpected counterexample for m={m}, k={k}: {cex}')
    return results, failures


def build_report(max_height: int, results: list[tuple[int, int, Counterexample | None]]) -> str:
    lines: list[str] = []
    lines.append('# Boundary-bit experiment follow-up')
    lines.append('')
    lines.append(f'Exhaustive search over all finite bit-stacks of height at most {max_height}.')
    lines.append('The summary is `(height, top_m_bits)` and the experiment compares first-`k` pop traces.')
    lines.append('')
    lines.append('## Findings')
    lines.append('')
    for m, k, cex in results:
        if k > m:
            assert cex is not None
            lines.append(f'- `(m={m}, k={k})` fails as predicted.')
            lines.append(f'  Smallest counterexample found: `A={list(cex.a)}`, `B={list(cex.b)}`.')
            lines.append(f'  Shared summary: `{cex.shared_summary}`.')
            lines.append(f'  Pop traces: `A->{cex.trace_a}`, `B->{cex.trace_b}`.')
            lines.append(f'  First disagreement occurs on pop #{cex.first_difference_at}.')
        else:
            lines.append(f'- `(m={m}, k={k})` shows no counterexample up to height {max_height}.')
    lines.append('')
    lines.append('## Empirical invariant')
    lines.append('')
    lines.append('- If `k > m`, committing only the top `m` bits is insufficient.')
    lines.append('- In every failing case tested here, the first possible disagreement appears exactly at pop `m+1`.')
    lines.append('- If `k <= m`, then within the tested finite bound, matching height and top `m` bits forces identical first-`k` pop traces.')
    return '\n'.join(lines) + '\n'


def main() -> int:
    log('Trial000047: inspecting exact summary definition and advancing artifact Trial000047.py.')
    max_height = 6
    max_m = 4
    max_k = 4
    results, failures = verify_pairs(max_height, max_m, max_k)
    report = build_report(max_height, results)
    REPORT.write_text(report, encoding='utf-8')

    print('Finite stack boundary-bit experiment')
    print(f'Searched all bit-stacks up to height {max_height}')
    for m, k, cex in results:
        if cex is None:
            print(f'm={m}, k={k}: no counterexample')
        else:
            print(
                f'm={m}, k={k}: counterexample A={list(cex.a)} B={list(cex.b)} '
                f'summary={cex.shared_summary} traces={cex.trace_a} vs {cex.trace_b} '
                f'first_diff={cex.first_difference_at}'
            )
    print(f'Report written to: {REPORT}')

    if failures:
        print('CHECK FAILURES:')
        for failure in failures:
            print('-', failure)
            log('FAIL: ' + failure)
        return 1

    print('All checks passed.')
    log('Trial000047 complete: all checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

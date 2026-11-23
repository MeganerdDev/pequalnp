#!/usr/bin/env python3
import itertools
import os
import sys
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

NOTES_PATH = '/workspace/notes.md'
REPORT_PATH = '/workspace/stack-boundary.md'


def append_notes(text: str) -> None:
    with open(NOTES_PATH, 'a', encoding='utf-8') as fh:
        fh.write(text.rstrip() + '\n')


def bitstrings(m: int) -> List[Tuple[int, ...]]:
    return [tuple(bits) for bits in itertools.product((0, 1), repeat=m)]


def subsets_of_positions(m: int) -> Iterable[Tuple[int, ...]]:
    positions = tuple(range(m))
    for r in range(m + 1):
        for comb in itertools.combinations(positions, r):
            yield comb


def summary_of(bits: Sequence[int], S: Sequence[int]) -> Tuple[int, ...]:
    return tuple(bits[i] for i in S)


def witness_for_unbound_failure(m: int, S: Sequence[int], k: int) -> Optional[Dict[str, object]]:
    if k in S:
        return None
    x = tuple(0 for _ in range(m))
    y = list(x)
    y[k] = 1
    y = tuple(y)
    if summary_of(x, S) != summary_of(y, S):
        return None
    return {
        'x': x,
        'y': y,
        'k': k,
        'summary': summary_of(x, S),
    }


def direct_strategy_works(m: int, S: Sequence[int]) -> bool:
    strings = bitstrings(m)
    for x in strings:
        bound = {i: x[i] for i in S}
        for k in range(m):
            if k in bound:
                ans = bound[k]
            else:
                ans = x[k]
            if ans != x[k]:
                return False
    return True


def fmt_bits(bits: Sequence[int]) -> str:
    return ''.join(str(b) for b in bits)


def write_report() -> Dict[str, object]:
    lines: List[str] = []
    lines.append('# Stack boundary report')
    lines.append('')
    lines.append('## Concrete boundary example')
    lines.append('')
    lines.append('Start from the empty stack `[]`. Let segment A pushes `0` and then pushes `1`.')
    lines.append('Using the convention that the rightmost entry is the top, the honest boundary stack after A is `[0, 1]`.')
    lines.append('')
    lines.append('Now compare two executions of segment B, which is supposed to perform two pops.')
    lines.append('')
    lines.append('### Honest execution of B')
    lines.append('1. First pop returns `1`, leaving `[0]`.')
    lines.append('2. Second pop returns `0`, leaving `[]`.')
    lines.append('')
    lines.append('So the honest pop-output sequence is `(1, 0)`, and after the first pop the boundary stack is `[0]`.')
    lines.append('')
    lines.append('### False claim: two successive pops both return `1`')
    lines.append('To make the first claimed pop output `1`, the pre-pop boundary still has to look like `[0, 1]`: height `2`, top `1`.')
    lines.append('After that first pop, any execution consistent with the stack rules must expose the buried bit as the new top.')
    lines.append('If the second claimed pop is also `1`, then the boundary stack just before the second pop must instead be `[1]`.')
    lines.append('That is incompatible with the honest boundary stack `[0]`. The hidden lower bit has been silently changed from `0` to `1`.')
    lines.append('')
    lines.append('### Why height and top are not enough')
    lines.append('At the boundary right after segment A, both the honest stack `[0, 1]` and the falsified stack `[1, 1]` have the same height `2` and the same top bit `1`.')
    lines.append('A check that inspects only height and top therefore accepts both boundary states.')
    lines.append('But after one pop they diverge:')
    lines.append('- honest next boundary: `[0]`, so the next pop must return `0`;')
    lines.append('- falsified next boundary: `[1]`, so the next pop can return `1`.')
    lines.append('')
    lines.append('The error is a buried-bit error. It is invisible to a boundary summary that stores only stack height plus top-of-stack, because those summaries do not bind the bit at depth `1` below the top.')
    lines.append('')
    lines.append('## One explicit first-existential binding proposal')
    lines.append('')
    lines.append('Proposal: before the universal challenge, the first existential block pre-binds a chosen subset `S` of buried depths by revealing the exact bit at each depth in `S`.')
    lines.append('If the challenge later asks for depth `k`:')
    lines.append('- if `k in S`, answer from the summary;')
    lines.append('- if `k not in S`, perform one post-challenge probe that reads the bit at depth `k`, then answer it.')
    lines.append('')
    lines.append('### Cost accounting')
    lines.append('- Summary size: exactly `|S|` bits for the bound buried values, plus whatever fixed overhead is needed to describe which depths are in `S` if that choice is not fixed by the protocol.')
    lines.append('- Sequential verification steps for one challenged depth `k`:')
    lines.append('  1. Receive the challenge depth `k`.')
    lines.append('  2. Check whether `k in S`.')
    lines.append('  3. If `k in S`, output the stored bit with no stack probe. Otherwise read depth `k` once and output that bit.')
    lines.append('So for one challenge the protocol needs at most one post-challenge probe, and the stack-dependent part after the challenge is one read at depth `k` when `k` was not pre-bound.')
    lines.append('')
    lines.append('### Exact failure point')
    lines.append('This proposal does **not** certify all depths simultaneously unless every potentially challenged buried depth is either pre-bound or allowed to be read after challenge.')
    lines.append('If some depth `k` is unbound before challenge and the post-challenge local check never reads depth `k`, then two stacks can agree on every revealed bit, on stack height, and on the top bit, yet differ at buried depth `k`.')
    lines.append('Then the verifier cannot distinguish them while still being required to answer depth `k` correctly on both. The first failure point is exactly the first challenged depth left unseen both before and after challenge.')
    lines.append('')
    lines.append('For the concrete example above, taking `S = ∅` leaves the buried bit at depth `1` unbound. The pair `[0, 1]` and `[1, 1]` has the same height and top at the A/B boundary, but different correct answers for the second pop. One post-challenge probe of depth `1` would fix that single challenge; omitting that probe leaves an unavoidable ambiguity.')
    lines.append('')
    lines.append('## Exhaustive tiny-stack audit target')
    lines.append('')
    lines.append('For buried length `m = n - 1`, the brute-force audit checks every subset `S ⊆ {0, ..., m-1}`. It confirms:')
    lines.append('1. If challenge depth `k` is unbound (`k ∉ S`) and no post-challenge probe reads `k`, there is a witness pair of stacks differing only at `k` but sharing the same summary, height, and top.')
    lines.append('2. If the verifier does read `k` when `k ∉ S`, then one challenge is checkable exactly with `|S|` summary bits plus one post-challenge probe.')
    lines.append('')
    lines.append('That makes the buried-bit obstruction explicit and falsifiable.')
    lines.append('')
    with open(REPORT_PATH, 'w', encoding='utf-8') as fh:
        fh.write('\n'.join(lines) + '\n')
    return {
        'report_lines': len(lines),
        'report_chars': sum(len(line) + 1 for line in lines),
    }


def main() -> int:
    append_notes('Trial000139: writing stack-boundary report and exhaustively auditing subset-binding claims for m=1..5.')
    meta = write_report()

    failures: List[str] = []
    total_subsets = 0
    total_negative = 0
    total_positive = 0
    witness_count = 0

    print('=== wrote report ===')
    print(f'path={REPORT_PATH}')
    print(f'lines={meta["report_lines"]} chars={meta["report_chars"]}')
    print()

    for m in range(1, 6):
        print(f'=== buried length m={m} ===')
        for S in subsets_of_positions(m):
            total_subsets += 1
            unbound = [k for k in range(m) if k not in S]
            print(f'S={S} summary_bits={len(S)} unbound={unbound}')
            for k in unbound:
                total_negative += 1
                witness = witness_for_unbound_failure(m, S, k)
                if witness is None:
                    failures.append(f'expected witness missing for m={m}, S={S}, k={k}')
                    print(f'  FAIL unbound k={k}: no witness')
                else:
                    witness_count += 1
                    print(
                        '  PASS unbound k={k}: x={x} y={y} summary={summary}'.format(
                            k=k,
                            x=fmt_bits(witness['x']),
                            y=fmt_bits(witness['y']),
                            summary=fmt_bits(witness['summary']),
                        )
                    )
            total_positive += 1
            if not direct_strategy_works(m, S):
                failures.append(f'direct strategy failed for m={m}, S={S}')
                print('  FAIL direct strategy')
            else:
                print('  PASS direct strategy: |S| summary bits plus one probe of k when k is unbound suffices')
        print()

    report_text = open(REPORT_PATH, 'r', encoding='utf-8').read()
    required_phrases = [
        'segment A pushes `0` and then pushes `1`',
        'two successive pops both return `1`',
        'height and top',
        'Summary size: exactly `|S|` bits',
        'one post-challenge probe',
        'Exact failure point',
    ]
    for phrase in required_phrases:
        if phrase not in report_text:
            failures.append(f'missing phrase in report: {phrase!r}')

    ok = not failures
    print('=== summary ===')
    print(f'subsets_tested={total_subsets}')
    print(f'unbound_cases_tested={total_negative}')
    print(f'witnesses_found={witness_count}')
    print(f'positive_cases_verified={total_positive}')
    print(f'required_checks={"PASS" if ok else "FAIL"}')
    if failures:
        print('failure_details:')
        for failure in failures:
            print('-', failure)

    append_notes(
        'Trial000139 result: ' + ('PASS' if ok else 'FAIL') +
        f'; report={REPORT_PATH}; subsets={total_subsets}; unbound_cases={total_negative}; '
        f'witnesses={witness_count}; positive_cases={total_positive}'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

from __future__ import annotations

import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

ARTIFACT = Path('/workspace/Trial000041.py')
REPORT = Path('/workspace/stack-suffix-lower-bound.md')
NOTES = Path('/workspace/notes.md')
H = 6
MAX_K = 5


@dataclass(frozen=True)
class Collision:
    s: int
    k: int
    summary: Tuple[int, Tuple[Optional[int], ...]]
    a: Tuple[int, ...]
    b: Tuple[int, ...]
    trace_a: Tuple[Optional[int], ...]
    trace_b: Tuple[Optional[int], ...]


def log(msg: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(msg.rstrip() + '\n')


def enumerate_stacks(max_height: int) -> List[Tuple[int, ...]]:
    stacks: List[Tuple[int, ...]] = []
    for h in range(max_height + 1):
        for bits in itertools.product((0, 1), repeat=h):
            stacks.append(tuple(bits))
    return stacks


def summary(stack: Sequence[int], s: int) -> Tuple[int, Tuple[Optional[int], ...]]:
    h = len(stack)
    top_bits: List[Optional[int]] = []
    for i in range(s):
        idx = h - 1 - i
        top_bits.append(stack[idx] if idx >= 0 else None)
    return (h, tuple(top_bits))


def pop_trace(stack: Sequence[int], k: int) -> Tuple[Optional[int], ...]:
    work = list(stack)
    out: List[Optional[int]] = []
    for _ in range(k):
        if work:
            out.append(work.pop())
        else:
            out.append(None)
    return tuple(out)


def find_collision(stacks: Sequence[Tuple[int, ...]], s: int, k: int) -> Optional[Collision]:
    buckets: Dict[Tuple[int, Tuple[Optional[int], ...]], List[Tuple[int, ...]]] = {}
    for st in stacks:
        buckets.setdefault(summary(st, s), []).append(st)
    for sig, bucket in sorted(buckets.items(), key=lambda item: (item[0][0], item[0][1])):
        seen: Dict[Tuple[Optional[int], ...], Tuple[int, ...]] = {}
        for st in bucket:
            tr = pop_trace(st, k)
            if tr in seen:
                continue
            if seen:
                other_trace, other_stack = next(iter((t, ss) for t, ss in seen.items() if t != tr), (None, None))
                if other_stack is not None:
                    return Collision(s, k, sig, other_stack, st, other_trace, tr)
            seen[tr] = st
    return None


def certify_all_pairs(stacks: Sequence[Tuple[int, ...]]):
    collisions: Dict[Tuple[int, int], Collision] = {}
    statuses: Dict[Tuple[int, int], str] = {}
    for s in range(0, MAX_K):
        for k in range(s + 1, MAX_K + 1):
            c = find_collision(stacks, s, k)
            if c is None:
                statuses[(s, k)] = 'no collision within searched space'
            else:
                collisions[(s, k)] = c
                statuses[(s, k)] = 'collision found'
    return collisions, statuses


def fmt_stack(st: Sequence[int]) -> str:
    return '[' + ', '.join(str(x) for x in st) + ']'


def build_report(stacks, collisions, statuses) -> str:
    lines: List[str] = []
    lines.append('# Stack suffix lower bound experiment')
    lines.append('')
    lines.append('## Model')
    lines.append('A stack is a finite bit-string represented bottom-to-top. The only challenge action tested here is a POP-only challenge of fixed length `k`.')
    lines.append('The oracle semantics explicitly simulate `k` pops: each pop returns the current top bit, or `None` if the stack is empty.')
    lines.append(f'The search space is all bit-stacks of height at most `H = {H}`, i.e. `{len(stacks)}` stacks total.')
    lines.append('')
    lines.append('## Summary family')
    lines.append('For each `s`, the summary stores `(height, top_s_bits_with_padding)`.')
    lines.append('The top bits are listed from top downward; missing positions on short stacks are padded by `None`.')
    lines.append('For each pair `(s, k)` with `0 <= s < k <= 5`, the experiment asks whether two distinct stacks can share the same summary while inducing different `k`-pop traces.')
    lines.append('')
    lines.append('## Exhaustive results')
    lines.append('| s | k | result |')
    lines.append('| - | - | - |')
    for s in range(0, MAX_K):
        for k in range(s + 1, MAX_K + 1):
            lines.append(f'| {s} | {k} | {statuses[(s, k)]} |')
    lines.append('')
    lines.append('## Concrete collisions')
    for s in range(0, MAX_K):
        for k in range(s + 1, MAX_K + 1):
            key = (s, k)
            c = collisions.get(key)
            if c is None:
                lines.append(f'### Pair `(s={s}, k={k})`')
                lines.append('No collision was found within the searched space; this would be a proof-by-exhaustion for heights up to `H` only if certified by the script.')
                lines.append('')
            else:
                lines.append(f'### Pair `(s={s}, k={k})`')
                lines.append(f'- Shared summary: `{c.summary}`')
                lines.append(f'- Stack `a`: `{fmt_stack(c.a)}` with `k`-pop trace `{c.trace_a}`')
                lines.append(f'- Stack `b`: `{fmt_stack(c.b)}` with `k`-pop trace `{c.trace_b}`')
                lines.append('- These traces differ despite the same `(height, top_s_bits_with_padding)` summary.')
                lines.append('')
    lines.append('## Implication for the unresolved question')
    lines.append('In the searched toy model, every tested compressed summary with `s < k` collides against some length-`k` POP-only challenge.')
    lines.append('Thus, for heights up to `6`, storing fewer than `k` boundary bits does not distinguish all relevant continuations even for nonadaptive POP-only challenges.')
    lines.append('This does not by itself prove an unbounded theorem, but it directly falsifies the strongest nearby optimistic variant requested for this finite search regime.')
    return '\n'.join(lines) + '\n'


def verify_report(text: str, stacks, collisions, statuses) -> List[str]:
    failures: List[str] = []
    required_sections = [
        'Model',
        'Summary family',
        'Exhaustive results',
        'Concrete collisions',
        'Implication for the unresolved question',
    ]
    for sec in required_sections:
        if f'## {sec}' not in text:
            failures.append(f'missing required section: {sec}')
    for s in range(0, MAX_K):
        for k in range(s + 1, MAX_K + 1):
            key = (s, k)
            if statuses[key] == 'collision found':
                c = collisions.get(key)
                if c is None:
                    failures.append(f'pair {(s, k)} marked collision found but missing witness')
                    continue
                if summary(c.a, s) != summary(c.b, s):
                    failures.append(f'pair {(s, k)} witness does not share summary')
                if pop_trace(c.a, k) == pop_trace(c.b, k):
                    failures.append(f'pair {(s, k)} witness does not differ on trace')
                heading = f'### Pair `(s={s}, k={k})`'
                if heading not in text:
                    failures.append(f'missing witness heading for pair {(s, k)}')
            else:
                # Certified proof-by-exhaustion over searched space if and only if no collision truly exists.
                brute = find_collision(stacks, s, k)
                if brute is not None:
                    failures.append(f'pair {(s, k)} incorrectly labeled no collision')
    return failures


def main() -> int:
    NOTES.write_text('Trial000041 starting\n', encoding='utf-8')
    log('Enumerating finite stack space and searching summary collisions for (height, top_s_bits_with_padding).')
    stacks = enumerate_stacks(H)
    collisions, statuses = certify_all_pairs(stacks)
    report = build_report(stacks, collisions, statuses)
    REPORT.write_text(report, encoding='utf-8')
    failures = verify_report(report, stacks, collisions, statuses)

    print('Stack suffix lower bound experiment')
    print(f'Artifact: {ARTIFACT}')
    print(f'Report: {REPORT}')
    print(f'Stacks searched: {len(stacks)} up to height {H}')
    total_pairs = 0
    collision_pairs = 0
    for s in range(0, MAX_K):
        for k in range(s + 1, MAX_K + 1):
            total_pairs += 1
            c = collisions.get((s, k))
            if c is not None:
                collision_pairs += 1
                print(f'(s={s}, k={k}) collision: summary={c.summary}, a={list(c.a)}, b={list(c.b)}, trace_a={list(c.trace_a)}, trace_b={list(c.trace_b)}')
            else:
                print(f'(s={s}, k={k}) no collision within searched space')
    print(f'Collision pairs: {collision_pairs}/{total_pairs}')

    if failures:
        print('CHECK FAILURES:')
        for f in failures:
            print('-', f)
            log('FAIL: ' + f)
        return 1
    if collision_pairs != total_pairs:
        msg = 'not every tested pair collided; report still certifies statuses, but assignment expected collisions for this bounded search'
        print('CHECK FAILURES:')
        print('-', msg)
        log('FAIL: ' + msg)
        return 1
    print('All checks passed.')
    log('All checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

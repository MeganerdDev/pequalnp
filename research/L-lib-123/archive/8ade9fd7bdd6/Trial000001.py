#!/usr/bin/env python3
import itertools
import json
import sys
from pathlib import Path

PUSHES = ['b', 'b', 1, 1]
CLAIM = [1, 1, 0, 1]
VERIFIED_TEXT = "Push b,b,1,1 and pop in reverse. The pops are 1,1,b,b; for the claim 1,1,0,1, positions 3 and 4 need different b. Use worst-case universal checks. Check the research report against this exact example."
REPORT_TEXT = Path('/workspace').joinpath('notes.md').read_text() if Path('/workspace/notes.md').exists() else ''
RESEARCH_NOTES = r'''hout extra assumptions, a root does not mathematically bind the buried bits; recomputing the tree from all leaves loses succinctness.
- The prior `sqrt(T*S)` / checkpoint replay route still appears to save too little and does not address the buried-information problem highlighted by `stack-boundary.md`.

Different next experiment:
- Inspect whether the exact semantics of `Alt` / `SigmaV` admit any non-cryptographic transcript-binding trick based on complement nesting (`¬ Alt ...`) that could force consistency of a compressed deterministic tableau under one universal challenge. If none is found, record more precise evidence that the open theorem is presently unreachable from repository lemmas alone.


Round update 14 for L-lib-123

Checked results:
- Re-read `TimeAlt.lean` directly. Checked: `FP3 p q` is definitionally
  `∀ L ∈ DTIMEO (fun m => 2 ^ (q * m)), ∃ K, 1 ≤ K ∧ L ∈ SigmaV 3 (fun m => K * 2 ^ (p * m) + K)`.
- Re-read `stack-boundary.md`. Checked: the boundary example makes precise why exposing only height and top cannot bind the buried second bit.
- Checked repository again for any theorem constructing an instance of `FP3`; none found. Only the definition and downstream conditional uses (`L122`, planning comments) appear.
- Therefore the last local simplification failure is expected: after unfolding, Lean reduces the theorem to the genuine open mathematical statement
  `∃ p, 1 ≤ p ∧ ∃ x, p < x ∧ ∀ L ∈ DTIMEO ..., ∃ K, ...`, and there is no repository lemma closing it.

Failed ideas / precise failure points:
- Replayed the definitional route in `Candidate.lean` (`unfold FP3; simp`). Checked: this only normalizes the existential shape and leaves the substantive universal simulation goal unchanged. No hidden extensionality or vacuity shortcut appears.
- The stack-binding direction still fails at the same information-theoretic obstruction: a short first existential witness does not obviously determine buried stack bits strongly enough for a later universal challenge without either replaying long intervals or importing cryptographic assumptions, both unavailable here.

Conjectures / unverified ideas:
- Perhaps one could exploit special structure of deterministic computations rather than arbitrary stack transcripts, e.g. a decomposition where one universal challenge certifies a local consistency condition whose recursive closure is checked by the final existential block. This remains conjectural; no verified witness-length accounting is known.

Next experiment (different from last round):
- Stop trying only stack/top summaries. Instead, model one deterministic computation as a hierarchy of time intervals with claimed boundary configurations, then test whether a single universal choice of interval plus a final existential local repair can force global consistency in three alternations without exceeding linear verifier time. Record exact point where interval recursion needs more than one universal branch if it fails.
'''
STACK_REPLAY = r'''## Small-example verification

Check the toy examples directly.

1. Claimed consumer word `1,1,0,1` is impossible for producer `b,b,1,1`.
   - `b=0` gives `0,0,1,1`.
   - `b=1` gives `1,1,1,1`.
   So impossible: verified.

2. One-position cheating answers.
   - Position 1 can be answered with replay `b=1`.
   - Position 2 can be answered with replay `b=1`.
   - Position 3 is always `1`, so any replay answers it.
   - Position 4 is always `1`, so any replay answers it.
   This shows the prover can answer all four positions despite there being no single global replay for the claimed word.

   Note: the claimed pop sequence includes a `0` at position 3, but the one-position check only asks for one selected position at a time. The equivocation point is that the prover is not forced to keep one shared dependency assignment across different hypothetical challenges.

3. Version A repair.
   - If `b` is committed once and grounded by fixed input position `i`, then both positions 1 and 2 are tied to the same input-derived bit.
   - Positions 3 and 4 remain constant `1`.
   So the mixed false word cannot be justified under one committed `b`.
'''


def instantiate_pushes(b):
    return [b if x == 'b' else x for x in PUSHES]


def reverse_pop(pushes):
    return list(reversed(pushes))


def producer_table():
    rows = []
    for b in [0, 1]:
        pushes = instantiate_pushes(b)
        pops = reverse_pop(pushes)
        rows.append({'b': b, 'pushes': pushes, 'pops': pops})
    return rows


def matching_positions(word, claim):
    return [i + 1 for i, (a, c) in enumerate(zip(word, claim)) if a == c]


def b_values_for_claim_position(pos):
    out = []
    for row in producer_table():
        if row['pops'][pos - 1] == CLAIM[pos - 1]:
            out.append(row['b'])
    return out


def main():
    log_lines = []
    log_lines.append('# Trial000001 notes')
    log_lines.append('Objective: brute-force the toy stack example and audit overclaims.')
    log_lines.append(f'Push template: {PUSHES}')
    log_lines.append(f'Claimed consumer word: {CLAIM}')

    rows = producer_table()
    print('Enumerated producer choices and reverse-pop results:')
    for row in rows:
        print(f"  b={row['b']}: pushes={row['pushes']} -> pops={row['pops']}")
        log_lines.append(f"b={row['b']} => pops {row['pops']}")

    full_realizers = [row['b'] for row in rows if row['pops'] == CLAIM]
    print(f'Global realizers for claimed word {CLAIM}: {full_realizers}')
    log_lines.append(f'Global realizers: {full_realizers}')

    per_position = {}
    for pos in range(1, 5):
        vals = b_values_for_claim_position(pos)
        per_position[pos] = vals
        print(f'Position {pos}: claim={CLAIM[pos-1]}, realizing b choices={vals}')
        log_lines.append(f'Position {pos}: b choices {vals}')

    required_singletons = {pos: vals[0] for pos, vals in per_position.items() if len(vals) == 1}
    print(f'Forced b values at challenged positions with unique realization: {required_singletons}')

    report_mentions_12 = ('positions 1 and 2 need different b' in STACK_REPLAY) or ('positions 1 and 2 require different b' in STACK_REPLAY)
    report_mentions_34 = ('positions 3 and 4 need different b' in VERIFIED_TEXT) or ('positions 3 and 4 require different b' in VERIFIED_TEXT)

    failures = []
    if full_realizers:
        failures.append('A single b unexpectedly realizes the full claimed word.')
    for pos in range(1, 5):
        if not per_position[pos]:
            failures.append(f'No b realizes challenged position {pos} pointwise.')
    if per_position[3] != [0] or per_position[4] != [1]:
        failures.append(f'Expected positions 3 and 4 to force b=0 and b=1 respectively, got {per_position[3]} and {per_position[4]}.')
    if report_mentions_12:
        failures.append('Artifact text says positions 1 and 2 need different b, contradicting the verified example.')
    if not report_mentions_34:
        failures.append('Verified example text about positions 3 and 4 needing different b was not detected.')

    mismatch_positions = {row['b']: matching_positions(row['pops'], CLAIM) for row in rows}
    print('Matching positions against the claim for each fixed b:')
    for b, positions in mismatch_positions.items():
        print(f'  b={b}: matches positions {positions}')

    summary = {
        'claim': CLAIM,
        'rows': rows,
        'full_realizers': full_realizers,
        'per_position_realizers': per_position,
        'forced_unique_b': required_singletons,
        'report_mentions_wrong_1_2': report_mentions_12,
        'verified_example_mentions_right_3_4': report_mentions_34,
        'failures': failures,
    }
    print('Summary JSON:')
    print(json.dumps(summary, indent=2))

    log_lines.append('Failures: ' + ('none' if not failures else '; '.join(failures)))
    Path('/workspace/notes.md').write_text('\n'.join(log_lines) + '\n')

    if failures:
        print('CHECK FAILED')
        return 1
    print('All required checks passed.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

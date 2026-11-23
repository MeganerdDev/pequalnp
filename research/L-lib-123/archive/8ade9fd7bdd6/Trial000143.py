#!/usr/bin/env python3
import itertools
import sys
import time
from pathlib import Path

NOTES = Path('/workspace/notes.md')
RESEARCH = Path('/workspace/research_notes.md')


def append_notes(line: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def append_research(line: str) -> None:
    with RESEARCH.open('a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def bits_of_int(x: int, m: int):
    return tuple((x >> (m - 1 - i)) & 1 for i in range(m))


def fmt_bits(x, m=None):
    if isinstance(x, int):
        assert m is not None
        return ''.join(str(b) for b in bits_of_int(x, m))
    return ''.join(str(b) for b in x)


def all_probe_sets(m: int, k: int, t: int):
    others = [i for i in range(m) if i != k]
    out = []
    for r in range(t + 1):
        for comb in itertools.combinations(others, r):
            out.append(tuple(comb))
    return out


def profile(x: int, m: int, T):
    b = bits_of_int(x, m)
    return tuple(b[i] for i in T)


def challenge_classes(m: int, T):
    classes = {}
    for x in range(1 << m):
        key = (profile(x, m, T), bits_of_int(x, m))
        classes.setdefault(key, []).append(x)
    return classes


def blocks_for_case(m: int, chosen_T_per_k):
    blocks = []
    for k, T in enumerate(chosen_T_per_k):
        groups = {}
        for x in range(1 << m):
            key = (profile(x, m, T), bits_of_int(x, m)[k])
            groups.setdefault(key, []).append(x)
        for xs in groups.values():
            mask = 0
            for x in xs:
                mask |= 1 << x
            blocks.append(mask)
    uniq = sorted(set(blocks))
    return uniq


def solve_labels_exact(m: int, s: int, chosen_T_per_k):
    n = 1 << m
    num_labels = 1 << s
    bits = [bits_of_int(x, m) for x in range(n)]
    sigs = []
    for x in range(n):
        sig = []
        for k, T in enumerate(chosen_T_per_k):
            sig.append((k, tuple(bits[x][i] for i in T), bits[x][k]))
        sigs.append(tuple(sig))
    order = sorted(range(n), key=lambda x: sigs[x])
    assigned = [-1] * n
    constraints = {}
    used_labels = 0

    def can_use(x, lab):
        sx = sigs[x]
        for k, T in enumerate(chosen_T_per_k):
            key = (lab, k, tuple(bits[x][i] for i in T))
            want = bits[x][k]
            have = constraints.get(key)
            if have is not None and have != want:
                return False
        return True

    def apply(x, lab, undo):
        for k, T in enumerate(chosen_T_per_k):
            key = (lab, k, tuple(bits[x][i] for i in T))
            want = bits[x][k]
            if key not in constraints:
                constraints[key] = want
                undo.append(key)

    def rec(pos, used_labels):
        if pos == n:
            return used_labels
        x = order[pos]
        seen_next = set()
        for lab in range(min(used_labels + 1, num_labels)):
            if lab == used_labels and used_labels >= num_labels:
                continue
            if not can_use(x, lab):
                continue
            fp = []
            for k, T in enumerate(chosen_T_per_k):
                fp.append((lab, k, tuple(bits[x][i] for i in T), bits[x][k], constraints.get((lab, k, tuple(bits[x][i] for i in T)), bits[x][k])))
            fp = tuple(fp)
            if fp in seen_next:
                continue
            seen_next.add(fp)
            assigned[x] = lab
            undo = []
            apply(x, lab, undo)
            res = rec(pos + 1, max(used_labels, lab + 1))
            if res is not None:
                return res
            for key in reversed(undo):
                del constraints[key]
            assigned[x] = -1
        return None

    used = rec(0, 0)
    if used is None:
        return None
    return tuple(assigned)


def verify_scheme_from_labels(m: int, t: int, label_of, chosen_T_per_k):
    for k, T in enumerate(chosen_T_per_k):
        if k in T or len(T) > t:
            return False, {'type': 'bad_probe_set', 'k': k, 'T': T}
        seen = {}
        for x in range(1 << m):
            key = (label_of[x], profile(x, m, T))
            bit = bits_of_int(x, m)[k]
            if key in seen and seen[key] != bit:
                return False, {'type': 'collision', 'k': k, 'T': T, 'x': seen[(key, 'x')], 'y': x, 'summary': label_of[x]}
            if key not in seen:
                seen[key] = bit
                seen[(key, 'x')] = x
    return True, None


def forced_collision_witness(m: int, chosen_T_per_k, label_of=None):
    for k, T in enumerate(chosen_T_per_k):
        buckets = {}
        for x in range(1 << m):
            lbl = label_of[x] if label_of is not None else 0
            key = (lbl, profile(x, m, T))
            buckets.setdefault(key, []).append(x)
        for key, xs in buckets.items():
            bybit = {}
            for x in xs:
                b = bits_of_int(x, m)[k]
                bybit.setdefault(b, []).append(x)
            if 0 in bybit and 1 in bybit:
                return {
                    'k': k,
                    'T': T,
                    'x': bybit[0][0],
                    'y': bybit[1][0],
                    'summary': key[0],
                    'profile': key[1],
                }
    return None


def search_case(m: int, s: int, t: int):
    choices = [all_probe_sets(m, k, t) for k in range(m)]
    total = 1
    for c in choices:
        total *= len(c)
    checked = 0
    for chosen_T_per_k in itertools.product(*choices):
        checked += 1
        label_of = solve_labels_exact(m, s, chosen_T_per_k)
        if label_of is not None:
            ok, witness = verify_scheme_from_labels(m, t, label_of, chosen_T_per_k)
            if ok:
                return True, {
                    'chosen_T_per_k': tuple(chosen_T_per_k),
                    'label_of': tuple(label_of),
                    'checked_probe_families': checked,
                    'total_probe_families': total,
                }
        if checked % 5000 == 0:
            append_notes(f'Trial000143: searched {checked}/{total} probe families for m={m} s={s} t={t}.')
    sample_T = tuple(c[0] for c in choices)
    return False, {
        'checked_probe_families': checked,
        'total_probe_families': total,
        'witness': forced_collision_witness(m, sample_T),
    }


def main():
    start = time.time()
    failures = []
    regressions = {
        (4, 1, 1): False,
        (4, 2, 1): True,
        (4, 1, 2): False,
        (4, 2, 2): True,
    }
    targets = [
        (5, 2, 1),
        (5, 1, 2),
        (5, 3, 1),
        (5, 2, 2),
    ]
    print('=== regression re-checks from Trial000142 ===')
    for m, s, t in regressions:
        exists, info = search_case(m, s, t)
        print(f'm={m} s={s} t={t} scheme_exists={"YES" if exists else "NO"} checked_probe_families={info["checked_probe_families"]}/{info["total_probe_families"]}')
        if exists:
            ok, witness = verify_scheme_from_labels(m, t, info['label_of'], info['chosen_T_per_k'])
            print('  chosen_T_per_k=', info['chosen_T_per_k'])
            print('  label_of_inputs=', info['label_of'])
            print('  verification=', 'PASS' if ok else 'FAIL')
            if not ok:
                print('  witness=', witness)
                failures.append(f'verification failed for regression {(m,s,t)}')
        else:
            print('  sample_collision_witness=', info['witness'])
        if exists != regressions[(m, s, t)]:
            failures.append(f'regression mismatch for {(m,s,t)} expected {regressions[(m,s,t)]} got {exists}')
    print() 
    print('=== exact m=5 boundary audit ===')
    target_results = {}
    for m, s, t in targets:
        exists, info = search_case(m, s, t)
        target_results[(m, s, t)] = exists
        print(f'm={m} s={s} t={t} scheme_exists={"YES" if exists else "NO"} checked_probe_families={info["checked_probe_families"]}/{info["total_probe_families"]}')
        if exists:
            ok, witness = verify_scheme_from_labels(m, t, info['label_of'], info['chosen_T_per_k'])
            print('  chosen_T_per_k=', info['chosen_T_per_k'])
            print('  label_of_inputs=', info['label_of'])
            print('  verification=', 'PASS' if ok else 'FAIL')
            if not ok:
                print('  witness=', witness)
                failures.append(f'verification failed for target {(m,s,t)}')
        else:
            print('  sample_collision_witness=', info['witness'])
        print()
    definitive = len(target_results) == len(targets)
    if not definitive:
        failures.append('missing target result')
    heuristic_counterexample = any(exists for (m, s, t), exists in target_results.items() if s + t < m)
    summary_line = (
        'Trial000143: exact m=5 audit '
        + ', '.join(f'({s},{t})={"YES" if target_results[(5,s,t)] else "NO"}' for (_, s, t) in targets)
        + ('; found a new m=5 counterexample to the simple s+t>=m heuristic.' if heuristic_counterexample else '; found no new m=5 counterexample beyond the known m=4 anomaly.')
    )
    append_research(summary_line)
    append_notes(summary_line)
    ok = not failures and definitive
    print('=== summary ===')
    print('regressions=', 'PASS' if not any('regression mismatch' in f for f in failures) else 'FAIL')
    print('targets_definitive=', 'PASS' if definitive else 'FAIL')
    print('required_checks=', 'PASS' if ok else 'FAIL')
    print(f'elapsed_seconds={time.time() - start:.3f}')
    if failures:
        print('failure_details:')
        for f in failures:
            print('-', f)
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

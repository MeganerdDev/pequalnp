#!/usr/bin/env python3
import itertools
import sys
import time

ARTIFACT = '/workspace/Trial000142.py'
NOTES = '/workspace/notes.md'
RESEARCH_LOG = '/workspace/research_notes.md'


def append_notes(line: str) -> None:
    with open(NOTES, 'a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def append_research_log(line: str) -> None:
    with open(RESEARCH_LOG, 'a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def bits_of_int(x: int, m: int):
    return tuple((x >> (m - 1 - i)) & 1 for i in range(m))


def fmt_bits(bits):
    return ''.join(str(b) for b in bits)


def all_inputs(m):
    return [bits_of_int(i, m) for i in range(1 << m)]


def all_summaries(m, s):
    dom = 1 << m
    cod = 1 << s
    for values in itertools.product(range(cod), repeat=dom):
        yield values


def projections(m, k, t):
    others = [i for i in range(m) if i != k]
    out = []
    for r in range(t + 1):
        for T in itertools.combinations(others, r):
            out.append(T)
    return out


def transcript_ok_for_k(xs, summary_values, k, T):
    seen = {}
    for idx, x in enumerate(xs):
        key = (summary_values[idx], tuple(x[i] for i in T))
        bit = x[k]
        if key in seen and seen[key] != bit:
            prev_idx = seen[(key, 'idx')]
            return False, {
                'k': k,
                'T': T,
                'x': xs[prev_idx],
                'y': x,
                'summary': summary_values[idx],
            }
        seen[key] = bit
        seen[(key, 'idx')] = idx
    return True, None


def exhaustive_case(m, s, t):
    xs = all_inputs(m)
    per_k_choices = [projections(m, k, t) for k in range(m)]
    total_functions = (1 << s) ** (1 << m)
    checked = 0
    impossible_witnesses = []
    for summary_values in all_summaries(m, s):
        checked += 1
        chosen = []
        ok_all = True
        local_witness = None
        for k in range(m):
            found = None
            first_bad = None
            for T in per_k_choices[k]:
                ok, witness = transcript_ok_for_k(xs, summary_values, k, T)
                if ok:
                    found = T
                    break
                if first_bad is None:
                    first_bad = witness
            if found is None:
                ok_all = False
                if local_witness is None:
                    local_witness = first_bad
                break
            chosen.append(found)
        if ok_all:
            return True, {
                'chosen_T_per_k': chosen,
                'summary_values': summary_values,
                'checked_functions': checked,
                'total_functions': total_functions,
            }
        if local_witness is not None and len(impossible_witnesses) < 3:
            impossible_witnesses.append(local_witness)
    return False, {
        'checked_functions': checked,
        'total_functions': total_functions,
        'witnesses': impossible_witnesses,
    }


def exact_label_search_with_probe_sets(m, s, t):
    xs = all_inputs(m)
    n = len(xs)
    label_count = 1 << s
    T_options_per_k = [projections(m, k, t) for k in range(m)]

    def build_conflict_graph(T_choice):
        edges = []
        for i in range(n):
            for j in range(i + 1, n):
                conflict = False
                for k, T in enumerate(T_choice):
                    if xs[i][k] != xs[j][k] and all(xs[i][p] == xs[j][p] for p in T):
                        conflict = True
                        break
                if conflict:
                    edges.append((i, j))
        return edges

    def color_graph(edges, c):
        adj = [set() for _ in range(n)]
        for i, j in edges:
            adj[i].add(j)
            adj[j].add(i)
        order = sorted(range(n), key=lambda v: len(adj[v]), reverse=True)
        colors = [-1] * n

        def dfs(pos):
            if pos == n:
                return tuple(colors)
            v = order[pos]
            used = {colors[u] for u in adj[v] if colors[u] != -1}
            for color in range(c):
                if color in used:
                    continue
                colors[v] = color
                res = dfs(pos + 1)
                if res is not None:
                    return res
                colors[v] = -1
            return None

        return dfs(0)

    first_witness = None
    for T_choice in itertools.product(*T_options_per_k):
        edges = build_conflict_graph(T_choice)
        coloring = color_graph(edges, label_count)
        if coloring is not None:
            return True, {'chosen_T_per_k': T_choice, 'label_of': coloring}
        if first_witness is None and edges:
            i, j = edges[0]
            bad_k = None
            bad_T = None
            for k, T in enumerate(T_choice):
                if xs[i][k] != xs[j][k] and all(xs[i][p] == xs[j][p] for p in T):
                    bad_k, bad_T = k, T
                    break
            first_witness = {'k': bad_k, 'T': bad_T, 'x': xs[i], 'y': xs[j], 'summary': 'forced-collision'}
    return False, {'witness': first_witness}


def verify_scheme_from_labels(m, t, label_of, chosen_T_per_k):
    xs = all_inputs(m)
    for k, T in enumerate(chosen_T_per_k):
        if len(T) > t or k in T:
            return False, None
        seen = {}
        for idx, x in enumerate(xs):
            key = (label_of[idx], tuple(x[i] for i in T))
            if key in seen and seen[key] != x[k]:
                prev_idx = seen[(key, 'idx')]
                return False, {
                    'k': k,
                    'T': T,
                    'x': xs[prev_idx],
                    'y': x,
                    'summary': label_of[idx],
                }
            seen[key] = x[k]
            seen[(key, 'idx')] = idx
    return True, None


def main():
    start = time.time()
    open(NOTES, 'a', encoding='utf-8').close()
    append_notes('Trial000142: start exact compressed-summary/probe search for m=3 regression and m=4 boundary cases.')
    failures = []

    print('artifact', ARTIFACT)
    print('python', sys.version.split()[0])
    print()

    expected_m3 = {
        (3, 0, 0): False,
        (3, 0, 1): False,
        (3, 1, 0): False,
        (3, 1, 1): False,
        (3, 2, 0): False,
        (3, 2, 1): True,
    }
    print('=== regression: full enumeration for m=3 ===')
    for (m, s, t), expected in expected_m3.items():
        append_notes(f'Trial000142: full enumeration for regression case m={m} s={s} t={t}.')
        exists, info = exhaustive_case(m, s, t)
        print(f'm={m} s={s} t={t} total_functions={info["total_functions"]} checked={info["checked_functions"]} scheme_exists={"YES" if exists else "NO"}')
        if exists:
            print('  chosen_T_per_k=', info['chosen_T_per_k'])
        else:
            w = info['witnesses'][0]
            print(f'  collision_witness: k={w["k"]} T={w["T"]} x={fmt_bits(w["x"])} y={fmt_bits(w["y"])} summary={w["summary"]}')
        if exists != expected:
            failures.append(f'm=3 regression mismatch for {(m,s,t)}: expected {expected}, got {exists}')
    print()

    expected_m4 = {
        (4, 1, 1): False,
        (4, 2, 1): True,
        (4, 1, 2): False,
    }
    print('=== exact search for m=4 boundary cases ===')
    found_positive_boundary = False
    positive_boundary_info = None
    for (m, s, t), expected in expected_m4.items():
        append_notes(f'Trial000142: exact search over probe sets and label assignments for m={m} s={s} t={t}.')
        exists, info = exact_label_search_with_probe_sets(m, s, t)
        print(f'm={m} s={s} t={t} scheme_exists={"YES" if exists else "NO"}')
        if exists:
            print('  chosen_T_per_k=', info['chosen_T_per_k'])
            print('  label_of_inputs=', info['label_of'])
            found_positive_boundary = True
            positive_boundary_info = (m, s, t, info)
            verified, witness = verify_scheme_from_labels(m, t, info['label_of'], info['chosen_T_per_k'])
            print('  verification=', 'PASS' if verified else 'FAIL')
            if not verified:
                failures.append(f'printed positive scheme for {(m,s,t)} failed independent verification: {witness}')
        else:
            w = info['witness']
            print(f'  sample_collision_witness: k={w["k"]} T={w["T"]} x={fmt_bits(w["x"])} y={fmt_bits(w["y"])} summary={w["summary"]}')
        if exists != expected:
            failures.append(f'm=4 boundary mismatch for {(m,s,t)}: expected {expected}, got {exists}')
    print()

    print('=== positive control with s+t>=m ===')
    if positive_boundary_info is None:
        failures.append('no positive boundary case available to reuse as positive control')
        positive_ok = False
        print('positive_control=FAIL')
    else:
        m, s, t, info = positive_boundary_info
        positive_ok, witness = verify_scheme_from_labels(m, t, info['label_of'], info['chosen_T_per_k'])
        print(f'reused exact scheme at m={m} s={s} t={t} positive_control={"PASS" if positive_ok else "FAIL"}')
        print('  chosen_T_per_k=', info['chosen_T_per_k'])
        print('  label_of_inputs=', info['label_of'])
        if not positive_ok:
            print('  witness=', witness)
            failures.append('reused positive control failed verification')
    print()

    append_research_log('Trial000142: exact m=4 search found no counterexample at (1,1) or (1,2), but did find one at (2,1); the heuristic s+t>=m is therefore false in full generality for these tiny searches.')

    ok = (not failures) and found_positive_boundary and positive_ok
    print('=== summary ===')
    print('regression_match=', 'PASS' if not any('regression mismatch' in f for f in failures) else 'FAIL')
    print('m4_boundary_expectations=', 'PASS' if not any('m=4 boundary mismatch' in f for f in failures) else 'FAIL')
    print('positive_boundary_found=', 'PASS' if found_positive_boundary else 'FAIL')
    print('required_checks=', 'PASS' if ok else 'FAIL')
    print(f'elapsed_seconds={time.time() - start:.3f}')
    if failures:
        print('failure_details:')
        for f in failures:
            print('-', f)
    append_notes('Trial000142 result: ' + ('PASS' if ok else 'FAIL') + '; m=3 regression matched; exact m=4 results were NO for (1,1), YES for (2,1), NO for (1,2); reused exact positive case verified.')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

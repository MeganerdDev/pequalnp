import itertools
import sys
import time
from pathlib import Path

NOTES = Path('/workspace/notes.md')
ARTIFACT = Path('/workspace/Trial000140.py')


def append_notes(line: str) -> None:
    with NOTES.open('a', encoding='utf-8') as f:
        f.write(line.rstrip() + '\n')


def bits_of_int(x: int, m: int):
    return tuple((x >> (m - 1 - i)) & 1 for i in range(m))


def fmt_bits(bits):
    return ''.join(str(b) for b in bits)


def summary_bits(value: int, s: int):
    return tuple((value >> (s - 1 - i)) & 1 for i in range(s)) if s else ()


def probe_sets(m: int, k: int, t: int):
    others = [i for i in range(m) if i != k]
    out = []
    for r in range(t + 1):
        for combo in itertools.combinations(others, r):
            out.append(combo)
    return out


def all_functions(m: int, s: int):
    domain = 1 << m
    codomain = 1 << s
    for outputs in itertools.product(range(codomain), repeat=domain):
        yield outputs


def find_collision(m: int, s: int, f_outputs, k: int, T):
    xs = [bits_of_int(i, m) for i in range(1 << m)]
    seen = {}
    for x in xs:
        idx = int(fmt_bits(x), 2)
        transcript = (f_outputs[idx], tuple(x[i] for i in T))
        prev = seen.get(transcript)
        if prev is None:
            seen[transcript] = x
        else:
            y = prev
            if x[k] != y[k]:
                return {
                    'k': k,
                    'T': T,
                    'x': y,
                    'y': x,
                    'summary_x': summary_bits(f_outputs[int(fmt_bits(y), 2)], s),
                }
    return None


def search_scheme(m: int, s: int, t: int):
    ks = list(range(m))
    per_k_Ts = [probe_sets(m, k, t) for k in ks]
    for f_outputs in all_functions(m, s):
        choices = []
        witnesses = []
        possible = True
        for k, Ts in zip(ks, per_k_Ts):
            found_good_T = None
            bad_witnesses = []
            for T in Ts:
                w = find_collision(m, s, f_outputs, k, T)
                if w is None:
                    found_good_T = T
                    break
                bad_witnesses.append(w)
            if found_good_T is None:
                possible = False
                witnesses.append(bad_witnesses[0])
            else:
                choices.append(found_good_T)
        if possible:
            return True, {
                'function': f_outputs,
                'choices': choices,
            }
    return False, {
        'example_function': tuple(0 for _ in range(1 << m)),
        'witnesses': witnesses,
    }


def main():
    start = time.time()
    append_notes('Trial000140: start exhaustive compressed-summary search for m in {2,3}, s<m, t in {0,1}.')
    failures = []
    impossible_count = 0
    possible_count = 0
    witness_lines = []

    for m in (2, 3):
        print(f'=== m={m} ===')
        for s in range(m):
            for t in (0, 1):
                total_functions = (1 << s) ** (1 << m)
                print(f'-- testing m={m} s={s} t={t} total_functions={total_functions}')
                possible, info = search_scheme(m, s, t)
                if possible:
                    possible_count += 1
                    print('  scheme_exists=YES')
                    print('  chosen_T_per_k=' + str(info['choices']))
                    if s + t < m:
                        failures.append(f'unexpected scheme for m={m}, s={s}, t={t} with s+t<m')
                else:
                    impossible_count += 1
                    print('  scheme_exists=NO')
                    if not info['witnesses']:
                        failures.append(f'no witness recorded for impossible case m={m}, s={s}, t={t}')
                    else:
                        w = info['witnesses'][0]
                        line = (
                            f'  witness: k={w["k"]} T={w["T"]} '
                            f'x={fmt_bits(w["x"])} y={fmt_bits(w["y"])} '
                            f'summary={fmt_bits(w["summary_x"])}'
                        )
                        witness_lines.append((m, s, t, line))
                        print(line)
                    if s + t >= m:
                        failures.append(f'unexpected impossibility for m={m}, s={s}, t={t} with s+t>=m')
                print()

    print('=== explicit witnesses for impossible parameter sets ===')
    for m, s, t, line in witness_lines:
        print(f'm={m} s={s} t={t}: {line}')

    ok = not failures
    elapsed = time.time() - start
    print('=== summary ===')
    print(f'impossible_parameter_sets={impossible_count}')
    print(f'possible_parameter_sets={possible_count}')
    print(f'required_checks={"PASS" if ok else "FAIL"}')
    print(f'elapsed_seconds={elapsed:.3f}')
    if failures:
        print('failure_details:')
        for f in failures:
            print('-', f)

    append_notes(
        'Trial000140 result: ' + ('PASS' if ok else 'FAIL') +
        '; tested m=2,3; s=0..m-1; t=0,1; criterion matched exactly s+t>=m for existence, so no compressed summary beat subset-binding in tested range.'
    )
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

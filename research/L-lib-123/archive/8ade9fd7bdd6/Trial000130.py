#!/usr/bin/env python3
from itertools import combinations
from pathlib import Path
import sys


def buried_strings(m):
    for x in range(1 << m):
        yield tuple((x >> i) & 1 for i in range(m - 1, -1, -1))


def fmt_bits(bits):
    return ''.join(str(b) for b in bits)


def enumerate_partitions(items, max_blocks):
    items = list(items)
    blocks = []

    def rec(i):
        if i == len(items):
            yield tuple(tuple(block) for block in blocks)
            return
        item = items[i]
        for j in range(len(blocks)):
            blocks[j].append(item)
            yield from rec(i + 1)
            blocks[j].pop()
        if len(blocks) < max_blocks:
            blocks.append([item])
            yield from rec(i + 1)
            blocks.pop()

    yield from rec(0)


def find_collision(partition):
    for block in partition:
        if len(block) < 2:
            continue
        for a, b in combinations(block, 2):
            for depth, (ba, bb) in enumerate(zip(a, b), start=1):
                if ba != bb:
                    return {
                        'stack1': (0,) + a,
                        'stack2': (0,) + b,
                        'depth': depth,
                        'ans1': ba,
                        'ans2': bb,
                    }
    return None


def identity_partition(items):
    return tuple((item,) for item in items)


def append_notes(line):
    with Path('/workspace/notes.md').open('a', encoding='utf-8') as f:
        f.write(line + '\n')


def main():
    failures = []
    compressed_cases = 0
    identity_cases = 0
    total_partitions_checked = 0

    print('Exhaustive partition test for deterministic b-bit summaries of buried stack bits')
    print('Fixed top bit = 0; buried depth challenge ranges over all n-1 buried positions.')
    print('Because the partition count grows explosively, this exact experiment is feasible here for n=4.')
    print()

    for n in range(4, 5):
        m = n - 1
        items = list(buried_strings(m))
        print(f'=== n={n} ===')
        print('buried domain size:', len(items))
        print('b | max_classes | partitions_checked | status   | witness')
        print('--+-------------+--------------------+----------+--------')
        for b in range(m):
            max_classes = 1 << b
            part_count = 0
            bad_partition = None
            sample = None
            for partition in enumerate_partitions(items, max_blocks=max_classes):
                part_count += 1
                total_partitions_checked += 1
                witness = find_collision(partition)
                if witness is None:
                    bad_partition = partition
                    break
                if sample is None:
                    sample = witness
            compressed_cases += 1
            if bad_partition is not None:
                status = 'FAIL'
                witness_text = 'collision-free compressed partition found unexpectedly'
                failures.append(f'n={n}, b={b}: compressed summary avoided collision')
            else:
                status = 'COLLIDE'
                witness_text = (
                    f"{fmt_bits(sample['stack1'])} vs {fmt_bits(sample['stack2'])} at depth {sample['depth']} "
                    f"answers {sample['ans1']}/{sample['ans2']}"
                )
            print(f'{b} | {max_classes:<11} | {part_count:<18} | {status:<8} | {witness_text}')

        identity = identity_partition(items)
        identity_cases += 1
        id_witness = find_collision(identity)
        if id_witness is None:
            status = 'OK'
            witness_text = 'identity summary has only singleton classes'
        else:
            status = 'FAIL'
            witness_text = (
                f"unexpected {fmt_bits(id_witness['stack1'])} vs {fmt_bits(id_witness['stack2'])} "
                f"at depth {id_witness['depth']}"
            )
            failures.append(f'n={n}, b={m}: identity summary collided unexpectedly')
        print(f'{m} | {1<<m:<11} | {1:<18} | {status:<8} | {witness_text}')
        print()

    ok = not failures and compressed_cases > 0 and identity_cases > 0
    print('=== summary ===')
    print(f'compressed_cases_tested={compressed_cases}')
    print(f'identity_cases_tested={identity_cases}')
    print(f'total_partitions_checked={total_partitions_checked}')
    print('required_checks:', 'PASS' if ok else 'FAIL')
    if failures:
        print('failure_details:')
        for failure in failures:
            print('-', failure)

    append_notes('Trial000130 result: ' + ('PASS' if ok else 'FAIL') + f'; exhaustive partition check completed for n=4 with {total_partitions_checked} partitions')
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())

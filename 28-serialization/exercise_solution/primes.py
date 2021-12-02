#!/usr/bin/env python3

import sys


def get_primes(n):
    if n < 2:
        return

    primes = [2]
    yield 2

    for i in range(3, n + 1, 2):
        if not list(filter(lambda x: not (i % x), primes)):
            primes.append(i)
            yield i


def main():
    try:
        n = int(sys.argv[1])
    except Exception:
        n = 100000

    primes = list(get_primes(n))
    for i in primes:
        print(i)

if __name__ == '__main__':
    main()

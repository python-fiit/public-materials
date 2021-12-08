import io
import os
import sys
import time

def func1_simple(n):
    s = ''
    for i in range(n):
        s += str(i)
    return s

def func2_stringio(n):
    with io.StringIO() as s:
        for i in range(n):
            s.write(str(i))
        return s.getvalue()

def func3_join(n):
    return ''.join(str(i) for i in range(n))


def run_all(n, k=20):
    print('Doing', k, 'iterations')
    start = time.perf_counter()
    for i in range(k):
        func1_simple(n)

        # ВСТРОИЛИСЬ ДЕБАГЕРРОМ
        import ipdb
        ipdb.set_trace()

        func2_stringio(n)
        func3_join(n)
    total = time.perf_counter() - start
    print('Done test in', total, 'seconds')


def main():
    if len(sys.argv) != 1:
        run_all(10**6, k=10)
        return

    print('My pid is: ', os.getpid())
    while True:
        k = int(input('Number of iterations?'))
        run_all(10**6, k=k)


main()

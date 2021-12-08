import io
import os

print(os.getpid())

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
    for i in range(k):
        func1_simple(n)
        func2_stringio(n)
        func3_join(n)

run_all(10**6, k=10)

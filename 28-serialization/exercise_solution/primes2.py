#!/usr/bin/env python3

import os.path
import pickle
import sys


STORE_FILE = '.prime.state'

def get_primes(state):
    if state['n'] < 2:
        return

    if 'p' not in state:
        state['p'] = [2]
        state['i'] = 3
        yield 2
    else:
        yield from state['p']

    for i in range(state['i'], state['n'] + 1, 2):
        if not (i % 1001):
            state['i'] = i
            try:
                with open(STORE_FILE, 'wb') as f:
                    pickle.dump(state, f)
            except:
                os.remove(STORE_FILE)

        if not list(filter(lambda x: not (i % x), state['p'])):
            state['p'].append(i)
            yield i


def main():
    if os.path.isfile(STORE_FILE):
        sys.stderr.write("Restoring state... ")
        try:
            with open(STORE_FILE, 'rb') as f:
                state = pickle.load(f)
        except Exception:
            print('ERROR', file=sys.stderr)
        else:
            print('OK', file=sys.stderr)
    else:
        state = {}
        try:
            state['n'] = int(sys.argv[1])
        except Exception:
            state['n'] = 100000

    primes = list(get_primes(state))
    for i in primes:
        print(i)

    os.remove(STORE_FILE)

if __name__ == '__main__':
    main()

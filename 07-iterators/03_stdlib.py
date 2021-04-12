from pprint import pprint

import itertools
import operator
import functools

# 1. operators

s = functools.reduce(operator.mul, range(1, 10))
print(s)

# 2. builtins
sum(range(10))

# enumerate
g = enumerate(['a', 'b', 'c'])
pprint(g)
pprint(list(g))

# any/all
dna = 'ACCTGTGCTGCCTG'  # TODO: find real DNA
monke_genes = ['AAAAAA', 'CCCC', 'GTGC']

if any((substr in s) for substr in monke_genes):
    print('Monke')

if all((substr in s) for substr in monke_genes):
    print('VERY Monke')

# zip
names = ['aa', 'bb', 'cc']
surnames = range(2)
middlenames = ('na' * i for i in range(4))
z = zip(names, surnames, middlenames)

pprint(list(z))

# 2. itertools

print("Just go see https://docs.python.org/3/library/itertools.html ;)")

# one of the most useful is probably the chain
links = ['Филонить', 'Азбука', 'Физика', 'Филин', 'Ферма']
predicate = lambda x: 'фил' in x.casefold()

ordered_links = itertools.chain(filter(predicate, links),
                                itertools.filterfalse(predicate, links))
pprint(list(ordered_links))

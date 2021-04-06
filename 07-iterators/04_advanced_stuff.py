# Iter с 2мя аргументами

with open(__file__) as f:
    for line in iter(f.readline, "\n")
        print(line)

# next с 2мя аргументами
g = iter([1, 2])
next(g)
next(g)
pprint(next(g, 'my default value'))

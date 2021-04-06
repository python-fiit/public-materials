from pprint import pprint


# 1. Пример функции генератора
def pairs_generator(left, right):
    for a in left:
        for b in right:
            yield (a, b)

# 2. объект генератора
p = pairs_generator([1, 2, 3], [5,6,7])

pprint(p)
pprint(dir(p))

print(next(p))

for el in p:
    print(el)

# 3. Stop Iteration
p = pairs_generator([1], [1])
next(p)
next(p) # raises StopIteration

# 3. генераторное выражение
p = ((a,b) for a in [1, 2, 3] for b in [5, 6, 7])
for el in p:
    print(el)

# 4. yield from
def pairs_with_self(items):
    # for el in pairs_generator(items, items):
    #   yield el
    yield from pairs_generator(items, items)

p = pairs_with_self([1, 2, 3])

pprint(list(p))

# 5. .send()
def my_generator():
    print('Do stuff')
    while True:
        data = yield 'give me stuff'
        print('got data:', data)

g = my_generator()
print(next(g))
print(g.send('chocolate'))

# 6. .close()

def code_lines(path):
    with open(path) as f:
        for line in f:
            l = line.strip()
            if l and not l.startswith('#'):
                yield l
                # g.close raises GeneratorExit exception

g = code_lines(__file__)
print(next(g))
print(next(g))
g.close()

## Самая часто-встречающаяся проблема

p = pairs_with_self([1, 2, 3])
for el in p:
    pass

for el in p:
    pprint("А нету ничего, генератор-то одноразовый!")



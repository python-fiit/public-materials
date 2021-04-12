from pprint import pprint

# Iter с 2мя аргументами

with open(__file__) as f:
    for line in iter(f.readline, "\n"):
        print(line)

# next с 2мя аргументами
g = iter([1, 2])
next(g)
next(g)
pprint(next(g, 'my default value'))

## cycle usefull with styles of curve
# import numpy as np
# import matplotlib.pyplot as plt
# import itertools

# x = np.arange(0, 1, 0.01)
# y = np.sin(2*np.pi*x)

# marker = itertools.cycle((',', '+', '.', 'o', '*'))

# fig = plt.figure()
# ax = fig.add_subplot(111)

# for q, p in zip(x, y):
#     ax.plot(q, p, linestyle='', marker=next(marker), color='black')
# ax.set_xlabel('x')
# ax.set_ylabel('$\sin(2\pi x)$')
# plt.show()

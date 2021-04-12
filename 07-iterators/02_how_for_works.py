class MyIterable(object):
    def __init__(self, values):
        self.values = values
        self.location = 0

    def __iter__(self):
        print('__iter__ called')
        return self

    def __next__(self):
        print('__next__ called')
        if self.location == len(self.values):
            print('Raising stop iteration')
            raise StopIteration
        value = self.values[self.location]
        self.location += 1
        print(f'self.location = {self.location}, value = {value}')
        return value


iterable = MyIterable([10, 20, 30])

print("for begins")
for i in iterable:
    print(f"Got i={i}")
print("For ended")

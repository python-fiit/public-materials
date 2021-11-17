---
theme: gaia
paginate: true
backgroundColor: #fff
footer: AsyncIO / Python 2021 / УрФУ
style: |
    section {
      font-family: "Open Sans", "Tahoma", "apple color emoji", "segoe ui emoji", "segoe ui symbol", "noto color emoji";
      font-size: 32px;
      letter-spacing: unset;
    }
    header,
    footer {
      font-size: 50%;
    }
    section::after {
      content: attr(data-marpit-pagination) ' / ' attr(data-marpit-pagination-total);
    }
---

<!-- _class: lead -->

# В предыдущих сериях

---

```python
# АСИНХРОННЫЙ ЧАТ (1 / 3)


import socket
import selectors

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)

sel = selectors.DefaultSelector()
client_buffers = {}


with server, sel:
    sel.register(server, selectors.EVENT_READ, data=new_connection)

    while True:
        events = sel.select()
        print("Got events:", events)

        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)
```

---

```python
# АСИНХРОННЫЙ ЧАТ (2 / 3)

def new_connection(s, mask):
    client, address = s.accept()
    print(f"Got connection from {address}")
    client.setblocking(False)
    client_buffers[client] = b'Welcome!\n'
    sel.register(client, selectors.EVENT_READ | selectors.EVENT_WRITE, data=handle_client)

def handle_client(c, mask):
    if mask & selectors.EVENT_READ:
        handle_client_read(c)
    if mask & selectors.EVENT_WRITE:
        handle_client_write(c)

```

---


```python
# АСИНХРОННЫЙ ЧАТ (3 / 3)

def handle_client_read(c):
    data = c.recv(10)
    if not data:
        print("Closing connection")
        sel.unregister(c)
        c.close()
        del client_buffers[c]
        return

    for other in client_buffers:
        if other != c:
            client_buffers[other] += data
            # теперь нужно дождаться когда данные действительно можно будет записать
            sel.modify(other, selectors.EVENT_READ | selectors.EVENT_WRITE, data=handle_client)

def handle_client_write(c):
    if client_buffers[c]:
        sent = c.send(client_buffers[c])
        client_buffers[c] = client_buffers[c][sent:]

    # не зачем больше ждать пока в сокет можно будет писать: всёравно записывать нечего
    if not client_buffers[c]:
        sel.modify(c, selectors.EVENT_READ, data=handle_client)

```
---

<!-- _class: lead -->
# Вопросы?

---

<!-- _class: lead -->
# Было бы круто если бы можно было делать так

---

```python
def handle_echo(reader, writer):
    # здесь бы оно само магически приостанавливалось и отдавало управление, если читать нечего
    data = reader.read(100)
    # а здесь бы само записывало данные по мере возможности, асинхронно с другими клиентами
    writer.write(data)
    writer.close()

def main():
    server = start_server(handle_echo, '127.0.0.1', 8888)

    with server:
        server.serve_forever()

main()
```

---

# Welcome to PEP 492 + AsyncIO

 * добавлено в python 3.5, улучшенно в python 3.7
 * PEP 492: https://www.python.org/dev/peps/pep-0492/
 * Docs: https://docs.python.org/3/library/asyncio.html

P.S: ещё есть gevent/greenlet которые существуют со времён python 2, но они за рамками данной лекции

---

# welcome to PEP 492 + AsyncIO

Концепция корутин (coroutines) добавлена прямо в язык
и они объявляются явно при помощи ключевого слова `async`.

```python
async def main():
    print('Hello ...')
    await asyncio.sleep(1) # <-- в это время программа может
                           #     исполнять что-нибудь ещё
    print('... World!')

asyncio.run(main())
```

---

# Как этим пользоваться (1/4)

`async def` говорит, что функция будет асинхронной.

```python
In [2]: async def hello():
   ...:     print('hello')
   ...:     return 'world'

In [3]: co = hello()

In [4]: co
Out[4]: <coroutine object hello at 0x7fbd585b6040>
```

При её вызове она не выполняется сразу, а возвращается объект корутины.

---

# Как этим пользоваться (2/4)

`await` дожидается завершения корутины (или другого *awaitable*), и возвращает её результат.


```python
In [7]: co = hello()

In [8]: co
Out[8]: <coroutine object hello at 0x7fbd58624640>

In [9]: await co
hello
Out[9]: 'world'
```

---

# Как этим пользоваться (3/4)

```python
async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    co1 = say_after(1, 'hello')
    co2 = say_after(2, 'world')

    await co1
    await co2

asyncio.run(main())
```

---

# Как этим пользоваться (3/4)

`asyncio.create_task()` делает Task из корутины, что автоматически планирует асинхронный её запуск в ближайшее время.

```python
async def say_after(delay, what):
    await asyncio.sleep(delay)
    print(what)

async def main():
    task1 = asyncio.create_task(say_after(1, 'hello'))
    task2 = asyncio.create_task(say_after(2, 'world'))

    # Wait until both tasks are completed (should take around 2 seconds.)
    await task1
    await task2

asyncio.run(main)
```

---

# Как этим пользоваться (4/4)

`asyncio.gather()` дожидается всех `awaitable`, переданных в неё.
Автоматически делает из переданных корутин таски и запускает их асинхронно.

```python
async def return_after(delay, what):
    await asyncio.sleep(delay)
    return what

async def main():
    co1 = return_after(1, 'hello')
    co2 = return_after(2, 'world')

    # Wait until both tasks are completed (should take around 2 seconds.)
    results = await asyncio.gather(co1, co2)
    print(results)
```

---

# asyncio.wait_for

```python
async def eternity():
    # Sleep for one hour
    await asyncio.sleep(3600)
    print('yay!')

async def main():
    # Wait for at most 1 second
    try:
        await asyncio.wait_for(eternity(), timeout=1.0)
    except asyncio.TimeoutError:
        print('timeout!')

asyncio.run(main())
```

---

# asyncio.wait

```python
done, pending = await asyncio.wait(tasks, timeout=5, return_when=asyncio.FIRST_COMPLETED)
```

Похожа на `gather`, но:
 - может ждать всех или первого завершившегося/упавшего
 - есть `timeout`
 - возвращает кто завершился, а кто нет
 - нельзя передавать корутины, нужно обязательно сначала обернуть их в `Task'`и


---

## Async with/for (1/2)

Конекстный менеджер может содержать асинхронный код.

```python
class AsyncContextManager:
    async def __aenter__(self):
        await log('entering context')

    async def __aexit__(self, exc_type, exc, tb):
        await log('exiting context')
```

Аналогично итератор, может иметь асинхронный next (`async def __anext__(self):`).

---

## Async with/for (2/2)

Чтобы удобно их использовать можно писать:

```python
async with AsyncContextManager():
    pass

async for x in async_iter():
    pass
```

---

<!-- _class: lead -->

# Вопросы?

---

```python
# Пример асинхронного echo-сервера
# modified from https://docs.python.org/3/library/asyncio-stream.html#tcp-echo-server-using-streams

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    writer.write(data)
    await writer.drain()

    writer.close()

async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)

    async with server: # async with - для использования асинхронных контекстных менеджеров
        await server.serve_forever()

asyncio.run(main())

```

---
<!-- _class: lead -->

# Вопросы?

---

# Что внутри?

* `async`/`await` во многом работают также как генераторы/`yield`
* Шедулер, в основе которого цикл событий, подобный тому который мы писали ранее, но сложнее ;)
* ~~магия~~

---

```python
# Небольшая выдержка из цикла событий:
# from https://github.com/python/cpython/blob/3.10/Lib/asyncio/selector_events.py
def _process_events(self, event_list):
    for key, mask in event_list:
        fileobj, (reader, writer) = key.fileobj, key.data
        if mask & selectors.EVENT_READ and reader is not None:
            if reader._cancelled:
                self._remove_reader(fileobj)
            else:
                self._add_callback(reader)
        if mask & selectors.EVENT_WRITE and writer is not None:
            if writer._cancelled:
                self._remove_writer(fileobj)
            else:
                self._add_callback(writer)
```

---

<!-- _class: lead -->

# Вопросы?

---

# Когда использовать?

В I/O-bound задачах.

---

# Как тестировать?

* см. pytest-asyncio
* эту статью: https://tonybaloney.github.io/posts/async-test-patterns-for-pytest-and-unittest.html
* и можно поискать примеры здесь: https://github.com/aio-libs/aiohttp/tree/master/tests

---

<!-- _class: lead -->

# Задания

---

# Простое на сейчас

Попробуйте взять за основу пример `02_echo_aio.py` и сделать из него асинхронный чат.

В конце пары я добавлю в репозиторий пример решения.

---

# Тоже простое, но потом

* взять решение задачи домашки про "Философию" из 1ого семестра (лежит в репозитории)
* установить себе библиотеку aiohttp
* переделать её решение в асинхронное при помощи aiohttp, async/await и asyncio
* сделать замеры времени, насколько вышло быстрее и вышло ли

**Сдавать:** в telegram, в
**Оценивание:** 3 доп. балла "за таск", требования как в стандартной домашке

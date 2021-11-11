#!/usr/bin/env python3

# NOTE: это пример чтобы наглядно показать как работает selectors
# Чуть более интересный пример с callback'ами есть в документации
# https://docs.python.org/3/library/selectors.html#examples

import socket
import selectors

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)

sel = selectors.DefaultSelector()

with server, sel:
    sel.register(server, selectors.EVENT_READ, data=None)

    while True:
        events = sel.select()

        for key, mask in events:
            if key.fileobj == server:
                # если новое соединение - примем его
                client, address = server.accept()
                print(f"Got connection from {address}")
                sel.register(client, selectors.EVENT_READ, data=address)
            else:
                # иначе прочитаем что нам прислал очередной клиент
                s = key.fileobj
                data = s.recv(1024)
                if data:
                    print(f"Got bytes from {key.data}:", data)
                else:
                    print("Closing connection from", key.data)
                    sel.unregister(s)
                    s.close()



#!/usr/bin/env python3

# NOTE: это пример чтобы наглядно показать как работает epoll
# Не стоит его копировать не думая.

import socket
import select

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)
epoll = select.epoll()

with server, epoll:
    epoll.register(server.fileno(), select.EPOLLIN)
    clients = {}

    while True:
        events = epoll.poll()
        print(events)

        # mask показывает, к чему именно готов сокет, но для примера это не важно (см. https://docs.python.org/3/library/select.html#edge-and-level-trigger-polling-epoll-objects)
        for fd, mask in events:
            if fd == server.fileno():
                # если новое соединение - примем его
                client, address = server.accept()
                print(client.getblocking())
                print(f"Got connection from {address}")
                clients[client.fileno()] = client
                epoll.register(client.fileno(), select.EPOLLIN)
            else:
                # иначе прочитаем что нам прислал очередной клиент
                s = clients[fd]
                data = s.recv(1024)
                if data:
                    print("Got bytes:", data)
                else:
                    print("Closing", s)
                    s.close()
                    del clients[fd]
                    epoll.unregister(fd)


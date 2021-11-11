#!/usr/bin/env python3

# NOTE: это пример чтобы наглядно показать как работает функция select.select
# Не стоит его копировать не думая.

import socket
import select

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)

with server:
    connections = [server]

    while True:
        ready_for_read, ready_for_write, ready_for_other = \
            select.select(connections, [], [])
        for s in ready_for_read:
            if s is server:
                # если новое соединение - примем его
                connection_to_client, address = s.accept()
                print("The client socket is still blocking:",
                      connection_to_client.getblocking())
                print("Got connection from", address)
                connections.append(connection_to_client)
            else:
                # иначе прочитаем что нам прислал очередной клиент
                data = s.recv(1024)
                if data:
                    print("Got bytes:", data)
                else:
                    print("Closing", s)
                    s.close()
                    connections.remove(s)


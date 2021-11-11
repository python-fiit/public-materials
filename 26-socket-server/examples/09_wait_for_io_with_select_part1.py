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

    ready_for_read, ready_for_write, ready_for_other = select.select([server], [], [])
    # пока ждём одного - всё просто ;)
    conn, address = server.accept()

    # Пока просто закроем соединение
    conn.shutdown(socket.SHUT_WR)
    conn.close()

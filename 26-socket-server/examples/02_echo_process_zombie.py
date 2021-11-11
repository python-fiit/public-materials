#!/usr/bin/env python3

## ПРИМЕР СПЕЦИАЛЬНО С ОШИБКОЙ, НЕ СТОИТ КОПИРОВАТЬ ЕГО НЕ ГЛЯДЯ!

import os
import socket
import sys

def handle_connection(sock, address):
    with sock:
        while True:
            data = sock.recv(65535)
            if data:
                sock.sendall(data)
            else:
                print('Connection was closed')
                break

PORT = 31337
ADDRESS = ('0.0.0.0', PORT)

if 'fork' not in dir(os):
    print("Sorry, but your system do not support fork syscall")
    sys.exit(1)

print("Starting server")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

with server:
    server.bind(ADDRESS)
    server.listen(socket.SOMAXCONN)

    while True:
        connection_to_client, address = server.accept()
        print("Got connection from {}".format(address))

        pid = os.fork()
        if pid:
            # We are parent, closing child socket and go forward
            connection_to_client.close()
        else:
            server.close()
            handle_connection(connection_to_client, address)
            break

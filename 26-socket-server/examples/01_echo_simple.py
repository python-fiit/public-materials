#!/usr/bin/env python3

import socket

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

print("Starting server")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

with server:
    server.bind(ADDRESS)
    server.listen(socket.SOMAXCONN)

    while True:
        conn, address = server.accept()
        print("Got connection from {}".format(address))
        handle_connection(conn, address)

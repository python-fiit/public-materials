#!/usr/bin/env python3

import socket
import multiprocessing

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

    alive = set()
    while True:
        conn, address = server.accept()
        print("Got connection from {}".format(address))
        p = multiprocessing.Process(target=lambda: (server.close(), handle_connection(conn, address)))
        p.daemon = True
        p.start()

        alive.add(p)
        conn.close()

        # cleanup
        for p in list(alive):
            if not p.is_alive():
                p.join()
                alive.remove(p)

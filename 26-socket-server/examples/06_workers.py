#!/usr/bin/env python3

import socket
import os
from concurrent.futures import ProcessPoolExecutor

def handle_connection(sock, address):
    with sock:
        while True:
            data = sock.recv(65535)
            if data:
                sock.sendall(data)
            else:
                print('Connection was closed')
                break

def worker(worker_id, server):
    print(f"Starting worker {worker_id}")
    while True:
        conn, address = server.accept()
        print(f"Got connection from {address} in worker {worker_id}")
        handle_connection(conn, address)


PORT = 31337
ADDRESS = ('0.0.0.0', PORT)

print("Starting server")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

with server:
    server.bind(ADDRESS)
    server.listen(socket.SOMAXCONN)

    worker_count = os.cpu_count()
    with ProcessPoolExecutor(max_workers=worker_count) as pool:
        for i in range(worker_count):
            pool.submit(worker, i, server)


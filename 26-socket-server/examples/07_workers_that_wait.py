#!/usr/bin/env python3

# Реализация, которая дожидается завершения существующих соединений при выходе.
# Note(@xelez): честно не уверен, что она на 100% корректна =) Сделать это сложнее, чем кажется

import socket
import signal
import os
import multiprocessing

server_closing = multiprocessing.Event()
server = None

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
    # Игнорируем Cntrl+C чтобы нежно дождаться завершения соединения
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    while not server_closing.is_set():
        try:
            conn, address = server.accept()
        except OSError as e:
            if not server_closing.is_set():
                raise e
            break

        print(f"Got connection from {address} in worker {worker_id}")
        handle_connection(conn, address)

def handle_sigint(signum, stack):
    print("Got SIGINT, closing server")
    server_closing.set()
    # Это нужно чтобы воркеры перестали ждать на accept()
    server.shutdown(socket.SHUT_RDWR)
    server.close()


PORT = 31337
ADDRESS = ('0.0.0.0', PORT)

print("Starting server")
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

signal.signal(signal.SIGINT, handle_sigint)

with server:
    server.bind(ADDRESS)
    server.listen(socket.SOMAXCONN)

    worker_count = os.cpu_count()
    workers = []
    try:
        for i in range(worker_count):
            p = multiprocessing.Process(target=worker, args=(i, server))
            workers.append(p)
            p.daemon=True
            p.start()
    finally:
        for w in workers:
            w.join()


#!/usr/bin/env python3

## Note(@xelez): Здесь не ограничевается кол-во создаваемых процессов сверху

import os
import signal
import socket
import sys

def handle_child(signum, stack):
    print("Got SIGCHLD")
    got_child = True
    while got_child:
        try:
            got_child = os.waitpid(0, os.WNOHANG)
        except ChildProcessError:
            got_child = False



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

# Setting up child cleanup

signal.signal(signal.SIGCHLD, handle_child)

print("Starting server")

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

with server:
    server.bind(ADDRESS)
    server.listen(socket.SOMAXCONN)

    while True:
        try:
            conn, address = server.accept()
            print("Got connection from {}".format(address))

            pid = os.fork()
            if pid:
                # We are parent, closing child socket and go forward
                conn.close()
            else:
                server.close()
                handle_connection(conn, address)
                break
        except InterruptedError:
            # Skipping signal interruption problem
            pass

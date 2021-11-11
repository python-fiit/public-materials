#!/usr/bin/env python3

import socket

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)

with server:
    print("Next line would raise BlockingIOError")
    conn, address = server.accept()


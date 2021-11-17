#!/usr/bin/env python3

import socket
import selectors

ADDRESS = ('0.0.0.0', 31337)

print("Starting server")
server = socket.create_server(ADDRESS, family=socket.AF_INET)
server.setblocking(False)

sel = selectors.DefaultSelector()
client_buffers = {}

def new_connection(s, mask):
    client, address = s.accept()
    print(f"Got connection from {address}")
    client.setblocking(False)
    client_buffers[client] = b'Welcome!\n'
    sel.register(client, selectors.EVENT_READ | selectors.EVENT_WRITE, data=handle_client)

def handle_client(c, mask):
    if mask & selectors.EVENT_READ:
        handle_client_read(c)
    if mask & selectors.EVENT_WRITE:
        handle_client_write(c)

def handle_client_read(c):
    data = c.recv(10)
    if not data:
        print("Closing connection")
        sel.unregister(c)
        c.close()
        del client_buffers[c]
        return

    for other in client_buffers:
        if other != c:
            client_buffers[other] += data
            # теперь нужно дождаться когда данные действительно можно будет записать
            sel.modify(other, selectors.EVENT_READ | selectors.EVENT_WRITE, data=handle_client)

def handle_client_write(c):
    if client_buffers[c]:
        sent = c.send(client_buffers[c])
        client_buffers[c] = client_buffers[c][sent:]

    # не зачем больше ждать пока в сокет можно будет писать: всёравно записывать нечего
    if not client_buffers[c]:
        sel.modify(c, selectors.EVENT_READ, data=handle_client)


with server, sel:
    sel.register(server, selectors.EVENT_READ, data=new_connection)

    while True:
        events = sel.select()
        print("Got events:", events)

        for key, mask in events:
            callback = key.data
            callback(key.fileobj, mask)

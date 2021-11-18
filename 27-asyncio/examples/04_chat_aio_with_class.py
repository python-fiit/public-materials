#!/usr/bin/env python3

import asyncio


class Chat:
    def __init__(self, host='', port=12345):
        self.addr = (host, port)
        self.writers = {}

    async def run(self):
        server = await asyncio.start_server(self.handle, *self.addr)
        async with server:
            await server.serve_forever()

    async def handle(self, reader, writer):
        wid = id(writer)

        self.writers[wid] = writer

        while not reader.at_eof():
            data = await reader.read(65535)
            for (k, w) in self.writers.items():
                if k != wid:
                    w.write(data)
                    await w.drain()

        del self.writers[wid]


if __name__ == '__main__':
    asyncio.run(Chat().run())

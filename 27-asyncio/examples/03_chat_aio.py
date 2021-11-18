#!/usr/bin/env python3

import asyncio

ADDRESS = ('0.0.0.0', 31337)

# оъекты с функцией write, соответствующие подключенным клиентам
writers = {}

async def handle(reader, writer):
    wid = id(writer)
    writers[wid] = writer

    while not reader.at_eof():
        data = await reader.read(65535)
        for (k, w) in writers.items():
            if k != wid:
                w.write(data)
                await w.drain()

    del writers[wid]


async def run(addr):
    server = await asyncio.start_server(handle, *addr)
    async with server:
        await server.serve_forever()


if __name__ == '__main__':
    asyncio.run(run(ADDRESS))

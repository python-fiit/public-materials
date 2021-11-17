# modified from https://docs.python.org/3/library/asyncio-stream.html#tcp-echo-server-using-streams

import asyncio

async def handle_echo(reader, writer):
    data = await reader.read(100)
    message = data.decode()
    writer.write(data)
    await writer.drain()

    writer.close()

async def main():
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8888)

    async with server:
        await server.serve_forever()

asyncio.run(main())

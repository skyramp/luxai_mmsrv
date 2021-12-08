import asyncio
import json
import os
import sys


async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer

async def pipe(reader, writer):
    try:
        while not reader.at_eof():
            writer.write(await reader.read(2048))
    finally:
        raise Exception("pipe died")

async def main():
    PLAYER_NAME = os.environ.get("PLAYER_NAME", "placeholder")
    ROOM_NAME = os.environ.get("ROOM_NAME", "default")
    MMSRV = os.environ.get("MMSRV", "127.0.0.1")
    MMPORT = int(os.environ.get("MMPORT", "7777"))

    reader, writer = await connect_stdin_stdout()

    player_id = (await reader.readline()).decode()
    map_size = (await reader.readline()).decode()

    cli_reader, cli_writer = None, None
    while not cli_reader:
        try:
            cli_reader, cli_writer = await asyncio.open_connection(MMSRV, MMPORT)
            cli_writer.write(json.dumps(dict(mode='host', player_name = PLAYER_NAME, room = ROOM_NAME, player_id=player_id, map_size=map_size)).encode() + b'\n')
            await asyncio.wait_for(cli_writer.drain(), 30)
            match_info = await cli_reader.readline()
            if not match_info:
                raise Exception(f"no players in room '{ROOM_NAME}'")
            print('match', match_info, file=sys.stderr)
            break
        except Exception as exc:
            await asyncio.sleep(1)
            print("exc", exc, file=sys.stderr)
            cli_reader, cli_writer = None, None
            continue

    cli_writer.write(player_id.encode())
    cli_writer.write(map_size.encode())
    await cli_writer.drain()

    try:
        pipe1 = pipe(reader, cli_writer)
        pipe2 = pipe(cli_reader, writer)
        await asyncio.gather(pipe1, pipe2)
        print('match finished', file=sys.stderr)
    except Exception as exc:
        print(f"exception: {repr(exc)}", file=sys.stderr)
    finally:
        print("closing connection", file=sys.stderr)
        cli_writer.close()

if __name__ == "__main__":
    asyncio.run(main())

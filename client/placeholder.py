import asyncio
import json
import logging
import os
import struct
import sys
import zlib
from asyncio import IncompleteReadError

async def connect_stdin_stdout():
    loop = asyncio.get_event_loop()
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await loop.connect_read_pipe(lambda: protocol, sys.stdin)
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, sys.stdout)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader, loop)
    return reader, writer

async def compress_pipe(reader, writer, timeout=60):
    try:
        while not reader.at_eof():
            data = await asyncio.wait_for(reader.read(2048*4), timeout)
            data_comp = zlib.compress(data, level=9)
            hdr = struct.pack("I", len(data_comp))
            writer.write(hdr)
            writer.write(data_comp)
            await asyncio.wait_for(writer.drain(), timeout)
    except IncompleteReadError:
        logging.error("connection closed")
    finally:
        writer.close()

async def decompress_pipe(reader, writer, timeout=60):
    try:
        while not reader.at_eof():
            header = await asyncio.wait_for(reader.readexactly(4), timeout)
            data_size = struct.unpack("I", header)[0]
            data = await asyncio.wait_for(reader.readexactly(data_size), timeout)
            writer.write(zlib.decompress(data))
            await asyncio.wait_for(writer.drain(), timeout)
    except IncompleteReadError:
        logging.error("connection closed")
    finally:
        writer.close()

async def main():
    logging.basicConfig(level=logging.DEBUG)
    PLAYER_NAME = os.environ.get("PLAYER", "placeholder")
    ROOM_NAME = os.environ.get("ROOM", "default")
    MMSRV = os.environ.get("SRV", "127.0.0.1")
    MMPORT = int(os.environ.get("PORT", "7777"))

    reader, writer = await connect_stdin_stdout()

    cli_reader, cli_writer = None, None
    while not cli_reader:
        try:
            cli_reader, cli_writer = await asyncio.open_connection(MMSRV, MMPORT)
            cli_writer.write(json.dumps(dict(mode='host', player_name = PLAYER_NAME, room = ROOM_NAME)).encode() + b'\n')
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

    try:
        pipe1 = compress_pipe(reader, cli_writer)
        pipe2 = decompress_pipe(cli_reader, writer)
        await asyncio.gather(pipe1, pipe2)
        print('match finished', file=sys.stderr)
    except Exception as exc:
        print(f"exception: {repr(exc)}", file=sys.stderr)
    finally:
        print("closing connection", file=sys.stderr)
        cli_writer.close()

if __name__ == "__main__":
    asyncio.run(main())

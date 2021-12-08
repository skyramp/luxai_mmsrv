import asyncio
import json
import logging
import signal
import struct
import zlib
from asyncio import IncompleteReadError


class BrokenPipeException(Exception):
    pass

async def compress_pipe(reader, writer, timeout=60):
    try:
        while not reader.at_eof():
            data = await asyncio.wait_for(reader.read(2048*4), timeout)
            data_comp = zlib.compress(data, level=9)
            hdr = struct.pack("I", len(data_comp))
            writer.write(hdr)
            writer.write(data_comp)
            await asyncio.wait_for(writer.drain(), timeout)
    except (IncompleteReadError, BrokenPipeError):
        logging.error("connection broken")
    finally:
        logging.warning("closing connection")
        writer.close()

async def decompress_pipe(reader, writer, timeout=60):
    try:
        while not reader.at_eof():
            header = await asyncio.wait_for(reader.readexactly(4), timeout)
            data_size = struct.unpack("I", header)[0]
            data = await asyncio.wait_for(reader.readexactly(data_size), timeout)
            writer.write(zlib.decompress(data))
            await asyncio.wait_for(writer.drain(), timeout)
    except (IncompleteReadError, BrokenPipeError):
        logging.error("connection broken")
    finally:
        logging.warning("closing connection")
        writer.close()


async def prepare_connection(name, player_name, room, srv, port):
    timeout = 30
    while True:
        try:
            cli_reader, cli_writer = await asyncio.wait_for(asyncio.open_connection(srv, port), timeout)

            cli_writer.write(json.dumps(dict(mode='player', room=room, player_name = player_name)).encode() + b'\n')
            await asyncio.wait_for(cli_writer.drain(), timeout)

            logging.info(f"{name}: waiting for placeholder process in room '{room}'")
            match_info = await asyncio.wait_for(cli_reader.readline(), timeout)

            if not match_info:
                logging.info(f"{name}: no placeholder process in room '{room}', sleeping 10s and retrying")
                await asyncio.sleep(10)
                cli_writer.close()
                continue

            logging.info(f'{name}: running match {json.loads(match_info)}')
            cli_writer.write(json.dumps(dict(ready=True)).encode() + b'\n')
            await asyncio.wait_for(cli_writer.drain(), timeout)
            return cli_reader, cli_writer

        except Exception as exc:
            await asyncio.sleep(10)
            logging.exception(f'{name}: exception while waiting for match {repr(exc)}')
            continue


async def run_client(name, args):
    cli_reader, cli_writer = await prepare_connection(name, args.player, args.room, args.srv, args.port)

    agent_process = await asyncio.create_subprocess_shell(
        args.cmd,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    try:
        pipe1 = compress_pipe(agent_process.stdout, cli_writer, timeout=30)
        pipe2 = decompress_pipe(cli_reader, agent_process.stdin, timeout=30)
        await asyncio.gather(pipe1, pipe2)
    except Exception as exc:
        logging.exception(f"{name}: exception {repr(exc)}")
        return
    finally:
        logging.info(f"{name}: closing connection")
        cli_writer.close()

        try:
            agent_process.kill()
        except ProcessLookupError:
            pass


async def run_client_forever(name, args):
    while True:
        logging.info(f"{name}: waiting for next match")
        await run_client(name, args)


async def main(args):
    tasks = []
    for i in range(args.workers):
        tasks += [asyncio.create_task(run_client_forever(f'{args.player}[{i}]', args))]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--player", type=str, required=True, help="player name")
    parser.add_argument("--room", type=str, default="default", help="room name")
    parser.add_argument("--srv", type=str, default="127.0.0.1", help="server addr")
    parser.add_argument("--port", type=int, default=7777, help="server port")
    parser.add_argument("--cmd", type=str, required=True, help="agent cmd line")
    parser.add_argument("--workers", type=int, default=1, help="max concurrent games")

    args = parser.parse_args()
    asyncio.run(main(args))

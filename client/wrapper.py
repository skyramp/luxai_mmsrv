import asyncio
import logging
import signal
import json
import sys

class BrokenPipeException(Exception):
    pass

async def pipe(reader, writer, timeout=30):
    try:
        while not reader.at_eof():
            writer.write(await asyncio.wait_for(reader.read(2048), timeout))
            await writer.drain()
    finally:
        writer.close()

async def prepare_connection(player_name, room, srv, port):
    while True:
        try:
            cli_reader, cli_writer = await asyncio.open_connection(srv, port)
            cli_writer.write(json.dumps(dict(mode='player', room=room, player_name = player_name)).encode() + b'\n')
            await cli_writer.drain()
            match_info = await cli_reader.readline()
            if not match_info:
                await asyncio.sleep(10)
                logging.info("waiting for placeholder process")
                cli_writer.close()
                continue

            logging.info('match %s' % json.loads(match_info))
            cli_writer.write(json.dumps(dict(ready=True)).encode() + b'\n')
            await cli_writer.drain()
            return cli_reader, cli_writer

        except Exception as exc:
            await asyncio.sleep(10)
            logging.exception("exc: %s" % exc)
            continue



async def make_writer(f, reader):
    loop = asyncio.get_event_loop()
    w_transport, w_protocol = await loop.connect_write_pipe(asyncio.streams.FlowControlMixin, f)
    writer = asyncio.StreamWriter(w_transport, w_protocol, reader=reader, loop=loop)
    return writer

async def main(args):
    agent_process = await asyncio.create_subprocess_shell(
        args.cmd,
        stdout=asyncio.subprocess.PIPE,
        stdin=asyncio.subprocess.PIPE
    )

    cli_reader, cli_writer = await prepare_connection(args.name, args.room, args.srv, args.port)

    try:
        pipe1 = pipe(agent_process.stdout, cli_writer)
        pipe2 = pipe(cli_reader, agent_process.stdin)
        await asyncio.gather(pipe1, pipe2)
    except Exception as exc:
        logging.exception("exception %s" % repr(exc))
        return
    finally:
        logging.info("closing connection")
        cli_writer.close()
        agent_process.kill()

if __name__ == "__main__":
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    logging.basicConfig(level=logging.INFO)

    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, required=True, help="agent name")
    parser.add_argument("--room", type=str, default="default", help="room name")
    parser.add_argument("--srv", type=str, default="127.0.0.1", help="server addr")
    parser.add_argument("--port", type=int, default=7777, help="server port")
    parser.add_argument("--cmd", type=str, required=True, help="agent cmd line")
    args = parser.parse_args()

    while True:
        logging.info("waiting for next match")
        try:
            asyncio.run(main(args))
        except KeyboardInterrupt:
            break
        except Exception as exc:
            logging.exception("exception: %s" % exc)
            continue

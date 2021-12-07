import asyncio
import json
import logging
import os
import sys
import uuid
from collections import defaultdict


class PendingGames:
    def __init__(self):
        self.pending = defaultdict(dict)
        self.lk = asyncio.Lock()

    async def push_pending(self, room, conn):
        async with self.lk:
            ix = str(uuid.uuid4())
            self.pending[room][ix] = conn
            return ix

    async def get_by_ix(self, room, ix):
        async with self.lk:
            if ix in self.pending:
                try:
                    x = self.pending[ix]
                    del self.pending[ix]
                    return x
                except KeyError:
                    return None

    async def get_pending(self, room):
        async with self.lk:
            if room not in self.pending:
                return None
            proom = self.pending[room]
            if not proom:
                return None
            ix = next(iter(proom.keys()))
            x = proom[ix]
            del proom[ix]
            if not proom:
                del self.pending[room]
            return x



pg = PendingGames()

async def handle_player(player_header, player_reader, player_writer):
    # print('waiting for host', player_header)
    room = player_header['room']
    logging.info(f"player {player_header} waits for host in room {room}")
    ix = await pg.push_pending(room, (player_header, player_reader, player_writer))
    await asyncio.sleep(15)
    p = await pg.get_by_ix(room, ix)
    if not p:
        return
    # print('discarding connection', player_header)
    player_writer.close()

async def pipe(reader, writer, timeout=30):
    try:
        while not reader.at_eof():
            writer.write(await asyncio.wait_for(reader.read(2048), timeout))
    finally:
        writer.close()

async def handle_host(host_reader, host_writer):
    data = await host_reader.readline()

    host_header = json.loads(data.decode())
    if host_header['mode'] == 'player':
        return await handle_player(host_header, host_reader, host_writer)
    elif host_header['mode'] != 'host':
        host_writer.close()
        return

    room = host_header['room']

    while True:
        await asyncio.sleep(1)
        opponent_conn = await pg.get_pending(room)
        if not opponent_conn:
            logging.info(f"no players in room {room} for {host_header}")
            host_writer.close()
            return

        player_header, player_reader, player_writer = opponent_conn
        try:
            logging.info(f"trying match {host_header} {player_header}")
            player_writer.write(json.dumps(dict(host=host_header)).encode() + b'\n')
            await player_writer.drain()
            ok_marker = await player_reader.readline()
            ok_marker_dec = json.loads(ok_marker.decode())
            logging.info(f"player {player_header} ready")
            break
        except Exception as exc:
            logging.error("handshake failed: %s" % repr(exc))
            player_writer.close()
            continue

    logging.info(f"starting match {host_header} {player_header}")
    host_writer.write(json.dumps(dict(player=player_header)).encode() + b'\n')
    await host_writer.drain()

    try:
        pipe1 = pipe(host_reader, player_writer)
        pipe2 = pipe(player_reader, host_writer)
        await asyncio.gather(pipe1, pipe2)
    except Exception as exc:
        logging.exception("exception: %s" % exc)
    finally:
        logging.info(f"stopping match {host_header} {player_header}")
        player_writer.close()
        host_writer.close()


async def main():
    logging.basicConfig(level=logging.INFO)
    ADDR = os.environ.get("ADDR", "127.0.0.1")
    PORT = os.environ.get("PORT", 7777)
    server = await asyncio.start_server(handle_host, ADDR, PORT)

    addrs = ', '.join(str(sock.getsockname()) for sock in server.sockets)
    logging.info(f'Serving on {addrs}')

    async with server:
        await server.serve_forever()

asyncio.run(main())
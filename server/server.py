import asyncio
import json
import logging
import os
import random
import sys
import uuid
from collections import defaultdict
from typing import DefaultDict, Any


class PendingGames:
    def __init__(self):
        self.pending:DefaultDict[str, DefaultDict[str, DefaultDict[str, Any]]] = defaultdict(lambda : defaultdict(lambda : defaultdict(Any)))
        self.lk = asyncio.Lock()

    async def push_pending(self, room, player_name, conn):
        async with self.lk:
            ix = str(uuid.uuid4())
            self.pending[room][player_name][ix] = conn
            return ix

    async def get_by_ix(self, room, player_name, ix):
        async with self.lk:
            pending_room = self.pending.get(room)
            if not pending_room:
                return None

            pending_player = pending_room.get(player_name)
            if not pending_player:
                return None

            pending_client = pending_player.get(ix)
            if not pending_client:
                return None

            del pending_player[ix]
            if not pending_player:
                del pending_room[player_name]
            if not pending_room:
                del self.pending[room]
            return pending_client

    async def get_pending_client(self, room, exclude_player_name):
        async with self.lk:
            pending_room = self.pending.get(room)
            if not pending_room:
                return None

            players_in_room = [ p for p in pending_room if p != exclude_player_name]
            if not players_in_room:
                return None

            player_name = random.choice(players_in_room)
            pending_player = pending_room.get(player_name)
            if not pending_player:
                return None

            ix = next(iter(pending_player.keys()))

            pending_client = pending_player[ix]
            del pending_player[ix]

            if not pending_player:
                del pending_room[player_name]
            if not pending_room:
                del self.pending[room]
            return pending_client


pg = PendingGames()

async def handle_player(player_header, player_reader, player_writer):
    room = player_header['room']
    player_name = player_header['player_name']

    logging.info(f"player {player_header} waits for host in room {room}")
    ix = await pg.push_pending(room, player_name, (player_header, player_reader, player_writer))

    await asyncio.sleep(15)
    p = await pg.get_by_ix(room, player_name, ix)
    if not p:
        return

    logging.error(f'discarding connection {player_header}')
    player_writer.close()

async def pipe(reader, writer, timeout=60):
    try:
        while not reader.at_eof():
            writer.write(await asyncio.wait_for(reader.read(2048), timeout))
            await asyncio.wait_for(writer.drain(), timeout)
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
    player_name = host_header['player_name']

    while True:
        await asyncio.sleep(1)
        opponent_conn = await pg.get_pending_client(room, player_name)
        if not opponent_conn:
            logging.info(f"no players in room {room} for {host_header}")
            host_writer.close()
            return

        player_header, player_reader, player_writer = opponent_conn
        try:
            logging.info(f"trying match {host_header} {player_header}")
            player_writer.write(json.dumps(dict(host=host_header)).encode() + b'\n')
            await player_writer.drain()
            ok_marker = json.loads((await player_reader.readline()).decode())
            logging.info(f"player {player_header} ready {ok_marker}")
            break
        except Exception as exc:
            logging.error("handshake failed: %s" % repr(exc))
            player_writer.close()
            continue

    logging.info(f"starting match {host_header} {player_header}")
    host_writer.write(json.dumps(dict(player=player_header)).encode() + b'\n')
    await host_writer.drain()

    try:
        pipe1 = pipe(host_reader, player_writer, timeout=30)
        pipe2 = pipe(player_reader, host_writer, timeout=30)
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
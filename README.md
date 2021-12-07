# luxai 2021 client-server matchmaking tools

some tools for matchmaking using remote server and without need to share agents code

## How to use

1. Someone need to start server and share IP/port.
2. You need to run your agent with client wrapper
3. You might want to start luxai host runner to play against someone else and get the replay


## Server

usage: `ADDR=127.0.0.1 PORT=7777 python ./server/server.py`

## Client wrapper

usage (assuming your agent is main.py): `python ./client/wrapper.py --name "agent_name" --room "my_matchmaking_room" --srv 127.0.0.1 --port 7777 --cmd "python main.py"`

wrapper will run your agent indefinitely, until killed

## Host
Someone has to be host to run luxai runner. `placeholder.py` is a placeholder agent that would communicate with some client agent in the specified room. 

usage for one-time runs (you might want to run host in `while True` loop):
```
ROOM_NAME="my_matchmaking_room" MMPORT=7778 lux-ai-2021 ./client/placeholder.py ./client/placeholder.py --maxtime 1000000
```
or 
```
PLAYER_NAME="test" ROOM_NAME="my_matchmaking_room" MMSRV=127.0.0.1 MMPORT=7778 lux-ai-2021 ./client/placeholder.py my_another_agent.py --maxtime 1000000
```
or in tournament mode
```
PLAYER_NAME="test" ROOM_NAME="my_matchmaking_room" MMSRV=127.0.0.1 MMPORT=7778 lux-ai-2021 ./client/placeholder.py my_another_agent.py --maxtime 1000000 --tournament
```

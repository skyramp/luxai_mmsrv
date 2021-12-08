# luxai 2021 client-server matchmaking tools

Some tools for matchmaking using remote server without sharing your agents source code.

```
├── clients
│   ├── placeholder.py
│   ├── runner.py
├── server
│   └── server.py
```

## How it works
`runner.py` is a wrapper that runs your agent locally, waits for observations from server, and sends actions back.

`placeholder.py` is a dummy agent that pairs with some runner connected to server, reads observations from lux-ai-2021, sends them to the selected runner and waits for actions.

`server.py` arranges pairing between runners and placeholders and transfers data between them

## Installing
Clone the repo somewhere (for example `~/luxai_mmsrv`)

## How to use
Find someone you want to play against, and choose who will be simulating games (by running lux-ai-2021) and who would run their bots with runner. 
You might as well both start your own bots as runners and run simulations against placeholder agent.

### If you run the runner and someone else runs lux-ai-2021 simulator
1. Chose some name for your agent, for example `player1`. Server won't pair placeholder and runner with same player name.
2. Select some unique room name, for example `my_matchmaking_room`
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in --srv option)
```
python ~/luxai_mmsrv/clients/runner.py --room "my_matchmaking_room" --player "player1" --workers 1 --srv 127.0.0.1 --cmd "python main.py"
```
4. While runner is working, your agent could be selected to play a match against another players inside the room, but you would not be able to get replays. 
   You might want to increase workers count if you want your runner to run multiple matches simultaneously. 

### If you run lux-ai-2021 simulator and someone else runs the runner 
1. Chose name for your agent, for example `player2`. Server won't pair placeholder and runner with same player name.
2. Ask someone you want to play with to be client and choose room name (for example `my_matchmaking_room`)
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in SRV env variable)
```
ROOM="my_matchmaking_room" PLAYER="player2" SRV=127.0.0.1 lux-ai-2021 ~/luxai_mmsrv/clients/placeholder.py main.py --maxtime 30000
```
4. This command starts `lux-ai-2021` to run single match with placeholder bot. 
   Placeholder bot (`placeholder.py`) would pair with random runner from the room `my_matchmaking_room` on server, and will communicate with it to send observations and get actions back. 
   You might want to change other lux-ai-2021 options (like tune replay saving options, add tournament, rankSystem and so on). 
   Large maxtime might be useful if all runners are currently busy playing matches.
   

### Server
If you want to run server by yourself - better look into dockerfiles and sources.

usage: `ADDR=0.0.0.0 PORT=7777 python server.py`




## Usage

### runner
```
usage: runner.py [-h] --player PLAYER [--room ROOM] [--srv SRV] [--port PORT] --cmd CMD [--workers WORKERS]

optional arguments:
  -h, --help         show this help message and exit
  --player PLAYER    player name
  --room ROOM        room name (default room name is 'default')
  --srv SRV          server addr (default 127.0.0.1)
  --port PORT        server port (default 7777)
  --cmd CMD          agent cmd line
  --workers WORKERS  max concurrent games (default 1)
```

### placeholder agent

host agent can be configured with following environment variables:
```
PLAYER - player name (default player name is 'placeholder')
ROOM - room (default room name is 'default')
SRV - server address (default 127.0.0.1)
PORT - server port (default 7777)

usage: ROOM="my_matchmaking_room" PLAYER="test_host_name" SRV=127.0.0.1 PORT=7777 lux-ai-2021 ~/luxai_mmsrv/clients/placeholder.py main.py --maxtime 30000 
```

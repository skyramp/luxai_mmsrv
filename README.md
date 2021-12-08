# luxai 2021 client-server matchmaking tools

Some tools for matchmaking using remote server and without need to share agents code.

## How it works
Client wrapper runs your agent, waits for observations from placeholder agent and sends actions back.

Placeholder is just a dummy agent that reads observations from luxai runner, pushes it to remote client and waits for actions from remote client. You can use placeholder agent as you use any other agent in while locallt testing your bots.
 
## Installing
Clone the repo somewhere (for example `~/luxai_mmsrv`)

## How to use
Find someone you want to play against, and choose who will be hosting games and who would run their bots as client. 
You might as well both start your bots as host and as clients.

### If you run the client wrapper and someone else runs the host
1. Chose some name for your agent, for example `test_client_name`. Server won't start matches between hosts and players with same name.
2. Select some unique room name, for example `my_matchmaking_room`
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in --srv option)
```
python ~/luxai_mmsrv/client/wrapper.py --room "my_matchmaking_room" --player "test_client_name" --workers 1 --srv 127.0.0.1 --cmd "python main.py"
```
4. While client wrapper is working, you will be running your own bot against another players inside selected room, but you would not be able to get replays. 
   You might want to increase workers count if you want your client to run multiple matches simultaneously. 

### If you run the host and someone else runs the client wrapper 
1. Chose name for your agent, for example `test_host_name`. Server won't start matches between hosts and players with same name.
2. Ask someone you want to play with to be client and choose room name (for example `my_matchmaking_room`)
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in SRV env variable)
```
ROOM="my_matchmaking_room" PLAYER="test_host_name" SRV=127.0.0.1 lux-ai-2021 ~/luxai_mmsrv/client/placeholder.py main.py --maxtime 30000
```
4. This command basically starts `lux-ai-2021` to run single match with placeholder bot. 
   Placeholder bot (`placeholder.py`) would select random bot running as client from the room `my_matchmaking_room` on server, and will communicate with it to send observations and get actions. 
   You might want to change other lux-ai-2021 options (like tune replay saving options, add tournament, rankSystem and so on). 
   Large maxtime might be useful if all client bots are currently busy playing matches (one client bot process runs one game at a time)
   
### Server
If you want to run server by yourself - better look into dockerfiles and sources.

usage: `ADDR=0.0.0.0 PORT=7777 python ./server/server.py`




## Usage

### wrapper
```
usage: wrapper.py [-h] --player PLAYER [--room ROOM] [--srv SRV] [--port PORT] --cmd CMD [--workers WORKERS]

optional arguments:
  -h, --help         show this help message and exit
  --player PLAYER    player name
  --room ROOM        room name
  --srv SRV          server addr (default 127.0.0.1)
  --port PORT        server port (default 7777)
  --cmd CMD          agent cmd line
  --workers WORKERS  max concurrent games
```

### placeholder

placeholder is configured with following environment variables:
```
PLAYER - player name (default player name is 'placeholder')
ROOM - room (default room name is 'default')
SRV - server address (default 127.0.0.1)
PORT - server port (default 7777)

usage: ROOM="my_matchmaking_room" PLAYER="test_host_name" SRV=127.0.0.1 PORT=7777 lux-ai-2021 ~/luxai_mmsrv/client/placeholder.py main.py --maxtime 30000 
```

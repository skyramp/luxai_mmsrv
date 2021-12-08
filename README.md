# luxai 2021 client-server matchmaking tools

Some tools for matchmaking using remote server and without need to share agents code.

## How it works
Client wrapper runs your agent, waits for observations from placeholder agent and sends actions back.

Placeholder is just a dummy agent that reads observations from luxai runner, pushes it to remote client and waits for actions from remote client. You can use placeholder agent as you use any other agent in while locallt testing your bots.
 
## Installing
Clone the repo somewhere (for example `~/luxai_mmsrv`)

## How to use

### You run the client wrapper and someone else runs the host
1. Chose some name for your agent, for example `test_client_name`. Server won't start matches between hosts and players with same name.
2. Select some unique room name, for example `my_matchmaking_room`
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in --srv option)
```
python ~/luxai_mmsrv/client/wrapper.py --name "test_client_name" --room "my_matchmaking_room" --workers 1 --srv 127.0.0.1 --port 7777 --cmd "python main.py"
```
4. While client wrapper is working, you will be running your own bot against another players, but you would not be able to get replays. 
   You might want to increase workers count if you want your client to run multiple matches simultaneously. 

### You run the host and someone else runs the client wrapper 
1. Chose name for your agent, for example `test_host_name`. Server won't start matches between hosts and players with same name.
2. Ask someone you want to play with to be client and choose room name (for example `my_matchmaking_room`)
3. Assuming your bot is `main.py`, run following (don't forget to replace server address in MMSRV env variable)
```
ROOM_NAME="my_matchmaking_room" PLAYER_NAME="test_host_name" MMSRV=127.0.0.1 MMPORT=7777 lux-ai-2021 ~/luxai_mmsrv/client/placeholder.py main.py --maxtime 10000
```
4. `placeholder.py` would select random bot from the room `my_matchmaking_room` on server, and you will run match against it. 
   This will run single match against some other player. 
   You might want to change other lux-ai-2021 options (like tune replay saving options, add tournament, rankSystem and so on). 
   Large max time might be useful if all client bots are busy (one client bot process runs one game at a time)
   
### Server
If you want to run server by yourself - better look into dockerfiles and sources.

usage: `ADDR=0.0.0.0 PORT=7777 python ./server/server.py`

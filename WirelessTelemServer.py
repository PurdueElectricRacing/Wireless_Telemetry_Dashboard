import asyncio
import websockets
from datetime import datetime
import datetime
import json

# Contains list of all connected users
USERS = set()


def get_server(ip, port):
    print('Serving websocket server on ' + ip + ':' + str(port) + ' ...')
    return websockets.serve(on_client_connect, ip, port)


# Main server entry point
async def on_client_connect(websocket, path):
    connection_addr = (str(websocket.remote_address[0]) + ' : ' +
                       str(websocket.remote_address[1]))

    print('Connected to client at ' + connection_addr +
          ' on ' + str(datetime.datetime.now()))

    await websocket.send(json.dumps({'type': 'connected', 'payload': 'true',
                                     'timestamp': str(datetime.datetime.now())
                                     }))
    global USERS
    try:
        # Track all connected users to broadcast new data whenever available.
        USERS.add(websocket)
        # Recieve handler is used to monitor messages from the clients.
        await recieve_data_loop(websocket)
        # Client disconnects whenever this handler returns.
        USERS.remove(websocket)
    finally:
        print("Client disconnected.")


# Broadcast data to all users connected on the socket
async def send_data(data):
    global USERS
    if USERS:
        payload = json.dumps(data, default=str)

        await asyncio.wait([user.send(payload) for user in USERS])


# This function runs in its own loop to handle recieving any messages
async def recieve_data_loop(websocket):
    while websocket.open:
        try:
            message = await websocket.recv()
            print('Message from client: ' + str(message))
        except Exception:
            print('Client disconnected!')
            return


if __name__ == "__main__":
    ip = '127.0.0.1'
    port = 5000
    asyncio.get_event_loop().run_until_complete(get_server(ip, port))
    asyncio.get_event_loop().run_forever()

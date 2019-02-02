import WirelessTelemServer as server
import asyncio
import random
import json
import os

# This file simulates the job of the DAQ code.
# A server is setup and broadcast on ip:port
# Data is sent every second to simulate reading the CAN bus

ip = '127.0.0.1'
port = 5000
currentDir = os.path.dirname(__file__)

async def send_data():
    print("Sending data...")
    while True:
        f = open(os.path.join(currentDir, 'logs/2018_11_19_20_41_50.txt'), "r")
        lines = f.readlines()
        for line in lines:
            await asyncio.sleep(0.002)
            await server.send_data(line)

async def run_server(ip, port):
    wait_task = asyncio.ensure_future(send_data())
    server_task = asyncio.ensure_future(server.get_server('127.0.0.1', 5000))

    done, pending = await asyncio.wait(
        [wait_task, server_task],
        return_when=asyncio.ALL_COMPLETED
    )

asyncio.get_event_loop().run_until_complete(run_server(ip, port))

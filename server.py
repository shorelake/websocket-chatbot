import time
import random

import asyncio
import websockets

from message import Message

msg_queue = asyncio.Queue()


async def consumer_handler(websocket):
    global msg_queue
    while True:
        try:
            data = await websocket.recv()
        except websockets.exceptions.ConnectionClosedError as err:
            print('connection closed by remote')
            break
        msg = Message.from_json(data)        
        print("Received message {}".format(msg))
        await msg_queue.put(msg)


async def producer_handler(websocket):
    global msg_queue
    while True:
        print("Waiting for message in queue")
        msg = await msg_queue.get()
        msg.sender = "Bot"
        msg.text = 'rep: ' + msg.text
        msg.created_at = int(time.time())
        try:
            await websocket.send(msg.json())
        except websockets.exceptions.ConnectionClosedError as err:
            print('connection closed by remote')
            break
        print("Message '{}' sent".format(msg))
        await asyncio.sleep(random.random() * 2)
        try:
            await websocket.send(msg.json())
        except websockets.exceptions.ConnectionClosedError as err:
            print('connection closed by remote')
            break
        print("Message '{}' double sent".format(msg))


async def handler(websocket, path):
    print("Got a new connection...")
    consumer_task = asyncio.ensure_future(consumer_handler(websocket))
    producer_task = asyncio.ensure_future(producer_handler(websocket))

    done, pending = await asyncio.wait([consumer_task, producer_task]
                                       , return_when=asyncio.FIRST_COMPLETED)
    print("Connection closed, canceling pending tasks")
    for task in pending:
        task.cancel()


host = 'localhost'
port = 5555
start_server = websockets.serve(handler, host, port)

asyncio.get_event_loop().run_until_complete(start_server)
print(f'start to listem to {host}:{port}')
asyncio.get_event_loop().run_forever()

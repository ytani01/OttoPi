#!/usr/bin/env python3

import asyncio
import websockets
from MyLogger import get_logger

log = get_logger(__name__, True)

import ssl
context = ssl.SSLContext(ssl.PROTOCOL_TLSv1)

async def hello():
    uri = 'wss://192.168.0.228:9003/'
    async with websockets.connect(uri) as websocket:
        await websocket.send('Hello world!')

asyncio.get_event_loop().run_until_complete(hello())

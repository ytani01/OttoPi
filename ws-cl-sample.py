#!/usr/bin/env python3

import asyncio
import websockets
from MyLogger import get_logger

log = get_logger(__name__, True)

async def hello():
    uri = 'ws://localhost:9002/'
    async with websockets.connect(uri) as websocket:
        await websocket.send('Hello world!')

asyncio.get_event_loop().run_until_complete(hello())

#!/usr/bin/env python3

import asyncio
import pathlib
import ssl
import websockets
from MyLogger import get_logger

log = get_logger(__name__, True)

ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
cert = pathlib.Path(__file__).with_name('cert.pem')
log.info('aaa')
ssl_context.load_verify_locations(cert)
log.info('bbb')

async def hello():
    uri = 'wss://127.0.0.1:9003/'
    async with websockets.connect(uri, ssl=ssl_context) as websocket:
        await websocket.send('Hello world!')

asyncio.get_event_loop().run_until_complete(hello())

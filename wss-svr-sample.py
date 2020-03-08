#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
webscokets sample
"""
import asyncio
import websockets
import ssl
import pathlib
import sys
from MyLogger import get_logger

log = get_logger(__name__, True)

async def handle(websocket, path):
    msg = await websocket.recv()
    log.info('msg=%s', msg)

def main():
    log.debug('start')

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    cert = pathlib.Path(__file__).with_name('cert.pem')
    ssl_context.load_cert_chain(cert)

    start_server = websockets.serve(handle, "0.0.0.0", 9003,
                                    ssl=ssl_context)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == '__main__':
    main()

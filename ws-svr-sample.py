#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
webscokets sample
"""
import asyncio
import websockets
import sys
from MyLogger import get_logger

log = get_logger(__name__, True)


async def handle(websocket, path):
    async for msg in websocket:
        log.debug('msg=%s', msg)

def main():
    log.debug('start')

    start_server = websockets.serve(handle, "0.0.0.0", 9002)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(start_server)
    loop.run_forever()


if __name__ == '__main__':
    main()

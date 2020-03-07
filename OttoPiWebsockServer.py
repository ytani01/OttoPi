#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
OttoPi WebSocket Server
"""
__author__ = 'Yoichi Tanibayashi'
__date__ = '2020'

from OttoPiClient import OttoPiClient
import asyncio
import websockets
import click
from MyLogger import get_logger


class OttoPiWebsockServer():
    DEF_PORT = 9001
    DEF_SVR_PORT = 12345

    def __init__(self, port=DEF_PORT, host="0.0.0.0",
                 svrhost='localhost', svrport=DEF_SVR_PORT,
                 debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('host=%s, port=%s', host, port)
        self._log.debug('svrhost=%s, svrport=%s', svrhost, svrport)

        self.svrhost = svrhost
        self.svrport = svrport

        # websockets
        self.start_server = websockets.serve(self.handle, host, port)
        self.loop = asyncio.get_event_loop()

    def main(self):
        self._log.debug('')

        self._log.info('start_server ..')
        self.loop.run_until_complete(self.start_server)
        
        self._log.info('run_forever ..')
        self.loop.run_forever()

    def end(self):
        self._log.debug('')

    async def handle(self, websocket, path):
        self._log.debug('websocket=%s:%s, path=%s',
                        websocket.local_address,
                        websocket.host,
                        path)
        msg = await websocket.recv()
        self._log.debug('msg=%s', msg)

        robot_client = OttoPiClient(self.svrhost, self.svrport, debug=False)
        robot_client.send_cmd(msg)
        robot_client.close()
        self._log.info('send msg=%s: done', msg)

class App:
    def __init__(self, svr_port=OttoPiWebsockServer.DEF_SVR_PORT, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('svr_port=svr_port')

        self.svr_port = svr_port
        self.ws_svr = OttoPiWebsockServer(port=OttoPiWebsockServer.DEF_PORT,
                                          svrport=OttoPiWebsockServer.DEF_SVR_PORT,
                                          debug=self._dbg)

    def main(self):
        self._log.debug('')
        self.ws_svr.main()

    def end(self):
        self.ws_svr.end()
        self._log.debug('')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help='''
OttoPi Websocket Server
''')
@click.option('--svr_port', '--sp', 'svr_port', type=int,
              default=OttoPiWebsockServer.DEF_SVR_PORT,
              help='server port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(svr_port, debug):
    _log = get_logger(__name__, debug)
    _log.debug('svr_port=%s', svr_port)

    app = App(svr_port=svr_port, debug=debug)
    try:
        app.main()
    finally:
        app.end()


if __name__ == '__main__':
    main()

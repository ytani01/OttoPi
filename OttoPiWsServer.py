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
from websocket_server import WebsocketServer
import click
from MyLogger import get_logger


class OttoPiWsServer():
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
        self.robotsvr = None
        self.server = WebsocketServer(port, host=host)

    def new_client(self, client, server):
        self._log.debug('client=%s', client)
        self.robotsvr = OttoPiClient(self.svrhost, self.svrport,
                                     debug=self._dbg)

    def client_left(self, client, server):
        self._log.debug('client=%s', client)
        self.robotsvr.close()

    def message_received(self, client, server, msg):
        self._log.debug('client=%s, msg=%s', client, msg)
        self.msg = msg.encode('utf-8')
        self._log.info('msg=%s.', msg)
        self.robotsvr.send_cmd(msg)

    def run(self):
        self._log.debug('')
        self.server.set_fn_new_client(self.new_client)
        self.server.set_fn_client_left(self.client_left)
        self.server.set_fn_message_received(self.message_received)
        self.server.run_forever()


class App:
    def __init__(self, svr_port=OttoPiWsServer.DEF_SVR_PORT, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('svr_port=svr_port')

        self.svr_port = svr_port
        self.ws_svr = OttoPiWsServer(port=OttoPiWsServer.DEF_PORT,
                                     svrport=OttoPiWsServer.DEF_SVR_PORT,
                                     debug=self._dbg)

    def main(self):
        self._log.debug('')
        self.ws_svr.run()

    def end(self):
        self._log.debug('')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS, help='''
OttoPi WebSocket Server
''')
@click.option('--svr_port', '--sp', 'svr_port', type=int,
              default=OttoPiWsServer.DEF_SVR_PORT, help='server port number')
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

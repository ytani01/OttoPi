#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

import telnetlib
import time

import click

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN
logger = getLogger(__name__)
logger.setLevel(INFO)
console_handler = StreamHandler()
console_handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
console_handler.setFormatter(handler_fmt)
logger.addHandler(console_handler)
logger.propagate = False
def get_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l


#####
DEF_HOST = 'localhost'
DEF_PORT = 12345
    
#####
class OttoPiClient:
    def __init__(self, svr_host=DEF_HOST, svr_port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)

        self.svr_host = svr_host
        self.svr_port = svr_port

        self.tn = self.open(self.svr_host, self.svr_port)

    def __del__(self):
        self.logger.debug('')
        self.close()

    def open(self, svr_host=DEF_HOST, svr_port=DEF_PORT):
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)
        return telnetlib.Telnet(self.svr_host, self.svr_port)
        
    def close(self):
        self.logger.debug('')
        self.tn.close()

    def send_cmd(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        in_data = self.tn.read_very_eager()
        if len(in_data) > 0:
            self.logger.debug('in_data:%a', in_data)

        for ch in cmd:
            self.logger.debug('ch=%a(0x%02x)', ch, ord(ch))

            self.tn.write(ch.encode('utf-8'))

            time.sleep(0.1)

            in_data = self.tn.read_very_eager()
            if len(in_data) > 0:
                self.logger.debug('in_data:%a', in_data)


##### Sample
class Sample:
    def __init__(self, svr_host, svr_port, command='', debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)
        self.logger.debug('command=%s', command)

        self.cl = OttoPiClient(svr_host, svr_port, debug=self.debug)
        self.command = command

    def main(self):
        self.logger.debug('command:%s', self.command)
        
        if self.command != '':
            for ch in self.command:
                self.logger.debug('ch=%a', ch)
                self.cl.send_cmd(ch)
                time.sleep(3)
            self.cl.send_cmd('s')
        else:
            self.cl.send_cmd('1')
            time.sleep(3)
            self.cl.send_cmd('2')
            time.sleep(3)
            self.cl.send_cmd('s')

    def end(self):
        self.logger.debug('')
        self.cl.close()

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('svr_host', type=str, default="localhost")
@click.argument('svr_port', type=int, default=DEF_PORT)
@click.option('--command', '-c', type=str, default='',
              help='control commands')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(svr_host, svr_port, command, debug):
    logger = get_logger('', debug)
    logger.info('svr_host=%s, svr_port=%d', svr_host, svr_port)
    
    obj = Sample(svr_host, svr_port, command, debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()

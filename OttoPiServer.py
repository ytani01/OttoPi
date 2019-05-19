#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
from OttoPiCtrl import OttoPiCtrl

import pigpio
import socketserver
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
DEF_PORT = 12345

#####
class OttoPiHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.debug = server.debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('client_address: %s', client_address)
        
        self.robot = server.robot

        self.cmd_key = {
            'w': 'forward',
            'x': 'backward',
            'a': 'turn_left',
            'd': 'turn_right',
            'A': 'slide_left',
            'D': 'slide_right',
            '1': 'happy',
            '2': 'ojigi',
            '0': 'home',

            'h': 'move_up0',
            'H': 'move_down0',
            'j': 'move_up1',
            'J': 'move_down1',
            'k': 'move_up2',
            'K': 'move_down2',
            'l': 'move_up3',
            'L': 'move_down3',

            'u': 'home_up0',
            'U': 'home_down0',
            'i': 'home_up1',
            'I': 'home_down1',
            'o': 'home_up2',
            'O': 'home_down2',
            'p': 'home_up3',
            'P': 'home_down3',

            's': OttoPiCtrl.CMD_STOP,
            'S': OttoPiCtrl.CMD_STOP,
            '' : OttoPiCtrl.CMD_END}

        return super().__init__(request, client_address, server)

    def setup(self):
        self.logger.debug('')
        return super().setup()

    def net_write(self, msg):
        self.logger.debug('msg=%s', msg)
        try:
            self.wfile.write(msg)
        except:
            pass

    def handle(self):
        self.logger.debug('')
        
        # Telnet Protocol
        #
        # mode character
        #  0xff IAC
        #  0xfd D0
        #  0x22 LINEMODE
        self.net_write(b'\xff\xfd\x22')

        #self.robot.send_cmd('happy')

        self.net_write('# Ready\r\n'.encode('utf-8'))

        flag_continue = True
        while flag_continue:
            try:
                net_data = self.request.recv(512)
            except BaseException as e:
                self.logger.info('BaseException:%s:%s.', type(e), e)
                self.robot.send_cmd(OttoPiCtrl.CMD_STOP)
                return
            else:
                self.logger.debug('net_data:%a', net_data)

            try:
                decoded_data = net_data.decode('utf-8')
            except UnicodeDecodeError as e:
                self.logger.debug('%s:%s .. ignored', type(e), e)
                continue
            else:
                self.logger.debug('decoded_data:%a', decoded_data)

            self.net_write('\r\n'.encode('utf-8'))
            
            data = ''
            for ch in decoded_data:
                if ord(ch) >= 0x20:
                    data += ch
            self.logger.debug('data=%a', data)
            if len(data) == 0:
                self.logger.debug('No data .. disconnect')
                self.net_write('No data .. disconnect\r\n'.encode('utf-8'))
                break

            for ch in data:
                self.logger.debug('ch=\'%a\'', ch)

                if not ch in self.cmd_key.keys():
                    self.robot.send_cmd(OttoPiCtrl.CMD_STOP)
                    self.logger.debug('invalid command:\'%a\' .. stop', ch)
                    self.net_write('NG .. stop\r\n'.encode('utf-8'))
                    continue

                self.net_write('OK\r\n'.encode('utf-8'))
                self.robot.send_cmd(self.cmd_key[ch])

        #self.robot.send_cmd('ojigi')
        self.logger.debug('done')
        
    def finish(self):
        self.logger.debug('')
        return super().finish()
    

class OttoPiServer(socketserver.TCPServer):
    def __init__(self, pi=None, port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi   = %s', pi)
        self.logger.debug('port = %d', port)

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   = pigpio.pi()
            self.mypi = True
        self.logger.debug('mypi = %s', self.mypi)

        self.robot = OttoPiCtrl(self.pi, debug=self.debug)
        self.logger.debug('start robot')
        self.robot.start()
        time.sleep(1)

        self.port  = port

        try:
            super().__init__(('', self.port), OttoPiHandler)
        except:
            return None

    def serve_forever(self):
        self.logger.debug('')
        return super().serve_forever()

    def end(self):
        self.logger.debug('')

        #if self.robot.is_running():
        if self.robot.is_alive():
            self.logger.debug('stop robot')
            self.robot.send_cmd(OttoPiCtrl.CMD_END)
            self.logger.debug('join()')
            self.robot.join()
            self.logger.debug('join():done')

        if self.mypi:
            self.logger.debug('clean up pigpio')
            self.pi.stop()
            self.mypi = False
            
        self.logger.debug('done')
        
    def _del_(self):
        self.logger.debug('')
        self.end()
        
#####
class Sample:
    def __init__(self, port, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('port=%d', port)

        self.port   = port
        self.server = OttoPiServer(None, self.port, debug=self.debug)
        
    def main(self):
        self.logger.debug('')
        self.logger.debug('start server')
        self.server.serve_forever()
        
    def end(self):
        self.logger.debug('')
        self.server.end()
        self.logger.debug('done')
        
        
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('port', type=int, default=DEF_PORT)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, debug):
    logger = get_logger('', debug)
    logger.info('port=%d', port)

    obj = Sample(port, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.end()

if __name__ == '__main__':
    main()

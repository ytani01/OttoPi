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

DEF_PIN1 = 17
DEF_PIN2 = 27
DEF_PIN3 = 22
DEF_PIN4 = 23

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
            'h': 'happy',
            'o': 'ojigi',
            's': OttoPiCtrl.CMD_STOP,
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
                self.logger.warn('%s:%s .. ignored', type(e), e)
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
    def __init__(self, pi=None, pin=(DEF_PIN1, DEF_PIN2, DEF_PIN3, DEF_PIN4),
                 port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi = %s', pi)
        self.logger.debug('pin=%s', (pin))
        self.logger.debug('port=%d', port)

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   = pigpio.pi()
            self.mypi = True

        self.robot = OttoPiCtrl(self.pi, pin, debug=self.debug)
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
        super().serve_forever()

    def end(self):
        self.logger.debug('')

        #if self.robot.is_running():
        if self.robot.is_alive():
            self.logger.debug('stop robot')
            self.robot.send_cmd(OttoPiCtrl.CMD_END)
            self.robot.join()

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
    def __init__(self, port, pin, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('port=%d, pin=%s', port, pin)

        self.port   = port
        self.server = OttoPiServer(None, pin, self.port, debug=self.debug)
        
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
@click.argument('pin1', type=int, default=DEF_PIN1)
@click.argument('pin2', type=int, default=DEF_PIN2)
@click.argument('pin3', type=int, default=DEF_PIN3)
@click.argument('pin4', type=int, default=DEF_PIN4)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, pin1, pin2, pin3, pin4, debug):
    logger = get_logger('', debug)
    logger.info('port=%d, pins:%d,%d,%d,%d', port, pin1, pin2, pin3, pin4)

    obj = Sample(port, (pin1, pin2, pin3, pin4), debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.end()

if __name__ == '__main__':
    main()

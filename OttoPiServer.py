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

DEF_PIN1 = 4
DEF_PIN2 = 17
DEF_PIN3 = 27
DEF_PIN4 = 22

#####
class OttoPiHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.debug = server.debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('client_address: %s', client_address)
        
        self.robot = server.robot

        self.cmd = {
            'w': 'f',
            'x': 'b',
            'a': 'l',
            'd': 'r',
            'A': 'L',
            'D': 'R',
            'h': 'h',
            'o': 'o',
            's': 's',
            '' : ''}

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

        self.net_write('# Ready\r\n'.encode('utf-8'))

        flag_continue = True
        while flag_continue:
            try:
                net_data = self.request.recv(512)
                self.logger.debug('net_data:\'%s\'', net_data)
            except KeyboardInterrupt:
                self.reboto_send_cmd('s')
                return
            
            except ConnectionResetError:
                self.reboto_send_cmd('s')
                return

            if len(net_data) == 0:
                self.robot_send_cmd('s')
                self.robot_send_cmd('')
                break

            try:
                for ch in net_data.decode('utf-8'):
                    self.net_write('\r\n'.encode('utf-8'))

                    if ord(ch) > 0x20:
                        if ch.isnumeric():
                            self.robot.send_cmd(ch)
                            continue

                        if not ch in self.cmd.keys():
                            self.robot.send_cmd('s')
                            continue
                        
                        self.robot.send_cmd('s')
                        self.robot.send_cmd('0')
                        self.robot.send_cmd(self.cmd[ch])
                        
                    else:
                        self.robot.send_cmd('s')
                        flag_continue = False
            except UnicodeDecodeError:
                pass

    def finish(self):
        self.logger.debug('')
        return super().finish()
    

class OttoPiServer(socketserver.TCPServer):
    def __init__(self, robot, port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('port=%d', port)

        self.robot = robot
        self.port  = port

        try:
            super().__init__(('', self.port), OttoPiHandler)
        except:
            return None

    def serve_forever(self):
        self.logger.debug('')
        super().serve_forever()

    def _del__(self):
        self.logger.debug('')

        if self.robot.is_alive():
            self.robot.send_cmd('')
            self.robot.join()
        self.logger.debug('done')
        
        
#####
class Sample:
    def __init__(self, port, pin1, pin2, pin3, pin4, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('port=%d, (pin1,pin2,pin3,pin4)=%s',
                          port, (pin1, pin2, pin3, pin4))

        self.port = port

        self.pi = pigpio.pi()
        self.mypi = True
        
        self.opc = OttoPiCtrl(self.pi, pin1, pin2, pin3, pin4,
                              debug=self.debug)
        self.server = OttoPiServer(self.opc, self.port, debug=self.debug)
        
    def main(self):
        self.logger.debug('')

        self.logger.debug('start robot')
        self.opc.start()
        time.sleep(2)

        self.logger.debug('start server')
        self.server.serve_forever()
        
    def end(self):
        self.logger.debug('')

        self.opc.send_cmd('')
        self.opc.join()
        if self.mypi:
            self.pi.stop()
            self.mypi = False
        self.logger.debug('done')
        
        
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('port', type=int, default=DEF_PORT)
@click.argument('pin1', type=int, default=4)
@click.argument('pin2', type=int, default=17)
@click.argument('pin3', type=int, default=27)
@click.argument('pin4', type=int, default=22)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, pin1, pin2, pin3, pin4, debug):
    logger = get_logger('', debug)
    logger.info('port=%d, pins:%d,%d,%d,%d', port, pin1, pin2, pin3, pin4)

    obj = Sample(port, pin1, pin2, pin3, pin4, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.end()

if __name__ == '__main__':
    main()

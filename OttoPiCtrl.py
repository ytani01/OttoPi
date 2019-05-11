#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
from OttoPiMotion import OttoPiMotion

import pigpio
import time
import queue, threading

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
DEF_PIN1 = 4
DEF_PIN2 = 17
DEF_PIN3 = 27
DEF_PIN4 = 22

#####
class OttoPiCtrl(threading.Thread):
    def __init__(self, pi=None,
                 pin1=DEF_PIN1, pin2=DEF_PIN2,
                 pin3=DEF_PIN3, pin4=DEF_PIN4,
                 debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi:  %s', str(pi))
        self.logger.debug('pin: %s', [pin1, pin2, pin3, pin4])

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   =  pigpio.pi()
            self.mypi = True
            
        self.op = OttoPiMotion(self.pi, pin1, pin2, pin3, pin4,
                               debug=logger.propagate and debug)

        self.cmd_func = {
            'f': {'func':self.op.forward,    'continuous':True},
            'b': {'func':self.op.backward,   'continuous': True},
            'r': {'func':self.op.turn_right, 'continuous': True},
            'l': {'func':self.op.turn_left,  'continuous': True},
            'R': {'func':self.op.side_right, 'continuous': True},
            'L': {'func':self.op.side_left,  'continuous': True},
            'h': {'func':self.op.happy,      'continuous': False},
            'o': {'func':self.op.ojigi,      'continuous': False},
            's': {'func':self.op.stop,       'continuous': False},
            'g': {'func':self.op.go,         'continuous': False},
            '' : {'func':None,               'continuous': False}}
        
        self.cmdq = queue.Queue()
        
        super().__init__(daemon=True)


    def __del__(self):
        self.logger.debug('')
        self.end()

    def end(self):
        self.logger.debug('')

        self.op.end()
        time.sleep(0.5)
        if self.mypi:
            self.pi.stop()
            self.mypi = False
        

    # cmd: numeric string or one char command
    def send_cmd(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        if cmd == '':
            self.cmdq.put(cmd)
            return

        if not cmd in self.cmd_func.keys():
            self.logger.warn('invalid cmd:%s: ignored', cmd)
            return
            
        self.op.stop()
        while not self.cmdq.empty():
            c = self.cmdq.get()
            self.logger.warn('%s: ignored', c)
        self.cmdq.put('g')
        self.cmdq.put(cmd)

    def recv_cmd(self):
        self.logger.debug('')
        cmd = self.cmdq.get()
        self.logger.debug('cmd=%s', cmd)
        return cmd

    def exec_cmd(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        if cmd == '':
            # finish
            return False
        
        if cmd not in self.cmd_func.keys():
            self.logger.error('\'%s\': no such commdnd', cmd)
            return True
        
        n = 1
        if self.cmd_func[cmd]['continuous']:
            n = 0
        self.logger.debug('n=%d', n)
        
        self.cmd_func[cmd]['func'](n=n)
        return True
            
    # Thread
    def run(self):
        self.logger.debug('')

        run_flag = True
        while run_flag:
            cmd = self.recv_cmd()
            self.logger.debug('cmd=\'%s\'', cmd)
            run_flag = self.exec_cmd(cmd)

        self.logger.debug('done')
            
        
#####
class Sample:
    def __init__(self, pin1, pin2, pin3, pin4, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('(pin1,pin2,pin3,pin4)=%s',
                          (pin1, pin2, pin3, pin4))

        self.pi = pigpio.pi()
        self.opc = OttoPiCtrl(self.pi, pin1, pin2, pin3, pin4, debug=debug)
        self.opc.start()

    def main(self):
        self.logger.debug('')

        self.opc.send_cmd('h')

        while True:
            cmdline = input()
            self.logger.info('cmdline=\'%s\'', cmdline)
            if cmdline == '':
                self.logger.info('Bye!')
                break

            self.opc.send_cmd(cmdline[0])
        
    def end(self):
        self.logger.debug('')

        self.opc.send_cmd('o')
        self.opc.send_cmd('')
        self.opc.join()
        self.logger.debug('done')
        
        
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin1', type=int, default=DEF_PIN1)
@click.argument('pin2', type=int, default=DEF_PIN2)
@click.argument('pin3', type=int, default=DEF_PIN3)
@click.argument('pin4', type=int, default=DEF_PIN4)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    logger = get_logger('', debug)
    logger.debug('pins: %d, %d, %d, %d', pin1, pin2, pin3, pin4)

    obj = Sample(pin1, pin2, pin3, pin4, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.end()

if __name__ == '__main__':
    main()

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
logger.propagate = True
def get_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l


#####
DEF_PIN1 = 17
DEF_PIN2 = 27
DEF_PIN3 = 22
DEF_PIN4 = 23

#####
class OttoPiCtrl(threading.Thread):
    CMD_STOP   = 'stop'
    CMD_RESUME = 'resume'
    CMD_END    = 'end'

    def __init__(self, pi=None, pin=(DEF_PIN1, DEF_PIN2, DEF_PIN3, DEF_PIN4),
                 debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi  = %s', str(pi))
        self.logger.debug('pin = %s', pin)

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   =  pigpio.pi()
            self.mypi = True
            
        self.op = OttoPiMotion(self.pi, pin, debug=logger.propagate and debug)

        self.cmd_func = {
            'forward':       {'func':self.op.forward,     'continuous': True},
            'backward':      {'func':self.op.backward,    'continuous': True},
            'turn_right':    {'func':self.op.turn_right,  'continuous': True},
            'turn_left':     {'func':self.op.turn_left,   'continuous': True},
            'slide_right':   {'func':self.op.slide_right, 'continuous': True},
            'slide_left':    {'func':self.op.slide_left,  'continuous': True},
            'happy':         {'func':self.op.happy,       'continuous': False},
            'ojigi':         {'func':self.op.ojigi,       'continuous': False},
            self.CMD_STOP:   {'func':self.op.stop,        'continuous': False},
            self.CMD_RESUME: {'func':self.op.resume,      'continuous': False},
            self.CMD_END :   {'func':None,                'continuous': False}}
        
        self.cmdq = queue.Queue()

        self.running = False
        
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
        

    def clear_cmdq(self):
        self.logger.info('')
        while not self.cmdq.empty():
            c = self.cmdq.get()
            self.logger.info('%s: ignored', c)

    # cmd: numeric string or one char command
    def send_cmd(self, cmd):
        self.logger.debug('cmd=\'%s\'', cmd)

        if not cmd in self.cmd_func.keys():
            self.logger.warn('invalid cmd:%s: ignored', cmd)
            return
            
        self.op.stop() # stop continuous motion (Don't self.op.go() immediately)
        self.clear_cmdq()
        self.cmdq.put(self.CMD_RESUME) 
        self.cmdq.put(cmd)

    def recv_cmd(self):
        self.logger.debug('')
        cmd = self.cmdq.get()
        self.logger.debug('cmd=\'%s\'', cmd)
        return cmd

    def exec_cmd(self, cmd):
        self.logger.debug('cmd=\'%s\'', cmd)

        if cmd not in self.cmd_func.keys():
            self.logger.error('\'%s\': no such commdnd', cmd)
            return True
        
        if cmd == self.CMD_END:
            # finish
            return False
        
        n = 1
        if self.cmd_func[cmd]['continuous']:
            n = 0
        self.logger.debug('n=%d', n)
        
        self.cmd_func[cmd]['func'](n=n)
        return True
            
    def is_running(self):
        return self.running   

    # Thread
    def run(self):
        self.logger.debug('')

        self.running = True
        while self.running:
            cmd = self.recv_cmd()
            self.logger.debug('cmd=\'%s\'', cmd)
            self.running = self.exec_cmd(cmd)
            self.logger.debug('running=%s', self.running)

        self.logger.debug('done(running=%s)', self.running)
            
        
#####
class Sample:
    def __init__(self, pin1, pin2, pin3, pin4, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('(pin1,pin2,pin3,pin4)=%s',
                          (pin1, pin2, pin3, pin4))

        self.pi = pigpio.pi()
        self.opc = OttoPiCtrl(self.pi, (pin1, pin2, pin3, pin4), debug=debug)
        self.opc.start()

    def main(self):
        self.logger.debug('')

        self.opc.send_cmd('happy')

        while True:
            cmdline = input()
            self.logger.info('cmdline=\'%s\'', cmdline)
            if cmdline == '':
                self.logger.info('Bye!')
                break

            self.opc.send_cmd(cmdline)
        
    def end(self):
        self.logger.debug('')

        self.opc.send_cmd('ojigi')
        time.sleep(3)
        self.opc.send_cmd(OttoPiCtrl.CMD_END)
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

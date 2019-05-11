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
            'f': {'func': self.op.forward, 'preemptive': False},
            'b': {'func': self.op.backward, 'preemptive': False},
            'r': {'func': self.op.turn_right, 'preemptive': False},
            'l': {'func': self.op.turn_left, 'preemptive': False},
            'R': {'func': self.op.side_right, 'preemptive': False},
            'L': {'func': self.op.side_left, 'preemptive': False},
            'h': {'func': self.op.happy, 'preemptive': False},
            'o': {'func': self.op.ojigi, 'preemptive': False},
            's': {'func': self.op.stop, 'preemptive': True},
            'g': {'func': self.op.go, 'preemptive': False},
            '' : {'func': None, 'preemptive': False}}

        self.cmdq = queue.Queue()
        self.cmd_n = 1
        
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
        

    def send_cmd(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        if cmd.isnumeric():
            self.cmdq.put(cmd)
            return

        if not cmd in self.cmd_func.keys():
            self.logger.warn('invalid cmd:%s: ignored', cmd)
            return
            
        if not self.cmd_func[cmd]['preemptive']:
            self.cmdq.put(cmd)
            return
        
        # preemptive command
        self.logger.warn('cmd:%s is preemptive', cmd)
        while not self.cmdq.empty():
            c = self.cmdq.get()
            self.logger.warn('%s: ignored', c)
        self.exec_cmd1(cmd)
        self.cmdq.put('g')


    def recv_cmd(self):
        self.logger.debug('')
        cmd = self.cmdq.get()
        self.logger.debug('cmd=%s', cmd)
        return cmd

    def cmd_empty(self):
        self.logger.debug('')
        ret = self.cmdq.empty()
        self.logger.debug('ret=%s', ret)
        return ret

    def exec_cmd(self, cmds):
        self.logger.debug('cmds=%s', cmds)

        ret = True

        while cmds != []:
            cmd = cmds.pop(0)
            self.logger.debug('cmd=\'%s\', cmds=%s', cmd, cmds)

            if cmd.isnumeric():
                self.cmd_n = int(cmd)
                self.logger.debug('cmd_n=%d', self.cmd_n)
                continue

            ret = self.exec_cmd1(cmd, self.cmd_n)
            self.cmd_n = 1
            if ret == False:
                break

        self.logger.debug('ret=%s', ret)
        return ret

            
    def exec_cmd1(self, cmd, n=1):
        self.logger.debug('cmd=\'%s\'', cmd)
        
        if cmd == '':
            return False

        if cmd not in self.cmd_func.keys():
            self.logger.error('\'%s\': no such command', cmd)
            return True
        
        self.logger.debug('func=%s, n=%d', self.cmd_func[cmd], n)
        self.cmd_func[cmd]['func'](n=n)
        #time.sleep(2)
        return True
        

    # Thread
    def run(self):
        self.logger.debug('')

        run_flag = True
        while run_flag:
            cmds = []
            cmds.append(self.recv_cmd())
            self.logger.debug('cmds = %s', cmds)
            
            while not self.cmd_empty():
                cmds.append(self.recv_cmd())
                self.logger.debug('cmds = %s', cmds)

            run_flag = self.exec_cmd(cmds)

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
            self.logger.info('cmdline=%s', cmdline)
            if cmdline == '':
                self.opc.send_cmd('s')
                break

            if cmdline.isnumeric():
                self.opc.send_cmd(cmdline)
                continue
            
            if len(cmdline) == 1 and not cmdline[0].isnumeric():
                self.opc.send_cmd('s')
                self.opc.send_cmd('0')
                self.opc.send_cmd(cmdline)
                continue
            
            while cmdline != '':
                cmd = cmdline[0]
                cmdline = cmdline[1:]
                self.opc.send_cmd(cmd)
        
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

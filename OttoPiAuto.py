#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

from OttoPiCtrl import OttoPiCtrl
import VL53L0X
import pigpio
import time
import random
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
class OttoPiAuto(threading.Thread):
    CMD_AUTO = 'auto'
    ARG_ON   = 'on'
    ARG_OFF  = 'off'
    ARG_END  = 'end'

    D_TOO_NEAR    = 250
    D_NEAR        = 400
    D_FAR         = 8000
    
    STAT_NONE     = ''
    STAT_TOO_NEAR = 'too near'
    STAT_NEAR     = 'near'
    STAT_FAR      = 'far'

    def __init__(self, ottopi_ctrl=None, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('')

        self.my_opc = False
        self.op_ctrl = ottopi_ctrl
        if ottopi_ctrl == None:
            self.myopc = True
            self.op_ctrl = OttoPiCtrl(None, debug=self.debug)
            self.op_ctrl.start()

        self.tof = VL53L0X.VL53L0X()
        self.tof.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)
        #self.tof_timing = self.tof.get_timing()
        self.d = 0

        self.cmdq = queue.Queue()

        self.running = True

        self.prev_stat = self.STAT_NONE
        self.stat      = self.STAT_NONE

        super().__init__(daemon=True)

    def __del__(self):
        self.logger.debug('')

    def end(self):
        self.logger.debug('')
        self.running = False

        self.op_ctrl.send_cmd(OttoPiCtrl.CMD_STOP)
        
        self.tof.stop_ranging()

        if self.my_opc:
            self.op_ctrl.end()

    def send_cmd(self, cmdline):
        self.logger.debug('cmdline=\'%s\'', cmdline)

        self.cmdq.put(cmdline)

    def recv_cmd(self, timeout=1):
        self.logger.debug('')
        try:
            cmdline = self.cmdq.get(timeout=timeout)
        except queue.Empty:
            cmdline = ''
        self.logger.debug('cmdline=\'%s\'', cmdline)
        return cmdline

    def exec_cmd(self, cmdline):
        self.logger.debug('cmdline=\'%s\'', cmdline)

        cmd = cmdline.split()
        self.logger.debug('cmd=%s', cmd)

        if len(cmd) == 0:
            (cmd_name, cmd_arg) = ('NULL', '')
        elif len(cmd) == 1:
            (cmd_name, cmd_arg) = (cmd[0], '')
        else:
            (cmd_name, cmd_arg) = (cmd[0], cmd[1])
        self.logger.debug('cmd_name=\'%s\', cmd_arg=\'%s\'', cmd_name, cmd_arg)

        if cmd_name != self.CMD_AUTO:
            self.logger.error('\'%s\': no such command .. ignore', cmd_name)
            return True
        

    def get_distance(self):
        self.d = self.tof.get_distance()
        return self.d

    def run(self):
        self.logger.debug('')

        while self.running:
            self.get_distance()
            self.logger.debug('d = %smm', '{:,}'.format(self.d))
            self.prev_stat = self.stat
            if self.d <= self.D_TOO_NEAR:
                self.stat = self.STAT_NEAR
                if self.prev_stat != self.STAT_NEAR:
                    self.op_ctrl.send_cmd('happy')
                else:
                    self.op_ctrl.send_cmd('backward')
                time.sleep(2)
            elif self.d <= self.D_NEAR:
                self.stat = self.STAT_NEAR
                if self.prev_stat != self.STAT_NEAR:
                    if random.random() < 0.5:
                        self.op_ctrl.send_cmd('slide_right')
                    else:
                        self.op_ctrl.send_cmd('slide_left')
                else:
                    if random.random() < 0.5:
                        self.op_ctrl.send_cmd('turn_right')
                    else:
                        self.op_ctrl.send_cmd('turn_left')
                time.sleep(2)
            elif self.d >= self.D_FAR:
                self.stat = self.STAT_FAR
                if self.prev_stat == self.STAT_NEAR:
                    self.op_ctrl.send_cmd('forward')
            else:
                self.stat = self.STAT_NONE
                if self.prev_stat == self.STAT_NEAR:
                    self.op_ctrl.send_cmd('forward')
            self.logger.debug('stat=%s', self.stat)

            cmdline = self.recv_cmd()
            self.logger.debug('cmdline=\'%s\'', cmdline)
            if cmdline != '':
                self.exec_cmd(cmdline)
                
        self.logger.debug('done(running=%s)', self.running)


#####
class Sample:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('')

        self.pi = pigpio.pi()

        self.op_ctrl = OttoPiCtrl(self.pi, debug=self.debug)
        self.op_ctrl.start()

        self.op_auto = OttoPiAuto(self.op_ctrl, debug=self.debug)
        self.op_auto.start()

        self.running = True

    def main(self):
        self.logger.debug('')

        while self.running:
            cmdline = input().split()
            self.logger.debug('cmdline = %s', cmdline)

            if len(cmdline) == 0:
                self.running = False
                break

            if cmdline[0] == OttoPiAuto.CMD_AUTO:
                self.op_auto.send_cmd(' '.join(cmdline))
            elif self.op_ctrl.is_valid_cmd(cmdline[0]):
                self.op_ctrl.send_cmd(' '.join(cmdline))
            else:
                self.logger.debug('invalid command:%s', cmdline[0])

                
        self.logger.debug('done(running=%s)', self.running)

    def end(self):
        self.logger.debug('')

        self.op_auto.end()
        self.op_auto.join()
        self.logger.debug('OttoPiAuto thread: joined')

        self.op_ctrl.send_cmd(OttoPiCtrl.CMD_STOP)
        self.op_ctrl.end()
        self.op_ctrl.join()
        self.logger.debug('OttoPiCtrl thread: joined')

        self.pi.stop()
        self.logger.debug('done')

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = get_logger('', debug)

    obj = Sample(debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()
    
        

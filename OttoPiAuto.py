#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
ロボットの自動運転

距離センサーで障害物からの距離を認識し、
OttoPiCtrlを利用して、ロボットを自動運転する。

send()で、自動運転のON/OFFを制御できる。

OttoPiAuto -- ロボットの自動運転 (自動運転スレッド)
 |
 +- OttoPiCtrl -- コマンド制御 (動作実行スレッド)
     |
     +- OttoPiMotion -- 動作定義
         |
         +- PiServo -- 複数サーボの同期制御
         +- OttoPiConfig -- 設定ファイルの読み込み・保存

'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from OttoPiCtrl import OttoPiCtrl
import VL53L0X as VL53L0X
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
    CMD_ON   = 'on'
    CMD_OFF  = 'off'
    CMD_END  = 'end'

    DEF_RECV_TIMEOUT = 0.5 # sec

    D_TOO_NEAR    = 250
    D_NEAR        = 400
    D_FAR         = 8000
    
    STAT_NONE     = ''
    STAT_TOO_NEAR = 'too near'
    STAT_NEAR     = 'near'
    STAT_FAR      = 'far'

    def __init__(self, robot_ctrl=None, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('')

        self.cmd_func = {self.CMD_ON:  self.cmd_on,
                         self.CMD_OFF: self.cmd_off,
                         self.CMD_END: self.cmd_end}

        self.my_robot_ctrl = False
        self.robot_ctrl = robot_ctrl
        if self.robot_ctrl == None:
            self.my_robot_ctrl = True
            self.robot_ctrl = OttoPiCtrl(None, debug=self.debug)
            self.robot_ctrl.start()

        self.tof = VL53L0X.VL53L0X()
        self.tof.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)
        #self.tof_timing = self.tof.get_timing()
        self.d = 0

        self.cmdq = queue.Queue()

        self.alive = True
        self.on    = False

        self.prev_stat = self.STAT_NONE
        self.stat      = self.STAT_NONE

        super().__init__(daemon=True)

    def __del__(self):
        self.logger.debug('')

    def end(self):
        self.logger.debug('')
        self.alive = False

        self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)
        
        self.tof.stop_ranging()

        if self.my_robot_ctrl:
            self.robot_ctrl.end()

        self.join()
        self.logger.debug('done')


    def cmd_on(self):
        self.logger.debug('')
        self.robot_ctrl.send('forward')
        self.on = True

    def cmd_off(self):
        self.logger.debug('')
        self.robot_ctrl.send('stop')
        self.on = False

    def cmd_end(self):
        self.logger.debug('')
        self.cmd_off()
        self.alive = False

    def is_alive(self):
        self.logger.debug('alive=%s', self.alive)
        return self.alive

    def send(self, cmd):
        self.logger.debug('cmd=\'%s\'', cmd)
        self.cmdq.put(cmd)

    def recv(self, timeout=DEF_RECV_TIMEOUT):
        self.logger.debug('timeout=%.1f', timeout)
        try:
            cmd = self.cmdq.get(timeout=timeout)
        except queue.Empty:
            cmd = ''
        self.logger.debug('cmd=\'%s\'', cmd)
        return cmd

    def get_distance(self):
        return self.tof.get_distance()

    def run(self):
        self.logger.debug('')

        while self.alive:
            cmd = self.recv()
            if cmd != '':
                self.logger.info('cmd=\'%s\'', cmd)
                if cmd in self.cmd_func.keys():
                    self.cmd_func[cmd]()
                else:
                    self.logger.error('%s: invalid command .. ignore', cmd)

            if not self.on:
                continue
                
            d = self.get_distance()
            self.logger.info('d = %smm', '{:,}'.format(d))

            self.prev_stat = self.stat

            if d <= self.D_TOO_NEAR:
                self.logger.warn('TOO_NEAR')
                self.stat = self.STAT_NEAR
                if self.prev_stat != self.STAT_NEAR:
                    self.robot_ctrl.send('happy')
                else:
                    self.robot_ctrl.send('backward')
                time.sleep(2)

            elif d <= self.D_NEAR:
                self.logger.warn('NEAR')
                self.stat = self.STAT_NEAR
                if self.prev_stat != self.STAT_NEAR:
                    if random.random() < 0.5:
                        self.robot_ctrl.send('slide_right')
                    else:
                        self.robot_ctrl.send('slide_left')
                else:
                    if random.random() < 0.5:
                        self.robot_ctrl.send('turn_right')
                    else:
                        self.robot_ctrl.send('turn_left')
                time.sleep(2)

            elif d >= self.D_FAR:
                self.logger.info('FAR')
                self.stat = self.STAT_FAR
                if self.prev_stat == self.STAT_NEAR:
                    self.robot_ctrl.send('forward')

            else:
                self.stat = self.STAT_NONE
                if self.prev_stat == self.STAT_NEAR:
                    self.robot_ctrl.send('forward')

            self.logger.debug('stat=%s', self.stat)

        self.logger.info('done(alive=%s)', self.alive)


#####
class Sample:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('')

        self.pi = pigpio.pi()

        self.robot_ctrl = OttoPiCtrl(self.pi, debug=self.debug)
        self.robot_ctrl.start()

        self.robot_auto = OttoPiAuto(self.robot_ctrl, debug=self.debug)
        self.robot_auto.start()

        self.alive = True

    def main(self):
        self.logger.debug('')

        while self.alive:
            cmdline = input()
            self.logger.debug('cmdline = %s', cmdline)

            self.robot_auto.send(cmdline)
            time.sleep(1)

            if not self.robot_auto.is_alive():
                self.alive = False
                
        self.logger.debug('done(alive=%s)', self.alive)

    def end(self):
        self.logger.debug('')

        self.robot_auto.end()
        self.logger.info('robot_auto thread: end')

        self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)
        self.robot_ctrl.end()
        self.logger.info('robot_ctrl thread: end')

        self.pi.stop()
        self.logger.info('done')

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = get_logger('', debug)

    app = Sample(debug=debug)
    try:
        app.main()
    finally:
        logger.info('finally')
        app.end()

if __name__ == '__main__':
    main()
    
        
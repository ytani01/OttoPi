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

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
class OttoPiAuto(threading.Thread):
    CMD_ON    = 'on'
    CMD_OFF   = 'off'
    CMD_READY = 'ready'
    CMD_END   = 'end'

    DEF_RECV_TIMEOUT = 0.5 # sec

    D_TOUCH       = 40
    D_TOO_NEAR    = 200
    D_NEAR        = 400
    D_FAR         = 8000
    D_READY_MIN   = D_TOUCH + 10
    D_READY_MAX   = 120
    D_ON_MIN      = 300
    
    STAT_NONE     = 'none'
    STAT_YELLOW   = 'yellow'
    STAT_TOO_NEAR = 'too_near'
    STAT_NEAR     = 'near'
    STAT_FAR      = 'far'
    STAT_READY    = 'ready'

    TOUCH_COUNT_COMMIT = 2
    READY_COUNT_COMMIT = 2

    def __init__(self, robot_ctrl=None, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, self.debug)
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

        self.prev_stat   = self.STAT_NONE
        self.stat        = self.STAT_NONE
        self.prev_rl     = ""
        self.touch_count = 0
        self.ready_count = 0

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
        self.touch_count = 0
        self.stat = self.STAT_NONE

    def cmd_off(self):
        self.logger.debug('')
        self.robot_ctrl.send('stop')
        self.on = False
        self.ready_count = 0
        self.stat = self.STAT_NONE

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

            d = self.get_distance()
            self.logger.info('d = %smm', '{:,}'.format(d))
            if d < 0:
                continue

            if not self.on:
                if self.ready_count > 0:
                    self.logger.info('ready_count=%d', self.ready_count)

                if self.ready_count < self.READY_COUNT_COMMIT:
                    if d >= self.D_READY_MIN and d <= self.D_READY_MAX:
                        self.ready_count += 1
                        self.robot_ctrl.send('happy')
                        time.sleep(1)
                    else:
                        self.ready_count = 0

                else: # self.ready_count >= self.READY_COUNT_COMMIT
                    self.cmd_on()
                        
                continue
                
            self.prev_stat = self.stat

            if d <= self.D_TOUCH:
                self.logger.warn('touched(<= %d)', self.D_TOUCH)
                self.robot_ctrl.send('suprised')
                time.sleep(2)

                if self.touch_count < self.TOUCH_COUNT_COMMIT:
                    self.touch_count += 1
                    self.logger.info('touch_count=%d', self.touch_count)
                    if self.touch_count >= self.TOUCH_COUNT_COMMIT:
                        self.logger.warn('STOP!')
                        self.cmd_off()
                        self.robot_ctrl.send('suprised')
                        time.sleep(3)
                    else:
                        self.robot_ctrl.send('forward')
                    continue
            else:
                self.touch_count = 0

            if d <= self.D_TOO_NEAR:
                self.logger.warn('TOO_NEAR(<= %d)', self.D_TOO_NEAR)
                self.stat = self.STAT_NEAR

                if self.prev_stat != self.STAT_NEAR:
                    self.robot_ctrl.send('suprised')
                    time.sleep(1)
                else:
                    self.robot_ctrl.send('backward')
                    time.sleep(2)

            elif d <= self.D_NEAR:
                self.logger.warn('NEAR(<= %d)', self.D_NEAR)
                self.stat = self.STAT_NEAR
                if self.prev_stat != self.STAT_NEAR:
                    if random.random() < 0.5:
                        self.prev_rl = "right"
                        self.robot_ctrl.send('slide_right')
                    else:
                        self.prev_rl = "left"
                        self.robot_ctrl.send('slide_left')
                else:
                    if self.prev_rl == "right":
                        self.robot_ctrl.send('turn_right')
                    else:
                        self.robot_ctrl.send('turn_left')
                time.sleep(1.5)

            elif d >= self.D_FAR:
                self.logger.info('FAR(>= %d)', self.D_FAR)
                self.stat = self.STAT_FAR
                if self.prev_stat in [self.STAT_NEAR, self.STAT_YELLOW]:
                    self.robot_ctrl.send('forward')

            else:
                if self.prev_stat == self.STAT_NEAR:
                    self.stat = self.STAT_NONE
                    if d <= self.D_NEAR + 200:
                        self.stat = self.STAT_YELLOW
                        self.logger.info('stat: %s', self.stat)
                        self.robot_ctrl.send('suriashi_fwd')
                    else:
                        self.logger.info('stat: %s', self.stat)
                        self.robot_ctrl.send('forward')

            self.touch_count = 0
            self.logger.debug('stat=%s', self.stat)

        self.logger.info('done(alive=%s)', self.alive)


#####
class Sample:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
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
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = my_logger.get_logger(__name__, debug)

    app = Sample(debug=debug)
    try:
        app.main()
    finally:
        logger.info('finally')
        app.end()

if __name__ == '__main__':
    main()

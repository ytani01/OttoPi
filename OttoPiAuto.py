#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
ロボットの自動運転

距離センサーで障害物からの距離を認識し、
OttoPiCtrlを利用して、ロボットを自動運転する。

send()で、自動運転のON/OFFを制御できる。

------------------------------------------------------------
OttoPiAuto -- ロボットの自動運転 (自動運転スレッド)
 |
 +- OttoPiCtrl -- コマンド制御 (動作実行スレッド)
     |
     +- OttoPiMotion -- 動作定義
         |
         +- PiServo -- 複数サーボの同期制御
         +- OttoPiConfig -- 設定ファイルの読み込み・保存
------------------------------------------------------------
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020'

import time
import random
import queue
import threading
import pigpio
import VL53L0X as VL53L0X
from OttoPiCtrl import OttoPiCtrl
from MyLogger import get_logger


class OttoPiAuto(threading.Thread):
    """ auto pilot """
    CMD_NULL  = 'null'
    CMD_ON    = 'on'
    CMD_OFF   = 'off'
    CMD_ENABLE = 'enable'
    CMD_DISABLE = 'disable'
    CMD_READY = 'ready'
    CMD_END   = 'end'

    DEF_RECV_TIMEOUT = 0.2  # sec

    D_TOUCH       = 40
    D_TOO_NEAR    = 180
    D_NEAR        = 250
    D_FAR         = 8000
    D_READY_MIN   = D_TOUCH + 10
    D_READY_MAX   = 120

    STAT_NONE     = 'none'
    STAT_YELLOW   = 'yellow'
    STAT_TOO_NEAR = 'too_near'
    STAT_NEAR     = 'near'
    STAT_FAR      = 'far'
    STAT_READY    = 'ready'

    TOUCH_COUNT_COMMIT = 3
    READY_COUNT_COMMIT = 2

    def __init__(self, robot_ctrl=None, debug=False):
        """ init """
        self.dbg = debug
        self._log = get_logger(__class__.__name__, self.dbg)
        self._log.debug('')

        self.cmd_func = {self.CMD_NULL: self.cmd_null,
                         self.CMD_ON:  self.cmd_on,
                         self.CMD_OFF: self.cmd_off,
                         self.CMD_ENABLE:  self.cmd_enable,
                         self.CMD_DISABLE: self.cmd_disable,
                         self.CMD_END: self.cmd_end}

        self.my_robot_ctrl = False
        self.robot_ctrl = robot_ctrl
        if self.robot_ctrl is None:
            self.my_robot_ctrl = True
            self.robot_ctrl = OttoPiCtrl(None, debug=self.dbg)
            self.robot_ctrl.start()

        self.tof = VL53L0X.VL53L0X()
        # self.tof.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)
        self.tof.start_ranging(VL53L0X.VL53L0X_BETTER_ACCURACY_MODE)
        self.tof_timing = self.tof.get_timing()
        self._log.info('tof_timing = %.02f ms', self.tof_timing / 1000)
        self.d = 0

        self.cmdq = queue.Queue()

        self.active = True
        self.on    = False
        self.enable = False

        self.prev_stat   = self.STAT_NONE
        self.stat        = self.STAT_NONE
        self.prev_rl     = ""
        self.touch_count = 0
        self.ready_count = 0

        self.distance = self.D_FAR

        super().__init__(daemon=True)

    def __del__(self):
        """ del """
        self._log.debug('')

    def end(self):
        """ end """
        self._log.debug('')
        self.active = False

        self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)

        if self.my_robot_ctrl:
            self.robot_ctrl.end()

        self.join()

        self.tof.stop_ranging()

        self._log.debug('done')

    def cmd_null(self):
        """ do nothing (to get distance) """
        self._log.debug('')

    def cmd_on(self):
        """ cmd on """
        self._log.debug('')
        if not self.enable:
            self._log.warning('enable=%s .. ignored', self.enable)
            return
        self.robot_ctrl.send('forward')
        self.on = True
        self.touch_count = 0
        self.stat = self.STAT_NONE

    def cmd_off(self):
        """ cmd off """
        self._log.debug('')
        self.robot_ctrl.send('stop')
        self.on = False
        self.ready_count = 0
        self.stat = self.STAT_NONE

    def cmd_enable(self):
        """ cmd enable """
        self._log.debug('')
        self.enable = True
        self._log.debug('enable=%s', self.enable)
        self.ready_count = 0
        self.stat = self.STAT_NONE

    def cmd_disable(self):
        """ cmd disable """
        self._log.debug('')
        self.cmd_off()
        self.enable = False
        self._log.debug('enable=%s', self.enable)
        self.ready_count = 0
        self.stat = self.STAT_NONE

    def cmd_end(self):
        """ cmd end """
        self._log.debug('')
        self.cmd_off()
        self.active = False

    def is_active(self):
        """ """
        self._log.debug('active=%s', self.active)
        return self.active

    def send(self, cmd):
        """ """
        self._log.debug('cmd=\'%s\'', cmd)
        self.cmdq.put(cmd)
        d = self.get_distance()
        self._log.debug('d=%smm', '{:,}'.format(d))
        return d

    def recv(self, timeout=DEF_RECV_TIMEOUT):
        """ """
        self._log.debug('timeout=%.1f', timeout)
        try:
            cmd = self.cmdq.get(timeout=timeout)
        except queue.Empty:
            cmd = ''
        else:
            self._log.debug('cmd=\'%s\'', cmd)

        return cmd

    def get_distance(self):
        """ """
        self.distance = self.tof.get_distance()
        if self.distance == 0:
            # ???
            self.distance = self.D_FAR
            self._log.warning('Crrection: distance = %smm',
                              '{:,}'.format(self.distance))

        return self.distance

    def run(self):
        """ run """
        self._log.debug('')

        while self.active:
            cmd = self.recv()
            if cmd != '':
                self._log.debug('cmd=%a', cmd)
                cmdline = cmd.split()
                cmd_name = cmdline[0]
                self._log.info('cmd_name=%a', cmd_name)
                if cmd_name in self.cmd_func.keys():
                    self.cmd_func[cmd_name]()
                else:
                    self._log.error('%s: invalid command .. ignore', cmd)

            d = self.get_distance()
            # self._log.debug('d = %smm', '{:,}'.format(d))
            if d < 0:
                continue

            if not self.enable:
                continue

            if not self.on:
                if self.ready_count > 0:
                    self._log.info('ready_count=%d/%d',
                                   self.ready_count, self.READY_COUNT_COMMIT)

                if self.ready_count < self.READY_COUNT_COMMIT:
                    if d >= self.D_READY_MIN and d <= self.D_READY_MAX:
                        self._log.warn('%dmm <= %dmm <= %dmm',
                                       self.D_READY_MIN,
                                       d,
                                       self.D_READY_MAX)
                        self.ready_count += 1
                        self.robot_ctrl.send('happy')
                        time.sleep(1)
                    else:
                        self.ready_count = 0

                else:  # self.ready_count >= self.READY_COUNT_COMMIT
                    self.cmd_on()

                continue

            self.prev_stat = self.stat

            if d <= self.D_TOUCH:
                self._log.warn('touched(%dmm <= %dmm)', d, self.D_TOUCH)
                self.robot_ctrl.send('suprised')
                time.sleep(1)

                if self.touch_count < self.TOUCH_COUNT_COMMIT:
                    self.touch_count += 1
                    self._log.info('touch_count=%d', self.touch_count)
                    if self.touch_count >= self.TOUCH_COUNT_COMMIT:
                        self._log.warn('STOP!')
                        self.cmd_off()
                        # self.robot_ctrl.send('suprised')
                        time.sleep(3)
                    else:
                        self.robot_ctrl.send('backward')
                    continue
            else:
                self.touch_count = 0

            if d <= self.D_TOO_NEAR:
                self._log.warn('TOO_NEAR(%dmm <= %dmm)', d, self.D_TOO_NEAR)
                self.stat = self.STAT_NEAR

                if self.prev_stat != self.STAT_NEAR:
                    self.robot_ctrl.send('suprised')
                    time.sleep(1)
                else:
                    self.robot_ctrl.send('backward')
                    time.sleep(2)

            elif d <= self.D_NEAR:
                self._log.warn('NEAR(%dmm <= %dmm)', d, self.D_NEAR)
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
                    time.sleep(1)
                time.sleep(1.5)

            elif d >= self.D_FAR:
                self._log.info('FAR(%dmm >= %dmm)', d, self.D_FAR)
                self.stat = self.STAT_FAR
                if self.prev_stat in [self.STAT_NEAR, self.STAT_YELLOW]:
                    self.robot_ctrl.send('forward')

            else:
                if self.prev_stat == self.STAT_NEAR:
                    self.stat = self.STAT_NONE
                    if d <= self.D_NEAR + 50:
                        self.stat = self.STAT_YELLOW
                        self._log.info('stat: %s', self.stat)
                        self.robot_ctrl.send('suriashi_fwd')
                    else:
                        self._log.info('stat: %s', self.stat)
                        self.robot_ctrl.send('forward')

            self.touch_count = 0
            self._log.debug('stat=%s', self.stat)

        self._log.info('done(active=%s)', self.active)


class OttoPiAutoApp:
    """ OttoPiAutoApp """
    def __init__(self, debug=False):
        """ init """
        self.dbg = debug
        self._log = get_logger(__class__.__name__, debug)
        self._log.debug('')

        self.pi = pigpio.pi()

        self.robot_ctrl = OttoPiCtrl(self.pi, debug=self.dbg)
        self.robot_ctrl.start()

        self.robot_auto = OttoPiAuto(self.robot_ctrl, debug=self.dbg)
        self.robot_auto.start()

        self.active = True

    def main(self):
        """ main """
        self._log.debug('')

        while self.active:
            cmdline = input()
            self._log.debug('cmdline = %s', cmdline)

            self.robot_auto.send(cmdline)
            time.sleep(1)

            if not self.robot_auto.is_active():
                self.active = False

        self._log.debug('done(active=%s)', self.active)

    def end(self):
        """ end """
        self._log.debug('')

        self.robot_auto.end()
        self._log.info('robot_auto thread: end')

        self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)
        self.robot_ctrl.end()
        self._log.info('robot_ctrl thread: end')

        self.pi.stop()
        self._log.info('done')


import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = get_logger(__name__, debug)

    app = OttoPiAutoApp(debug=debug)
    try:
        app.main()
    finally:
        logger.info('finally')
        app.end()


if __name__ == '__main__':
    main()

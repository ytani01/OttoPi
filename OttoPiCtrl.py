#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
コマンド(文字列)を受信して、OttoPiMotionで定義されている動きを起動する。

send()にコマンド(文字列)を指定する。
実行(モーター制御)は独立したスレッドで行う。
このとき、現在の動作を「キリのいいところで」中断し、割り込む。


OttoPiCtrl -- コマンド制御 (動作実行スレッド)
 |
 +- OttoPiMotion -- 動作定義
     |
     +- PiServo -- 複数サーボの同期制御
     +- OttoPiConfig -- 設定ファイルの読み込み・保存

'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from OttoPiMotion import OttoPiMotion

import pigpio
import time
import queue
import threading

from MyLogger import get_logger


#####
class OttoPiCtrl(threading.Thread):
    CMD_HOME   = 'home'
    CMD_STOP   = 'stop'
    CMD_RESUME = 'resume'
    CMD_HELP   = 'help'
    CMD_END    = 'end'

    def __init__(self, pi=None, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi  = %s', str(pi))

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   = pigpio.pi()
            self.mypi = True
        self.logger.debug('mypi = %s', self.mypi)

        # self.opm = OttoPiMotion(self.pi, debug=logger.propagate and debug)
        self.opm = OttoPiMotion(self.pi, debug=self.debug)

        # コマンド名とモーション関数の対応づけ
        self.cmd_func = {
            # モーション
            'forward':        {'func': self.opm.forward,        'loop': True},
            'right_forward':  {'func': self.opm.right_forward,  'loop': True},
            'left_forward':   {'func': self.opm.left_forward,   'loop': True},

            'backward':       {'func': self.opm.backward,       'loop': True},
            'right_backward': {'func': self.opm.right_backward, 'loop': True},
            'left_backward':  {'func': self.opm.left_backward,  'loop': True},
            'suriashi_fwd':   {'func': self.opm.suriashi,       'loop': True},

            'turn_right':     {'func': self.opm.turn_right,     'loop': True},
            'turn_left':      {'func': self.opm.turn_left,      'loop': True},
            'slide_right':    {'func': self.opm.slide_right,    'loop': True},
            'slide_left':     {'func': self.opm.slide_left,     'loop': True},
            'happy':          {'func': self.opm.happy,          'loop': False},
            'hi':             {'func': self.opm.hi,             'loop': False},
            'surprised':      {'func': self.opm.surprised,      'loop': False},
            'ojigi':          {'func': self.opm.ojigi,          'loop': False},
            'ojigi2':         {'func': self.opm.ojigi2,         'loop': False},

            # サーボモーター個別操作
            'move_up0':       {'func': self.opm.move_up0,       'loop': False},
            'move_down0':     {'func': self.opm.move_down0,     'loop': False},
            'move_up1':       {'func': self.opm.move_up1,       'loop': False},
            'move_down1':     {'func': self.opm.move_down1,     'loop': False},
            'move_up2':       {'func': self.opm.move_up2,       'loop': False},
            'move_down2':     {'func': self.opm.move_down2,     'loop': False},
            'move_up3':       {'func': self.opm.move_up3,       'loop': False},
            'move_down3':     {'func': self.opm.move_down3,     'loop': False},

            # ホームポジションの調整
            'home_up0':       {'func': self.opm.home_up0,       'loop': False},
            'home_down0':     {'func': self.opm.home_down0,     'loop': False},
            'home_up1':       {'func': self.opm.home_up1,       'loop': False},
            'home_down1':     {'func': self.opm.home_down1,     'loop': False},
            'home_up2':       {'func': self.opm.home_up2,       'loop': False},
            'home_down2':     {'func': self.opm.home_down2,     'loop': False},
            'home_up3':       {'func': self.opm.home_up3,       'loop': False},
            'home_down3':     {'func': self.opm.home_down3,     'loop': False},

            # 基本コマンド
            self.CMD_HOME:    {'func': self.opm.home,           'loop': False},
            self.CMD_STOP:    {'func': self.opm.stop,           'loop': False},
            self.CMD_RESUME:  {'func': self.opm.resume,         'loop': False},
            self.CMD_HELP:    {'func': self.help,               'loop': False},
            self.CMD_END :    {'func': None,                    'loop': False}}

        self.cmdq = queue.Queue()

        self.alive = False

        super().__init__(daemon=True)

    def __del__(self):
        self.logger.debug('')

    def end(self):
        self.logger.debug('')

        self.send(self.CMD_END)
        self.join()

        self.opm.end()
        time.sleep(0.5)
        if self.mypi:
            self.pi.stop()
            self.mypi = False

        self.logger.debug('done')

    def clear_cmdq(self):
        self.logger.debug('')
        while not self.cmdq.empty():
            c = self.cmdq.get()
            self.logger.debug('%s: ignored', c)

    def is_valid_cmd(self, cmd=''):
        self.logger.debug('cmd = \'%s\'', cmd)
        return cmd in self.cmd_func.keys()

    # 連続実行中断
    def interrupt_loop(self):
        self.logger.warn('')
        self.opm.stop()

    # cmd: "[コマンド名]"
    def send(self, cmd, doInterrupt=True):
        self.logger.info('cmd=\'%s\' doInterrupt=%s', cmd, doInterrupt)

        cmdline = cmd.split()
        self.logger.info('cmdline=%s', cmdline)

        if doInterrupt:
            self.interrupt_loop()
            self.clear_cmdq()

        self.cmdq.put(self.CMD_RESUME)
        self.cmdq.put(cmd)

    def recv(self):
        self.logger.debug('')
        cmd = self.cmdq.get()
        self.logger.debug('cmd=\'%s\'', cmd)
        return cmd

    def exec_cmd(self, cmd):
        self.logger.debug('cmd=\'%s\'', cmd)

        # コマンドライン分割
        cmdline = cmd.split()
        self.logger.debug('cmdline=%s', cmdline)

        # cmd_name: コマンド名
        # cmd_n:    実行回数
        if len(cmdline) == 0:
            (cmd_name, cmd_n) = ('NULL', '')
        elif len(cmdline) == 1:
            (cmd_name, cmd_n) = (cmdline[0], '')
        else:
            (cmd_name, cmd_n) = (cmdline[0], cmdline[1])
        self.logger.info('cmd_name,cmd_n=\'%s\',\'%s\'', cmd_name, cmd_n)

        if not self.is_valid_cmd(cmd_name):
            self.logger.error('\'%s\': no such command .. ignore', cmd_name)
            return True

        # 終了確認
        if cmd_name == self.CMD_END:
            self.logger.debug('finish')
            return False

        # cmd_n -> n: 実行回数(0=連続実行)
        n = 1
        if cmd_n.isnumeric():
            n = int(cmd_n)
        elif self.cmd_func[cmd_name]['loop']:
            n = 0  # loop move
        self.logger.debug('n=%d', n)

        # コマンド実行
        self.cmd_func[cmd_name]['func'](n)
        return True

    def help(self, n=1):
        cmd_list = [cmd for cmd in self.cmd_func]
        for cmd in sorted(cmd_list):
            print('%s' % cmd)
        return

    def is_alive(self):
        return self.alive

    # Thread
    def run(self):
        self.logger.debug('')

        self.alive = True
        while self.alive:
            # コマンドライン受信
            cmd = self.recv()
            self.logger.debug('cmd=\'%s\'', cmd)
            # コマンドライン実行
            self.alive = self.exec_cmd(cmd)
            self.logger.debug('alive=%s', self.alive)

        # スレッド終了処理
        self.logger.info('done(alive=%s)', self.alive)


#####
class App:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)

        self.pi = pigpio.pi()
        self.robot_ctrl = OttoPiCtrl(self.pi, debug=debug)
        self.robot_ctrl.start()

    def main(self):
        self.logger.debug('')

        self.robot_ctrl.send('happy')

        while True:
            cmdline = input()
            self.logger.info('cmdline=\'%s\'', cmdline)
            if cmdline == '':
                break
            self.robot_ctrl.send(cmdline)
            time.sleep(1)

            if not self.robot_ctrl.is_alive():
                break

        self.logger.info('done')

    def end(self):
        self.logger.debug('')

        self.robot_ctrl.end()
        self.logger.debug('done')


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = get_logger(__name__, debug)

    app = App(debug=debug)
    try:
        app.main()
    finally:
        logger.info('finally')
        app.end()


if __name__ == '__main__':
    main()

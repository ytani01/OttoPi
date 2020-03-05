#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'
'''
PiServo を利用して、4個のサーボを制御し、歩行やダンスなどの動作をさせる。

また、OttoPiConfigで、設定ファイルから、GPIOピン番号とサーボの初期値を読み込む。

OttoPiMotion -- 動作定義
 |
 +- PiServo -- 複数サーボの同期制御
 +- OttoPiConfig -- 設定ファイルの読み込み・保存

'''

from PiServo import PiServo
from OttoPiConfig import OttoPiConfig

import pigpio
import time
import random

from MyLogger import get_logger


#####
DEF_PIN        = [17, 27, 22, 23]
DEF_PULSE_HOME = [1470, 1430, 1490, 1490]
DEF_PULSE_MIN  = [ 500,  500,  500,  500]
DEF_PULSE_MAX  = [2500, 2500, 2500, 2500]

N_CONTINUOUS = 99999


#####
class OttoPiMotion:
    def __init__(self, pi=None, pin=[],
                 pulse_home=[],
                 pulse_min=DEF_PULSE_MIN,
                 pulse_max=DEF_PULSE_MAX,
                 debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi  = %s', str(pi))
        self.logger.debug('pin = %s', pin)
        self.logger.debug('pulse_home = %s', pulse_home)
        self.logger.debug('pulse_min  = %s', pulse_min)
        self.logger.debug('pulse_max  = %s', pulse_max)

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   = pigpio.pi()
            self.mypi = True
        self.logger.debug('mypi = %s', self.mypi)

        self.cnf = OttoPiConfig(debug=self.debug)

        if pin != []:
            self.pin = pin
        else:
            self.pin = self.cnf.get_pin()
            self.logger.debug('pin = %s', self.pin)

        if pulse_home != []:
            self.pulse_home = pulse_home
        else:
            self.pulse_home = self.cnf.get_home()
            self.logger.debug('pulse_home = %s', self.pulse_home)

        self.pulse_min = pulse_min
        self.pulse_max = pulse_max

        self.stop_flag = False

        self.servo = None
        self.reset_servo()

    def __del__(self):
        self.logger.debug('')
        # self.end()

    def reset_servo(self):
        self.logger.debug('')
        del(self.servo)
        self.servo = PiServo(self.pi, self.pin,
                             self.pulse_home, self.pulse_min, self.pulse_max,
                             debug=self.debug)
        self.servo.home()

    def end(self):
        self.logger.debug('')

        self.home()
        time.sleep(1)
        self.off()

        if self.mypi:
            self.pi.stop()
            self.mypi = False

    def off(self):
        self.logger.debug('')
        self.servo.off()

    def stop(self, n=1):
        self.logger.debug('n = %d', n)
        self.stop_flag = True

    def resume(self, n=1):
        self.logger.debug('n = %d', n)
        self.stop_flag = False

    def home(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, v, q)
        self.move1(0, 0, 0, 0, v=v, q=q)

    def change_pos(self, i, d_pos, n=1, v=None, q=False):
        self.logger.debug('i=%d, d_pos=%d', i, d_pos)

        for count in range(n):
            cur_pos = self.get_cur_position()
            cur_pos[i] += d_pos
            self.logger.info('cur_pos = %s', cur_pos)
            self.move1(cur_pos[0], cur_pos[1], cur_pos[2], cur_pos[3],
                       v=v, q=q)

    def move_up0(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(0, 5, n)

    def move_down0(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(0, -5, n)

    def move_up1(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(1, 5, n)

    def move_down1(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(1, -5, n)

    def move_up2(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(2, 5, n)

    def move_down2(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(2, -5, n)

    def move_up3(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(3, 5, n)

    def move_down3(self, n=1, v=None, q=False):
        self.logger.debug('n=%d, v=%s, q=%s', n, str(v), q)
        self.change_pos(3, -5, n)

    def adjust_home(self, i, v):
        self.logger.debug('i = %d, v = %d', i, v)
        self.pulse_home[i] += v
        self.logger.info('pulse_home = %s', self.pulse_home)
        cnf = OttoPiConfig(debug=self.debug)
        cnf.set_intlist('home', self.pulse_home)
        cnf.save()
        self.reset_servo()

    def home_up0(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(0, 5)

    def home_down0(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(0, -5)

    def home_up1(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(1, 5)

    def home_down1(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(1, -5)

    def home_up2(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(2, 5)

    def home_down2(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(2, -5)

    def home_up3(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(3, 5)

    def home_down3(self, n=1):
        self.logger.debug('n = %d', n)
        self.adjust_home(3, -5)

    def get_cur_position(self):
        self.logger.debug('')
        cur_pulse = self.servo.get_cur_position()
        self.logger.debug('cur_pulse = %s', cur_pulse)
        cur_pos = [(cur_pulse[i] / 10) for i in range(len(cur_pulse))]
        self.logger.debug('cur_pos = %s', cur_pos)
        return cur_pos

    def move(self, p_list=[], interval_msec=0, v=None, q=False):
        self.logger.debug('p_list=%s, interval_msec=%d, v=%s, q=%s',
                          p_list, interval_msec, v, q)
        for p in p_list:
            if p == []:
                self.logger.debug('p=%s: ignored', p)
                continue
            self.move1(p[0], p[1], p[2], p[3], v, q)
            time.sleep(interval_msec/1000)

    def move1(self, p1, p2, p3, p4, v=None, q=False):
        self.logger.debug('(p1, p2, p3, p4)=%s, v=%s, q=%s',
                          (p1, p2, p3, p4), v, q)
        self.servo.move1([p1*10, p2*10, p3*10, p4*10], v, q)

    def change_rl(self, rl=''):
        self.logger.debug('rl=%s', rl)

        if rl[0] == 'right'[0]:
            return 'left'
        if rl[0] == 'left'[0]:
            return 'right'
        return ''

    def ojigi(self, n=1, interval_msec=1000, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        p1 = [10, 15, 15]
        p2 = 85

        self.home()
        time.sleep(0.3)

        for i in range(n):
            if self.stop_flag:
                break

            self.move([[-p1[0], -p2, 0, 0],
                       [-p1[0], -p2, p2, p1[0]]], v=v, q=q)
            self.move([[-p1[1], -p2, p2, p1[1]],
                       [-p1[2], -p2, p2, p1[1]]],
                      interval_msec=500, v=v, q=q)
            self.move([[-p1[0], -p2, 0, 0],
                       [0, 0, 0, 0]], v=v, q=q)
            time.sleep(interval_msec / 1000)

    def ojigi2(self, n=1, interval_msec=1000, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        self.home()
        time.sleep(0.3)

        for i in range(n):
            if self.stop_flag:
                break

            self.move([[-10, -90, -30, -5],
                       [-15, -90, -35, -10],
                       [-10, -90, -30, -5],
                       [0, 0, 0, 0]],
                      interval_msec=500)

            time.sleep(interval_msec / 1000)

    def happy(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        p1 = 70
        p2 = 10

        self.home()
        time.sleep(0.3)

        for i in range(n):
            if self.stop_flag:
                break

            self.move([[p1, 0, 0, -p2],
                       [0,  0, 0,  0],
                       [p2, 0, 0, -p1],
                       [0, 0, 0, 0]], v=v, q=q)
            time.sleep(interval_msec / 1000)

    def hi(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)
        p1 = [-80, -70]
        p2 = -85
        p3 = -50
        p4 = -10

        self.home()

        for i in range(2):
            self.move1(p1[0], p2, p3, p4, v=v, q=q)
            time.sleep(0.2)
            self.move1(p1[1], p2, p3, p4, v=v, q=q)
            time.sleep(0.2)
        self.move1(p1[0], p2, p3, p4, v=v, q=q)
        # self.turn_right(1)

        time.sleep(1)
        self.home()

    def suprised(self,  n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)
        p1 = 30

        self.home()
        time.sleep(.2)
        self.move1(-p1, 0, 0, p1, q=True)
        time.sleep(.3)
        self.home()

    def slide_right(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.slide1('r', interval_msec=interval_msec, v=v, q=q)

    def slide_left(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.slide1('l', interval_msec=interval_msec, v=v, q=q)

    def slide1(self, rl='r', interval_msec=0, v=None, q=False):
        self.logger.debug('rl=%s, interval_msec=%d, v=%s, q=%s',
                          rl, interval_msec, str(v), q)

        p1 = (80, 20)
        p2 = (-10, -60)

        self.home()
        time.sleep(interval_msec/1000)

        if rl[0] == 'left'[0]:
            self.move([[p1[0], 0, 0, p1[1]],
                       [p2[0], 0, 0, p2[1]],
                       [0, 0 , 0 , 0]], interval_msec=interval_msec, v=v, q=q)

        if rl[0] == 'right'[0]:
            self.move([[-p1[1], 0, 0, -p1[0]],
                       [-p2[1], 0, 0, -p2[0]],
                       [0, 0, 0, 0]], interval_msec=interval_msec, v=v, q=q)

    def right_forward(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        self.turn1('r', interval_msec=interval_msec, v=v, q=q)
        self.walk(n, 'f', rl='', v=v, q=q)

    def left_forward(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        self.turn1('l', interval_msec=interval_msec, v=v, q=q)
        self.walk(n, 'f', rl='', v=v, q=q)

    def right_backward(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        self.turn1('l', interval_msec=interval_msec, v=v, q=q)
        self.walk(n, 'b', rl='', v=v, q=q)

    def left_backward(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        self.turn1('r', interval_msec=interval_msec, v=v, q=q)
        self.walk(n, 'b', rl='', v=v, q=q)

    def turn_right(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.turn1('r', interval_msec=interval_msec, v=v, q=q)

    def turn_left(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.info('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.turn1('l', interval_msec=interval_msec, v=v, q=q)

    def turn1(self, rl='r', interval_msec=0, v=None, q=False):
        self.logger.debug('rl=%s, interval_msec=%d, v=%s, q=%s',
                          rl, interval_msec, str(v), q)

        p1 = (60, 25)
        p2 = (20, 5)
        p3 = 0.6
        sleep_sec = 0.1

        self.home()
        time.sleep(interval_msec/1000)

        if rl[0] == 'left'[0]:
            self.move([[ p1[0],       p2[0],  p2[0],  p1[1]     ],
                       [ p1[0] * p3, -p2[0],  p2[0],  p1[1]     ],
                       [ 0,          -p2[0],  p2[0],  0         ]],
                      interval_msec=interval_msec, v=v, q=q)
            time.sleep(sleep_sec)
            self.move([[-p1[1],      -p2[0],  p2[0], -p1[0]     ],
                       [-p1[1],       p2[1], -p2[1], -p1[0] * p3],
                       [0, 0, 0, 0]], interval_msec=interval_msec, v=v, q=q)
            time.sleep(sleep_sec)

        if rl[0] == 'right'[0]:
            self.move([[-p1[1],      -p2[0], -p2[0], -p1[0]     ],
                       [-p1[1],      -p2[0],  p2[0], -p1[0] * p3],
                       [ 0,          -p2[0],  p2[0],  0         ]],
                      interval_msec=interval_msec, v=v, q=q)
            time.sleep(sleep_sec)
            self.move([[ p1[0],      -p2[0],  p2[0],  p1[1]     ],
                       [ p1[0] * p3,  p2[1], -p2[1],  p1[1]     ],
                       [0, 0, 0, 0]], interval_msec=interval_msec, v=v, q=q)
            time.sleep(sleep_sec)

    def forward(self, n=1, rl='', v=None, q=False):
        self.logger.debug('n=%d, rl=%s, v=%s, q=%s', n, rl, str(v), q)
        self.walk(n, 'f', rl, v=v, q=q)

    def backward(self, n=1, rl='', v=None, q=False):
        self.logger.debug('n=%d, rl=%s, v=%s, q=%s', n, rl, str(v), q)
        self.walk(n, 'b', rl, v=v, q=q)

    def walk(self, n=1, mv='f', rl='', v=None, q=False):
        self.logger.debug('n=%d, mv=%s rl=%s, v=%s, q=%s',
                          n, mv, rl, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        if rl == '':
            rl = 'rl'[random.randint(0, 1)]
            self.logger.debug('rl=%s', rl)

        self.home()
        time.sleep(0.2)

        for i in range(n):
            if self.stop_flag:
                break

            self.walk1(mv, rl, v=v, q=q)
            rl = self.change_rl(rl)

        self.walk1('end', rl, v=v, q=q)

    def walk1(self, mv='f', rl='r', v=None, q=False):
        self.logger.debug('mv=%s, rl=%s, v=%s, q=%s',
                          mv, rl, str(v), q)

        if rl == '':
            return

        p1 = (65, 25)
        p2 = 30

        if mv[0] == 'backward'[0]:
            p2 = -p2

        if rl[0] == 'right'[0]:
            self.move1(     p1[0],   p2/2,     0, p1[1],    v=v, q=q)
            if mv[0] != 'end'[0]:
                self.move1( p1[0]/2, p2/2,  p2/2, p1[1],    v=v, q=q)

        if rl[0] == 'left'[0]:
            self.move1(    -p1[1],      0, -p2/2, -p1[0],   v=v, q=q)
            if mv[0] != 'end'[0]:
                self.move1(-p1[1],  -p2/2, -p2/2, -p1[0]/2, v=v, q=q)

        time.sleep(.02)

        if mv[0] == 'end'[0]:
            self.home(v=v, q=q)
            return

        if rl[0] == 'right'[0]:
            self.move1(0,  p2,  p2, 0, v=v, q=q)

        if rl[0] == 'left'[0]:
            self.move1(0, -p2, -p2, 0, v=v, q=q)

    def suriashi(self, n=1, mv='f', rl='', v=None, q=False):
        self.logger.debug('n=%d, mv=%s, rl=%s, v=%s, q=%s',
                          n, mv, rl, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.debug('n=%d!', n)

        if rl == '':
            rl = 'rl'[random.randint(0, 1)]
            self.logger.debug('rl=%s', rl)

        self.home()
        time.sleep(0.5)

        for i in range(n):
            if self.stop_flag:
                break

            self.suriashi1(mv, rl, v=v, q=q)
            rl = self.change_rl(rl)

        self.suriashi1('end', rl, v=v, q=q)

    def suriashi1(self, mv='f', rl='r', v=None, q=False):
        self.logger.debug('mv=%s, rl=%s, v=%s, q=%s',
                          mv, rl, str(v), q)

        p1 = 40
        p2 = 15
        p3 = 25

        if mv[0] == 'end'[0]:
            self.home(v=v, q=q)
            return

        if rl[0] == 'right'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(p1, p3, p3, p2, v=v, q=q)
            else:
                pass

        if rl[0] == 'left'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(-p2, -p3, -p3, -p1, v=v, q=q)
            else:
                pass

        if rl[0] == 'right'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(-p2, p3, p3, -p1, v=v, q=q)
            else:
                pass

        if rl[0] == 'left'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(p1, -p3, -p3, p2, v=v, q=q)
            else:
                pass


#####
class App:
    '''
    '''
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)

        self.opm = OttoPiMotion(pi=None, debug=self.debug)

    def main(self, pos=(), interval=0.0):
        self.logger.debug('pos=%s, interval=%.2f', pos, interval)

        self.opm.home()
        time.sleep(1)

        for p in pos:
            if p[0] == '@':
                try:
                    [p1, p2, p3, p4] = [int(i) for i in p[1:].split(',')]
                except ValueError:
                    self.logger.error('p=\'%s\': invalid parameters', p)
                    return

                self.logger.info('move1(%d,%d,%d,%d)', p1, p2, p3, p4)
                self.opm.move1(p1, p2, p3, p4)

            elif p[0] in 'sS':
                sleep_sec = float(p[1:])
                self.logger.info('sleep(%.1f)', sleep_sec)
                time.sleep(sleep_sec)

            elif p[0] in 'hH':
                self.logger.info('home()')
                self.opm.home()

            else:
                self.logger.error('%s: invalid argument', p)
                break

            if interval > 0:
                time.sleep(interval)

    def end(self):
        self.logger.debug('')


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pos', type=str, nargs=-1)
@click.option('--interval', '-i', 'interval', type=float, default=0,
              help='interval[sec]')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pos, interval, debug):
    logger = get_logger(__name__, debug)
    logger.debug("interval = %0.2f", interval)
    logger.debug('pos = %s', pos)

    app = App(debug=debug)
    try:
        app.main(pos, interval)
    finally:
        logger.debug('finally')
        app.end()


if __name__ == '__main__':
    main()

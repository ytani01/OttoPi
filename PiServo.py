#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
複数のサーボモーターを同期をとりながら制御する(個数は任意)
'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

import pigpio
import time

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
PULSE_OFF  = 0
PULSE_MIN  = 500
PULSE_MAX  = 2500
PULSE_HOME = 1500

PULSE_STEP      = 22
INTERVAL_FACTOR = 0.40

DEF_PIN = [17, 27, 22, 23]
DEF_PULSE_HOME = [1500, 1500, 1500, 1500]
DEF_PULSE_MIN  = [ 500,  500,  500,  500]
DEF_PULSE_MAX  = [2500, 2500, 2500, 2500]


#####
class PiServo:
    def __init__(self, pi=None, pins=DEF_PIN,
                 pulse_home=None, pulse_min=None, pulse_max=None,
                 debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pi         = %s', pi)
        self.logger.debug('pins       = %s', pins)
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

        self.pin   = pins
        self.pin_n = len(self.pin)

        self.pulse_home = pulse_home
        self.pulse_min  = pulse_min
        self.pulse_max  = pulse_max

        if self.pulse_home is None:
            self.pulse_home = [PULSE_HOME] * self.pin_n
            self.logger.debug('pulse_home = %s', self.pulse_home)

        if self.pulse_min is None:
            self.pulse_min = [PULSE_MIN] * self.pin_n
            self.logger.debug('pulse_min  = %s', self.pulse_min)

        if self.pulse_max is None:
            self.pulse_max = [PULSE_MAX] * self.pin_n
            self.logger.debug('pulse_max  = %s', self.pulse_max)

        self.pulse_off = [PULSE_OFF] * self.pin_n
        self.logger.debug('pulse_off  = %s', self.pulse_off)

        self.cur_pulse = [0] * self.pin_n

        self.home()
        self.off()

    def off(self):
        self.logger.debug('')
        self.set_pulse(self.pulse_off)

    def get_cur_position(self):
        cur_pos = [(self.cur_pulse[i] - self.pulse_home[i])
                   for i in range(self.pin_n)]
        self.logger.debug('cur_pos = %s', cur_pos)
        return cur_pos

    def set_pulse(self, pulse):
        self.logger.debug('pulse=%s', pulse)

        for i in range(self.pin_n):
            if pulse[i] != 0:
                if pulse[i] < self.pulse_min[i]:
                    self.logger.warn('[%d]: %d < %d !', i, pulse[i],
                                     self.pulse_min[i])
                    pulse[i] = self.pulse_min[i]

                if pulse[i] > self.pulse_max[i]:
                    self.logger.warn('[%d]: %d > %d !', i, pulse[i],
                                     self.pulse_max[i])
                    pulse[i] = self.pulse_max[i]

                self.cur_pulse[i] = pulse[i]

            self.pi.set_servo_pulsewidth(self.pin[i], pulse[i])

    def home(self):
        self.logger.debug('')
        self.set_pulse(self.pulse_home)

    def move(self, pos_list=[], interval_msec=0, v=None, quick=False):
        self.logger.debug('pos_list=%s, v=%s, quick=%s', pos_list, v, quick)

        if type(pos_list[0]) != list:
            self.move1(pos_list, v, quick)
            return

        for p in pos_list:
            self.move1(p, v, quick)
            time.sleep(interval_msec/1000)

    def move1(self, pos, v=None, quick=False):
        self.logger.debug('pos=%s, v=%s, quick=%s', pos, v, quick)
        p = [pos[i] + self.pulse_home[i] for i in range(self.pin_n)]
        self.move_p(p, v, quick)

    def move_p(self, pulse, v=None, quick=False):
        self.logger.debug('pulse=%s, v=%s, quick=%s', pulse, v, quick)

        if v is None:
            v = INTERVAL_FACTOR

        d_list = [abs(pulse[i] - self.cur_pulse[i]) for i in range(self.pin_n)]
        self.logger.debug('d_list = %s', d_list)

        d_max = max(d_list)
        self.logger.debug('d_max=%d', d_max)

        # d_min = min(d_list)
        # self.logger.debug('d_min=%d', d_min)

        if quick:
            # quick mode
            sleep_msec = d_max * v
            self.logger.debug('sleep_msec = %d', sleep_msec)

            self.set_pulse(pulse)
            time.sleep(sleep_msec/1000)
            return

        step_n = int(d_max / PULSE_STEP)
        if d_max > PULSE_STEP * step_n:
            step_n += 1
        self.logger.debug('step_n = %d', step_n)

        if step_n == 0:
            interval_msec = 0
        else:
            interval_msec = d_max / step_n * v
        self.logger.debug('interval_msec=%d', interval_msec)

        pulse0 = [0] * self.pin_n
        dp = [0] * self.pin_n
        for i in range(self.pin_n):
            pulse0[i] = self.cur_pulse[i]

            if step_n == 0:
                dp[i] = pulse[i] - self.cur_pulse[i]
            else:
                dp[i] = (pulse[i] - self.cur_pulse[i]) / step_n

        self.logger.debug('pulse0 = %s', pulse0)
        self.logger.debug('dp = %s', dp)

        p = [0] * self.pin_n
        for s in range(step_n):
            for i in range(self.pin_n):
                p[i] = pulse0[i] + dp[i] * (s + 1)

            self.logger.debug('p = %s', p)
            self.set_pulse(p)
            time.sleep(interval_msec/1000)

    def print_pulse(self):
        self.logger.debug('')

        print('cur_pulse = %s' % self.cur_pulse)
        print('cur_pos = %s' %
              [(self.cur_pulse[i] - self.pulse_home[i])
               for i in range(self.pin_n)])


#####
class Sample:
    def __init__(self, pins, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('pins = %s', pins)

        self.pin = pins

        self.pi  = pigpio.pi()
        self.servo = PiServo(self.pi, self.pin, DEF_PULSE_HOME,
                             debug=self.debug)

    def main(self):
        self.logger.debug('')

        self.servo.move1([-200, 0, 0, -200])
        self.servo.move1([0, 0, 0, 0])
        self.servo.move1([200, 0, 0, 200])
        self.servo.move1([0, 0, 0, 0])

        time.sleep(1)

        self.servo.move([[200, 0, 0, -200],
                         [0, 0, 0, 0],
                         [-200, 0, 0, 200],
                         [0, 0, 0, 0]],
                        interval_msec=100)

    def end(self):
        self.logger.debug('')

        self.servo.home()
        self.servo.print_pulse()
        time.sleep(1)
        self.servo.off()
        self.pi.stop()


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin1', type=int, default=DEF_PIN[0])
@click.argument('pin2', type=int, default=DEF_PIN[1])
@click.argument('pin3', type=int, default=DEF_PIN[2])
@click.argument('pin4', type=int, default=DEF_PIN[3])
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('pins: %d, %d, %d, %d', pin1, pin2, pin3, pin4)

    obj = Sample([pin1, pin2, pin3, pin4], debug=debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()


if __name__ == '__main__':
    main()

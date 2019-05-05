#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import pigpio
import time

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
PULSE_OFF  = 0
PULSE_MIN  = 500
PULSE_MAX  = 2500
PULSE_HOME = 1500

PULSE_STEP      = 20
INTERVAL_FACTOR = 0.25

#####
class PiServo:
    def __init__(self, pi, pins,
                 pulse_home=None, pulse_min=None, pulse_max=None,
                 debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)

        self.pi    = pigpio.pi()
        self.pin  = pins
        self.pin_n = len(self.pin)

        self.pulse_min  = pulse_min
        self.pulse_max  = pulse_max
        self.pulse_home = pulse_home

        if self.pulse_min is None:
            self.pulse_min = [PULSE_MIN] * self.pin_n

        if self.pulse_max is None:
            self.pulse_max = [PULSE_MAX] * self.pin_n

        if self.pulse_home is None:
            self.pulse_home = [PULSE_HOME] * self.pin_n

        self.cur_pulse = [pulse_home] * self.pin_n
        self.set_pulse(self.pulse_home)
        self.stop()

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

                self.cur_pulse[i] = pulse[i] - self.pulse_min[i]

            self.pi.set_servo_pulsewidth(self.pin[i], pulse[i])

    def stop(self):
        self.logger.debug('')

        pulse = [0] * self.pin_n
        self.set_pulse(pulse)
        
    def move(self, pulse):
        self.logger.debug('pulse=%s', pulse)

        d_max = 0
        for i in range(self.pin_n):
            d = pulse[i] - self.cur_pulse[i]
            if abs(d) > d_max:
                d_max = abs(d)
        print('d_max =', d_max)

        step_n = int(d_max / PULSE_STEP)
        if d_max > PULSE_STEP * step_n:
            step_n += 1
        print('step_n =', step_n)
        
        pulse0 = [0] * self.pin_n
        dp = [0] * self.pin_n
        for i in range(self.pin_n):
            pulse0[i] = self.cur_pulse[i]
            dp[i] = (pulse[i] - self.cur_pulse[i]) / step_n
        print('pulse0 =', dp)
        print('dp =', dp)

        p = [0] * self.pin_n
        for s in range(step_n):
            for i in range(self.pin_n):
                p[i] = pulse0[i] + dp[i] * (s + 1)

            print('p =', p)
            self.set_pulse(p)
            
            
        '''
        if interval_msec is None:
            interval_msec = self.DEF_INTERVAL_MSEC

        if new_pos > self.cur_pulse:
            pulse_step = self.PULSE_STEP
        else:
            pulse_step = -self.PULSE_STEP

        while self.cur_pulse != new_pos:
            d = new_pos - self.cur_pulse
            if abs(d) >= self.PULSE_STEP:
                next_pos = self.cur_pulse + pulse_step
            else:
                next_pos = self.cur_pulse + d
            self.logger.debug('next_pos = %d', next_pos)

            self.set_pulse(next_pos + self.pulse_home)
            time.sleep(interval_msec/1000)
        '''

    def print_pulse(self):
        self.logger.debug('')

        print('cur_pulse = %s' % self.cur_pulse)

#####
class Sample:
    SLEEP_MSEC = 2000

    def __init__(self, pi, pins, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pins = %s', pins)

        self.pi  = pi
        self.pin = pins

        self.servo = PiServo(self.pi, self.pin, debug=self.debug)

    def main(self):
        self.logger.debug('')

        self.servo.print_pulse()

        self.servo.move([1000,  2000, 1750, 1999])
        self.servo.print_pulse()

        time.sleep(self.SLEEP_MSEC/1000)

        self.servo.move([1500, 1500, 1500, 1500])
        self.servo.print_pulse()

        self.finish()
            
    def finish(self):
        self.logger.debug('')

        self.servo.stop()
        
#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pin1', type=int, default=4)
@click.argument('pin2', type=int, default=17)
@click.argument('pin3', type=int, default=27)
@click.argument('pin4', type=int, default=22)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pin1, pin2, pin3, pin4, debug):
    logger = get_logger('', debug)
    logger.debug('pins: %d, %d, %d, %d', pin1, pin2, pin3, pin4)

    pi  = pigpio.pi()
    obj = Sample(pi, [pin1, pin2, pin3, pin4], debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.finish()
        pi.stop()

if __name__ == '__main__':
    main()

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

PULSE_STEP      = 25
INTERVAL_FACTOR = 0.4
#INTERVAL_FACTOR = 1

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

        self.logger.debug('pulse_min  = %s', self.pulse_min)
        self.logger.debug('pulse_max  = %s', self.pulse_max)
        self.logger.debug('pulse_home = %s', self.pulse_home)

        self.pulse_stop = [0] * self.pin_n
        self.logger.debug('pulse_stop = %s', self.pulse_home)

        self.cur_pulse = [PULSE_HOME] * self.pin_n

        self.home()
        self.stop()


    def stop(self):
        self.logger.debug('')
        self.set_pulse(self.pulse_stop)
        

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


    def home(self, v=None, quick=False):
        self.logger.debug('')
        
        p = [0] * self.pin_n
        self.move(p, v, quick)
        #self.set_pulse(self.pulse_home)


    def pos2pulse(self, pos):
        self.logger.debug('pos=%s', pos)

        p = []
        for i in range(self.pin_n):
            p.append(pos[i] + self.pulse_home[i])

        return p


    def move(self, pos, v=None, quick=False):
        self.logger.debug('pos=%s, v=%s, quick=%s', pos, v, quick)
        p = [pos[i] + self.pulse_home[i] for i in range(self.pin_n)]
        #p = self.pos2pulse(pos)
        self.move0(p, v, quick)


    def move0(self, pulse, v=None, quick=False):
        self.logger.debug('pulse=%s, v=%s, quick=%s', pulse, v, quick)

        if v is None:
            v = INTERVAL_FACTOR
            
        d_list = [abs(pulse[i] - self.cur_pulse[i]) for i in range(self.pin_n)]
        self.logger.debug('d_list = %s', d_list)

        d_max = max(d_list)
        self.logger.debug('d_max=%d', d_max)

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
    #SLEEP_MSEC = 1000

    def __init__(self, pi, pins, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pins = %s', pins)

        self.pi  = pi
        self.pin = pins

        self.servo = PiServo(self.pi, self.pin,
                             [1500, 1440, 1340, 1450], debug=self.debug)

    def move(self, p1, p2, p3, p4, v=None, quick=False):
        self.logger.debug('')

        self.servo.move([p1, p2, p3, p4], v, quick)
        self.servo.print_pulse()

    def walk1(self, v=None, quick=False):
        p1 = 250
        p2 = 200
        p3 = 600
        p4 = 260
        
        self.move( p1,  p2,   0,  p3, v, quick)
        self.move(  0,  p4,  p4,   0, v, quick)
        self.move(-p3,   0, -p2, -p1, v, quick)
        self.move(  0, -p4, -p4,   0, v, quick)
        

    def main(self):
        self.logger.debug('')

        self.servo.home()
        self.servo.print_pulse()

        self.move( 100,  200,  200,  100)
        self.move(-100, -200, -200, -100)
        self.servo.home()
        time.sleep(2)

        self.move(0, 260, 260, 0)
        self.walk1()
        self.walk1()
        self.walk1()
        self.walk1()

        self.finish()
            
    def finish(self):
        self.logger.debug('')

        self.servo.home()
        self.servo.print_pulse()
        time.sleep(1)
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

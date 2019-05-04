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
handler = StreamHandler()
handler.setLevel(DEBUG)
handler_fmt = Formatter(
    '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
    datefmt='%H:%M:%S')
handler.setFormatter(handler_fmt)
logger.addHandler(handler)
logger.propagate = False
def init_logger(name, debug):
    l = logger.getChild(name)
    if debug:
        l.setLevel(DEBUG)
    else:
        l.setLevel(INFO)
    return l

#####
class Sample:
    SLEEP_MSEC = 500

    VAL_CENTER = 1500
    VAL_MIN    = 500
    VAL_MAX    = 2500
    
    def __init__(self, pi, pins, sleep_msec=None, debug=False):
        self.debug = debug
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('pins = %s', pins)

        self.pi         = pi
        self.pins       = pins
        self.sleep_msec = sleep_msec
        if self.sleep_msec is None:
            self.sleep_msec = self.SLEEP_MSEC

        self.stop()


    def main(self):
        self.logger.debug('')

        while True:
            for v in [500, 2500, 1500, 1200, 1800, 1500]:
                pv = {}
                for p in self.pins:
                    pv[p] = v
                self.move_all(pv)


    def finish(self):
        self.logger.debug('')

        pv = {}
        for p in self.pins:
            if p == 0:
                continue

            pv[p] = self.VAL_CENTER
        
        self.move_all(pv)
        self.stop()

        
    def stop(self):
        self.logger.debug('')
        
        for p in self.pins:
            if p == 0:
                continue
            self.pi.set_servo_pulsewidth(p, 0)

    def move_all(self, pv, sleep_msec=None):
        self.logger.debug('pv=%s', str(pv))

        if sleep_msec is None:
            sleep_msec = self.sleep_msec
            
        for p in pv.keys():
            if p == 0:
                self.logger.warn('p=%d: ignored', p)
                continue

            v = pv[p]
            if v < 500 or v > 2500:
                self.logger.warn('500 <= v <= 2500')
                continue
        
            self.move1(p, v)

        self.logger.debug('sleep %d msec', sleep_msec)
        time.sleep(sleep_msec/1000)


    def move1(self, pin, val):
        self.logger.debug('%d:%d', pin, val)

        self.pi.set_servo_pulsewidth(pin, val)

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pins',   type=int, nargs=-1)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pins, debug):
    logger = init_logger('', debug)
    logger.debug('pins   = %s', pins)

    if len(pins) == 0:
        return
    
    pi  = pigpio.pi()
    obj = Sample(pi, pins, 500, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.finish()
        pi.stop()

if __name__ == '__main__':
    main()

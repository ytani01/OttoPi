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
    
    def __init__(self, pins, debug=False):
        self.debug = debug
        self.logger = init_logger(__class__.__name__, debug)
        self.logger.debug('pins = %s', pins)

        self.pins = pins

        self.pi = pigpio.pi()

        self.stop()

    def move_all(self, val):
        self.logger.debug('val=%d', val)
        
        for p in self.pins:
            self.pi.set_servo_pulsewidth(p, val)

        time.sleep(self.SLEEP_MSEC)

    def main(self):
        self.logger.debug('')

        while True:
            for v in [550, 2450, 1500]:
                self.move_all(v)
                
    def stop(self):
        for p in self.pins:
            self.pi.set_servo_pulsewidth(p, 0)

    def finish(self):
        self.logger.debug('')
        self.stop()
        self.pi.stop()

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('pins', type=int, nargs=-1)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(pins, debug):
    logger = init_logger('', debug)
    logger.debug('pins   = %s', pins)

    obj = Sample(pins, debug=debug)
    try:
        obj.main()
    finally:
        print('finally')
        obj.finish()

if __name__ == '__main__':
    main()

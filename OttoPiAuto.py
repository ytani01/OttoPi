#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

import OttoPiCtrl
import VL53L0X
import time
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
    def __init__(self, ottopi_ctrl=None, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('')

        self.my_opc = False
        self.opc = ottopi_ctrl
        if ottopi_ctrl == None:
            self.myopc = True
            self.opc = OttoPiCtrl.OttoPiCtrl(None, debug=self.debug)
            self.opc.start()

        self.tof = VL53L0X.VL53L0X()
        self.tof.start_ranging(VL53L0X.VL53L0X_BEST_ACCURACY_MODE)
        #self.tof_timing = self.tof.get_timing()

        self.d = 0

        super().__init__(daemon=True)

    def __del__(self):
        self.logger.debug('')

    def end(self):
        self.logger.debug('')
        self.tof.stop_ranging()
        if self.my_opc:
            self.opc.end()

    def get_distance(self):
        self.d = self.tof.get_distance()
        return self.d

    def run(self):
        self.logger.debug('')

        while True:
            self.get_distance()
            self.logger.debug('d = %smm', '{:,}'.format(self.d))
            if self.d < 350:
                self.opc.send_cmd(self.opc.CMD_STOP)
            time.sleep(0.5)


#####
class Sample:
    def __init__(self, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('')

        self.opa = OttoPiAuto(debug=self.debug)
        self.opa.start()

    def main(self):
        self.logger.debug('')

        while True:
            time.sleep(1)

    def end(self):
        self.logger.debug('')
        self.opa.end()

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    logger = get_logger('', debug)

    obj = Sample(debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()
    
        

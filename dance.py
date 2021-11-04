#!/usr/bin/env python3
#
# (c) 2021 Yoichi Tanibayashi
#
import time
import random
import threading
from OttoPiCtrl import OttoPiCtrl
from MyLogger import get_logger


class Dance(threading.Thread):
    """ Dance mode """

    CMD = [
        "slide_right",
        "slide_right",
        "slide_left",
        "slide_left",
        "happy",
        "happy",
        "surprised",
        "surprised",
        "hi_right",
        "hi_left",
        "bye_right",
        "bye_left",
        "toe_right 2",
        "toe_right 2",
        "toe_left 2",
        "toe_left 2",
        "heel_right 2",
        "heel_right 2",
        "heel_left 2",
        "heel_left 2",
        "ojigi",
        "home"
    ]

    def __init__(self, robot_ctrl, max_sleep_sec=5, debug=False):
        """ __init__ """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('max_sleep_sec=%s', max_sleep_sec)

        self._robot_ctrl = robot_ctrl
        self._max_sleep_sec = max_sleep_sec

        self.active = False

        super().__init__(daemon=True)

    def run(self):
        """ run """
        self._log.debug('')

        self.active = True
        while self.active:
            cmd_i = int(random.random() * len(self.CMD))
            cmd = self.CMD[cmd_i] + ' 1'
            self._log.debug('cmd=%a', cmd)
            self._robot_ctrl.send(cmd, doInterrupt=False)

            sleep_sec = random.random() * self._max_sleep_sec
            self._log.debug('sleep_sec=%s', sleep_sec)
            time.sleep(sleep_sec)

    def end(self):
        """ end """
        self._log.debug('')
        self._robot_ctrl.send('home 1', doInterrupt=True)
        self.active = False
        self.join()
        self._log.debug('done')


import pigpio
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('max_sleep_sec', type=float, default=4)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(max_sleep_sec, debug):
    _log = get_logger(__name__, debug)
    _log.info('max_sleep_sec=%d', max_sleep_sec)

    try:
        pi = pigpio.pi()
        robot_ctrl = OttoPiCtrl(pi)
        robot_ctrl.start()
        obj = Dance(robot_ctrl, max_sleep_sec, debug=debug)
        obj.start()
        cmdline = input('> ')
        print('cmdline=%a' % (cmdline))
        obj.end()
        while not robot_ctrl.cmdq.empty():
            time.sleep(1)
            print('.', end='', flush=True)

    finally:
        _log.info('finally')
        robot_ctrl.end()


if __name__ == '__main__':
    main()

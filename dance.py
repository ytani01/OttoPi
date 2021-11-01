#!/usr/bin/env python3
#
# (c) 2021 Yoichi Tanibayashi
#
import random
import time
import click

from OttoPiClient import OttoPiClient

from MyLogger import get_logger


class OttoPiDanceApp:
    """ OttoPiDanceApp """

    CMD = [
        ":slide_right",
        ":slide_left",
        ":happy",
        ":surprised",
        ":hi_right",
        ":hi_left",
        ":bye_right",
        ":bye_left",
        ":ojigi",
        ":home"
    ]

    def __init__(self, max_sleep_sec, svr_host, svr_port, debug=False):
        """ __init__ """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)

        self._max_sleep_sec = max_sleep_sec
        self._cl = OttoPiClient(svr_host, svr_port)

    def main(self):
        """ main """
        self._log.debug('')

        while True:
            cmd_i = int(random.random() * len(self.CMD))
            cmd = self.CMD[cmd_i] + " 1"
            self._log.debug('cmd=%a', cmd)
            self._cl.send_cmd(cmd)

            sleep_sec = random.random() * self._max_sleep_sec
            self._log.debug('sleep_sec=%s', sleep_sec)
            time.sleep(sleep_sec)

    def end(self):
        """ end """
        self._log.debug('')


CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('max_sleep_sec', type=int, default=3)
@click.option('--svr_host', '-s', 'svr_host', type=str, default="localhost",
              help='server hostname or IP address')
@click.option('--svr_port', '--port', '-p', 'svr_port', type=int,
              default=OttoPiClient.DEF_PORT,
              help='server port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(max_sleep_sec, svr_host, svr_port, debug):
    _log = get_logger(__name__, debug)
    _log.info('max_sleep_sec=%d, svr_host=%s, svr_port=%d',
              max_sleep_sec, svr_host, svr_port)

    obj = OttoPiDanceApp(max_sleep_sec, svr_host, svr_port, debug=debug)
    try:
        obj.main()
    finally:
        _log.info('finally')
        obj.end()


if __name__ == '__main__':
    main()

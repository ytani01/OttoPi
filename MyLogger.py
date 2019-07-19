#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from logging import getLogger, StreamHandler, Formatter, DEBUG, INFO, WARN

class MyLogger:
    def __init__(self, name=''):
        self.handler_fmt = Formatter(
            '%(asctime)s %(levelname)s %(name)s.%(funcName)s> %(message)s',
            datefmt='%H:%M:%S')

        self.console_handler = StreamHandler()
        self.console_handler.setLevel(DEBUG)
        self.console_handler.setFormatter(self.handler_fmt)

        self.logger = getLogger(name)
        self.logger.setLevel(INFO)
        self.logger.addHandler(self.console_handler)
        self.logger.propagate = False

    def get_logger(self, name, debug):
        l = self.logger.getChild(name)
        if debug:
            l.setLevel(DEBUG)
        else:
            l.setLevel(INFO)
        return l


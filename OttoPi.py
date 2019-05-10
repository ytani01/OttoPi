#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
from PiServo import PiServo

import pigpio
import time
import random

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
PULSE_HOME = [1470, 1430, 1490, 1490]

DEF_PIN1 = 4
DEF_PIN2 = 17
DEF_PIN3 = 27
DEF_PIN4 = 22

N_CONTINUOUS = 99999

#####
class OttoPi:
    def __init__(self, pi=None,
                 pin1=DEF_PIN1, pin2=DEF_PIN2,
                 pin3=DEF_PIN3, pin4=DEF_PIN4,
                 debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi:  %s', str(pi))
        self.logger.debug('pin: %s', [pin1, pin2, pin3, pin4])

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   =  pigpio.pi()
            self.mypi = True
            
        self.pin = [pin1, pin2, pin3, pin4]

        self.servo = PiServo(self.pi, self.pin, PULSE_HOME,
                             debug=logger.propagate)

        self.stop_flag = False

        self.off()
        self.home()

    def off(self):
        self.logger.debug('')
        self.servo.off()


    def stop(self, n=1):
        self.logger.debug('')

        self.stop_flag = True

    def go(self, n=1):
        self.logger.debug('')

        self.stop_flag = False
            

    def move(self, p_list=[], interval_msec=0, v=None, q=False):
        self.logger.debug('p_list=%s, interval_msec=%d, v=%s, q=%s',
                          p_list, interval_msec, v, q)

        for p in p_list:
            self.move1(p[0], p[1], p[2], p[3], v, q)
            time.sleep(interval_msec/1000)


    def move1(self, p1, p2, p3, p4, v=None, q=False):
        self.logger.debug('(p1, p2, p3, p4)=%s, v=%s, q=%s',
                          (p1, p2, p3, p4), v, q)

        self.servo.move1([p1*10, p2*10, p3*10, p4*10], v, q)


    def home(self, v=None, q=False):
        self.logger.debug('v=%s, q=%s', v, q)
        self.move1(0, 0, 0, 0, v=v, q=q)

    def change_rl(self, rl=''):
        self.logger.debug('rl=%s', rl)

        if rl=='':
            return ''

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
            self.logger.info('n=%d!', n)
            
        p1 = [10, 25, 15]
        p2 = 90

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
                       [0,0,0,0]],v=v,q=q)
            time.sleep(interval_msec/1000)
        
    def happy(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)
            
        p1 = 70
        p2 = 10

        self.home()
        time.sleep(0.3)

        for i in range(n):
            if self.stop_flag:
                break
            
            self.move([[p1,0,0,-p2],
                       [0,0,0,0],
                       [p2,0,0,-p1],
                       [0,0,0,0]],
                      v=v, q=q)
            time.sleep(interval_msec/1000)
                      

    def side_right(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.side1('r', interval_msec=interval_msec, v=v, q=q)

    def side_left(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)

        for i in range(n):
            if self.stop_flag:
                break

            self.side1('l', interval_msec=interval_msec, v=v, q=q)

    def side1(self, rl='r', interval_msec=0, v=None, q=False):
        self.logger.debug('rl=%s, interval_msec=%d, v=%s, q=%s',
                          rl, interval_msec, str(v), q)

        p1 = (80, 30)
        p2 = (-10, -60)

        self.home()
        time.sleep(interval_msec/1000)

        if rl[0] == 'left'[0]:
            self.move([(p1[0], 0, 0, p1[1]),
                       (p2[0], 0, 0, p2[1]),
                       (0,0,0,0)], interval_msec=interval_msec, v=v, q=q)

        if rl[0] == 'right'[0]:
            self.move([(-p1[1], 0, 0, -p1[0]),
                       (-p2[1], 0, 0, -p2[0]),
                       (0,0,0,0)], interval_msec=interval_msec, v=v, q=q)


    def turn_right(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
                          n, interval_msec, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)
            
        for i in range(n):
            if self.stop_flag:
                break
            
            self.turn1('r', interval_msec=interval_msec, v=v, q=q)

    def turn_left(self, n=1, interval_msec=0, v=None, q=False):
        self.logger.debug('n=%d, interval_msec=%d, v=%s, q=%s',
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

        p1 = (65, 35)
        p2 = 30

        self.home()
        time.sleep(interval_msec/1000)
        
        if rl[0] == 'left'[0]:
            self.move([[p1[0],   p2, p2,   p1[1]],
                       [0,      -p2, p2, p1[1]/2],
                       [0,      -p2, p2,       0],
                       [-p1[1],   0,  0,  -p1[0]],
                       [0,0,0,0]], interval_msec=interval_msec, v=v, q=q)

        if rl[0] == 'right'[0]:
            self.move([[-p1[1], -p2, -p2, -p1[0]],
                       [-p1[1]/2, -p2, p2, 0],
                       [0, -p2, p2, 0],
                       [p1[0], 0, 0, p1[1]],
                       [0,0,0,0]],
                      interval_msec=interval_msec, v=v, q=q)


    def forward(self, n=1, rl='', v=None, q=False):
        self.logger.debug('n=%d, rl=%s, v=%s, q=%s',
                          n, rl, str(v), q)

        self.walk(n, 'f', rl, v=v, q=q)
        
    def backward(self, n=1, rl='', v=None, q=False):
        self.logger.debug('n=%d, rl=%s, v=%s, q=%s',
                          n, rl, str(v), q)

        self.walk(n, 'b', rl, v=v, q=q)
        
    def walk(self, n=1, mv='f', rl='', v=None, q=False):
        self.logger.debug('n=%d, mv=%s rl=%s, v=%s, q=%s',
                          n, mv, rl, str(v), q)

        if n == 0:
            n = N_CONTINUOUS
            self.logger.info('n=%d!', n)
            
        if rl == '':
            rl = 'rl'[random.randint(0,1)]
            self.logger.debug('rl=%s', rl)

        self.home()
        time.sleep(0.5)

        for i in range(n):
            if self.stop_flag:
                break
            
            self.walk1(mv, rl, v=v, q=q)
            rl = self.change_rl(rl)

        self.walk1('e', rl, v=v, q=q)

    def walk1(self, mv='f', rl='r', v=None, q=False):
        self.logger.debug('mv=%s, rl=%s, v=%s, q=%s',
                          mv, rl, str(v), q)

        if rl == '':
            return

        p1 = (65, 35)
        p2 = (40)

        if rl[0] == 'right'[0]:
            if mv[0] == 'forward'[0]:
                self.move1( p1[0], p2/2,  0,  p1[1], v=v, q=q)
            if mv[0] == 'backward'[0]:
                self.move1( p1[0],  0,  0,  p1[1], v=v, q=q)
            if mv[0] == 'end'[0]:
                self.move1( p1[0], p2/2,  0,  p1[1], v=v, q=q)
                
        if rl[0] == 'left'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(-p1[1], 0, -p2/2, -p1[0], v=v, q=q)
            if mv[0] == 'backward'[0]:
                self.move1(-p1[1], 0,   0, -p1[0], v=v, q=q)
            if mv[0] == 'end'[0]:
                self.move1(-p1[1], 0, -p2/2, -p1[0], v=v, q=q)

        time.sleep(.1)

        if mv[0] == 'end'[0]:
            self.home(v=v, q=q)
            return
        
        if rl[0] == 'right'[0]:
            if mv[0] == 'forward'[0]:
                self.move1(0, p2, p2, 0, v=v, q=q)
            if mv[0] == 'back'[0]:
                self.move1(0,-p2,-p2, 0, v=v, q=q)
            
        if rl[0] == 'left'[0]:
            if mv[0] == 'forowar'[0]:
                self.move1(0,-p2,-p2, 0, v=v, q=q)
            if mv[0] == 'back'[0]:
                self.move1(0, p2, p2, 0, v=v, q=q)


    def end(self):
        self.logger.debug('')

        self.servo.home()
        time.sleep(1)
        self.servo.off()
        if self.mypi:
            self.pi.stop()

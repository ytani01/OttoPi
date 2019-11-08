#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'
'''

'''

from OttoPiClient import OttoPiClient
from Led import Led
from Switch import Switch, SwitchListener, SwitchEvent

import RPi.GPIO as GPIO
import subprocess
import time
import os

from MyLogger import get_logger


#####
DEF_PIN_SW  = 21
DEF_PIN_VCC = 26
DEF_PIN_LED = 20


#####
class App:
    STOP_SPEECH_FILE = os.environ['HOME'] + '/stop_speech'
    STOP_MUSIC_FILE  = os.environ['HOME'] + '/stop_music'

    CMDLINE = {'shutdown':     ['sudo', 'shutdown', '-h', 'now'],
               'reboot':       ['sudo', 'shutdown', '-r', 'now'],
               'start_speech': ['rm', '-f', STOP_SPEECH_FILE],
               'start_music':  ['rm', '-f', STOP_MUSIC_FILE],
               'stop_speech':  ['touch', STOP_SPEECH_FILE],
               'stop_music':   ['touch', STOP_MUSIC_FILE]}

    def __init__(self, sw_pin=DEF_PIN_SW, sw_vcc=DEF_PIN_VCC,
                 led_pin=DEF_PIN_LED, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('sw_pin  = %d', sw_pin)
        self.logger.debug('sw_vcc  = %d', sw_vcc)
        self.logger.debug('led_pin = %d', led_pin)

        self.sw_pin  = sw_pin
        self.sw_vcc  = sw_vcc
        self.led_pin = led_pin

        if sw_vcc != 0:
            # VCC ON
            GPIO.setup(sw_vcc, GPIO.OUT)
            GPIO.output(sw_vcc, GPIO.HIGH)

        self.long_press = [
            {'timeout': 0.7, 'blink': {'on': 1,    'off': 0}},    # multi click
            {'timeout': 1,   'blink': {'on': 0.2,  'off': 0.04}},  # blink1
            {'timeout': 3,   'blink': {'on': 0.1,  'off': 0.04}},  # blink2
            {'timeout': 5,   'blink': {'on': 0.02, 'off': 0.04}},  # blink3
            {'timeout': 7,   'blink': {'on': 0,    'off': 0}}]     # off

        self.level = 0

        self.timeout_sec = []
        for i in range(len(self.long_press)):
            self.timeout_sec.append(self.long_press[i]['timeout'])

        self.sw  = Switch(self.sw_pin, self.timeout_sec, debug=self.debug)
        self.sl  = SwitchListener([self.sw], self.cb_sw, debug=self.debug)
        self.led = Led(self.led_pin)

        self.blink_alive()

    def main(self):
        self.logger.debug('')

        while True:
            self.logger.debug('level:%d', self.level)
            time.sleep(10)

    def end(self):
        self.logger.debug('')

    def blink_alive(self):
        self.logger.debug('')
        self.led.blink(0.05, 0.95)

    def exec_cmd(self, cmd):
        self.logger.debug('CMDLINE[%s]=%s', cmd, str(self.CMDLINE[cmd]))
        subprocess.run(self.CMDLINE[cmd])

    def exec_shutdown_cmd(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        self.led.off()
        GPIO.setup(self.led_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        self.exec_cmd(cmd)

    def start_sound(self, start_speech=True, start_music=True):
        self.logger.debug('start_speech=%s, start_music=%s',
                          start_speech, start_music)

        if start_speech:
            self.start_speech()

        if start_music:
            self.start_music()
        
    def start_speech(self):
        self.logger.debug('')
        self.exec_cmd('start_speech')

    def start_music(self):
        self.logger.debug('')
        self.exec_cmd('start_music')

    def stop_sound(self, stop_speech=True, stop_music=True):
        self.logger.debug('stop_speech=%s, stop_music=%s',
                          stop_speech, stop_music)

        if stop_speech:
            self.stop_speech()

        if stop_music:
            self.stop_music()

    def stop_speech(self):
        self.logger.debug('')
        self.exec_cmd('stop_music')

    def stop_music(self):
        self.logger.debug('')
        self.exec_cmd('stop_speech')

    def shutdown(self):
        self.logger.debug('')
        self.exec_shutdown_cmd('shutdown')

    def reboot(self):
        self.logger.debug('')
        self.exec_shutdown_cmd('reboot')

    def call_robot(self, cmd):
        self.logger.debug('cmd')

        rc = OttoPiClient('localhost', 12345, self.debug)
        rc.send_cmd(cmd)
        rc.close()

    def cb_sw(self, event):
        '''
        callback function for switch
        '''
        self.logger.info('level=%d, pin:%d, %s[%d,%d]:%s',
                         self.level,
                         event.pin,
                         event.name, event.push_count, event.timeout_idx,
                         Switch.val2str(event.value))

        if event.name == 'pressed':
            self.led.on()

            return

        if event.name == 'released':
            if self.level == len(self.long_press) - 2:
                self.reboot()

            if event.push_count >= 2:
                self.logger.info('auto')
                self.call_robot(':auto_on')
                self.start_sound()
            else:
                self.logger.info('stop')
                self.call_robot(':auto_off')
                self.stop_sound()

            self.level = 0
            self.blink_alive()
            return

        if event.name == 'timer':
            self.level = event.timeout_idx
            if self.level > 0 and self.level < len(self.long_press) - 1:
                self.led.off()
                self.led.blink(self.long_press[self.level]['blink']['on'],
                               self.long_press[self.level]['blink']['off'])
            else:
                self.blink_alive()

            if self.level >= len(self.long_press) - 1:
                self.shutdown()


####
def setup_GPIO():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)


def cleanup_GPIO():
    GPIO.cleanup()


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


@click.command(context_settings=CONTEXT_SETTINGS)
@click.option('--switch_pin', '-s', 'switch_pin', type=int,
              default=DEF_PIN_SW, help='Switch pin')
@click.option('--switch_vcc', '-v', 'switch_vcc', type=int,
              default=DEF_PIN_VCC, help='Switch VCC')
@click.option('--led_pin', '-l', 'led_pin', type=int,
              default=DEF_PIN_LED, help='LED pin')
@click.option('--debug', '-d', 'debug', is_flag=True,
              default=False, help='debug flag')
def main(switch_pin, switch_vcc, led_pin, debug):
    logger = get_logger(__name__, debug)

    logger.info('switch_pin=%d, switch_vcc=%d, led_pin=%d',
                switch_pin, switch_vcc, led_pin)

    setup_GPIO()
    obj = App(switch_pin, switch_vcc, led_pin, debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()
        cleanup_GPIO()


if __name__ == '__main__':
    main()

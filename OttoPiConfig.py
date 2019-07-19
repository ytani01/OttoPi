#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
import configparser

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
DEF_CONF_FILE = 'OttoPi.conf'
DEF_SECTION   = 'OttoPi'
KEY_PIN       = 'pin'
KEY_HOME      = 'home'

#####
class OttoPiConfig:
    def __init__(self, conf_file=DEF_CONF_FILE, debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('conf_file = %s', conf_file)

        self.conf_file = conf_file
        self.config    = configparser.ConfigParser()
        self.load()

    def load(self, conf_file=DEF_CONF_FILE):
        self.logger.debug('conf_file=%s', conf_file)
        self.config.read(self.conf_file)

    def save(self, conf_file=DEF_CONF_FILE):
        self.logger.debug('conf_file=%s', conf_file)
        f = open(conf_file, mode='w')
        self.config.write(f)
        f.close()

    def get_intlist(self, key, section=DEF_SECTION):
        self.logger.debug('')
        int_list = [int(i) for i in self.config[section][key].split()]
        self.logger.debug('int_list=%s', int_list)
        return int_list
    
    def set_intlist(self, key, int_list, section=DEF_SECTION):
        self.logger.debug('key=%s, int_list=%s', key, int_list)
        self.config[section][key] = ' '.join([str(i) for i in int_list])


    def get_pin(self):
        self.logger.debug('')
        return self.get_intlist(KEY_PIN)

    def get_home(self):
        self.logger.debug('')
        return self.get_intlist(KEY_HOME)

    def set_pin(self, v_list):
        self.logger.debug('v_list=%s', v_list)
        self.set_intlist(KEY_PIN, v_list)

    def set_home(self, v_list):
        self.logger.debug('v_list=%s', v_list)
        self.set_intlist(KEY_HOME, v_list)

    def change_home(self, i, v=0):
        self.logger.debug('i=%d, v=%d', i, v)
        hl = self.get_home()
        hl[i] += v
        self.set_home(hl)

#####
class Sample:
    def __init__(self, conf_file='', debug=False):
        self.debug = debug
        self.logger = my_logger.get_logger(__class__.__name__, debug)
        self.logger.debug('conf_file=%s', conf_file)

        self.c = OttoPiConfig(debug=self.debug)

    def main(self):
        self.logger.debug('')
        print(self.c.get_pin())
        print(self.c.get_home())
        self.c.set_intlist('pin', [1 , 2, 3, 4])
        self.c.change_home(1, 10)
        self.c.change_home(2, -10)
        self.c.save()

    def __del__(self):
        self.logger.debug('')
        #self.end()

    def end(self):
        self.logger.debug('')
        self.c.save('a.conf')

#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('conf_file', type=str, default=DEF_CONF_FILE)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(conf_file, debug):
    logger = my_logger.get_logger(__name__, debug)
    logger.debug('conf_file=%s', conf_file)

    obj = Sample(conf_file, debug=debug)
    try:
        obj.main()
    finally:
        logger.debug('finally')
        obj.end()

if __name__ == '__main__':
    main()

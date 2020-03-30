#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#

import telnetlib
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
DEF_HOST = 'localhost'
DEF_PORT = 12349
    
REPLY_READY = '#Ready'
REPLY_OK    = '#OK'

#####
class SpeakClient:
    def __init__(self, svr_host=DEF_HOST, svr_port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)

        self.svr_host = svr_host
        self.svr_port = svr_port

        self.tn = self.open(self.svr_host, self.svr_port)

    def __del__(self):
        self.logger.debug('')
        self.close()

    def open(self, svr_host=DEF_HOST, svr_port=DEF_PORT):
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)
        
        tn = telnetlib.Telnet(self.svr_host, self.svr_port)
        while True:
            in_data = tn.read_some()
            decoded_data = ''
            self.logger.debug('in_data:%a', in_data)
            try:
                decoded_data = in_data.decode('utf-8')
            except UnicodeDecodeError:
                decoded_data = ''
            else:
                self.logger.debug('decoded_data:\"%s\"', decoded_data)

            if REPLY_READY in decoded_data:
                self.logger.info(decoded_data)
                break

        return tn

        
    def close(self):
        self.logger.debug('')
        self.tn.close()

    def speak(self, msg):
        self.logger.debug('msg=%s', msg)

        in_data = self.tn.read_eager()
        self.logger.debug('in_data:%a', in_data)
        try:
            decoded_data = in_data.decode('utf-8')
        except UnicodeDecodeError:
            decoded_data = ''
        else:
            self.logger.debug('decoded_data:\"%s\"', decoded_data)
            
        self.tn.write(msg.encode('utf-8'))

        time.sleep(0.1)

        in_data = self.tn.read_very_eager()
        self.logger.debug('in_data:%a', in_data)
        try:
            decoded_data = in_data.decode('utf-8')
        except UnicodeDecodeError:
            decoded_data = ''
        else:
            self.logger.debug('decoded_data:\"%s\"', decoded_data)


##### Sample
class Sample:
    def __init__(self, host, port, msg_list=[], debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('host=%s, port=%d', host, port)
        self.logger.debug('msg_list=%s', msg_list)

        self.message = ' '.join(msg_list)
        self.logger.debug('message:\'%s\'', self.message)
        self.cl = SpeakClient(host, port, debug=self.debug)

    def main(self):
        if self.message == '':
            tm = time.localtime()
            message = '%s月%s日 %s時%s分' % (tm.tm_mon, tm.tm_mday, tm.tm_hour, tm.tm_min)
            self.logger.info(message)
            self.cl.speak(message)
        else:
            self.cl.speak(self.message)

    def __del__(self):
        self.logger.debug('')
        self.end()

    def end(self):
        self.logger.debug('')
        self.cl.close()

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('message', type=str, nargs=-1)
@click.option('--host', '--server', '-s', 'host', type=str, default="localhost",
              help='server host')
@click.option('--port', '-p', 'port', type=int, default=DEF_PORT,
              help='server port')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(message, host, port, debug):
    logger = get_logger('', debug)
    logger.info('host=%s, port=%d', host, port)
    logger.info('message:%s', message)
    
    obj = Sample(host, port, message, debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()

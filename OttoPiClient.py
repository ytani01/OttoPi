#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
ロボット制御クライアント

OttoPiServerにコマンドを送信する

OttoPiClient -- ロボット制御クライアント
|
|(TCP/IP)
|
OttoPiServer -- ロボット制御サーバ (ネットワーク送受信スレッド)
 |
 +- OttoPiAuto -- ロボットの自動運転 (自動運転スレッド)
 |   |
 +---+- OttoPiCtrl -- コマンド制御 (動作実行スレッド)
         |
         + OttoPiMotion -- 動作定義
            |
            +- PiServo -- 複数サーボの同期制御
            +- OttoPiConfig -- 設定ファイルの読み込み・保存

'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from OttoPiServer import OttoPiServer
import telnetlib
import time

from MyLogger import get_logger


#####
DEF_HOST = 'localhost'
DEF_PORT = 12345
    
#####
class OttoPiClient:
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
        return telnetlib.Telnet(self.svr_host, self.svr_port)
        
    def close(self):
        self.logger.debug('')
        self.tn.close()

    def recv_reply(self):
        self.logger.debug('')

        ret = b''
        
        while True:
            time.sleep(0.1)
            try:
                in_data = self.tn.read_eager()
            except Exception as e:
                self.logger.debug('%s:%s', type(e), e)
                in_data = b''
                
            if len(in_data) == 0:
                break
            self.logger.debug('in_data:%a', in_data)
            ret += in_data

        self.logger.debug('ret=%a', ret)
        return ret

    def send_cmd1(self, cmd):
        self.logger.debug('cmd=%s', cmd)

        try:
            self.tn.write(cmd.encode('utf-8'))
        except Exception as e:
            self.logger.warn('Retry:%s:%s:%s.', cmd, type(e), e)
            self.tn = self.open(self.svr_host, self.svr_port)
            self.tn.write(cmd.encode('utf-8'))
        
        ret = self.recv_reply()
        self.logger.debug('ret=%a', ret)
        ret = ret.decode('utf-8')
        self.logger.info('ret=\'%s\'', ret)

        return ret

    def send_cmd(self, cmd):
        self.logger.debug('cmd=%s, %s', cmd, cmd[0])

        self.recv_reply()

        if cmd[0] == OttoPiServer.CMD_PREFIX:
            ret = self.send_cmd1(cmd)
        else:
            for ch in cmd:
                self.logger.debug('ch=%a(0x%02x)', ch, ord(ch))
                ret = self.send_cmd1(ch)

        return ret

##### Sample
class Sample:
    def __init__(self, svr_host, svr_port, command='', debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)
        self.logger.debug('command=%s', command)

        self.cl = OttoPiClient(svr_host, svr_port, debug=self.debug)
        self.command = command

    def main(self):
        self.logger.debug('command:\'%s\'', self.command)
        
        if self.command != '':
            if self.command[0] == OttoPiServer.CMD_PREFIX:
                self.cl.send_cmd(self.command)
                time.sleep(3)
            else:
                for ch in self.command:
                    self.logger.debug('ch=%a', ch)
                    self.cl.send_cmd(ch)
                    time.sleep(3)

            self.cl.send_cmd(':stop')

        else:
            self.cl.send_cmd(':happy')
            time.sleep(3)
            self.cl.send_cmd(':ojigi')
            time.sleep(3)
            self.cl.send_cmd(':stop')

    def end(self):
        self.logger.debug('')
        self.cl.close()

#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('svr_host', type=str, default="localhost")
@click.argument('svr_port', type=int, default=DEF_PORT)
@click.option('--command', '-c', type=str, default='',
              help='control commands')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(svr_host, svr_port, command, debug):
    logger = get_logger(__name__, debug)
    logger.info('svr_host=%s, svr_port=%d', svr_host, svr_port)
    
    obj = Sample(svr_host, svr_port, command, debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()

#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
"""
ロボット制御クライアント

OttoPiServerにコマンドを送信する

-----------------------------------------------------------------
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
-----------------------------------------------------------------
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from OttoPiServer import OttoPiServer
import telnetlib
import time
import json

from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class OttoPiClient:
    """ OttoPiClient """
    DEF_HOST = 'localhost'
    DEF_PORT = 12345

    def __init__(self, svr_host=DEF_HOST, svr_port=DEF_PORT, debug=False):
        """ init """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, debug)
        self._log.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)

        self.svr_host = svr_host
        self.svr_port = svr_port

        self.tn = self.open(self.svr_host, self.svr_port)

    def __del__(self):
        """ __del__ """
        self._log.debug('')
        self.close()

    def open(self, svr_host=DEF_HOST, svr_port=DEF_PORT):
        """ open """
        self._log.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)
        return telnetlib.Telnet(self.svr_host, self.svr_port)

    def close(self):
        """ close """
        self._log.debug('')
        self.tn.close()

    def recv_reply(self):
        """ recv_reply """
        self._log.debug('')

        buf = b''

        while True:
            time.sleep(0.1)
            try:
                in_data = self.tn.read_eager()
            except Exception as e:
                self._log.debug('%s:%s', type(e), e)
                in_data = b''

            if len(in_data) == 0:
                break

            self._log.debug('in_data:%a', in_data)
            buf += in_data

        self._log.debug('buf=%a', buf)

        try:
            ret_str = buf.decode('utf-8')
        except UnicodeDecodeError:
            if buf == b'':
                ret_str = ''
            else:
                ret_str = str(buf)

        self._log.debug('ret_str=%a', ret_str)

        try:
            ret = json.loads(ret_str)
        except json.decoder.JSONDecodeError:
            ret = {'CMD': '', 'ACCEPT': '', 'MSG': ret_str}

        self._log.debug('ret=%s', ret)

        return ret

    def send_cmd1(self, cmd):
        """ send_cmd1 """
        self._log.debug('cmd=%s', cmd)

        try:
            self.tn.write(cmd.encode('utf-8'))
        except Exception as e:
            self._log.warning('Retry:%s:%s:%s.', cmd, type(e), e)
            self.tn = self.open(self.svr_host, self.svr_port)
            self.tn.write(cmd.encode('utf-8'))

        ret = self.recv_reply()
        self._log.debug('ret=%s', ret)

        return ret

    def send_cmd(self, cmd):
        """ send_cmd """
        self._log.debug('cmd=%s', cmd)

        self.recv_reply()

        if cmd[0] == OttoPiServer.CMD_PREFIX:
            ret = self.send_cmd1(cmd)
        else:
            for ch in cmd:
                self._log.debug('ch=%a(0x%02x)', ch, ord(ch))
                ret = self.send_cmd1(ch)

        return ret


class OttoPiClientApp:
    """ OttoPiClientApp """
    def __init__(self, command, svr_host, svr_port, debug=False):
        """ __init__ """
        self._dbg = debug
        self._log = get_logger(__class__.__name__, debug)
        self._log.debug('command=%s', command)
        self._log.debug('svr_host=%s, svr_port=%d', svr_host, svr_port)

        self.cl = OttoPiClient(svr_host, svr_port, debug=self._dbg)
        self.command = command

    def main(self):
        """ __init__ """
        self._log.debug('command:\'%s\'', self.command)

        for cmd1 in self.command:
            if cmd1[0] == OttoPiServer.CMD_PREFIX:
                ret = self.cl.send_cmd(cmd1)
                print(ret)
            else:
                for ch in cmd1:
                    self._log.debug('ch=%a', ch)
                    ret = self.cl.send_cmd(ch)
                    print(ret)

    def end(self):
        """ end """
        self._log.debug('')
        self.cl.close()


@click.command(context_settings=CONTEXT_SETTINGS,
               help='OttoPiClient')
@click.argument('command', type=str, nargs=-1)
@click.option('--svr_host', '-s', 'svr_host', type=str,
              default=OttoPiClient.DEF_HOST,
              help='server hostname or IP address')
@click.option('--svr_port', '-p', 'svr_port', type=int,
              default=OttoPiClient.DEF_PORT,
              help='server port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(command, svr_host, svr_port, debug):
    """ main """
    _log = get_logger(__name__, debug)
    _log.debug('command=%s, svr_host=%s, svr_port=%d',
               command, svr_host, svr_port)

    obj = OttoPiClientApp(command, svr_host, svr_port, debug=debug)
    try:
        obj.main()
    finally:
        _log.debug('finally')
        obj.end()


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020'
"""
ロボット制御サーバ

ネットワークからコマンド(短縮文字、またはコマンド文字列)を受信し、
ロボットを制御する

自動運転のON/OFF、マニュアル操作が行える。

-----------------------------------------------------------------
OttoPiServer -- ロボット制御サーバ (ネットワーク送受信スレッド)
 |
 +- OttoPiAuto -- ロボットの自動運転 (自動運転スレッド)
 |   |
 +---+- OttoPiCtrl -- コマンド制御 (動作実行スレッド)
         |
         +- OttoPiMotion -- 動作定義
             |
             +- PiServo -- 複数サーボの同期制御
             +- OttoPiConfig -- 設定ファイルの読み込み・保存
-----------------------------------------------------------------
"""

from OttoPiCtrl import OttoPiCtrl
from OttoPiAuto import OttoPiAuto

import pigpio
import socketserver
import time
import json

from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class OttoPiHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self._dbg = server._dbg
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('client_address: %s', client_address)

        self._svr     = server
        self._ctrl = server._ctrl
        self._auto = server._auto

        self.cmd_key = {
            # auto switch commands
            '@': 'auto_on',
            ' ': 'auto_off',

            # robot control commands
            'w': 'forward',
            'q': 'left_forward',
            'e': 'right_forward',
            'x': 'backward',
            'W': 'suriashi_fwd',
            'a': 'turn_left',
            'd': 'turn_right',
            'A': 'slide_left',
            'D': 'slide_right',
            '1': 'happy',
            '2': 'hi_right',
            '3': 'hi_left',
            '4': 'bye_right',
            '5': 'bye_left',
            '6': 'surprised',
            '8': 'ojigi',
            '9': 'ojigi2',
            '0': 'home',

            'h': 'move_up0',
            'H': 'move_down0',
            'j': 'move_up1',
            'J': 'move_down1',
            'k': 'move_up2',
            'K': 'move_down2',
            'l': 'move_up3',
            'L': 'move_down3',

            'u': 'home_up0',
            'U': 'home_down0',
            'i': 'home_up1',
            'I': 'home_down1',
            'o': 'home_up2',
            'O': 'home_down2',
            'p': 'home_up3',
            'P': 'home_down3',

            's': OttoPiCtrl.CMD_STOP,
            'S': OttoPiCtrl.CMD_STOP,
            '' : OttoPiCtrl.CMD_END}

        return super().__init__(request, client_address, server)

    def setup(self):
        self._log.debug('')
        return super().setup()

    def net_write(self, msg):
        self._log.debug('msg=%s', msg)

        try:
            self.wfile.write(msg)
        except BrokenPipeError as e:
            self._log.debug('%s:%s', type(e).__name__, e)
        except Exception as e:
            self._log.warning('%s:%s', type(e).__name__, e)

    def send_reply(self, cmd, accept=True, msg=''):
        self._log.debug('cmd=%s, accept=%s, msg=%s', cmd, accept, msg)

        ret_str = json.dumps({
            'CMD': cmd,
            'ACCEPT': accept,
            'MSG': msg
        })
        self._log.debug('ret_str=%s', ret_str)

        ret = ret_str.encode('utf-8')
        self._log.info('ret=%a', ret)

        self.net_write(ret)

    def handle(self):
        self._log.debug('')

        # Telnet Protocol
        #
        # mode character
        #  0xff IAC
        #  0xfd D0
        #  0x22 LINEMODE
        # self.net_write(b'\xff\xfd\x22')

        self.net_write('#Ready\r\n'.encode('utf-8'))

        net_data = b''
        flag_continue = True
        while flag_continue:
            # データー受信
            try:
                net_data = self.request.recv(512)
            except ConnectionResetError as e:
                self._log.warning('%s:%s.', type(e), e)
                return
            except BaseException as e:
                self._log.warning('BaseException:%s:%s.', type(e), e)
                self._log.warning('send: OttoPiCtrl.CMD_STOP')
                self._ctrl.send(OttoPiCtrl.CMD_STOP)
                return
            else:
                self._log.debug('net_data:%a', net_data)

            # デコード(UTF-8)
            try:
                decoded_data = net_data.decode('utf-8')
            except UnicodeDecodeError as e:
                self._log.warning('%s:%s .. ignored', type(e), e)
                continue
            else:
                self._log.debug('decoded_data:%a', decoded_data)

            self.net_write('\r\n'.encode('utf-8'))

            # 文字列抽出(コントロールキャラクター削除)
            data = ''
            for ch in decoded_data:
                if ord(ch) >= 0x20:
                    data += ch
            self._log.debug('data=%a', data)

            if len(data) == 0:
                msg = 'No data .. disconnect'
                self._log.warning(msg)
                self.net_write((msg + '\r\n').encode('utf-8'))
                break

            # 制御スレッドが動いていない場合は(異常終了など?)、再起動
            if not self._ctrl.is_active():
                self._log.warning('robot control thread is dead !? .. restart')
                self._svr._ctrl = OttoPiCtrl(self._svr._pi,
                                             debug=self._svr._dbg)

                self._ctrl = self._svr._ctrl
                self._ctrl.start()

            # 自動運転スレッドが動いていない場合は(異常終了など?)、再起動
            if not self._auto.is_active():
                self._log.warning('auto control thread is dead !? .. restart')
                self._svr._auto = OttoPiAuto(self._ctrl, debug=self._svr._dbg)

                self._auto = self._svr._auto
                self._auto.start()

            # word command
            if data[0] == OttoPiServer.CMD_PREFIX:
                cmd = data[1:]
                interrupt_flag = True

                if data[1] == OttoPiServer.CMD_PREFIX2:
                    cmd = data[2:]
                    interrupt_flag = False

                cmd_name = cmd.split()[0]

                self._log.info('cmd=%s, cmd_name=%s, interrupt_flag=%s',
                               cmd, cmd_name, interrupt_flag)

                if cmd.startswith(OttoPiServer.CMD_AUTO_PREFIX):
                    """
                    auto command

                    注意
                    ----
                    auto commandは、回数パラメータがないため、
                    cmd_nameだけをsendする。

                    """
                    auto_cmd = cmd.replace(OttoPiServer.CMD_AUTO_PREFIX, '')
                    cmd_name = cmd_name.replace(OttoPiServer.CMD_AUTO_PREFIX,
                                                '')
                    self._log.info('auto_cmd=%s, cmd_name=%s',
                                   auto_cmd, cmd_name)

                    if cmd_name in self._auto.cmd_func.keys():
                        d = self._auto.send(cmd_name)
                        self._log.info('d=%smm', '{:,}'.format(d))

                        self.send_reply(data, True, {'d': d})
                    else:
                        self._log.warning('%s: invalid auto command', auto_cmd)
                        self.send_reply(data, False, 'invalid auto command')
                else:
                    """
                    control command
                    """
                    if cmd_name in self._ctrl.cmd_func.keys():
                        self._ctrl.send(cmd, interrupt_flag)
                        self.send_reply(data, True, '')
                    else:
                        msg = 'invalid control command'
                        self._log.warning('%s: %s', cmd, msg)
                        self.send_reply(data, False, msg)

                continue

            # one-key command
            for ch in data:
                self._log.info('ch=%a', ch)

                if ch not in self.cmd_key.keys():
                    self._ctrl.send(OttoPiCtrl.CMD_STOP)
                    self._log.warning('invalid 1-key command:%a .. stop', ch)
                    self.send_reply(ch, False, 'invalid 1-key command')
                    continue

                cmd = self.cmd_key[ch]
                self._log.info('cmd=%s', cmd)

                if cmd.startswith(OttoPiServer.CMD_AUTO_PREFIX):
                    # auto command
                    auto_cmd = cmd.replace(OttoPiServer.CMD_AUTO_PREFIX, '')
                    self._log.info('auto_cmd=%s', auto_cmd)

                    self._auto.send(auto_cmd)
                    self.send_reply('%s(%s)' % (ch, cmd), True, '')

                else:
                    # control command
                    self._ctrl.send(cmd)
                    self.send_reply('%s(%s)' % (ch, cmd), True, '')

        self._log.debug('done')

    def finish(self):
        self._log.debug('')
        return super().finish()


class OttoPiServer(socketserver.ThreadingTCPServer):
    DEF_PORT = 12345
    CMD_PREFIX = ':'
    CMD_PREFIX2 = '.'
    CMD_AUTO_PREFIX = 'auto_'

    def __init__(self, pi=None, port=DEF_PORT, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, debug)
        self._log.debug('pi=%s, port=%s', pi, port)

        if type(pi) == pigpio.pi:
            self._pi   = pi
            self._mypi = False
        else:
            self._pi   = pigpio.pi()
            self._mypi = True
        self._log.debug('mypi = %s', self._mypi)

        self._ctrl = OttoPiCtrl(self._pi, debug=self._dbg)
        self._ctrl.start()

        self._auto = OttoPiAuto(self._ctrl, debug=self._dbg)
        self._auto.start()

        time.sleep(1)

        self._port  = port

        try:
            super().__init__(('', self._port), OttoPiHandler)
        except Exception as e:
            self._log.warning('%s:%s', type(e).__name__, e)
            return None

    def serve_forever(self):
        self._log.debug('')
        return super().serve_forever()

    def end(self):
        self._log.debug('')

        if self._auto.is_active():
            self._auto.end()
            self._log.debug('_auto thread: done')

        if self._ctrl.is_active():
            self._ctrl.end()
            self._log.debug('_ctrl thread: done')

        if self._mypi:
            self._log.debug('clean up pigpio')
            self._pi.stop()
            self._mypi = False

        self._log.debug('done')

    def _del_(self):
        self._log.debug('')
        self.end()


class OttoPiServerApp:
    def __init__(self, port, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, debug)
        self._log.debug('port=%d', port)

        self._port = port
        self._svr = OttoPiServer(None, self._port, debug=self._dbg)

    def main(self):
        self._log.debug('')
        self._log.debug('start server')
        self._svr.serve_forever()

    def end(self):
        self._log.debug('')
        self._svr.end()
        self._log.debug('done')


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('port', type=int, default=OttoPiServer.DEF_PORT)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, debug):
    _log = get_logger(__name__, debug)
    _log.info('port=%d', port)

    obj = OttoPiServerApp(port, debug=debug)
    try:
        obj.main()
    finally:
        _log.info('finally')
        obj.end()


if __name__ == '__main__':
    main()

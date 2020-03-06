#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'
'''
ロボット制御サーバ

ネットワークからコマンド(短縮文字、またはコマンド文字列)を受信し、
ロボットを制御する

自動運転のON/OFF、マニュアル操作が行える。

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

from OttoPiCtrl import OttoPiCtrl
from OttoPiAuto import OttoPiAuto

import pigpio
import socketserver
import time

from MyLogger import get_logger


#####
class OttoPiHandler(socketserver.StreamRequestHandler):
    def __init__(self, request, client_address, server):
        self.debug = server.debug
        self.logger = get_logger(__class__.__name__, self.debug)
        self.logger.debug('client_address: %s', client_address)
        
        self.server     = server
        self.robot_ctrl = server.robot_ctrl
        self.robot_auto = server.robot_auto

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
            '2': 'hi',
            '3': 'supprized',
            '4': 'ojigi',
            '5': 'ojigi2',
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

            '.': 'null',
            
            's': OttoPiCtrl.CMD_STOP,
            'S': OttoPiCtrl.CMD_STOP,
            '' : OttoPiCtrl.CMD_END}

        return super().__init__(request, client_address, server)

    def setup(self):
        self.logger.debug('')
        return super().setup()

    def net_write(self, msg):
        self.logger.debug('msg=%s', msg)
        try:
            self.wfile.write(msg)
        except:
            pass

    def send_reply(self, cmd, ok=True):
        self.logger.debug('')

        line = '#CMD ' + cmd + '\r\n'
        self.net_write(line.encode('utf-8'))

        line = '#STAT ' + self.robot_auto.stat + '\r\n'
        self.net_write(line.encode('utf-8'))

        line = '#AUTO ' + str(self.robot_auto.on) + '\r\n'
        self.net_write(line.encode('utf-8'))

        self.net_write('#OK\r\n'.encode('utf-8'))
        

    def cmd_null(self):
        self.logger.debug('')
        

    def handle(self):
        self.logger.debug('')
        
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
                self.logger.warn('%s:%s.', type(e), e)
                return
            except BaseException as e:
                self.logger.warn('BaseException:%s:%s.', type(e), e)
                self.logger.warn('send: CootPiCtrl.CMD_STOP')
                self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)
                return
            else:
                self.logger.debug('net_data:%a', net_data)

            # デコード(UTF-8)
            try:
                decoded_data = net_data.decode('utf-8')
            except UnicodeDecodeError as e:
                self.logger.warning('%s:%s .. ignored', type(e), e)
                continue
            else:
                self.logger.info('decoded_data:%a', decoded_data)

            self.net_write('\r\n'.encode('utf-8'))
            
            # 文字列抽出(コントロールキャラクター削除)
            data = ''
            for ch in decoded_data:
                if ord(ch) >= 0x20:
                    data += ch
            self.logger.info('data=%a', data)
            if len(data) == 0:
                self.logger.debug('No data .. disconnect')
                self.net_write('No data .. disconnect\r\n'.encode('utf-8'))
                break

            # 制御スレッドが動いていない場合は(異常終了など?)、再起動
            if not self.robot_ctrl.is_alive():
                self.logger.warn('robot control thread is dead !? .. restart')
                self.server.robot_ctrl = OttoPiCtrl(self.server.pi,
                                                    debug=self.server.debug)
                self.robot_ctrl = self.server.robot_ctrl
                self.robot_ctrl.start()

            # ダイレクトコマンド
            self.logger.info('%s,%s.', data[0], OttoPiServer.CMD_PREFIX)
            if data[0] == OttoPiServer.CMD_PREFIX:
                cmd = data[1:]
                interrupt_flag = True

                if data[1] == OttoPiServer.CMD_PREFIX2:
                    cmd = data[2:]
                    interrupt_flag = False
                
                self.logger.info('cmd=%s, interrupt_flag=%s',
                                 cmd, interrupt_flag)

                self.send_reply(cmd)

                if cmd.startswith('auto_on'):
                    self.robot_auto.send('on')
                elif cmd.startswith('auto_off'):
                    self.robot_auto.send('off')
                else:
                    self.robot_ctrl.send(cmd, interrupt_flag)
                continue
                
            # ワンキーコマンド
            for ch in data:
                self.logger.info('ch=%a', ch)

                if not ch in self.cmd_key.keys():
                    self.robot_ctrl.send(OttoPiCtrl.CMD_STOP)
                    self.logger.debug('invalid command:\'%a\' .. stop', ch)
                    self.net_write('#NG .. stop\r\n'.encode('utf-8'))
                    continue

                cmd = self.cmd_key[ch]
                self.logger.debug('command:%s', cmd)

                self.send_reply(cmd)

                if cmd.startswith('auto_on'):
                    self.robot_auto.send('on')
                elif cmd.startswith('auto_off'):
                    self.robot_auto.send('off')
                elif cmd.startswith('null'):
                    self.cmd_null()
                else:
                    self.robot_ctrl.send(cmd)

        self.logger.debug('done')
        
    def finish(self):
        self.logger.debug('')
        return super().finish()
    

class OttoPiServer(socketserver.ThreadingTCPServer):
    DEF_PORT = 12345
    CMD_PREFIX = ':'
    CMD_PREFIX2 = '.'

    def __init__(self, pi=None, port=DEF_PORT, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('pi   = %s', pi)
        self.logger.debug('port = %d', port)

        if type(pi) == pigpio.pi:
            self.pi   = pi
            self.mypi = False
        else:
            self.pi   = pigpio.pi()
            self.mypi = True
        self.logger.debug('mypi = %s', self.mypi)

        self.robot_ctrl = OttoPiCtrl(self.pi, debug=self.debug)
        self.robot_ctrl.start()

        self.robot_auto = OttoPiAuto(self.robot_ctrl, debug=self.debug)
        self.robot_auto.start()

        time.sleep(1)

        self.port  = port

        try:
            super().__init__(('', self.port), OttoPiHandler)
        except:
            return None

    def serve_forever(self):
        self.logger.debug('')
        return super().serve_forever()

    def end(self):
        self.logger.debug('')

        if self.robot_auto.is_alive():
            self.robot_auto.end()
            self.logger.debug('robot_auto thread: done')

        if self.robot_ctrl.is_alive():
            self.robot_ctrl.end()
            self.logger.debug('robot_ctrl thread: done')

        if self.mypi:
            self.logger.debug('clean up pigpio')
            self.pi.stop()
            self.mypi = False
            
        self.logger.debug('done')
        
    def _del_(self):
        self.logger.debug('')
        self.end()
        
#####
class Sample:
    def __init__(self, port, debug=False):
        self.debug = debug
        self.logger = get_logger(__class__.__name__, debug)
        self.logger.debug('port=%d', port)

        self.port   = port
        self.server = OttoPiServer(None, self.port, debug=self.debug)
        
    def main(self):
        self.logger.debug('')
        self.logger.debug('start server')
        self.server.serve_forever()
        
    def end(self):
        self.logger.debug('')
        self.server.end()
        self.logger.debug('done')
        
        
#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('port', type=int, default=OttoPiServer.DEF_PORT)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(port, debug):
    logger = get_logger(__name__, debug)
    logger.info('port=%d', port)

    obj = Sample(port, debug=debug)
    try:
        obj.main()
    finally:
        logger.info('finally')
        obj.end()

if __name__ == '__main__':
    main()

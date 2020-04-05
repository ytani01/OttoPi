#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
ロボットBLEサーバー

BLEでコマンドを受信し、OttoPiServerにコマンドを中継する

-----------------------------------------------------------------
OttoPiBleServer -- ロボットBLEサーバー
 |
 +- OttoPiClient -- ロボット制御クライアント
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
__data__   = '2020'

from OttoPiClient import OttoPiClient
from BlePeripheral import BlePeripheral, BleService, BleCharacteristic
from BlePeripheral import BlePeripheralApp
import json

from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class OttoPiBleServer(BlePeripheral):
    MY_NAME = 'OttoPi'
    DEF_ROBOT_PORT = 12345

    _log = get_logger(__name__, False)

    def __init__(self, robot_host='localhost', robot_port=DEF_ROBOT_PORT,
                 name=MY_NAME, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('name=%s', name)
        self._log.debug('robot_host=%s, robot_port=%s', robot_host, robot_port)

        self._name = name
        self._robot_host = robot_host
        self._robot_port = robot_port

        self._chara_resp = RespCharacteristic(debug=self._dbg)
        self._chara_cmd = CmdCharacteristic(self._robot_host, self._robot_port,
                                            self._chara_resp,
                                            debug=self._dbg)

        self._svc = OttoPiService(charas=[self._chara_cmd, self._chara_resp],
                                  debug=self._dbg)

        super().__init__(self._name, [self._svc], debug=self._dbg)


class OttoPiService(BleService):
    UUID = '4e769f72-391f-4cd3-bbea-25a2e945066b'

    _log = get_logger(__name__, False)

    def __init__(self, uuid=UUID, charas=[], debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s', uuid)

        super().__init__(uuid, charas, debug=self._dbg)


class CmdCharacteristic(BleCharacteristic):
    UUID = '70e45870-79ec-44c6-859d-0897aa7134b6'

    _log = get_logger(__name__, False)

    def __init__(self, robot_host, robot_port, chara_resp,
                 uuid=UUID, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('robot_host=%s, robot_port=%s', robot_host, robot_port)
        self._log.debug('chara_resp=<%s>', chara_resp._uuid)
        self._log.debug('uuid=%s', uuid)

        self._robot_host = robot_host
        self._robot_port = robot_port
        self._chara_resp = chara_resp

        super().__init__(uuid, ['write', 'read', 'notify'], debug=debug)

    def onWriteRequest(self, data, offset, withoutRespoinse, callback):
        self._log.debug('data=%a', data)

        super().onWriteRequest(data, offset, withoutRespoinse, callback)

        cmd = data.decode('utf-8')
        self._log.debug('cmd=%a', cmd)

        robot_client = OttoPiClient(self._robot_host, self._robot_port,
                                    debug=False)
        ret = robot_client.send_cmd(cmd)
        self._log.debug('ret=%s', ret)

        robot_client.close()

        self._chara_resp._value = bytearray(json.dumps(ret).encode('utf-8'))
        self._log.debug('_chara_resp._value=%s', self._chara_resp._value)

        if self._chara_resp._updateValueCallback:
            self._chara_resp._updateValueCallback(self._chara_resp._value)

        self._log.debug('done')


class RespCharacteristic(BleCharacteristic):
    UUID = '79394316-6874-4506-9c20-1245751c6c20'

    _log = get_logger(__name__, False)

    def __init__(self, uuid=UUID, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s', uuid)

        super().__init__(uuid, ['read', 'notify'], debug=debug)

        self._updateValueCallback = None

    def onSubscribe(self, maxValueSize, updateValueCallback):
        self._log.debug('maxValueSize=%s', maxValueSize)
        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):
        self._log.debug('')
        self._updateValueCallback = None


class OttoPiBleServerApp(BlePeripheralApp):
    def __init__(self, robot_svr, robot_port, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('')

        self._ble = OttoPiBleServer(robot_svr, robot_port, debug=self._dbg)


@click.command(context_settings=CONTEXT_SETTINGS, help='')
@click.option('--robot_svr', '-s', 'robot_svr', type=str, default='localhost',
              help='robot server hosstname')
@click.option('--robot_port', '-p', 'robot_port', type=int, default=12345,
              help='robot server port number')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(robot_svr, robot_port, debug):
    log = get_logger(__name__, debug)

    app = OttoPiBleServerApp(robot_svr, robot_port, debug=debug)
    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.info('done')


if __name__ == '__main__':
    main()

#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
from OttoPiClient import OttoPiClient
from BlePeripheral import BlePeripheral, BleService, BleCharacteristic
from BlePeripheral import BlePeripheralApp
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
    UUID = 'ec00'

    _log = get_logger(__name__, False)

    def __init__(self, uuid=UUID, charas=[], debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s', uuid)

        super().__init__(uuid, charas, debug=self._dbg)


class CmdCharacteristic(BleCharacteristic):
    UUID = 'ec0E'

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
        
        super().__init__(uuid, ['write'], debug=debug)

    def onWriteRequest(self, data, offset, withoutRespoinse, callback):
        self._log.debug('data=%a', data)

        super().onWriteRequest(data, offset, withoutRespoinse, callback)

        cmd = data.decode('utf-8')
        self._log.debug('cmd=%a', cmd)
        
        robot_client = OttoPiClient(self._robot_host, self._robot_port,
                                    debug=False)
        ret = robot_client.send_cmd(cmd)
        self._log.debug('ret=%a', ret)

        robot_client.close()

        ret_cmd = ''
        ret_result = ''
        for line in ret.split('\r\n'):
            if line.startswith('#CMD'):
                ret_cmd = line
            if line == '#OK' or line == '#NG':
                ret_result = line

        ret1 = ret_cmd + ' ' + ret_result
        self._log.debug('ret1=%a', ret1)

        self._chara_resp._value = bytearray(ret1.encode('utf-8'))
        self._log.debug('_chara_resp._value=%s', self._chara_resp._value)

        self._log.debug('done')


class RespCharacteristic(BleCharacteristic):
    UUID = 'ec0F'

    _log = get_logger(__name__, False)

    def __init__(self, uuid=UUID, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s', uuid)

        super().__init__(uuid, ['read', 'notify'], debug=debug)


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

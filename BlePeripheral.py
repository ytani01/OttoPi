#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
# usage:
#   sudo ./BlePeripheraral.py myname -d
#

from pybleno import Bleno, BlenoPrimaryService, Characteristic
import time
from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class BlePeripheral:
    ADTYPE_FLAGS = 0x01
    ADTYPE_COMPLETE_LIST_16BIT_SVC = 0x03
    ADTYPE_COMPLETE_LIST_128BIT_SVC = 0x07
    ADTYPE_SHORTENED_LOCAL_NAME = 0x08
    ADTYPE_COMPLETE_LOCAL_NAME = 0x09
    ADTYPE_MANUFACTURER_SPCIFIC_DATA = 0xff

    """
    BLE Peripheral
    """
    _log = get_logger(__name__, False)

    def __init__(self, name, svcs=[], ms_data=None, debug=False):
        """
        Parameters
        ----------
        name: str
        svcs: list[BleService]
        ms_data: bytes
        """
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('name=%s, svcs=%s, ms_data=%a',
                        name, [ s.UUID for s in svcs ], ms_data)

        self._name = name
        self._svcs = svcs
        self._ms_data = ms_data

        self._bleno = Bleno()
        self._bleno.on('stateChange', self.onStateChange)
        self._bleno.on('advertisingStart', self.onAdvertisingStart)
        # self._bleno.on('servicesSet', self.onServicesSet)
        # self._bleno.on('accept', self.onAccept)
        # self._bleno.on('disconnect', self.onDisconnect)
        # self._bleno.on('rssiUpdate', self.onRssiUpdate)

        self._address = None
        self._log.debug('_address=%s', self._address)

    def start(self):
        self._log.debug('')
        self._bleno.start()

    def end(self):
        self._log.debug('')
        self._bleno.stopAdvertising()
        self._bleno.disconnect()
        self._log.debug('done')

    def startAdvertising(self, name, svcs, ms_data):
        """
        Advertise ..
        - Flags
        - Complete Local Name (not Shortened Local Name)
        - Services


        Parameters
        ----------
        name: str
        svcs: list[BleService]
        ms_data: bytes (b'...')
        """
        self._log.debug('name=%s, ms_data=%a', name, ms_data)

        # Flags
        ad_flags = bytearray(3)
        ad_flags[0] = 2     # length
        ad_flags[1] = self.ADTYPE_FLAGS
        ad_flags[2] = 0x06  # <LE General Discoverable Mode> |
        #                     <BR/EDR Not Supported>

        # Shortened Local Name
        ad_sl_name = bytearray(b'  ' + name.encode('utf-8'))
        ad_sl_name[0] = len(self._name) + 1
        ad_sl_name[1] = self.ADTYPE_SHORTENED_LOCAL_NAME

        # Complete Local Name
        ad_cl_name = bytearray(b'  ' + name.encode('utf-8'))
        ad_cl_name[0] = len(self._name) + 1
        ad_cl_name[1] = self.ADTYPE_COMPLETE_LOCAL_NAME

        # Service UUIDs
        ad_svc16 = bytearray(b'')
        ad_svc128 = bytearray(b'')
        svc16 = bytearray(b'')
        svc128 = bytearray(b'')
        for s in svcs:
            uuid1 = s.UUID.replace('-', '')
            self._log.debug('uuid1=%s', uuid1)
            uuid_rev = [
                int(uuid1[i:i+2], 16) for i in range(0, len(uuid1), 2)
            ][::-1]
            self._log.debug('uuid_rev=%s', uuid_rev)

            if len(uuid1) == 4:  # 16-bit Service UUID
                svc16 += bytearray(uuid_rev)

            if len(uuid1) == 32:  # 128-bit Service UUID
                svc128 += bytearray(uuid_rev)

        self._log.debug('svc16=%s', svc16)
        self._log.debug('svc128=%s', svc128)

        if len(svc16) > 0:
            ad_svc16 = bytearray(b'  ' + svc16)
            ad_svc16[0] = len(svc16) + 1
            ad_svc16[1] = self.ADTYPE_COMPLETE_LIST_16BIT_SVC

            self._log.debug('ad_svc16=%s', ad_svc16)

        if len(svc128) > 0:
            ad_svc128 = bytearray(b'  ' + svc128)
            ad_svc128[0] = len(svc128) + 1
            ad_svc128[1] = self.ADTYPE_COMPLETE_LIST_128BIT_SVC

            self._log.debug('ad_svc128=%s', ad_svc16)

        ad_svcs = ad_svc16 + ad_svc128

        # Manufacturer Specific Data
        ad_ms_data = b''
        if ms_data is not None:
            if len(ms_data) > 0:
                ad_ms_data = bytearray(b'  ' + ms_data)
                ad_ms_data[0] = len(ms_data) + 1
                ad_ms_data[1] = 0xff

        #
        # Advertisement Data
        #
        advertisementData = ad_flags
        # advertisementData += ad_sl_name + ad_cl_name
        advertisementData += ad_cl_name
        advertisementData += ad_svcs + ad_ms_data
        self._log.debug('advertisementData=(%d)%s',
                        len(advertisementData), advertisementData)

        # Scan Data (exactly same as Advertisement Data)
        scanData = ad_cl_name + ad_svcs

        self._bleno.startAdvertisingWithEIRData(advertisementData, scanData)

    def onStateChange(self, state):
        self._log.debug('state=%s', state)

        uuids = [u.UUID for u in self._svcs]
        self._log.debug('service uuids=%s', uuids)

        if (state == 'poweredOn'):
            # reverse MAC address
            self._address = ':'.join(
                self._bleno.address.split(':')[::-1]
            )
            self._log.debug('_address=%s', self._address)

            """
            self._log.info('start Advertising(%s) ..', self._name)
            self._bleno.startAdvertising(self._name, uuids)
            """
            self.startAdvertising(self._name, self._svcs, self._ms_data)
        else:
            self._log.info('stop Advertising ..')
            self._bleno.stopAdvertising()

    def onAdvertisingStart(self, error):
        self._log.debug('error=%s', error)

        if not error:
            self._log.debug('setService:%s', [s.uuid for s in self._svcs])
            self._bleno.setServices(self._svcs)

    """
    def onServicesSet(self, error):
        self._log.debug('error=%s', error)

    def onAccept(self, client):
        self._log.debug('client=%s', client)

    def onDisconnect(self, client):
        self._log.debug('client=%s', client)

    def onRssiUpdate(self, rssi):
        self._log.debug('rssi=%s')
    """


class BleService(BlenoPrimaryService):
    _log = get_logger(__name__, False)

    def __init__(self, uuid, charas=[], debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s', uuid)
        self._log.debug('charas=%s', [ c._uuid for c in charas])

        self._uuid = uuid
        self._charas = charas

        super().__init__({
            'uuid': self._uuid,
            'characteristics': self._charas
        })


class BleCharacteristic(Characteristic):
    _log = get_logger(__name__, False)

    def __init__(self, uuid, properties=[], debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('uuid=%s, properties=%s', uuid, properties)

        self._uuid = uuid
        self._properties = properties

        super().__init__({
            'uuid': self._uuid,
            'properties': self._properties,
            'value': None
        })

        self._value = bytearray(''.encode('utf-8'))
        self._updateValueCallback = None

    def onReadRequest(self, offset, callback):
        self._log.debug('offset=%s', offset)
        self._log.debug('_value=%a', self._value)

        ret = self._value[offset:]
        self._log.info('ret=%a', ret)

        callback(Characteristic.RESULT_SUCCESS, ret)

    def onWriteRequest(self, data, offset, withoutResponse, callback):
        self._log.debug('data=%s, offset=%s, withoutResponse=%s',
                        data, offset, withoutResponse)

        self._value = data[offset:]
        self._log.info('_value=%s', self._value)

        if self._updateValueCallback:
            self._log.info('notifying: %s ..', self._value)
            self._updateValueCallback(self._value)

        callback(Characteristic.RESULT_SUCCESS)

    def onSubscribe(self, maxValueSize, updateValueCallback):
        self._log.debug('maxValueSize=%s', maxValueSize)
        self._log.debug('updateValueCallback=%s', updateValueCallback)
        self._updateValueCallback = updateValueCallback

    def onUnsubscribe(self):
        self._log.debug('')
        self._updateValueCallback = None


class BlePeripheralApp:
    _log = get_logger(__name__, False)

    def __init__(self, name, ms_data, debug=False):
        self._dbg = debug
        self._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('name=%s, ms_data=%a', name, ms_data)

        self._name = name
        self._ms_data = ms_data

        self._ble = BlePeripheral(self._name, [], self._ms_data,
                                  debug=self._dbg)

    def main(self):
        self._log.debug('')

        self._ble.start()

        while True:
            time.sleep(10)

    def end(self):
        self._log.debug('')
        self._ble.end()
        self._log.debug('done')


@click.command(context_settings=CONTEXT_SETTINGS, help='')
@click.argument('name', type=str)
@click.argument('ms_data', type=str)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(name, ms_data, debug):
    log = get_logger(__name__, debug)

    app = BlePeripheralApp(name, ms_data.encode('utf-8'), debug=debug)
    try:
        app.main()
    finally:
        log.debug('finally')
        app.end()
        log.info('done')


if __name__ == '__main__':
    main()

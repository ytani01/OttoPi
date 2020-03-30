#!/usr/bin/env python3
#
# (c) 2020 Yoichi Tanibayashi
#
"""
Description
"""
__author__ = 'Yoichi Tanibayashi'
__date__   = '2020'

import os
import netifaces
import time
from MyLogger import get_logger
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])


class IpAddr:
    _log = get_logger(__name__, False)

    def __init__(self, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('')

        self._addrs = {}

    def get_ipaddr(self):
        self.get_addrs()

        if len(self._addrs) == 0:
            return None

        ifname = list(self._addrs.keys())[0]
        self._log.debug('ifname=%s', ifname)

        if len(self._addrs[ifname]['ip']) == 0:
            return None

        ipaddr = self._addrs[ifname]['ip'][0]
        self._log.debug('ipaddr=%s', ipaddr)

        return ipaddr

    def get_addrs(self):
        """
        Returns
        -------
        addrs: list
            {
                'if0': {
                    'mac': [mac_addr, ..],
                    'ip': [ip_addr, .. ]
                },
                :
            }
        """
        addrs = {}

        for if_name in netifaces.interfaces():
            self._log.debug('if_name=%s', if_name)

            if if_name == 'lo':
                continue

            addrs[if_name] = {'mac': [], 'ip': []}

            ifaddrs = netifaces.ifaddresses(if_name)

            # MAC address
            macs = ifaddrs[netifaces.AF_LINK]
            for m in macs:
                addrs[if_name]['mac'].append(m['addr'])

            # IP address
            try:
                ips = ifaddrs[netifaces.AF_INET]
            except KeyError:
                ips = []

            for ip in ips:
                addrs[if_name]['ip'].append(ip['addr'])

        self._log.debug('addrs=%s', addrs)
        self._addrs = addrs
        return self._addrs


class IpAddrApp:
    _log = get_logger(__name__, False)

    def __init__(self, debug=False):
        self._dbg = debug
        __class__._log = get_logger(__class__.__name__, self._dbg)
        self._log.debug('')

        self._ipaddr = IpAddr(debug=self._dbg)

    def main(self):
        self._log.debug('')

        while True:
            ipaddr = self._ipaddr.get_ipaddr()
            self._log.debug('ipaddr=%s', ipaddr)
            if ipaddr is not None:
                break

            self._log.warning('sleep to retry ..')
            time.sleep(2)

        print(ipaddr)

        self._log.debug('done')

    def end(self):
        self._log.debug('')

        self._log.debug('done')


@click.command(context_settings=CONTEXT_SETTINGS, help='''
Description
''')
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(debug):
    _log = get_logger(__name__, debug)
    _log.debug('')

    app = IpAddrApp(debug=debug)
    try:
        app.main()
    finally:
        _log.debug('finally')
        app.end()


if __name__ == '__main__':
    main()

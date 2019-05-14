#!/usr/bin/env python3
#
from flask import Flask, render_template, request
from OttoPiClient import OttoPiClient

import netifaces
import sys
import os

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
MyName = os.path.basename(sys.argv[0])

app = Flask(__name__)

DEF_HOST = 'localhost'
DEF_PORT = 12345

Flag_Video = 'off'

RobotHost = DEF_HOST
RobotPort = DEF_PORT

#####
def get_ipaddr():
    for if_name in netifaces.interfaces():
        if if_name == 'lo':
            continue

        print(if_name)
        
        addrs = netifaces.ifaddresses(if_name)
        print(addrs)

        try:
            ip = addrs[netifaces.AF_INET]
        except(KeyError):
            continue
        print(ip)

        return ip[0]['addr']

    return ''

def index0(video_sw):
    ipaddr = get_ipaddr()
    return render_template('index.html', ipaddr=ipaddr, video=video_sw)
    
#####
@app.route('/')
def index():
    return index0('off')

@app.route('/video')
def video_movde():
    return index0('on')
        
@app.route('/action', methods=['POST'])
def action():
    global RobotHost, RobotPort
    
    if request.method != 'POST':
        return

    cmd = str(request.form['cmd'])
    #print(MyName + ': cmd = \'' + cmd + '\'')

    rc = OttoPiClient(RobotHost, RobotPort)
    rc.send_cmd(cmd)
    rc.close()

    return ''
    

#####
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('robot_host', type=str, default=DEF_HOST)
@click.argument('robot_port', type=int, default=DEF_PORT)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(robot_host, robot_port, debug):
    global RobotHost, RobotPort

    logger = get_logger('', debug)
    logger.info('robot_host=%s, robot_port=%d', robot_host, robot_port)

    RobotHost = robot_host
    RobotPort = robot_port

    try:
        app.run(host='0.0.0.0', debug=debug)
    finally:
        logger.info('finally')
    
if __name__ == '__main__':
    main()
    

#!/usr/bin/env python3
#
# (c) 2019 Yoichi Tanibayashi
#
'''
ロボット制御Webインタフェース

Web経由で入力を受信し、OttoPiServerにコマンドを送信する

OttoPiHttpServer -- ロボットWebインタフェース
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
'''
__author__ = 'Yoichi Tanibayashi'
__date__   = '2019'

from flask import Flask, render_template, request
from OttoPiClient import OttoPiClient
from SpeakClient import SpeakClient

import netifaces
import sys
import os

#####
from MyLogger import MyLogger
my_logger = MyLogger(__file__)

#####
MyName = os.path.basename(sys.argv[0])

SpeechStopFile = '/home/pi/speech_stop'
MusicStopFile = '/home/pi/music_stop'

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
    Flag_Video = video_sw
    return render_template('index.html', ipaddr=ipaddr, video=video_sw)
    
#####
@app.route('/')
def index():
    return index0('off')

@app.route('/video')
def video_mode():
    return index0('on')
        
@app.route('/action', methods=['POST'])
def action():
    global RobotHost, RobotPort
    
    if request.method != 'POST':
        return

    cmd = str(request.form['cmd'])
    print(MyName + ': cmd = \'' + cmd + '\'')

    rc = OttoPiClient(RobotHost, RobotPort)
    rc.send_cmd(cmd)
    rc.close()

    return ''
    
@app.route('/speak', methods=['POST'])
def speak():
    print('speak():request=%s' % request)
    if request.method != 'POST':
        return

    msg = request.form['msg']
    print('msg = %s' % msg)
    sc = SpeakClient()
    sc.speak(msg)
    sc.close()

    return index0(Flag_Video)
    #return ''

@app.route('/speech', methods=['POST'])
def speech():
    print('speech():request=%s' % request)
    if request.method != 'POST':
        return

    onoff = request.form['onoff']
    print('onoff = %s' % onoff)

    if os.path.isfile(SpeechStopFile):
        print('remove: %s' % SpeechStopFile)
        print(os.remove(SpeechStopFile))

    if onoff != 'on':
        f = open(SpeechStopFile, 'w')
        f.close()

    return ''

@app.route('/music', methods=['POST'])
def music():
    print('music():request=%s' % request)
    if request.method != 'POST':
        return

    onoff = request.form['onoff']
    print('onoff = %s' % onoff)

    if os.path.isfile(MusicStopFile):
        print('remove: %s' % MusicStopFile)
        print(os.remove(MusicStopFile))

    if onoff != 'on':
        f = open(MusicStopFile, 'w')
        f.close()

    return ''


#####
import click
CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'])
@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('robot_host', type=str, default=DEF_HOST)
@click.argument('robot_port', type=int, default=DEF_PORT)
@click.option('--debug', '-d', 'debug', is_flag=True, default=False,
              help='debug flag')
def main(robot_host, robot_port, debug):
    global RobotHost, RobotPort

    logger = my_logger.get_logger('', debug)
    logger.info('robot_host=%s, robot_port=%d', robot_host, robot_port)

    RobotHost = robot_host
    RobotPort = robot_port

    try:
        app.run(host='0.0.0.0', debug=debug)
    finally:
        logger.info('finally')
    
if __name__ == '__main__':
    main()

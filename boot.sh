#!/bin/sh
#
# (c) 2020 Yoichi Tanibayashi
#
MYNAME=`basename $0`
MYDIR=`dirname $0`

LOGDIR=${HOME}/tmp

IPHTML="/tmp/`hostname`-ip.html"
HTTP_PORT=5000

IPHTML_DST="ytani@ssh.ytani.net:public_html/iot"

PIN_AUDIO1=12
PIN_AUDIO2=13

PIN_SERVO1=17
PIN_SERVO2=27
PIN_SERVO3=22
PIN_SERVO4=23

PIN_SW=21
PIN_VCC=26
PIN_LED=20

OPENING_MUSIC="StarTrek-VOY-opening.mp3"
OPENING_MUSIC_PLAYER="cvlc --play-and-exit --alsa-gain 0.5"

SPEAK_SVR="SpeakServer.py"
SPEAK_SVR_OPT="-d"
SPEAK_LOG="${LOGDIR}/speak.log"
SPEAK_CMD="SpeakClient.py"
SPEAKIPADDR="speakipaddr2.sh"

HTTP_SVR="OttoPiHttpServer.py"
HTTP_SVR_OPT="-d"
HTTP_LOG="${LOGDIR}/http.log"

ROBOT_SVR="OttoPiServer.py"
ROBOT_SVR_OPT="12345"
ROBOT_LOG="${LOGDIR}/robot.log"
ROBOT_CLIENT="OttoPiClient.py"

BLE_SVR="OttoPiBleServer.py"
BLE_SVR_OPT="-d"
BLE_LOG="${LOGDIR}/ble.log"

LOOP_SH="loop.sh"
LOOP_LOG="${LOGDIR}/loop.log"

MUSIC_SH="music.sh"
MUSIC_LOG="${LOGDIR}/music.log"

#
# functions
#
echo_date () {
    DATE_STR=`date +'%Y/%m%d(%a) %H:%M:%S'`
    echo "${DATE_STR}> $*"
}

echo_do () {
    DATE_STR=`date +'%Y/%m%d(%a) %H:%M:%S'`
    echo_date $*
    eval $*
}

#
# init
#
echo_date "MYNAME=${MYNAME}"
echo_date "MYDIR=${MYDIR}"

cd ${MYDIR}
BASEDIR=`pwd`
echo_date "BASEDIR=${BASEDIR}"

cd ..
ENVDIR=`pwd`
if [ ! -f ${ENVDIR}/bin/activate ]; then
    echo "${ENVDIR}: invalid venv directory"
    exit 1
fi
echo_date "ENVDIR=${ENVDIR}"

BINDIR="${ENVDIR}/bin"
echo_date "BINDIR=${BINDIR}"

#
# main
#

#
# start pigpiod
#
echo_date "* start pigpiod"
sudo pigpiod
sleep 5

#
# setup GPIO pins
#
echo_date "* setup GPIO pins"
pigs m ${PIN_AUDIO1} 0
pigs m ${PIN_AUDIO2} 0

pigs s ${PIN_SERVO1} 0
pigs s ${PIN_SERVO2} 0
pigs s ${PIN_SERVO3} 0
pigs s ${PIN_SERVO4} 0

pigs m ${PIN_LED} w
pigs m ${PIN_VCC} w
pigs m ${PIN_SW} r

pigs w ${PIN_LED} 0
pigs w ${PIN_VCC} 1

#
# activate Python venv
#
echo_date "* activate Python venv"
. ${BINDIR}/activate

sleep 5

#
# start opening music
#
echo_date "* start opening music"
OPENING_MUSIC_FILE="${BASEDIR}/sound/opening/${OPENING_MUSIC}"
if [ -f ${OPENING_MUSIC_FILE} ]; then
    echo_do ${OPENING_MUSIC_PLAYER} ${OPENING_MUSIC_FILE} &
else
    echo_date "${OPENING_MUSIC_FILE}: no such file"
fi
sleep 1

#
# get IP address
#
IPADDR=`${BASEDIR}/IpAddr.py -d 2> ${LOGDIR}/IpAddr.log`
echo_date "IPADDR=${IPADDR}"

#
# make HTML file including IP address and publish
#
IPHTML_TEMPLATE=${BASEDIR}/ipaddr-template.html
TMPFILE1=`tempfile -s '.html'`
sed "s/{{ ipaddr }}/${IPADDR}/g" ${IPHTML_TEMPLATE} > ${TMPFILE1}
sed "s/{{ port }}/${HTTP_PORT}/g" ${TMPFILE1} > ${IPHTML}
rm -fv ${TMPFILE1}
echo_date "IPHTML=${IPHTML}"

echo_date "* publish IP address file ${IPHTML} to ${IPHTML_DST}"
echo_do scp ${IPHTML} ${IPHTML_DST}
rm -fv ${IPHTML}

#
# start speak server
#
if which ${SPEAK_SVR}; then
    if [ -f ${SPEAK_LOG} ]; then
        mv -fv ${SPEAK_LOG} ${SPEAK_LOG}.1
    fi
    ${SPEAK_SVR} ${SPEAK_SVR_OPT} > ${SPEAK_LOG} 2>&1 &
    sleep 3
    ${SPEAK_CMD} "音声合成システムを起動しました" &
    sleep 3
    ${SPEAK_CMD} "起動処理を実行しています" &
    sleep 3
    ${SPEAK_CMD} "しばらくお待ちください" &
    sleep 3
    ${SPEAK_CMD} "起動処理の状況を音声でお知らせします" &
    sleep 3
fi

#
# speak IP address
#
if which ${SPEAKIPADDR}; then
    ${SPEAKIPADDR} ${PIN_SW}
    ${SPEAK_CMD} "起動処理を続行します" &
    sleep 2
fi

#
# HTTP server
#
if which ${HTTP_SVR}; then
    if [ -f ${HTTP_LOG} ]; then
        mv -fv ${HTTP_LOG} ${HTTP_LOG}.1
    fi
    cd ${BASEDIR}
    ${HTTP_SVR} ${HTTP_SVR_OPT} > ${HTTP_LOG} 2>&1 &
    sleep 3
    ${SPEAK_CMD} "リモート操作インタフェースを起動します" &
    sleep 2
    ${SPEAK_CMD} "スマートフォンでの操作が可能になりました" &
    sleep 6
fi

#
# robot server
#
if which ${ROBOT_SVR}; then
    if [ -f ${ROBOT_LOG} ]; then
        mv -fv ${ROBOT_LOG} ${ROBOT_LOG}.1
    fi
    cd ${BASEDIR}
    ${ROBOT_SVR} ${ROBOT_SVR_OPT} > ${ROBOT_LOG} 2>&1 &
    sleep 3
    ${SPEAK_CMD} "モーター制御システムを起動し" &
    sleep 2
    ${SPEAK_CMD} "モーターの動作確認を行います" &
    sleep 6
    ${ROBOT_CLIENT} -d ':.happy'
    sleep 5
fi

#
# BLE server
#
if which ${BLE_SVR}; then
    if [ -f ${BLE_LOG} ]; then
        mv -fv ${BLE_LOG} ${BLE_LOG}.1
    fi
    cd ${BASEDIR}
    sudo ${BINDIR}/activate-do.sh ${ENVDIR} ${BLE_SVR} ${BLE_SVR_OPT} > ${BLE_LOG} 2>&1 &
    sleep 3
    ${SPEAK_CMD} "BLEサーバーを起動します" &
    sleep 3
    ${SPEAK_CMD} "スクラッチからの制御が可能になりました" &
    sleep 3
fi

#
# boot complete
#
${SPEAK_CMD} "起動処理が完了しました" &
sleep 2
${SPEAK_CMD} "お待たせしました" &
sleep 2
${SPEAK_CMD} "準備、オーケーです" &
sleep 3
${ROBOT_CLIENT} -d ':.hi_right'

#
# wait opening music
#
#while pgrep vlc; do
#    echo_date "waiting vlc to end .."
#    sleep 1
#done

sleep 5

echo_date "start ${LOOP_SH}"
if which ${LOOP_SH}; then
    ${LOOP_SH} > ${LOOP_LOG} 2>&1 &
fi

echo_date "start ${MUSIC_SH}"
if which ${MUSIC_SH}; then
    ${MUSIC_SH} > ${MUSIC_LOG} 2>&1 &
fi

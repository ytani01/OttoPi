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

OPENING_MUSIC="opening"
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
ts_echo () {
    DATE_STR=`date +'%Y/%m%d(%a) %H:%M:%S'`
    echo "${DATE_STR}> $*"
}

ts_echo_do () {
    DATE_STR=`date +'%Y/%m%d(%a) %H:%M:%S'`
    ts_echo $*
    eval $*
}

#
# init
#
MYNAME=`basename $0`
ts_echo "MYNAME=${MYNAME}"

MYDIR=`dirname $0`
ts_echo "MYDIR=${MYDIR}"

cd ${MYDIR}
BASEDIR=`pwd`
ts_echo "BASEDIR=${BASEDIR}"

cd ..
VENVDIR=`pwd`
ts_echo "VENVDIR=${VENVDIR}"

BINDIR="${VENVDIR}/bin"
ts_echo "BINDIR=${BINDIR}"

#
# check venv and activate it
#
if [ -z "${VIRTUAL_ENV}" ]; then
    ACTIVATE="${BINDIR}/activate"
    ts_echo "ACTIVATE=${ACTIVATE}"

    if [ ! -f ${ACTIVATE} ]; then
        ts_echo "ERROR: ${ACTIVATE}: no such file"
        exit 1
    fi
    . ${ACTIVATE}
fi
if [ ${VIRTUAL_ENV} != ${VENVDIR} ]; then
    ts_echo "ERROR: VIRTUAL_ENV=${VIRTUAL_ENV} != VENVIDR=${VENVDIR}"
    exit 1
fi
ts_echo "VIRTUAL_ENV=${VIRTUAL_ENV}"
ts_echo "PATH=${PATH}"

#
# start pigpiod
#
ts_echo "* start pigpiod"
ts_echo_do sudo pigpiod
sleep 5

#
# setup GPIO pins
#
ts_echo "* setup GPIO pins"
pigs m ${PIN_AUDIO1} 0
pigs m ${PIN_AUDIO2} 0

sleep 3

#
# start opening music
#
ts_echo "* start opening music"
OPENING_MUSIC_FILE="${BASEDIR}/sound/music/${OPENING_MUSIC}"
if [ -f ${OPENING_MUSIC_FILE} ]; then
    ts_echo_do ${OPENING_MUSIC_PLAYER} ${OPENING_MUSIC_FILE} &
else
    ts_echo "${OPENING_MUSIC_FILE}: no such file"
fi
sleep 2

#
# get IP address
#
IPADDR=`${BASEDIR}/IpAddr.py -d 2> ${LOGDIR}/IpAddr.log`
ts_echo "IPADDR=${IPADDR}"

#
# make HTML file including IP address and publish
#
IPHTML_TEMPLATE=${BASEDIR}/ipaddr-template.html
TMPFILE1=`tempfile -s '.html'`
sed "s/{{ ipaddr }}/${IPADDR}/g" ${IPHTML_TEMPLATE} > ${TMPFILE1}
sed "s/{{ port }}/${HTTP_PORT}/g" ${TMPFILE1} > ${IPHTML}
rm -fv ${TMPFILE1}
ts_echo "IPHTML=${IPHTML}"

ts_echo "* publish IP address file ${IPHTML} to ${IPHTML_DST}"
ts_echo_do scp ${IPHTML} ${IPHTML_DST}
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
else
    ts_echo "ERROR> ${SPEAK_SVR}: not found"
    exit 1
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
    sleep 5
    ${SPEAK_CMD} "リモート操作インタフェースを起動します" &
    sleep 2
    ${SPEAK_CMD} "スマートフォンでの操作が可能になりました" &
    sleep 6
else
    ts_echo "ERROR> ${HTTP_SVR}: not found"
    exit 1
fi

#
# robot server
#
if which ${ROBOT_SVR}; then
    if [ -f ${ROBOT_LOG} ]; then
        mv -fv ${ROBOT_LOG} ${ROBOT_LOG}.1
    fi
    cd ${BINDIR}
    ${ROBOT_SVR} ${ROBOT_SVR_OPT} > ${ROBOT_LOG} 2>&1 &
    sleep 5
    ${SPEAK_CMD} "モーター制御システムを起動し" &
    sleep 2
    ${SPEAK_CMD} "モーターの動作確認を行います" &
    sleep 8
    while ! ${ROBOT_CLIENT} -d ':.surprised'; do
        sleep 2
    done
    sleep 5
else
    ts_echo "ERROR> ${ROBOT_SVR}: not found"
    exit 1
fi

#
# BLE server
#
if which ${BLE_SVR}; then
    if [ -f ${BLE_LOG} ]; then
        mv -fv ${BLE_LOG} ${BLE_LOG}.1
    fi
    cd ${BINDIR}
    ${BLE_SVR} ${BLE_SVR_OPT} > ${BLE_LOG} 2>&1 &
    sleep 5
    ${SPEAK_CMD} "BLEサーバーを起動します" &
    sleep 2
    ${SPEAK_CMD} "スクラッチからの制御が可能になりました" &
    sleep 3
else
    ts_echo "ERROR> ${BLE_SVR}: not found"
    exit 1
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
${ROBOT_CLIENT} -d ':.happy'

#
# wait opening music
#
#while pgrep vlc; do
#    ts_echo "waiting vlc to end .."
#    sleep 1
#done

sleep 5

ts_echo "start ${LOOP_SH}"
if which ${LOOP_SH}; then
    ${LOOP_SH} > ${LOOP_LOG} 2>&1 &
fi

ts_echo "start ${MUSIC_SH}"
if which ${MUSIC_SH}; then
    ${MUSIC_SH} > ${MUSIC_LOG} 2>&1 &
fi

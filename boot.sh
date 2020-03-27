#!/bin/sh -x
#
# Sample boot.sh
#
# (c) Yoichi Tanibayashi
#
MY_NAME="オットーパイ"

BINDIR=${HOME}/bin
LOGDIR=${HOME}/tmp
ROBOT_DIR=${HOME}/OttoPi

export PATH=${BINDIR}:${PATH}

for d in OttoPi LedSwitch speak; do
    export PYTHONPATH="${PYTHONPATH}:${HOME}/$d"
done
echo "PYTHONPATH=${PYTHONPATH}"

### Button and LED
PIN_SW=21
PIN_VCC=26
PIN_LED=20

BUTTON_CMD="${ROBOT_DIR}/RobotButton.py"
BUTTON_OPT=" -s ${PIN_SW} -v ${PIN_VCC} -l ${PIN_LED}"
BUTTON_LOG="${LOGDIR}/button.log"

### Music
OPENING_MUSIC="ON"
OPENING_MUSIC_PLAYER="cvlc --play-and-exit"
OPENING_MUSIC_DATA="${HOME}/tmp/opening-music"

### Speak
SPEAK=OFF
SPEAK_DIR=${HOME}/speak
SPEAK_SERVER="${SPEAK_DIR}/SpeakServer.py"
SPEAK_LOG="${LOGDIR}/speak.log"
SPEAK_CMD="${SPEAK_DIR}/SpeakClient.py"
SPEAKIPADDR_CMD="${SPEAK_DIR}/speakipaddr2.sh"

### Robot Server
ROBOT_SERVER="${ROBOT_DIR}/OttoPiServer.py"
ROBOT_OPT="12345"
#ROBOT_OPT="-d"
ROBOT_LOG="${LOGDIR}/robot.log"

### HTTP Server
HTTP_SERVER="${ROBOT_DIR}/OttoPiHttpServer.py"
#HTTP_OPT=""
HTTP_OPT="-d"
HTTP_LOG="${LOGDIR}/http.log"

### WebSocket Server
WS_SERVER="${ROBOT_DIR}/OttoPiWebsockServer.py"
WS_SERVER_OPT="-d"
WS_SERVER_LOG="${LOGDIR}/ws_server.log"

### BLE Server
BLE_SERVER="${ROBOT_DIR}/OttoPiBleServer.py"
BLE_SERVER_OPT="-d"
BLE_SERVER_LOG="${LOGDIR}/ble_server.log"

### Robot Client
ROBOT_CLIENT="${ROBOT_DIR}/OttoPiClient.py"

### loop.sh
LOOP_SH="${ROBOT_DIR}/loop.sh"
LOOP_LOG="${LOGDIR}/loop.log"

### music.sh
MUSIC_SH="${ROBOT_DIR}/music.sh"
MUSIC_LOG="${LOGDIR}/music.log"

### mjpg_streamer
MJPG_STREAMER="${BINDIR}/mjpg-streamer.sh"
MJPG_STREAMER_LOG="${LOGDIR}/mjpg-streamer.log"

#######
# main
#######

gpio -g mode ${PIN_LED} output && gpio -g write ${PIN_LED} 1
gpio -g mode ${PIN_VCC} output && gpio -g write ${PIN_VCC} 1
gpio -g mode ${PIN_SW} input

echo "OPENING_MUSIC=${OPENING_MUSIC}"
if [ "${OPENING_MUSIC}" = "ON" ]; then
    #nice -n 5 ${OPENING_MUSIC_PLAYER} ${OPENING_MUSIC_DATA} &
    ${OPENING_MUSIC_PLAYER} ${OPENING_MUSIC_DATA} &
    sleep 5
fi

if [ -x ${SPEAK_SERVER} ]; then
    SPEAK=ON
    if [ -f ${SPEAK_LOG} ]; then
	mv ${SPEAK_LOG} ${SPEAK_LOG}.1
    fi
    ${SPEAK_SERVER} -d > ${SPEAK_LOG} 2>&1 &
    sleep 3
    ${SPEAK_CMD} "音声合成システムを起動しました"
    sleep 3

    #${SPEAK_CMD} "私は二そくほこうロボット"
    #${SPEAK_CMD} "${MY_NAME} です"
    ${SPEAK_CMD} "起動処理を実行しています"
    ${SPEAK_CMD} "しばらくお待ちください"
    sleep 3
fi

if which ${SPEAKIPADDR_CMD}; then
    ${SPEAKIPADDR_CMD} ${PIN_SW}
    ${SPEAK_CMD} "起動処理を続行します"
fi

if [ -x ${HTTP_SERVER} ]; then
    cd ${BINDIR}
    if [ -f ${HTTP_LOG} ]; then
	mv ${HTTP_LOG} ${HTTP_LOG}.1
    fi
    ${HTTP_SERVER} ${HTTP_OPT} > ${HTTP_LOG} 2>&1 &

    ${SPEAK_CMD} "リモート操作インターフェースを起動します" &
    sleep 3
fi

if [ -x ${ROBOT_SERVER} ]; then
    cd ${BINDIR}
    if [ -f ${ROBOT_LOG} ]; then
	mv ${ROBOT_LOG} ${ROBOT_LOG}.1
    fi
    ${ROBOT_SERVER} ${ROBOT_OPT} > ${ROBOT_LOG} 2>&1 &

    ${SPEAK_CMD} "モーター制御システムを起動します" &
    sleep 3
    ${ROBOT_CLIENT} -d ':.happy'
    sleep 2
fi

#if [ -x ${WS_SERVER} ]; then
#    cd ${BINDIR}
#    if [ -f ${WS_SERVER_LOG} ]; then
#	mv ${WS_SERVER_LOG} ${WS_SERVER_LOG}.1
#    fi
#    ${WS_SERVER} ${WS_SERVER_OPT} > ${WS_SERVER_LOG} 2>&1 &
#
#    ${SPEAK_CMD} "ウエブソックサーバーを起動します" &
#    sleep 3
#    ${ROBOT_CLIENT} -d  ':.surprised'
#    sleep 3
#fi

if [ -x ${BLE_SERVER} ]; then
    cd ${BINDIR}
    if [ -f ${BLE_SERVER_LOG} ]; then
	mv ${BLE_SERVER_LOG} ${BLE_SERVER_LOG}.1
    fi
    sudo ${BLE_SERVER} ${BLE_SERVER_OPT} > ${BLE_SERVER_LOG} 2>&1 &

    ${SPEAK_CMD} "BLEサーバーを起動します" &
    sleep 3
    ${ROBOT_CLIENT} -d ':.hi_right'
    sleep 2
fi

if [ -x ${MJPG_STREAMER} ]; then
    ${MJPG_STREAMER} > ${MJPG_STREAMER_LOG} 2>&1 &
fi

# if [ -x ${BUTTON_CMD} ]; then
#     ${BUTTON_CMD} ${BUTTON_OPT} > ${BUTTON_LOG} 2>&1 &

#     ${SPEAK_CMD} "ボタン操作を可能にします" &
#     sleep 5
# fi

# if which ${SPEAKIPADDR_CMD}; then
#     #${SPEAKIPADDR_CMD} ${PIN_SW} repeat &
#     ${SPEAKIPADDR_CMD} ${PIN_SW} &
#     PID_IPADDR=$!
# fi
# echo "wait ${PID_IPADDR}"
# wait ${PID_IPADDR}
# echo "done: ${PID_IPADDR}"

${SPEAK_CMD} "起動処理が完了しました"
${SPEAK_CMD} "お待たせしました"
${SPEAK_CMD} "準備、オーケーです"

sleep 5
if [ -x ${LOOP_SH} ]; then
    ${LOOP_SH} > ${LOOP_LOG} 2>&1 &
fi

if [ -x ${MUSIC_SH} ]; then
    ${MUSIC_SH} > ${MUSIC_LOG} 2>&1 &
fi

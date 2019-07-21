#!/bin/sh
#
# Sample boot.sh
#
# (c) Yoichi Tanibayashi
#

BINDIR=${HOME}/bin
LOGDIR=${HOME}/tmp

PATH=${BINDIR}:${PATH}

MY_NAME="オットー・パイ"

### Button and LED
PIN_SW=21
PIN_VCC=26
PIN_LED=20

BUTTON_CMD="RobotButton.py"
BUTTON_OPT=" -s ${PIN_SW} -v ${PIN_VCC} -l ${PIN_LED}"
BUTTON_LOG="${LOGDIR}/button.log"

### Music
MUSIC=OFF
MUSIC_PLAYER="cvlc"
MUSIC_PLAYER_OPT="--play-and-exit"
MUSIC_DATA="${HOME}/tmp/boot-music.aac"

### Speak
SPEAK=OFF
SPEAK_SERVER="SpeakServer.py"
SPEAK_LOG="${LOGDIR}/speak.log"
SPEAK_CMD="SpeakClient.py"
SPEAKIPADDR_CMD="speakipaddr2.sh"

### Robot Server
ROBOT_SERVER="${BINDIR}/OttoPiServer.py"
ROBOT_OPT="12345"
#ROBOT_OPT="-d"
ROBOT_LOG="${LOGDIR}/robot.log"

### HTTP Server
HTTP_SERVER="${BINDIR}/OttoPiHttpServer.py"
#HTTP_OPT=""
HTTP_OPT="-d"
HTTP_LOG="${LOGDIR}/http.log"

### Robot Client
ROBOT_CLIENT="${BINDIR}/OttoPiClient.py"

### mjpg_streamer
MJPG_STREAMER="${BINDIR}/mjpg-streamer.sh"
MJPG_STREAMER_LOG="${LOGDIR}/mjpg-streamer.log"

#######
# main
#######
gpio -g mode ${PIN_LED} output && gpio -g write ${PIN_LED} 1
gpio -g mode ${PIN_VCC} output && gpio -g write ${PIN_VCC} 1

if [ "${MUSIC}" = "ON" ]; then
    $MUSIC_PLAYER $MUSIC_PLAYER_OPT $MUSIC_DATA > /dev/null 2>&1 &
fi

#if "${MUSIC}" != "ON"; then
  if which ${SPEAK_SERVER}; then
    SPEAK=ON
    if [ -f ${SPEAK_LOG} ]; then
	mv ${SPEAK_LOG} ${SPEAK_LOG}.1
    fi
    ${SPEAK_SERVER} -d > ${SPEAK_LOG} 2>&1 &
    sleep 10
    #${SPEAK_CMD} "私は二足歩行ロボット"
    ${SPEAK_CMD} "私は二そくほこうロボット"
    ${SPEAK_CMD} "${MY_NAME} です"
  fi
#fi

if [ -x ${ROBOT_SERVER} ]; then
    if [ ${SPEAK} = ON ]; then
	${SPEAK_CMD} "ロボット制御システムを起動します" &
    fi
    if [ -f ${ROBOT_LOG} ]; then
	mv ${ROBOT_LOG} ${ROBOT_LOG}.1
    fi
    cd ${BINDIR}
    ${ROBOT_SERVER} ${ROBOT_OPT} > ${ROBOT_LOG} 2>&1 &
    sleep 10
fi

if [ -x ${MJPG_STREAMER} ]; then
    ${MJPG_STREAMER} > ${MJPG_STREAMER_LOG} 2>&1 &
fi

if [ -x ${HTTP_SERVER} ]; then
    if [ ${SPEAK} = ON ]; then
	${SPEAK_CMD} "ウェブインターフェースサーバーを 起動します" &
    fi
    if [ -f ${HTTP_LOG} ]; then
	mv ${HTTP_LOG} ${HTTP_LOG}.1
    fi
    cd ${BINDIR}
    ${HTTP_SERVER} ${HTTP_OPT} > ${HTTP_LOG} 2>&1 &
    sleep 10 
fi

if [ ${SPEAK} = ON ]; then
    if which ${SPEAKIPADDR_CMD}; then
	${SPEAKIPADDR_CMD} repeat &
    fi
fi

sleep 10

if which ${BUTTON_CMD}; then
    ${BUTTON_CMD} ${BUTTON_OPT} > ${BUTTON_LOG} 2>&1 &
fi

${ROBOT_CLIENT} -d -c ':happy'
